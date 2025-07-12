# Test Directory Structure

This directory contains test files and resources for the Auteur Movie Director project.

## Organization

### `/fixtures`
Test data files used by integration tests (images, videos, etc.)

### `/integration` 
End-to-end integration tests that test multiple components together.
- Frontend tests using Playwright (TypeScript)
- Backend tests using pytest (Python)

### `/helpers`
Utility functions and helpers for tests.

## Running Tests

### All Tests
```bash
npm run test
```

### Integration Tests Only
```bash
npm run test:integration
```

### End-to-End Tests (Docker)
```bash
npm run test:e2e
```

### Manual Testing
See `MANUAL_TEST_CHECKLIST.md` for comprehensive manual testing procedures.

## Test Categories

- **Unit Tests**: Located in component directories (e.g., `frontend/src/lib/**/*.test.ts`)
- **Integration Tests**: Test interactions between components
- **E2E Tests**: Full system tests using Docker Compose
- **Manual Tests**: Checklist for human verification

## Writing Tests

1. Unit tests should be colocated with the code they test
2. Integration tests go in the `/tests/integration` directory
3. Use meaningful test names that describe what is being tested
4. Include both positive and negative test cases
5. Clean up test data after tests complete