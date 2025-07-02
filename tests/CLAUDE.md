# Test Suite

## Overview

This directory contains the test suite for the Generative Media Studio platform. Tests are organized by component (backend, frontend, integration).

## Test Organization

```
tests/
├── __init__.py                    # Test package root
├── test_backend/                  # Backend API tests
│   ├── __init__.py
│   ├── test_api.py               # FastAPI endpoint tests
│   ├── test_websocket.py         # WebSocket handler tests
│   └── test_services.py          # Service layer tests
├── test_frontend/                 # Frontend tests
│   ├── __init__.py
│   ├── test_components.py        # Svelte component tests
│   └── test_stores.py            # Store logic tests
└── test_integration/              # End-to-end tests
    ├── __init__.py
    └── test_workflows.py          # Complete workflow tests
```

## Running Tests

### Using NPM Scripts (Recommended)

All test commands should be run through npm scripts:

```bash
# Run all tests
npm run test

# Run backend tests only
npm run test:backend

# Run frontend tests only  
npm run test:frontend

# Run integration tests
npm run test:integration

# Run with coverage
npm run test:backend -- --cov

# Run linting
npm run lint

# Auto-format code
npm run format
```

### Direct Test Execution

For backend tests (Python/pytest):
```bash
# Run all backend tests
cd backend && pytest

# Run specific test file
cd backend && pytest tests/test_api.py -v

# Run with coverage
cd backend && pytest --cov=app --cov-report=html
```

For frontend tests (JavaScript/Vitest):
```bash
# Run all frontend tests
cd frontend && npm test

# Run in watch mode
cd frontend && npm run test:watch

# Run with UI
cd frontend && npm run test:ui
```

### Manual Testing

Start the development servers:
```bash
# Start both frontend and backend
npm run dev

# Or start individually:
npm run dev:backend   # Backend on port 8000
npm run dev:frontend  # Frontend on port 3000
```

Access the application:
- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Test Requirements

### Backend (Python)
- Python 3.11+ required
- Test dependencies in `backend/requirements-dev.txt`
- Uses pytest for test runner
- FastAPI TestClient for API testing

### Frontend (JavaScript)
- Node.js 18+ required
- Test dependencies in `frontend/package.json`
- Uses Vitest for test runner
- Svelte Testing Library for component tests

## Writing Tests

### Backend Test Pattern (Python)
```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Generative Media Studio API"}

@pytest.mark.asyncio
async def test_websocket():
    async with client.websocket_connect("/ws") as websocket:
        await websocket.send_json({"type": "ping"})
        data = await websocket.receive_json()
        assert data["type"] == "pong"
```

### Frontend Test Pattern (JavaScript)
```javascript
import { render, screen } from '@testing-library/svelte'
import { describe, it, expect } from 'vitest'
import MyComponent from './MyComponent.svelte'

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(MyComponent, { props: { name: 'Test' } })
    expect(screen.getByText('Test')).toBeInTheDocument()
  })
})
```

## Coverage Goals

- Minimum 80% coverage for API endpoints
- 100% coverage for critical paths (project management, WebSocket handling)
- Frontend components tested for user interactions
- Integration tests for complete workflows

## Continuous Integration

Tests are designed to run in CI/CD pipelines:
- No browser dependencies for unit tests
- Configurable timeouts for async operations
- Mock external services by default
- Environment variables for configuration