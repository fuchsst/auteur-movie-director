#!/bin/bash
# Setup script for Blender Movie Director development environment

set -e  # Exit on error

echo "🎬 Setting up Blender Movie Director development environment..."

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
REQUIRED_VERSION="3.11"

echo "📍 Project root: $PROJECT_ROOT"
echo "🐍 Python version: $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip and install build tools
echo "⬆️  Upgrading pip and build tools..."
pip install --upgrade pip setuptools wheel

# Install dependencies based on environment
if [ "$1" == "dev" ] || [ -z "$1" ]; then
    echo "📚 Installing development dependencies..."
    pip install -r requirements-dev.txt
    
    # Install pre-commit hooks
    echo "🪝 Setting up pre-commit hooks..."
    pre-commit install
    
elif [ "$1" == "test" ]; then
    echo "🧪 Installing test dependencies..."
    pip install -r requirements-test.txt
    
else
    echo "📚 Installing core dependencies..."
    pip install -r requirements.txt
fi

# Create necessary directories
echo "📁 Creating project directories..."
mkdir -p logs
mkdir -p temp
mkdir -p generated

# Check for .env file
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo "📋 Creating .env file from example..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys and configuration"
fi

# Display next steps
echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Configure your .env file with API keys (if needed)"
echo "3. Run tests: ./scripts/test.sh"
echo "4. Launch Blender with addon: ./scripts/run-blender.sh"
echo ""
echo "For more information, see CLAUDE.md"