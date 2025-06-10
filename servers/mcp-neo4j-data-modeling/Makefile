# Makefile for cypher-guard Python bindings

.PHONY: format test clean

format:
	uv run ruff format .
	uv run ruff check --select I . --fix

test:
	uv run pytest tests/ -vv
	

clean:
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf .pytest_cache/
	rm -rf .vscode/
	rm -rf .venv/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf .pytest_cache/