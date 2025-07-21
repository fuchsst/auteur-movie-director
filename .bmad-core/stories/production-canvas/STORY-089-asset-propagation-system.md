# User Story: STORY-089 - Asset Propagation System

## Story Description
**As a** filmmaker managing complex productions
**I want** a robust asset propagation system that ensures changes to source assets automatically update all dependent shots and sequences
**So that** I can maintain complete creative consistency across thousands of shots without manual intervention

## Acceptance Criteria

### Functional Requirements
- [ ] **AssetReference Pointer System** for dynamic asset linking
- [ ] **Change Propagation Engine** for automatic updates
- [ ] **Dependency Tracking** across all asset types
- [ ] **Version Control** for asset evolution
- [ ] **Rollback Capability** for asset changes
- [ ] **Conflict Resolution** for simultaneous updates
- [ ] **Propagation Rules Engine** for customizable behaviors
- [ ] **Real-time Sync** across all project views

### Technical Requirements
- [ ] **Asset Dependency Graph** construction and maintenance
- [ ] **Change Detection System** for asset modifications
- [ ] **Batch Update Processing** for large-scale changes
- [ ] **Conflict Detection** and resolution algorithms
- [ ] **Performance Optimization** for 1000+ asset dependencies
- [ ] **Cache Invalidation** for updated assets
- [ ] **Notification System** for change events
- [ ] **Audit Trail** for all propagation actions

### Quality Requirements
- [ ] **Propagation Accuracy** 99.9% success rate
- [ ] **Performance Testing** with 5000+ dependencies
- [ ] **Conflict Resolution** testing under load
- [ ] **Rollback Testing** for all scenarios
- [ ] **Consistency Validation** across all views
- [ ] **User Experience** testing for change management

## Implementation Notes

### Asset Propagation Architecture
```python
class AssetPropagationSystem:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.dependency_graph = DependencyGraph()
        self.change_detector = ChangeDetector()
        self.propagation_engine = PropagationEngine()
        self.version_manager = VersionManager()
        self.conflict_resolver = ConflictResolver()
    
    async def propagate_asset_change(self, asset_id: str, change_data: dict) -> PropagationResult:
        """Propagate asset change to all dependent entities"""
        
        # Detect change type and scope
        change_type = await self.change_detector.classify_change(change_data)
        
        # Get affected dependencies
        dependencies = await self.dependency_graph.get_dependencies(asset_id)
        
        # Check for conflicts
        conflicts = await self.conflict_resolver.detect_conflicts(asset_id, change_data)
        
        if conflicts:
            resolution = await self.conflict_resolver.resolve(conflicts)
            if resolution.requires_intervention:
                return PropagationResult(
                    status='conflict',
                    conflicts=conflicts,
                    requires_intervention=True
                )
        
        # Create new version
        new_version = await self.version_manager.create_version(asset_id, change_data)
        
        # Propagate changes
        propagation_plan = await self.propagation_engine.create_plan(
            asset_id, new_version, dependencies
        )
        
        # Execute propagation
        results = await self.propagation_engine.execute(propagation_plan)
        
        # Notify stakeholders
        await self.notify_stakeholders(asset_id, results)
        
        return PropagationResult(
            status='success',
            affected_entities=results['affected_count'],
            version=new_version.id
        )
```

