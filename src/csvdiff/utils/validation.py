from pathlib import Path

import typer

from csvdiff.utils.csv import detect_encoding


def validate_csv_file(file_path: Path, file_label: str) -> None:
    """Validate that the file exists, is a CSV, and is readable."""
    # Check if file exists
    if not file_path.is_file():
        typer.secho(
            f"Error: {file_label} '{file_path}' is not a file or does not exist.", fg=typer.colors.RED, err=True
        )
        raise typer.Exit(1)

    # Check file extension
    if file_path.suffix.lower() != ".csv":
        typer.secho(f"Error: {file_label} '{file_path}' is not a CSV file.", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    # Check if file is readable
    try:
        encoding = detect_encoding(file_path)
        with open(file_path, encoding=encoding) as f:
            f.read(1)  # Try to read first character
    except PermissionError:
        typer.secho(f"Error: No permission to read {file_label} '{file_path}'.", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.secho(f"Error: Cannot read {file_label} '{file_path}': {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)


def validate_output_path(output_path: Path | str) -> None:
    """Validate that the output directory is writable."""
    # Convert string to Path if needed
    if isinstance(output_path, str):
        output_path = Path(output_path)

    output_dir = output_path.parent

    # Check if parent directory exists
    if not output_dir.exists():
        typer.secho(f"Error: Output directory '{output_dir}' does not exist.", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    # Check if we can write to the directory
    if not output_dir.is_dir():
        typer.secho(f"Error: Output path parent '{output_dir}' is not a directory.", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    # Check writability with a temporary file
    try:
        test_file = output_dir / ".write_test"
        test_file.write_text("test")
        test_file.unlink()
    except PermissionError:
        typer.secho(f"Error: No permission to write to directory '{output_dir}'.", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.secho(f"Error: Cannot write to directory '{output_dir}': {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
