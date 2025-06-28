#!/bin/bash
# Run a Python script with the Movie Director environment

set -e  # Exit on error

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Check if script path provided
if [ -z "$1" ]; then
    echo "❌ Error: No script specified"
    echo ""
    echo "Usage: ./scripts/run-script.sh <script.py> [args...]"
    echo ""
    echo "Examples:"
    echo "  ./scripts/run-script.sh examples/test_service_discovery.py"
    echo "  ./scripts/run-script.sh scripts/check_backends.py --verbose"
    exit 1
fi

SCRIPT_PATH="$1"
shift  # Remove first argument, keep the rest for the script

# Check if script exists
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "❌ Error: Script not found: $SCRIPT_PATH"
    exit 1
fi

# Activate virtual environment
if [ -d "venv" ]; then
    echo "🔌 Activating virtual environment..."
    source venv/bin/activate
else
    echo "❌ Virtual environment not found. Run ./scripts/setup.sh first"
    exit 1
fi

# Load environment variables if .env exists
if [ -f ".env" ]; then
    echo "📋 Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
fi

# Set Python path to include our modules
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Run the script
echo "🐍 Running: $SCRIPT_PATH"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python "$SCRIPT_PATH" "$@"