### Dependency Graph System
```python
class DependencyGraph:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.index_cache = {}
    
    async def build_dependency_graph(self, project_data: dict) -> None:
        """Build complete dependency graph for project"""
        
        # Add all assets as nodes
        for asset_type in ['character', 'prop', 'wardrobe', 'location', 'style']:
            assets = project_data.get(f'{asset_type}s', [])
            for asset in assets:
                self.graph.add_node(
                    asset['id'],
                    type=asset_type,
                    data=asset
                )
        
        # Add dependency edges
        await self.add_asset_dependencies(project_data)
        await self.add_shot_dependencies(project_data)
        await self.add_sequence_dependencies(project_data)
    
    async def add_asset_dependencies(self, project_data: dict) -> None:
        """Add asset-to-asset dependencies"""
        
        for asset in project_data.get('assets', []):
            # Wardrobe depends on character
            if asset['type'] == 'wardrobe' and 'worn_by' in asset:
                self.graph.add_edge(asset['worn_by'], asset['id'])
            
            # Props used in locations
            if asset['type'] == 'prop' and 'used_in' in asset:
                for location_id in asset['used_in']:
                    self.graph.add_edge(location_id, asset['id'])
    
    async def add_shot_dependencies(self, project_data: dict) -> None:
        """Add shot-to-asset dependencies"""
        
        for shot in project_data.get('shots', []):
            shot_id = shot['shot_id']
            
            # Add character dependencies
            for char_ref in shot.get('visual_prompt', {}).get('character_references', []):
                self.graph.add_edge(char_ref['asset_id'], shot_id)
            
            # Add prop dependencies
            for prop_id in shot.get('visual_prompt', {}).get('prop_references', []):
                self.graph.add_edge(prop_id, shot_id)
            
            # Add wardrobe dependencies
            for wardrobe_ref in shot.get('visual_prompt', {}).get('wardrobe_references', []):
                self.graph.add_edge(wardrobe_ref['asset_id'], shot_id)
    
    async def get_dependencies(self, asset_id: str, depth: int = None) -> List[str]:
        """Get all entities dependent on this asset"""
        
        if depth:
            return list(nx.single_source_shortest_path_length(
                self.graph, asset_id, cutoff=depth
            ).keys())
        else:
            return list(nx.descendants(self.graph, asset_id))
    
    async def get_affected_shots(self, asset_id: str) -> List[str]:
        """Get all shots affected by this asset"""
        
        descendants = nx.descendants(self.graph, asset_id)
        return [node for node in descendants if node.startswith('shot-')]
```

### Change Detection and Processing
```python
class ChangeDetector:
    """Detects and classifies asset changes"""
    
    def __init__(self):
        self.change_classifiers = {
            'visual': VisualChangeClassifier(),
            'metadata': MetadataChangeClassifier(),
            'relationship': RelationshipChangeClassifier()
        }
    
    async def classify_change(self, asset_id: str, change_data: dict) -> ChangeClassification:
        """Classify the type and impact of a change"""
        
        classifications = []
        
        for classifier_type, classifier in self.change_classifiers.items():
            classification = await classifier.classify(change_data)
            if classification['is_relevant']:
                classifications.append(classification)
        
        # Determine overall impact
        impact_level = self.calculate_impact_level(classifications)
        
        return ChangeClassification(
            classifications=classifications,
            impact_level=impact_level,
            propagation_priority=self.get_propagation_priority(impact_level)
        )
    
    async def calculate_change_impact(self, asset_id: str, change_data: dict) -> ImpactAnalysis:
        """Calculate the impact of a change across the project"""
        
        affected_shots = await self.get_affected_shots(asset_id)
        affected_sequences = await self.get_affected_sequences(asset_id)
        
        impact = ImpactAnalysis(
            affected_shots=len(affected_shots),
            affected_sequences=len(affected_sequences),
            estimated_processing_time=self.estimate_processing_time(affected_shots),
            memory_impact=self.estimate_memory_impact(affected_shots),
            can_be_batch_processed=len(affected_shots) > 100
        )
        
        return impact
```

