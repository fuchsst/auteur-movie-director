# Development Scripts

Quick reference for Blender Movie Director development scripts.

## Script Usage Guide

### Environment Setup
```bash
./scripts/setup.sh [dev|test] [--clean]
```
- **When to use**: First time setup or when dependencies change
- `dev` (default): Install all dependencies including dev/test tools
- `test`: Install only test dependencies
- `--clean`: Remove existing venv and start fresh
- **Example**: `./scripts/setup.sh dev --clean` after Python version issues

### Running Blender
```bash
./scripts/run-blender.sh [blend_file]
```
- **When to use**: Test addon in Blender with automatic loading
- Loads addon in development mode
- Optional: Pass .blend file to open
- **Example**: `./scripts/run-blender.sh my_project.blend`

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

### Running Python Scripts
```bash
./scripts/run-script.sh <script.py> [args]
```
- **When to use**: Run Python scripts with project environment
- Activates venv and sets PYTHONPATH
- **Example**: `./scripts/run-script.sh tests/manual_test_discovery.py`

### Blender Python Access
```bash
./scripts/blender-python.sh [-i|-c 'code'|script.py]
```
- **When to use**: Debug or test Blender Python API
- `-i`: Interactive Blender Python console
- `-c`: Run Python command
- `script.py`: Run script in Blender
- **Example**: `./scripts/blender-python.sh -c 'import bpy; print(bpy.app.version)'`

### Backend Services
```bash
./scripts/dev-server.sh [all|stop|status|comfyui|wan2gp|rvc|audioldm]
```
- **When to use**: Start/stop backend AI services
- `all` (default): Start all services
- `stop`: Stop all services
- `status`: Check service status
- Service names: Start specific service
- **Example**: `./scripts/dev-server.sh status`

### Packaging Addon
```bash
./scripts/package.sh [filename]
```
- **When to use**: Create distribution .zip file
- Packages addon with proper structure
- Excludes development files
- **Example**: `./scripts/package.sh blender-movie-director-v1.0.0`

## Common Workflows

### Initial Setup
```bash
git clone <repo>
cd blender-movie-director
./scripts/setup.sh dev
```

### Daily Development
```bash
# Start backend services
./scripts/dev-server.sh all

# Run Blender with addon
./scripts/run-blender.sh

# Quick test after changes
./scripts/test.sh quick

# Full test before commit
./scripts/test.sh all
```

### Troubleshooting
```bash
# Python version issues
./scripts/setup.sh dev --clean

# Test specific functionality
./scripts/run-script.sh tests/manual_test_discovery.py

# Check Blender integration
./scripts/blender-python.sh -i
```

### Release Preparation
```bash
# Format and lint
./scripts/test.sh format
./scripts/test.sh lint

# Full test suite
./scripts/test.sh all

# Create package
./scripts/package.sh
```

## Environment Variables

Set in `.env` file:
- `BLENDER_PATH`: Custom Blender executable path
- `COMFYUI_PORT`: ComfyUI service port (default: 8188)
- `WAN2GP_PORT`: Wan2GP service port (default: 7860)
- `DEBUG`: Enable debug mode (true/false)

## Tips

1. Always run `setup.sh` after pulling new changes
2. Use `--clean` flag if encountering dependency conflicts
3. Run `test.sh quick` frequently during development
4. Use `blender-python.sh` to debug Blender API issues
5. Check service status before running integration tests