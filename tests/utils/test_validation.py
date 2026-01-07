from pathlib import Path

import pytest
import typer

from csvdiff.utils.validation import validate_csv_file, validate_output_path


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


# --- Test cases for validate_output_path ---


def test_validate_output_path_absolute():
    with pytest.raises(typer.Exit):
        validate_output_path(Path("/tmp/result.diff"))


def test_validate_output_path_traversal():
    with pytest.raises(typer.Exit):
        validate_output_path(Path("../result.diff"))


def test_validate_output_path_traversal_deep():
    with pytest.raises(typer.Exit):
        validate_output_path(Path("subdir/../../etc/passwd"))


def test_validate_output_path_valid_subdir():
    result = validate_output_path(Path("outputs/result.diff"))
    assert result == Path("outputs/result.diff")


def test_validate_output_path_allowed_extensions():
    """Test that .diff, .txt, .log, and no extension are allowed."""
    # All should succeed without raising
    assert validate_output_path(Path("result.diff")) == Path("result.diff")
    assert validate_output_path(Path("result.txt")) == Path("result.txt")
    assert validate_output_path(Path("result.log")) == Path("result.log")
    assert validate_output_path(Path("result")) == Path("result")  # No extension


def test_validate_output_path_case_insensitive_extension():
    """Test that extensions are case-insensitive."""
    assert validate_output_path(Path("result.DIFF")) == Path("result.DIFF")
    assert validate_output_path(Path("result.TXT")) == Path("result.TXT")
    assert validate_output_path(Path("result.Log")) == Path("result.Log")


def test_validate_output_path_reject_invalid_extensions():
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
            validate_output_path(Path(path_str))
