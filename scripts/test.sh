#!/bin/bash
# Run tests for Blender Movie Director

set -e  # Exit on error

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Activate virtual environment
if [ -d "venv" ]; then
    echo "🔌 Activating virtual environment..."
    source venv/bin/activate
else
    echo "❌ Virtual environment not found. Run ./scripts/setup.sh first"
    exit 1
fi

# Parse command line arguments
TEST_TYPE="${1:-all}"
EXTRA_ARGS="${@:2}"

echo "🧪 Running tests: $TEST_TYPE"
echo ""

case "$TEST_TYPE" in
    "unit")
        echo "🔬 Running unit tests..."
        pytest tests/unit $EXTRA_ARGS
        ;;
    
    "integration")
        echo "🔗 Running integration tests..."
        pytest tests/integration $EXTRA_ARGS
        ;;
    
    "coverage")
        echo "📊 Running tests with coverage..."
        pytest --cov=blender_movie_director --cov-report=html --cov-report=term $EXTRA_ARGS
        echo ""
        echo "📄 Coverage report generated in htmlcov/index.html"
        ;;
    
    "lint")
        echo "🎨 Running code quality checks..."
        
        echo "  📏 Running ruff..."
        ruff check blender_movie_director tests
        
        echo "  🖤 Running black..."
        black --check blender_movie_director tests
        
        echo "  🔍 Running mypy..."
        mypy blender_movie_director
        ;;
    
    "format")
        echo "✨ Formatting code..."
        
        echo "  🖤 Running black..."
        black blender_movie_director tests scripts
        
        echo "  📏 Running ruff with fixes..."
        ruff check --fix blender_movie_director tests
        ;;
    
    "quick")
        echo "⚡ Running quick tests (no integration, parallel)..."
        pytest -n auto -m "not integration" $EXTRA_ARGS
        ;;
    
    "all"|*)
        echo "🎯 Running all tests and checks..."
        
        # Run linting first
        echo ""
        echo "1️⃣ Code quality checks..."
        ./scripts/test.sh lint
        
        # Run tests with coverage
        echo ""
        echo "2️⃣ Running tests with coverage..."
        pytest --cov=blender_movie_director --cov-report=term-missing $EXTRA_ARGS
        
        echo ""
        echo "✅ All tests passed!"
        ;;
esac

# Show test summary
if [ "$TEST_TYPE" != "lint" ] && [ "$TEST_TYPE" != "format" ]; then
    echo ""
    echo "📊 Test Summary:"
    echo "  - Python version: $(python --version)"
    echo "  - pytest version: $(pytest --version | head -1)"
    echo "  - Test directory: tests/"
fi