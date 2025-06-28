#!/bin/bash
# Run Python commands inside Blender's Python environment

set -e  # Exit on error

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Default Blender executable
BLENDER_PATH="${BLENDER_PATH:-blender}"

# Check if Blender is available
if ! command -v "$BLENDER_PATH" &> /dev/null; then
    echo "❌ Blender not found at: $BLENDER_PATH"
    echo ""
    echo "Please install Blender or set the BLENDER_PATH environment variable:"
    echo "  export BLENDER_PATH=/path/to/blender"
    exit 1
fi

# Set Python path to include our addon
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
export ADDON_PATH="$PROJECT_ROOT"

# Determine mode
if [ "$1" == "-c" ]; then
    # Execute command mode
    shift
    PYTHON_CMD="$@"
    
    echo "🐍 Running Python command in Blender..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    "$BLENDER_PATH" --background --python-expr "
import sys
import os
sys.path.insert(0, os.environ.get('ADDON_PATH', '.'))
$PYTHON_CMD
"

elif [ "$1" == "-i" ] || [ -z "$1" ]; then
    # Interactive mode
    echo "🐍 Starting Blender Python interactive shell..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Available modules:"
    echo "  - bpy: Blender Python API"
    echo "  - blender_movie_director: Our addon"
    echo ""
    
    "$BLENDER_PATH" --background --python-console

elif [ -f "$1" ]; then
    # Script file mode
    SCRIPT_PATH="$1"
    shift
    
    echo "🐍 Running script in Blender: $SCRIPT_PATH"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    "$BLENDER_PATH" --background --python "$SCRIPT_PATH" -- "$@"

else
    echo "❌ Invalid usage"
    echo ""
    echo "Usage:"
    echo "  ./scripts/blender-python.sh              # Interactive shell"
    echo "  ./scripts/blender-python.sh -i           # Interactive shell"
    echo "  ./scripts/blender-python.sh -c 'command' # Execute command"
    echo "  ./scripts/blender-python.sh script.py    # Run script file"
    echo ""
    echo "Examples:"
    echo "  ./scripts/blender-python.sh -c 'import bpy; print(bpy.app.version)'"
    echo "  ./scripts/blender-python.sh examples/test_addon.py"
    exit 1
fi