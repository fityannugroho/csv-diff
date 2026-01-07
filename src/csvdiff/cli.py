import time
from difflib import unified_diff
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from typing_extensions import Annotated

from csvdiff.utils.csv import read_csv_with_duckdb, rows_to_csv_lines
from csvdiff.utils.files import get_unique_filename
from csvdiff.utils.validation import validate_csv_file, validate_output_path

app = typer.Typer()
console = Console()


def version_option_callback(value: bool):
    """
    Callback function for the `--version` option.
    """
    if value:
        package_name = "csv-diff-py"
        try:
            typer.echo(f"{package_name}: {version(package_name)}")
            raise typer.Exit()
        except PackageNotFoundError:
            typer.secho(
                f"{package_name}: Version information not available. Make sure the package is installed.",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(1)


@app.command(no_args_is_help=True)
def compare(
    file1: Annotated[Path, typer.Argument(help="Path to the first CSV file.")],
    file2: Annotated[Path, typer.Argument(help="Path to the second CSV file.")],
    output: Annotated[str, typer.Option("--output", "-o", help="Specify the output file name.")] = "result",
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version", "-v", callback=version_option_callback, is_eager=True, help="Show the version of this package."
        ),
    ] = None,
):
    """
    Compare two CSV files and save the result to a .diff file.
    """
    # Validate input files
    validate_csv_file(file1, "First CSV file")
    validate_csv_file(file2, "Second CSV file")

    # Determine output path and validate
    output_path = get_unique_filename(output, ".diff")
    validate_output_path(output_path)

    start_time = time.time()
    try:
        with console.status("Reading and sorting CSV files...") as status:
            # 1. Read and sort CSVs
            rows1, cols1 = read_csv_with_duckdb(file1)
            rows2, cols2 = read_csv_with_duckdb(file2)

        # 2. Validate data (outside spinner to ensure clean error messages)
        if not rows1:
            typer.secho(f"Error: First CSV file '{file1}' contains no data.", fg=typer.colors.RED, err=True)
            raise typer.Exit(1)
        if not rows2:
            typer.secho(f"Error: Second CSV file '{file2}' contains no data.", fg=typer.colors.RED, err=True)
            raise typer.Exit(1)

        # Check column structures
        if cols1 != cols2:
            typer.secho("Warning: CSV files have different column structures.", fg=typer.colors.YELLOW, err=True)

        with console.status("Computing differences...") as status:
            # 3. Compute diff
            lines1 = rows_to_csv_lines(rows1)
            lines2 = rows_to_csv_lines(rows2)
            del rows1, rows2  # Free memory

            diff = unified_diff(lines1, lines2, fromfile=file1.name, tofile=file2.name, lineterm="")

            # 4. Write output
            status.update("Writing result...")
            with open(output_path, "w", encoding="utf-8") as f:
                for line in diff:
                    f.write(line + "\n")

        typer.secho(f"Success. The result saved to `{output_path}`", fg=typer.colors.BRIGHT_GREEN)

    except typer.Exit:
        raise
    except PermissionError:
        typer.secho(f"Error: No permission to write to file '{output_path}'.", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    finally:
        # Display execution time
        end_time = time.time()
        duration = end_time - start_time
        typer.secho(f"({duration:.3f}s)", fg=typer.colors.CYAN)


if __name__ == "__main__":
    app()
