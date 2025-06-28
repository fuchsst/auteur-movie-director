#!/bin/bash
# Run tests for Blender Movie Director using UV

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

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ UV is not installed. Run './scripts/setup.sh' first${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${RED}❌ Virtual environment not found. Run './scripts/setup.sh' first${NC}"
    exit 1
fi

# Parse command line arguments
TEST_TYPE="${1:-all}"
EXTRA_ARGS="${@:2}"

echo -e "${BLUE}🧪 Running tests: $TEST_TYPE${NC}"
echo ""

case "$TEST_TYPE" in
    "unit")
        echo -e "${GREEN}🔬 Running unit tests...${NC}"
        uv run pytest tests/test_*/test_*.py -v $EXTRA_ARGS
        ;;
    
    "integration")
        echo -e "${GREEN}🔗 Running integration tests...${NC}"
        uv run pytest tests/test_*/*integration*.py -v $EXTRA_ARGS
        ;;
    
    "coverage")
        echo -e "${GREEN}📊 Running tests with coverage...${NC}"
        uv run pytest --cov=blender_movie_director --cov-report=html --cov-report=term $EXTRA_ARGS
        echo ""
        echo -e "${YELLOW}📄 Coverage report generated in htmlcov/index.html${NC}"
        ;;
    
    "lint")
        echo -e "${GREEN}🎨 Running code quality checks...${NC}"
        
        echo -e "${BLUE}  📏 Running ruff...${NC}"
        uv run ruff check blender_movie_director tests
        
        echo -e "${BLUE}  🖤 Running black check...${NC}"
        uv run black --check blender_movie_director tests
        
        echo -e "${BLUE}  🔍 Running mypy...${NC}"
        uv run mypy blender_movie_director
        
        echo -e "${GREEN}✅ All linting checks passed!${NC}"
        ;;
    
    "format")
        echo -e "${GREEN}🎨 Formatting code...${NC}"
        
        echo -e "${BLUE}  🖤 Running black...${NC}"
        uv run black blender_movie_director tests
        
        echo -e "${BLUE}  📏 Running ruff with fixes...${NC}"
        uv run ruff check --fix blender_movie_director tests
        
        echo -e "${GREEN}✅ Code formatting complete!${NC}"
        ;;
    
    "quick")
        echo -e "${GREEN}⚡ Running quick tests (fail fast, rerun failures)...${NC}"
        uv run pytest -x --ff tests/ $EXTRA_ARGS
        ;;
    
    "all")
        echo -e "${GREEN}🎯 Running all tests and checks...${NC}"
        echo ""
        
        echo -e "${YELLOW}1️⃣ Code quality checks...${NC}"
        $0 lint
        echo ""
        
        echo -e "${YELLOW}2️⃣ Unit tests...${NC}"
        $0 unit
        echo ""
        
        echo -e "${YELLOW}3️⃣ Integration tests...${NC}"
        $0 integration
        echo ""
        
        echo -e "${GREEN}✨ All tests passed! ✨${NC}"
        ;;
    
    *)
        echo -e "${RED}❌ Unknown test type: $TEST_TYPE${NC}"
        echo ""
        echo "Usage: $0 [type] [extra pytest args]"
        echo ""
        echo "Available test types:"
        echo "  all         - Run all tests and linting (default)"
        echo "  unit        - Run unit tests only"
        echo "  integration - Run integration tests only"
        echo "  coverage    - Run tests with coverage report"
        echo "  lint        - Run code quality checks"
        echo "  format      - Auto-format code"
        echo "  quick       - Fast test run (fail fast)"
        echo ""
        echo "Examples:"
        echo "  $0                    # Run all tests"
        echo "  $0 unit               # Run unit tests only"
        echo "  $0 coverage -v        # Run with coverage and verbose output"
        echo "  $0 quick -k service   # Run tests matching 'service' quickly"
        exit 1
        ;;
esac