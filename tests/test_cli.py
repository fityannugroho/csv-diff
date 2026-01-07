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


def test_compare_identical_files(in_tmp_path):
    """Test comparing identical CSV files (should produce minimal/empty diff)."""
    # Create two identical CSV files
    content = "a,b,c\n1,2,3\n4,5,6\n7,8,9"
    create_temp_csv(content, in_tmp_path, "file1.csv")
    create_temp_csv(content, in_tmp_path, "file2.csv")

    result = runner.invoke(app, ["file1.csv", "file2.csv", "-o", "output.diff"])

    assert result.exit_code == 0
    output_file = in_tmp_path / "output.diff"
    assert output_file.exists()

    # When files are identical, diff should be minimal (only headers, no +/- lines)
    diff_content = output_file.read_text()
    # Check that there are no added (+) or removed (-) lines (beyond the header lines)
    lines = diff_content.split("\n")
    # Filter out header lines (---, +++, @@)
    data_lines = [
        line
        for line in lines
        if line and not line.startswith("---") and not line.startswith("+++") and not line.startswith("@@")
    ]
    # For identical files, we should have no +/- data lines
    changed_lines = [line for line in data_lines if line.startswith("+") or line.startswith("-")]
    assert len(changed_lines) == 0, f"Expected no changes, but found: {changed_lines}"

    # Verify user-friendly message
    assert "No differences found" in result.output
    assert "identical" in result.output.lower()


def test_compare_non_csv_extension(tmp_path):
    not_csv = create_temp_csv("x,y\n1,2", tmp_path, "invalid.txt")
    csv = create_temp_csv("x,y\n1,2", tmp_path, "valid.csv")

    result = runner.invoke(app, [str(not_csv), str(csv)])

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
