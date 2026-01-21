# DevOps Hub - Development Makefile
# Run `make help` for available commands

.PHONY: help install dev test lint format clean build docker run migrate

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RESET := \033[0m

#==============================================================================
# HELP
#==============================================================================

help: ## Show this help message
	@echo "$(BLUE)DevOps Hub - Development Commands$(RESET)"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'

#==============================================================================
# SETUP & INSTALLATION
#==============================================================================

install: ## Install all dependencies
	pip install -r requirements.txt
	cd frontend && npm install

install-dev: install ## Install with development dependencies
	pip install pre-commit black isort flake8 mypy
	pre-commit install

#==============================================================================
# DEVELOPMENT
#==============================================================================

dev: ## Start development servers (backend + frontend)
	@echo "$(BLUE)Starting development servers...$(RESET)"
	@make -j2 dev-backend dev-frontend

dev-backend: ## Start backend with hot-reload
	python -m uvicorn service.api:app --host 0.0.0.0 --port 8100 --reload

dev-frontend: ## Start frontend dev server
	cd frontend && npm run dev

run: ## Start production backend server
	python -m uvicorn service.api:app --host 0.0.0.0 --port 8100

#==============================================================================
# TESTING
#==============================================================================

test: ## Run all tests
	python -m pytest tests/ -v

test-cov: ## Run tests with coverage report
	python -m pytest tests/ --cov=. --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)Coverage report generated: htmlcov/index.html$(RESET)"

test-fast: ## Run tests without slow markers
	python -m pytest tests/ -v -m "not slow"

test-watch: ## Run tests in watch mode
	python -m pytest tests/ -v --tb=short -f

#==============================================================================
# CODE QUALITY
#==============================================================================

lint: ## Run all linters
	@echo "$(BLUE)Running Python linters...$(RESET)"
	flake8 core/ service/ factory/ built_in_agents/ --max-line-length=120 --ignore=E501,W503
	@echo "$(BLUE)Running TypeScript linter...$(RESET)"
	cd frontend && npm run lint

format: ## Format all code
	@echo "$(BLUE)Formatting Python code...$(RESET)"
	black core/ service/ factory/ built_in_agents/ tests/ --line-length=120
	isort core/ service/ factory/ built_in_agents/ tests/ --profile=black
	@echo "$(BLUE)Formatting TypeScript code...$(RESET)"
	cd frontend && npm run lint -- --fix || true

typecheck: ## Run type checking
	mypy core/ service/ factory/ --ignore-missing-imports

check: lint typecheck test ## Run all checks (lint + typecheck + tests)
	@echo "$(GREEN)All checks passed!$(RESET)"

#==============================================================================
# DATABASE
#==============================================================================

migrate: ## Run database migrations
	alembic upgrade head

migrate-down: ## Rollback last migration
	alembic downgrade -1

migrate-new: ## Create new migration (use: make migrate-new MSG="description")
	alembic revision -m "$(MSG)"

migrate-status: ## Show migration status
	alembic current
	@echo ""
	alembic history

db-reset: ## Reset database (WARNING: destroys data)
	@echo "$(YELLOW)WARNING: This will delete all data!$(RESET)"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ]
	rm -f data/devops_hub.db
	alembic upgrade head
	@echo "$(GREEN)Database reset complete$(RESET)"

#==============================================================================
# BACKUP & RECOVERY
#==============================================================================

backup: ## Create full backup (database + config)
	./scripts/backup.sh

backup-db: ## Create database-only backup
	./scripts/backup.sh --db-only

backup-s3: ## Create backup and upload to S3 (use: make backup-s3 S3_DEST=s3://bucket/path)
	./scripts/backup.sh --to $(S3_DEST)

restore: ## Restore from backup (use: make restore BACKUP=path/to/backup.tar.gz)
	./scripts/restore.sh $(BACKUP)

restore-dry: ## Dry run restore (use: make restore-dry BACKUP=path/to/backup.tar.gz)
	./scripts/restore.sh --dry-run $(BACKUP)

#==============================================================================
# DOCKER
#==============================================================================

docker-build: ## Build Docker images
	docker-compose build

docker-up: ## Start Docker containers
	docker-compose up -d

docker-down: ## Stop Docker containers
	docker-compose down

docker-logs: ## Show Docker logs
	docker-compose logs -f

docker-prod: ## Start production Docker stack
	docker-compose -f docker-compose.prod.yml up -d

docker-clean: ## Remove Docker containers and volumes
	docker-compose down -v --rmi local

#==============================================================================
# BUILD & DEPLOY
#==============================================================================

build: ## Build frontend for production
	cd frontend && npm run build

build-docker: ## Build production Docker image
	docker build -t devops-hub:latest .
	docker build -t devops-hub-frontend:latest -f frontend/Dockerfile frontend/

#==============================================================================
# UTILITIES
#==============================================================================

clean: ## Clean build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	cd frontend && rm -rf node_modules/.cache dist 2>/dev/null || true
	@echo "$(GREEN)Cleaned build artifacts$(RESET)"

health: ## Check API health
	@curl -s http://localhost:8100/health | python -m json.tool || echo "$(YELLOW)API not running$(RESET)"

docs: ## Open API documentation
	@echo "$(BLUE)Opening API docs at http://localhost:8100/docs$(RESET)"
	@python -m webbrowser "http://localhost:8100/docs" 2>/dev/null || echo "Open http://localhost:8100/docs in your browser"

shell: ## Start Python shell with app context
	python -c "from core.database import *; from service.api import *; print('DevOps Hub shell ready')" -i

logs: ## Tail application logs
	tail -f logs/*.log 2>/dev/null || echo "$(YELLOW)No log files found$(RESET)"

#==============================================================================
# GIT HOOKS
#==============================================================================

hooks-install: ## Install git pre-commit hooks
	pre-commit install
	@echo "$(GREEN)Pre-commit hooks installed$(RESET)"

hooks-run: ## Run pre-commit on all files
	pre-commit run --all-files

hooks-update: ## Update pre-commit hooks
	pre-commit autoupdate
