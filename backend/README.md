# Auteur Movie Director - Backend

FastAPI backend service for the Auteur Movie Director platform.

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install -r requirements-dev.txt
```

## Development

```bash
# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or use npm from root directory
npm run dev:backend
```

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

## API Documentation

When running, access:
- API docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI schema: http://localhost:8000/openapi.json