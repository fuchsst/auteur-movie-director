# Story: STORY-105 - Quality System Documentation

## Story Description
As a technical writer, I need comprehensive documentation for the quality tier system so that developers, administrators, and users can understand how to use and configure the three-tier quality system effectively.

## Acceptance Criteria
- [ ] User documentation for quality tier selection
- [ ] Developer documentation for quality system integration
- [ ] Administrator documentation for configuration management
- [ ] API documentation with examples
- [ ] Troubleshooting guide
- [ ] Best practices documentation
- [ ] No complex technical concepts requiring resource analysis

## Technical Details

### User Documentation

#### Quality Tier User Guide
```markdown
# Auteur Quality Tier System - User Guide

## Overview
The Auteur platform provides three quality tiers for content generation:

- **Low Quality**: Fast generation with basic quality (30-60 seconds)
- **Standard Quality**: Balanced quality and performance (60-120 seconds)
- **High Quality**: Maximum quality with fine details (120-300 seconds)

## How to Select Quality Tiers

### Character Creator
1. Open the Character Creator interface
2. Select your character type (portrait, full body, expression, style)
3. Choose your desired quality tier from the quality cards
4. Click the tier that best matches your needs

### Storyboard Generation
1. Navigate to the storyboard generation page
2. Select your pipeline (storyboard, shot, or sequence generation)
3. Choose your quality tier using the quality buttons
4. Review the estimated time and stage breakdown

### Direct API Usage
```bash
curl -X POST http://localhost:8000/api/v1/quality/select \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "character_portrait",
    "quality_tier": "standard"
  }'
```

## Quality Tier Descriptions

### Low Quality
- **Use Case**: Quick prototyping, testing ideas
- **Features**: Basic quality, faster generation
- **Parameters**: Lower step count, smaller dimensions
- **Estimated Time**: 30-60 seconds

### Standard Quality
- **Use Case**: Most production use cases
- **Features**: Balanced quality and speed
- **Parameters**: Moderate step count, standard dimensions
- **Estimated Time**: 60-120 seconds

### High Quality
- **Use Case**: Final production, detailed work
- **Features**: Maximum quality, fine details
- **Parameters**: Higher step count, larger dimensions
- **Estimated Time**: 120-300 seconds

## Tips for Choosing Quality Tiers

1. **Start with Standard**: Begin with standard quality for most use cases
2. **Use Low for Testing**: Use low quality when testing parameters or ideas
3. **Reserve High for Finals**: Use high quality for final production outputs
4. **Consider Time Budgets**: Factor in estimated generation times for your workflow
```

### Developer Documentation

#### Quality System Integration Guide
```markdown
# Quality System Integration - Developer Guide

## Architecture Overview

The quality tier system consists of:

1. **QualityConfigManager**: Manages quality-to-workflow mappings
2. **ComfyUIQualityIntegration**: Handles workflow preparation
3. **QualityTaskExecutor**: Manages task execution with quality tiers
4. **ParameterValidator**: Validates and merges parameters

## Integration Points

### Basic Integration
```python
from app.services.quality_config_manager import QualityConfigManager
from app.services.comfyui_quality_integration import ComfyUIQualityIntegration

# Initialize services
config_manager = QualityConfigManager("/path/to/quality_mappings.yaml")
integration = ComfyUIQualityIntegration(
    workflows_root="/path/to/workflows",
    quality_config_manager=config_manager
)

# Prepare workflow with quality tier
execution_data = integration.prepare_workflow_execution(
    task_type="character_portrait",
    quality_tier="standard",
    user_parameters={"positive_prompt": "test prompt"}
)
```

### Adding New Task Types
```python
# Update quality_mappings.yaml
mappings:
  new_task_type:
    low:
      workflow_path: "library/new_task_type/low_v1"
      description: "Fast new task generation"
      parameters:
        steps: 20
        cfg_scale: 7.0
    standard:
      workflow_path: "library/new_task_type/standard_v1"
      description: "Standard new task quality"
      parameters:
        steps: 35
        cfg_scale: 7.5
    high:
      workflow_path: "library/new_task_type/high_v1"
      description: "High quality new task"
      parameters:
        steps: 60
        cfg_scale: 8.0
```

### API Integration
```python
# Frontend integration example
async function selectQuality(taskType, qualityTier) {
    const response = await fetch('/api/v1/quality/select', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            task_type: taskType,
            quality_tier: qualityTier
        })
    });
    
    const data = await response.json();
    return data.workflow_path;
}
```

## Administrator Documentation

### Configuration Management Guide
```markdown
# Quality System Configuration - Administrator Guide