### Propagation Engine
```python
class PropagationEngine:
    """Executes asset change propagation"""
    
    def __init__(self):
        self.batch_processor = BatchProcessor()
        self.real_time_processor = RealTimeProcessor()
        self.cache_manager = CacheManager()
    
    async def create_propagation_plan(
        self, 
        asset_id: str, 
        new_version: AssetVersion, 
        dependencies: List[str]
    ) -> PropagationPlan:
        """Create detailed propagation plan"""
        
        plan = PropagationPlan(
            asset_id=asset_id,
            version=new_version,
            dependencies=dependencies,
            phases=[]
        )
        
        # Batch processing for large changes
        if len(dependencies) > 100:
            plan.phases.append(await self.create_batch_phase(dependencies))
        
        # Real-time processing for critical changes
        critical_deps = await self.identify_critical_dependencies(dependencies)
        if critical_deps:
            plan.phases.append(await self.create_realtime_phase(critical_deps))
        
        # Background processing for remaining changes
        remaining_deps = [d for d in dependencies if d not in critical_deps]
        if remaining_deps:
            plan.phases.append(await self.create_background_phase(remaining_deps))
        
        return plan
    
    async def execute_propagation(self, plan: PropagationPlan) -> PropagationResults:
        """Execute the propagation plan"""
        
        results = PropagationResults()
        
        for phase in plan.phases:
            if phase.type == 'batch':
                phase_result = await self.execute_batch_phase(phase)
            elif phase.type == 'realtime':
                phase_result = await self.execute_realtime_phase(phase)
            elif phase.type == 'background':
                phase_result = await self.execute_background_phase(phase)
            
            results.add_phase_result(phase_result)
        
        return results
    
    async def execute_batch_phase(self, phase: BatchPhase) -> PhaseResult:
        """Execute batch processing phase"""
        
        batch_size = 50  # Process 50 entities at a time
        batches = [phase.dependencies[i:i+batch_size] 
                  for i in range(0, len(phase.dependencies), batch_size)]
        
        for batch in batches:
            await self.process_batch(batch, phase.asset_id, phase.new_version)
            await asyncio.sleep(0.1)  # Prevent overwhelming the system
        
        return PhaseResult(
            type='batch',
            processed_count=len(phase.dependencies),
            errors=[]
        )
```

### Version Management System
```python
class VersionManager:
    """Manages asset versions and rollbacks"""
    
    def __init__(self, storage_backend: StorageBackend):
        self.storage = storage_backend
        self.version_store = VersionStore()
    
    async def create_version(self, asset_id: str, change_data: dict) -> AssetVersion:
        """Create new asset version"""
        
        previous_version = await self.get_current_version(asset_id)
        
        version = AssetVersion(
            id=f"{asset_id}_v{previous_version.number + 1}",
            asset_id=asset_id,
            number=previous_version.number + 1,
            changes=change_data,
            previous_version=previous_version.id,
            timestamp=datetime.utcnow(),
            author=change_data.get('author', 'system'),
            checksum=await self.calculate_checksum(change_data)
        )
        
        await self.version_store.save(version)
        await self.mark_as_current(version)
        
        return version
    
    async def rollback_to_version(self, asset_id: str, version_number: int) -> RollbackResult:
        """Rollback to specific version"""
        
        target_version = await self.version_store.get_version(
            asset_id, version_number
        )
        
        if not target_version:
            raise ValueError(f"Version {version_number} not found")
        
        # Create rollback plan
        rollback_plan = await self.create_rollback_plan(target_version)
        
        # Execute rollback
        results = await self.execute_rollback(rollback_plan)
        
        return RollbackResult(
            success=True,
            affected_entities=results['affected_count'],
            new_current_version=target_version.id
        )
    
    async def create_rollback_plan(self, target_version: AssetVersion) -> RollbackPlan:
        """Create detailed rollback plan"""
        
        # Get all versions between current and target
        versions_to_rollback = await self.get_versions_between(
            target_version.asset_id,
            target_version.number
        )
        
        # Calculate affected entities
        affected_entities = []
        for version in versions_to_rollback:
            affected = await self.get_affected_entities(version)
            affected_entities.extend(affected)
        
        return RollbackPlan(
            target_version=target_version,
            affected_entities=list(set(affected_entities)),
            rollback_steps=self.generate_rollback_steps(versions_to_rollback)
        )
```

