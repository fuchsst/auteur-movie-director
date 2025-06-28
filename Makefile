# Makefile for Blender Movie Director

.PHONY: help setup test lint format clean run package docs

# Default target
help:
	@echo "Blender Movie Director - Development Commands"
	@echo "============================================"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup       - Full dev setup (installs UV if needed)"
	@echo "  make setup-test  - Test environment only"
	@echo "  make setup-clean - Clean setup (removes existing environment)"
	@echo "  make setup-prod  - Production environment only"
	@echo ""
	@echo "Development:"
	@echo "  make run         - Run Blender with addon loaded"
	@echo "  make test        - Run all tests"
	@echo "  make test-quick  - Run quick tests (no integration)"
	@echo "  make test-coverage - Generate coverage report"
	@echo "  make lint        - Run code quality checks"
	@echo "  make format      - Format code automatically"
	@echo ""
	@echo "Backend Services:"
	@echo "  make services         - Start all backend services"
	@echo "  make services-stop    - Stop all backend services"
	@echo "  make services-status  - Check service status"
	@echo "  make services-restart - Restart all services"
	@echo "  make services-logs    - View service logs"
	@echo ""
	@echo "Individual Services:"
	@echo "  make service-comfyui  - Start ComfyUI only"
	@echo "  make service-wan2gp   - Start Wan2GP only"
	@echo "  make service-rvc      - Start RVC only"
	@echo "  make service-audioldm - Start AudioLDM only"
	@echo ""
	@echo "Docker Services:"
	@echo "  make services-docker      - Start all services in Docker"
	@echo "  make services-docker-stop - Stop Docker services"
	@echo ""
	@echo "Docker Compose (Alternative):"
	@echo "  make docker-up     - Start services with docker-compose"
	@echo "  make docker-down   - Stop docker-compose services"
	@echo "  make docker-logs   - View docker-compose logs"
	@echo "  make docker-status - Check docker-compose status"
	@echo ""
	@echo "Distribution:"
	@echo "  make package     - Create addon .zip file"
	@echo "  make clean       - Clean build artifacts"
	@echo ""
	@echo "Blender Integration:"
	@echo "  make blender-deps - Install deps in Blender's Python"

# Setup commands - always use setup.sh which handles UV installation
setup:
	@./scripts/setup.sh dev

setup-test:
	@./scripts/setup.sh test

setup-clean:
	@./scripts/setup.sh dev --clean

setup-prod:
	@./scripts/setup.sh prod

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
	@./scripts/services.sh start all

services-stop:
	@./scripts/services.sh stop all

services-status:
	@./scripts/services.sh status

services-restart:
	@./scripts/services.sh restart all

services-logs:
	@./scripts/services.sh logs

# Individual service targets
service-comfyui:
	@./scripts/services.sh start comfyui

service-wan2gp:
	@./scripts/services.sh start wan2gp

service-rvc:
	@./scripts/services.sh start rvc

service-audioldm:
	@./scripts/services.sh start audioldm

# Docker services
services-docker:
	@USE_DOCKER=true ./scripts/services.sh start all

services-docker-stop:
	@USE_DOCKER=true ./scripts/services.sh stop all

# Docker Compose services
docker-up:
	@docker-compose up -d

docker-down:
	@docker-compose down

docker-logs:
	@docker-compose logs -f

docker-status:
	@docker-compose ps

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
	@uv run pre-commit install

# Blender integration
blender-deps:
	@./scripts/blender-python.sh --install-addon-deps

# CI/CD helpers - use UV commands
ci-test:
	@uv run pytest --cov=blender_movie_director --cov-report=xml

ci-lint:
	@uv run ruff check blender_movie_director tests
	@uv run black --check blender_movie_director tests
	@uv run mypy blender_movie_director

# UV specific commands
uv-update:
	@echo "📦 Updating UV to latest version..."
	@curl -LsSf https://astral.sh/uv/install.sh | sh

uv-lock:
	@echo "🔒 Regenerating lock file..."
	@uv pip compile pyproject.toml -o uv.lock