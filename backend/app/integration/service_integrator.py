"""
Service Integrator

Orchestrates integration between all platform services.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .models import ServiceEvent, IntegrationError, ServiceUnavailableError
from ..services.workspace import WorkspaceService
from ..services.takes import TakesService
from ..services.git import GitService
from ..api.websocket import WebSocketManager

logger = logging.getLogger(__name__)


class EventBus:
    """Simple event bus for service communication"""
    
    def __init__(self):
        self._subscribers: Dict[str, List[callable]] = {}
        self._running = False
        self._event_queue = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the event bus"""
        if self._running:
            return
        
        self._running = True
        self._worker_task = asyncio.create_task(self._event_worker())
        logger.info("Event bus started")
    
    async def stop(self):
        """Stop the event bus"""
        self._running = False
        
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Event bus stopped")
    
    def subscribe(self, pattern: str, handler: callable):
        """Subscribe to events matching pattern"""
        if pattern not in self._subscribers:
            self._subscribers[pattern] = []
        
        self._subscribers[pattern].append(handler)
        logger.debug(f"Subscribed to {pattern}")
    
    def unsubscribe(self, pattern: str, handler: callable):
        """Unsubscribe from events"""
        if pattern in self._subscribers:
            try:
                self._subscribers[pattern].remove(handler)
                if not self._subscribers[pattern]:
                    del self._subscribers[pattern]
                logger.debug(f"Unsubscribed from {pattern}")
            except ValueError:
                pass
    
    async def publish(self, event: ServiceEvent):
        """Publish an event"""
        if self._running:
            await self._event_queue.put(event)
    
    async def _event_worker(self):
        """Process events in the background"""
        while self._running:
            try:
                # Wait for event with timeout
                event = await asyncio.wait_for(
                    self._event_queue.get(), 
                    timeout=1.0
                )
                
                await self._process_event(event)
                
            except asyncio.TimeoutError:
                # Normal timeout, continue
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}")
    
    async def _process_event(self, event: ServiceEvent):
        """Process a single event"""
        event_type = f"{event.service}.{event.type}"
        
        # Find matching subscribers
        handlers = []
        for pattern, pattern_handlers in self._subscribers.items():
            if self._pattern_matches(pattern, event_type):
                handlers.extend(pattern_handlers)
        
        # Call handlers
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")
    
    def _pattern_matches(self, pattern: str, event_type: str) -> bool:
        """Check if pattern matches event type"""
        # Simple wildcard matching
        if '*' in pattern:
            parts = pattern.split('*')
            if len(parts) == 2:
                prefix, suffix = parts
                return event_type.startswith(prefix) and event_type.endswith(suffix)
        
        return pattern == event_type


class ServiceHealthMonitor:
    """Monitor health of integrated services"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._health_checks: Dict[str, callable] = {}
        self._running = False
        self._check_interval = 30.0  # seconds
        self._monitor_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start health monitoring"""
        if self._running:
            return
        
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Service health monitor started")
    
    async def stop(self):
        """Stop health monitoring"""
        self._running = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Service health monitor stopped")
    
    async def register_service(self, name: str, service: Any, health_check: callable = None):
        """Register a service for monitoring"""
        self._services[name] = service
        
        if health_check:
            self._health_checks[name] = health_check
        elif hasattr(service, 'health_check'):
            self._health_checks[name] = service.health_check
        
        logger.info(f"Registered service: {name}")
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self._running:
            try:
                await self._check_all_services()
                await asyncio.sleep(self._check_interval)
            except Exception as e:
                logger.error(f"Error in health monitoring: {e}")
                await asyncio.sleep(self._check_interval)
    
    async def _check_all_services(self):
        """Check health of all registered services"""
        for name, service in self._services.items():
            try:
                health_check = self._health_checks.get(name)
                
                if health_check:
                    if asyncio.iscoroutinefunction(health_check):
                        is_healthy = await health_check()
                    else:
                        is_healthy = health_check()
                    
                    if not is_healthy:
                        logger.warning(f"Service {name} health check failed")
                        # Could trigger alerts or recovery actions here
                
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")


