import io
from pathlib import Path


def create_unique_output_file(base_name: str, extension: str = ".diff") -> io.TextIOWrapper:
    """
    Atomically create a unique output file and return path and file handle.

    This function eliminates race conditions by using exclusive file creation mode ('x').
    If a file with the target name already exists, it automatically retries with an
    incremented counter.

    Args:
        base_name: Base name for the output file (without extension)
        extension: File extension (default: ".diff")

    Returns:
        file_handle where the file is already opened for writing

    Raises:
        RuntimeError: If unable to create a unique file after max attempts
        PermissionError: If lacking permission to create the file
        OSError: If other OS-level errors occur during file creation
    """
    counter = 0
    max_attempts = 1000

    while counter < max_attempts:
        if counter == 0:
            filename = f"{base_name}{extension}"
        else:
            filename = f"{base_name} ({counter}){extension}"

        output_path = Path(filename)
        try:
            # 'x' mode: exclusive creation (atomic operation)
            # Fails immediately if file exists - no race condition
            return open(output_path, "x", encoding="utf-8")
        except FileExistsError:
            # File exists, try next counter
            counter += 1
            continue

    # Should never reach here in normal operation
    raise RuntimeError(f"Failed to create unique file after {max_attempts} attempts")
