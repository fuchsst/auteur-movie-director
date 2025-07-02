# Development Environment Setup Guide

This guide will help you set up your development environment for the Auteur Movie Director project.

## Prerequisites

Before starting, ensure you have the following installed:

### Required
- **Node.js** (v18.0.0 or higher) - [Download](https://nodejs.org/)
- **Python** (v3.11 or higher) - [Download](https://www.python.org/)
- **Git** - [Download](https://git-scm.com/)

### Optional (Recommended)
- **Docker** - [Download](https://www.docker.com/)
- **Git LFS** - [Download](https://git-lfs.github.com/)
- **FFmpeg** - [Download](https://ffmpeg.org/)
- **NVIDIA GPU** with CUDA support (for AI services)

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/auteur-movie-director.git
   cd auteur-movie-director
   ```

2. **Run the automated setup**
   ```bash
   npm run setup
   ```
   
   This will:
   - Check all prerequisites
   - Install dependencies for frontend and backend
   - Create environment configuration files
   - Set up the workspace directory structure

3. **Start the development servers**
   ```bash
   npm run dev
   ```
   
   This starts both the backend (FastAPI) and frontend (SvelteKit) servers.

4. **Open the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Manual Setup

If you prefer to set up components individually:

### 1. Check Prerequisites
```bash
npm run setup:check
```

### 2. Create Environment Files
```bash
npm run setup:env
```

This creates `.env` files from templates. Review and update:
- `.env` - Main configuration
- `backend/.env` - Backend-specific settings
- `frontend/.env.local` - Frontend-specific settings

### 3. Install Dependencies

#### Backend (Python)
```bash
cd backend
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development
```

#### Frontend (Node.js)
```bash
cd frontend
npm install  # or pnpm install
```

### 4. Validate Environment
```bash
npm run validate
```

## Environment Configuration

### Core Settings (.env)

```env
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
```

### AI Service Configuration

If using AI services, configure these endpoints:

```env
# AI Service Endpoints
COMFYUI_HOST=localhost
COMFYUI_PORT=8188
WAN2GP_HOST=localhost
WAN2GP_PORT=7860
RVC_HOST=localhost
RVC_PORT=7865
AUDIOLDM_HOST=localhost
AUDIOLDM_PORT=7863
```

## Docker Services (Optional)

To run AI services locally using Docker:

```bash
# Start all services
npm run docker:up

# View logs
npm run docker:logs

# Stop services
npm run docker:down
```

### Docker Requirements
- NVIDIA Docker runtime for GPU support
- At least 16GB VRAM (RTX 4080 or better)
- 50GB+ free disk space for models

## Available Commands

### Development
- `npm run dev` - Start both frontend and backend in development mode
- `npm run dev:backend` - Start only the backend server
- `npm run dev:frontend` - Start only the frontend server

### Testing
- `npm run test` - Run all tests
- `npm run test:backend` - Run backend tests
- `npm run test:frontend` - Run frontend tests
- `npm run test:integration` - Run integration tests

### Code Quality
- `npm run lint` - Check code quality
- `npm run format` - Auto-format code

### Build & Production
- `npm run build` - Build frontend for production
- `npm run start` - Start in production mode

### Utilities
- `npm run clean` - Clean build artifacts and caches
- `npm run validate` - Validate environment setup
- `npm run workspace:init` - Initialize workspace structure
- `npm run project:create` - Create a new project

## Troubleshooting

### Common Issues

#### Port Already in Use
If you get a "port already in use" error:
```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process or change the port in .env
```

#### Python Module Not Found
```bash
# Ensure you're using the correct Python version
python --version  # Should be 3.11+

# Try using pip3 explicitly
pip3 install -r requirements.txt
```

#### Node Version Issues
```bash
# Check Node version
node --version  # Should be 18+

# Use nvm to switch versions
nvm use 18
```

#### Docker GPU Access
Ensure NVIDIA Docker runtime is installed:
```bash
# Test GPU access
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### Platform-Specific Notes

#### Windows
- Use PowerShell or Git Bash for commands
- May need to run as Administrator for Docker
- Path separators in .env should use forward slashes

#### macOS
- Install Xcode Command Line Tools if prompted
- Docker Desktop required for Docker support
- No native GPU support for CUDA

#### Linux
- May need to add user to docker group
- Install NVIDIA drivers for GPU support
- Use package manager for system dependencies

## Getting Help

- Check the [FAQ](./FAQ.md)
- Join our [Discord](https://discord.gg/generative-media-studio)
- Open an [issue](https://github.com/yourusername/generative-media-studio/issues)

## Next Steps

1. Review the [Architecture Guide](./ARCHITECTURE.md)
2. Read the [Development Workflow](./DEVELOPMENT.md)
3. Explore the [API Documentation](http://localhost:8000/docs)
4. Try the [Tutorial](./TUTORIAL.md)