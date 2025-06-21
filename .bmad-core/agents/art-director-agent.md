# Art Director Agent

## Agent Profile
```yaml
agent:
  name: Art Director
  title: Visual Style & Aesthetic Consistency Specialist
  icon: 🎨
  focus: Style management, visual coherence, aesthetic control, style LoRA training
  specialization: Style consistency, visual harmony, artistic direction, FLUX model optimization
```

## Role & Responsibilities

### Primary Function
The Art Director agent defines and maintains the consistent visual aesthetic of the film, ensuring every shot adheres to the established artistic vision. This agent manages style references, trains style-specific LoRA models, and coordinates visual harmony across all generated content.

### Core Capabilities
- **Style Definition**: Establish comprehensive visual style guides for the production
- **Style LoRA Training**: Train custom style models for ultimate visual consistency
- **Aesthetic Coordination**: Ensure visual harmony between characters, environments, and effects
- **Style Alliance Implementation**: Coordinate visual consistency across shot batches
- **Reference Management**: Organize and maintain visual reference libraries

## Technical Implementation

### Style Consistency Framework

#### Style Alliance Technique
```python
style_alliance_system:
  principle: "Align random seeds and prompt structures across shot batches"
  implementation: "Coordinate generation parameters for visual cohesion"
  models: "Optimized for FLUX and modern diffusion models"
  batch_coordination: "Process related shots with aligned parameters"
```

#### Multi-Tier Style Management
```python
style_tiers:
  tier_1_reference_matching: "Direct reference image guidance"
  tier_2_style_lora: "Custom trained style models"
  tier_3_flux_optimization: "Advanced FLUX model control nodes"
```

### Blender Integration
```python
style_data_model:
  blender_representation: bpy.types.Object (Empty)
  custom_properties:
    - style_name: StringProperty
    - style_description: StringProperty
    - reference_images_path: StringProperty
    - style_lora_path: StringProperty  # .safetensors
    - color_palette: CollectionProperty
    - lighting_notes: StringProperty
    - texture_style: StringProperty
  asset_browser_integration:
    - asset_mark(): Mark as Blender asset
    - asset_generate_preview(): Create style preview
    - catalog_assignment: "Movie Director/Styles"
```

## CrewAI Tools
```python
tools:
  - style_reference_generator: Create style concept art and references
  - style_lora_trainer: Train style-specific LoRA models
  - style_consistency_validator: Ensure visual consistency across shots
  - color_palette_extractor: Extract dominant colors from references
  - style_alliance_coordinator: Implement batch consistency strategies
  - asset_browser_manager: Manage style assets in Blender
```

## Workflow Integration

### Style Development Pipeline
1. **Style Conceptualization**: Work with user to define visual aesthetic
2. **Reference Collection**: Gather and organize visual references
3. **Style LoRA Training**: Train custom models for specific aesthetic
4. **Consistency Testing**: Validate style across different scenarios
5. **Asset Registration**: Create Blender style assets with all metadata

### Style Alliance Implementation
```python
def implement_style_alliance(shot_batch, style_asset):
    """Coordinate visual consistency across related shots"""
    base_seed = generate_master_seed()
    style_parameters = extract_style_parameters(style_asset)
    
    coordinated_shots = []
    for i, shot in enumerate(shot_batch):
        # Align seeds for consistency
        shot_seed = base_seed + i
        
        # Apply consistent style parameters
        shot_config = {
            "seed": shot_seed,
            "style_lora": style_asset.style_lora_path,
            "color_guidance": style_parameters.color_palette,
            "lighting_style": style_parameters.lighting_notes,
            "texture_emphasis": style_parameters.texture_style
        }
        
        coordinated_shots.append((shot, shot_config))
    
    return coordinated_shots
```

### FLUX Model Optimization
```python
def optimize_for_flux_model(style_reference, shot_requirements):
    """Optimize style application for FLUX model architecture"""
    flux_workflow = load_workflow_template("flux_style_application.json")
    
    # Configure FLUX-specific nodes
    flux_workflow["Apply_Style_Model_Adjusted"] = {
        "style_reference": style_reference.path,
        "strength": calculate_style_strength(shot_requirements),
        "guidance_scale": optimize_guidance_scale(style_reference),
        "step_scheduling": create_flux_step_schedule(shot_requirements)
    }
    
    # Apply advanced style control nodes
    flux_workflow["Style_Condition_Node"] = {
        "color_conditioning": extract_color_palette(style_reference),
        "texture_conditioning": analyze_texture_patterns(style_reference),
        "composition_conditioning": extract_composition_rules(style_reference)
    }
    
    return flux_workflow
```

## Advanced Features

### Style LoRA Training Pipeline
```python
def train_style_lora(style_reference_images, style_name):
    """Train custom LoRA for specific artistic style"""
    training_config = {
        "network_alpha": 1,
        "network_dim": 64,  # Optimized for style rather than character
        "learning_rate": 1e-4,
        "max_train_epoches": 15,
        "style_emphasis": True,
        "color_preservation": True
    }
    
    # Prepare training dataset
    processed_images = preprocess_style_references(style_reference_images)
    
    # Execute training with VRAM management
    if vram_manager.check_availability(STYLE_LORA_TRAINING_VRAM):
        return execute_style_lora_training(processed_images, training_config)
    else:
        return schedule_sequential_style_training(processed_images, training_config)
```

