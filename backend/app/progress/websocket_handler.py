"""WebSocket handler for progress streaming"""

from typing import Dict, Set, Optional
from collections import defaultdict
from fastapi import WebSocket, WebSocketDisconnect
import json

from app.progress.tracker import ProgressTracker
from app.services.websocket import WebSocketManager


class ProgressWebSocketHandler:
    """Handle WebSocket connections for progress updates"""
    
    def __init__(self, tracker: ProgressTracker, ws_manager: WebSocketManager):
        self.tracker = tracker
        self.ws_manager = ws_manager
        self.subscriptions: Dict[str, Set[str]] = defaultdict(set)  # task_id -> {client_ids}
        self.client_subscriptions: Dict[str, Set[str]] = defaultdict(set)  # client_id -> {task_ids}
    
    async def handle_connection(self, websocket: WebSocket, client_id: str):
        """Handle new WebSocket connection"""
        await self.ws_manager.connect(websocket, client_id)
        
        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                await self.handle_message(websocket, client_id, message)
                
        except WebSocketDisconnect:
            await self.handle_disconnect(client_id)
    
    async def handle_message(
        self, 
        websocket: WebSocket, 
        client_id: str, 
        message: Dict
    ):
        """Handle incoming WebSocket message"""
        msg_type = message.get('type')
        
        if msg_type == 'subscribe':
            await self.handle_subscribe(websocket, client_id, message)
        elif msg_type == 'unsubscribe':
            await self.handle_unsubscribe(client_id, message)
        elif msg_type == 'get_progress':
            await self.handle_get_progress(websocket, message)
        elif msg_type == 'get_batch_progress':
            await self.handle_get_batch_progress(websocket, message)
        else:
            await websocket.send_json({
                'type': 'error',
                'message': f'Unknown message type: {msg_type}'
            })
    
    async def handle_subscribe(
        self, 
        websocket: WebSocket, 
        client_id: str, 
        message: Dict
    ):
        """Handle progress subscription request"""
        task_ids = message.get('task_ids', [])
        
        if not task_ids:
            await websocket.send_json({
                'type': 'error',
                'message': 'No task_ids provided'
            })
            return
        
        # Subscribe to tasks
        for task_id in task_ids:
            self.subscriptions[task_id].add(client_id)
            self.client_subscriptions[client_id].add(task_id)
            
            # Send current progress immediately
            progress = await self.tracker.get_progress(task_id)
            if progress:
                await websocket.send_json({
                    'type': 'progress.current',
                    'task_id': task_id,
                    'data': {
                        'status': progress.status.value,
                        'current_stage': progress.current_stage,
                        'overall_progress': progress.overall_progress,
                        'eta': progress.eta.isoformat() if progress.eta else None,
                        'stages': {
                            str(k): {
                                'name': v.name,
                                'status': v.status.value,
                                'progress': v.progress,
                                'message': v.message
                            } for k, v in progress.stages.items()
                        },
                        'preview_url': progress.preview_url,
                        'resource_usage': progress.resource_usage,
                        'updated_at': progress.updated_at.isoformat()
                    }
                })
            else:
                await websocket.send_json({
                    'type': 'progress.not_found',
                    'task_id': task_id
                })
        
        # Confirm subscription
        await websocket.send_json({
            'type': 'subscribed',
            'task_ids': task_ids
        })
    
    async def handle_unsubscribe(self, client_id: str, message: Dict):
        """Handle progress unsubscribe request"""
        task_ids = message.get('task_ids', [])
        
        for task_id in task_ids:
            if task_id in self.subscriptions:
                self.subscriptions[task_id].discard(client_id)
                if not self.subscriptions[task_id]:
                    del self.subscriptions[task_id]
            
            if client_id in self.client_subscriptions:
                self.client_subscriptions[client_id].discard(task_id)
    
    async def handle_get_progress(self, websocket: WebSocket, message: Dict):
        """Handle single progress query"""
        task_id = message.get('task_id')
        
        if not task_id:
            await websocket.send_json({
                'type': 'error',
                'message': 'No task_id provided'
            })
            return
        
        progress = await self.tracker.get_progress(task_id)
        
        if progress:
            await websocket.send_json({
                'type': 'progress.response',
                'task_id': task_id,
                'data': {
                    'status': progress.status.value,
                    'current_stage': progress.current_stage,
                    'overall_progress': progress.overall_progress,
                    'eta': progress.eta.isoformat() if progress.eta else None,
                    'stages': {
                        str(k): {
                            'name': v.name,
                            'status': v.status.value,
                            'progress': v.progress,
                            'message': v.message,
                            'duration': v.duration.total_seconds() if v.duration else None
                        } for k, v in progress.stages.items()
                    },
                    'preview_url': progress.preview_url,
                    'resource_usage': progress.resource_usage,
                    'created_at': progress.created_at.isoformat(),
                    'started_at': progress.started_at.isoformat() if progress.started_at else None,
                    'completed_at': progress.completed_at.isoformat() if progress.completed_at else None,
                    'error': progress.error
                }
            })
        else:
            await websocket.send_json({
                'type': 'progress.not_found',
                'task_id': task_id
            })
    
    async def handle_get_batch_progress(self, websocket: WebSocket, message: Dict):
        """Handle batch progress query"""
        batch_id = message.get('batch_id')
        task_ids = message.get('task_ids', [])
        
        if not batch_id or not task_ids:
            await websocket.send_json({
                'type': 'error',
                'message': 'batch_id and task_ids required'
            })
            return
        
        batch_progress = await self.tracker.get_batch_progress(batch_id, task_ids)
        
        await websocket.send_json({
            'type': 'batch_progress.response',
            'batch_id': batch_id,
            'data': {
                'total_tasks': batch_progress.total_tasks,
                'completed_tasks': batch_progress.completed_tasks,
                'failed_tasks': batch_progress.failed_tasks,
                'overall_progress': batch_progress.overall_progress,
                'eta': batch_progress.eta.isoformat() if batch_progress.eta else None,
                'task_summaries': batch_progress.task_summaries
            }
        })
    
    async def handle_disconnect(self, client_id: str):
        """Handle client disconnect"""
        # Remove all subscriptions for this client
        if client_id in self.client_subscriptions:
            task_ids = list(self.client_subscriptions[client_id])
            for task_id in task_ids:
                if task_id in self.subscriptions:
                    self.subscriptions[task_id].discard(client_id)
                    if not self.subscriptions[task_id]:
                        del self.subscriptions[task_id]
            
            del self.client_subscriptions[client_id]
        
        # Disconnect from WebSocket manager
        await self.ws_manager.disconnect(client_id)
    
    async def broadcast_progress_update(self, task_id: str, progress_data: Dict):
        """Broadcast progress update to subscribed clients"""
        if task_id not in self.subscriptions:
            return
        
        message = {
            'type': 'progress.update',
            'task_id': task_id,
            'data': progress_data
        }
        
        # Send to all subscribed clients
        disconnected_clients = []
        for client_id in self.subscriptions[task_id]:
            try:
                await self.ws_manager.send_to_client(client_id, message)
            except Exception:
                # Client disconnected
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            await self.handle_disconnect(client_id)