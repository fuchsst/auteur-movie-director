#!/bin/bash
# Package the Generative Media Studio for distribution

set -e  # Exit on error

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Application name and version
APP_NAME="generative-media-studio"
VERSION=$(node -p "require('./package.json').version")

# Output directory
OUTPUT_DIR="${OUTPUT_DIR:-dist}"
mkdir -p "$OUTPUT_DIR"

# Package filename
if [ -n "$1" ]; then
    PACKAGE_NAME="$1"
else
    PACKAGE_NAME="${APP_NAME}_v${VERSION}.tar.gz"
fi

OUTPUT_PATH="$OUTPUT_DIR/$PACKAGE_NAME"

echo "📦 Packaging Generative Media Studio..."
echo "  Version: $VERSION"
echo "  Output: $OUTPUT_PATH"
echo ""

# Create temporary directory for packaging
TEMP_DIR=$(mktemp -d)
PACKAGE_DIR="$TEMP_DIR/$APP_NAME"

# Build frontend
echo "🔨 Building frontend..."
cd frontend
npm run build
cd ..

# Copy application files
echo "📂 Copying application files..."
mkdir -p "$PACKAGE_DIR"

# Copy backend
cp -r backend "$PACKAGE_DIR/"
# Copy frontend build
cp -r frontend/build "$PACKAGE_DIR/frontend"
# Copy configuration files
cp package.json "$PACKAGE_DIR/"
cp .env.example "$PACKAGE_DIR/"
cp docker-compose.yml "$PACKAGE_DIR/"
cp README.md "$PACKAGE_DIR/"

# Remove development files
echo "🧹 Cleaning up development files..."
find "$PACKAGE_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$PACKAGE_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true
find "$PACKAGE_DIR" -type f -name "*.pyo" -delete 2>/dev/null || true
find "$PACKAGE_DIR" -type f -name ".DS_Store" -delete 2>/dev/null || true
find "$PACKAGE_DIR" -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
find "$PACKAGE_DIR" -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
find "$PACKAGE_DIR" -type d -name ".svelte-kit" -exec rm -rf {} + 2>/dev/null || true
find "$PACKAGE_DIR" -type f -name "*.test.js" -delete 2>/dev/null || true
find "$PACKAGE_DIR" -type f -name "*.test.ts" -delete 2>/dev/null || true

# Create the archive
echo "🗜️  Creating archive..."
cd "$TEMP_DIR"
tar -czf "$PROJECT_ROOT/$OUTPUT_PATH" "$APP_NAME"

# Cleanup
echo "🧹 Cleaning up temporary files..."
rm -rf "$TEMP_DIR"

echo ""
echo "✅ Package created successfully!"
echo "   $OUTPUT_PATH"
echo ""
echo "📚 To deploy:"
echo "   1. Extract the archive on your server"
echo "   2. Install dependencies:"
echo "      - Backend: cd backend && pip install -r requirements.txt"
echo "      - Frontend is pre-built"
echo "   3. Configure environment variables"
echo "   4. Run with: npm start"