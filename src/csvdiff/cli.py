import csv
import io
import time
from difflib import unified_diff
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Optional

import duckdb
import typer
from rich.console import Console
from typing_extensions import Annotated

app = typer.Typer()
console = Console()


def rows_to_csv_lines(rows: list[tuple]) -> list[str]:
    """Convert list of row tuples to CSV string lines."""
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="")
    lines = []
    for row in rows:
        # Clear buffer
        output.seek(0)
        output.truncate(0)
        writer.writerow(row)
        lines.append(output.getvalue())
    return lines


def read_csv_with_duckdb(file_path: Path) -> tuple[list[tuple], list[str]]:
    """Read and sort a single CSV file using DuckDB for memory-efficient processing."""
    conn = duckdb.connect()

    try:
        # Use DuckDB to read CSV
        # We assume headers exist as per limitations
        # all_varchar=True ensures all data is treated as strings to match original behavior

        # Read and sort file
        rel = conn.from_query(f"SELECT * FROM read_csv_auto('{file_path}', all_varchar=True) ORDER BY ALL")
        rows = rel.fetchall()
        cols = rel.columns

        return rows, cols
    finally:
        conn.close()


def validate_csv_file(file_path: Path, file_label: str) -> None:
    """Validate that the file exists, is a CSV, and is readable."""
    # Check if file exists
    if not file_path.is_file():
        typer.echo(f"❌ {file_label} '{file_path}' is not a file or does not exist.", err=True)
        raise typer.Exit(1)

    # Check file extension
    if file_path.suffix.lower() != ".csv":
        typer.echo(f"❌ {file_label} '{file_path}' is not a CSV file.", err=True)
        raise typer.Exit(1)

    # Check if file is readable
    try:
        with open(file_path, encoding="utf-8") as f:
            f.read(1)  # Try to read first character
    except PermissionError:
        typer.echo(f"🔒 No permission to read {file_label} '{file_path}'.", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ Cannot read {file_label} '{file_path}': {e}", err=True)
        raise typer.Exit(1)


def validate_output_path(output_path: Path) -> None:
    """Validate that the output directory is writable."""
    output_dir = output_path.parent

    # Check if parent directory exists
    if not output_dir.exists():
        typer.echo(f"📁 Output directory '{output_dir}' does not exist.", err=True)
        raise typer.Exit(1)

    # Check if we can write to the directory
    if not output_dir.is_dir():
        typer.echo(f"📁 Output path parent '{output_dir}' is not a directory.", err=True)
        raise typer.Exit(1)

    # Check writability with a temporary file
    try:
        test_file = output_dir / ".write_test"
        test_file.write_text("test", encoding="utf-8")
        test_file.unlink()
    except PermissionError:
        typer.echo(f"🔒 No permission to write to directory '{output_dir}'.", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ Cannot write to directory '{output_dir}': {e}", err=True)
        raise typer.Exit(1)


def get_unique_filename(base_name: str, extension: str = ".diff") -> Path:
    """Generate a unique filename by appending a counter if necessary."""
    output_path = Path(f"{base_name}{extension}")
    counter = 1
    while output_path.exists():
        output_path = Path(f"{base_name} ({counter}){extension}")
        counter += 1
    return output_path


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
            typer.echo(f"{package_name}: Version information not available. Make sure the package is installed.")
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
        with console.status("⏳ Comparing CSV files..."):
            try:
                rows1, cols1 = read_csv_with_duckdb(file1)
                rows2, cols2 = read_csv_with_duckdb(file2)
            except Exception as e:
                typer.echo(f"❌ Error: Failed to read CSV files: {e}", err=True)
                raise typer.Exit(1)

        # Validate that data is not empty
        if not rows1:
            typer.echo(f"📄 Error: First CSV file '{file1}' contains no data.", err=True)
            raise typer.Exit(1)

        if not rows2:
            typer.echo(f"📄 Error: Second CSV file '{file2}' contains no data.", err=True)
            raise typer.Exit(1)

        # Check if both files have the same columns
        if cols1 != cols2:
            typer.echo("⚠️  Warning: CSV files have different column structures.", err=True)
            typer.echo(f"📋 File1 columns: {cols1}", err=True)
            typer.echo(f"📋 File2 columns: {cols2}", err=True)

        lines1 = rows_to_csv_lines(rows1)
        lines2 = rows_to_csv_lines(rows2)

        # Free memory from rows immediately
        del rows1, rows2

        # Generate diff as an iterator (not a list) to save memory
        diff = unified_diff(lines1, lines2, fromfile=file1.name, tofile=file2.name, lineterm="")
    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"❌ Error: Failed to compute diff: {e}", err=True)
        raise typer.Exit(1)

    # Write output with error handling - stream line-by-line to save memory
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            for line in diff:
                f.write(line + "\n")

        typer.echo(f"✅ Diff result saved to: {output_path}")
    except PermissionError:
        typer.echo(f"🔒 No permission to write to file '{output_path}'.", err=True)
    except Exception as e:
        typer.echo(f"❌ Error: Failed to write output file: {e}", err=True)

    # Display execution time
    end_time = time.time()
    duration = end_time - start_time
    typer.echo(f"⏱️  Execution time: {duration:.3f}s")


if __name__ == "__main__":
    app()
