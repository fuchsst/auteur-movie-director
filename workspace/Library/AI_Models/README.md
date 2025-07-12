# AI Model Storage for Function Runner Architecture

This directory contains AI models organized by category for the Auteur Movie Director platform.
Each model should include proper manifests and pipeline configurations for containerized execution.

## Directory Structure

- `image/` - Image generation models (Flux, SDXL, etc.)
- `video/` - Video generation models (WannaGAN, etc.)
- `audio/` - Audio generation models (AudioLDM, RVC, etc.)
- `language/` - Language models (LLMs for script generation)

Each category contains:
- `models/` - Model files (weights, configs)
- `pipelines/` - Pipeline execution configurations
- `configs/` - Additional configuration files

## Model Manifest Schema (model.json)

```json
{
  "id": "model-unique-id",
  "name": "Model Display Name",
  "version": "1.0.0",
  "type": "image|video|audio|language",
  "requirements": {
    "vram": 16,
    "disk_space": 5.5,
    "cuda_version": "11.8",
    "python_version": "3.10"
  },
  "files": [
    {
      "name": "model.safetensors",
      "size": 5368709120,
      "hash": "sha256:...",
      "url": "https://example.com/model.safetensors"
    }
  ],
  "capabilities": [
    "text-to-image",
    "image-to-image"
  ],
  "license": "Apache-2.0",
  "description": "Model description and usage notes"
}
```

## Pipeline Configuration Schema (pipeline.json)

```json
{
  "id": "pipeline-unique-id",
  "name": "Pipeline Display Name",
  "model_id": "associated-model-id",
  "container_image": "auteur/model:tag",
  "execution": {
    "command": "python generate.py",
    "args": ["--model", "/models/flux", "--config", "/config/standard.json"],
    "environment": {
      "CUDA_VISIBLE_DEVICES": "0",
      "HF_HOME": "/models/cache"
    }
  },
  "resources": {
    "gpu": true,
    "vram": 16,
    "cpu": 4,
    "memory": "16Gi"
  },
  "mounts": [
    {
      "source": "/workspace",
      "target": "/workspace",
      "readonly": false
    },
    {
      "source": "/models",
      "target": "/models",
      "readonly": true
    }
  ],
  "quality_tier": "standard",
  "optimizations": ["moderate_parallel", "standard_res"]
}
```

## Integration Notes

Models in this directory will be automatically discovered by the Function Runner
system and made available for pipeline execution. Ensure all models follow
the manifest schema for proper integration.

For development, placeholder models can be used for testing the pipeline
execution without requiring large model downloads.
