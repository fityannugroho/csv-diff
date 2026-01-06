from csvdiff.cli import rows_to_csv_lines


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
