#!/bin/bash
# Run Blender with the Movie Director addon loaded

set -e  # Exit on error

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "🔌 Activating virtual environment..."
    source venv/bin/activate
fi

# Set Python path to include our addon
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Default Blender executable (can be overridden with BLENDER_PATH env var)
BLENDER_PATH="${BLENDER_PATH:-blender}"

# Check if Blender is available
if ! command -v "$BLENDER_PATH" &> /dev/null; then
    echo "❌ Blender not found at: $BLENDER_PATH"
    echo ""
    echo "Please install Blender or set the BLENDER_PATH environment variable:"
    echo "  export BLENDER_PATH=/path/to/blender"
    echo ""
    echo "Download Blender from: https://www.blender.org/download/"
    exit 1
fi

# Get Blender version
BLENDER_VERSION=$("$BLENDER_PATH" --version | grep -oE 'Blender [0-9]+\.[0-9]+' | cut -d' ' -f2)
echo "🎬 Found Blender $BLENDER_VERSION at: $BLENDER_PATH"

# Prepare Blender startup script
STARTUP_SCRIPT=$(cat << 'EOF'
import sys
import os

# Add addon directory to Python path
addon_path = os.environ.get('ADDON_PATH', '.')
if addon_path not in sys.path:
    sys.path.insert(0, addon_path)

# Enable the addon
import bpy
addon_name = "blender_movie_director"

# Disable existing version if any
if addon_name in bpy.context.preferences.addons:
    bpy.ops.preferences.addon_disable(module=addon_name)

# Enable our development version
try:
    bpy.ops.preferences.addon_enable(module=addon_name)
    print(f"✅ {addon_name} addon enabled successfully")
except Exception as e:
    print(f"❌ Failed to enable addon: {e}")
    print("Make sure to run ./scripts/setup.sh first")

# Save preferences
bpy.ops.wm.save_userpref()
EOF
)

# Launch options
BLEND_FILE="${1:-$PROJECT_ROOT/bmad_project_template.blend}"

# Check if blend file exists
if [ -f "$BLEND_FILE" ]; then
    echo "📄 Opening: $BLEND_FILE"
else
    echo "📄 Starting with default scene"
    BLEND_FILE=""
fi

# Set addon path environment variable
export ADDON_PATH="$PROJECT_ROOT"

# Launch Blender
echo "🚀 Launching Blender with Movie Director addon..."
echo ""

if [ -n "$BLEND_FILE" ]; then
    "$BLENDER_PATH" "$BLEND_FILE" --python-expr "$STARTUP_SCRIPT"
else
    "$BLENDER_PATH" --python-expr "$STARTUP_SCRIPT"
fi