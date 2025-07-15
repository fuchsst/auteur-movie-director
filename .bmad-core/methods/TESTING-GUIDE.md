# BMAD Testing Guide

## Quick Start

```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run in Docker (recommended for CI-like environment)
make test-e2e
```

## Test Commands

### Backend Tests
```bash
cd backend && pytest                    # All backend tests
cd backend && pytest --cov=app         # With coverage
cd backend && pytest -xvs              # Debug mode (stop on failure, verbose)
cd backend && pytest tests/test_*.py   # Specific file
```

### Frontend Tests
```bash
cd frontend && npm test                # All frontend tests
cd frontend && npm test -- --coverage  # With coverage
cd frontend && npm test -- --watch     # Watch mode
cd frontend && npm test ComponentName  # Specific component
```

### Docker Tests (Recommended)
```bash
# Run complete test suite in containers
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# Clean up after tests
docker-compose -f docker-compose.test.yml down -v
```

## Test Structure

```
backend/tests/
├── test_*.py              # Unit tests
├── integration/           # Integration tests
└── performance/           # Performance tests

frontend/src/
├── lib/**/*.test.ts       # Component/service tests
└── test/setup.ts          # Test configuration

tests/
└── integration/           # E2E tests (Playwright)
```

## Writing Tests

### Backend (pytest)
```python
import pytest
from app.services.workspace import WorkspaceService

def test_create_project():
    service = WorkspaceService("/tmp")
    project = service.create_project("test")
    assert project.name == "test"

@pytest.mark.asyncio
async def test_async_operation():
    result = await some_async_function()
    assert result is not None
```

### Frontend (vitest)
```typescript
import { render } from '@testing-library/svelte';
import { describe, it, expect } from 'vitest';
import MyComponent from './MyComponent.svelte';

describe('MyComponent', () => {
  it('should render', () => {
    const { getByText } = render(MyComponent);
    expect(getByText('Hello')).toBeInTheDocument();
  });
});
```

## Coverage Requirements

- **Target**: 80% minimum
- **Backend**: `pytest --cov=app --cov-report=term-missing`
- **Frontend**: `npm test -- --coverage`
- **View Reports**: 
  - Backend: `open backend/htmlcov/index.html`
  - Frontend: `open frontend/coverage/index.html`

## CI/CD Integration

Tests automatically run on every push via GitHub Actions. Use Docker for local CI-like testing:

```bash
make test-e2e  # Runs same tests as CI
```

## Common Issues & Solutions

**Missing dependencies**: 
```bash
cd frontend && npm install
cd backend && pip install -r requirements-dev.txt
```

**Tests timeout**: Add timeout to specific tests
```python
@pytest.mark.timeout(60)  # Backend
test.setTimeout(60000);   // Frontend
```

**Clean test state**:
```bash
make clean
find . -name "__pycache__" -type d -rm -rf
```

## Best Practices

1. **Run before commit**: `make format && make test`
2. **Test in Docker**: Ensures consistency with CI
3. **Fix immediately**: Don't commit broken tests
4. **Focus on behavior**: Test what, not how
5. **Keep fast**: Unit tests < 100ms