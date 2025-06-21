# Hardware Detection & Optimization

## Role
Hardware capability detection and performance optimization. Provides intelligent model selection and configuration based on available system resources.

## Detection Capabilities
- **GPU Information** - Model, VRAM, compute capability
- **System Memory** - Available RAM for model loading
- **CPU Cores** - Parallel processing capability
- **Storage Speed** - Model loading performance

## Implementation Pattern
```python
def detect_hardware_profile():
    """Detect system capabilities and recommend settings"""
    gpu_info = get_gpu_info()
    
    if gpu_info.vram < 8:
        return "tier1_minimum"
    elif gpu_info.vram >= 24:
        return "tier2_recommended" 
    else:
        return "tier3_high_performance"
```

## Optimization Strategies
- **Model Selection** - Choose appropriate models for hardware
- **Backend Routing** - Route tasks to suitable backends
- **Quality Presets** - Adjust quality based on capabilities
- **Performance Monitoring** - Track resource usage

## Hardware Tiers
- **Tier 1** - 8-16GB VRAM, focus on efficiency
- **Tier 2** - 16-24GB VRAM, balanced performance
- **Tier 3** - 24GB+ VRAM, maximum quality

## Auto-Configuration
- **Model Compatibility** - Check model requirements
- **Performance Profiling** - Benchmark generation speeds
- **Resource Allocation** - Optimize for available hardware
- **Fallback Strategies** - Handle resource constraints

## Reference
- [Hardware Configurations](/../CLAUDE.md#hardware-provisioning)