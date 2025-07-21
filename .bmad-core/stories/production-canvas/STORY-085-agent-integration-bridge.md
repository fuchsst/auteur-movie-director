# User Story: STORY-085 - Agent Integration Bridge

## Story Description
**As a** filmmaker using agentic workflows
**I want** seamless integration between specialized AI agents and the video assembly pipeline
**So that** agent-generated content flows directly into professional production workflows without manual intervention

## Acceptance Criteria

### Functional Requirements
- [ ] **Agent API Bridge** for Prop Master, Costume Designer, VFX Supervisor agents
- [ ] **AssetReference Resolution** from agent outputs to video assembly
- [ ] **Checkpoint System** for agentic revisions and rollbacks
- [ ] **Real-time Integration** with agentic crew workflows
- [ ] **Validation Pipeline** for agent-generated shot lists
- [ ] **Conflict Resolution** for overlapping agent recommendations
- [ ] **Progress Tracking** for agentic workflow stages
- [ ] **Human Approval Gates** at critical integration points

### Technical Requirements
- [ ] **Agent Communication Protocol** (REST/WebSocket)
- [ ] **Asset Registry Integration** for agent-generated assets
- [ ] **Shot List Transformation** from agent format to GenerativeShotList
- [ ] **Dependency Management** for agent-generated sequences
- [ ] **Error Handling** for agent workflow failures
- [ ] **State Synchronization** between agents and assembly pipeline
- [ ] **Version Control** for agentic iterations
- [ ] **Performance Optimization** for real-time agent integration

### Quality Requirements
- [ ] **Integration Testing** with all agent types
- [ ] **Asset Consistency Validation** across agent outputs
- [ ] **Performance Testing** under agent load
- [ ] **Error Recovery Testing** for agent failures
- [ ] **User Experience Testing** for approval workflows
- [ ] **Cross-agent Conflict Resolution** testing

## Implementation Notes

### Agent Architecture Integration
```python
class AgentIntegrationBridge:
    def __init__(self, project_id: str, agent_registry: dict):
        self.project_id = project_id
        self.agent_registry = agent_registry
        self.asset_bridge = AssetBridge()
        self.shot_transformer = ShotTransformer()
        self.checkpoint_manager = CheckpointManager()
    
    async def process_agent_output(self, agent_type: str, agent_output: dict) -> dict:
        """Process output from any specialized agent"""
        processor = self.get_agent_processor(agent_type)
        return await processor.process(agent_output)
    
    def get_agent_processor(self, agent_type: str):
        processors = {
            "prop_master": PropMasterProcessor(),
            "costume_designer": CostumeDesignerProcessor(),
            "vfx_supervisor": VFXSupervisorProcessor(),
            "dramaturg": DramaturgProcessor()
        }
        return processors[agent_type]

class PropMasterProcessor:
    def __init__(self):
        self.asset_creator = AssetCreator()
        self.validator = AssetValidator()
    
    async def process(self, agent_output: dict) -> dict:
        """Process Prop Master agent output"""
        props = agent_output.get("props", [])
        created_assets = []
        
        for prop_data in props:
            asset = self.asset_creator.create_prop_asset(prop_data)
            validated = self.validator.validate_prop_asset(asset)
            
            if validated:
                created_assets.append(asset)
                await self.notify_assembly_pipeline(asset)
        
        return {
            "success": True,
            "created_assets": created_assets,
            "total_processed": len(props)
        }
```

### Agent Communication Protocol
```python
class AgentCommunicationProtocol:
    def __init__(self):
        self.message_types = {
            "asset_creation": "Create new asset from agent",
            "shot_modification": "Modify existing shot",
            "metadata_update": "Update shot metadata",
            "validation_request": "Validate agent output",
            "approval_request": "Request human approval"
        }
    
    async def send_to_agent(self, agent_type: str, message: dict) -> dict:
        """Send message to specific agent"""
        endpoint = f"ws://agent-{agent_type}.auteur.local/api/v1/process"
        
        async with websockets.connect(endpoint) as websocket:
            await websocket.send(json.dumps(message))
            response = await websocket.recv()
            return json.loads(response)
    
    async def broadcast_to_crew(self, crew_data: dict) -> list:
        """Broadcast to entire agentic crew"""
        tasks = []
        for agent_type in ["prop_master", "costume_designer", "vfx_supervisor"]:
            task = self.send_to_agent(agent_type, crew_data)
            tasks.append(task)
        
        return await asyncio.gather(*tasks)
```

