# Movie Director (BMAD)

## Overview

**Movie Director (BMAD)** is a revolutionary web-based generative film studio that transforms narrative concepts into cinematic sequences using AI agents and distributed processing. Built on modern web technologies and the regenerative content model, BMAD enables global teams to collaborate in real-time on professional film production without hardware limitations.

### Key Features

- 🎬 **Node-Based Production Canvas** - Visual workflow editor with real-time collaboration
- 🤖 **AI Agent Orchestration** - Intelligent agents manage the entire production pipeline
- 🎨 **Quality-Tiered Generation** - Three levels (Low/Standard/High) for all content
- 🌐 **Cloud-Native Architecture** - No local GPU required, scales with demand
- 👥 **Real-Time Collaboration** - Multiple users work simultaneously via WebSocket
- 📦 **Regenerative Content Model** - Store parameters, regenerate content anytime
- 🗂️ **Git-Based Version Control** - Complete history with Git + Git LFS
- 🚀 **Heterogeneous Backend Support** - ComfyUI, Wan2GP, and custom models

## Architecture Overview

### Three-Tier System

1. **Frontend (SvelteKit)**
   - Browser-based interface with Svelte Flow
   - Real-time WebSocket synchronization
   - Responsive design for any device

2. **Backend (FastAPI + Celery)**
   - RESTful API and WebSocket server
   - Distributed task processing
   - Quality-based queue routing

3. **Storage & Processing**
   - PostgreSQL for metadata
   - S3/File storage for media
   - Docker containers for model execution
   - Git + Git LFS for version control

### Quality Tier System

All generation tasks support three quality levels:

| Quality | Use Case | Performance | Resource Usage |
|---------|----------|-------------|----------------|
| **Low** | Draft/Preview | Fast (1-2 min) | 8GB VRAM |
| **Standard** | Production | Balanced (3-5 min) | 16GB VRAM |
| **High** | Premium/Final | Best (5-10 min) | 24GB+ VRAM |

## Project Structure

```
blender-movie-director/
├── backend/
│   ├── api/                    # FastAPI application
│   │   ├── endpoints/          # REST endpoints
│   │   ├── websocket/          # WebSocket handlers
│   │   └── models/             # Pydantic models
│   ├── pipelines/              # Containerized model pipelines
│   │   ├── image_generation/
│   │   │   ├── low/           # SD 1.5 container
│   │   │   ├── standard/      # Flux Schnell container
│   │   │   └── high/          # Flux Dev FP16 container
│   │   ├── video_generation/
│   │   │   ├── low/           # AnimateDiff SD1.5
│   │   │   ├── standard/      # SVD or equivalent
│   │   │   └── high/          # Latest video models
│   │   └── audio_generation/
│   │       └── [quality tiers]
│   ├── workers/               # Celery workers
│   │   ├── gpu_workers.py     # GPU task processing
│   │   ├── cpu_workers.py     # CPU task processing
│   │   └── function_runner.py # Heterogeneous model execution
│   └── shared/                # Shared utilities
│       ├── database/          # Database models
│       ├── storage/           # S3/file handling
│       └── project_paths.py   # Path management
│
├── frontend/                  # SvelteKit application
│   ├── src/
│   │   ├── routes/           # Page components
│   │   ├── lib/              # Shared components
│   │   │   ├── nodes/        # Custom node types
│   │   │   ├── stores/       # Svelte stores
│   │   │   └── websocket/    # Real-time client
│   │   └── app.html          # App template
│   └── static/               # Static assets
│
├── models/                    # Model storage (volume mount)
│   ├── checkpoints/          # Base models
│   ├── loras/                # LoRA models
│   └── embeddings/           # Text embeddings
│
├── projects/                  # User projects (volume mount)
│   └── PROJECT_NAME/         # Individual project
│       ├── project.json      # Project manifest
│       ├── .git/             # Git repository
│       ├── 01_Assets/        # Source materials
│       ├── 02_Source_Creative/ # Scripts, canvases
│       ├── 03_Renders/       # Generated outputs
│       └── [other dirs]      # See PRD-008
│
├── docker-compose.yml         # Development orchestration
├── .env.example              # Environment template
└── Makefile                  # Project commands
```

## Development Setup

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)
- Git & Git LFS
- Make (for running commands)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/blender-movie-director.git
   cd blender-movie-director
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Configure Docker volumes**
   ```bash
   # Create directories for persistent data
   mkdir -p ./models ./projects ./postgres_data
   ```

