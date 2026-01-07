from typer.testing import CliRunner

from csvdiff.cli import app

runner = CliRunner()


def test_latin1_encoding(tmp_path):
    # Create a Latin-1 encoded CSV file with characters that are invalid in UTF-8
    content1 = "col1,col2\nvalue1,café"
    content2 = "col1,col2\nvalue1,café_modified"
    file1 = tmp_path / "file1.csv"
    file2 = tmp_path / "file2.csv"

    # Write as latin-1
    with open(file1, "w", encoding="latin-1") as f:
        f.write(content1)
    with open(file2, "w", encoding="latin-1") as f:
        f.write(content2)

    output_path = tmp_path / "output"
    result = runner.invoke(app, [str(file1), str(file2), "-o", str(output_path)])

    assert result.exit_code == 0
    assert "Success" in result.output

    diff_file = tmp_path / "output.diff"
    assert diff_file.exists()

    # Verify content
    diff_content = diff_file.read_text(encoding="utf-8")
    assert "café" in diff_content
    assert "café_modified" in diff_content


def test_cp1252_encoding(tmp_path):
    # CP1252 specific char (euro sign)
    content1 = "col1,col2\nvalue1,€"
    content2 = "col1,col2\nvalue1,€_new"
    file1 = tmp_path / "file1_cp1252.csv"
    file2 = tmp_path / "file2_cp1252.csv"

    with open(file1, "w", encoding="cp1252") as f:
        f.write(content1)
    with open(file2, "w", encoding="cp1252") as f:
        f.write(content2)

    output_path = tmp_path / "output"
    result = runner.invoke(app, [str(file1), str(file2), "-o", str(output_path)])

    assert result.exit_code == 0
    assert "Success" in result.output

    diff_file = tmp_path / "output.diff"
    assert diff_file.exists()

    # Verify content
    diff_content = diff_file.read_text(encoding="utf-8")
    assert "€" in diff_content


def test_iso8859_1_encoding(tmp_path):
    # ISO-8859-1 specific test
    content1 = "col1,col2\nvalue1,café"
    content2 = "col1,col2\nvalue1,café_iso"
    file1 = tmp_path / "file1_iso.csv"
    file2 = tmp_path / "file2_iso.csv"

    with open(file1, "w", encoding="iso-8859-1") as f:
        f.write(content1)
    with open(file2, "w", encoding="iso-8859-1") as f:
        f.write(content2)

    output_path = tmp_path / "output"
    result = runner.invoke(app, [str(file1), str(file2), "-o", str(output_path)])

    assert result.exit_code == 0
    assert "Success" in result.output

    diff_file = tmp_path / "output.diff"
    assert diff_file.exists()

    # Verify content
    diff_content = diff_file.read_text(encoding="utf-8")
    assert "café" in diff_content


def test_utf16_encoding(tmp_path):
    # UTF-16 specific test
    content1 = "col1,col2\nvalue1,café"
    content2 = "col1,col2\nvalue1,café_utf16"
    file1 = tmp_path / "file1_utf16.csv"
    file2 = tmp_path / "file2_utf16.csv"

    with open(file1, "w", encoding="utf-16") as f:
        f.write(content1)
    with open(file2, "w", encoding="utf-16") as f:
        f.write(content2)

    output_path = tmp_path / "output"
    result = runner.invoke(app, [str(file1), str(file2), "-o", str(output_path)])

    assert result.exit_code == 0
    assert "Success" in result.output

    diff_file = tmp_path / "output.diff"
    assert diff_file.exists()

    # Verify content
    diff_content = diff_file.read_text(encoding="utf-8")
    assert "café" in diff_content
    assert "café_utf16" in diff_content


def test_utf8_sig_encoding(tmp_path):
    # UTF-8 with BOM
    content1 = "\ufeffcol1,col2\nvalue1,café"
    content2 = "\ufeffcol1,col2\nvalue1,café_bom"
    file1 = tmp_path / "file1_bom.csv"
    file2 = tmp_path / "file2_bom.csv"

    with open(file1, "w", encoding="utf-8-sig") as f:
        f.write(content1)
    with open(file2, "w", encoding="utf-8-sig") as f:
        f.write(content2)

    output_path = tmp_path / "output"
    result = runner.invoke(app, [str(file1), str(file2), "-o", str(output_path)])

    assert result.exit_code == 0
    assert "Success" in result.output

    diff_file = tmp_path / "output.diff"
    assert diff_file.exists()

    # Verify content
    diff_content = diff_file.read_text(encoding="utf-8")
    assert "café" in diff_content