### Asset Transformation Pipeline
```python
class AssetTransformer:
    def __init__(self):
        self.transformers = {
            "prop": PropTransformer(),
            "wardrobe": WardrobeTransformer(),
            "character": CharacterTransformer(),
            "location": LocationTransformer()
        }
    
    def transform_agent_asset(self, agent_asset: dict, asset_type: str) -> dict:
        """Transform agent asset to system asset format"""
        transformer = self.transformers[asset_type]
        return transformer.transform(agent_asset)

class PropTransformer:
    def transform(self, agent_prop: dict) -> dict:
        """Transform Prop Master output to system PropAsset"""
        return {
            "assetId": f"prop-{uuid.uuid4()}",
            "name": agent_prop["name"],
            "description": agent_prop["description"],
            "category": agent_prop.get("category", "general"),
            "referenceImages": agent_prop.get("images", []),
            "triggerWord": agent_prop.get("trigger", ""),
            "tags": agent_prop.get("tags", []),
            "createdAt": datetime.utcnow().isoformat(),
            "source_agent": "prop_master",
            "confidence": agent_prop.get("confidence", 0.8)
        }
```

### Checkpoint and Rollback System
```python
class CheckpointManager:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.checkpoint_storage = CheckpointStorage()
    
    async def create_checkpoint(self, agent_outputs: dict, stage: str) -> str:
        """Create checkpoint for agentic workflow stage"""
        checkpoint = {
            "checkpoint_id": str(uuid.uuid4()),
            "project_id": self.project_id,
            "stage": stage,
            "timestamp": datetime.utcnow().isoformat(),
            "agent_outputs": agent_outputs,
            "asset_state": await self.get_current_asset_state(),
            "shot_list_state": await self.get_current_shot_list()
        }
        
        return self.checkpoint_storage.save(checkpoint)
    
    async def rollback_to_checkpoint(self, checkpoint_id: str) -> bool:
        """Rollback to previous agentic workflow state"""
        checkpoint = self.checkpoint_storage.load(checkpoint_id)
        
        # Restore asset state
        await self.restore_asset_state(checkpoint["asset_state"])
        
        # Restore shot list state
        await self.restore_shot_list_state(checkpoint["shot_list_state"])
        
        # Notify agents of rollback
        await self.notify_agents_rollback(checkpoint_id)
        
        return True
```

### Shot List Transformation
```python
class ShotTransformer:
    def __init__(self):
        self.asset_resolver = AssetResolver()
        self.emotional_mapper = EmotionalBeatMapper()
    
    def transform_agent_shot(self, agent_shot: dict) -> dict:
        """Transform agent shot to GenerativeShotList format"""
        return {
            "shot_id": f"shot-{uuid.uuid4()}",
            "shot_description": agent_shot["description"],
            "emotional_beat_ref": self.emotional_mapper.map_beat(agent_shot["emotional_context"]),
            "emotional_intensity": agent_shot.get("intensity", 0.5),
            "visual_prompt": self.build_visual_prompt(agent_shot),
            "audio_prompt": self.build_audio_prompt(agent_shot),
            "dependencies": agent_shot.get("dependencies", []),
            "metadata": {
                "source_agent": agent_shot["agent_type"],
                "confidence": agent_shot.get("confidence", 0.8),
                "created_at": datetime.utcnow().isoformat()
            }
        }
    
    def build_visual_prompt(self, agent_shot: dict) -> dict:
        """Build visual prompt from agent data"""
        return {
            "base_text": agent_shot["visual_description"],
            "character_references": self.resolve_character_refs(agent_shot.get("characters", [])),
            "wardrobe_references": self.resolve_wardrobe_refs(agent_shot.get("wardrobe", [])),
            "prop_references": self.resolve_prop_refs(agent_shot.get("props", [])),
            "style_reference": self.resolve_style_ref(agent_shot.get("style", {})),
            "camera_setup": self.build_camera_setup(agent_shot.get("camera", {})),
            "sfx_flags": self.build_sfx_flags(agent_shot.get("effects", [])),
            "gen_params": self.build_gen_params(agent_shot.get("quality", {}))
        }
```

### Validation Pipeline
```python
class AgentValidationPipeline:
    def __init__(self):
        self.validators = [
            AssetConsistencyValidator(),
            TechnicalFeasibilityValidator(),
            NarrativeContinuityValidator(),
            BudgetImpactValidator()
        ]
    
    async def validate_agent_output(self, agent_output: dict) -> dict:
        """Run complete validation pipeline"""
        validation_results = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "suggestions": []
        }
        
        for validator in self.validators:
            result = await validator.validate(agent_output)
            
            if not result["valid"]:
                validation_results["valid"] = False
                validation_results["errors"].extend(result.get("errors", []))
            
            validation_results["warnings"].extend(result.get("warnings", []))
            validation_results["suggestions"].extend(result.get("suggestions", []))
        
        return validation_results
    
    async def get_approval_required(self, agent_output: dict) -> bool:
        """Determine if human approval is required"""
        validation = await self.validate_agent_output(agent_output)
        
        # Require approval for high-impact changes or errors
        return (
            validation["errors"] or
            len(validation["warnings"]) > 3 or
            agent_output.get("confidence", 1.0) < 0.7
        )
```

