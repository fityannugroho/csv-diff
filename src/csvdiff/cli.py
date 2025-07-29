import pandas as pd
from difflib import unified_diff
from pathlib import Path
import typer
from typing_extensions import Annotated, Optional
from importlib.metadata import version, PackageNotFoundError

app = typer.Typer()

def validate_csv_file(file_path: Path, file_label: str) -> None:
    """Validate that the file exists, is a CSV, and is readable."""
    # Check if file exists
    if not file_path.is_file():
        typer.echo(f"❌ {file_label} '{file_path}' is not a file or does not exist.", err=True)
        raise typer.Exit(1)

    # Check file extension
    if file_path.suffix.lower() != '.csv':
        typer.echo(f"❌ {file_label} '{file_path}' is not a CSV file.", err=True)
        raise typer.Exit(1)

    # Check if file is readable
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
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
    version: Annotated[Optional[bool], typer.Option("--version", "-v", callback=version_option_callback, is_eager=True, help="Show the version of this package.")] = None
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

    try:
        # Read CSV files with error handling
        df1 = pd.read_csv(file1, dtype=str)
        df2 = pd.read_csv(file2, dtype=str)
    except pd.errors.EmptyDataError:
        typer.echo("📄 Error: One of the CSV files is empty.", err=True)
        raise typer.Exit(1)
    except pd.errors.ParserError as e:
        typer.echo(f"📊 Error: Failed to parse CSV files: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ Error: Failed to read CSV files: {e}", err=True)
        raise typer.Exit(1)

    # Validate that DataFrames are not empty
    if df1.empty:
        typer.echo(f"📄 Error: First CSV file '{file1}' contains no data.", err=True)
        raise typer.Exit(1)

    if df2.empty:
        typer.echo(f"📄 Error: Second CSV file '{file2}' contains no data.", err=True)
        raise typer.Exit(1)

    # Check if both files have the same columns
    if not df1.columns.equals(df2.columns):
        typer.echo("⚠️  Warning: CSV files have different column structures.", err=True)
        typer.echo(f"📋 File1 columns: {list(df1.columns)}", err=True)
        typer.echo(f"📋 File2 columns: {list(df2.columns)}", err=True)

    try:
        df1_sorted = df1.sort_values(by=df1.columns.tolist()).reset_index(drop=True)
        df2_sorted = df2.sort_values(by=df2.columns.tolist()).reset_index(drop=True)

        lines1 = df1_sorted.to_csv(index=False, header=False).splitlines()
        lines2 = df2_sorted.to_csv(index=False, header=False).splitlines()

        diff = list(unified_diff(
            lines1, lines2,
            fromfile=file1.name,
            tofile=file2.name,
            lineterm=''
        ))
    except Exception as e:
        typer.echo(f"❌ Error: Failed to compute diff: {e}", err=True)
        raise typer.Exit(1)

    # Write output with error handling
    try:
        output_path.write_text('\n'.join(diff), encoding='utf-8')
        typer.echo(f"✅ Diff result saved to: {output_path}")
    except PermissionError:
        typer.echo(f"🔒 No permission to write to file '{output_path}'.", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ Error: Failed to write output file: {e}", err=True)
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
