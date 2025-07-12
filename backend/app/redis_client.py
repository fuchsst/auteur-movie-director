"""
Redis client for pub/sub and caching functionality.
Handles project state management and progress updates.
"""

import json
import logging
from typing import Any

import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Async Redis client for pub/sub and state management"""

    def __init__(self):
        self.redis: redis.Redis | None = None
        self.pubsub: redis.client.PubSub | None = None

    async def connect(self):
        """Initialize Redis connection"""
        try:
            self.redis = await redis.from_url(
                settings.redis_url, encoding="utf-8", decode_responses=True
            )
            self.pubsub = self.redis.pubsub()

            # Test connection
            await self.redis.ping()
            logger.info(f"Redis client connected to {settings.redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self):
        """Close Redis connections"""
        if self.pubsub:
            await self.pubsub.close()
        if self.redis:
            await self.redis.close()
        logger.info("Redis client disconnected")

    async def publish_progress(self, project_id: str, task_id: str, progress: dict[str, Any]):
        """Publish progress update to Redis channel"""
        message = {"project_id": project_id, "task_id": task_id, "type": "progress", **progress}
        await self.redis.publish(settings.redis_progress_channel, json.dumps(message))
        logger.debug(f"Published progress for task {task_id}: {progress.get('progress', 0)}%")

    async def get_project_state(self, project_id: str) -> dict | None:
        """Get project state from Redis"""
        key = f"{settings.redis_state_prefix}{project_id}"
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def set_project_state(self, project_id: str, state: dict):
        """Store project state in Redis"""
        key = f"{settings.redis_state_prefix}{project_id}"
        await self.redis.set(
            key,
            json.dumps(state),
            ex=3600,  # 1 hour expiry
        )

    async def delete_project_state(self, project_id: str):
        """Delete project state from Redis"""
        key = f"{settings.redis_state_prefix}{project_id}"
        await self.redis.delete(key)

    async def health_check(self) -> bool:
        """Check Redis connection health"""
        try:
            if self.redis:
                await self.redis.ping()
                return True
        except Exception:
            pass
        return False


# Global instance
redis_client = RedisClient()
