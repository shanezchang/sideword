"""Headless integration tests exercise the real controller and renderer together."""

import curses
from unittest.mock import Mock

import pytest

from sideword.storage import Store
from sideword.ui.app import Desk
from sideword.vocabulary import Library


@pytest.fixture
def desk(tmp_path, monkeypatch):
    screen = Mock()
    screen.getmaxyx.return_value = (24, 80)
    voice = Mock(status="")
    monkeypatch.setattr("sideword.ui.app.Speaker", lambda _: voice)
    monkeypatch.setattr(curses, "has_colors", lambda: False)
    monkeypatch.setattr(curses, "curs_set", lambda _: None)
    monkeypatch.setattr(curses, "set_escdelay", lambda _: None)
    store = Store(tmp_path / "progress.sqlite3")
    app = Desk(screen, store, "sample", quiet=True)
    yield app
    store.db.close()


def drawn(desk):
    desk.s.addstr.reset_mock()
    desk.render()
    return "\n".join(call.args[2] for call in desk.s.addstr.call_args_list)


def test_startup_identity_and_quiet_mode(desk):
    assert "[/] sideword" in drawn(desk)
    assert not desk.autoplay
    desk.speaker.play.assert_not_called()
    desk.key("a")
    desk.speaker.play.assert_called_once()
    assert desk.store.setting("autoplay") == "1"
    desk.key("x")
    desk.speaker.stop.assert_called()


def test_navigation_details_settings_and_home(desk):
    desk.key("m")
    for key in "10\n":
        desk.key(key)
    desk.key(curses.KEY_DOWN)
    assert desk.study_state["index"] == 1
    desk.key("\n")
    assert desk.word_detail
    assert desk.study_word()["name"] in drawn(desk)
    desk.key(curses.KEY_DOWN)
    desk.key("t")
    desk.key("f")
    assert desk.store.progress("sample")[desk.study_word()["key"]]["starred"]
    desk.key("v")
    desk.key("-")
    assert desk.accent_name == "us" and desk.slow
    desk.key("\n")
    desk.key("?")
    assert "每页词数" in drawn(desk)
    desk.key("?")
    desk.key("p")
    assert "待复习总计" in drawn(desk)
    desk.key("\n")
    desk.key("\t")
    assert "看词学习" in drawn(desk)
    desk.key("7")
    assert desk.limit == 20
    desk.key("\x1b")
    assert not desk.running


def test_lookup_and_book_selection(desk, tmp_path):
    (tmp_path / "work.json").write_text('[{"name":"ship","trans":["交付"]}]')
    desk.library = Library(tmp_path)
    desk.books = desk.library.catalog
    desk.key("\t")
    desk.key("5")
    for key in "prepare":
        desk.key(key)
    assert "prepare" in drawn(desk)
    desk.key("\n")
    assert desk.study_word()["key"] == "prepare"
    desk.key("\t")
    desk.key("6")
    desk.key(curses.KEY_DOWN)
    assert "work" in drawn(desk)
    desk.key("\n")
    assert desk.book == "work"
    assert desk.study_word()["key"] == "ship"


def test_review_hides_meaning_then_advances(desk):
    word = desk.study_word()
    desk.store.rate_word("sample", word["key"], False, now=0)
    desk.key("r")
    assert "先回忆" in drawn(desk)
    desk.key("s")
    desk.speaker.play.assert_not_called()
    desk.key("\n")
    assert word["trans"][0] in drawn(desk)
    desk.key("2")
    assert "本轮到期词已复习完" in drawn(desk)
    desk.key("\t")
    desk.key("1")
    assert word["key"] not in desk.study_state["queue"]


@pytest.mark.parametrize("size", [(15, 42), (24, 80), (40, 120)])
def test_all_screens_fit_supported_terminal_sizes(desk, size):
    desk.s.getmaxyx.return_value = size
    desk.store.start("sample", desk.words)
    desk.state = desk.store.session("sample")
    for page in ("home", "learn", "books", "help", "browse", "schedule", "practice"):
        desk.page = page
        drawn(desk)
        for call in desk.s.addstr.call_args_list:
            y, x, _ = call.args[:3]
            assert 0 <= y < size[0]
            assert 0 <= x < size[1]


def test_tiny_terminal_can_still_quit(desk):
    desk.s.getmaxyx.return_value = (10, 30)
    assert "请把终端放大" in drawn(desk)
    desk.key("m")
    assert getattr(desk, "page_size_input", None) is None
    desk.key("\x1b")
    assert not desk.running