### Real-time Integration
```python
class RealTimeIntegration:
    def __init__(self):
        self.websocket_manager = WebSocketManager()
        self.event_bus = EventBus()
    
    async def start_real_time_sync(self, project_id: str):
        """Start real-time synchronization with agents"""
        await self.websocket_manager.connect_project(project_id)
        
        # Subscribe to agent events
        await self.event_bus.subscribe("agent_output", self.handle_agent_output)
        await self.event_bus.subscribe("asset_created", self.handle_asset_created)
        await self.event_bus.subscribe("shot_modified", self.handle_shot_modified)
    
    async def handle_agent_output(self, event_data: dict):
        """Handle real-time agent output"""
        agent_type = event_data["agent_type"]
        output = event_data["output"]
        
        # Process immediately for low-confidence outputs
        if output.get("confidence", 1.0) < 0.8:
            await self.request_human_approval(agent_type, output)
        else:
            await self.auto_integrate(agent_type, output)
```

### Conflict Resolution
```python
class ConflictResolver:
    def __init__(self):
        self.resolution_strategies = {
            "prop_overlap": PropOverlapResolver(),
            "wardrobe_conflict": WardrobeConflictResolver(),
            "timeline_overlap": TimelineConflictResolver()
        }
    
    async def resolve_conflicts(self, conflicts: list) -> dict:
        """Resolve conflicts between agent outputs"""
        resolved_conflicts = []
        
        for conflict in conflicts:
            strategy = self.get_resolution_strategy(conflict["type"])
            resolution = await strategy.resolve(conflict)
            resolved_conflicts.append(resolution)
        
        return {
            "resolved": resolved_conflicts,
            "requires_approval": any(r["requires_approval"] for r in resolved_conflicts)
        }
    
    def get_resolution_strategy(self, conflict_type: str):
        return self.resolution_strategies.get(conflict_type, GenericConflictResolver())
```

### API Endpoints

#### Agent Integration
```python
POST /api/v1/agents/process
{
  "agent_type": "prop_master",
  "project_id": "proj-123",
  "input": {
    "script_text": "Scene description...",
    "context": {...}
  }
}

POST /api/v1/agents/validate
{
  "agent_output": {...},
  "project_id": "proj-123"
}

POST /api/v1/agents/approve
{
  "agent_output_id": "output-123",
  "approved": true,
  "notes": "Approved with modifications"
}

GET /api/v1/agents/checkpoints/{project_id}
POST /api/v1/agents/rollback
{
  "project_id": "proj-123",
  "checkpoint_id": "checkpoint-456"
}
```

### Testing Strategy

#### Integration Testing
```python
async def test_prop_master_integration():
    bridge = AgentIntegrationBridge("test-project", {})
    
    agent_output = {
        "agent_type": "prop_master",
        "props": [
            {
                "name": "Hero's Sword",
                "description": "Ancient bronze sword",
                "category": "weapon",
                "confidence": 0.9
            }
        ]
    }
    
    result = await bridge.process_agent_output("prop_master", agent_output)
    assert result["success"] is True
    assert len(result["created_assets"]) == 1
    assert result["created_assets"][0]["name"] == "Hero's Sword"

async def test_checkpoint_system():
    manager = CheckpointManager("test-project")
    
    # Create checkpoint
    checkpoint_id = await manager.create_checkpoint({"test": "data"}, "prop_analysis")
    assert checkpoint_id is not None
    
    # Rollback
    success = await manager.rollback_to_checkpoint(checkpoint_id)
    assert success is True

async def test_conflict_resolution():
    resolver = ConflictResolver()
    
    conflict = {
        "type": "prop_overlap",
        "agents": ["prop_master", "costume_designer"],
        "data": {"prop": "overlapping_suggestion"}
    }
    
    resolution = await resolver.resolve_conflicts([conflict])
    assert "resolved" in resolution
```

## Story Size: **Large (13 story points)**

## Sprint Assignment: **Sprint 5-6 (Phase 3)**

## Dependencies
- **STORY-083**: Expanded Asset System for asset creation
- **STORY-084**: Structured GenerativeShotList for shot integration
- **STORY-074-Enhanced**: Professional metadata for agent outputs
- **Agent Framework**: Agentic crew system
- **Validation Framework**: Asset and shot validation
- **Checkpoint System**: State management and rollback

## Success Criteria
- All agent types integrated with assembly pipeline
- Asset transformation accuracy 99%+
- Real-time sync latency < 100ms
- Checkpoint creation/rollback < 5 seconds
- Conflict resolution automation 95%+
- Human approval gates functional
- Integration tests pass for all agent types
- Performance tested with concurrent agents
- User acceptance testing passed

## Future Enhancements
- **AI Agent Collaboration**: Multi-agent negotiation
- **Predictive Integration**: ML-based conflict prediction
- **Cloud Agent Scaling**: Distributed agent processing
- **Advanced Approval Flows**: Context-aware approval systems
- **Agent Performance Analytics**: Optimization insights