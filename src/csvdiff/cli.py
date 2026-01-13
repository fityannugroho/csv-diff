import time
from difflib import unified_diff
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from typing_extensions import Annotated

from csvdiff.utils.csv import read_csv_with_duckdb
from csvdiff.utils.files import create_unique_output_file
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
    file1: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=False,
            help="Path to the first CSV file.",
        ),
    ],
    file2: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=False,
            help="Path to the second CSV file.",
        ),
    ],
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            exists=False,
            file_okay=True,
            dir_okay=False,
            resolve_path=False,
            help="Specify the output file path (.diff, .txt, or .log extension).",
        ),
    ] = Path("result.diff"),
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

    # Validate output path (security and business rules)
    validated_output = validate_output_path(output)

    start_time = time.time()
    try:
        with console.status("Reading CSV files...") as status:
            # 1. Process first CSV file
            lines1, cols1 = read_csv_with_duckdb(file1)

            # Validate first file data
            if not lines1:
                typer.secho(f"Error: First CSV file '{file1}' contains no data.", fg=typer.colors.RED, err=True)
                raise typer.Exit(1)

            # 2. Process second CSV file
            lines2, cols2 = read_csv_with_duckdb(file2)

            # Validate second file data
            if not lines2:
                typer.secho(f"Error: Second CSV file '{file2}' contains no data.", fg=typer.colors.RED, err=True)
                raise typer.Exit(1)

        # Check column structures (outside spinner for clean messages)
        if cols1 != cols2:
            typer.secho("Warning: CSV files have different column structures.", fg=typer.colors.YELLOW, err=True)

        with console.status("Computing differences...") as status:
            # 3. Compute diff
            diff = unified_diff(lines1, lines2, fromfile=str(file1.resolve()), tofile=str(file2.resolve()), lineterm="")

            # 4. Write output
            status.update("Writing result...")
            has_differences = False
            with create_unique_output_file(validated_output) as f:
                actual_output_path = f.name  # Get actual filename created
                for line in diff:
                    f.write(line + "\n")
                    has_differences = True

        # Check if files are identical (no diff content)
        if not has_differences:
            typer.secho(
                f"No differences found. Files are identical. Empty diff saved to `{actual_output_path}`",
                fg=typer.colors.BRIGHT_CYAN,
            )
        else:
            typer.secho(f"Success. The result saved to `{actual_output_path}`", fg=typer.colors.BRIGHT_GREEN)

    except typer.Exit:
        raise
    except PermissionError as e:
        typer.secho(f"Error: No permission to write to file: {e}", fg=typer.colors.RED, err=True)
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
