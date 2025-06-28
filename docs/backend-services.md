# Backend Services Setup Guide

This guide explains how to set up and run the AI backend services required by Blender Movie Director.

## Overview

Blender Movie Director requires four backend services:

1. **ComfyUI** (port 8188) - Image/video generation workflows
2. **Wan2GP** (port 7860) - Fast video generation
3. **RVC** (port 7865) - Voice cloning and audio processing
4. **AudioLDM** (port 7863) - Sound effects and ambient audio

## Quick Start

### Using Make Commands

```bash
# Start all services
make services

# Check service status
make services-status

# Stop all services
make services-stop

# View logs
make services-logs
```

### Starting Individual Services

```bash
# Start only ComfyUI
make service-comfyui

# Start only Wan2GP
make service-wan2gp

# Start only RVC
make service-rvc

# Start only AudioLDM
make service-audioldm
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Service ports (customize if needed)
COMFYUI_PORT=8188
WAN2GP_PORT=7860
RVC_PORT=7865
AUDIOLDM_PORT=7863

# Local installation paths
COMFYUI_DIR=../ComfyUI
WAN2GP_DIR=../Wan2GP
RVC_DIR=../RVC
AUDIOLDM_DIR=../AudioLDM

# Use Docker instead of local Python
USE_DOCKER=false
```

### Local Python Installation

1. Install each service in its directory:
   ```bash
   # Example for ComfyUI
   git clone https://github.com/comfyanonymous/ComfyUI.git ../ComfyUI
   cd ../ComfyUI
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Update paths in `.env` to point to your installations

3. Start services:
   ```bash
   make services
   ```

### Docker Installation

#### Option 1: Using Docker Commands

```bash
# Set Docker mode in environment
export USE_DOCKER=true

# Or use Docker-specific make targets
make services-docker
make services-docker-stop
```

#### Option 2: Using Docker Compose

```bash
# Start all services
make docker-up

# View logs
make docker-logs

# Check status
make docker-status

# Stop all services
make docker-down
```

## Service Health Checks

Each service has a health check endpoint:

- ComfyUI: `http://localhost:8188/system_stats`
- Wan2GP: `http://localhost:7860/api/health`
- RVC: `http://localhost:7865/api/status`
- AudioLDM: `http://localhost:7863/api/ready`

The service discovery system automatically checks these endpoints.

## Troubleshooting

### Port Already in Use

If a port is already in use:

1. Check what's using the port:
   ```bash
   lsof -i :8188  # Example for ComfyUI
   ```

2. Either stop the conflicting service or change the port in `.env`

### Service Won't Start

1. Check logs:
   ```bash
   make services-logs
   # Or for specific service
   ./scripts/services.sh logs comfyui
   ```

2. Verify the service directory exists and has proper setup:
   ```bash
   ls -la ../ComfyUI  # Example
   ```

3. Try starting manually to see error messages:
   ```bash
   cd ../ComfyUI
   source venv/bin/activate
   python main.py --port 8188
   ```

### Docker Issues

1. Ensure Docker is running:
   ```bash
   docker ps
   ```

2. Check Docker has GPU access (for NVIDIA):
   ```bash
   docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
   ```

3. Pull latest images:
   ```bash
   docker-compose pull
   ```

## Service-Specific Notes

### ComfyUI
- Requires models in `models/` directory
- Custom nodes go in `custom_nodes/`
- Workflows stored in `workflows/`

### Wan2GP
- Optimized for fast video generation
- Lower quality but much faster than ComfyUI
- Good for previews and iterations

### RVC
- Voice models in `models/` directory
- Supports real-time voice conversion
- Requires audio input files

### AudioLDM
- Text-to-audio generation
- Sound effects and ambient audio
- Models downloaded on first use

## Advanced Configuration

### Custom Docker Images

Edit `docker-compose.yml` or set in `.env`:

```bash
COMFYUI_IMAGE=myregistry/comfyui:custom
WAN2GP_IMAGE=myregistry/wan2gp:custom
```

### GPU Assignment

For multi-GPU systems, edit `docker-compose.yml`:

```yaml
environment:
  - CUDA_VISIBLE_DEVICES=0,1  # Use GPUs 0 and 1
```

### Memory Limits

Add to `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      memory: 16G
```

## Integration with Blender

Once services are running, the addon will automatically discover them:

1. Open Blender with the addon
2. Go to addon preferences
3. Click "Discover Services"
4. Services should appear as "Connected"

If auto-discovery fails, you can manually set service URLs in the preferences.