from csvdiff.utils.files import get_unique_filename


def test_get_unique_filename_no_conflict(tmp_path):
    base_name = tmp_path / "output"
    unique_filename = get_unique_filename(str(base_name))
    assert unique_filename == base_name.with_suffix(".diff")
    assert not unique_filename.exists()


def test_get_unique_filename_with_conflict(tmp_path):
    base_name = tmp_path / "output"
    (base_name.with_suffix(".diff")).touch()  # Create a conflicting file
    unique_filename = get_unique_filename(str(base_name))
    assert unique_filename == tmp_path / "output (1).diff"
    assert not unique_filename.exists()


def test_get_unique_filename_multiple_conflicts(tmp_path):
    base_name = tmp_path / "output"
    (base_name.with_suffix(".diff")).touch()  # Create first conflicting file
    (tmp_path / "output (1).diff").touch()  # Create second conflicting file
    unique_filename = get_unique_filename(str(base_name))
    assert unique_filename == tmp_path / "output (2).diff"
    assert not unique_filename.exists()


def test_get_unique_filename_custom_extension(tmp_path):
    base_name = tmp_path / "output"
    (base_name.with_suffix(".log")).touch()  # Create a conflicting file with custom extension
    unique_filename = get_unique_filename(str(base_name), ".log")
    assert unique_filename == tmp_path / "output (1).log"
    assert not unique_filename.exists()
