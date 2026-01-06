import pytest
from typer.testing import CliRunner

from csvdiff.cli import app, read_csv_with_duckdb

runner = CliRunner()


def test_read_csv_with_single_quote_filename(tmp_path):
    # Create a file with a single quote in the name
    # This simulates a valid user filename that causes syntax error in SQL injection
    filename = tmp_path / "test'file.csv"
    filename.write_text("col1,col2\n1,2", encoding="utf-8")

    try:
        # This should fail if the code is vulnerable to SQL injection
        rows, cols = read_csv_with_duckdb(filename)

        # Verify correctness of data read
        assert len(rows) == 1
        assert cols == ["col1", "col2"]
        assert rows[0] == ("1", "2")
    except Exception as e:
        pytest.fail(f"Failed to read file with quote in name: {e}")


def test_cli_with_single_quote_filename(tmp_path):
    # End-to-end CLI test
    file1 = tmp_path / "data'1.csv"
    file2 = tmp_path / "data'2.csv"

    file1.write_text("a,b\n1,2", encoding="utf-8")
    file2.write_text("a,b\n1,3", encoding="utf-8")

    result = runner.invoke(app, [str(file1), str(file2), "-o", str(tmp_path / "out")])

    assert result.exit_code == 0
    assert "Success" in result.output
