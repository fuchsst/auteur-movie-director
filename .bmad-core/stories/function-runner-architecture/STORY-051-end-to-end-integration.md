# Story: End-to-End Integration

**Story ID**: STORY-051  
**Epic**: EPIC-003-function-runner-architecture  
**Type**: Integration  
**Points**: 8 (Large)  
**Priority**: High  
**Status**: ✅ Completed  

## Story Description
As a platform engineer, I want complete end-to-end integration of all function runner components with the existing platform, ensuring seamless task submission from the UI through to result delivery with proper error handling, progress tracking, and resource management throughout the entire pipeline.

## Acceptance Criteria

### Functional Requirements
- [ ] Complete task flow from UI submission to result display
- [ ] Integration with existing project and asset management
- [ ] WebSocket events flow through entire pipeline
- [ ] File uploads integrate with storage service
- [ ] Results automatically saved to project structure
- [ ] Canvas nodes can submit function runner tasks
- [ ] Takes system captures function outputs
- [ ] Batch operations work across all components

### Technical Requirements
- [ ] Wire up all API endpoints with frontend client
- [ ] Integrate WebSocket events across all services
- [ ] Connect storage service with function outputs
- [ ] Link task results to takes system
- [ ] Implement service discovery and routing
- [ ] Add distributed tracing across services
- [ ] Create integration test harness
- [ ] Implement service health checks

### Quality Requirements
- [ ] End-to-end latency < 500ms overhead
- [ ] Zero message loss across service boundaries
- [ ] 99.9% uptime for integrated system
- [ ] Graceful degradation when services unavailable
- [ ] Support for 100+ concurrent workflows
- [ ] Integration points documented
- [ ] Performance monitoring across services

## Implementation Notes

### Service Integration Architecture
```python
class ServiceIntegrator:
    """Orchestrate integration between all platform services"""
    
    def __init__(self):
        self.services = {
            'function_runner': FunctionRunnerService(),
            'workspace': WorkspaceService(),
            'takes': TakesService(),
            'storage': StorageService(),
            'websocket': WebSocketService(),
            'git': GitService()
        }
        self.event_bus = EventBus()
        self.health_monitor = ServiceHealthMonitor()
        
    async def initialize(self):
        """Initialize all service connections"""
        
        # Start health monitoring
        await self.health_monitor.start()
        
        # Initialize services
        for name, service in self.services.items():
            try:
                await service.initialize()
                await self.health_monitor.register_service(name, service)
                logger.info(f"Initialized service: {name}")
            except Exception as e:
                logger.error(f"Failed to initialize {name}: {e}")
                raise
        
        # Set up event routing
        await self._setup_event_routing()
        
        # Verify integration
        await self._verify_integration()
    
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
```

