from pathlib import Path

import pytest
import typer

from csvdiff.utils.validation import (
    sanitize_output_path,
    validate_csv_file,
    validate_output_path,
)


def test_validate_csv_file_wrong_extension(tmp_path):
    non_csv_file = tmp_path / "file.txt"
    non_csv_file.touch()
    with pytest.raises(typer.Exit):
        validate_csv_file(non_csv_file, "Test CSV file")


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
        sanitize_output_path(Path("/tmp/result.diff"))


def test_sanitize_output_path_traversal():
    with pytest.raises(typer.Exit):
        sanitize_output_path(Path("../result.diff"))


def test_sanitize_output_path_traversal_deep():
    with pytest.raises(typer.Exit):
        sanitize_output_path(Path("subdir/../../etc/passwd"))


def test_sanitize_output_path_valid_subdir():
    result = sanitize_output_path(Path("outputs/result.diff"))
    assert result == Path("outputs/result.diff")


def test_sanitize_output_path_allowed_extensions():
    """Test that .diff, .txt, .log, and no extension are allowed."""
    # All should succeed without raising
    assert sanitize_output_path(Path("result.diff")) == Path("result.diff")
    assert sanitize_output_path(Path("result.txt")) == Path("result.txt")
    assert sanitize_output_path(Path("result.log")) == Path("result.log")
    assert sanitize_output_path(Path("result")) == Path("result")  # No extension


def test_sanitize_output_path_case_insensitive_extension():
    """Test that extensions are case-insensitive."""
    assert sanitize_output_path(Path("result.DIFF")) == Path("result.DIFF")
    assert sanitize_output_path(Path("result.TXT")) == Path("result.TXT")
    assert sanitize_output_path(Path("result.Log")) == Path("result.Log")


def test_sanitize_output_path_reject_invalid_extensions():
    """Test that non-text extensions are rejected."""
    invalid_extensions = [
        "result.csv",
        "result.json",
        "result.xml",
        "result.pdf",
        "result.docx",
        "result.html",
        "output.png",
    ]

    for path_str in invalid_extensions:
        with pytest.raises(typer.Exit):
            sanitize_output_path(Path(path_str))


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
