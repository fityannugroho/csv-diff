---
name: csv-diff
description: Compare two CSV files and generate a unified diff file showing line-by-line differences.
---

# CSV Diff

Compare two CSV files to identify changes, additions, or deletions between them. Generates unified diff output similar to `git diff`.

## When to use

Use this skill when you need to:
- Compare two versions of a CSV file to see what changed
- Track updates in datasets, configurations, or tabular data
- Generate a diff file for code review or documentation
- Verify data migrations or transformations

## Requirements

The `csv-diff-py` package must be installed in your environment. You can install it globally via `uv`:

```bash
uv tool install csv-diff-py
```

Alternatively, run it directly with `uvx` without installing:

```bash
uvx --from csv-diff-py csvdiff file1.csv file2.csv
```

## Quick start

Compare two CSV files:

```bash
csvdiff old.csv new.csv
```

This will generate a `result.diff` file showing the differences.

### View help

```bash
csvdiff --help
```

## Output

The tool generates a unified diff output similar to the following:

```diff
--- old.csv
+++ new.csv
@@ -2,3 +2,3 @@
 0,Alice,70000
-1,John,50000
+1,John,55000
 2,Jane,60000
```

The output shows:
- Lines prefixed with `-` were removed or changed
- Lines prefixed with `+` were added or changed
- Context lines (no prefix) show unchanged data for reference

## Notes

- CSV files must have a header row
- Output is saved to a `.diff` file (default: `result.diff`)
