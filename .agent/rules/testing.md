# Testing

## Test Organization
- `tests/`: Root test directory.
- `tests/test_cli.py`: Main test file for CLI functionality.
- Test files follow `test_*.py` naming convention.
- Test functions follow `test_*` naming convention.
- Test classes follow `Test*` naming convention.

## Best Practices
- Keep tests focused and isolated.
- Test from the exposed public API when possible.
- Use `tmp_path` fixture for temporary file operations.
- Use `CliRunner` from `typer.testing` for end-to-end CLI tests.
- Use `pytest.raises(typer.Exit)` to verify validation failures.
- Use `monkeypatch` fixture for mocking file system errors.
- Test both success paths and all error paths.

## Coverage
- Source coverage tracked in `src/` (configured in `pytest.ini`).
- All error paths should be tested.