4. **Start development environment**
   ```bash
   make dev
   # This starts all services with docker-compose
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/docs
   - Flower (Celery): http://localhost:5555

### Environment Variables

Key configuration in `.env`:

```bash
# Database
DATABASE_URL=postgresql://user:password@postgres:5432/bmad

# Redis
REDIS_URL=redis://redis:6379

# S3/Storage
STORAGE_TYPE=local  # or 's3'
STORAGE_PATH=/app/storage

# GPU Configuration
GPU_WORKERS_LOW=2
GPU_WORKERS_STANDARD=1
GPU_WORKERS_HIGH=1

# Quality Settings
DEFAULT_QUALITY=standard

# Authentication
JWT_SECRET=your-secret-key
```

## Container Architecture

### Pipeline Containers

Each quality tier runs in isolated Docker containers:

```dockerfile
# Example: pipelines/image_generation/standard/Dockerfile
FROM pytorch/pytorch:2.0.1-cuda11.8-cudnn8-runtime

# Install dependencies
RUN pip install diffusers transformers accelerate

# Copy pipeline code
COPY pipeline.py /app/

# Volume mounts
VOLUME ["/models", "/inputs", "/outputs"]

# Run pipeline
CMD ["python", "/app/pipeline.py"]
```

### Volume Mounts

All containers share common volumes:

- `/models` - Read-only model weights
- `/inputs` - Input data from projects
- `/outputs` - Generated content
- `/projects` - Project file structure

## API Overview

### Core Endpoints

- `POST /api/projects` - Create new project
- `GET /api/projects/{id}/canvas` - Load project canvas
- `POST /api/nodes/generate` - Start generation task
- `GET /api/assets/{type}` - List assets (characters, styles, etc.)
- `POST /api/characters/{id}/train` - Train character LoRA

### WebSocket Events

- `client:node.update` - Node position/data changes
- `server:generation.progress` - Task progress updates
- `server:canvas.sync` - Canvas state synchronization

## Development Commands

All commands use the Makefile:

```bash
# Development
make dev              # Start all services
make dev-frontend     # Frontend only with hot reload
make dev-backend      # Backend only with auto-reload

# Testing
make test             # Run all tests
make test-frontend    # Frontend tests only
make test-backend     # Backend tests only

# Production
make build            # Build all containers
make deploy           # Deploy to production

# Utilities
make logs             # View all logs
make shell-backend    # Backend shell
make db-migrate       # Run migrations
make clean            # Clean volumes
```

## Contributing

We follow the BMAD development methodology:

1. **Planning** - Create detailed PRDs in `.bmad-core/prds/`
2. **Implementation** - Follow PRD specifications exactly
3. **Testing** - Comprehensive test coverage required
4. **Documentation** - Update relevant documentation

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## Architecture Decisions

### Why Web-Based?

- **Accessibility** - Use from any device without installation
- **Collaboration** - Real-time multi-user editing
- **Scalability** - Leverage cloud GPU resources
- **Maintenance** - Centralized updates and deployment

### Why Quality Tiers?

- **Flexibility** - Users choose speed vs quality
- **Resource Optimization** - Efficient GPU utilization
- **Cost Management** - Pay for what you need
- **Progressive Workflow** - Draft → Refine → Finalize

### Why Regenerative Model?

- **Storage Efficiency** - 95% reduction in storage costs
- **Infinite Iterations** - Regenerate with new parameters
- **Future-Proof** - Upgrade with better models later
- **Collaboration** - Share projects without large files

## Roadmap

### Phase 1: Core Infrastructure ✅
- FastAPI backend with Celery
- SvelteKit frontend with Svelte Flow
- Basic node types and generation

### Phase 2: Advanced Features 🚧
- Character consistency engine
- Style framework
- Script breakdown system

### Phase 3: Production Features 📋
- Multi-user collaboration
- Advanced models (InfiniteYou, DreamO)
- Template marketplace

### Phase 4: Enterprise 🔮
- Multi-tenant architecture
- Custom model training
- API for third-party integration

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

## Support

- Documentation: [docs.bmad.ai](https://docs.bmad.ai)
- Discord: [discord.gg/bmad](https://discord.gg/bmad)
- Issues: [GitHub Issues](https://github.com/your-org/blender-movie-director/issues)

---
