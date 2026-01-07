import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from csvdiff.cli import app

runner = CliRunner()


def create_temp_csv(content: str, dir_path: Path, name: str) -> Path:
    path = dir_path / name
    path.write_text(content)
    return path


@pytest.fixture
def in_tmp_path(tmp_path):
    """Fixture to change CWD to tmp_path during test."""
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(original_cwd)


def test_compare_success(in_tmp_path):
    # Create two temporary CSV files
    create_temp_csv("a,b\n1,2\n3,4", in_tmp_path, "file1.csv")
    create_temp_csv("a,b\n1,2\n3,5", in_tmp_path, "file2.csv")

    # Use relative path for output with extension
    result = runner.invoke(app, ["file1.csv", "file2.csv", "-o", "output.diff"])

    assert result.exit_code == 0
    output_file = in_tmp_path / "output.diff"
    assert output_file.exists()
    assert "3,4" in output_file.read_text()
    assert "3,5" in output_file.read_text()
    assert "Success" in result.output


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
    assert "missing.csv" in result.output


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


def test_csv_with_different_columns(in_tmp_path):
    create_temp_csv("a,b\n1,2", in_tmp_path, "a.csv")
    create_temp_csv("x,y\n1,2", in_tmp_path, "b.csv")

    result = runner.invoke(app, ["a.csv", "b.csv", "-o", "diff.diff"])
    assert result.exit_code == 0
    assert "different column structures" in result.output


def test_cli_with_single_quote_filename(in_tmp_path):
    # End-to-end CLI test with single quote in filename
    file1 = in_tmp_path / "data'1.csv"
    file2 = in_tmp_path / "data'2.csv"

    file1.write_text("a,b\n1,2", encoding="utf-8")
    file2.write_text("a,b\n1,3", encoding="utf-8")

    result = runner.invoke(app, ["data'1.csv", "data'2.csv", "-o", "out.diff"])

    assert result.exit_code == 0
    assert "Success" in result.output


def test_latin1_encoding(in_tmp_path):
    # Create a Latin-1 encoded CSV file with characters that are invalid in UTF-8
    content1 = "col1,col2\nvalue1,café"
    content2 = "col1,col2\nvalue1,café_modified"
    file1 = in_tmp_path / "file1.csv"
    file2 = in_tmp_path / "file2.csv"

    # Write as latin-1
    with open(file1, "w", encoding="latin-1") as f:
        f.write(content1)
    with open(file2, "w", encoding="latin-1") as f:
        f.write(content2)

    result = runner.invoke(app, ["file1.csv", "file2.csv", "-o", "output.diff"])

    assert result.exit_code == 0
    assert "Success" in result.output

    diff_file = in_tmp_path / "output.diff"
    assert diff_file.exists()

    # Verify content
    diff_content = diff_file.read_text(encoding="utf-8")
    assert "café" in diff_content
    assert "café_modified" in diff_content


def test_cp1252_encoding(in_tmp_path):
    # CP1252 specific char (euro sign)
    content1 = "col1,col2\nvalue1,€"
    content2 = "col1,col2\nvalue1,€_new"
    file1 = in_tmp_path / "file1_cp1252.csv"
    file2 = in_tmp_path / "file2_cp1252.csv"

    with open(file1, "w", encoding="cp1252") as f:
        f.write(content1)
    with open(file2, "w", encoding="cp1252") as f:
        f.write(content2)

    result = runner.invoke(app, ["file1_cp1252.csv", "file2_cp1252.csv", "-o", "output.diff"])

    assert result.exit_code == 0
    assert "Success" in result.output

    diff_file = in_tmp_path / "output.diff"
    assert diff_file.exists()

    # Verify content
    diff_content = diff_file.read_text(encoding="utf-8")
    assert "€" in diff_content


def test_iso8859_1_encoding(in_tmp_path):
    # ISO-8859-1 specific test
    content1 = "col1,col2\nvalue1,café"
    content2 = "col1,col2\nvalue1,café_iso"
    file1 = in_tmp_path / "file1_iso.csv"
    file2 = in_tmp_path / "file2_iso.csv"

    with open(file1, "w", encoding="iso-8859-1") as f:
        f.write(content1)
    with open(file2, "w", encoding="iso-8859-1") as f:
        f.write(content2)

    result = runner.invoke(app, ["file1_iso.csv", "file2_iso.csv", "-o", "output.diff"])

    assert result.exit_code == 0
    assert "Success" in result.output

    diff_file = in_tmp_path / "output.diff"
    assert diff_file.exists()

    # Verify content
    diff_content = diff_file.read_text(encoding="utf-8")
    assert "café" in diff_content


