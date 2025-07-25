# CSV Diff

**csv-diff** is a CLI tool for comparing two CSV files and displaying the results in `git diff` style.

## 📦 Installation

1. Clone this repository:
    ```bash
    git clone https://github.com/fityannugroho/csv-diff.git
    cd csv-diff
    ```

1. Create a virtual environment (optional but recommended):
    ```bash
    python -m venv .venv
    ```

    Then, activate it:

    ```bash
    source .venv/bin/activate  # For Linux/Mac
    .venv\Scripts\activate  # For Windows
    ```

    > To disabled the virtual environment, use `deactivate`

1. Install dependencies:
    ```bash
    pip install -e .
    ```

## 🚀 Usage

```bash
csvdiff path/to/file1.csv path/to/file2.csv
```
