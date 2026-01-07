import pytest

from csvdiff.utils.csv import read_csv_with_duckdb, rows_to_csv_lines


def test_rows_to_csv_lines_basic():
    """Test basic CSV conversion."""
    rows = [
        ("a", "b", "c"),
        ("1", "2", "3"),
        ("x", "y", "z"),
    ]
    result = rows_to_csv_lines(rows)

    assert len(result) == 3
    assert result[0] == "a,b,c"
    assert result[1] == "1,2,3"
    assert result[2] == "x,y,z"


def test_rows_to_csv_lines_with_quotes():
    """Test CSV conversion with fields that need quoting."""
    rows = [
        ("field1", "field,with,comma", "field3"),
        ("field1", 'field"with"quotes', "field3"),
    ]
    result = rows_to_csv_lines(rows)

    assert len(result) == 2
    # CSV should quote fields with commas
    assert "field,with,comma" in result[0] or '"field,with,comma"' in result[0]
    # CSV should quote fields with quotes and escape internal quotes
    assert 'field"with"quotes' in result[1] or 'field""with""quotes' in result[1]


def test_rows_to_csv_lines_with_newlines():
    """Test CSV conversion with fields containing newlines."""
    rows = [
        ("field1", "field\nwith\nnewlines", "field3"),
    ]
    result = rows_to_csv_lines(rows)

    # Should produce a single line (row), not split by the internal newlines
    assert len(result) == 1
    # The newline should be preserved inside quotes
    assert "field\nwith\nnewlines" in result[0] or "field\nwith\nnewlines" in result[0]


def test_rows_to_csv_lines_empty():
    """Test with empty rows list."""
    rows = []
    result = rows_to_csv_lines(rows)

    assert result == []


def test_rows_to_csv_lines_single_column():
    """Test with single column."""
    rows = [
        ("value1",),
        ("value2",),
    ]
    result = rows_to_csv_lines(rows)

    assert len(result) == 2
    assert result[0] == "value1"
    assert result[1] == "value2"


def test_read_csv_with_duckdb_basic(tmp_path):
    file1 = tmp_path / "file1.csv"
    file1.write_text("a,b\n1,2\n3,4\n")

    rows1, cols1 = read_csv_with_duckdb(file1)

    assert len(rows1) == 2
    assert cols1 == ["a", "b"]


def test_read_csv_with_duckdb_sorted(tmp_path):
    file1 = tmp_path / "unsorted.csv"
    file1.write_text("a,b\n3,4\n1,2\n")

    rows1, _ = read_csv_with_duckdb(file1)

    # rows1 should be sorted by all columns: ('1', '2') then ('3', '4')
    # Note: DuckDB returns tuples of values
    assert rows1[0][0] == "1"
    assert rows1[0][1] == "2"
    assert rows1[1][0] == "3"
    assert rows1[1][1] == "4"


def test_read_csv_with_single_quote_filename(tmp_path):
    # Create a file with a single quote in the name
    filename = tmp_path / "test'file.csv"
    filename.write_text("col1,col2\n1,2", encoding="utf-8")

    try:
        rows, cols = read_csv_with_duckdb(filename)
        assert len(rows) == 1
        assert cols == ["col1", "col2"]
        assert rows[0] == ("1", "2")
    except Exception as e:
        pytest.fail(f"Failed to read file with quote in name: {e}")