## Configuration File Structure

The quality system uses YAML configuration files with the following structure:

```yaml
version: "1.0"
mappings:
  task_type_name:
    quality_tier_name:
      workflow_path: "path/to/workflow"
      description: "Human-readable description"
      parameters:
        steps: integer
        cfg_scale: float
        width: integer
        height: integer
```

## Environment-Specific Configuration

### Development Environment
- Located: `deployment/quality-config/development.yaml`
- Fast parameters for testing
- Smaller dimensions for quick iteration

### Staging Environment
- Located: `deployment/quality-config/staging.yaml`
- Production-like parameters
- Full testing capabilities

### Production Environment
- Located: `deployment/quality-config/production.yaml`
- Full quality parameters
- Optimized for production use

## Configuration Validation

### Manual Validation
```bash
# Validate configuration
python -m app.services.workflow_validator \
  --config /opt/comfyui_workflows/config/quality_mappings.yaml \
  --workflows /opt/comfyui_workflows
```

### Automated Validation
```bash
# Run deployment validation
./deployment/scripts/validate-deployment.py --environment production
```

## Adding New Quality Tiers

1. **Update Configuration**: Add new tier to quality_mappings.yaml
2. **Create Workflows**: Create corresponding workflow directories
3. **Validate**: Run validation scripts
4. **Deploy**: Use deployment scripts
5. **Test**: Run integration tests

## Monitoring and Maintenance

### Health Check Endpoints
- `/api/v1/quality/health` - System health
- `/api/v1/quality/ready` - Readiness status
- `/api/v1/quality/version` - Version information

### Log Monitoring
Monitor these key metrics:
- Quality tier selection rates
- Workflow execution times by tier
- Configuration validation failures
- Missing workflow alerts
```

### API Documentation

#### Quality System API Reference
```markdown
# Quality System API Reference

## Base URL
`http://localhost:8000/api/v1/quality`

## Endpoints

### Get Quality Tiers
```http
GET /api/v1/quality/tiers/{task_type}
```

**Parameters:**
- `task_type` (string): Type of task (e.g., "character_portrait")

**Response:**
```json
{
  "task_type": "character_portrait",
  "available_tiers": {
    "low": {
      "description": "Fast generation with basic quality",
      "estimated_time": "30-60 seconds",
      "workflow_path": "library/image_generation/character_portrait/low_v1"
    },
    "standard": {
      "description": "Balanced quality and performance",
      "estimated_time": "60-120 seconds",
      "workflow_path": "library/image_generation/character_portrait/standard_v1"
    },
    "high": {
      "description": "Maximum quality with fine details",
      "estimated_time": "120-300 seconds",
      "workflow_path": "library/image_generation/character_portrait/high_v1"
    }
  }
}
```

### Select Quality Tier
```http
POST /api/v1/quality/select
```

**Request Body:**
```json
{
  "task_type": "character_portrait",
  "quality_tier": "standard"
}
```

**Response:**
```json
{
  "task_type": "character_portrait",
  "quality_tier": "standard",
  "workflow_path": "library/image_generation/character_portrait/standard_v1",
  "status": "selected"
}
```

### Health Check
```http
GET /api/v1/quality/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-17T10:30:00Z",
  "checks": {
    "configuration": {
      "status": "healthy",
      "details": {
        "total_mappings": 18
      }
    },
    "workflows": {
      "status": "healthy",
      "details": {
        "total_workflows": 18,
        "missing_workflows": []
      }
    }
  }
}
```

### Character Quality Options
```http
GET /api/v1/character-quality/quality-options/{character_type}
```

**Parameters:**
- `character_type` (string): Type of character ("character_portrait", "character_fullbody", etc.)

**Response:**
```json
{
  "character_type": "character_portrait",
  "quality_options": {
    "low": {
      "description": "Fast character portrait generation",
      "estimated_time": 45,
      "parameters": {
        "steps": 20,
        "cfg_scale": 7.0,
        "width": 512,
        "height": 768
      }
    },
    "standard": {
      "description": "Balanced quality character portrait",
      "estimated_time": 90,
      "parameters": {
        "steps": 35,
        "cfg_scale": 7.5,
        "width": 512,
        "height": 768
      }
    },
    "high": {
      "description": "High quality character portrait with details",
      "estimated_time": 180,
      "parameters": {
        "steps": 60,
        "cfg_scale": 8.0,
        "width": 768,
        "height": 1024
      }
    }
  }
}
```
```

### Troubleshooting Guide

#### Common Issues and Solutions
```markdown
# Quality System Troubleshooting Guide

