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


def sanitize_output_path(output_path: Path) -> Path:
    """
    Sanitize and validate output path to prevent path traversal.

    Rules:
    - Must be relative path (no absolute paths)
    - Must not traverse parent directories (no ../)
    - Must resolve to location within or below CWD
    - Can include subdirectories (e.g., "outputs/result.diff")

    Args:
        output_path: User-provided output Path object (with extension)

    Returns:
        Sanitized Path object relative to CWD

    Raises:
        typer.Exit: If path is invalid or attempts traversal
    """
    # Reject absolute paths
    if output_path.is_absolute():
        typer.secho(
            f"Error: Output path '{output_path}' must be relative, not absolute.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)

    # Validate extension (must be text file format)
    suffix = output_path.suffix.lower()
    allowed_extensions = {".diff", ".txt", ".log", ""}  # "" means no extension
    if suffix not in allowed_extensions:
        typer.secho(
            "Error: Output must be a text file (.diff, .txt, or .log).",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)

    # Check for parent directory traversal in components
    # This catches "../", "../../", etc.
    if ".." in output_path.parts:
        typer.secho(
            f"Error: Output path '{output_path}' contains parent directory traversal (..).",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)

    # Resolve path and verify it's within CWD
    # This is defense-in-depth in case symbolic links or other tricks are used
    try:
        cwd = Path.cwd().resolve()
        resolved = (cwd / output_path).resolve()

        # Check if resolved path is within CWD
        # Use relative_to() which raises ValueError if not relative
        try:
            resolved.relative_to(cwd)
        except ValueError:
            typer.secho(
                f"Error: Output path '{output_path}' resolves outside working directory.",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(1)

    except Exception as e:
        # Avoid double Exit raising if already raised by relative_to check
        if isinstance(e, typer.Exit):
            raise
        typer.secho(
            f"Error: Cannot validate output path '{output_path}': {e}",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)

    return output_path


def validate_output_path(output_path: Path) -> None:
    """
    Validate that the output directory is writable, creating it if necessary.

    Note: This function assumes output_path has already been sanitized
    by sanitize_output_path() to prevent path traversal.

    Args:
        output_path: Pre-sanitized Path object (relative to CWD)

    Raises:
        typer.Exit: If directory cannot be created or isn't writable
    """
    output_dir = output_path.parent

    # Create parent directory if it doesn't exist (Option B)
    if not output_dir.exists():
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            typer.secho(
                f"Error: Cannot create output directory '{output_dir}': {e}",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(1)

    # Verify it's a directory
    if not output_dir.is_dir():
        typer.secho(
            f"Error: Output path parent '{output_dir}' is not a directory.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)

    # Test writability with a temporary file
    try:
        test_file = output_dir / ".write_test"
        test_file.write_text("test")
        test_file.unlink()
    except PermissionError:
        typer.secho(
            f"Error: No permission to write to directory '{output_dir}'.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)
    except Exception as e:
        typer.secho(
            f"Error: Cannot write to directory '{output_dir}': {e}",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)
