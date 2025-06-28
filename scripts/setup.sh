#!/bin/bash
# Master setup script for Blender Movie Director
# Handles UV installation and environment setup

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🎬 Setting up Blender Movie Director development environment...${NC}"

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Parse command line arguments
SETUP_TYPE="${1:-dev}"
CLEAN_INSTALL=false

for arg in "$@"; do
    case $arg in
        --clean)
            CLEAN_INSTALL=true
            ;;
        dev|test|prod|blender|bundle)
            SETUP_TYPE="$arg"
            ;;
    esac
done

echo -e "${YELLOW}📍 Project root: $PROJECT_ROOT${NC}"
echo -e "${YELLOW}🔧 Setup type: $SETUP_TYPE${NC}"

# Function to install UV
install_uv() {
    if ! command -v uv &> /dev/null; then
        echo -e "${YELLOW}📦 Installing UV package manager...${NC}"
        
        # Detect OS and install UV accordingly
        if [[ "$OSTYPE" == "win32" ]]; then
            # Native Windows (not Git Bash)
            echo -e "${BLUE}🪟 Detected Windows environment${NC}"
            powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
        else
            # Unix-like (Linux, macOS, WSL, Git Bash)
            echo -e "${BLUE}🐧 Detected Unix-like environment${NC}"
            curl -LsSf https://astral.sh/uv/install.sh | sh
        fi
        
        # Add UV to PATH for current session (always use Unix-style paths in Git Bash)
        export PATH="$HOME/.cargo/bin:$PATH"
        export PATH="$HOME/.local/bin:$PATH"
        
        # Verify installation
        if ! command -v uv &> /dev/null; then
            echo -e "${RED}❌ UV installation failed${NC}"
            echo -e "${YELLOW}Please install UV manually from: https://docs.astral.sh/uv/getting-started/installation/${NC}"
            exit 1
        fi
        
        echo -e "${GREEN}✅ UV installed successfully: $(uv --version)${NC}"
    else
        echo -e "${GREEN}✅ UV already installed: $(uv --version)${NC}"
    fi
}

# Function to bundle dependencies for self-contained addon
bundle_dependencies() {
    echo -e "${YELLOW}📦 Bundling dependencies for self-contained Blender addon...${NC}"
    
    # Ensure we have a virtual environment
    if [ ! -d ".venv" ]; then
        echo -e "${YELLOW}Creating virtual environment first...${NC}"
        uv venv --python 3.11
        uv sync --extra ai
    fi
    
    # Create libs directory in addon
    LIBS_DIR="$PROJECT_ROOT/blender_movie_director/libs"
    
    # Clean existing libs directory
    if [ -d "$LIBS_DIR" ]; then
        echo -e "${YELLOW}🗑️  Removing existing libs directory...${NC}"
        rm -rf "$LIBS_DIR"
    fi
    
    echo -e "${GREEN}📁 Creating libs directory: $LIBS_DIR${NC}"
    mkdir -p "$LIBS_DIR"
    
    # Install production dependencies into libs directory
    echo -e "${BLUE}📚 Installing production dependencies into libs...${NC}"
    uv pip install --target "$LIBS_DIR" \
        aiohttp \
        pyyaml \
        requests \
        crewai \
        litellm \
        gradio-client \
        numpy \
        --no-deps
    
    # Install additional core dependencies with their deps
    echo -e "${BLUE}📚 Installing additional core dependencies...${NC}"
    uv pip install --target "$LIBS_DIR" \
        aiohttp \
        pyyaml \
        requests
    
    # Create __init__.py in libs to make it a package
    touch "$LIBS_DIR/__init__.py"
    
    # Clean up unnecessary files
    echo -e "${BLUE}🧹 Cleaning up unnecessary files...${NC}"
    find "$LIBS_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "$LIBS_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true
    find "$LIBS_DIR" -type f -name "*.pyo" -delete 2>/dev/null || true
    find "$LIBS_DIR" -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
    find "$LIBS_DIR" -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    
    # Calculate size
    LIBS_SIZE=$(du -sh "$LIBS_DIR" 2>/dev/null | cut -f1 || echo "unknown")
    
    echo ""
    echo -e "${GREEN}✅ Dependencies bundled successfully!${NC}"
    echo -e "${BLUE}📊 Bundled libraries size: $LIBS_SIZE${NC}"
    echo -e "${BLUE}📁 Location: $LIBS_DIR${NC}"
    echo ""
    echo -e "${YELLOW}The addon is now self-contained and ready for Blender!${NC}"
}

