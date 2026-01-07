import csv
import io
import os
import shutil
import tempfile
from pathlib import Path

import duckdb


def detect_encoding(file_path: Path) -> str:
    """Detect encoding by trying a prioritized list of encodings."""
    # Try to detect BOM first
    try:
        with open(file_path, "rb") as f:
            raw = f.read(4)
        if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
            return "utf-16"
        if raw.startswith(b"\xef\xbb\xbf"):
            return "utf-8-sig"
    except Exception:
        pass

    encodings = [
        "utf-8",
        "cp1252",
        "iso-8859-1",
    ]

    for encoding in encodings:
        try:
            with open(file_path, encoding=encoding) as f:
                # Read a larger chunk to be more certain
                f.read(8192)
            return encoding
        except UnicodeError:
            continue

    # If we get here, none worked. Raise an error that will be caught by the caller.
    raise ValueError(f"Could not detect encoding for {file_path}. Tried: {', '.join(encodings)}")


def rows_to_csv_lines(rows: list[tuple]) -> list[str]:
    """Convert list of row tuples to CSV string lines."""
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="")
    lines = []
    for row in rows:
        output.seek(0)
        output.truncate(0)
        writer.writerow(row)
        lines.append(output.getvalue())
    return lines


def read_csv_with_duckdb(file_path: Path) -> tuple[list[tuple], list[str]]:
    """Read and sort a single CSV file using DuckDB for memory-efficient processing."""
    encoding = detect_encoding(file_path)
    conn = duckdb.connect()
    temp_file_path = None

    try:
        target_path = file_path

        # If encoding is not UTF-8, convert to a temporary UTF-8 file
        # DuckDB only supports UTF-8 for CSV reading efficiently
        if encoding.lower() not in ["utf-8", "utf8"]:
            # Create a temporary file
            fd, temp_path = tempfile.mkstemp(suffix=".csv")
            os.close(fd)
            temp_file_path = Path(temp_path)

            # Convert to UTF-8
            # We read with detected encoding and write as UTF-8
            with open(file_path, encoding=encoding) as src:
                with open(temp_file_path, "w", encoding="utf-8") as dst:
                    shutil.copyfileobj(src, dst)

            target_path = temp_file_path

        # Use DuckDB to read CSV
        # We assume headers exist as per limitations
        # all_varchar=True ensures all data is treated as strings to match original behavior

        # Read and sort file using Relational API
        # This approach is safe from SQL injection and faster than parameterized SQL queries
        rel = conn.read_csv(str(target_path), all_varchar=True).order("ALL")
        rows = rel.fetchall()
        cols = rel.columns

        return rows, cols
    finally:
        conn.close()
        # Clean up temporary file if it exists
        if temp_file_path and temp_file_path.exists():
            try:
                temp_file_path.unlink()
            except Exception:
                pass  # Best effort cleanup
