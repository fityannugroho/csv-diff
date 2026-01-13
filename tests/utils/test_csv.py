import pytest

from csvdiff.utils.csv import read_csv_with_duckdb


def test_read_csv_with_duckdb_basic(tmp_path):
    file1 = tmp_path / "file1.csv"
    file1.write_text("a,b\n1,2\n3,4\n")

    lines1, cols1 = read_csv_with_duckdb(file1)

    assert len(lines1) == 2
    assert cols1 == ["a", "b"]
    assert lines1[0] == "1,2"
    assert lines1[1] == "3,4"


def test_read_csv_with_duckdb_unsorted(tmp_path):
    file1 = tmp_path / "unsorted.csv"
    file1.write_text("a,b\n3,4\n1,2\n")

    lines1, _ = read_csv_with_duckdb(file1)

    # lines1 should maintain original order
    assert lines1[0] == "3,4"
    assert lines1[1] == "1,2"


def test_read_csv_with_single_quote_filename(tmp_path):
    # Create a file with a single quote in the name
    filename = tmp_path / "test'file.csv"
    filename.write_text("col1,col2\n1,2", encoding="utf-8")

    try:
        lines, cols = read_csv_with_duckdb(filename)
        assert len(lines) == 1
        assert cols == ["col1", "col2"]
        assert lines[0] == "1,2"
    except Exception as e:
        pytest.fail(f"Failed to read file with quote in name: {e}")


def test_read_csv_with_embedded_commas(tmp_path):
    """Test CSV with fields containing commas."""
    file1 = tmp_path / "commas.csv"
    file1.write_text('a,b\n"hello,world",test\n')

    lines, cols = read_csv_with_duckdb(file1)

    assert len(lines) == 1
    assert cols == ["a", "b"]
    # csv.writer should properly quote the field with comma
    assert '"hello,world"' in lines[0]


def test_read_csv_with_embedded_quotes(tmp_path):
    """Test CSV with fields containing quotes."""
    file1 = tmp_path / "quotes.csv"
    file1.write_text('a,b\n"say ""hello""",test\n')

    lines, cols = read_csv_with_duckdb(file1)

    assert len(lines) == 1
    # csv.writer escapes quotes by doubling them
    assert '""' in lines[0]


def test_read_csv_with_embedded_newlines(tmp_path):
    """Test CSV with fields containing newlines."""
    file1 = tmp_path / "newlines.csv"
    file1.write_text('a,b\n"line1\nline2",test\n')

    lines, cols = read_csv_with_duckdb(file1)

    assert len(lines) == 1
    # The newline should be preserved inside the quoted field
    assert "\n" in lines[0]
