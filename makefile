install:
	uv sync --all-extras

lint:
	uv run ruff check && uv run ruff format --check

lint-fix:
	uv run ruff check --fix && uv run ruff format

test:
	uv run pytest

build:
	uv build
