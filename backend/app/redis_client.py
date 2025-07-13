"""
Redis client for pub/sub and caching functionality.
Handles project state management and progress updates.
"""

import json
import logging
from typing import Any

import redis
import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Async Redis client for pub/sub and state management"""

    def __init__(self):
        self.redis: aioredis.Redis | None = None
        self.pubsub: aioredis.client.PubSub | None = None

    async def connect(self):
        """Initialize Redis connection"""
        try:
            self.redis = await aioredis.from_url(
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

    async def flushdb(self):
        """Flush all keys from current database (for testing)"""
        if self.redis:
            await self.redis.flushdb()

    async def health_check(self) -> bool:
        """Check Redis connection health"""
        try:
            if self.redis:
                await self.redis.ping()
                return True
        except Exception:
            pass
        return False

    async def set_with_expiry(self, key: str, value: Any, expiry_seconds: int = 300):
        """Set a key with expiry"""
        if self.redis:
            await self.redis.set(key, json.dumps(value), ex=expiry_seconds)

    async def get(self, key: str) -> Any:
        """Get a value by key"""
        if self.redis:
            data = await self.redis.get(key)
            return json.loads(data) if data else None
        return None

    async def delete(self, key: str):
        """Delete a key"""
        if self.redis:
            await self.redis.delete(key)

    async def publish(self, channel: str, message: str):
        """Publish message to channel"""
        if self.redis:
            await self.redis.publish(channel, message)


class SynchronousRedisClient:
    """Synchronous Redis client for worker components"""
    
    def __init__(self):
        self.redis: redis.Redis | None = None
    
    def connect(self):
        """Initialize synchronous Redis connection"""
        try:
            self.redis = redis.from_url(
                settings.redis_url, encoding="utf-8", decode_responses=True
            )
            # Test connection
            self.redis.ping()
            logger.info(f"Synchronous Redis client connected to {settings.redis_url}")
            return self.redis
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis = None
            return None
    
    def disconnect(self):
        """Close Redis connection"""
        if self.redis:
            self.redis.close()
        logger.info("Synchronous Redis client disconnected")
    
    def set_with_expiry(self, key: str, value: Any, expiry_seconds: int = 300) -> bool:
        """Set a key with expiry"""
        if self.redis:
            try:
                serialized_value = json.dumps(value) if not isinstance(value, str) else value
                return self.redis.setex(key, expiry_seconds, serialized_value)
            except Exception as e:
                logger.error(f"Error setting key {key}: {e}")
                return False
        return False
    
    def get(self, key: str) -> Any:
        """Get a value by key"""
        if self.redis:
            try:
                data = self.redis.get(key)
                if data:
                    try:
                        return json.loads(data)
                    except json.JSONDecodeError:
                        return data  # Return as string if not JSON
                return None
            except Exception as e:
                logger.error(f"Error getting key {key}: {e}")
                return None
        return None
    
    def delete(self, key: str) -> bool:
        """Delete a key"""
        if self.redis:
            try:
                return bool(self.redis.delete(key))
            except Exception as e:
                logger.error(f"Error deleting key {key}: {e}")
                return False
        return False
    
    def publish(self, channel: str, message: str) -> bool:
        """Publish message to channel"""
        if self.redis:
            try:
                return bool(self.redis.publish(channel, message))
            except Exception as e:
                logger.error(f"Error publishing to channel {channel}: {e}")
                return False
        return False
    
    def llen(self, key: str) -> int:
        """Get length of list"""
        if self.redis:
            try:
                return self.redis.llen(key)
            except Exception as e:
                logger.error(f"Error getting length of {key}: {e}")
                return 0
        return 0
    
    def lindex(self, key: str, index: int) -> str | None:
        """Get item from list by index"""
        if self.redis:
            try:
                return self.redis.lindex(key, index)
            except Exception as e:
                logger.error(f"Error getting index {index} from {key}: {e}")
                return None
        return None
    
    def lpush(self, key: str, *values) -> int:
        """Push values to start of list"""
        if self.redis:
            try:
                return self.redis.lpush(key, *values)
            except Exception as e:
                logger.error(f"Error pushing to {key}: {e}")
                return 0
        return 0
    
    def lrange(self, key: str, start: int, end: int) -> list:
        """Get range of items from list"""
        if self.redis:
            try:
                return self.redis.lrange(key, start, end)
            except Exception as e:
                logger.error(f"Error getting range from {key}: {e}")
                return []
        return []
    
    def expire(self, key: str, time: int) -> bool:
        """Set expiration on key"""
        if self.redis:
            try:
                return bool(self.redis.expire(key, time))
            except Exception as e:
                logger.error(f"Error setting expiration on {key}: {e}")
                return False
        return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        if self.redis:
            try:
                return bool(self.redis.exists(key))
            except Exception as e:
                logger.error(f"Error checking existence of {key}: {e}")
                return False
        return False
    
    def setex(self, key: str, time: int, value: Any) -> bool:
        """Set key with expiration"""
        if self.redis:
            try:
                serialized_value = json.dumps(value) if not isinstance(value, str) else value
                return bool(self.redis.setex(key, time, serialized_value))
            except Exception as e:
                logger.error(f"Error setting {key} with expiration: {e}")
                return False
        return False
    
    def zadd(self, key: str, mapping: dict) -> int:
        """Add to sorted set"""
        if self.redis:
            try:
                return self.redis.zadd(key, mapping)
            except Exception as e:
                logger.error(f"Error adding to sorted set {key}: {e}")
                return 0
        return 0
    
    def zremrangebyscore(self, key: str, min_score: float, max_score: float) -> int:
        """Remove items from sorted set by score range"""
        if self.redis:
            try:
                return self.redis.zremrangebyscore(key, min_score, max_score)
            except Exception as e:
                logger.error(f"Error removing from sorted set {key}: {e}")
                return 0
        return 0
    
    def zcard(self, key: str) -> int:
        """Get cardinality of sorted set"""
        if self.redis:
            try:
                return self.redis.zcard(key)
            except Exception as e:
                logger.error(f"Error getting cardinality of {key}: {e}")
                return 0
        return 0
    
    def zrangebyscore(self, key: str, min_score: float, max_score: str, withscores: bool = False) -> list:
        """Get items from sorted set by score range"""
        if self.redis:
            try:
                return self.redis.zrangebyscore(key, min_score, max_score, withscores=withscores)
            except Exception as e:
                logger.error(f"Error getting range from sorted set {key}: {e}")
                return []
        return []
    
    def hgetall(self, key: str) -> dict:
        """Get all fields and values from hash"""
        if self.redis:
            try:
                return self.redis.hgetall(key)
            except Exception as e:
                logger.error(f"Error getting hash {key}: {e}")
                return {}
        return {}
    
    def hincrby(self, key: str, field: str, amount: int = 1) -> int:
        """Increment hash field by amount"""
        if self.redis:
            try:
                return self.redis.hincrby(key, field, amount)
            except Exception as e:
                logger.error(f"Error incrementing {key}:{field}: {e}")
                return 0
        return 0
    
    def incr(self, key: str) -> int:
        """Increment key value"""
        if self.redis:
            try:
                return self.redis.incr(key)
            except Exception as e:
                logger.error(f"Error incrementing {key}: {e}")
                return 0
        return 0


# Global instances
redis_client = RedisClient()
_sync_redis_client = None


def get_redis_client() -> SynchronousRedisClient:
    """Get or create synchronous Redis client instance"""
    global _sync_redis_client
    if _sync_redis_client is None:
        _sync_redis_client = SynchronousRedisClient()
        try:
            _sync_redis_client.connect()
        except Exception as e:
            logger.warning(f"Could not connect to Redis during initialization: {e}")
            # Return the client anyway, it will handle missing connections gracefully
    return _sync_redis_client
