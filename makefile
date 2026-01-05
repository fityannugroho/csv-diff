install:
	uv sync --all-extras

lint:
	uv run ruff check && uv run ruff format

test:
	uv run pytest

build:
	uv build
