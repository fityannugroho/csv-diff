# Coding Rules

- Follow DRY (Don't Repeat Yourself) and KISS (Keep It Simple, Stupid) principles.
- Write modular, reusable functions and classes.
- Prefer clear function/variable names over inline comments.
- Naming conventions:
  - Functions/Variables: `snake_case`
  - Constants: `UPPER_SNAKE_CASE`
  - Private functions: `_prefix_underscore`
- Prefer composition over inheritance.
- Avoid duck typing; prefer static typing to ensure type safety and clarity.

## Code Style & Quality
- Use docstrings for all public functions. Focus on the *why* rather than the *what* for complex logic.
- Use Python 3.9+ compatible type hinting syntax.
- Use `Optional[T]` from `typing` for optional types.
- Annotate all function signatures.

## Import Order
Order imports in three groups, separated by blank lines:
1. Standard library imports (e.g., `import os`, `from pathlib import Path`)
2. Third-party library imports (e.g., `import pandas as pd`, `import typer`)
3. Local application imports (e.g., `from csvdiff.cli import validate_csv_file`)

Example:
```python
import pandas as pd
from difflib import unified_diff
from pathlib import Path

import typer
from typing import Annotated, Optional

from importlib.metadata import version, PackageNotFoundError
```

## Error Handling
- Use `typer.Exit` with appropriate exit codes (0=success, 1=error).
- All error messages should use appropriate output to stderr via `typer.echo(..., err=True)`.

## Data Processing Patterns
- Use `duckdb` for CSV operations to handle larger files efficiently.
- Read CSVs with `all_varchar=True` to preserve all data as strings.

- Use `pathlib.Path` for all file path operations.
- Validation functions should raise `typer.Exit(1)` on failure, return `None` on success.

## CLI Design Patterns
- Use Typer's `@app.command(no_args_is_help=True)` decorator.
- Use `Annotated` for parameter documentation.
- Generate unique filenames to avoid overwriting: `get_unique_filename()`
- Write with explicit encoding: `output_path.write_text(..., encoding='utf-8')`

Example:
```python
@app.command(no_args_is_help=True)
def compare(
    file1: Annotated[Path, typer.Argument(help="Path to the first CSV file.")],
    file2: Annotated[Path, typer.Argument(help="Path to the second CSV file.")],
    output: Annotated[str, typer.Option("--output", "-o", help="Specify the output file name.")] = "result",
):
    """Compare two CSV files and save the result to a .diff file."""
    # Implementation
```
