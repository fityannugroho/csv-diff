import threading
from pathlib import Path

import pytest

from csvdiff.utils.files import create_unique_output_file


def test_create_unique_output_file_no_conflict(tmp_path):
    """Test atomic file creation when no conflict exists."""
    base_name = tmp_path / "output"
    handle = create_unique_output_file(base_name)

    try:
        output_path = Path(handle.name)
        assert output_path == base_name.with_suffix(".diff")
        assert output_path.exists()  # File should be created
        assert handle.writable()  # Handle should be open for writing
        assert handle.name == str(output_path)
    finally:
        handle.close()


def test_create_unique_output_file_with_conflict(tmp_path):
    """Test atomic file creation with existing file (should use counter)."""
    base_name = tmp_path / "output"
    # Create a conflicting file
    conflict_file = base_name.with_suffix(".diff")
    conflict_file.touch()

    handle = create_unique_output_file(base_name)

    try:
        output_path = Path(handle.name)
        assert output_path == tmp_path / "output (1).diff"
        assert output_path.exists()
        assert handle.writable()
    finally:
        handle.close()


def test_create_unique_output_file_multiple_conflicts(tmp_path):
    """Test atomic file creation with multiple existing files."""
    base_name = tmp_path / "output"
    # Create multiple conflicting files
    (base_name.with_suffix(".diff")).touch()
    (tmp_path / "output (1).diff").touch()

    handle = create_unique_output_file(base_name)

    try:
        output_path = Path(handle.name)
        assert output_path == tmp_path / "output (2).diff"
        assert output_path.exists()
        assert handle.writable()
    finally:
        handle.close()


def test_create_unique_output_file_custom_extension(tmp_path):
    """Test atomic file creation with custom extension."""
    base_name = tmp_path / "output"
    # Create a conflicting file with custom extension
    (base_name.with_suffix(".log")).touch()

    handle = create_unique_output_file(base_name, ".log")

    try:
        output_path = Path(handle.name)
        assert output_path == tmp_path / "output (1).log"
        assert output_path.exists()
        assert handle.writable()
    finally:
        handle.close()


def test_create_unique_output_file_can_write(tmp_path):
    """Test that the returned file handle can be written to."""
    base_name = tmp_path / "output"
    handle = create_unique_output_file(base_name)

    try:
        output_path = Path(handle.name)
        # Write some content
        handle.write("test content\n")
        handle.flush()

        # Verify content was written
        assert output_path.read_text() == "test content\n"
    finally:
        handle.close()
        output_path = Path(handle.name)
        if output_path.exists():
            output_path.unlink()


def test_create_unique_output_file_concurrent_creation(tmp_path):
    """Test concurrent file creation to verify race-condition protection."""
    base_name = tmp_path / "concurrent_test"
    created_files = []
    errors = []

    def create_file():
        try:
            handle = create_unique_output_file(base_path=base_name)
            output_path = Path(handle.name)
            created_files.append(output_path)
            handle.write(f"Thread {threading.current_thread().name}\n")
            handle.close()
        except Exception as e:
            errors.append(e)

    # Create multiple threads that try to create files simultaneously
    threads = []
    for i in range(10):
        t = threading.Thread(target=create_file, name=f"Thread-{i}")
        threads.append(t)

    # Start all threads
    for t in threads:
        t.start()

    # Wait for all threads to complete
    for t in threads:
        t.join()

    # Verify no errors occurred
    assert len(errors) == 0, f"Errors occurred: {errors}"

    # Verify all files were created
    assert len(created_files) == 10

    # Verify all filenames are unique
    assert len(set(created_files)) == 10

    # Verify all files exist and have content
    for file_path in created_files:
        assert file_path.exists()
        content = file_path.read_text()
        assert "Thread" in content


def test_create_unique_output_file_encoding(tmp_path):
    """Test that file is created with UTF-8 encoding."""
    base_name = tmp_path / "output"
    handle = create_unique_output_file(base_name)

    try:
        output_path = Path(handle.name)
        # Write unicode content
        handle.write("Hello 世界 🌍\n")
        handle.flush()

        # Verify content can be read back correctly
        content = output_path.read_text(encoding="utf-8")
        assert content == "Hello 世界 🌍\n"
    finally:
        handle.close()
        output_path = Path(handle.name)
        if output_path.exists():
            output_path.unlink()


def test_create_unique_output_file_permission_error(tmp_path):
    """Test handling of permission errors during file creation."""
    # Create a directory without write permission
    restricted_dir = tmp_path / "restricted"
    restricted_dir.mkdir()
    restricted_dir.chmod(0o555)  # Read + execute only, no write

    base_name = restricted_dir / "output"

    try:
        with pytest.raises(PermissionError):
            create_unique_output_file(base_name)
    finally:
        # Restore permissions for cleanup
        restricted_dir.chmod(0o755)
