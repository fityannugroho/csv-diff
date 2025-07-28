# CSV Diff

CSV Diff is a CLI tool for comparing two CSV files and displaying the results in `git diff` style.

For example, there are two CSV files, [`districts-2022.csv`](./docs/examples/districts-2022.csv) and [`districts-2025.csv`](./docs/examples/districts-2025.csv). With this tool, you can easily see the data differences between these two CSV files. The output will be saved as a `.diff` file, like this:

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

> To see the full differences, please check the [`result.diff`](./docs/examples/result.diff) file.

## 📦 Installation

### Using pip

This package is available on [PyPI](https://pypi.org/project/csv-diff-py). You can install it easily using the following command:

```bash
pip install csv-diff-py
```

### From source code

1. Clone this repository:
    ```bash
    git clone https://github.com/fityannugroho/csv-diff.git
    cd csv-diff
    ```

2. Use virtual environment (optional but recommended):
    ```bash
    # Create a virtual environment named .venv
    python -m venv .venv
    ```

    Then, activate it:

    ```bash
    source .venv/bin/activate  # For Linux/Mac
    .venv\Scripts\activate  # For Windows
    ```

    > To disabled the virtual environment, use `deactivate`

3. Install dependencies:
    ```bash
    pip install -e .
    ```

## 🚀 Usage

```bash
csvdiff path/to/file1.csv path/to/file2.csv
```

> Use `--help` to see the available options.

## Limitations

- Only supports CSV files with a header row.
- Not suitable for huge CSV files with hundreds of thousands of rows (for 1 million rows, it takes around 50 seconds).