### Conflict Resolution System
```python
class ConflictResolver:
    """Resolves conflicts during asset changes"""
    
    def __init__(self):
        self.resolution_strategies = {
            'simultaneous_edit': SimultaneousEditResolver(),
            'version_conflict': VersionConflictResolver(),
            'dependency_conflict': DependencyConflictResolver()
        }
    
    async def detect_conflicts(self, asset_id: str, change_data: dict) -> List[Conflict]:
        """Detect potential conflicts"""
        
        conflicts = []
        
        # Check for simultaneous edits
        simultaneous_conflict = await self.check_simultaneous_edits(asset_id)
        if simultaneous_conflict:
            conflicts.append(simultaneous_conflict)
        
        # Check for version conflicts
        version_conflict = await self.check_version_conflicts(asset_id, change_data)
        if version_conflict:
            conflicts.append(version_conflict)
        
        # Check for dependency conflicts
        dependency_conflict = await self.check_dependency_conflicts(asset_id, change_data)
        if dependency_conflict:
            conflicts.append(dependency_conflict)
        
        return conflicts
    
    async def resolve(self, conflicts: List[Conflict]) -> ConflictResolution:
        """Resolve detected conflicts"""
        
        resolution = ConflictResolution(
            conflicts=conflicts,
            resolved=0,
            requires_intervention=False
        )
        
        for conflict in conflicts:
            strategy = self.get_resolution_strategy(conflict.type)
            result = await strategy.resolve(conflict)
            
            if result['resolved']:
                resolution.resolved += 1
            else:
                resolution.requires_intervention = True
                resolution.unresolved_conflicts.append(conflict)
        
        return resolution
    
    async def check_simultaneous_edits(self, asset_id: str) -> Optional[Conflict]:
        """Check for simultaneous edits"""
        
        active_sessions = await self.get_active_sessions(asset_id)
        if len(active_sessions) > 1:
            return Conflict(
                type='simultaneous_edit',
                severity='medium',
                description=f"{len(active_sessions)} users editing simultaneously",
                affected_users=active_sessions,
                resolution_options=['merge', 'manual_resolution']
            )
        
        return None
```

### Real-time Synchronization
```python
class RealTimeSyncManager:
    """Manages real-time synchronization across all views"""
    
    def __init__(self):
        self.websocket_manager = WebSocketManager()
        self.event_bus = EventBus()
        self.subscription_manager = SubscriptionManager()
    
    async def start_real_time_sync(self, project_id: str) -> None:
        """Start real-time synchronization for project"""
        
        # Subscribe to asset change events
        await self.event_bus.subscribe('asset_changed', self.handle_asset_change)
        await self.event_bus.subscribe('version_created', self.handle_version_created)
        await self.event_bus.subscribe('rollback_completed', self.handle_rollback)
        
        # Initialize WebSocket connections
        await self.websocket_manager.initialize_project(project_id)
    
    async def handle_asset_change(self, event: AssetChangeEvent) -> None:
        """Handle asset change events"""
        
        # Get affected users
        affected_users = await self.subscription_manager.get_subscribers(event.asset_id)
        
        # Create update payload
        update_payload = {
            'type': 'asset_update',
            'asset_id': event.asset_id,
            'change_type': event.change_type,
            'affected_entities': event.affected_entities,
            'timestamp': event.timestamp
        }
        
        # Broadcast to affected users
        for user_id in affected_users:
            await self.websocket_manager.send_to_user(user_id, update_payload)
    
    async def broadcast_propagation_progress(self, asset_id: str, progress: dict) -> None:
        """Broadcast propagation progress"""
        
        progress_update = {
            'type': 'propagation_progress',
            'asset_id': asset_id,
            'progress': progress['percentage'],
            'processed': progress['processed_count'],
            'total': progress['total_count'],
            'eta': progress['estimated_completion']
        }
        
        await self.websocket_manager.broadcast_to_project(
            self.get_project_id(asset_id), 
            progress_update
        )
```

### Performance Optimization
```python
class PerformanceOptimizer:
    """Optimizes asset propagation performance"""
    
    def __init__(self):
        self.cache_manager = CacheManager()
        self.batch_optimizer = BatchOptimizer()
        self.index_manager = IndexManager()
    
    async def optimize_propagation(self, asset_id: str, dependencies: List[str]) -> OptimizedPlan:
        """Create optimized propagation plan"""
        
        # Analyze dependency patterns
        patterns = await self.analyze_dependency_patterns(dependencies)
        
        # Optimize batch sizes
        optimized_batches = await self.batch_optimizer.create_batches(
            dependencies, patterns
        )
        
        # Optimize cache usage
        cache_strategy = await self.cache_manager.create_strategy(
            asset_id, dependencies
        )
        
        # Create optimized indices
        indices = await self.index_manager.create_indices(dependencies)
        
        return OptimizedPlan(
            batches=optimized_batches,
            cache_strategy=cache_strategy,
            indices=indices,
            estimated_time=self.calculate_estimated_time(optimized_batches)
        )
    
    async def benchmark_performance(self, project_id: str) -> PerformanceReport:
        """Benchmark propagation performance"""
        
        test_scenarios = [
            {'assets': 100, 'dependencies': 1000},
            {'assets': 500, 'dependencies': 5000},
            {'assets': 1000, 'dependencies': 10000}
        ]
        
        results = []
        for scenario in test_scenarios:
            result = await self.run_performance_test(scenario)
            results.append(result)
        
        return PerformanceReport(
            scenarios=results,
            recommendations=self.generate_recommendations(results)
        )
```

