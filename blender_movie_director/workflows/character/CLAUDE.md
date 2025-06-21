# Character Generation Workflows

## Role
Specialized workflows for character creation and consistency management. Implements the multi-tier character strategy from basic reference to ultimate fidelity.

## Character Consistency Tiers
1. **Baseline** - IPAdapter + InstantID for quick visualization
2. **Enhanced** - ComfyUI-ReActor for face swap refinement  
3. **Ultimate** - Custom LoRA training for main characters

## Workflow Templates
- **character_reference.json** - Generate initial character references
- **character_basic.json** - IPAdapter consistency workflow
- **character_enhanced.json** - ReActor face swap integration
- **character_lora_training.json** - LoRA training pipeline
- **character_voice_training.json** - RVC voice model training

## Implementation Strategy
```python
def generate_character_with_consistency(character_obj, tier="enhanced"):
    if tier == "baseline":
        return execute_ipadapter_workflow(character_obj)
    elif tier == "enhanced":
        return execute_reactor_workflow(character_obj)
    elif tier == "ultimate":
        return train_character_lora(character_obj)
```

## Character Asset Pipeline
1. **Reference Generation** - Create character reference images
2. **Consistency Testing** - Validate across different poses/expressions
3. **Model Training** - Train LoRA for main characters
4. **Voice Model** - Train RVC for dialogue consistency
5. **Asset Creation** - Create Blender character objects

## Quality Control
- **Facial Feature Matching** - Ensure consistent facial characteristics
- **Expression Range** - Test across different emotions
- **Pose Variation** - Validate in different positions
- **Style Compatibility** - Test with various visual styles

## Reference
- [Casting Director](/../agents/casting_director/CLAUDE.md)