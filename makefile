install:
	uv sync --all-extras

lint:
	uv run ruff check && uv run ruff format --check

test:
	uv run pytest

build:
	uv build
