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


def read_csv_with_duckdb(file_path: Path) -> tuple[list[str], list[str]]:
    """Read a single CSV file using DuckDB for memory-efficient processing, returning CSV strings."""
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
        rel = conn.read_csv(str(target_path), all_varchar=True)
        cols = rel.columns

        # Convert to CSV string lines directly using chunked fetching for efficiency
        lines = []
        output = io.StringIO()
        writer = csv.writer(output, lineterminator="")

        chunk_size = 10000
        while True:
            chunk = rel.fetchmany(size=chunk_size)
            if not chunk:
                break
            for row in chunk:
                output.seek(0)
                output.truncate(0)
                writer.writerow(row)
                lines.append(output.getvalue())

        return lines, cols
    finally:
        conn.close()
        # Clean up temporary file if it exists
        if temp_file_path and temp_file_path.exists():
            try:
                temp_file_path.unlink()
            except Exception:
                pass
