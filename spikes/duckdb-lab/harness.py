"""Spike harness: duckdb read path vs stdlib csv.reader vs raw lines (plan 005).

Scratch tooling for the read-path spike. Not part of the package; not wired
into CI. Run from the repo root with:

    uv run spikes/duckdb-lab/harness.py

For each fixture under fixtures/, three readers are compared:

1. the current csvdiff path (duckdb read + csv.writer re-serialization)
2. a stdlib candidate (csv.reader + identical re-serialization)
3. a raw-line candidate (physical lines, no parsing)

Output: one JSON object per fixture on stdout (also written to
harness-output.jsonl), then a human-readable summary table.
"""

import csv
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from csvdiff.utils.csv import detect_encoding, read_csv_with_duckdb  # noqa: E402

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
OUTPUT_FILE = Path(__file__).resolve().parent / "harness-output.jsonl"


def read_stdlib(file_path: Path) -> tuple[list[str], list[str]]:
    """Read via stdlib csv.reader; re-serialize exactly like the duckdb path.

    Returns (lines, cols) in the same shape as read_csv_with_duckdb so the
    outputs are directly comparable.
    """
    encoding = detect_encoding(file_path)
    with open(file_path, encoding=encoding, newline="") as fh:
        rows = list(csv.reader(fh))
    if not rows:
        return [], []
    cols = list(rows[0])
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="")
    lines = []
    for row in rows[1:]:
        out.seek(0)
        out.truncate(0)
        writer.writerow(row)
        lines.append(out.getvalue())
    return lines, cols


def read_raw_lines(file_path: Path) -> list[str]:
    """Raw physical lines: decode per detect_encoding, split on line boundaries."""
    encoding = detect_encoding(file_path)
    with open(file_path, encoding=encoding) as fh:
        text = fh.read()
    return text.splitlines()


def first_diff(a: list[str], b: list[str]) -> dict:
    """Exact first difference between two line lists, or None."""
    common = min(len(a), len(b))
    for i in range(common):
        if a[i] != b[i]:
            return {"index": i, "duckdb": a[i], "stdlib": b[i]}
    if len(a) != len(b):
        return {
            "index": common,
            "duckdb": a[common] if len(a) > common else None,
            "stdlib": b[common] if len(b) > common else None,
        }
    return None


def fidelity_vs_raw(lines: list[str], raw: list[str]) -> list[int]:
    """How many re-serialized lines appear verbatim among the raw physical lines."""
    raw_set = set(raw)
    return [sum(1 for line in lines if line in raw_set), len(lines)]


def build_note(rec: dict, lines1: list[str], lines2: list[str], raw: list[str]) -> str:
    """One-line NOTE: round-trip fidelity and CLI diff impact."""
    r1, r2 = rec["reader1"], rec["reader2"]
    if not r1["ok"] and not r2["ok"]:
        return f"both readers fail: duckdb={r1['error']}; stdlib={r2['error']}"
    if not r1["ok"]:
        return (
            f"duckdb path fails ({r1['error']}); stdlib parses OK -> "
            "migration would ACCEPT a file the tool rejects today"
        )
    if not r2["ok"]:
        return (
            f"stdlib csv.reader fails ({r2['error']}); duckdb parses OK -> "
            "stdlib would REJECT a file the tool accepts today"
        )
    if rec["lines_equal_1v2"] and rec["cols_equal"]:
        # Compare re-serialized data lines against the raw physical lines with
        # the header row excluded (the header is not part of `lines`).
        raw_data = raw[1:] if raw else []
        if set(lines1) == set(raw_data):
            return "identical re-serialized output; raw-line candidate matches data lines exactly (nothing hidden)"
        if any("\n" in line or "\r" in line for line in lines1):
            return (
                "identical re-serialized output; raw-line candidate splits the embedded-newline "
                "cell into separate physical lines (plan 001 rejects this at the CLI)"
            )
        return (
            "identical re-serialized output; raw-line candidate preserves the original quoting "
            "(byte-level quote normalization, e.g. redundant quotes dropped / empty-vs-missing "
            "fields both serialize to empty) - see doc section 4"
        )
    if rec["lines_equal_1v2"]:
        return f"lines identical but column structure differs: duckdb cols={r1['cols']} stdlib cols={r2['cols']}"
    fd = rec["first_diff"]
    fid1 = fidelity_vs_raw(lines1, raw)
    fid2 = fidelity_vs_raw(lines2, raw)
    return (
        f"re-serialized lines differ at index {fd['index']}: "
        f"duckdb={fd['duckdb']!r} stdlib={fd['stdlib']!r}; "
        f"fidelity vs raw {fid1} vs {fid2} -> would change CLI diff output"
    )


def main() -> None:
    results = []
    for fixture in sorted(FIXTURES_DIR.glob("*.csv")):
        rec = {"fixture": fixture.name}
        lines1, lines2, lines3 = [], [], []
        try:
            lines1, cols1 = read_csv_with_duckdb(fixture)
            rec["reader1"] = {"ok": True, "n_lines": len(lines1), "cols": list(cols1)}
        except Exception as e:  # noqa: BLE001 - record and continue
            rec["reader1"] = {"ok": False, "error": f"{type(e).__name__}: {e}"}
        try:
            lines2, cols2 = read_stdlib(fixture)
            rec["reader2"] = {"ok": True, "n_lines": len(lines2), "cols": list(cols2)}
        except Exception as e:  # noqa: BLE001
            rec["reader2"] = {"ok": False, "error": f"{type(e).__name__}: {e}"}
        try:
            lines3 = read_raw_lines(fixture)
            rec["reader3"] = {"ok": True, "n_lines": len(lines3)}
        except Exception as e:  # noqa: BLE001
            rec["reader3"] = {"ok": False, "error": f"{type(e).__name__}: {e}"}

        rec["lines_equal_1v2"] = rec["reader1"]["ok"] and rec["reader2"]["ok"] and lines1 == lines2
        rec["cols_equal"] = rec["reader1"]["ok"] and rec["reader2"]["ok"] and cols1 == cols2
        if rec["lines_equal_1v2"] and rec["cols_equal"]:
            rec["first_diff"] = None
        elif rec["reader1"]["ok"] and rec["reader2"]["ok"]:
            rec["first_diff"] = first_diff(lines1, lines2)
            if not rec["cols_equal"]:
                rec["first_diff"]["cols"] = {"duckdb": list(cols1), "stdlib": list(cols2)}
        rec["note"] = build_note(rec, lines1, lines2, lines3)
        results.append(rec)
        print(json.dumps(rec, ensure_ascii=False))

    with OUTPUT_FILE.open("w", encoding="utf-8") as fh:
        for rec in results:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print()
    print("SUMMARY")
    print("fixture                        r1      r2      lines1v2  cols     note")
    for rec in results:
        r1 = "ok" if rec["reader1"]["ok"] else "ERR"
        r2 = "ok" if rec["reader2"]["ok"] else "ERR"
        eq = "equal" if rec["lines_equal_1v2"] else "DIFF"
        cols = "equal" if rec["cols_equal"] else "DIFF"
        print(f"{rec['fixture']:<30} {r1:<6}  {r2:<6}  {eq:<9}  {cols:<8} {rec['note']}")


if __name__ == "__main__":
    main()