### Testing Strategy

#### Comprehensive Propagation Testing
```python
class AssetPropagationTests:
    async def test_basic_propagation():
        system = AssetPropagationSystem("test-project")
        
        # Create test asset
        asset = await system.create_test_asset("character", "Test Character")
        
        # Create dependent shots
        shots = await system.create_test_shots(10, asset['id'])
        
        # Change asset
        change_data = {'description': 'Updated description'}
        result = await system.propagate_asset_change(asset['id'], change_data)
        
        assert result.status == 'success'
        assert result.affected_entities == 10
    
    async def test_rollback_functionality():
        system = AssetPropagationSystem("test-project")
        
        # Create asset and shots
        asset = await system.create_test_asset("prop", "Test Prop")
        shots = await system.create_test_shots(5, asset['id'])
        
        # Make changes
        original_desc = asset['description']
        await system.propagate_asset_change(asset['id'], {'description': 'Changed'})
        
        # Rollback
        rollback_result = await system.rollback_to_version(
            asset['id'], 
            original_version=1
        )
        
        assert rollback_result.success is True
        assert rollback_result.affected_entities == 5
    
    async def test_performance_under_load():
        system = AssetPropagationSystem("test-project")
        
        # Create large dependency graph
        asset = await system.create_test_asset("character", "Load Test Character")
        shots = await system.create_test_shots(1000, asset['id'])
        
        # Measure propagation time
        start_time = time.time()
        result = await system.propagate_asset_change(
            asset['id'], 
            {'description': 'Performance test'}
        )
        end_time = time.time()
        
        assert result.status == 'success'
        assert result.affected_entities == 1000
        assert (end_time - start_time) < 60  # Under 1 minute for 1000 dependencies
```

### API Endpoints

#### Asset Propagation
```python
POST /api/v1/assets/{asset_id}/propagate
{
  "change_data": {
    "description": "Updated character description",
    "visual_changes": {...}
  },
  "propagation_mode": "realtime",
  "notify_users": true
}

GET /api/v1/assets/{asset_id}/dependencies
{
  "depth": 2,
  "include_shots": true
}

POST /api/v1/assets/{asset_id}/rollback
{
  "version_number": 5,
  "reason": "Reverted to original design"
}

GET /api/v1/projects/{project_id}/propagation-status

POST /api/v1/propagation/batch
{
  "asset_changes": [
    {"asset_id": "char-001", "changes": {...}},
    {"asset_id": "prop-002", "changes": {...}}
  ]
}
```

## Story Size: **Large (13 story points)**

## Sprint Assignment: **Sprint 7-8 (Phase 4)**

## Dependencies
- **STORY-083**: Expanded Asset System for asset storage
- **STORY-084**: Structured GenerativeShotList for shot dependencies
- **STORY-085**: Agent Integration Bridge for change coordination
- **STORY-086**: Breakdown View Interface for change management
- **STORY-087**: Storyboard integration for visual consistency
- **Graph Database**: Dependency graph storage
- **Cache System**: Performance optimization
- **WebSocket**: Real-time synchronization

## Success Criteria
- Asset changes propagate to 1000+ dependents in < 60 seconds
- Dependency graph accurately tracks all relationships
- Rollback functionality works for all scenarios
- Conflict resolution handles 95%+ of cases automatically
- Real-time sync latency < 100ms
- Version control maintains complete audit trail
- Performance tested with 5000+ dependencies
- User acceptance testing passed for change management
- Cross-platform consistency verified

## Future Enhancements
- **Distributed Propagation**: Multi-server scaling
- **AI Change Prediction**: ML-based change impact prediction
- **Collaborative Editing**: Multi-user simultaneous changes
- **Cloud Sync**: Cross-device synchronization
- **Advanced Analytics**: Change pattern analysis
- **Integration APIs**: Third-party asset management systems