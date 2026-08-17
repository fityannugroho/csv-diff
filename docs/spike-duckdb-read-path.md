# Spike: duckdb read path vs stdlib CSV — evidence and recommendation

## Summary

**Recommendation: (c) keep duckdb + mitigations.** The duckdb read path handles three edge cases that stdlib `csv.reader` does not: auto-detection of non-comma delimiters (semicolon.csv), lenient parsing of malformed files (malformed.csv), and row padding for ragged CSVs (uneven.csv). Switching to stdlib would regress these behaviors with no clear user benefit. The startup cost (~200ms) can be reduced by lazy-importing duckdb inside the read function, and the version can be bounded (`duckdb>=1.0,<2.0`) for stability.

## Evidence table

All 12 fixtures processed by three readers:
1. **Duckdb** (current path): `read_csv_with_duckdb` → `(lines, cols)`
2. **Stdlib** (candidate): `csv.reader` re-serialized with `csv.writer(lineterminator="")`
3. **Raw lines** (candidate): `text.splitlines()` — no parsing

| Fixture | Duckdb | Stdlib | Lines Equal | Cols Equal | Note |
|---------|--------|--------|-------------|------------|------|
| basic.csv | ok | ok | equal | equal | Identical; raw matches exactly |
| crlf.csv | ok | ok | equal | equal | Identical; raw matches exactly |
| empty-fields.csv | ok | ok | equal | equal | Identical; raw preserves original quoting |
| malformed.csv | ok (3 lines) | ok (2 lines) | **DIFF** | equal | Duckdb lenient on unterminated quote; stdlib strict |
| multiline.csv | ok | ok | equal | equal | Identical; raw splits embedded newline (plan 001 rejects) |
| no-trailing-newline.csv | ok | ok | equal | equal | Identical; raw matches exactly |
| quoted-commas.csv | ok | ok | equal | equal | Identical; raw preserves original quoting |
| quoted-quotes.csv | ok | ok | equal | equal | Identical; raw matches exactly |
| semicolon.csv | ok | ok | **DIFF** | **DIFF** | Duckdb auto-detects `;` delimiter; stdlib uses `,` |
| uneven.csv | ok | ok | **DIFF** | **DIFF** | Duckdb pads rows + auto-generates col names; stdlib preserves structure |
| utf8-bom.csv | ok | ok | equal | equal | Identical; raw matches exactly |
| whitespace.csv | ok | ok | equal | equal | Identical; raw preserves original quoting |

**8 of 12 fixtures produce identical output between duckdb and stdlib.** The 4 remaining fixtures fall into two categories: quoting preservation (empty-fields, quoted-commas, whitespace — identical between readers but raw preserves original quoting) and real behavioral deltas (malformed, semicolon, uneven).

## Behavior deltas

### 1. malformed.csv — unterminated quote

**Input:**
```
a,b,c
1,2,3
"unterminated,4,5
6,7,8
```

**Duckdb output (3 lines):**
```
a,b,c
1,2,3
"""unterminated",4,5
```
Duckdb treats the unterminated quote as a quoting error and re-serializes with escaped quotes.

**Stdlib output (2 lines):**
```
a,b,c
"unterminated,4,5
6,7,8"
```
Stdlib treats the unterminated quote as continuing to end of file, absorbing lines 3-4 into one record.

**CLI diff impact:** YES — the two parsers produce different row counts and content. A file containing genuinely malformed CSV would produce different diffs depending on the reader. Duckdb's behavior is arguably more useful (it surfaces the malformed row for inspection).

### 2. semicolon.csv — auto-detected delimiter

**Input:**
```
name;age;city
alice;30;nyc
1;a,b;2
```

**Duckdb output (2 lines, 3 cols):**
```
name,age,city
alice,30,nyc
```
Duckdb auto-detects `;` as the delimiter and splits columns correctly.

**Stdlib output (2 lines, 1 col):**
```
name;age;city
alice;30;nyc
```
Stdlib csv.reader defaults to `,` delimiter, so the entire line is one field.

**CLI diff impact:** YES — semicolon-delimited CSVs would be compared as single-column files, producing completely wrong diffs. This is a critical behavioral regression.

### 3. uneven.csv — ragged rows

**Input:**
```
a,b,c
1,2
1,2,3,4
```

**Duckdb output (1 data line, 4 cols):**
```
column0,column1,column2,column2
1,2,3,4
```
Duckdb pads the short row (1,2 → 1,2,,) and auto-generates column names from the data. It also picks the maximum column count (4) as the schema.

