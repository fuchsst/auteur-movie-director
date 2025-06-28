# Test Suite

## Overview

This directory contains the test suite for the Blender Movie Director addon. The folder structure mirrors the `blender_movie_director` module for easy navigation.

## Test Organization

```
tests/
├── __init__.py                    # Test package root
├── manual_test_discovery.py       # Manual test script for service discovery
├── test_agents/                   # Agent-specific tests (mirrors agents/)
│   └── __init__.py
├── test_backend/                  # Backend integration tests
│   ├── __init__.py
│   ├── test_service_discovery.py           # Tests for backend/service_discovery.py
│   ├── test_service_discovery_simple.py    # Simplified tests without async complexity
│   └── test_service_discovery_integration.py # Integration tests for service discovery
└── test_ui/                       # UI component tests
    └── __init__.py
```

## Running Tests

### Using Makefile (Recommended)

All test commands should be run through the project's Makefile for consistency:

```bash
# Run all tests with linting and coverage
make test

# Run quick tests (unit tests only, no integration)
make test-quick

# Generate coverage report
make test-coverage

# Run code quality checks only
make lint

# Auto-format code
make format

# Clean test artifacts
make clean
```

### Direct Script Usage (Alternative)

If needed, you can also use the scripts directly:
```bash
./scripts/test.sh all        # All tests
./scripts/test.sh unit       # Unit tests only
./scripts/test.sh integration # Integration tests only
./scripts/test.sh quick      # Fast tests
```

**`./scripts/run-script.sh`** - Run Python scripts with project environment
```bash
# Run pytest on specific test file
./scripts/run-script.sh tests/test_backend/test_service_discovery.py -m pytest -v

# Note: For pytest, the script name comes first, then -m pytest and its args
```

**Direct pytest usage** (from project root with venv activated)
```bash
# Run all backend tests
pytest tests/test_backend/ -v

# Run specific test file
pytest tests/test_backend/test_service_discovery.py -v

# Run with specific test name pattern
pytest -k "test_service" -v
```

### Manual Testing

Before running manual tests, ensure backend services are running:
```bash
# Start all backend services
make services

# Check service status
make services-status
```

Then run manual test scripts:
```bash
# Test service discovery without Blender
./scripts/run-script.sh tests/manual_test_discovery.py

# Test specific service with custom port
./scripts/run-script.sh tests/manual_test_discovery.py --service comfyui --port 8188

# Stop services when done
make services-stop
```

## Test Requirements

### Python Environment
- Tests run outside of Blender using mocked `bpy` module
- Requires Python 3.11+ (matching Blender 4.0+ Python version)
- All test dependencies in `requirements-test.txt`

### Mocking Strategy
- `bpy` module is mocked for unit tests
- Blender-specific functionality tested with integration tests
- Manual test scripts for real service discovery

## Writing Tests

### Unit Test Pattern
```python
import unittest
from unittest.mock import Mock, patch

class TestMyComponent(unittest.TestCase):
    def setUp(self):
        # Mock Blender context if needed
        self.context = Mock()
        
    def test_functionality(self):
        # Test implementation
        pass
```

### Async Test Pattern
```python
import asyncio
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result == expected
```

### Integration Test Pattern
- Use `blender-python.sh` script for tests requiring real Blender
- Create separate integration test files
- Run with Blender's Python interpreter

## Coverage Goals

- Minimum 80% coverage for core functionality
- 100% coverage for critical paths (service discovery, agent orchestration)
- UI components tested for operator execution
- Backend integrations tested with mocks

## Continuous Integration

Tests are designed to run in CI/CD pipelines:
- No GUI dependencies for unit tests
- Configurable timeouts for network operations
- Mock external services by default
- Environment variables for integration testing