def test_utf16_encoding(in_tmp_path):
    # UTF-16 specific test
    content1 = "col1,col2\nvalue1,café"
    content2 = "col1,col2\nvalue1,café_utf16"
    file1 = in_tmp_path / "file1_utf16.csv"
    file2 = in_tmp_path / "file2_utf16.csv"

    with open(file1, "w", encoding="utf-16") as f:
        f.write(content1)
    with open(file2, "w", encoding="utf-16") as f:
        f.write(content2)

    result = runner.invoke(app, ["file1_utf16.csv", "file2_utf16.csv", "-o", "output.diff"])

    assert result.exit_code == 0
    assert "Success" in result.output

    diff_file = in_tmp_path / "output.diff"
    assert diff_file.exists()

    # Verify content
    diff_content = diff_file.read_text(encoding="utf-8")
    assert "café" in diff_content
    assert "café_utf16" in diff_content


def test_utf8_sig_encoding(in_tmp_path):
    # UTF-8 with BOM
    content1 = "\ufeffcol1,col2\nvalue1,café"
    content2 = "\ufeffcol1,col2\nvalue1,café_bom"
    file1 = in_tmp_path / "file1_bom.csv"
    file2 = in_tmp_path / "file2_bom.csv"

    with open(file1, "w", encoding="utf-8-sig") as f:
        f.write(content1)
    with open(file2, "w", encoding="utf-8-sig") as f:
        f.write(content2)

    result = runner.invoke(app, ["file1_bom.csv", "file2_bom.csv", "-o", "output.diff"])

    assert result.exit_code == 0
    assert "Success" in result.output

    diff_file = in_tmp_path / "output.diff"
    assert diff_file.exists()

    # Verify content
    diff_content = diff_file.read_text(encoding="utf-8")
    assert "café" in diff_content


def test_large_csv_files(in_tmp_path):
    """Test with large CSV files to validate memory efficiency."""
    # Create large CSV files (10K rows each)
    num_rows = 10000

    # Generate file1 with sequential data
    file1 = in_tmp_path / "large1.csv"
    with open(file1, "w", encoding="utf-8") as f:
        f.write("id,name,value,description\n")
        for i in range(num_rows):
            f.write(f"{i},name_{i},value_{i},description_{i}\n")

    # Generate file2 with some modifications
    file2 = in_tmp_path / "large2.csv"
    with open(file2, "w", encoding="utf-8") as f:
        f.write("id,name,value,description\n")
        for i in range(num_rows):
            # Modify every 100th row
            if i % 100 == 0:
                f.write(f"{i},name_{i}_modified,value_{i},description_{i}\n")
            else:
                f.write(f"{i},name_{i},value_{i},description_{i}\n")

    result = runner.invoke(app, ["large1.csv", "large2.csv", "-o", "output.diff"])

    assert result.exit_code == 0
    assert "Success" in result.output

    diff_file = in_tmp_path / "output.diff"
    assert diff_file.exists()

    # Verify diff contains modifications
    diff_content = diff_file.read_text(encoding="utf-8")
    assert "name_0_modified" in diff_content
    assert "name_100_modified" in diff_content


def test_compare_custom_extension_txt(in_tmp_path):
    """Test output with custom .txt extension."""
    create_temp_csv("a,b\n1,2", in_tmp_path, "file1.csv")
    create_temp_csv("a,b\n1,3", in_tmp_path, "file2.csv")

    result = runner.invoke(app, ["file1.csv", "file2.csv", "-o", "output.txt"])

    assert result.exit_code == 0
    output_file = in_tmp_path / "output.txt"
    assert output_file.exists()
    assert "Success" in result.output


def test_compare_custom_extension_log(in_tmp_path):
    """Test output with custom .log extension."""
    create_temp_csv("a,b\n1,2", in_tmp_path, "file1.csv")
    create_temp_csv("a,b\n1,3", in_tmp_path, "file2.csv")

    result = runner.invoke(app, ["file1.csv", "file2.csv", "-o", "changes.log"])

    assert result.exit_code == 0
    output_file = in_tmp_path / "changes.log"
    assert output_file.exists()
    assert "Success" in result.output


def test_compare_rejects_directory_as_output(in_tmp_path):
    """Test that Typer rejects directory paths for --output parameter."""
    create_temp_csv("a,b\n1,2", in_tmp_path, "file1.csv")
    create_temp_csv("a,b\n1,2", in_tmp_path, "file2.csv")

    # Create a directory
    output_dir = in_tmp_path / "output_dir"
    output_dir.mkdir()

    # Try to use directory as output (should fail)
    result = runner.invoke(app, ["file1.csv", "file2.csv", "-o", "output_dir"])

    assert result.exit_code != 0
    assert "directory" in result.output.lower()


