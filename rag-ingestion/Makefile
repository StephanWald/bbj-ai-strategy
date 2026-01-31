.DEFAULT_GOAL := help

.PHONY: help sync test lint format typecheck check clean

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

sync: ## Install all dependencies
	uv sync

test: ## Run tests
	uv run pytest

lint: ## Run linter
	uv run ruff check src/ tests/

format: ## Format code
	uv run ruff format src/ tests/

typecheck: ## Run type checker
	uv run mypy src/

check: lint typecheck test ## Run all checks (lint, typecheck, test)

clean: ## Remove build artifacts and caches
	rm -rf dist/ .mypy_cache/ .ruff_cache/ .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
