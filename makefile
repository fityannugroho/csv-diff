install:
	uv sync --all-extras

test:
	uv run pytest

build:
	uv build
