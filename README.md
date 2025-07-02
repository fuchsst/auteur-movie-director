# Auteur Movie Director

A web-based platform that transforms narrative concepts into cinematic sequences using AI agents and distributed generative engines.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/auteur-movie-director.git
cd auteur-movie-director

# Run automated setup
npm run setup

# Start development servers
npm run dev

# Open in browser
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```

For detailed setup instructions, see [docs/SETUP.md](./docs/SETUP.md).

## Overview

**Auteur Movie Director** is a revolutionary web-based platform that empowers directors to transform their narrative visions into cinematic sequences using AI agents and distributed processing. Built on modern web technologies and the regenerative content model, it provides a director-centric workflow that enables creative visionaries to maintain artistic control while leveraging AI-powered production capabilities. Global teams can collaborate in real-time on professional film production without hardware limitations.

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
auteur-movie-director/
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

- Node.js 18+ and npm 9+
- Python 3.11+
- Git & Git LFS
- Docker (optional, for containerized services)
- FFmpeg (optional, for video processing)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/generative-media-studio.git
   cd generative-media-studio
   ```

2. **Install npm dependencies**
   ```bash
   npm install
   ```

3. **Run automated setup**
   ```bash
   npm run setup
   # This will:
   # - Check prerequisites (Node, Python, Git)
   # - Install backend Python dependencies
   # - Install frontend npm dependencies
   # - Create .env files from templates
   # - Set up workspace directories
   ```

4. **Start development servers**
   ```bash
   npm run dev
   # Starts both frontend (port 3000) and backend (port 8000) concurrently
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/docs
   - WebSocket: ws://localhost:8000/ws

### Alternative: Using Make

If you prefer, you can also use the traditional Makefile:
```bash
make help     # View all available commands
make dev      # Start development servers
make test     # Run tests
make lint     # Run linters
```

### NPM Scripts

All project tasks are managed through npm scripts:

```bash
# Setup & Installation
npm run setup              # Complete project setup
npm run setup:check        # Check prerequisites only
npm run setup:env          # Create environment files

# Development
npm run dev                # Start frontend + backend concurrently
npm run dev:backend        # Start backend only
npm run dev:frontend       # Start frontend only

# Testing
npm run test               # Run all tests
npm run test:backend       # Backend tests only
npm run test:frontend      # Frontend tests only
npm run test:integration   # Integration tests

# Code Quality
npm run lint               # Run linters
npm run format             # Auto-format code

# Utilities
npm run clean              # Clean build artifacts
npm run workspace:init     # Initialize workspace
npm run project:create     # Create new project

# Docker (optional)
npm run docker:build       # Build containers
npm run docker:up          # Start with docker-compose
npm run docker:down        # Stop containers
```

### Environment Variables

Key configuration in `.env`:

```bash
# Backend Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# Frontend Configuration
FRONTEND_HOST=0.0.0.0
FRONTEND_PORT=3000

# Workspace Configuration
WORKSPACE_ROOT=./workspace
DEFAULT_QUALITY=standard

# Development Settings
DEBUG=true
LOG_LEVEL=INFO

# Git Configuration
GIT_AUTO_COMMIT=false
GIT_LFS_ENABLED=true
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
