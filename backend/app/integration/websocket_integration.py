"""
WebSocket Integration Layer

Integrates Function Runner events with the WebSocket system.
"""

import logging
from typing import Dict, Any, Optional, Set
import json

from .models import ServiceEvent, WebSocketEvent
from ..api.websocket import WebSocketManager

logger = logging.getLogger(__name__)


class WebSocketIntegrationLayer:
    """Integrate WebSocket events across all services"""
    
    def __init__(self, ws_manager: WebSocketManager):
        self.ws_manager = ws_manager
        self.event_handlers = {
            'task.progress': self._handle_task_progress,
            'task.completed': self._handle_task_completed,
            'task.failed': self._handle_task_failed,
            'task.cancelled': self._handle_task_cancelled,
            'take.created': self._handle_take_created,
            'asset.uploaded': self._handle_asset_uploaded,
            'worker.status': self._handle_worker_status,
            'service.health': self._handle_service_health
        }
        self._subscriptions: Dict[str, Set[str]] = {}  # client_id -> set of channels
    
    async def route_event(self, event: ServiceEvent):
        """Route service events to WebSocket clients"""
        
        try:
            # Determine event type and routing
            event_type = f"{event.service}.{event.type}"
            
            logger.debug(f"Routing event: {event_type}")
            
            # Get handler
            handler = self.event_handlers.get(event_type, self._default_handler)
            
            # Process event
            ws_event = await handler(event)
            
            # Send to appropriate clients
            if ws_event:
                await self._send_to_clients(ws_event, event.metadata)
                logger.debug(f"Event {event_type} routed successfully")
            
        except Exception as e:
            logger.error(f"Error routing event {event.service}.{event.type}: {e}")
    
    async def _handle_task_progress(self, event: ServiceEvent) -> WebSocketEvent:
        """Transform task progress event for WebSocket"""
        
        return WebSocketEvent(
            type='generation.progress',
            data={
                'taskId': event.data['task_id'],
                'progress': event.data.get('progress', 0),
                'stage': event.data.get('stage', 'processing'),
                'message': event.data.get('message', ''),
                'preview': event.data.get('preview_url'),
                'eta': event.data.get('eta'),
                'timestamp': event.timestamp.isoformat()
            }
        )
    
    async def _handle_task_completed(self, event: ServiceEvent) -> WebSocketEvent:
        """Transform task completion event for WebSocket"""
        
        return WebSocketEvent(
            type='generation.completed',
            data={
                'taskId': event.data['task_id'],
                'outputs': event.data.get('outputs', {}),
                'executionTime': event.data.get('execution_time', 0),
                'takeId': event.data.get('take_id'),
                'quality': event.data.get('quality'),
                'timestamp': event.timestamp.isoformat()
            }
        )
    
    async def _handle_task_failed(self, event: ServiceEvent) -> WebSocketEvent:
        """Transform task failure event for WebSocket"""
        
        return WebSocketEvent(
            type='generation.failed',
            data={
                'taskId': event.data['task_id'],
                'error': event.data.get('error_message', 'Unknown error'),
                'stage': event.data.get('stage', 'unknown'),
                'recoverable': event.data.get('recoverable', False),
                'timestamp': event.timestamp.isoformat()
            }
        )
    
    async def _handle_task_cancelled(self, event: ServiceEvent) -> WebSocketEvent:
        """Transform task cancellation event for WebSocket"""
        
        return WebSocketEvent(
            type='generation.cancelled',
            data={
                'taskId': event.data['task_id'],
                'reason': event.data.get('reason', 'User cancelled'),
                'timestamp': event.timestamp.isoformat()
            }
        )
    
    async def _handle_take_created(self, event: ServiceEvent) -> WebSocketEvent:
        """Transform take creation event for WebSocket"""
        
        return WebSocketEvent(
            type='take.created',
            data={
                'takeId': event.data['take_id'],
                'projectId': event.data.get('project_id'),
                'shotId': event.data.get('shot_id'),
                'outputs': event.data.get('outputs', {}),
                'metadata': event.data.get('metadata', {}),
                'timestamp': event.timestamp.isoformat()
            }
        )
    
    async def _handle_asset_uploaded(self, event: ServiceEvent) -> WebSocketEvent:
        """Transform asset upload event for WebSocket"""
        
        return WebSocketEvent(
            type='asset.uploaded',
            data={
                'assetId': event.data['asset_id'],
                'projectId': event.data.get('project_id'),
                'path': event.data.get('path'),
                'type': event.data.get('type'),
                'size': event.data.get('size'),
                'timestamp': event.timestamp.isoformat()
            }
        )
    
    async def _handle_worker_status(self, event: ServiceEvent) -> WebSocketEvent:
        """Transform worker status event for WebSocket"""
        
        return WebSocketEvent(
            type='worker.status',
            data={
                'workerId': event.data['worker_id'],
                'status': event.data.get('status'),
                'load': event.data.get('load', 0),
                'activeTasks': event.data.get('active_tasks', 0),
                'health': event.data.get('health', 'unknown'),
                'timestamp': event.timestamp.isoformat()
            }
        )
    
    async def _handle_service_health(self, event: ServiceEvent) -> WebSocketEvent:
        """Transform service health event for WebSocket"""
        
        return WebSocketEvent(
            type='service.health',
            data={
                'service': event.data['service_name'],
                'status': event.data.get('status'),
                'message': event.data.get('message'),
                'checks': event.data.get('checks', []),
                'timestamp': event.timestamp.isoformat()
            }
        )
    
    async def _default_handler(self, event: ServiceEvent) -> WebSocketEvent:
        """Default handler for unrecognized events"""
        
        logger.debug(f"Using default handler for {event.service}.{event.type}")
        
        return WebSocketEvent(
            type=f"{event.service}.{event.type}",
            data={
                **event.data,
                'timestamp': event.timestamp.isoformat()
            }
        )
    
    async def _send_to_clients(self, 
                             ws_event: WebSocketEvent,
                             metadata: Dict[str, Any]):
        """Send event to appropriate WebSocket clients"""
        
        try:
            # Prepare message
            message = {
                'type': ws_event.type,
                'data': ws_event.data
            }
            
            # Determine target clients
            if 'user_id' in metadata:
                # Send to specific user
                await self._send_to_user(metadata['user_id'], message)
                
            elif 'project_id' in metadata:
                # Send to all users in project
                await self._send_to_project(metadata['project_id'], message)
                
            elif 'task_id' in metadata:
                # Send to clients subscribed to this task
                await self._send_to_task_subscribers(metadata['task_id'], message)
                
            else:
                # Broadcast to all admin users for system events
                await self._broadcast_to_admins(message)
                
        except Exception as e:
            logger.error(f"Error sending WebSocket event: {e}")
    
    async def _send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send message to specific user"""
        
        try:
            await self.ws_manager.send_to_user(user_id, message)
            logger.debug(f"Sent message to user {user_id}")
        except Exception as e:
            logger.error(f"Error sending to user {user_id}: {e}")
    
    async def _send_to_project(self, project_id: str, message: Dict[str, Any]):
        """Send message to all users in project"""
        
        try:
            # Get users in project (would need to implement this)
            # For now, just broadcast with project filter
            filtered_message = {
                **message,
                'filter': {'project_id': project_id}
            }
            await self.ws_manager.broadcast(filtered_message)
            logger.debug(f"Sent message to project {project_id}")
        except Exception as e:
            logger.error(f"Error sending to project {project_id}: {e}")
    
    async def _send_to_task_subscribers(self, task_id: str, message: Dict[str, Any]):
        """Send message to clients subscribed to a specific task"""
        
        try:
            # Find clients subscribed to this task
            channel = f"task.{task_id}"
            for client_id, channels in self._subscriptions.items():
                if channel in channels:
                    await self.ws_manager.send_to_client(client_id, message)
            
            logger.debug(f"Sent message to task {task_id} subscribers")
        except Exception as e:
            logger.error(f"Error sending to task subscribers {task_id}: {e}")
    
    async def _broadcast_to_admins(self, message: Dict[str, Any]):
        """Send message to admin users only"""
        
        try:
            # Add admin filter
            admin_message = {
                **message,
                'filter': {'admin_only': True}
            }
            await self.ws_manager.broadcast(admin_message)
            logger.debug("Sent message to admin users")
        except Exception as e:
            logger.error(f"Error broadcasting to admins: {e}")
    
    async def subscribe_client(self, client_id: str, channels: list[str]):
        """Subscribe client to specific channels"""
        
        if client_id not in self._subscriptions:
            self._subscriptions[client_id] = set()
        
        for channel in channels:
            self._subscriptions[client_id].add(channel)
            logger.debug(f"Client {client_id} subscribed to {channel}")
    
    async def unsubscribe_client(self, client_id: str, channels: list[str] = None):
        """Unsubscribe client from channels"""
        
        if client_id not in self._subscriptions:
            return
        
        if channels is None:
            # Unsubscribe from all
            del self._subscriptions[client_id]
            logger.debug(f"Client {client_id} unsubscribed from all channels")
        else:
            # Unsubscribe from specific channels
            for channel in channels:
                self._subscriptions[client_id].discard(channel)
                logger.debug(f"Client {client_id} unsubscribed from {channel}")
            
            # Clean up if no subscriptions left
            if not self._subscriptions[client_id]:
                del self._subscriptions[client_id]
    
    async def handle_client_disconnect(self, client_id: str):
        """Handle client disconnection"""
        
        if client_id in self._subscriptions:
            del self._subscriptions[client_id]
            logger.debug(f"Cleaned up subscriptions for disconnected client {client_id}")
    
    async def get_client_subscriptions(self, client_id: str) -> list[str]:
        """Get list of channels client is subscribed to"""
        
        return list(self._subscriptions.get(client_id, set()))
    
    async def get_channel_subscribers(self, channel: str) -> list[str]:
        """Get list of clients subscribed to a channel"""
        
        subscribers = []
        for client_id, channels in self._subscriptions.items():
            if channel in channels:
                subscribers.append(client_id)
        
        return subscribers
    
    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket integration statistics"""
        
        total_subscriptions = sum(len(channels) for channels in self._subscriptions.values())
        
        return {
            'active_clients': len(self._subscriptions),
            'total_subscriptions': total_subscriptions,
            'channels': list(set().union(*self._subscriptions.values())),
            'event_handlers': list(self.event_handlers.keys())
        }