#!/bin/bash
# Docker test runner script

set -e

echo "🧪 Running tests in Docker containers..."

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default test mode
TEST_MODE=${1:-all}

case $TEST_MODE in
  all)
    echo -e "${BLUE}Running all tests...${NC}"
    docker-compose -f docker-compose.test.yml up --abort-on-container-exit
    ;;
  
  backend)
    echo -e "${BLUE}Running backend tests...${NC}"
    docker-compose -f docker-compose.test.yml run --rm test-runner \
      sh -c "cd backend && pytest --cov=app --cov-report=term-missing"
    ;;
  
  frontend)
    echo -e "${BLUE}Running frontend tests...${NC}"
    docker-compose -f docker-compose.test.yml run --rm test-runner \
      sh -c "cd frontend && npm test -- --coverage"
    ;;
  
  e2e)
    echo -e "${BLUE}Running E2E tests...${NC}"
    docker-compose -f docker-compose.test.yml up --abort-on-container-exit
    ;;
  
  quick)
    echo -e "${BLUE}Running quick tests (no integration)...${NC}"
    docker-compose -f docker-compose.test.yml run --rm test-runner \
      sh -c "cd backend && pytest -k 'not integration' && cd ../frontend && npm test -- --run"
    ;;
  
  coverage)
    echo -e "${BLUE}Running tests with coverage report...${NC}"
    docker-compose -f docker-compose.test.yml run --rm test-runner \
      sh -c "cd backend && pytest --cov=app --cov-report=html --cov-report=term && cd ../frontend && npm test -- --coverage"
    ;;
  
  *)
    echo "Usage: $0 [all|backend|frontend|e2e|quick|coverage]"
    exit 1
    ;;
esac

# Clean up
echo -e "${BLUE}Cleaning up test containers...${NC}"
docker-compose -f docker-compose.test.yml down -v

echo -e "${GREEN}✅ Tests completed!${NC}"