def test_compare_rejects_directory_as_file1(tmp_path):
    """Test that Typer rejects directory paths for file1 argument."""
    # Create a directory instead of file
    dir1 = tmp_path / "dir1"
    dir1.mkdir()
    csv2 = create_temp_csv("a,b\n1,2", tmp_path, "file2.csv")

    result = runner.invoke(app, [str(dir1), str(csv2), "-o", "output.diff"])

    assert result.exit_code != 0
    assert "directory" in result.output.lower()


def test_compare_rejects_directory_as_file2(tmp_path):
    """Test that Typer rejects directory paths for file2 argument."""
    csv1 = create_temp_csv("a,b\n1,2", tmp_path, "file1.csv")
    # Create a directory instead of file
    dir2 = tmp_path / "dir2"
    dir2.mkdir()

    result = runner.invoke(app, [str(csv1), str(dir2), "-o", "output.diff"])

    assert result.exit_code != 0
    assert "directory" in result.output.lower()


def test_compare_rejects_nonexistent_file1(tmp_path):
    """Test that Typer rejects non-existent file1."""
    missing_file = tmp_path / "missing.csv"
    csv2 = create_temp_csv("a,b\n1,2", tmp_path, "file2.csv")

    result = runner.invoke(app, [str(missing_file), str(csv2), "-o", "output.diff"])

    assert result.exit_code != 0
    assert "does not exist" in result.output.lower()


def test_compare_rejects_nonexistent_file2(tmp_path):
    """Test that Typer rejects non-existent file2."""
    csv1 = create_temp_csv("a,b\n1,2", tmp_path, "file1.csv")
    missing_file = tmp_path / "missing.csv"

    result = runner.invoke(app, [str(csv1), str(missing_file), "-o", "output.diff"])

    assert result.exit_code != 0
    assert "does not exist" in result.output.lower()


def test_compare_output_with_subdirectory(in_tmp_path):
    """Test output path with subdirectory (auto-create)."""
    create_temp_csv("a,b\n1,2", in_tmp_path, "file1.csv")
    create_temp_csv("a,b\n1,3", in_tmp_path, "file2.csv")

    result = runner.invoke(app, ["file1.csv", "file2.csv", "-o", "outputs/result.diff"])

    assert result.exit_code == 0
    output_file = in_tmp_path / "outputs" / "result.diff"
    assert output_file.exists()
    assert "Success" in result.output


def test_compare_output_absolute_path_rejected(in_tmp_path):
    """Test that absolute output paths are rejected by sanitize_output_path."""
    create_temp_csv("a,b\n1,2", in_tmp_path, "file1.csv")
    create_temp_csv("a,b\n1,3", in_tmp_path, "file2.csv")

    result = runner.invoke(app, ["file1.csv", "file2.csv", "-o", "/tmp/output.diff"])

    assert result.exit_code != 0
    assert "absolute" in result.output.lower()


def test_compare_output_parent_traversal_rejected(in_tmp_path):
    """Test that parent directory traversal is rejected."""
    create_temp_csv("a,b\n1,2", in_tmp_path, "file1.csv")
    create_temp_csv("a,b\n1,3", in_tmp_path, "file2.csv")

    result = runner.invoke(app, ["file1.csv", "file2.csv", "-o", "../output.diff"])

    assert result.exit_code != 0
    assert "traversal" in result.output.lower() or "parent" in result.output.lower()


def test_compare_rejects_invalid_extension(in_tmp_path):
    """Test that non-text extensions are rejected."""
    create_temp_csv("a,b\n1,2", in_tmp_path, "file1.csv")
    create_temp_csv("a,b\n1,3", in_tmp_path, "file2.csv")

    # Try various invalid extensions
    invalid_outputs = ["output.csv", "output.json", "output.pdf", "output.html"]

    for output in invalid_outputs:
        result = runner.invoke(app, ["file1.csv", "file2.csv", "-o", output])
        assert result.exit_code != 0
        assert "text file" in result.output.lower()


def test_compare_output_no_extension(in_tmp_path):
    """Test that files without extension are allowed."""
    create_temp_csv("a,b\n1,2", in_tmp_path, "file1.csv")
    create_temp_csv("a,b\n1,3", in_tmp_path, "file2.csv")

    result = runner.invoke(app, ["file1.csv", "file2.csv", "-o", "result"])

    assert result.exit_code == 0
    output_file = in_tmp_path / "result"
    assert output_file.exists()
    assert "Success" in result.output


def test_compare_output_case_insensitive_extension(in_tmp_path):
    """Test that extensions are case-insensitive."""
    create_temp_csv("a,b\n1,2", in_tmp_path, "file1.csv")
    create_temp_csv("a,b\n1,3", in_tmp_path, "file2.csv")

    result = runner.invoke(app, ["file1.csv", "file2.csv", "-o", "output.DIFF"])

    assert result.exit_code == 0
    output_file = in_tmp_path / "output.DIFF"
    assert output_file.exists()
