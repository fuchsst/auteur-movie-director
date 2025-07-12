# Docker Setup Instructions

## Quick Start

1. **Prerequisites**
   - Docker Desktop installed and running
   - At least 4GB RAM allocated to Docker
   - Ports 3000 and 8000 available

2. **Start the Application**
   ```bash
   ./start.sh
   ```
   This will:
   - Check Docker is running
   - Create .env file if needed
   - Create workspace and models directories
   - Start all services in background
   - Show access URLs

3. **Access the Application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/api/docs

## Helper Scripts

### `./start.sh`
Starts all services in detached mode (background).

### `./stop.sh`
Stops all services and removes containers.

### `./logs.sh`
Shows live logs from all services. Press Ctrl+C to exit.

### `./dev.sh`
Starts services in foreground with live logs (good for development).

### `./restart.sh`
Stops and then starts all services.

## Volume Mounts

The development setup mounts these directories:
- `./workspace` → `/workspace` - Where projects are stored
- `./models` → `/models` - AI model storage (if using local models)
- `./frontend` → `/app` - Frontend source code (hot reload)
- `./backend` → `/app` - Backend source code (hot reload)

## Troubleshooting

### Port Already in Use
If you get port conflicts:
1. Check what's using the ports:
   ```bash
   lsof -i :3000
   lsof -i :8000
   ```
2. Either stop those services or change ports in `.env`

### Docker Not Running
Make sure Docker Desktop is started before running the scripts.

### Permission Issues
If you get permission errors, make sure the scripts are executable:
```bash
chmod +x *.sh
```

### Redis Connection Issues
The backend will show Redis connection warnings, but it will still work for basic functionality.

## Environment Variables

Create a `.env` file (copied from `.env.example`) to customize:
- `FRONTEND_PORT` - Frontend port (default: 3000)
- `BACKEND_PORT` - Backend port (default: 8000)
- `REDIS_PORT` - Redis port (default: 6379)
- `MODELS_PATH` - Path to models directory (default: ./models)
- `LOG_LEVEL` - Logging level (default: INFO)
- `DEBUG` - Debug mode (default: true)