class ServiceIntegrator:
    """Orchestrate integration between all platform services"""
    
    def __init__(self):
        self.services = {}
        self.event_bus = EventBus()
        self.health_monitor = ServiceHealthMonitor()
        self._initialized = False
    
    async def initialize(self):
        """Initialize all service connections"""
        if self._initialized:
            return
        
        logger.info("Initializing Service Integrator")
        
        try:
            # Initialize core services
            await self._initialize_core_services()
            
            # Start event bus
            await self.event_bus.start()
            
            # Set up event routing
            await self._setup_event_routing()
            
            # Start health monitoring
            await self.health_monitor.start()
            
            # Verify integration
            await self._verify_integration()
            
            self._initialized = True
            logger.info("Service Integrator initialization complete")
            
        except Exception as e:
            logger.error(f"Failed to initialize Service Integrator: {e}")
            raise IntegrationError(f"Initialization failed: {e}")
    
    async def _initialize_core_services(self):
        """Initialize all core services"""
        
        # Initialize workspace service
        self.services['workspace'] = WorkspaceService()
        if hasattr(self.services['workspace'], 'initialize'):
            await self.services['workspace'].initialize()
        
        # Initialize takes service
        self.services['takes'] = TakesService()
        if hasattr(self.services['takes'], 'initialize'):
            await self.services['takes'].initialize()
        
        # Initialize Git service
        self.services['git'] = GitService()
        if hasattr(self.services['git'], 'initialize'):
            await self.services['git'].initialize()
        
        # Initialize WebSocket manager
        self.services['websocket'] = WebSocketManager()
        if hasattr(self.services['websocket'], 'initialize'):
            await self.services['websocket'].initialize()
        
        # Register services with health monitor
        for name, service in self.services.items():
            await self.health_monitor.register_service(name, service)
        
        logger.info("Core services initialized")
    
    async def _setup_event_routing(self):
        """Configure event routing between services"""
        
        # Function runner events -> WebSocket
        self.event_bus.subscribe(
            'function_runner.task.*',
            self._route_to_websocket
        )
        
        # Function runner results -> Takes system
        self.event_bus.subscribe(
            'function_runner.task.completed',
            self._create_take_from_result
        )
        
        # Storage events -> Function runner
        self.event_bus.subscribe(
            'storage.file.uploaded',
            self._notify_function_runner
        )
        
        # Takes events -> Git
        self.event_bus.subscribe(
            'takes.created',
            self._commit_take_to_git
        )
        
        # Health events -> WebSocket
        self.event_bus.subscribe(
            'health.*',
            self._route_health_to_websocket
        )
        
        logger.info("Event routing configured")
    
    async def _route_to_websocket(self, event: ServiceEvent):
        """Route events to WebSocket clients"""
        try:
            websocket_service = self.services.get('websocket')
            if websocket_service:
                # Transform event for WebSocket
                ws_message = {
                    'type': f"{event.service}.{event.type}",
                    'data': event.data,
                    'timestamp': event.timestamp.isoformat()
                }
                
                # Route based on metadata
                if 'user_id' in event.metadata:
                    await websocket_service.send_to_user(
                        event.metadata['user_id'], 
                        ws_message
                    )
                elif 'project_id' in event.metadata:
                    await websocket_service.send_to_project(
                        event.metadata['project_id'], 
                        ws_message
                    )
                else:
                    await websocket_service.broadcast(ws_message)
                
                logger.debug(f"Routed event to WebSocket: {event.service}.{event.type}")
        
        except Exception as e:
            logger.error(f"Error routing to WebSocket: {e}")
    
    async def _create_take_from_result(self, event: ServiceEvent):
        """Create take from function runner result"""
        try:
            takes_service = self.services.get('takes')
            if not takes_service:
                return
            
            data = event.data
            metadata = event.metadata
            
            # Extract take information
            project_id = metadata.get('project_id')
            shot_id = metadata.get('shot_id')
            
            if not project_id:
                logger.warning("No project_id in task completion event")
                return
            
            # Create take
            take_data = {
                'outputs': data.get('outputs', {}),
                'metadata': {
                    'task_id': data.get('task_id'),
                    'execution_time': data.get('execution_time'),
                    'template_id': metadata.get('template_id'),
                    'quality': metadata.get('quality'),
                    'user_id': metadata.get('user_id')
                }
            }
            
            if shot_id:
                take = await takes_service.create_take(
                    project_id=project_id,
                    shot_id=shot_id,
                    **take_data
                )
            else:
                take = await takes_service.create_take(
                    project_id=project_id,
                    **take_data
                )
            
            # Publish take creation event
            await self.event_bus.publish(ServiceEvent(
                service='takes',
                type='created',
                data={
                    'take_id': take.id,
                    'project_id': project_id,
                    'shot_id': shot_id,
                    'outputs': take.outputs
                },
                metadata=metadata
            ))
            
            logger.info(f"Created take {take.id} from task result")
        
        except Exception as e:
            logger.error(f"Error creating take from result: {e}")
    
    async def _commit_take_to_git(self, event: ServiceEvent):
        """Commit take to Git repository"""
        try:
            git_service = self.services.get('git')
            if not git_service:
                return
            
            data = event.data
            metadata = event.metadata
            
            project_id = data.get('project_id')
            take_id = data.get('take_id')
            
            if not project_id or not take_id:
                return
            
            # Commit the take
            commit_message = f"Add take {take_id}"
            if 'template_id' in metadata:
                commit_message += f" - {metadata['template_id']}"
            
            await git_service.commit_changes(
                project_id,
                message=commit_message,
                include_patterns=[f"**/take_*/**"]
            )
            
            logger.info(f"Committed take {take_id} to Git")
        
        except Exception as e:
            logger.error(f"Error committing take to Git: {e}")
    
    async def _notify_function_runner(self, event: ServiceEvent):
        """Notify function runner of storage events"""
        try:
            # This would notify the function runner that a file is available
            logger.debug(f"File uploaded: {event.data}")
        
        except Exception as e:
            logger.error(f"Error notifying function runner: {e}")
    
    async def _route_health_to_websocket(self, event: ServiceEvent):
        """Route health events to WebSocket"""
        try:
            # Only send to admin users
            ws_message = {
                'type': 'system.health',
                'data': event.data,
                'timestamp': event.timestamp.isoformat()
            }
            
            websocket_service = self.services.get('websocket')
            if websocket_service:
                # Add admin filter
                ws_message['admin_only'] = True
                await websocket_service.broadcast(ws_message)
        
        except Exception as e:
            logger.error(f"Error routing health to WebSocket: {e}")
    
    async def _verify_integration(self):
        """Verify that integration is working"""
        
        # Test event routing
        test_event = ServiceEvent(
            service='test',
            type='integration_check',
            data={'message': 'Integration test'},
            metadata={'test': True}
        )
        
        await self.event_bus.publish(test_event)
        
        # Wait a moment for processing
        await asyncio.sleep(0.1)
        
        logger.info("Integration verification complete")
    
    async def publish_event(self, event: ServiceEvent):
        """Publish an event to the bus"""
        await self.event_bus.publish(event)
    
    async def get_service(self, name: str) -> Optional[Any]:
        """Get a service by name"""
        return self.services.get(name)
    
    async def get_service_health(self) -> Dict[str, Any]:
        """Get health status of all services"""
        
        health_status = {}
        
        for name, service in self.services.items():
            try:
                # Try to check service health
                if hasattr(service, 'health_check'):
                    if asyncio.iscoroutinefunction(service.health_check):
                        is_healthy = await service.health_check()
                    else:
                        is_healthy = service.health_check()
                    
                    health_status[name] = 'healthy' if is_healthy else 'unhealthy'
                else:
                    # Assume healthy if no check method
                    health_status[name] = 'healthy'
            
            except Exception as e:
                health_status[name] = f'error: {str(e)}'
        
        return health_status
    
    async def shutdown(self):
        """Shutdown the service integrator"""
        
        logger.info("Shutting down Service Integrator")
        
        try:
            # Stop health monitoring
            await self.health_monitor.stop()
            
            # Stop event bus
            await self.event_bus.stop()
            
            # Shutdown services
            for name, service in self.services.items():
                try:
                    if hasattr(service, 'shutdown'):
                        if asyncio.iscoroutinefunction(service.shutdown):
                            await service.shutdown()
                        else:
                            service.shutdown()
                except Exception as e:
                    logger.error(f"Error shutting down {name}: {e}")
            
            self._initialized = False
            logger.info("Service Integrator shutdown complete")
        
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            raise