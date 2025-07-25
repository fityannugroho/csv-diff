import typer
from typer.testing import CliRunner
import pytest
from pathlib import Path
from csvdiff.cli import validate_csv_file
from csvdiff.cli import validate_output_path
from csvdiff.cli import app

runner = CliRunner()

# --- Test cases for validate_csv_file ---

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

# --- Test cases for validate_output_path ---

def test_validate_output_path_nonexistent_directory(tmp_path):
    non_existent_dir = tmp_path / "nonexistent" / "output.diff"
    with pytest.raises(typer.Exit):
        validate_output_path(non_existent_dir)

def test_validate_output_path_not_a_directory(tmp_path):
    not_a_directory = tmp_path / "file.txt"
    not_a_directory.touch()
    output_path = not_a_directory / "output.diff"
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

# --- Test cases for CLI app ---

def create_temp_csv(content: str, dir_path: Path, name: str) -> Path:
    path = dir_path / name
    path.write_text(content)
    return path

def test_compare_success(tmp_path):
    # Create two temporary CSV files
    csv1 = create_temp_csv("a,b\n1,2\n3,4", tmp_path, "file1.csv")
    csv2 = create_temp_csv("a,b\n1,2\n3,5", tmp_path, "file2.csv")

    result = runner.invoke(app, [str(csv1), str(csv2), "-o", str(tmp_path / "output")])

    assert result.exit_code == 0
    output_file = tmp_path / "output.diff"
    assert output_file.exists()
    assert "3,4" in output_file.read_text()
    assert "3,5" in output_file.read_text()
    assert "✅" in result.output

def test_compare_non_csv_extension(tmp_path):
    not_csv = create_temp_csv("x,y\n1,2", tmp_path, "invalid.txt")
    csv = create_temp_csv("x,y\n1,2", tmp_path, "valid.csv")

    result = runner.invoke(app, [str(not_csv), str(csv)])

    assert result.exit_code != 0
    assert "not a CSV file" in result.output

def test_file1_not_found(tmp_path):
    file1 = tmp_path / "missing.csv"  # not created
    file2 = create_temp_csv("a,b\n1,2", tmp_path, "file2.csv")

    result = runner.invoke(app, [str(file1), str(file2)])
    assert result.exit_code != 0
    assert "does not exist" in result.output

def test_file2_is_not_csv(tmp_path):
    file1 = create_temp_csv("a,b\n1,2", tmp_path, "file1.csv")
    file2 = create_temp_csv("a,b\n1,2", tmp_path, "file2.txt")  # not a CSV

    result = runner.invoke(app, [str(file1), str(file2)])
    assert result.exit_code != 0
    assert "not a CSV file" in result.output

def test_empty_csv_file(tmp_path):
    file1 = create_temp_csv("", tmp_path, "empty.csv")
    file2 = create_temp_csv("a,b\n1,2", tmp_path, "valid.csv")

    result = runner.invoke(app, [str(file1), str(file2)])
    assert result.exit_code != 0
    assert "empty" in result.output or "no data" in result.output

def test_csv_with_different_columns(tmp_path):
    file1 = create_temp_csv("a,b\n1,2", tmp_path, "a.csv")
    file2 = create_temp_csv("x,y\n1,2", tmp_path, "b.csv")
    output = tmp_path / "diff.diff"

    result = runner.invoke(app, [str(file1), str(file2), "-o", str(output)])
    assert result.exit_code == 0
    assert "different column structures" in result.output
