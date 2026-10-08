"""Keyboard state machine and curses lifecycle."""

import argparse
import curses
import os
import time
from datetime import datetime

from sideword.audio import Speaker
from sideword.config import positive_int
from sideword.ui import views
from sideword.ui.text import clip
from sideword.vocabulary import Library, normalize


class Desk:
    def __init__(self, screen, store, book, library=None, quiet=False):
        self.s, self.store, self.book = screen, store, book
        self.library = library or Library()
        self.books = self.library.catalog
        self.words = self.library.load(book)
        self.page, self.selected, self.scroll = "home", 0, 0
        self.query, self.message = "", ""
        self.state = store.session(book)
        self.study_state = store.study(book, self.words)
        self.card_scroll = 0
        try:
            self.page_size = positive_int(store.setting("page_size", "5"))
        except argparse.ArgumentTypeError:
            self.page_size = 5
        self.book_cursor = 0
        self.word_detail = False
        self.accent_name = store.setting("accent", "uk")
        self.slow = store.setting("slow", "0") == "1"
        self.autoplay = not quiet and store.setting("autoplay", "1") == "1"
        self.translation = store.setting("translation", "1") == "1"
        self.speaker = Speaker(store.path.parent / "audio")
        self.limit = int(store.setting("limit", "10"))
        self.running = True
        self.mono = bool(os.environ.get("NO_COLOR"))
        self.accent = curses.A_BOLD
        if curses.has_colors() and not self.mono:
            curses.start_color()
            curses.use_default_colors()
            curses.init_pair(1, curses.COLOR_CYAN, -1)
            self.accent |= curses.color_pair(1)
        self.s.keypad(True)
        self.s.timeout(200)
        curses.set_escdelay(25)
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        self.open_study("review" if store.due_words(book, self.words) else "all")

    def put(self, y, text, attr=0, x=2):
        h, w = self.s.getmaxyx()
        if y < 0 or y >= h or x >= w - 1:
            return
        try:
            self.s.addstr(y, x, clip(text, w - x - 1), attr)
        except curses.error:
            pass

    def footer(self, text):
        self.put(self.s.getmaxyx()[0] - 2, text)
        self.put(self.s.getmaxyx()[0] - 1, "Tab 首页   Esc 保存退出")

    def active(self):
        return self.state and self.state["index"] < len(self.state["queue"])

    def current(self):
        return self.words[self.state["queue"][self.state["index"]]]

    def save(self):
        if self.state:
            self.store.save_session(self.book, self.state)
        if hasattr(self, "study_state"):
            self.store.save_study(self.book, self.study_state)

    def study_word(self):
        queue = self.study_state["queue"]
        if 0 <= self.study_state["index"] < len(queue):
            return self.words[queue[self.study_state["index"]]]
        return None

    def open_study(self, mode="all"):
        self.speaker.stop()
        self.word_detail = False
        self.study_state = self.store.study(self.book, self.words, mode)
        self.page = "learn"
        self.card_scroll = 0
        self.message = ""
        self.present_word()

    def present_word(self):
        self.card_scroll = 0
        self.review_revealed = False
        self.speaker.stop()
        word = self.study_word()
        if word:
            self.store.view_word(self.book, word["key"])
            if self.autoplay:
                self.speaker.play(word["name"], self.accent_name, self.slow)
        self.store.save_study(self.book, self.study_state)

    def due_label(self, due):
        if due is None:
            return ""
        seconds = due - time.time()
        if seconds <= 0:
            return "到期了"
        if seconds < 3600:
            return f"{max(1, int(seconds / 60))} 分钟后"
        return datetime.fromtimestamp(due).strftime("%m/%d %H:%M")

    def effective_page_size(self):
        if self.study_state["mode"] == "review" or getattr(self, "word_detail", False):
            return 1
        return getattr(self, "page_size", 1)

    def move_learning(self, index):
        if 0 <= index < len(self.study_state["queue"]):
            self.study_state["index"] = index
            self.message = ""
            self.present_word()

    def learning_key(self, key):
        if getattr(self, "page_size_input", None) is not None:
            if key in ("\x1b", "\t"):
                self.page_size_input = None
                self.message = "已取消"
            elif key in ("\n", "\r"):
                try:
                    value = positive_int(self.page_size_input)
                except argparse.ArgumentTypeError as error:
                    self.message = str(error) + "；重新输入，Enter 保存，Esc 取消"
                    self.page_size_input = ""
                    return
                self.page_size = value
                self.store.set_setting("page_size", value)
                self.word_detail = False
                self.page_size_input = None
                self.message = f"已保存：每页 {value} 词；↑↓ 滚动选词"
            else:
                if key in (curses.KEY_BACKSPACE, "\x7f", "\b"):
                    self.page_size_input = self.page_size_input[:-1]
                elif isinstance(key, str) and key in "0123456789" and len(key) == 1:
                    self.page_size_input += key
                self.message = "每页词数: " + self.page_size_input + "  Enter 保存 / Esc 取消"
            return
        if isinstance(key, str):
            key = key.lower()
        if key == "m":
            self.speaker.stop()
            self.page_size_input = ""
            self.message = (
                f"每页词数（当前 {getattr(self, 'page_size', 1)}）: 输入数字，Enter 保存 / Esc 取消"
            )
            return
        if key == "p":
            self.page = "schedule"
            return
        if key == "r":
            self.open_study("review")
            return
        if key == "u":
            self.open_study("unfamiliar")
            return
        word = self.study_word()
        if not word:
            return
        reviewing = self.study_state["mode"] == "review"
        if not reviewing and getattr(self, "word_detail", False) and key in ("\n", "\r"):
            self.word_detail = False
            self.card_scroll = 0
            return
        size = self.effective_page_size()
        if size > 1:
            index = self.study_state["index"]
            if key in ("\n", "\r"):
                self.word_detail = True
                self.card_scroll = 0
                return
            if key in (curses.KEY_DOWN, "j", curses.KEY_UP, "k"):
                self.move_learning(index + (-1 if key in (curses.KEY_UP, "k") else 1))
                return
            if key in (curses.KEY_LEFT, "h", curses.KEY_RIGHT, "l"):
                start = index // size * size
                target = start - size if key in (curses.KEY_LEFT, "h") else start + size
                if 0 <= target < len(self.study_state["queue"]):
                    self.move_learning(target)
                return
        if reviewing and key in ("\n", "\r"):
            self.review_revealed = True
            return
        if reviewing and key in ("1", "2") and not self.review_revealed:
            self.review_revealed = True
            self.message = "对照释义后，再按 1 忘了 / 2 记得"
            return
        if key in (curses.KEY_RIGHT, "l", "\n", "\r", curses.KEY_LEFT, "h"):
            change = -1 if key in (curses.KEY_LEFT, "h") else 1
            index = self.study_state["index"] + change
            if 0 <= index < len(self.study_state["queue"]):
                self.study_state["index"] = index
                self.message = ""
                self.present_word()
            else:
                self.message = (
                    "已到最后一个词；可回首页复习还不熟的词" if change > 0 else "这是第一个词"
                )
        elif key in (curses.KEY_DOWN, "j"):
            self.card_scroll += 1
        elif key in (curses.KEY_UP, "k"):
            self.card_scroll = max(0, self.card_scroll - 1)
        elif key in ("1", "2"):
            result = self.store.rate_word(self.book, word["key"], key == "2")
            self.message = "已安排复习：" + self.due_label(result["due"])
            if reviewing:
                self.study_state["index"] += 1
                self.present_word()
            elif key == "2" and self.study_state["mode"] in ("all", "unfamiliar"):
                self.study_state["queue"].pop(self.study_state["index"])
                self.study_state["index"] = min(
                    self.study_state["index"],
                    max(0, len(self.study_state["queue"]) - 1),
                )
                self.present_word()
        elif key in ("f", "\x06"):
            value = self.store.star(self.book, word["key"])
            self.message = "已收藏" if value else "已取消收藏"
        elif key in (" ", "s"):
            if key == "s" and reviewing and not self.review_revealed:
                self.message = "先按 Enter 揭晓，再听例句"
                return
            text = word["name"] if key == " " else (word.get("example") or {}).get("en")
            if text:
                self.speaker.play(text, self.accent_name, self.slow)
                self.message = ""
            else:
                self.message = "这个词暂未配例句"
        elif key == "x":
            self.speaker.stop()
        elif key == "v":
            self.speaker.stop()
            self.accent_name = "us" if self.accent_name == "uk" else "uk"
            self.store.set_setting("accent", self.accent_name)
        elif key == "-":
            self.slow = not self.slow
            self.store.set_setting("slow", int(self.slow))
        elif key == "a":
            self.autoplay = not self.autoplay
            self.store.set_setting("autoplay", int(self.autoplay))
            if self.autoplay:
                self.speaker.play(word["name"], self.accent_name, self.slow)
            else:
                self.speaker.stop()
        elif key == "t":
            self.translation = not self.translation
            self.store.set_setting("translation", int(self.translation))
        elif key == "?":
            self.page = "help"

    def start(self, mode):
        if self.active():
            self.page = "practice"
            self.message = "已继续未完成的一组；完成后可切换模式"
            return
        self.state = self.store.start(self.book, self.words, mode, self.limit)
        self.page = "practice"
        self.message = ""

    def matches(self):
        q = normalize(self.query)
        return [
            v for k, v in self.words.items() if not q or q in k or any(q in t for t in v["trans"])
        ]

    def key(self, key):
        if (
            self.page == "learn"
            and getattr(self, "page_size_input", None) is not None
            and key != "\x03"
        ):
            self.learning_key(key)
            return
        if key in ("\x1b", "\x03"):
            self.save()
            self.speaker.stop()
            self.running = False
            return
        if key == curses.KEY_RESIZE:
            return
        h, w = self.s.getmaxyx()
        if h < 15 or w < 42:
            return
        if key == "\t":
            self.save()
            self.speaker.stop()
            self.page = "home"
            self.message = ""
            return
        if self.page == "home":
            if key in ("p", "P"):
                self.page = "schedule"
            elif key in ("u", "U"):
                self.open_study("unfamiliar")
            elif key in ("r", "R"):
                self.open_study("review")
            elif key in ("j", curses.KEY_DOWN):
                self.selected = (self.selected + 1) % 7
            elif key in ("k", curses.KEY_UP):
                self.selected = (self.selected - 1) % 7
            elif key in ("\n", "\r") or isinstance(key, str) and key in "1234567":
                if key in "1234567":
                    self.selected = int(key) - 1
                if self.selected < 3:
                    self.open_study(["all", "review", "starred"][self.selected])
                elif self.selected == 3:
                    self.start("mix")
                elif self.selected == 4:
                    self.page = "browse"
                elif self.selected == 5:
                    self.page = "books"
                    self.book_cursor = list(self.books).index(self.book)
                else:
                    self.limit = {5: 10, 10: 20, 20: 5}.get(self.limit, 10)
                    self.store.set_setting("limit", self.limit)
        elif self.page == "books":
            if key in (curses.KEY_DOWN, "j"):
                self.book_cursor = min(self.book_cursor + 1, len(self.books) - 1)
            elif key in (curses.KEY_UP, "k"):
                self.book_cursor = max(0, self.book_cursor - 1)
            elif key in ("\n", "\r") or isinstance(key, str) and key in "123456789":
                index = int(key) - 1 if key in "123456789" else self.book_cursor
                if index >= len(self.books):
                    return
                book = list(self.books)[index]
                try:
                    words = self.library.load(book)
                except ValueError as error:
                    self.message = str(error)
                    return
                self.save()
                self.book, self.words = book, words
                self.store.set_setting("learning_book", self.book)
                self.state = self.store.session(self.book)
                self.open_study()
        elif self.page == "browse":
            if key in ("\n", "\r"):
                items = self.matches()
                if items:
                    self.study_state = {
                        "queue": [v["key"] for v in items],
                        "index": min(self.scroll, len(items) - 1),
                        "mode": "lookup",
                    }
                    self.page = "learn"
                    self.present_word()
            elif key == curses.KEY_DOWN:
                self.scroll += 1
            elif key == curses.KEY_UP:
                self.scroll = max(0, self.scroll - 1)
            elif key == "\x06":
                items = self.matches()
                if items:
                    self.store.star(self.book, items[min(self.scroll, len(items) - 1)]["key"])
            elif key in (curses.KEY_BACKSPACE, "\x7f", "\b"):
                self.query = self.query[:-1]
                self.scroll = 0
            elif isinstance(key, str) and key.isprintable() and len(self.query) < 100:
                self.query += key
                self.scroll = 0
        elif self.page == "practice":
            self.practice_key(key)
        elif self.page == "learn":
            self.learning_key(key)
        elif self.page == "help" and key in ("?", "\n", "\r"):
            self.page = "learn"
        elif self.page == "schedule":
            if key in ("r", "R"):
                self.open_study("review")
            elif key in ("\n", "\r"):
                self.page = "learn"

    def practice_key(self, key):
        if not self.active():
            if key in ("\n", "\r"):
                self.page = "home"
            return
        word = self.current()
        if key == "\x06":
            starred = self.store.star(self.book, word["key"])
            self.message = "已收藏" if starred else "已取消收藏"
        elif key == "\x08" and self.state["phase"] == "answer":
            self.state["assisted"] = True
        elif key == "\x0e" and self.state["phase"] == "answer":
            self.state["assisted"] = True
            self.store.grade(self.book, self.state, word, "")
            self.state["typed"] = ""
        elif key in ("\n", "\r"):
            if self.state["phase"] == "answer":
                if not self.state["typed"].strip():
                    return
                self.store.grade(self.book, self.state, word, self.state["typed"])
                if self.state["feedback"] != "correct":
                    self.state["typed"] = ""
            elif self.state["feedback"] == "correct" or normalize(self.state["typed"]) == normalize(
                word["name"]
            ):
                self.store.advance(self.book, self.state)
                self.message = ""
            else:
                self.message = "照着答案完整拼写一次，再继续"
        elif key in (curses.KEY_BACKSPACE, "\x7f"):
            self.state["typed"] = self.state["typed"][:-1]
        elif key == "\x15":
            self.state["typed"] = ""
        elif isinstance(key, str) and key.isprintable() and len(self.state["typed"]) < 100:
            self.state["typed"] += key
        self.save()

    def run(self):
        try:
            while self.running:
                self.render()
                try:
                    key = self.s.get_wch()
                except curses.error:
                    continue
                self.key(key)
        finally:
            self.speaker.stop()

    def render(self):
        views.render(self)

    def render_learning(self):
        views.render_learning(self)
