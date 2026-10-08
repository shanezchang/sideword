#!/usr/bin/env python3
"""A quiet keyboard-first IELTS study desk, using only Python's standard library."""

import argparse
import curses
import json
import locale
import os
import sqlite3
import sys
import time
from datetime import datetime, timedelta
import unicodedata
from pathlib import Path
from core import BOOKS, Store, load_book, normalize
from speech import Speaker


def positive_int(value):
    try:
        number = int(value)
    except (ValueError, TypeError):
        raise argparse.ArgumentTypeError("请输入大于 0 的整数") from None
    if number <= 0:
        raise argparse.ArgumentTypeError("请输入大于 0 的整数")
    return number


def width(text):
    return sum(
        0
        if unicodedata.combining(c)
        else 2
        if unicodedata.east_asian_width(c) in "WF"
        else 1
        for c in text
    )


def clip(text, columns):
    result = ""
    for c in str(text).replace("\n", " "):
        if unicodedata.category(c).startswith("C"):
            continue
        if width(result + c) > columns:
            break
        result += c
    return result


def wrap(text, columns):
    columns = max(1, columns)
    lines, line = [], ""
    for c in text:
        if c == "\n":
            lines.append(line.rstrip())
            line = ""
        elif width(line + c) > columns:
            split = line.rfind(" ")
            if split > 0 and c != " ":
                lines.append(line[:split].rstrip())
                line = line[split + 1 :] + c
            else:
                lines.append(line.rstrip())
                line = c.lstrip()
        else:
            line += c
    return lines + [line]


