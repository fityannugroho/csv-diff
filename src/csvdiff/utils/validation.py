from pathlib import Path

import typer


def validate_csv_file(file_path: Path, file_label: str) -> None:
    """
    Validate that the file has a .csv extension.

    Note: File existence, type (file vs directory), and readability are already
    validated by Typer with exists=True, file_okay=True, dir_okay=False, readable=True.
    """
    # Check file extension (only custom validation needed)
    if file_path.suffix.lower() != ".csv":
        typer.secho(f"Error: {file_label} '{file_path}' is not a CSV file.", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)


def validate_output_path(output_path: Path) -> Path:
    """
    Validate output path for security and business rules (pure validation, no side effects).

    Security Rules:
    - Must be relative path (no absolute paths)
    - Must not traverse parent directories (no ../)
    - Must resolve to location within or below CWD (defense against symlink attacks)

    Business Rules:
    - Must have text file extension (.diff, .txt, .log) or no extension
    - Can include subdirectories (e.g., "outputs/result.diff")

    Args:
        output_path: User-provided output Path object (with extension)

    Returns:
        Validated Path object relative to CWD

    Raises:
        typer.Exit: If path is invalid, violates security rules, or has wrong extension

    Note:
        This function is pure (no side effects). Directory creation and writability
        checks are handled by create_unique_output_file().
    """
    # Security Check 1: Reject absolute paths
    if output_path.is_absolute():
        typer.secho(
            f"Error: Output path '{output_path}' must be relative, not absolute.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)

    # Business Rule: Validate extension (must be text file format)
    suffix = output_path.suffix.lower()
    allowed_extensions = {".diff", ".txt", ".log", ""}  # "" means no extension
    if suffix not in allowed_extensions:
        typer.secho(
            "Error: Output must be a text file (.diff, .txt, or .log).",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)

    # Security Check 2: Check for parent directory traversal
    # This catches "../", "../../", etc.
    if ".." in output_path.parts:
        typer.secho(
            f"Error: Output path '{output_path}' contains parent directory traversal (..).",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)

    # Security Check 3: Resolve path and verify it's within CWD
    # This is defense-in-depth against symbolic link attacks
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

    except typer.Exit:
        # Re-raise typer.Exit from relative_to check above
        raise
    except Exception as e:
        typer.secho(
            f"Error: Cannot validate output path '{output_path}': {e}",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)

    return output_path
