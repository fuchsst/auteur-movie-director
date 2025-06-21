# Style Consistency Workflows

## Role
Workflows for creating and maintaining consistent visual aesthetics across all generated content. Implements style alliance and coherent visual identity.

## Style Consistency Techniques
- **Style Alliance** - Align random seeds and prompt structures
- **Style LoRAs** - Train custom style models
- **Apply Style Model** - Use ComfyUI style nodes for FLUX
- **Batch Consistency** - Coordinate style across multiple shots

## Workflow Templates
- **style_creation.json** - Initial style definition workflow
- **style_lora_training.json** - Train style-specific LoRA
- **style_application.json** - Apply style to generation
- **style_alliance.json** - Batch style consistency
- **style_validation.json** - Test style across scenarios

## Style Application Strategy
```python
def apply_style_consistency(shots, style_obj):
    """Apply consistent style across shot batch"""
    
    # Extract style parameters
    style_lora = style_obj.movie_director.style_lora_path
    style_seed = style_obj.movie_director.base_seed
    
    # Apply to all shots with seed alignment
    for i, shot in enumerate(shots):
        aligned_seed = style_seed + i  # Seed alliance
        apply_style_to_shot(shot, style_lora, aligned_seed)
```

## Style Elements
- **Color Palette** - Consistent color schemes
- **Lighting Style** - Consistent lighting approach
- **Texture Quality** - Material and surface consistency
- **Composition Rules** - Consistent framing principles

## Quality Assurance
- **Style Validation** - Test across different content types
- **Consistency Metrics** - Measure visual coherence
- **User Feedback** - Iterative style refinement
- **Style Library** - Reusable style assets

## Reference
- [Art Director](/../agents/art_director/CLAUDE.md)