## Issue: "Workflow not found" error

**Symptoms:**
- Error message: "Workflow file not found"
- Quality tier selection fails

**Solution:**
1. Check workflow directory exists:
   ```bash
   ls -la /opt/comfyui_workflows/library/{task_type}/{tier}_v1/
   ```
2. Verify workflow_api.json exists:
   ```bash
   test -f /opt/comfyui_workflows/library/{task_type}/{tier}_v1/workflow_api.json
   ```
3. Check configuration mapping:
   ```yaml
   # Verify quality_mappings.yaml
   mappings:
     task_type:
       tier:
         workflow_path: "library/task_type/tier_v1"
   ```

## Issue: "Invalid quality tier" error

**Symptoms:**
- API returns 400 error
- Quality tier not recognized

**Solution:**
1. Check available tiers:
   ```bash
   curl http://localhost:8000/api/v1/quality/tiers/{task_type}
   ```
2. Verify tier name is one of: "low", "standard", "high"

## Issue: Configuration validation fails

**Symptoms:**
- Health check shows unhealthy
- Configuration errors in logs

**Solution:**
1. Validate configuration:
   ```bash
   python -c "
   import yaml
   with open('/opt/comfyui_workflows/config/quality_mappings.yaml') as f:
       config = yaml.safe_load(f)
   print('Configuration is valid')
   "
   ```
2. Check YAML syntax:
   ```bash
   yamllint /opt/comfyui_workflows/config/quality_mappings.yaml
   ```

## Issue: Performance issues with high quality tier

**Symptoms:**
- Long generation times
- System resource warnings

**Solution:**
1. Check estimated times:
   ```bash
   curl http://localhost:8000/api/v1/quality/tiers/{task_type}
   ```
2. Consider using standard or low quality for testing
3. Verify system has sufficient resources

## Issue: Quality tier parameters not applied

**Symptoms:**
- Generation uses default parameters
- Quality tier selection appears to have no effect

**Solution:**
1. Check parameter merging in logs
2. Verify workflow API structure matches expected format
3. Test parameter validation:
   ```bash
   curl -X POST http://localhost:8000/api/v1/quality/select \
     -H "Content-Type: application/json" \
     -d '{"task_type": "test", "quality_tier": "standard"}'
   ```
```

### Best Practices Documentation

#### Quality Tier Usage Best Practices
```markdown
# Quality Tier Best Practices

## For Users

### Choosing the Right Quality Tier

1. **Start with Standard**
   - Use standard quality for initial work
   - Provides good balance of quality and speed
   - Suitable for most use cases

2. **Use Low for Iteration**
   - Perfect for testing parameters and concepts
   - Fast feedback loop for adjustments
   - Save time during development

3. **Reserve High for Final Outputs**
   - Use for final production assets
   - Maximum quality for deliverables
   - Worth the extra time for final results

### Pipeline Optimization

1. **Consistent Quality Across Stages**
   - Use same quality tier for all pipeline stages
   - Ensures consistent output quality
   - Simplifies configuration management

2. **Quality Tier Selection Strategy**
   - Low: Testing, prototyping, quick previews
   - Standard: Development, regular production
   - High: Final assets, client deliverables

## For Developers

### Integration Patterns

1. **Use QualityConfigManager**
   - Centralized configuration management
   - Consistent quality tier handling
   - Easy to extend for new task types

2. **Parameter Validation**
   - Always validate user parameters
   - Use QualityConfigManager for defaults
   - Provide clear error messages

3. **Error Handling**
   - Handle missing workflows gracefully
   - Provide fallback to standard quality
   - Log configuration issues clearly

## For Administrators

### Configuration Management

1. **Version Control**
   - Keep quality mappings in version control
   - Use environment-specific configurations
   - Test changes in staging before production

2. **Monitoring Setup**
   - Monitor quality tier usage patterns
   - Track workflow availability
   - Set up alerts for configuration issues

3. **Maintenance Schedule**
   - Regular validation of workflows
   - Periodic review of quality parameters
   - Update documentation with changes
```

## Test Requirements
- Documentation accuracy validation
- Example code functionality
- Configuration examples work
- API documentation matches implementation
- Troubleshooting steps are actionable

## Definition of Done
- All documentation is complete and accurate
- Code examples are tested and working
- Configuration examples are valid
- API documentation matches current implementation
- Troubleshooting guide covers common issues
- Best practices are actionable and tested