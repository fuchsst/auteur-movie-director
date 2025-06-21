# Casting Director Agent

## Agent Profile
```yaml
agent:
  name: Casting Director
  title: Character Asset Management & Consistency Specialist
  icon: 🎭
  focus: Character creation, LoRA training, facial consistency, voice model management
  specialization: Character stability, AI model training, asset lifecycle management
```

## Role & Responsibilities

### Primary Function
The Casting Director agent manages the complete lifecycle of character assets, ensuring visual and vocal consistency across all generated content. This agent is critical for solving character stability challenges in AI-generated film production.

### Core Capabilities
- **Character Asset Creation**: Generate and manage character reference materials
- **LoRA Training**: Train character-specific LoRA models for ultimate consistency
- **Voice Model Training**: Create RVC voice models for consistent character dialogue
- **Visual Consistency**: Implement multi-tiered character stability strategies
- **Asset Browser Integration**: Manage character assets in Blender's native asset system

## Technical Implementation

### Multi-Tiered Character Consistency Strategy

#### Tier 1: Baseline Consistency (Fast Generation)
```python
workflow_components:
  - IPAdapter: Facial identity capture from reference image
  - InstantID: Enhanced facial feature preservation
  - ControlNet: Pose and composition control
  - ComfyUI_Workflow: character_quick_gen.json
```

#### Tier 2: Enhanced Fidelity (Quality Generation)  
```python
workflow_components:
  - IPAdapter + InstantID: Base identity
  - ControlNet: Pose control
  - ReActor: High-quality face swap for final correction
  - ComfyUI_Workflow: character_enhanced_gen.json
```

#### Tier 3: Ultimate Fidelity (Main Characters)
```python
workflow_components:
  - Custom_LoRA: Character-specific trained model
  - Low_VRAM_Training: Consumer hardware compatible
  - ComfyUI_Workflow: character_lora_gen.json
```

### Backend Integration
- **ComfyUI**: Character generation workflows and LoRA training
- **RVC-Project**: Voice model training and synthesis
- **VRAM Budgeting**: Intelligent resource management for training processes

### Blender Integration
```python
character_data_model:
  blender_representation: bpy.types.Object (Empty)
  custom_properties:
    - name: StringProperty
    - description: StringProperty  
    - reference_images_path: StringProperty
    - character_lora_path: StringProperty  # .safetensors
    - rvc_voice_model_path: StringProperty  # .pth
  asset_browser_integration:
    - asset_mark(): Mark as Blender asset
    - asset_generate_preview(): Create thumbnail
    - catalog_assignment: "Movie Director/Characters"
```

## CrewAI Tools
```python
tools:
  - character_reference_generator: Create initial character concepts
  - lora_training_tool: Train character-specific LoRA models
  - rvc_voice_trainer: Train character voice models
  - consistency_validator: Verify character consistency across shots
  - asset_browser_manager: Manage Blender asset integration
```

## Workflow Integration

### Character Creation Pipeline
1. **Reference Generation**: Create character concept art and reference sheets
2. **Identity Capture**: Process reference images for IPAdapter/InstantID
3. **Voice Recording**: Generate or process voice samples for RVC training
4. **Asset Registration**: Create Blender asset with all associated files
5. **Consistency Testing**: Validate character across different scenarios

### LoRA Training Process
```python
def train_character_lora(character_asset, reference_images):
    """Train character-specific LoRA with VRAM budgeting"""
    vram_required = calculate_lora_training_vram()
    
    if vram_manager.check_availability(vram_required):
        training_config = {
            "network_alpha": 1,
            "network_dim": 128,
            "learning_rate": 1e-4,
            "max_train_epoches": 10,
            "save_every_n_epochs": 2
        }
        return execute_lora_training(character_asset, training_config)
    else:
        return schedule_sequential_training(character_asset)
```

### RVC Voice Training
```python
def train_character_voice(character_asset, voice_samples):
    """Train RVC voice model for character consistency"""
    rvc_config = {
        "sample_rate": 40000,
        "hop_length": 512,
        "epochs": 500,
        "batch_size": 4
    }
    return rvc_trainer.train_model(voice_samples, rvc_config)
```

## Advanced Features

### Intelligent Consistency Management
- **Style Alliance**: Coordinate with Art Director for visual harmony
- **Cross-Shot Validation**: Ensure character consistency across all scenes
- **Progressive Quality**: Automatically select appropriate consistency tier based on shot importance

### Asset Lifecycle Management
- **Version Control**: Track LoRA model iterations and improvements
- **Performance Monitoring**: Monitor generation quality and consistency metrics
- **Asset Optimization**: Optimize model files for production efficiency

### Blender Asset Browser Integration
```python
def create_character_asset(name, reference_images, lora_path, voice_path):
    """Create character asset in Blender with full integration"""
    character_empty = bpy.data.objects.new(name, None)
    
    # Set custom properties
    character_empty.movie_director.character_name = name
    character_empty.movie_director.reference_images = reference_images
    character_empty.movie_director.lora_path = lora_path
    character_empty.movie_director.voice_model_path = voice_path
    
    # Asset Browser integration
    character_empty.asset_mark()
    character_empty.asset_generate_preview()
    
    # Assign to catalog
    catalog_id = get_or_create_catalog("Movie Director/Characters")
    character_empty.asset_data.catalog_id = catalog_id
    
    return character_empty
```

## Quality Standards
- **Visual Consistency**: >95% facial similarity across generations
- **Voice Consistency**: Natural character voice with emotional range
- **Performance**: LoRA models optimized for real-time generation
- **Asset Management**: Proper cataloging and version control

## Performance Considerations
- **VRAM Optimization**: Sequential training for limited hardware
- **Training Efficiency**: Optimized LoRA training parameters
- **Asset Size**: Compressed models without quality loss
- **Generation Speed**: Balance between quality and inference time

## Integration Points
- **Input**: Character descriptions from Screenwriter
- **Output**: Character assets → Cinematographer for video generation
- **Collaboration**: Works with Art Director for visual style consistency
- **Resource Sharing**: Coordinates VRAM usage with other agents

## Error Handling
- **Training Failures**: Graceful fallback to baseline consistency methods
- **VRAM Overflow**: Automatic sequential processing
- **Asset Conflicts**: Version management and conflict resolution
- **Voice Synthesis Issues**: Fallback to text-to-speech alternatives

This agent is essential for maintaining character consistency and professional quality in AI-generated film production, providing the foundation for believable, recurring characters throughout the narrative.