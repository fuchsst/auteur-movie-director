# STORY-020: Docker Compose Orchestration

## Story
As a developer, I need a Docker Compose configuration that orchestrates all platform services, including the web application and AI model containers, with proper networking and volume management.

## Acceptance Criteria
- [x] docker-compose.yml defines all core services (frontend, backend, redis)
- [x] Service dependencies are properly configured
- [x] Named volumes persist data across container restarts
- [x] Workspace directory is mounted correctly in all services
- [x] Network configuration allows inter-service communication
- [x] Environment variables are properly passed to containers
- [x] Health checks ensure services start in correct order

## Technical Details

### Service Architecture

#### Core Services
```yaml
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - BACKEND_URL=http://backend:8000
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
      - /app/node_modules

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - WORKSPACE_ROOT=/workspace
    depends_on:
      - redis
    volumes:
      - ./backend:/app
      - workspace:/workspace

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
```

#### AI Model Services (Optional)
```yaml
  comfyui:
    image: auteur-movie-director/comfyui:latest
    ports:
      - "8188:8188"
    volumes:
      - models:/models
      - workspace:/workspace
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  litellm:
    image: auteur-movie-director/litellm:latest
    ports:
      - "8001:8000"
    volumes:
      - llm_models:/models
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

### Volume Configuration

```yaml
volumes:
  workspace:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${WORKSPACE_ROOT:-./workspace}
  
  redis_data:
  models:
  llm_models:
```

### Network Configuration

```yaml
networks:
  default:
    name: auteur-network
    driver: bridge
```

### Environment Files

Support multiple environment configurations:
- `.env` - Default environment variables
- `.env.development` - Development overrides
- `.env.production` - Production settings

### Health Checks

Implement health checks for service startup order:

```yaml
backend:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s
```

### Compose Profiles

Use profiles for optional services:

```yaml
services:
  comfyui:
    profiles:
      - ai
      - comfyui
    # ... rest of config

  litellm:
    profiles:
      - ai
      - llm
    # ... rest of config
```

### Override Files

Support compose override files for different configurations:
- `docker-compose.override.yml` - Local development overrides
- `docker-compose.prod.yml` - Production configuration
- `docker-compose.gpu.yml` - GPU-specific settings

### Resource Management

Configure resource limits for services:

```yaml
backend:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 4G
      reservations:
        cpus: '1'
        memory: 2G
```

## Implementation Notes

### GPU Support
- Check for NVIDIA Docker runtime
- Provide fallback for CPU-only mode
- Document GPU requirements clearly

### Data Persistence
- All user data in named volumes
- Workspace mounted from host
- Database data persisted
- Model files cached in volumes

### Security Considerations
- Don't expose unnecessary ports
- Use internal networks for service communication
- Set proper file permissions on volumes
- Don't include secrets in compose file

### Development Workflow
- Support hot-reloading for development
- Volume mount source code directories
- Exclude node_modules and __pycache__
- Enable debug modes via environment

## Dependencies
- Docker Engine 20.10+
- Docker Compose v2
- NVIDIA Container Toolkit (for GPU support)
- Makefile from STORY-019

## Story Points: 5

## Priority: High

## Implementation Status

**Completed: February 3, 2025**

All acceptance criteria have been met:

✅ **Docker Compose Files**
- docker-compose.yml - AI services configuration
- docker-compose.core.yml - Core platform services
- docker-compose.dev.yml - Development configuration
- docker-compose.test.yml - Test environment

✅ **Service Profiles**
Added profiles to all AI services:
- `ai` - All AI services
- `comfyui` - ComfyUI image generation
- `audio` - RVC and AudioLDM services
- `video` - Wan2GP video generation
- `full` - All services combined

✅ **Override File**
Created docker-compose.override.yml with:
- Development environment variables
- Volume mounts for local development
- Debug logging configuration
- Service-specific overrides

✅ **Makefile Integration**
Added profile-based commands:
- `make docker-up-ai`
- `make docker-up-comfyui`
- `make docker-up-audio`
- `make docker-up-video`
- `make docker-up-full`
- `make docker-clean`

✅ **Configuration**
- Named volumes for persistence
- Health checks on all services
- Proper service dependencies
- GPU support for AI services
- Network isolation

The Docker Compose orchestration is now fully implemented with profile support, override capabilities, and comprehensive Makefile integration.

## Status: ✅ Completed

## Related Stories
- STORY-019: Makefile Development Interface
- STORY-021: Function Runner Foundation