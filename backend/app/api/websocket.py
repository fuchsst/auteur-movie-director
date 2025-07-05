"""
WebSocket endpoints for real-time communication.
"""

import asyncio
import json
import logging
from typing import Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.config import settings
from app.core.dispatcher import task_dispatcher
from app.models.websocket import (
    CompleteMessage,
    ErrorMessage,
    PingMessage,
    PongMessage,
    ProgressMessage,
    StartGenerationMessage,
    TaskStartedMessage,
)
from app.redis_client import redis_client

logger = logging.getLogger(__name__)

websocket_router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections per project"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, asyncio.Task] = {}

    async def connect(self, project_id: str, websocket: WebSocket):
        """Accept WebSocket connection"""
        await websocket.accept()
        self.active_connections[project_id] = websocket
        logger.info(f"WebSocket connected: {project_id}")

    def disconnect(self, project_id: str):
        """Clean up disconnected WebSocket"""
        self.active_connections.pop(project_id, None)

        # Cancel subscription task
        if project_id in self.subscriptions:
            self.subscriptions[project_id].cancel()
            self.subscriptions.pop(project_id, None)

        logger.info(f"WebSocket disconnected: {project_id}")

    async def send_message(self, project_id: str, message: dict):
        """Send message to specific project connection"""
        if project_id in self.active_connections:
            try:
                await self.active_connections[project_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {project_id}: {e}")
                self.disconnect(project_id)

    async def broadcast(self, message: dict):
        """Broadcast message to all connections"""
        disconnected = []
        for project_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(project_id)

        # Clean up disconnected clients
        for project_id in disconnected:
            self.disconnect(project_id)


# Global connection manager
manager = ConnectionManager()


async def subscribe_to_progress(project_id: str):
    """Subscribe to Redis progress updates for a project"""
    try:
        await redis_client.pubsub.subscribe(settings.redis_progress_channel)

        async for message in redis_client.pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])

                    # Filter messages for this project
                    if data.get("project_id") == project_id:
                        # Convert to appropriate message type
                        if "error" in data:
                            msg = ErrorMessage(
                                project_id=project_id,
                                task_id=data.get("task_id"),
                                error_code="TASK_ERROR",
                                message=data.get("error", "Unknown error"),
                            )
                        elif data.get("progress", 0) >= 1.0:
                            msg = CompleteMessage(
                                project_id=project_id,
                                task_id=data["task_id"],
                                result=data.get("result", {}),
                                duration=0,  # TODO: Track actual duration
                            )
                        else:
                            msg = ProgressMessage(
                                project_id=project_id,
                                task_id=data["task_id"],
                                progress=data.get("progress", 0),
                                message=data.get("message"),
                                preview_url=data.get("preview_url"),
                            )

                        await manager.send_message(project_id, msg.dict())

                except Exception as e:
                    logger.error(f"Error processing Redis message: {e}")

    except asyncio.CancelledError:
        await redis_client.pubsub.unsubscribe(settings.redis_progress_channel)
        raise
    except Exception as e:
        logger.error(f"Error in progress subscription for {project_id}: {e}")


@websocket_router.websocket("/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    """WebSocket endpoint for project-specific connections"""
    await manager.connect(project_id, websocket)

    # Start progress subscription
    progress_task = asyncio.create_task(subscribe_to_progress(project_id))
    manager.subscriptions[project_id] = progress_task

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            # Handle different message types
            if data["type"] == "start_generation":
                try:
                    msg = StartGenerationMessage(**data, project_id=project_id)

                    # Dispatch task
                    task_id = await task_dispatcher.dispatch(
                        project_id=msg.project_id,
                        task_type=msg.task_type,
                        params=msg.params,
                        quality=msg.quality,
                    )

                    # Send acknowledgment
                    ack = TaskStartedMessage(project_id=project_id, task_id=task_id)
                    await manager.send_message(project_id, ack.dict())

                except Exception as e:
                    error_msg = ErrorMessage(
                        project_id=project_id, error_code="DISPATCH_ERROR", message=str(e)
                    )
                    await manager.send_message(project_id, error_msg.dict())

            elif data["type"] == "ping":
                pong = PongMessage(project_id=project_id)
                await manager.send_message(project_id, pong.dict())

    except WebSocketDisconnect:
        manager.disconnect(project_id)
    except Exception as e:
        logger.error(f"WebSocket error for {project_id}: {e}")
        error_msg = ErrorMessage(
            project_id=project_id, error_code="WEBSOCKET_ERROR", message=str(e)
        )
        try:
            await manager.send_message(project_id, error_msg.dict())
        except:
            pass
        manager.disconnect(project_id)