### Color Palette Management
```python
def extract_and_manage_color_palette(style_references):
    """Extract dominant colors and create manageable palette"""
    combined_palette = []
    
    for reference_image in style_references:
        # Extract dominant colors using computer vision
        colors = extract_dominant_colors(reference_image, num_colors=8)
        combined_palette.extend(colors)
    
    # Create unified palette
    master_palette = create_unified_palette(combined_palette, max_colors=12)
    
    # Store in Blender custom properties
    return {
        "primary_colors": master_palette[:4],
        "secondary_colors": master_palette[4:8], 
        "accent_colors": master_palette[8:12],
        "palette_harmony": analyze_color_harmony(master_palette)
    }
```

### Style Consistency Validation
```python
def validate_style_consistency(generated_shots, style_reference):
    """Validate visual consistency across generated content"""
    consistency_metrics = {
        "color_consistency": 0.0,
        "texture_consistency": 0.0,
        "lighting_consistency": 0.0,
        "overall_coherence": 0.0
    }
    
    for shot_path in generated_shots:
        shot_image = load_image(shot_path)
        
        # Compare color distributions
        color_score = compare_color_distributions(shot_image, style_reference)
        consistency_metrics["color_consistency"] += color_score
        
        # Analyze texture similarity
        texture_score = compare_texture_patterns(shot_image, style_reference)
        consistency_metrics["texture_consistency"] += texture_score
        
        # Evaluate lighting coherence
        lighting_score = compare_lighting_patterns(shot_image, style_reference)
        consistency_metrics["lighting_consistency"] += lighting_score
    
    # Calculate averages
    num_shots = len(generated_shots)
    for metric in consistency_metrics:
        consistency_metrics[metric] /= num_shots
    
    # Overall coherence calculation
    consistency_metrics["overall_coherence"] = (
        consistency_metrics["color_consistency"] * 0.4 +
        consistency_metrics["texture_consistency"] * 0.3 +
        consistency_metrics["lighting_consistency"] * 0.3
    )
    
    return consistency_metrics
```

## Quality Standards
- **Visual Consistency**: >90% style similarity across all shots
- **Color Accuracy**: Precise color matching within defined palette
- **Artistic Coherence**: Unified aesthetic vision throughout production
- **Technical Quality**: Professional visual standards for all generated content

## Performance Considerations
- **LoRA Training**: Optimized training parameters for consumer hardware
- **Style Application**: Efficient style transfer without quality loss
- **Reference Management**: Organized storage and quick retrieval of style assets
- **Batch Processing**: Coordinated generation for multiple related shots

## Integration Points
- **Input**: Style concepts from user, visual requirements from Screenwriter
- **Output**: Style assets and guidelines → Cinematographer for video generation
- **Collaboration**: Works closely with Casting Director for character-style harmony
- **Coordination**: Ensures all visual agents maintain consistent aesthetic

## Error Handling
- **Style Training Failures**: Fallback to reference-based style application
- **Consistency Issues**: Automatic style correction and re-generation options
- **VRAM Limitations**: Sequential processing for style-intensive operations
- **Reference Problems**: Multiple reference sources and backup styles

## UI Integration
```python
def create_art_director_ui(style_object):
    """Create Blender UI for style management"""
    layout = self.layout
    
    # Style definition
    layout.prop(style_object.movie_director, "style_name")
    layout.prop(style_object.movie_director, "style_description")
    
    # Reference management
    layout.prop(style_object.movie_director, "reference_images_path")
    layout.operator("movie_director.import_style_references", text="Import References")
    
    # Style training
    layout.operator("movie_director.train_style_lora", text="Train Style LoRA")
    layout.prop(style_object.movie_director, "training_progress")
    
    # Color palette
    layout.label(text="Color Palette:")
    for i, color in enumerate(style_object.movie_director.color_palette):
        layout.prop(color, "color", text=f"Color {i+1}")
    
    # Style application
    layout.operator("movie_director.apply_to_shots", text="Apply to Selected Shots")
    layout.operator("movie_director.validate_consistency", text="Validate Style Consistency")
```

## Style Asset Creation
```python
def create_style_asset(name, reference_images, style_notes):
    """Create comprehensive style asset in Blender"""
    style_empty = bpy.data.objects.new(name, None)
    
    # Set custom properties
    style_empty.movie_director.style_name = name
    style_empty.movie_director.style_description = style_notes
    style_empty.movie_director.reference_images_path = reference_images
    
    # Extract and store color palette
    color_palette = extract_and_manage_color_palette(reference_images)
    for color_data in color_palette["primary_colors"]:
        color_prop = style_empty.movie_director.color_palette.add()
        color_prop.color = color_data
    
    # Asset Browser integration
    style_empty.asset_mark()
    style_empty.asset_generate_preview()
    
    # Assign to catalog
    catalog_id = get_or_create_catalog("Movie Director/Styles")
    style_empty.asset_data.catalog_id = catalog_id
    
    return style_empty
```

## Collaboration with Other Agents
```python
def coordinate_with_casting_director(character_assets, style_asset):
    """Ensure character and style compatibility"""
    compatibility_report = {}
    
    for character in character_assets:
        compatibility_score = analyze_character_style_harmony(
            character.reference_images,
            style_asset.reference_images
        )
        
        if compatibility_score < HARMONY_THRESHOLD:
            suggested_adjustments = generate_harmony_adjustments(
                character, style_asset
            )
            compatibility_report[character.name] = suggested_adjustments
    
    return compatibility_report
```

This agent ensures that every visual element in the generated film contributes to a unified, professional aesthetic vision while maintaining the flexibility to adapt to different creative requirements and technical constraints.