# Function to setup Python environment
setup_environment() {
    echo -e "${YELLOW}🐍 Setting up Python environment...${NC}"
    
    # Unset conda environment variables that cause path issues in Git Bash
    echo -e "${BLUE}🔧 Clearing conda environment variables for UV compatibility...${NC}"
    unset CONDA_PREFIX
    unset CONDA_DEFAULT_ENV
    unset CONDA_SHLVL
    unset CONDA_EXE
    unset CONDA_PYTHON_EXE
    unset CONDA_PROMPT_MODIFIER
    
    # Clean install if requested
    if [ "$CLEAN_INSTALL" = true ]; then
        if [ -d ".venv" ]; then
            echo -e "${YELLOW}🗑️  Removing existing environment...${NC}"
            rm -rf .venv
        fi
        if [ -f "uv.lock" ]; then
            echo -e "${YELLOW}🗑️  Removing existing lock file...${NC}"
            rm -f uv.lock
        fi
    fi
    
    # Create virtual environment with UV if it doesn't exist
    if [ ! -d ".venv" ]; then
        echo -e "${GREEN}📦 Creating virtual environment with Python 3.11...${NC}"
        uv venv --python 3.11
    else
        echo -e "${GREEN}✅ Virtual environment already exists${NC}"
    fi
    
    # Install dependencies based on setup type using modern UV workflow
    echo -e "${GREEN}📚 Installing dependencies for: $SETUP_TYPE${NC}"
    
    case "$SETUP_TYPE" in
        "dev")
            echo -e "${BLUE}Installing development dependencies (ai, dev, test)...${NC}"
            uv sync --extra ai --extra dev --extra test
            ;;
        "test")
            echo -e "${BLUE}Installing test dependencies only...${NC}"
            uv sync --extra test
            ;;
        "prod")
            echo -e "${BLUE}Installing production dependencies only...${NC}"
            uv sync
            ;;
        "blender")
            echo -e "${BLUE}Installing Blender runtime dependencies...${NC}"
            uv sync --extra blender
            ;;
        "bundle")
            echo -e "${BLUE}Bundling dependencies for self-contained addon...${NC}"
            bundle_dependencies
            return  # Skip normal post-setup for bundle
            ;;
        *)
            echo -e "${RED}❌ Unknown setup type: $SETUP_TYPE${NC}"
            echo "Valid options: dev, test, prod, blender, bundle"
            exit 1
            ;;
    esac
}

# Function for post-setup configuration
post_setup() {
    echo -e "${YELLOW}🔧 Performing post-setup configuration...${NC}"
    
    
    # Create .env from example if doesn't exist
    if [ ! -f ".env" ] && [ -f ".env.example" ]; then
        echo -e "${GREEN}📋 Creating .env from example...${NC}"
        cp .env.example .env
        echo -e "${YELLOW}⚠️  Please edit .env with your configuration${NC}"
    fi
    
    # Create necessary directories
    echo -e "${GREEN}📁 Creating project directories...${NC}"
    mkdir -p logs
    mkdir -p dist
    mkdir -p .blender-cache
    
    # Create cache directories for development tools
    echo -e "${GREEN}📁 Creating cache directories for tools...${NC}"
    mkdir -p .cache/ruff
    mkdir -p .cache/mypy
    mkdir -p .cache/pytest
    mkdir -p .cache/black
    mkdir -p .cache/coverage_html
    
    # Display success message
    echo ""
    echo -e "${GREEN}✨ Setup complete! ✨${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "  1. Edit .env with your configuration"
    echo "  2. Run 'make run' to start Blender with the addon"
    echo "  3. Run 'make test' to run the test suite"
    echo "  4. Run 'make services' to start backend services"
    echo ""
    echo -e "${YELLOW}To activate the environment manually:${NC}"
    echo "  source .venv/bin/activate"
    echo ""
    echo -e "${YELLOW}To use UV commands directly:${NC}"
    echo "  uv run <command>  # Runs command in the virtual environment"
    echo "  uv pip list       # Lists installed packages"
}

# Main execution
main() {
    echo ""
    install_uv
    echo ""
    setup_environment
    echo ""
    post_setup
}

# Run main function
main
