#!/bin/bash
# Run a Python script with the Movie Director environment using UV

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

# Check if script path provided
if [ -z "$1" ]; then
    echo -e "${RED}❌ Error: No script specified${NC}"
    echo ""
    echo "Usage: $0 <script.py> [args...]"
    echo ""
    echo "Examples:"
    echo "  $0 tests/manual_test_discovery.py"
    echo "  $0 scripts/check_backends.py --verbose"
    echo ""
    echo "This script runs Python scripts using UV with the project environment."
    exit 1
fi

SCRIPT_PATH="$1"
shift  # Remove first argument, keep the rest for the script

# Check if script exists
if [ ! -f "$SCRIPT_PATH" ]; then
    echo -e "${RED}❌ Error: Script not found: $SCRIPT_PATH${NC}"
    exit 1
fi

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

# Load environment variables if .env exists
if [ -f ".env" ]; then
    echo -e "${BLUE}📋 Loading environment variables from .env...${NC}"
    set -a  # automatically export all variables
    source .env
    set +a  # turn off automatic export
fi

# Set Python path to include our modules
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Run the script with UV
echo -e "${GREEN}🐍 Running: $SCRIPT_PATH${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# UV automatically handles environment activation
uv run python "$SCRIPT_PATH" "$@"