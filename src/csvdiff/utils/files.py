from pathlib import Path


def get_unique_filename(base_name: str, extension: str = ".diff") -> Path:
    """Generate a unique filename by appending a counter if necessary."""
    output_path = Path(f"{base_name}{extension}")
    counter = 1
    while output_path.exists():
        output_path = Path(f"{base_name} ({counter}){extension}")
        counter += 1
    return output_path
