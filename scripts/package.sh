#!/bin/bash
# Package the Blender Movie Director addon for distribution

set -e  # Exit on error

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Addon name and version
ADDON_NAME="blender_movie_director"
VERSION=$(python -c "import re; print(re.search(r'version\s*=\s*\"([^\"]+)\"', open('pyproject.toml').read()).group(1))")

# Output directory
OUTPUT_DIR="${OUTPUT_DIR:-dist}"
mkdir -p "$OUTPUT_DIR"

# Package filename
if [ -n "$1" ]; then
    PACKAGE_NAME="$1"
else
    PACKAGE_NAME="${ADDON_NAME}_v${VERSION}.zip"
fi

OUTPUT_PATH="$OUTPUT_DIR/$PACKAGE_NAME"

echo "📦 Packaging Blender Movie Director addon..."
echo "  Version: $VERSION"
echo "  Output: $OUTPUT_PATH"
echo ""

# Create temporary directory for packaging
TEMP_DIR=$(mktemp -d)
ADDON_DIR="$TEMP_DIR/$ADDON_NAME"

# Copy addon files
echo "📂 Copying addon files..."
cp -r "$ADDON_NAME" "$ADDON_DIR"

# Copy essential files to addon root
cp -r workflows "$ADDON_DIR/"
cp -r config "$ADDON_DIR/"

# Remove development files
echo "🧹 Cleaning up development files..."
find "$ADDON_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$ADDON_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true
find "$ADDON_DIR" -type f -name "*.pyo" -delete 2>/dev/null || true
find "$ADDON_DIR" -type f -name ".DS_Store" -delete 2>/dev/null || true
find "$ADDON_DIR" -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
find "$ADDON_DIR" -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
find "$ADDON_DIR" -type f -name "CLAUDE.md" -delete 2>/dev/null || true

# Create addon info file
echo "📝 Creating addon info..."
cat > "$ADDON_DIR/README.md" << EOF
# Blender Movie Director v$VERSION

AI-powered generative film studio integrated into Blender.

## Installation

1. Download the latest release
2. In Blender: Edit > Preferences > Add-ons
3. Click "Install..." and select the downloaded .zip file
4. Enable "Sequencer: Blender Movie Director"

## Requirements

- Blender 4.0 or higher
- Python 3.11 (included with Blender)
- Local AI backend services (ComfyUI, Wan2GP, etc.)

## Documentation

See the full documentation at: https://github.com/yourusername/blender-movie-director

## License

MIT License - see LICENSE file for details
EOF

# Create requirements file for users
echo "📋 Creating user requirements..."
cat > "$ADDON_DIR/requirements.txt" << EOF
# Minimal requirements for running the addon
# Install these in Blender's Python environment if needed

aiohttp>=3.9.0
pyyaml>=6.0
numpy<2.0

# Optional AI integration (install if using AI features)
# crewai>=0.1.0
# litellm>=1.0.0
# gradio_client>=0.8.0
EOF

# Create the zip file
echo "🗜️  Creating zip archive..."
cd "$TEMP_DIR"
zip -r "$OUTPUT_PATH" "$ADDON_NAME" -x "*.git*" "*test*" "*tests*"

# Clean up
rm -rf "$TEMP_DIR"

# Calculate file size
SIZE=$(du -h "$OUTPUT_PATH" | cut -f1)

echo ""
echo "✅ Packaging complete!"
echo ""
echo "📦 Package details:"
echo "  - File: $OUTPUT_PATH"
echo "  - Size: $SIZE"
echo "  - Version: $VERSION"
echo ""
echo "📌 Installation instructions:"
echo "  1. Open Blender"
echo "  2. Edit > Preferences > Add-ons"
echo "  3. Click 'Install...' and select: $OUTPUT_PATH"
echo "  4. Enable 'Sequencer: Blender Movie Director'"
echo ""
echo "For development installation, use: ./scripts/run-blender.sh"