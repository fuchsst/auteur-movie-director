# Makefile for Blender Movie Director

.PHONY: help setup test lint format clean run package docs

# Default target
help:
	@echo "Blender Movie Director - Development Commands"
	@echo "============================================"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup       - Set up development environment"
	@echo "  make setup-test  - Set up test environment only"
	@echo ""
	@echo "Development:"
	@echo "  make run         - Run Blender with addon loaded"
	@echo "  make test        - Run all tests"
	@echo "  make lint        - Run code quality checks"
	@echo "  make format      - Format code automatically"
	@echo ""
	@echo "Backend Services:"
	@echo "  make services    - Start all backend services"
	@echo "  make services-stop - Stop all backend services"
	@echo "  make services-status - Check service status"
	@echo ""
	@echo "Distribution:"
	@echo "  make package     - Create addon .zip file"
	@echo "  make clean       - Clean build artifacts"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs        - Build documentation (TODO)"

# Setup commands
setup:
	@./scripts/setup.sh dev

setup-test:
	@./scripts/setup.sh test

# Development commands
run:
	@./scripts/run-blender.sh

test:
	@./scripts/test.sh all

test-quick:
	@./scripts/test.sh quick

test-coverage:
	@./scripts/test.sh coverage

lint:
	@./scripts/test.sh lint

format:
	@./scripts/test.sh format

# Backend services
services:
	@./scripts/dev-server.sh all

services-stop:
	@./scripts/dev-server.sh stop

services-status:
	@./scripts/dev-server.sh status

# Distribution
package:
	@./scripts/package.sh

clean:
	@echo "🧹 Cleaning build artifacts..."
	@rm -rf build/
	@rm -rf dist/
	@rm -rf *.egg-info
	@rm -rf .pytest_cache/
	@rm -rf .coverage
	@rm -rf htmlcov/
	@rm -rf .mypy_cache/
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@echo "✅ Clean complete"

# Documentation (TODO)
docs:
	@echo "📚 Documentation building not yet implemented"
	@echo "See CLAUDE.md for current documentation"

# Installation shortcuts
install: setup

install-dev: setup

install-hooks:
	@source venv/bin/activate && pre-commit install

# CI/CD helpers
ci-test:
	@source venv/bin/activate && pytest --cov=blender_movie_director --cov-report=xml

ci-lint:
	@source venv/bin/activate && ruff check blender_movie_director tests
	@source venv/bin/activate && black --check blender_movie_director tests
	@source venv/bin/activate && mypy blender_movie_director