### Integrated Task Submission Flow
```python
class IntegratedTaskSubmissionHandler:
    """Handle complete task submission flow"""
    
    async def submit_task(self, request: IntegratedTaskRequest) -> TaskResponse:
        """Submit task with full integration"""
        
        # 1. Validate project context
        project = await self._validate_project_context(request.project_id)
        
        # 2. Resolve asset references
        resolved_inputs = await self._resolve_asset_references(
            request.inputs,
            project
        )
        
        # 3. Create task tracking
        tracking_id = await self._create_task_tracking(
            project_id=request.project_id,
            user_id=request.user_id,
            task_type=request.template_id
        )
        
        # 4. Submit to function runner
        task = await self.function_runner.submit_task(
            template_id=request.template_id,
            inputs=resolved_inputs,
            quality=request.quality,
            metadata={
                'project_id': request.project_id,
                'tracking_id': tracking_id,
                'shot_id': request.shot_id,
                'user_id': request.user_id,
                'canvas_node_id': request.canvas_node_id
            }
        )
        
        # 5. Set up result handling
        task.on_complete = partial(
            self._handle_task_completion,
            project=project,
            request=request
        )
        
        # 6. Send initial notification
        await self._send_task_notification(
            'task_submitted',
            task_id=task.task_id,
            project_id=request.project_id,
            estimated_time=task.estimated_time
        )
        
        return TaskResponse(
            task_id=task.task_id,
            tracking_id=tracking_id,
            status='submitted',
            estimated_completion=task.estimated_time
        )
    
    async def _resolve_asset_references(self, 
                                      inputs: Dict[str, Any],
                                      project: Project) -> Dict[str, Any]:
        """Resolve asset references to actual file paths"""
        
        resolved = inputs.copy()
        
        for key, value in inputs.items():
            if isinstance(value, str) and value.startswith('asset://'):
                # Resolve asset reference
                asset_id = value[8:]  # Remove 'asset://' prefix
                asset_path = await self.workspace_service.resolve_asset(
                    project.id,
                    asset_id
                )
                resolved[key] = asset_path
            elif isinstance(value, dict):
                # Recursively resolve nested references
                resolved[key] = await self._resolve_asset_references(
                    value, project
                )
        
        return resolved
    
    async def _handle_task_completion(self,
                                    result: TaskResult,
                                    project: Project,
                                    request: IntegratedTaskRequest):
        """Handle completed task with full integration"""
        
        try:
            # 1. Store outputs in project structure
            stored_outputs = await self._store_outputs(
                result.outputs,
                project,
                request
            )
            
            # 2. Create take record
            take = await self._create_take(
                project_id=project.id,
                shot_id=request.shot_id,
                outputs=stored_outputs,
                metadata={
                    'task_id': result.task_id,
                    'template_id': request.template_id,
                    'quality': request.quality,
                    'generation_time': result.execution_time
                }
            )
            
            # 3. Update canvas node if applicable
            if request.canvas_node_id:
                await self._update_canvas_node(
                    request.canvas_node_id,
                    take_id=take.id,
                    outputs=stored_outputs
                )
            
            # 4. Commit to Git with LFS
            await self._commit_outputs_to_git(
                project, take, stored_outputs
            )
            
            # 5. Send completion notification
            await self._send_task_notification(
                'task_completed',
                task_id=result.task_id,
                project_id=project.id,
                take_id=take.id,
                outputs=stored_outputs
            )
            
        except Exception as e:
            logger.error(f"Failed to handle task completion: {e}")
            await self._send_task_notification(
                'task_failed',
                task_id=result.task_id,
                error=str(e)
            )
```

### WebSocket Integration Layer
```python
class WebSocketIntegrationLayer:
    """Integrate WebSocket events across all services"""
    
    def __init__(self, ws_manager: WebSocketManager):
        self.ws_manager = ws_manager
        self.event_handlers = {
            'task.progress': self._handle_task_progress,
            'task.completed': self._handle_task_completed,
            'take.created': self._handle_take_created,
            'asset.uploaded': self._handle_asset_uploaded
        }
    
    async def route_event(self, event: ServiceEvent):
        """Route service events to WebSocket clients"""
        
        # Determine event type and routing
        event_type = f"{event.service}.{event.type}"
        
        # Get handler
        handler = self.event_handlers.get(event_type)
        if not handler:
            handler = self._default_handler
        
        # Process event
        ws_event = await handler(event)
        
        # Send to appropriate clients
        if ws_event:
            await self._send_to_clients(ws_event, event.metadata)
    
    async def _handle_task_progress(self, event: ServiceEvent) -> WebSocketEvent:
        """Transform task progress event for WebSocket"""
        
        return WebSocketEvent(
            type='generation.progress',
            data={
                'taskId': event.data['task_id'],
                'progress': event.data['progress'],
                'stage': event.data['stage'],
                'message': event.data.get('message'),
                'preview': event.data.get('preview_url'),
                'eta': event.data.get('eta')
            }
        )
    
    async def _send_to_clients(self, 
                             ws_event: WebSocketEvent,
                             metadata: Dict[str, Any]):
        """Send event to appropriate WebSocket clients"""
        
        # Determine target clients
        if 'user_id' in metadata:
            # Send to specific user
            await self.ws_manager.send_to_user(
                metadata['user_id'],
                ws_event
            )
        elif 'project_id' in metadata:
            # Send to all users in project
            await self.ws_manager.send_to_project(
                metadata['project_id'],
                ws_event
            )
        else:
            # Broadcast to all
            await self.ws_manager.broadcast(ws_event)
```

