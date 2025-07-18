from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import Dict, List, Optional, Any
import json
import asyncio
from datetime import datetime
import uuid

from app.core.websocket_manager import WebSocketManager
from app.core.auth import get_current_user
from app.schemas.user import User
from app.services.workspace_service import WorkspaceService

router = APIRouter(prefix="/collaboration", tags=["collaboration"])

class CollaborationManager:
    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.project_rooms: Dict[str, List[str]] = {}
        self.cursor_positions: Dict[str, Dict[str, Any]] = {}
        self.operation_history: Dict[str, List[Dict[str, Any]]] = {}
        
    def join_project(self, project_id: str, user_id: str, user_name: str, websocket: WebSocket) -> str:
        """Join a collaborative project session."""
        session_id = str(uuid.uuid4())
        
        self.active_sessions[session_id] = {
            'project_id': project_id,
            'user_id': user_id,
            'user_name': user_name,
            'websocket': websocket,
            'joined_at': datetime.utcnow().isoformat(),
            'last_activity': datetime.utcnow().isoformat()
        }
        
        if project_id not in self.project_rooms:
            self.project_rooms[project_id] = []
        
        self.project_rooms[project_id].append(session_id)
        
        # Initialize cursor position
        if project_id not in self.cursor_positions:
            self.cursor_positions[project_id] = {}
        
        self.cursor_positions[project_id][user_id] = {
            'x': 0,
            'y': 0,
            'color': self._generate_user_color(user_id),
            'last_update': datetime.utcnow().isoformat()
        }
        
        return session_id
    
    def leave_project(self, session_id: str):
        """Leave a collaborative project session."""
        if session_id not in self.active_sessions:
            return
            
        session = self.active_sessions[session_id]
        project_id = session['project_id']
        user_id = session['user_id']
        
        # Clean up session
        del self.active_sessions[session_id]
        
        if project_id in self.project_rooms:
            self.project_rooms[project_id].remove(session_id)
            if not self.project_rooms[project_id]:
                del self.project_rooms[project_id]
        
        # Clean up cursor position
        if project_id in self.cursor_positions and user_id in self.cursor_positions[project_id]:
            del self.cursor_positions[project_id][user_id]
    
    async def broadcast_to_project(self, project_id: str, message: Dict[str, Any], exclude_session: Optional[str] = None):
        """Broadcast a message to all users in a project."""
        if project_id not in self.project_rooms:
            return
            
        for session_id in self.project_rooms[project_id]:
            if session_id == exclude_session:
                continue
                
            session = self.active_sessions[session_id]
            try:
                await session['websocket'].send_text(json.dumps(message))
            except Exception:
                # Handle disconnected clients
                self.leave_project(session_id)
    
    def get_project_users(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all users currently in a project."""
        if project_id not in self.project_rooms:
            return []
            
        users = []
        for session_id in self.project_rooms[project_id]:
            session = self.active_sessions[session_id]
            users.append({
                'user_id': session['user_id'],
                'user_name': session['user_name'],
                'joined_at': session['joined_at'],
                'last_activity': session['last_activity']
            })
        
        return users
    
    def _generate_user_color(self, user_id: str) -> str:
        """Generate a consistent color for a user."""
        colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', 
            '#FECA57', '#FF9FF3', '#54A0FF', '#5F27CD',
            '#00D2D3', '#FF9F43', '#10AC84', '#EE5A24'
        ]
        
        hash_value = sum(ord(c) for c in user_id)
        return colors[hash_value % len(colors)]
    
    def add_operation(self, project_id: str, operation: Dict[str, Any]):
        """Add an operation to the history."""
        if project_id not in self.operation_history:
            self.operation_history[project_id] = []
        
        operation['timestamp'] = datetime.utcnow().isoformat()
        operation['id'] = str(uuid.uuid4())
        
        self.operation_history[project_id].append(operation)
        
        # Keep only last 1000 operations
        if len(self.operation_history[project_id]) > 1000:
            self.operation_history[project_id] = self.operation_history[project_id][-1000:]
    
    def get_operation_history(self, project_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get operation history for a project."""
        if project_id not in self.operation_history:
            return []
        
        return self.operation_history[project_id][-limit:]

# Global collaboration manager
collaboration_manager = CollaborationManager()

@router.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    """WebSocket endpoint for real-time collaboration."""
    await websocket.accept()
    
    # Get user info (in a real app, this would come from auth)
    user_id = str(uuid.uuid4())
    user_name = f"User {user_id[:8]}"
    
    session_id = collaboration_manager.join_project(project_id, user_id, user_name, websocket)
    
    try:
        # Send initial state
        users = collaboration_manager.get_project_users(project_id)
        await websocket.send_text(json.dumps({
            'type': 'init',
            'user_id': user_id,
            'users': users,
            'cursor_positions': collaboration_manager.cursor_positions.get(project_id, {})
        }))
        
        # Notify others of new user
        await collaboration_manager.broadcast_to_project(project_id, {
            'type': 'user_joined',
            'user': {
                'user_id': user_id,
                'user_name': user_name,
                'joined_at': datetime.utcnow().isoformat()
            }
        }, exclude_session=session_id)
        
        # Handle incoming messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Update last activity
            collaboration_manager.active_sessions[session_id]['last_activity'] = datetime.utcnow().isoformat()
            
            message_type = message.get('type')
            
            if message_type == 'canvas_update':
                # Broadcast canvas update
                await collaboration_manager.broadcast_to_project(project_id, {
                    'type': 'canvas_update',
                    'user_id': user_id,
                    'user_name': user_name,
                    'update': message.get('update'),
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                # Add to operation history
                collaboration_manager.add_operation(project_id, {
                    'type': 'canvas_update',
                    'user_id': user_id,
                    'user_name': user_name,
                    'update': message.get('update')
                })
                
            elif message_type == 'cursor_move':
                # Update cursor position
                if project_id in collaboration_manager.cursor_positions:
                    collaboration_manager.cursor_positions[project_id][user_id] = {
                        **message.get('position', {}),
                        'color': collaboration_manager._generate_user_color(user_id),
                        'last_update': datetime.utcnow().isoformat()
                    }
                
                # Broadcast cursor position
                await collaboration_manager.broadcast_to_project(project_id, {
                    'type': 'cursor_move',
                    'user_id': user_id,
                    'user_name': user_name,
                    'position': message.get('position', {})
                })
                
            elif message_type == 'selection':
                # Broadcast selection changes
                await collaboration_manager.broadcast_to_project(project_id, {
                    'type': 'selection',
                    'user_id': user_id,
                    'user_name': user_name,
                    'selection': message.get('selection')
                })
                
            elif message_type == 'chat':
                # Broadcast chat message
                await collaboration_manager.broadcast_to_project(project_id, {
                    'type': 'chat',
                    'user_id': user_id,
                    'user_name': user_name,
                    'message': message.get('message'),
                    'timestamp': datetime.utcnow().isoformat()
                })
                
    except WebSocketDisconnect:
        pass
    finally:
        # Clean up on disconnect
        collaboration_manager.leave_project(session_id)
        
        # Notify others
        await collaboration_manager.broadcast_to_project(project_id, {
            'type': 'user_left',
            'user_id': user_id
        })

@router.get("/projects/{project_id}/users")
async def get_project_users(project_id: str):
    """Get all users currently in a project."""
    return {
        'users': collaboration_manager.get_project_users(project_id),
        'count': len(collaboration_manager.get_project_users(project_id))
    }

@router.get("/projects/{project_id}/history")
async def get_operation_history(project_id: str, limit: int = 100):
    """Get operation history for a project."""
    return {
        'history': collaboration_manager.get_operation_history(project_id, limit),
        'count': len(collaboration_manager.get_operation_history(project_id, limit))
    }