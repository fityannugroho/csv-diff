from typer.testing import CliRunner

from csvdiff.cli import app

runner = CliRunner()


def test_latin1_encoding(tmp_path):
    # Create a Latin-1 encoded CSV file with characters that are invalid in UTF-8
    content = "col1,col2\nvalue1,café"
    file1 = tmp_path / "file1.csv"

    # Write as latin-1
    with open(file1, "w", encoding="latin-1") as f:
        f.write(content)

    file2 = tmp_path / "file2.csv"
    with open(file2, "w", encoding="latin-1") as f:
        f.write(content)

    output_path = tmp_path / "output"
    result = runner.invoke(app, [str(file1), str(file2), "-o", str(output_path)])

    if result.exit_code != 0:
        print(f"\n[DEBUG] Output:\n{result.output}")
        print(f"[DEBUG] Exception: {result.exception}")

    assert result.exit_code == 0
    assert "Success" in result.output
    assert (tmp_path / "output.diff").exists()


def test_cp1252_encoding(tmp_path):
    # CP1252 specific char (euro sign)
    content = "col1,col2\nvalue1,€"
    file1 = tmp_path / "file1_cp1252.csv"
    file2 = tmp_path / "file2_cp1252.csv"

    with open(file1, "w", encoding="cp1252") as f:
        f.write(content)
    with open(file2, "w", encoding="cp1252") as f:
        f.write(content)

    output_path = tmp_path / "output"
    result = runner.invoke(app, [str(file1), str(file2), "-o", str(output_path)])

    if result.exit_code != 0:
        print(f"\n[DEBUG] Output:\n{result.output}")
        print(f"[DEBUG] Exception: {result.exception}")

    assert result.exit_code == 0
    assert "Success" in result.output
    assert (tmp_path / "output.diff").exists()


def test_iso8859_1_encoding(tmp_path):
    # ISO-8859-1 specific test
    # "café" in iso-8859-1 is b'caf\xe9'
    content = "col1,col2\nvalue1,café"
    file1 = tmp_path / "file1_iso.csv"
    file2 = tmp_path / "file2_iso.csv"

    with open(file1, "w", encoding="iso-8859-1") as f:
        f.write(content)
    with open(file2, "w", encoding="iso-8859-1") as f:
        f.write(content)

    output_path = tmp_path / "output"
    result = runner.invoke(app, [str(file1), str(file2), "-o", str(output_path)])

    if result.exit_code != 0:
        print(f"\n[DEBUG] Output:\n{result.output}")
        print(f"[DEBUG] Exception: {result.exception}")

    assert result.exit_code == 0
    assert "Success" in result.output
    assert (tmp_path / "output.diff").exists()


def test_utf16_encoding(tmp_path):
    # UTF-16 specific test
    content = "col1,col2\nvalue1,value2"
    file1 = tmp_path / "file1_utf16.csv"
    file2 = tmp_path / "file2_utf16.csv"

    with open(file1, "w", encoding="utf-16") as f:
        f.write(content)
    with open(file2, "w", encoding="utf-16") as f:
        f.write(content)

    output_path = tmp_path / "output"
    result = runner.invoke(app, [str(file1), str(file2), "-o", str(output_path)])

    if result.exit_code != 0:
        print(f"\n[DEBUG] Output:\n{result.output}")
        print(f"[DEBUG] Exception: {result.exception}")

    assert result.exit_code == 0
    assert "Success" in result.output
    assert (tmp_path / "output.diff").exists()


def test_utf8_sig_encoding(tmp_path):
    # UTF-8 with BOM
    content = "\ufeffcol1,col2\nvalue1,value2"
    file1 = tmp_path / "file1_bom.csv"
    file2 = tmp_path / "file2_bom.csv"

    with open(file1, "w", encoding="utf-8") as f:
        f.write(content)
    with open(file2, "w", encoding="utf-8") as f:
        f.write(content)

    output_path = tmp_path / "output"
    result = runner.invoke(app, [str(file1), str(file2), "-o", str(output_path)])

    if result.exit_code != 0:
        print(f"\n[DEBUG] Output:\n{result.output}")
        print(f"[DEBUG] Exception: {result.exception}")

    assert result.exit_code == 0
    assert "Success" in result.output
    assert (tmp_path / "output.diff").exists()
