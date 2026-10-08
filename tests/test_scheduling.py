import sqlite3
from contextlib import closing

from sideword.learning import REVIEW_INTERVALS, schedule_review
from sideword.storage import Store


def test_intervals_and_ceiling():
    for stage in range(10):
        schedule = schedule_review(stage, True, 100)
        assert schedule.stage == min(stage + 1, 6)
        assert schedule.due == 100 + REVIEW_INTERVALS[schedule.stage]
        assert schedule_review(stage, False, 100).due == 700


def test_old_database_migrates_without_losing_records(tmp_path):
    path = tmp_path / "progress.sqlite3"
    with closing(sqlite3.connect(path)) as db, db:
        db.execute(
            "CREATE TABLE learning (book TEXT, word TEXT, familiarity TEXT NOT NULL DEFAULT '', viewed REAL NOT NULL, PRIMARY KEY(book,word))"
        )
        db.execute("INSERT INTO learning VALUES ('sample','cancel','familiar',123)")
    store = Store(path)
    try:
        row = store.learned("sample")["cancel"]
        assert row["familiarity"] == "familiar"
        assert row["viewed"] == 123
        assert row["due"] is None
        assert row["stage"] == 0
    finally:
        store.db.close()
