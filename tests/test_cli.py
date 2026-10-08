import json
import subprocess
import sys

import pytest

from sideword import __version__
from sideword.cli import main
from sideword.config import data_directory


def test_installed_module_entrypoint():
    result = subprocess.run(
        [sys.executable, "-m", "sideword", "--version"], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert result.stdout.strip() == f"sideword {__version__}"


@pytest.mark.parametrize("value", ["0", "-5", "1.5", "abc"])
def test_invalid_page_size_fails_before_creating_data(tmp_path, value):
    with pytest.raises(SystemExit) as error:
        main(["--page-size", value, "--data-dir", str(tmp_path), "--stats"])
    assert error.value.code == 2
    assert not list(tmp_path.iterdir())


def test_arbitrary_page_size_is_persisted(tmp_path, capsys):
    assert main(["--page-size", "10", "--data-dir", str(tmp_path), "--stats"]) == 0
    assert json.loads(capsys.readouterr().out)["total"] == 30
    from sideword.storage import Store

    store = Store(tmp_path / "progress.sqlite3")
    try:
        assert store.setting("page_size") == "10"
    finally:
        store.db.close()


def test_check_is_read_only(tmp_path, capsys):
    assert main(["--check", "--data-dir", str(tmp_path)]) == 0
    assert "30 words" in capsys.readouterr().out
    assert not list(tmp_path.iterdir())


def test_custom_book_cli(tmp_path, capsys):
    books = tmp_path / "books"
    books.mkdir()
    (books / "work.json").write_text('[{"name":"ship","trans":["交付"]}]')
    assert main(["--book", "work", "--stats", "--data-dir", str(tmp_path)]) == 0
    assert json.loads(capsys.readouterr().out)["total"] == 1


def test_xdg_directory(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    assert data_directory() == tmp_path / "sideword"


def test_noninteractive_launch_has_clear_error(tmp_path):
    with pytest.raises(SystemExit) as error:
        main(["--data-dir", str(tmp_path)])
    assert error.value.code == 2
    assert not list(tmp_path.iterdir())
