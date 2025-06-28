#!/bin/bash
# Run Blender with the Movie Director addon loaded

set -e  # Exit on error

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    set -a  # automatically export all variables
    source <(grep -E '^[A-Z_].*=' .env)
    set +a  # stop automatically exporting
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "🔌 Activating virtual environment..."
    source venv/bin/activate
fi

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

# Set Blender system scripts path to the installation scripts directory
BLENDER_DIR="$(dirname "$BLENDER_PATH")"
export BLENDER_SYSTEM_SCRIPTS="$BLENDER_DIR/$BLENDER_VERSION/scripts"
echo "📁 BLENDER_SYSTEM_SCRIPTS set to: $BLENDER_SYSTEM_SCRIPTS"

# Bundle dependencies for self-contained addon
echo "📦 Bundling dependencies..."
./scripts/setup.sh bundle

# Auto-install addon for development
echo "🔧 Installing addon for development..."

# Determine Blender user scripts directory (user's AppData on Windows)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows: Use AppData directory
    BLENDER_USER_SCRIPTS="$HOME/AppData/Roaming/Blender Foundation/Blender/$BLENDER_VERSION/scripts/addons"
else
    # Unix systems: Use user config directory
    BLENDER_USER_SCRIPTS="$HOME/.config/blender/$BLENDER_VERSION/scripts/addons"
fi

# Create the addons directory if it doesn't exist
mkdir -p "$BLENDER_USER_SCRIPTS"

# Target addon directory
ADDON_TARGET="$BLENDER_USER_SCRIPTS/blender_movie_director"

# Remove existing installation if present
if [ -e "$ADDON_TARGET" ]; then
    echo "🗑️  Removing existing installation..."
    rm -rf "$ADDON_TARGET"
fi

# On Windows, copy the directory since symlinks require admin privileges
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "📋 Copying addon to Blender (Windows)..."
    cp -r "$PROJECT_ROOT/blender_movie_director" "$ADDON_TARGET"
    echo "✅ Addon copied successfully"
else
    # On Unix systems, create a symlink for easier development
    echo "🔗 Creating symlink to addon..."
    ln -s "$PROJECT_ROOT/blender_movie_director" "$ADDON_TARGET"
    echo "✅ Symlink created successfully"
fi

# Launch options
BLEND_FILE="${1:-$PROJECT_ROOT/bmad_project_template.blend}"

# Check if blend file exists
if [ -f "$BLEND_FILE" ]; then
    echo "📄 Opening: $BLEND_FILE"
else
    echo "📄 Starting with default scene"
    BLEND_FILE=""
fi

# Launch Blender
echo "🚀 Launching Blender with Movie Director addon..."
echo ""
echo "The addon has been automatically installed. To enable it:"
echo "  1. Go to Edit > Preferences > Add-ons"
echo "  2. Search for 'Blender Movie Director'"
echo "  3. Check the box to enable it"
echo "  4. Look for the 'Movie Director' tab in the 3D View sidebar (press N)"
echo ""
echo "For development workflow:"
echo "  - After making code changes, run 'make run' again to update the addon"
echo "  - Then press F8 in Blender to reload scripts"
echo ""

if [ -n "$BLEND_FILE" ]; then
    "$BLENDER_PATH" "$BLEND_FILE"
else
    "$BLENDER_PATH"
fi
