# Development Scripts

Quick reference for Generative Media Studio development scripts.

## Script Usage Guide

### Environment Setup
```bash
./scripts/setup.sh [dev|test] [--clean]
```
- **When to use**: First time setup or when dependencies change
- `dev` (default): Install all dependencies including dev/test tools
- `test`: Install only test dependencies
- `--clean`: Remove existing environments and start fresh
- **Example**: `./scripts/setup.sh dev --clean` after dependency issues

### Running Tests
```bash
./scripts/test.sh [all|unit|integration|coverage|lint|format|quick]
```
- **When to use**: Before committing code
- `all` (default): Run everything
- `unit`: Unit tests only
- `integration`: Integration tests only  
- `coverage`: Generate coverage report
- `lint`: Check code quality
- `format`: Auto-format code
- `quick`: Fast tests without integration
- **Example**: `./scripts/test.sh quick` for rapid feedback

### Backend Services
```bash
./scripts/services.sh [start|stop|status|restart|logs] [service_name|all]
```
- **When to use**: Managing AI backend services (ComfyUI, etc.)
- `start`: Start services
- `stop`: Stop services
- `status`: Check service health
- `restart`: Restart services
- `logs`: View service logs
- **Example**: `./scripts/services.sh start comfyui`

### Package Creation
```bash
./scripts/package.sh
```
- **When to use**: Create distribution package
- Creates a deployable package of the application
- **Example**: `./scripts/package.sh` before release

## Common Workflows

### Initial Setup
```bash
# Clone repository
git clone <repo-url>
cd generative-media-studio

# Install dependencies and setup
npm install
npm run setup
```

### Development Workflow
```bash
# Start development servers
npm run dev

# In another terminal, run tests in watch mode
npm run test:watch

# Before committing
npm run lint
npm run format
npm run test
```

### Service Management
```bash
# Start all backend services
./scripts/services.sh start all

# Check status
./scripts/services.sh status

# View logs
./scripts/services.sh logs

# Stop when done
./scripts/services.sh stop all
```

## Script Details

All scripts include:
- Error handling with clear messages
- Help text (`--help` flag)
- Cross-platform compatibility
- Automatic environment activation
- Color-coded output for clarity

## Troubleshooting

### Permission Denied
```bash
chmod +x scripts/*.sh
```

### Script Not Found
Ensure you're in the project root directory.

### Environment Issues
```bash
# Clean reinstall
./scripts/setup.sh dev --clean
```

### Service Won't Start
Check logs and ensure ports are available:
```bash
./scripts/services.sh logs <service_name>
lsof -i :8188  # Check if port is in use
```