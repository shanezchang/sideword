"""Local data and transactional practice sessions. No network access."""

import json
import random
import sqlite3
import time
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BOOKS = {
    "sample": ("学习样本 · 30 词", "sample.json"),
    "ielts": ("雅思词库 · 3575", "IELTS_3_T.json"),
    "bible": ("雅思词汇真经 · 3630", "IELTSVocabularyBible.json"),
}
BOOKS = {
    key: value for key, value in BOOKS.items() if (ROOT / "data" / value[1]).is_file()
}


def normalize(text):
    return " ".join(
        unicodedata.normalize("NFKC", text).casefold().replace("’", "'").split()
    )


def load_book(book):
    rows = json.loads((ROOT / "data" / BOOKS[book][1]).read_text())
    examples = json.loads((ROOT / "data" / "examples.json").read_text())
    result = {}
    for row in rows:
        word = row["name"].strip()
        if not word or not isinstance(row["trans"], list) or not row["trans"]:
            raise ValueError("词库包含缺失的单词或释义")
        key = normalize(word)
        if key not in result:
            result[key] = dict(row, name=word, key=key)
        else:
            result[key]["trans"] = list(
                dict.fromkeys(result[key]["trans"] + row["trans"])
            )
    for key, word in result.items():
        word["example"] = examples.get(key)
    if book == "sample":
        return {key: result[key] for key in examples if key in result}
    return result


