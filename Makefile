.PHONY: install dev test lint typecheck format clean build publish docs

install:  ## Install agenteval with all extras
	uv pip install -e ".[all]"

dev:  ## Install with dev dependencies
	uv pip install -e ".[all,dev]"

test:  ## Run tests with coverage
	pytest tests/ -v --cov=agenteval --cov-report=term-missing

test-unit:  ## Run unit tests only
	pytest tests/unit/ -v

lint:  ## Run linter
	ruff check src/ tests/

typecheck:  ## Run type checker
	mypy src/agenteval/

format:  ## Format code
	ruff format src/ tests/
	ruff check --fix src/ tests/

clean:  ## Remove build artifacts
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

build:  ## Build package
	uv build

publish: build  ## Publish to PyPI (use trusted publisher in CI)
	uv publish

docs:  ## Serve docs locally
	mkdocs serve

docs-build:  ## Build docs
	mkdocs build

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