### Storage Integration
```python
class StorageIntegration:
    """Integrate function outputs with storage service"""
    
    async def store_function_outputs(self,
                                   outputs: Dict[str, Any],
                                   project: Project,
                                   context: OutputContext) -> Dict[str, StoredFile]:
        """Store function outputs in project structure"""
        
        stored_files = {}
        
        for output_name, output_data in outputs.items():
            if output_data['type'] == 'file':
                # Determine storage path
                storage_path = self._determine_storage_path(
                    project, context, output_name, output_data
                )
                
                # Store file
                if 'url' in output_data:
                    # Download from URL
                    stored_file = await self.storage_service.download_and_store(
                        url=output_data['url'],
                        destination=storage_path,
                        metadata={
                            'source': 'function_runner',
                            'task_id': context.task_id,
                            'output_name': output_name
                        }
                    )
                elif 'data' in output_data:
                    # Store raw data
                    stored_file = await self.storage_service.store_data(
                        data=output_data['data'],
                        destination=storage_path,
                        content_type=output_data.get('content_type')
                    )
                
                stored_files[output_name] = stored_file
                
                # Track with Git LFS if large
                if stored_file.size > 10 * 1024 * 1024:  # 10MB
                    await self.git_lfs_service.track_file(
                        project.id,
                        stored_file.relative_path
                    )
        
        return stored_files
    
    def _determine_storage_path(self,
                              project: Project,
                              context: OutputContext,
                              output_name: str,
                              output_data: Dict) -> Path:
        """Determine where to store output file"""
        
        # Base path based on output type
        if context.shot_id:
            base_path = project.get_shot_path(context.shot_id)
        else:
            base_path = project.get_renders_path()
        
        # Add take directory
        take_dir = base_path / f"take_{context.take_number:03d}"
        
        # Determine filename
        extension = self._get_file_extension(output_data)
        filename = f"{output_name}_{context.timestamp}{extension}"
        
        return take_dir / filename
```

### Canvas Node Integration
```python
class CanvasNodeIntegration:
    """Integrate function runner with canvas nodes"""
    
    async def create_function_node(self,
                                 canvas_id: str,
                                 template_id: str,
                                 position: Dict[str, float]) -> CanvasNode:
        """Create a canvas node for a function template"""
        
        # Get template definition
        template = await self.template_registry.get_template(template_id)
        
        # Create node definition
        node_def = {
            'type': 'function',
            'template_id': template_id,
            'position': position,
            'inputs': self._create_node_inputs(template),
            'outputs': self._create_node_outputs(template),
            'properties': self._create_node_properties(template),
            'metadata': {
                'function_name': template.name,
                'category': template.category,
                'requires_gpu': template.requirements.get('gpu', False)
            }
        }
        
        # Create node in canvas
        node = await self.canvas_service.create_node(canvas_id, node_def)
        
        # Set up event handlers
        node.on_execute = partial(self._execute_function_node, template=template)
        node.on_cancel = self._cancel_function_node
        
        return node
    
    async def _execute_function_node(self,
                                   node: CanvasNode,
                                   inputs: Dict[str, Any],
                                   template: FunctionTemplate):
        """Execute a function node"""
        
        # Validate inputs
        validated_inputs = template.validate_inputs(inputs)
        
        # Get quality from node properties
        quality = node.properties.get('quality', 'standard')
        
        # Submit task
        task = await self.integrated_handler.submit_task(
            IntegratedTaskRequest(
                template_id=template.id,
                inputs=validated_inputs,
                quality=quality,
                project_id=node.canvas.project_id,
                canvas_node_id=node.id,
                user_id=node.canvas.user_id
            )
        )
        
        # Update node state
        node.state = 'executing'
        node.metadata['task_id'] = task.task_id
        
        # Set up progress updates
        task.on_progress = partial(
            self._update_node_progress,
            node=node
        )
        
        return task
```

