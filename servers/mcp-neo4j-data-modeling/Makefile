# Makefile for cypher-guard Python bindings

.PHONY: format test clean inspector build_local_docker_image

format:
	uv run ruff check --select I . --fix
	uv run ruff check --fix .
	uv run ruff format .

test:
	uv run pytest tests/ -s 

inspector:
	npx @modelcontextprotocol/inspector uv --directory src/mcp_neo4j_data_modeling run mcp-neo4j-data-modeling

build_local_docker_image:
	docker build -t mcp-neo4j-data-modeling .

clean:
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf .pytest_cache/
	rm -rf .vscode/
	rm -rf .venv/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf .pytest_cache/