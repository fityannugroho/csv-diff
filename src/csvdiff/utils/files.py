import io
from pathlib import Path


def create_unique_output_file(output_path: Path) -> io.TextIOWrapper:
    """
    Create parent directory if needed, then atomically create a unique output file.

    This function:
    1. Creates parent directory if it doesn't exist (with parents=True)
    2. Eliminates race conditions by using exclusive file creation mode ('x')
    3. If a file with the target name already exists, automatically retries with an
       incremented counter inserted before the extension

    Args:
        output_path: Full Path object including filename and extension (e.g., "result.diff")

    Returns:
        file_handle where the file is already opened for writing

    Raises:
        RuntimeError: If unable to create a unique file after max attempts
        PermissionError: If lacking permission to create directory or file
        FileExistsError: If parent path component exists as a file (not directory)
        NotADirectoryError: If parent component is a file (from mkdir)
        OSError: If other OS-level errors occur during directory or file creation
    """
    counter = 0
    max_attempts = 1000

    # Extract components: parent dir, stem (filename without extension), suffix (extension)
    parent_dir = output_path.parent
    stem = output_path.stem
    suffix = output_path.suffix

    # Create parent directory if it doesn't exist
    # Note: This will raise FileExistsError if parent_dir exists as a file (not directory)
    # and NotADirectoryError if any parent component is a file
    if parent_dir != Path(".") and not parent_dir.exists():
        parent_dir.mkdir(parents=True, exist_ok=True)

    while counter < max_attempts:
        if counter == 0:
            filename = f"{stem}{suffix}"
        else:
            filename = f"{stem} ({counter}){suffix}"

        # Construct full path: parent_dir / filename
        full_path = parent_dir / filename

        try:
            # 'x' mode: exclusive creation (atomic operation)
            # Fails immediately if file exists - no race condition
            return open(full_path, "x", encoding="utf-8")
        except FileExistsError:
            # File exists, try next counter
            counter += 1
            continue

    # Should never reach here in normal operation
    raise RuntimeError(f"Failed to create unique file after {max_attempts} attempts")
