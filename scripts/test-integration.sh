#!/bin/bash

# Integration Test Runner Script

set -e

echo "🧪 Running End-to-End Integration Tests"
echo "======================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if services are healthy
check_services() {
    echo -e "${YELLOW}Checking service health...${NC}"
    
    services=("frontend" "backend" "worker" "redis")
    all_healthy=true
    
    for service in "${services[@]}"; do
        if docker-compose ps | grep -E "auteur_${service}.*healthy" > /dev/null; then
            echo -e "${GREEN}✓ ${service} is healthy${NC}"
        else
            echo -e "${RED}✗ ${service} is not healthy${NC}"
            all_healthy=false
        fi
    done
    
    if [ "$all_healthy" = false ]; then
        echo -e "${RED}Some services are not healthy. Aborting tests.${NC}"
        exit 1
    fi
}

# Function to run backend tests
run_backend_tests() {
    echo -e "\n${YELLOW}Running backend integration tests...${NC}"
    docker-compose exec -T backend pytest tests/integration/test_project_flow.py -v
}

# Function to run frontend tests
run_frontend_tests() {
    echo -e "\n${YELLOW}Running frontend integration tests...${NC}"
    npm run test:integration
}

# Function to run e2e tests with Docker Compose
run_e2e_tests() {
    echo -e "\n${YELLOW}Running full E2E tests with Docker Compose...${NC}"
    docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test-runner
}

# Main execution
case "${1:-all}" in
    backend)
        check_services
        run_backend_tests
        ;;
    frontend)
        check_services
        run_frontend_tests
        ;;
    e2e)
        run_e2e_tests
        ;;
    all)
        check_services
        run_backend_tests
        run_frontend_tests
        ;;
    *)
        echo "Usage: $0 [backend|frontend|e2e|all]"
        exit 1
        ;;
esac

echo -e "\n${GREEN}✅ Integration tests completed!${NC}"