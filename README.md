# CSV Diff

CSV Diff is a CLI tool for comparing two CSV files and displaying the results in `git diff` style.

## 📦 Installation

### Using pip

You can install CSV Diff using pip with the following command:

```bash
pip install csv-diff-py
```

### From Source

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

## Limitations

- Only supports CSV files with a header row.
- Not suitable for huge CSV files with hundreds of thousands of rows (for 1 million rows, it takes around 50 seconds).
