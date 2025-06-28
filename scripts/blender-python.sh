#!/bin/bash
# Access Blender's Python environment and install dependencies using UV

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Try to find Blender
find_blender() {
    # Check BLENDER_PATH environment variable first
    if [ ! -z "$BLENDER_PATH" ] && [ -x "$BLENDER_PATH" ]; then
        echo "$BLENDER_PATH"
        return 0
    fi
    
    # Try common locations
    local blender_paths=(
        "blender"
        "/usr/bin/blender"
        "/usr/local/bin/blender"
        "/opt/blender/blender"
        "/Applications/Blender.app/Contents/MacOS/Blender"
        "C:/Program Files/Blender Foundation/Blender 4.4/blender.exe"
        "$HOME/blender-4.4*/blender"
    )
    
    for path in "${blender_paths[@]}"; do
        if command -v "$path" &> /dev/null || [ -x "$path" ]; then
            echo "$path"
            return 0
        fi
    done
    
    # Try to find with glob patterns
    for pattern in "$HOME"/blender-4*/blender /opt/blender-4*/blender; do
        for path in $pattern; do
            if [ -x "$path" ]; then
                echo "$path"
                return 0
            fi
        done
    done
    
    return 1
}

# Find Blender executable
BLENDER_EXE=$(find_blender)
if [ -z "$BLENDER_EXE" ]; then
    echo -e "${RED}❌ Blender not found${NC}"
    echo -e "${YELLOW}Please set BLENDER_PATH environment variable or add Blender to PATH${NC}"
    echo ""
    echo "Example:"
    echo "  export BLENDER_PATH=/path/to/blender"
    echo "  $0 $*"
    exit 1
fi

echo -e "${GREEN}✅ Found Blender: $BLENDER_EXE${NC}"

# Get Blender version and Python path
BLENDER_VERSION=$("$BLENDER_EXE" --version | grep "Blender" | cut -d' ' -f2 | cut -d'.' -f1-2)
echo -e "${BLUE}📦 Blender version: $BLENDER_VERSION${NC}"

# Find Blender's Python - try different possible locations
find_blender_python() {
    local blender_dir=$(dirname "$BLENDER_EXE")
    local possible_paths=(
        "$blender_dir/$BLENDER_VERSION/python/bin/python"
        "$blender_dir/../$BLENDER_VERSION/python/bin/python"
        "$blender_dir/python/bin/python"
        "$blender_dir/../Resources/$BLENDER_VERSION/python/bin/python"
    )
    
    for path in "${possible_paths[@]}"; do
        if [ -x "$path" ]; then
            echo "$path"
            return 0
        fi
    done
    
    # Windows paths
    local win_paths=(
        "$blender_dir/$BLENDER_VERSION/python/bin/python.exe"
        "$blender_dir/python/bin/python.exe"
    )
    
    for path in "${win_paths[@]}"; do
        if [ -x "$path" ]; then
            echo "$path"
            return 0
        fi
    done
    
    return 1
}

BLENDER_PYTHON=$(find_blender_python)
if [ -z "$BLENDER_PYTHON" ]; then
    echo -e "${RED}❌ Could not find Blender's Python executable${NC}"
    echo -e "${YELLOW}Blender's Python is usually in: <blender_dir>/<version>/python/bin/python${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Found Blender Python: $BLENDER_PYTHON${NC}"

# Handle different command modes
case "$1" in
    "--install-deps"|"--install")
        echo -e "${BLUE}📚 Installing dependencies in Blender's Python environment...${NC}"
        echo ""
        
        # Check if UV is installed
        if ! command -v uv &> /dev/null; then
            echo -e "${RED}❌ UV is not installed. Run './scripts/setup.sh' first${NC}"
            exit 1
        fi
        
        # Install dependencies using UV with Blender's Python
        echo -e "${YELLOW}Installing Blender runtime dependencies...${NC}"
        UV_PYTHON="$BLENDER_PYTHON" uv pip install -r <(echo "
# Blender runtime dependencies (auto-generated)
aiohttp>=3.12.13
pyyaml>=6.0.2
gradio-client>=1.10.4
")
        
        echo -e "${GREEN}✅ Dependencies installed successfully!${NC}"
        ;;
        
    "--install-addon-deps")
        echo -e "${BLUE}📚 Installing addon dependencies from pyproject.toml...${NC}"
        
        # Check if UV is installed
        if ! command -v uv &> /dev/null; then
            echo -e "${RED}❌ UV is not installed. Run './scripts/setup.sh' first${NC}"
            exit 1
        fi
        
        # Install from pyproject.toml blender extras
        UV_PYTHON="$BLENDER_PYTHON" uv pip install -e ".[blender]"
        
        echo -e "${GREEN}✅ Addon dependencies installed!${NC}"
        ;;
        
    "-i"|"--interactive")
        echo -e "${BLUE}🐍 Starting interactive Blender Python console...${NC}"
        echo -e "${YELLOW}Type 'exit()' or Ctrl+D to quit${NC}"
        echo ""
        "$BLENDER_PYTHON" -i
        ;;
        
    "-c"|"--command")
        if [ -z "$2" ]; then
            echo -e "${RED}❌ No command provided${NC}"
            exit 1
        fi
        "$BLENDER_PYTHON" -c "$2"
        ;;
        
    "-m"|"--module")
        if [ -z "$2" ]; then
            echo -e "${RED}❌ No module provided${NC}"
            exit 1
        fi
        shift
        "$BLENDER_PYTHON" -m "$@"
        ;;
        
    "--version"|"-V")
        "$BLENDER_PYTHON" --version
        ;;
        
    "--help"|"-h")
        echo "Blender Python Helper Script"
        echo ""
        echo "Usage: $0 [option] [args...]"
        echo ""
        echo "Options:"
        echo "  --install-deps       Install runtime dependencies in Blender"
        echo "  --install-addon-deps Install addon dependencies from pyproject.toml"
        echo "  -i, --interactive    Start interactive Python console"
        echo "  -c, --command CMD    Execute Python command"
        echo "  -m, --module MOD     Run Python module"
        echo "  --version, -V        Show Python version"
        echo "  --help, -h           Show this help"
        echo "  <script.py>          Run Python script"
        echo ""
        echo "Examples:"
        echo "  $0 --install-deps"
        echo "  $0 -i"
        echo "  $0 -c 'import bpy; print(bpy.app.version)'"
        echo "  $0 -m pip list"
        echo "  $0 test_script.py"
        ;;
        
    "")
        echo -e "${RED}❌ No arguments provided${NC}"
        echo "Use '$0 --help' for usage information"
        exit 1
        ;;
        
    *)
        # Assume it's a script file
        if [ ! -f "$1" ]; then
            echo -e "${RED}❌ Script not found: $1${NC}"
            exit 1
        fi
        echo -e "${BLUE}🐍 Running script: $1${NC}"
        "$BLENDER_PYTHON" "$@"
        ;;
esac