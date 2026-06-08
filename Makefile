.PHONY: fmt lint tests check

fmt:
	@echo "🔧  Formatting..."
	@uv run --dev ruff format .
	@uv run --dev ruff check --fix .

lint:
	@echo "🔧  Linting..."
	@uv run --dev ruff format --check . || (echo "Run make fmt" && exit 1)
	@uv run --dev ruff check .
	@uv run --dev ty check .

tests:
	@echo "🔧  Testing..."
	@uv run --dev pytest

check: fmt lint tests