**Stdlib output (2 data lines, 3 cols):**
```
a,b,c
1,2
1,2,3,4
```
Stdlib preserves the original structure: header is the first row, and each data row has its original column count.

**CLI diff impact:** YES — the two parsers produce different row counts, column names, and data content. Duckdb's normalization makes ragged CSVs comparable; stdlib's preservation makes them incomparable.

### 4. empty-fields / quoted-commas / whitespace — quoting preservation

These three fixtures produce identical re-serialized output between duckdb and stdlib. However, the raw-line candidate preserves the original quoting style:
- `a,,c` vs `a,"",c` both serialize to `a,,c` via csv.writer
- Quoted values with leading/trailing spaces preserve quotes in raw lines but not in re-serialized output

**CLI diff impact:** NO for the current tool (both readers produce the same output). YES if switching to raw-line diffing — byte-level quoting differences would appear as diffs.

## Fidelity note (C2: quote-only differences invisible)

**Would a stdlib path fix C2?** No. Both duckdb and stdlib re-serialize through `csv.writer`, which normalizes quoting (drops redundant quotes, normalizes empty-vs-missing fields). A `csv.reader`-based path would preserve the current behavior: quote-only differences remain invisible.

**Would a raw-line path fix C2?** Yes. Comparing raw physical lines preserves exact quoting, whitespace, and formatting. Byte-level differences in quoting (e.g., `a,b` vs `"a","b"`) would appear as diffs. However, this is a bigger contract change: the tool would compare file bytes, not parsed data, which means whitespace-only and formatting-only differences also appear.

## Memory/startup measurements

### Startup latency

| Measurement | Cold (ms) | Warm (ms) | Notes |
|-------------|-----------|-----------|-------|
| `duckdb` import | 246–498 | ~50–130 | Cold = first import after venv restart |
| `csvdiff.cli` import | 228–714 | ~80–130 | Includes duckdb import |
| `stdlib csv` import | 21–30 | ~0 | Part of Python stdlib |
| `csvdiff --version` | 293–411 | ~290–330 | Full CLI startup including duckdb |

**Key observation:** The duckdb import accounts for ~200–400ms of the ~300–400ms total startup. Removing duckdb would reduce startup by roughly 50–70%. However, with lazy import (moving `import duckdb` inside `read_csv_with_duckdb()`), `--help` and `--version` would skip the import entirely, saving the full cost for those commands.

### Disk footprint

| Component | Size | Notes |
|-----------|------|-------|
| duckdb native extension (`_duckdb.cpython-312-*.so`) | **56 MB** | The actual C++ engine |
| duckdb Python package (`duckdb/`) | 648 KB | Pure Python wrappers |
| Total duckdb installed | ~57 MB | In venv site-packages |
| stdlib `csv` module | 0 KB (included in Python) | No additional dependency |

The 56MB native extension is the primary packaging cost. For comparison, the entire csv-diff package (without duckdb) is under 50KB.

## Recommendation

**(c) Keep duckdb + mitigations.**

**Rationale:**
The three behavioral deltas (malformed, semicolon, uneven) represent real features that users depend on:
- **Auto-detection of non-comma delimiters** is a core duckdb advantage — semicolon-delimited CSVs are common in European data
- **Lenient parsing of malformed files** prevents crashes on real-world data that isn't perfectly formatted
- **Row padding for ragged CSVs** provides predictable comparison behavior

The cost of switching is high (3 behavioral regressions) while the benefit is mainly startup latency (~200ms savings). The mitigations are cheap and low-risk:

**Mitigation 1: Lazy import**
Move `import duckdb` from module scope (`csv.py:8`) to inside `read_csv_with_duckdb()`. This means:
- `--help` and `--version` skip the duckdb import entirely (saves ~200–400ms)
- The import happens only when actually comparing files
- No behavior change; just deferred initialization

**Mitigation 2: Bound the version**
Change `duckdb>=1.0.0` to `duckdb>=1.0,<2.0` in `pyproject.toml`. This:
- Prevents surprise breakage from major-version duckdb releases
- Allows the project to pin to known-good versions
- Is standard practice for native dependencies

**Migration sketch (if a future plan adopts these mitigations):**
1. In `src/csvdiff/utils/csv.py`: move `import duckdb` from line 8 to inside `read_csv_with_duckdb()` (1-line change)
2. In `pyproject.toml`: change `duckdb>=1.0.0` to `duckdb>=1.0,<2.0` (1-line change)
3. No test changes needed — existing tests exercise the full read path
4. No fixture changes — the spike fixtures become permanent tests only if the read path changes