### Integration Test Harness
```python
class IntegrationTestHarness:
    """Test harness for end-to-end integration testing"""
    
    def __init__(self):
        self.test_services = {}
        self.test_data = TestDataGenerator()
        self.assertions = IntegrationAssertions()
    
    async def setup_test_environment(self):
        """Set up integrated test environment"""
        
        # Start all services in test mode
        await self._start_test_services()
        
        # Create test data
        self.test_project = await self.test_data.create_test_project()
        self.test_user = await self.test_data.create_test_user()
        
        # Set up monitoring
        self.monitor = IntegrationMonitor()
        await self.monitor.start()
    
    async def test_complete_generation_flow(self):
        """Test complete generation flow end-to-end"""
        
        # 1. Create test inputs
        inputs = {
            'prompt': 'A beautiful sunset over mountains',
            'width': 512,
            'height': 512,
            'quality': 'standard'
        }
        
        # 2. Submit task through API
        response = await self.api_client.post(
            '/api/v1/functions/tasks',
            json={
                'template_id': 'image_generation_v1',
                'inputs': inputs,
                'project_id': self.test_project.id
            }
        )
        
        assert response.status_code == 200
        task_id = response.json()['task_id']
        
        # 3. Monitor WebSocket events
        events = []
        async with self.ws_client.connect(f'/ws/{self.test_user.id}') as ws:
            # Subscribe to task
            await ws.send_json({
                'type': 'subscribe',
                'task_ids': [task_id]
            })
            
            # Collect events
            async for message in ws:
                event = json.loads(message)
                events.append(event)
                
                if event['type'] == 'task.completed':
                    break
        
        # 4. Verify progress events
        progress_events = [e for e in events if e['type'] == 'task.progress']
        assert len(progress_events) > 0
        assert all(e['data']['task_id'] == task_id for e in progress_events)
        
        # 5. Verify take creation
        takes = await self.takes_service.list_takes(
            self.test_project.id,
            metadata_filter={'task_id': task_id}
        )
        assert len(takes) == 1
        take = takes[0]
        
        # 6. Verify file storage
        assert 'image' in take.outputs
        image_path = take.outputs['image']['path']
        assert await self.storage_service.file_exists(image_path)
        
        # 7. Verify Git commit
        commits = await self.git_service.get_recent_commits(
            self.test_project.id,
            limit=1
        )
        assert len(commits) == 1
        assert task_id in commits[0].message
        
        # 8. Verify complete data flow
        await self.assertions.assert_complete_data_flow(
            task_id=task_id,
            project_id=self.test_project.id,
            expected_outputs=['image']
        )
```

### Service Health Integration
```python
class ServiceHealthIntegration:
    """Integrate health monitoring across all services"""
    
    async def check_integration_health(self) -> IntegrationHealthReport:
        """Check health of all integration points"""
        
        checks = []
        
        # Check service connectivity
        for service_name in ['function_runner', 'workspace', 'takes', 'storage']:
            check = await self._check_service_connectivity(service_name)
            checks.append(check)
        
        # Check data flow
        flow_check = await self._check_data_flow()
        checks.append(flow_check)
        
        # Check event routing
        event_check = await self._check_event_routing()
        checks.append(event_check)
        
        # Calculate overall health
        healthy_checks = sum(1 for c in checks if c.status == 'healthy')
        overall_status = 'healthy' if healthy_checks == len(checks) else 'degraded'
        
        return IntegrationHealthReport(
            status=overall_status,
            checks=checks,
            timestamp=datetime.now()
        )
    
    async def _check_data_flow(self) -> HealthCheck:
        """Verify data can flow through entire pipeline"""
        
        try:
            # Submit minimal test task
            test_task = await self._submit_test_task()
            
            # Wait for completion (with timeout)
            result = await test_task.wait(timeout=30)
            
            # Verify result stored
            stored = await self._verify_result_stored(result)
            
            return HealthCheck(
                name='data_flow',
                status='healthy' if stored else 'unhealthy',
                message='Data flow test completed successfully' if stored else 'Result storage failed'
            )
            
        except Exception as e:
            return HealthCheck(
                name='data_flow',
                status='unhealthy',
                message=f'Data flow test failed: {str(e)}'
            )
```

## Dependencies
- All previous stories in EPIC-003
- **STORY-005**: WebSocket Service
- **STORY-021**: Takes System Implementation
- **STORY-026**: Git Integration
- All integration points must be implemented

## Testing Criteria
- [ ] End-to-end integration tests passing
- [ ] Load tests with 100+ concurrent workflows
- [ ] Service boundary tests
- [ ] Event routing tests
- [ ] Error propagation tests
- [ ] Performance tests across services
- [ ] Chaos engineering tests
- [ ] Data consistency tests

## Definition of Done
- [ ] All services integrated and communicating
- [ ] Complete task flow working end-to-end
- [ ] WebSocket events flowing correctly
- [ ] Storage integration working
- [ ] Takes system capturing outputs
- [ ] Canvas nodes can execute functions
- [ ] Health monitoring across services
- [ ] Integration tests comprehensive
- [ ] Performance meets requirements
- [ ] Documentation includes integration guide

## Story Links
- **Depends On**: All previous stories in EPIC-003
- **Blocks**: STORY-052 (Performance Testing Suite)
- **Related Epic**: EPIC-003-function-runner-architecture
- **Architecture Ref**: /concept/integration/service_integration.md