class Desk:
    def __init__(self, screen, store, book):
        self.s, self.store, self.book = screen, store, book
        self.words = load_book(book)
        self.page, self.selected, self.scroll = "home", 0, 0
        self.query, self.message = "", ""
        self.state = store.session(book)
        self.study_state = store.study(book, self.words)
        self.card_scroll = 0
        self.page_size = int(store.setting("page_size", "5"))
        self.word_detail = False
        self.accent_name = store.setting("accent", "uk")
        self.slow = store.setting("slow", "0") == "1"
        self.autoplay = store.setting("autoplay", "1") == "1"
        self.translation = store.setting("translation", "1") == "1"
        self.speaker = Speaker(
            Path(store.db.execute("PRAGMA database_list").fetchone()[2]).parent
            / "audio"
        )
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

    def learning_lines(self, word, columns):
        lines = []
        for label, key in [("英", "ukphone"), ("美", "usphone")]:
            phone = word.get(key, "").strip(" /[]")
            if phone:
                lines.extend(wrap(f"{label} /{phone}/", columns))
        if not lines:
            lines.append("音标暂缺")
        lines.append("")
        for meaning in word["trans"]:
            lines.extend(wrap(meaning, columns))
        example = word.get("example")
        lines.append("")
        if example:
            lines.extend(wrap(example["en"], columns))
            if self.translation:
                lines.extend(wrap(example["zh"], columns))
            lines.append("")
            lines.extend(wrap(example["phrase"], columns))
        else:
            lines.append("这词暂未配例句；可切换到 30 词样本体验")
        return lines

    def effective_page_size(self):
        if self.study_state["mode"] == "review" or getattr(self, "word_detail", False):
            return 1
        return getattr(self, "page_size", 1)

    def move_learning(self, index):
        if 0 <= index < len(self.study_state["queue"]):
            self.study_state["index"] = index
            self.message = ""
            self.present_word()

    def render_word_page(self, size):
        h, _ = self.s.getmaxyx()
        queue, selected = self.study_state["queue"], self.study_state["index"]
        start = selected // size * size
        capacity = max(1, (h - 9) // 3)
        end = min(start + size, len(queue))
        visible_start = max(start, min(selected - capacity + 1, end - capacity))
        learned, progress = (
            self.store.learned(self.book),
            self.store.progress(self.book),
        )
        for offset, key in enumerate(
            queue[visible_start : min(end, visible_start + capacity)]
        ):
            word = self.words[key]
            active = visible_start + offset == selected
            phone = word.get("ukphone") or word.get("usphone") or ""
            phone = f" /{phone.strip(' /[]')}/" if phone else ""
            star = " *" if progress.get(key, {}).get("starred") else ""
            status = {"familiar": " · 熟悉", "unfamiliar": " · 还不熟"}.get(
                learned.get(key, {}).get("familiarity"), ""
            )
            self.put(
                4 + offset * 3,
                ("› " if active else "  ") + word["name"] + phone + star,
                self.accent if active else 0,
            )
            self.put(5 + offset * 3, "  " + "；".join(word["trans"]) + status)
        accent = "英音" if self.accent_name == "uk" else "美音"
        playback = "自动" if self.autoplay else "手动"
        self.put(
            h - 5,
            f"{selected + 1}/{len(queue)}  每页 {size}  {accent} · {playback}  M 设置",
        )
        self.put(h - 4, "↑↓ 选词  ←→ 翻页  Enter 详情  空格 发音")
        self.footer("1 还不熟  2 记住了  F 收藏  ? 帮助")

    def render_learning(self):
        h, w = self.s.getmaxyx()
        word = self.study_word()
        if word is None:
            review = self.study_state["mode"] == "review"
            self.put(
                5,
                "本轮到期词已复习完"
                if review and self.study_state["queue"]
                else "暂时没有到期词"
                if review
                else "这些词都已记住；到期后仍会提醒复习"
                if self.study_state["mode"] == "all"
                else "还没有这些词",
                self.accent,
            )
            self.put(
                7,
                "记住的词仍会安排复习；P 查看计划"
                if review
                else "在学习卡片按 1 标记还不熟，F 收藏",
            )
            self.footer("Tab 首页   P 复习计划")
            return
        size = self.effective_page_size()
        if size > 1:
            self.render_word_page(size)
            return
        learned = self.store.learned(self.book).get(word["key"], {})
        familiarity = {"familiar": "熟悉", "unfamiliar": "还不熟"}.get(
            learned.get("familiarity"), ""
        )
        starred = self.store.progress(self.book).get(word["key"], {}).get("starred")
        self.put(4, word["name"] + ("  *" if starred else ""), self.accent)
        lines = self.learning_lines(word, w - 5)
        reviewing = self.study_state["mode"] == "review"
        if reviewing and not self.review_revealed:
            lines = [
                "先回忆这个词的意思。",
                "",
                "Enter 查看释义和例句",
                "空格可以听发音",
            ]
        visible = max(1, h - 12)
        self.card_scroll = min(self.card_scroll, max(0, len(lines) - visible))
        for i, line in enumerate(lines[self.card_scroll : self.card_scroll + visible]):
            self.put(6 + i, line)
        progress = f"{self.study_state['index'] + 1}/{len(self.study_state['queue'])}  {familiarity}"
        if len(lines) > visible:
            progress += "  ↑↓ 滚动全文"
        self.put(h - 6, progress)
        sound = ("英音" if self.accent_name == "uk" else "美音") + (
            " · 慢速" if self.slow else ""
        )
        sound += " · 自动播放" if self.autoplay else " · 手动播放"
        next_due = self.due_label(learned.get("due"))
        self.put(h - 5, "下次复习 " + next_due if next_due else sound)
        self.put(h - 4, "空格 读单词  S 读例句  ? 更多按键")
        self.footer(
            "Enter 揭晓   1 忘了   2 记得"
            if reviewing
            else "Enter 返回列表  ↑↓ 滚动全文"
            if getattr(self, "word_detail", False)
            else "←→ 翻词  1 不熟  2 记住  M 每页词数"
        )

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
                self.message = (
                    "每页词数: " + self.page_size_input + "  Enter 保存 / Esc 取消"
                )
            return
        if isinstance(key, str):
            key = key.lower()
        if key == "m":
            self.speaker.stop()
            self.page_size_input = ""
            self.message = f"每页词数（当前 {getattr(self, 'page_size', 1)}）: 输入数字，Enter 保存 / Esc 取消"
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
        if (
            not reviewing
            and getattr(self, "word_detail", False)
            and key in ("\n", "\r")
        ):
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
                    "已到最后一个词；可回首页复习还不熟的词"
                    if change > 0
                    else "这是第一个词"
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

    def render(self):
        self.s.erase()
        h, w = self.s.getmaxyx()
        if w < 42 or h < 15:
            self.put(1, "请把终端放大至 42 列 × 15 行", x=0)
            self.put(3, "Esc 保存退出", x=0)
            self.s.refresh()
            return
        self.put(1, "sideword", self.accent)
        due_count = len(self.store.due_words(self.book, self.words))
        self.put(
            2, BOOKS[self.book][0] + (f"  待复习 {due_count} · R" if due_count else "")
        )
        if self.page == "home":
            stats = self.store.stats(self.book, self.words)
            learned = self.store.learned(self.book)
            self.put(
                4,
                f"已浏览 {len(learned)} / {stats['total']}   还不熟 {sum(r['familiarity'] == 'unfamiliar' for r in learned.values())}",
            )
            choices = [
                "看词学习 / 继续",
                f"到期复习 · {due_count} 词",
                "收藏词卡片",
                "拼写测验（可选）",
                "查词 / 浏览",
                "切换词本",
                f"每组 {self.limit} 词",
            ]
            for i, label in enumerate(choices):
                self.put(
                    (5 if h < 18 else 6) + i,
                    f"{'›' if self.selected == i else ' '} {i + 1}  {label}",
                    self.accent if self.selected == i else 0,
                )
            self.footer("Enter 打开  P 计划  U 不熟的词")
        elif self.page == "books":
            for i, (key, (label, _)) in enumerate(BOOKS.items()):
                self.put(
                    5 + i * 2,
                    f"{i + 1}  {label}" + ("  当前" if key == self.book else ""),
                    self.accent if key == self.book else 0,
                )
            self.put(10, "各词本独立保存进度，可随时切换")
            self.footer("按对应数字选择词本")
        elif self.page == "browse":
            self.render_browse()
        elif self.page == "practice":
            self.render_practice()
        elif self.page == "learn":
            self.render_learning()
        elif self.page == "help":
            self.render_help()
        elif self.page == "schedule":
            self.render_schedule()
        if self.message:
            self.put(h - 3, self.message)
        if self.speaker.status:
            self.put(h - 3, self.speaker.status)
        self.s.refresh()

    def render_help(self):
        entries = [
            "空格 朗读单词    S 朗读英文例句",
            "V 切换英/美音   - 切换慢速",
            "A 自动播放开关  X 立即停止声音",
            "T 译文开关；单词页 ←→ 翻词 ↑↓ 滚动",
            "M 输入每页词数；多词页 ↑↓ 选词 ←→ 翻页",
            "多词页 Enter 查看/返回详情；操作仅作用于选中词",
            "1 还不熟  2 记住了  F 收藏",
            "R 到期复习  P 计划  U 不熟词",
        ]
        for i, text in enumerate(entries):
            self.put(4 + i, text)
        self.footer("? / Enter 返回词卡")

    def render_schedule(self):
        rows = self.store.learned(self.book)
        now = time.time()
        planned = [r["due"] for r in rows.values() if r.get("due") is not None]
        self.put(
            4,
            f"到期 {sum(d <= now for d in planned)}  待复习总计 {len(planned)}",
            self.accent,
        )
        today = datetime.now().date()
        for i in range(7):
            day = today + timedelta(days=i)
            count = sum(
                datetime.fromtimestamp(d).date() == day and d > now for d in planned
            )
            label = "今天稍后" if i == 0 else day.strftime("%m/%d")
            self.put(5 + i, f"{label}   {count} 词")
        self.footer("R 开始到期复习   Enter 返回")

    def matches(self):
        q = normalize(self.query)
        return [
            v
            for k, v in self.words.items()
            if not q or q in k or any(q in t for t in v["trans"])
        ]

    def render_browse(self):
        h, w = self.s.getmaxyx()
        self.put(4, "/ " + self.query, self.accent)
        items = self.matches()
        self.scroll = min(self.scroll, max(0, len(items) - 1))
        visible = max(1, h - 11)
        start = self.scroll // visible * visible
        rows = self.store.progress(self.book)
        for i, v in enumerate(items[start : start + visible]):
            mark = "*" if rows.get(v["key"], {}).get("starred") else " "
            self.put(
                6 + i,
                f"{mark} {v['name']}  {' / '.join(v['trans'])}",
                self.accent if start + i == self.scroll else 0,
            )
        if not items:
            self.put(6, "没有匹配项，试试中文释义或英文词干")
        self.put(h - 4, f"{len(items)} 个匹配   英文 / 中文搜索")
        self.footer("↑↓ 翻词   Enter 详情   ^F 收藏")

    def render_practice(self):
        h, w = self.s.getmaxyx()
        if not self.active():
            total = len(self.state["queue"])
            self.put(
                5, "这一组完成了" if total else "目前没有需要练习的词", self.accent
            )
            if total:
                self.put(7, f"独立拼对 {self.state['correct']} / {total}")
                self.put(9, "错词已安排复习；记住的词会逐步延长间隔")
            else:
                self.put(7, "回首页开始混合练习，或先在查词里收藏")
            self.footer("Enter 回首页")
            return
        word = self.current()
        self.put(
            4,
            f"{self.state['index'] + 1} / {len(self.state['queue'])}   写出英文",
            self.accent,
        )
        definitions = wrap("；".join(word["trans"]), w - 5)
        # Leave space for answer, correction and controls even in a tmux split.
        count = max(1, min(len(definitions), h - 13))
        for i, line in enumerate(definitions[:count]):
            self.put(
                6 + i,
                line + (" …" if i == count - 1 and len(definitions) > count else ""),
            )
        y = 7 + count
        if self.state["phase"] == "answer":
            self.put(y, "> " + self.state["typed"] + "▏", curses.A_BOLD)
            if self.state["assisted"]:
                self.put(y + 2, word["name"][0] + " _" * (len(word["name"]) - 1))
            self.footer("Enter 检查  ^H 提示  ^N 不会")
        else:
            good = self.state["feedback"] == "correct"
            self.put(y, ("正确  " if good else "答案  ") + word["name"], self.accent)
            phone = word.get("ukphone") or word.get("usphone") or ""
            self.put(y + 1, f"/{phone}/" if phone else "")
            if not good:
                self.put(y + 2, "> " + self.state["typed"] + "▏")
                self.footer("订正后 Enter   ^F 收藏")
            else:
                self.footer("Enter 下一个   ^F 收藏")

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
                else:
                    self.limit = {5: 10, 10: 20, 20: 5}.get(self.limit, 10)
                    self.store.set_setting("limit", self.limit)
        elif self.page == "books" and key in ("1", "2", "3"):
            if int(key) > len(BOOKS):
                return
            self.save()
            self.book = list(BOOKS)[int(key) - 1]
            self.store.set_setting("learning_book", self.book)
            self.words = load_book(self.book)
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
                    self.store.star(
                        self.book, items[min(self.scroll, len(items) - 1)]["key"]
                    )
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
            elif self.state["feedback"] == "correct" or normalize(
                self.state["typed"]
            ) == normalize(word["name"]):
                self.store.advance(self.book, self.state)
                self.message = ""
            else:
                self.message = "照着答案完整拼写一次，再继续"
        elif key in (curses.KEY_BACKSPACE, "\x7f"):
            self.state["typed"] = self.state["typed"][:-1]
        elif key == "\x15":
            self.state["typed"] = ""
        elif (
            isinstance(key, str)
            and key.isprintable()
            and len(self.state["typed"]) < 100
        ):
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


def main():
    parser = argparse.ArgumentParser(description="Sideword · 离线雅思词汇练习")
    parser.add_argument("--book", choices=BOOKS)
    parser.add_argument(
        "--page-size", type=positive_int, help="每页词数（任意正整数），保存为本地偏好"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share")))
        / "sideword",
    )
    parser.add_argument(
        "--stats", action="store_true", help="显示拼写测验统计，不打开界面"
    )
    parser.add_argument("--check", action="store_true", help="验证本地词库")
    parser.add_argument(
        "--audio-check", action="store_true", help="诊断系统合成和播放（会发声）"
    )
    args = parser.parse_args()
    if args.check:
        for book in BOOKS:
            print(f"{BOOKS[book][0]}: {len(load_book(book))} unique words")
        return
    if args.audio_check:
        okay, detail = Speaker(args.data_dir / "audio").check()
        print(detail)
        if not okay:
            raise SystemExit(1)
        return
    store = Store(args.data_dir / "progress.sqlite3")
    try:
        store.apply_full_book_defaults()
        if args.page_size is not None:
            store.set_setting("page_size", args.page_size)
        book = args.book or store.setting("learning_book", "ielts")
        if book not in BOOKS:
            book = "ielts" if "ielts" in BOOKS else "sample"
        if args.stats:
            print(
                json.dumps(
                    store.stats(book, load_book(book)), ensure_ascii=False, indent=2
                )
            )
            return
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            parser.error("请在交互式终端运行；统计可使用 --stats")
        if os.environ.get("TERM", "dumb") == "dumb":
            parser.error(
                "当前终端不支持交互界面；请用 Terminal / iTerm，或 TERM=xterm-256color sideword"
            )
        locale.setlocale(locale.LC_ALL, "")
        curses.wrapper(lambda screen: Desk(screen, store, book).run())
    finally:
        store.db.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except (OSError, ValueError, sqlite3.Error, curses.error) as error:
        print(f"无法启动 Sideword：{error}", file=sys.stderr)
        sys.exit(1)
