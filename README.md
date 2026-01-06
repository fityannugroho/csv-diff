# CSV Diff

[![PyPI](https://img.shields.io/pypi/v/csv-diff-py.svg)][pypi-package]
[![License](https://img.shields.io/github/license/fityannugroho/csv-diff)](https://github.com/fityannugroho/csv-diff/blob/main/LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/fityannugroho/csv-diff/test.yml?branch=main)](https://github.com/fityannugroho/csv-diff/actions/workflows/test.yml)

CSV Diff is a CLI tool for comparing two CSV files and displaying the results in `git diff` style.

For example, there are two CSV files, [`districts-2022.csv`](https://github.com/fityannugroho/csv-diff/blob/main/docs/examples/districts-2022.csv) and [`districts-2025.csv`](https://github.com/fityannugroho/csv-diff/blob/main/docs/examples/districts-2025.csv). With this tool, you can easily see the data differences between these two CSV files. The output will be saved as a `.diff` file, like this:

```diff
--- districts-2022.csv
+++ districts-2025.csv
@@ -7,9 +7,9 @@
 11.01.07,11.01,Sawang
 11.01.08,11.01,Tapaktuan
 11.01.09,11.01,Trumon
-11.01.10,11.01,Pasi Raja
-11.01.11,11.01,Labuhan Haji Timur
-11.01.12,11.01,Labuhan Haji Barat
+11.01.10,11.01,Pasie Raja
+11.01.11,11.01,Labuhanhaji Timur
+11.01.12,11.01,Labuhanhaji Barat
 11.01.13,11.01,Kluet Tengah
 11.01.14,11.01,Kluet Timur
 11.01.15,11.01,Bakongan Timur
@@ -141,7 +141,7 @@
 11.08.11,11.08,Syamtalira Bayu
 11.08.12,11.08,Tanah Luas
 11.08.13,11.08,Tanah Pasir
-11.08.14,11.08,T. Jambo Aye
+11.08.14,11.08,Tanah Jambo Aye
 11.08.15,11.08,Sawang
 11.08.16,11.08,Nisam
 11.08.17,11.08,Cot Girek
... (truncated)
```

> To see the full differences, please check the [`result.diff`](https://github.com/fityannugroho/csv-diff/blob/main/docs/examples/result.diff) file.

## Usage

```bash
csvdiff path/to/file1.csv path/to/file2.csv
```

> Use `--help` to see the available options.

## Installation

This package is available on [PyPI][pypi-package].
You can install it as a standalone CLI application using [`pipx`](https://pypa.github.io/pipx/) or [`uv`](https://docs.astral.sh/uv/guides/tools).

### Using `pipx`

```bash
pipx install csv-diff-py
csvdiff
```

### Using `uv`

```bash
uv tool install csv-diff-py
csvdiff
```

or without installing globally, you can use `uvx` to run it directly:
```bash
uvx --from csv-diff-py csvdiff
```

## Development Setup

### Prerequisites

- [`uv`](https://docs.astral.sh/uv/getting-started/installation) package manager
- Python 3.8 or higher

> Tip: You can use `uv` to install Python. See the [Python installation guide](https://docs.astral.sh/uv/guides/install-python) for more details.

### Steps

1. Clone this repository
    ```bash
    git clone https://github.com/fityannugroho/csv-diff.git
    cd csv-diff
    ```

1. Install dependencies
    ```bash
    uv sync --all-extras
    ```

1. Run the tool locally

    Via `uv`:
    ```bash
    uv run csvdiff
    ```

    Via virtual environment:
    ```bash
    source .venv/bin/activate
    csvdiff
    ```

1. Run tests
    ```bash
    uv run pytest
    ```

1. Run linter and formatter
    ```bash
    uv run ruff check
    uv run ruff format
    ```

## Limitations

- Only supports CSV files with a header row.

[pypi-package]: https://pypi.org/project/csv-diff-py
