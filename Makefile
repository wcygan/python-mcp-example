.PHONY: help install install-dev test lint format type-check clean dev

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements-dev.txt
	pre-commit install

test: ## Run unit tests only
	pytest tests/ -k "not integration" -v

test-unit: ## Run unit tests only
	pytest tests/test_server.py -v

test-integration: ## Run integration tests
	pytest tests/integration/ -v

test-all: ## Run all tests including integration
	pytest tests/ -v

test-cov: ## Run tests with coverage
	pytest --cov=mcp_kubernetes --cov-report=html --cov-report=term

test-integration-safe: ## Run integration tests with safety checks
	MCP_KUBERNETES_READ_ONLY=true MCP_KUBERNETES_LOG_LEVEL=WARNING pytest tests/integration/ -v

lint: ## Run linting
	flake8 mcp_kubernetes tests
	isort --check-only mcp_kubernetes tests
	black --check mcp_kubernetes tests

format: ## Format code
	isort mcp_kubernetes tests
	black mcp_kubernetes tests

type-check: ## Run type checking
	mypy mcp_kubernetes

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

dev: ## Start development server
	python -m mcp_kubernetes --debug

build: ## Build package
	python -m build

install-package: ## Install package in development mode
	pip install -e .

check: lint type-check test ## Run all checks

ci: check ## Run CI checks