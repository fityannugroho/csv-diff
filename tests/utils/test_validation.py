from pathlib import Path

import pytest
import typer

from csvdiff.utils.validation import (
    sanitize_output_path,
    validate_csv_file,
    validate_output_path,
)


def test_validate_csv_file_nonexistent_file(tmp_path):
    non_existent_file = tmp_path / "nonexistent.csv"
    with pytest.raises(typer.Exit):
        validate_csv_file(non_existent_file, "Test CSV file")


def test_validate_csv_file_not_a_file(tmp_path):
    directory = tmp_path / "directory"
    directory.mkdir()
    with pytest.raises(typer.Exit):
        validate_csv_file(directory, "Test CSV file")


def test_validate_csv_file_wrong_extension(tmp_path):
    non_csv_file = tmp_path / "file.txt"
    non_csv_file.touch()
    with pytest.raises(typer.Exit):
        validate_csv_file(non_csv_file, "Test CSV file")


def test_validate_csv_file_no_permission(tmp_path):
    csv_file = tmp_path / "file.csv"
    csv_file.touch()
    csv_file.chmod(0o000)  # Remove all permissions
    try:
        with pytest.raises(typer.Exit):
            validate_csv_file(csv_file, "Test CSV file")
    finally:
        csv_file.chmod(0o644)  # Restore permissions for cleanup


def test_validate_csv_file_valid_file(tmp_path):
    valid_csv_file = tmp_path / "file.csv"
    valid_csv_file.write_text("header1,header2\nvalue1,value2\n", encoding="utf-8")
    try:
        validate_csv_file(valid_csv_file, "Test CSV file")  # Should not raise any exception
    except typer.Exit:
        pytest.fail("validate_csv_file raised an exception for a valid file")


# --- Test cases for sanitize_output_path ---


def test_sanitize_output_path_absolute():
    with pytest.raises(typer.Exit):
        sanitize_output_path("/tmp/result")


def test_sanitize_output_path_traversal():
    with pytest.raises(typer.Exit):
        sanitize_output_path("../result")


def test_sanitize_output_path_traversal_deep():
    with pytest.raises(typer.Exit):
        sanitize_output_path("subdir/../../etc/passwd")


def test_sanitize_output_path_valid():
    result = sanitize_output_path("result")
    assert result == Path("result")


def test_sanitize_output_path_valid_subdir():
    result = sanitize_output_path("outputs/result")
    assert result == Path("outputs/result")


# --- Test cases for validate_output_path ---


def test_validate_output_path_auto_create(tmp_path):
    import os

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        output_path = Path("new_dir/output.diff")
        validate_output_path(output_path)
        assert (tmp_path / "new_dir").exists()
        assert (tmp_path / "new_dir").is_dir()
    finally:
        os.chdir(original_cwd)


def test_validate_output_path_not_a_directory(tmp_path):
    not_a_directory = tmp_path / "file.txt"
    not_a_directory.touch()
    output_path = not_a_directory / "output.diff"
    # This might fail during mkdir or is_dir check
    with pytest.raises(typer.Exit):
        validate_output_path(output_path)


def test_validate_output_path_no_permission(tmp_path, monkeypatch):
    restricted_dir = tmp_path / "restricted"
    restricted_dir.mkdir()
    output_path = restricted_dir / "output.diff"

    # Simulate a write error by patching the write_text method
    def fake_write_text(*args, **kwargs):
        raise PermissionError("Simulated write error")

    monkeypatch.setattr(Path, "write_text", fake_write_text)

    with pytest.raises(typer.Exit):
        validate_output_path(output_path)


def test_validate_output_path_valid_directory(tmp_path):
    valid_dir = tmp_path / "valid"
    valid_dir.mkdir()
    output_path = valid_dir / "output.diff"
    try:
        validate_output_path(output_path)  # Should not raise any exception
    except typer.Exit:
        pytest.fail("validate_output_path raised an exception for a valid directory")