class Store:
    def __init__(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS progress (
            book TEXT, word TEXT, level INTEGER NOT NULL DEFAULT 0,
            due REAL NOT NULL DEFAULT 0, attempts INTEGER NOT NULL DEFAULT 0,
            errors INTEGER NOT NULL DEFAULT 0, starred INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(book, word));
        CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE IF NOT EXISTS sessions (book TEXT PRIMARY KEY, state TEXT);
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY, book TEXT, word TEXT, correct INTEGER,
            assisted INTEGER, at REAL);
        CREATE TABLE IF NOT EXISTS learning (
            book TEXT, word TEXT, familiarity TEXT NOT NULL DEFAULT '',
            viewed REAL NOT NULL, PRIMARY KEY(book, word));
        CREATE TABLE IF NOT EXISTS study_sessions (book TEXT, mode TEXT, state TEXT,
            PRIMARY KEY(book, mode));
        CREATE TABLE IF NOT EXISTS review_log (id INTEGER PRIMARY KEY, book TEXT,
            word TEXT, remembered INTEGER, at REAL, next_due REAL);
        """)
        columns = {r[1] for r in self.db.execute("PRAGMA table_info(learning)")}
        with self.db:
            for name, definition in [
                ("due", "REAL"),
                ("stage", "INTEGER NOT NULL DEFAULT 0"),
                ("last_review", "REAL"),
                ("lapses", "INTEGER NOT NULL DEFAULT 0"),
            ]:
                if name not in columns:
                    self.db.execute(
                        f"ALTER TABLE learning ADD COLUMN {name} {definition}"
                    )

    def setting(self, key, default=None):
        row = self.db.execute(
            "SELECT value FROM settings WHERE key=?", (key,)
        ).fetchone()
        return row[0] if row else default

    def learned(self, book):
        return {
            r["word"]: dict(r)
            for r in self.db.execute("SELECT * FROM learning WHERE book=?", (book,))
        }

    def view_word(self, book, word, familiarity=None):
        with self.db:
            self.db.execute(
                "INSERT OR IGNORE INTO learning(book,word,viewed) VALUES (?,?,?)",
                (book, word, time.time()),
            )
            if familiarity is not None:
                self.db.execute(
                    "UPDATE learning SET familiarity=? WHERE book=? AND word=?",
                    (familiarity, book, word),
                )

    def due_words(self, book, words, now=None):
        now = time.time() if now is None else now
        return [
            r[0]
            for r in self.db.execute(
                "SELECT word FROM learning WHERE book=? AND due IS NOT NULL AND due<=? ORDER BY due",
                (book, now),
            )
            if r[0] in words
        ]

    def rate_word(self, book, word, remembered, now=None):
        """Simple scheduling, not a fitted forgetting curve or an exam score."""
        now = time.time() if now is None else now
        with self.db:
            self.db.execute(
                "INSERT OR IGNORE INTO learning(book,word,viewed) VALUES (?,?,?)",
                (book, word, now),
            )
            row = self.db.execute(
                "SELECT * FROM learning WHERE book=? AND word=?", (book, word)
            ).fetchone()
            # Repeated clicks or revisiting tomorrow's card do not inflate intervals.
            if remembered and row["due"] is not None and row["due"] > now:
                return dict(row)
            if (
                not remembered
                and row["stage"] == 0
                and row["last_review"] is not None
                and now - row["last_review"] < 30
            ):
                return dict(row)
            stage = min(row["stage"] + 1, 6) if remembered else 0
            seconds = [600, 86400, 259200, 604800, 1209600, 2592000, 5184000][stage]
            due = now + seconds
            self.db.execute(
                "UPDATE learning SET familiarity=?,due=?,stage=?,last_review=?,lapses=lapses+? WHERE book=? AND word=?",
                (
                    "familiar" if remembered else "unfamiliar",
                    due,
                    stage,
                    now,
                    int(not remembered),
                    book,
                    word,
                ),
            )
            self.db.execute(
                "INSERT INTO review_log(book,word,remembered,at,next_due) VALUES (?,?,?,?,?)",
                (book, word, int(remembered), now, due),
            )
        return self.learned(book)[word]

    def study(self, book, words, mode="all", now=None):
        learned = self.learned(book)
        row = self.db.execute(
            "SELECT state FROM study_sessions WHERE book=? AND mode=?", (book, mode)
        ).fetchone()
        if mode == "all" and row:
            state = json.loads(row[0])
            if state["queue"] and all(w in words for w in state["queue"]):
                if state.get("order") != "random-v1":
                    # Keep the current card and browsing history; shuffle only ahead.
                    split = min(state["index"] + 1, len(state["queue"]))
                    remaining = state["queue"][split:]
                    random.shuffle(remaining)
                    state["queue"] = state["queue"][:split] + remaining
                    state["order"] = "random-v1"
                    self.save_study(book, state)
                current = state["queue"][min(state["index"], len(state["queue"]) - 1)]
                eligible = {
                    w
                    for w in words
                    if learned.get(w, {}).get("familiarity") != "familiar"
                }
                queue = [w for w in state["queue"] if w in eligible]
                missing = list(eligible - set(queue))
                if missing:
                    random.shuffle(missing)
                queue.extend(missing)
                state["queue"] = queue
                state["index"] = (
                    queue.index(current)
                    if current in queue
                    else min(state["index"], max(0, len(queue) - 1))
                )
                self.save_study(book, state)
                return state
        learned = self.learned(book)
        progress = self.progress(book)
        queue = list(words)
        if mode == "all":
            queue = [
                w for w in queue if learned.get(w, {}).get("familiarity") != "familiar"
            ]
            random.shuffle(queue)
        if mode == "unfamiliar":
            queue = [
                w
                for w in queue
                if learned.get(w, {}).get("familiarity") == "unfamiliar"
            ]
        elif mode == "starred":
            queue = [w for w in queue if progress.get(w, {}).get("starred")]
        elif mode == "review":
            queue = self.due_words(book, words, now)
        state = {"queue": queue, "index": 0, "mode": mode}
        if mode == "all":
            state["order"] = "random-v1"
        self.save_study(book, state)
        return state

    def apply_full_book_defaults(self):
        """One-time upgrade requested by the user; subsequent choices stay saved."""
        if self.setting("full_book_defaults_v1"):
            return
        with self.db:
            self.db.executemany(
                "INSERT OR REPLACE INTO settings VALUES (?,?)",
                [
                    ("learning_book", "ielts" if "ielts" in BOOKS else "sample"),
                    ("accent", "uk"),
                    ("autoplay", "1"),
                    ("full_book_defaults_v1", "1"),
                ],
            )

    def save_study(self, book, state):
        with self.db:
            self.db.execute(
                "INSERT OR REPLACE INTO study_sessions VALUES (?,?,?)",
                (book, state["mode"], json.dumps(state)),
            )

    def set_setting(self, key, value):
        with self.db:
            self.db.execute(
                "INSERT OR REPLACE INTO settings VALUES (?,?)", (key, str(value))
            )

    def progress(self, book):
        return {
            r["word"]: dict(r)
            for r in self.db.execute("SELECT * FROM progress WHERE book=?", (book,))
        }

    def stats(self, book, words, now=None):
        now = time.time() if now is None else now
        rows = self.progress(book)
        seen = [rows[w] for w in words if w in rows and rows[w]["attempts"]]
        return dict(
            total=len(words),
            seen=len(seen),
            new=len(words) - len(seen),
            due=sum(r["due"] <= now for r in seen),
            stable=sum(r["level"] >= 3 for r in seen),
            errors=sum(r["errors"] > 0 for r in seen),
            starred=sum(r["starred"] for w, r in rows.items() if w in words),
        )

    def session(self, book):
        row = self.db.execute(
            "SELECT state FROM sessions WHERE book=?", (book,)
        ).fetchone()
        return json.loads(row[0]) if row else None

    def save_session(self, book, state):
        with self.db:
            self._save(book, state)

    def _save(self, book, state):
        self.db.execute(
            "INSERT OR REPLACE INTO sessions VALUES (?,?)", (book, json.dumps(state))
        )

    def start(self, book, words, mode="mix", limit=10, now=None):
        now = time.time() if now is None else now
        rows = self.progress(book)
        due = [
            w
            for w in words
            if w in rows and rows[w]["attempts"] and rows[w]["due"] <= now
        ]
        due.sort(key=lambda w: rows[w]["due"])
        new = [w for w in words if w not in rows or not rows[w]["attempts"]]
        random.shuffle(new)
        if mode == "errors":
            queue = [w for w in words if w in rows and rows[w]["errors"] > 0]
            queue.sort(key=lambda w: (rows[w]["due"], -rows[w]["errors"]))
        elif mode == "starred":
            queue = [w for w in words if w in rows and rows[w]["starred"]]
            random.shuffle(queue)
        elif mode == "review":
            queue = due
        else:
            queue = due + new
        state = dict(
            queue=queue[:limit],
            index=0,
            correct=0,
            mode=mode,
            typed="",
            assisted=False,
            phase="answer",
            feedback="",
            graded=False,
        )
        self.save_session(book, state)
        return state

    def grade(self, book, state, word, typed, now=None):
        if state["graded"]:
            return
        now = time.time() if now is None else now
        exact = normalize(typed) == normalize(word["name"])
        success = exact and not state["assisted"]
        with self.db:
            self.db.execute(
                "INSERT OR IGNORE INTO progress(book,word) VALUES (?,?)",
                (book, word["key"]),
            )
            row = self.db.execute(
                "SELECT * FROM progress WHERE book=? AND word=?", (book, word["key"])
            ).fetchone()
            level = min(row["level"] + 1, 6) if success else 0
            interval = [600, 86400, 259200, 604800, 1209600, 2592000, 5184000][level]
            self.db.execute(
                "UPDATE progress SET level=?,due=?,attempts=attempts+1,errors=errors+? WHERE book=? AND word=?",
                (level, now + interval, int(not success), book, word["key"]),
            )
            self.db.execute(
                "INSERT INTO answers(book,word,correct,assisted,at) VALUES (?,?,?,?,?)",
                (book, word["key"], int(success), int(state["assisted"]), now),
            )
            state.update(
                graded=True,
                typed=typed,
                phase="feedback",
                feedback="correct" if success else "retry",
            )
            state["correct"] += int(success)
            self._save(book, state)

    def advance(self, book, state):
        state.update(
            index=state["index"] + 1,
            typed="",
            assisted=False,
            phase="answer",
            feedback="",
            graded=False,
        )
        self.save_session(book, state)

    def star(self, book, word):
        with self.db:
            self.db.execute(
                "INSERT OR IGNORE INTO progress(book,word) VALUES (?,?)", (book, word)
            )
            self.db.execute(
                "UPDATE progress SET starred=1-starred WHERE book=? AND word=?",
                (book, word),
            )
        return self.progress(book)[word]["starred"]
