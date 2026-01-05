# CSV Diff - Agent Guidelines

## Overview
A Python CLI tool for comparing two CSV files and displaying differences in `git diff` style. The tool sorts CSV data, computes unified diffs, and outputs results to `.diff` files.

## Tech Stack
- **Language:** Python 3.8+
- **Package Manager:** `uv`
- **CLI Framework:** `typer`
- **Data Processing:** `pandas`
- **Testing:** `pytest`
- **Linting & Formatting:** `ruff`

## Commands
- `uv sync --all-extras`: Install dependencies
- `uv run pytest`: Run all tests
- `uv run pytest --cov=csvdiff --cov-report=term-missing`: Run tests with coverage
- `uv run pytest tests/test_cli.py::test_compare_success`: Run a specific test
- `uv run ruff check`: Run linter
- `uv run ruff format`: Format code
- `uv build`: Build the package

## Rules and Workflows
- Follow all rules specified in [`.agent/rules`](.agent/rules) directory.
- Follow the workflow specified in [`.agent/workflows`](.agent/workflows) directory.

## Project Structure
- `src/csvdiff/` - Main source code
  - `cli.py` - Typer CLI with compare command, validation functions, and error handling
- `tests/` - Test suite
  - `test_cli.py` - Comprehensive CLI tests
- `docs/examples/` - Sample CSV files and expected diff outputs
- `pyproject.toml` - Project dependencies and metadata
- `pytest.ini` - Pytest configuration

## Key Components

### CLI Entry Point (`cli.py`)
The `compare()` function validates input CSV files, sorts DataFrames, computes unified diff using `difflib.unified_diff`, and writes output to a `.diff` file.

### Validation Functions
- `validate_csv_file()`: Checks file existence, extension (.csv), and read permissions
- `validate_output_path()`: Verifies output directory exists and is writable
- `get_unique_filename()`: Generates unique filenames by appending counters when conflicts exist

### Error Handling
Uses `typer.Exit` with exit codes (0=success, 1=error). Use user-friendly error messages.
