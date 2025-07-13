"""
WebSocket service for managing real-time connections.

This module provides a WebSocketManager for sending messages to connected clients.
"""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections and message broadcasting."""

    def __init__(self):
        self.active_connections: dict[str, Any] = {}

    async def connect(self, client_id: str, websocket: Any):
        """Connect a new WebSocket client."""
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")

    def disconnect(self, client_id: str):
        """Disconnect a WebSocket client."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected")

    async def send_personal_message(self, message: dict[str, Any], client_id: str):
        """Send a message to a specific client."""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                # Handle different WebSocket implementations
                if hasattr(websocket, 'send_json'):
                    await websocket.send_json(message)
                elif hasattr(websocket, 'send_text'):
                    await websocket.send_text(json.dumps(message))
                else:
                    logger.warning(f"Unknown websocket type for client {client_id}")
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)

    async def broadcast(self, message: dict[str, Any]):
        """Broadcast a message to all connected clients."""
        disconnected = []
        for client_id in self.active_connections:
            try:
                await self.send_personal_message(message, client_id)
            except Exception:
                disconnected.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)


# Global manager instance
manager = WebSocketManager()