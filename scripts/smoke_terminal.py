"""Exercise a real terminal executable and its saved learning state in isolation."""

import fcntl
import json
import os
import pty
import select
import sqlite3
import struct
import subprocess
import sys
import tempfile
import termios
import time
from contextlib import closing
from pathlib import Path


def saved_state(data: Path) -> tuple[dict, dict, list]:
    with closing(sqlite3.connect(data / "progress.sqlite3")) as db:
        state = json.loads(
            db.execute(
                "SELECT state FROM study_sessions WHERE book='sample' AND mode='all'"
            ).fetchone()[0]
        )
        settings = dict(db.execute("SELECT key,value FROM settings"))
        reviews = db.execute("SELECT word,remembered FROM review_log").fetchall()
    return state, settings, reviews


def session(executable: Path, home: Path, interact) -> bytes:
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 32, 110, 0, 0))
    env = {
        "HOME": str(home),
        "XDG_DATA_HOME": str(home / "data"),
        "XDG_CONFIG_HOME": str(home / "config"),
        "XDG_CACHE_HOME": str(home / "cache"),
        "TMPDIR": str(home),
        "TERM": "xterm-256color",
        "PATH": "/usr/bin:/bin",
        "LANG": "en_US.UTF-8",
    }
    process = subprocess.Popen(
        [str(executable), "--quiet", "--book", "sample"],
        stdin=slave,
        stdout=slave,
        stderr=slave,
        env=env,
        cwd=home,
    )
    os.close(slave)
    output = bytearray()

    def wait_for(predicate, timeout=15):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if select.select([master], [], [], 0.05)[0]:
                try:
                    output.extend(os.read(master, 65536))
                except OSError:
                    break
            if predicate(bytes(output)):
                return
            if process.poll() is not None:
                break
        if predicate(bytes(output)):
            return
        raise AssertionError(output.decode(errors="replace"))

    def send(keys):
        os.write(master, keys)

    try:
        wait_for(lambda text: b"Esc" in text)
        interact(send, wait_for, home / "data/sideword")
        send(b"\x1b")
        # Drain curses output while quitting; a full PTY buffer blocks get_wch.
        wait_for(lambda _: process.poll() is not None, timeout=8)
        assert process.wait(timeout=1) == 0, output.decode(errors="replace")
        return bytes(output)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        os.close(master)


def smoke(executable: Path) -> None:
    executable = executable.absolute()
    with tempfile.TemporaryDirectory(prefix="sideword-smoke-") as temp:
        home = Path(temp)
        data = home / "data/sideword"
        first_word = ""

        def study(send, wait_for, data):
            nonlocal first_word
            state, _, _ = saved_state(data)
            assert len(state["queue"]) == 30
            first_word = state["queue"][state["index"]]
            wait_for(lambda text: first_word.encode() in text)
            send(b"2")
            wait_for(lambda _: (first_word, 1) in saved_state(data)[2])
            send(b"m10\n")
            wait_for(lambda _: saved_state(data)[1].get("page_size") == "10")

        session(executable, home, study)
        before, settings, reviews = saved_state(data)
        assert first_word not in before["queue"] and len(before["queue"]) == 29
        assert (first_word, 1) in reviews
        assert settings["page_size"] == "10"

        def resume(send, wait_for, data):
            state, restored, rows = saved_state(data)
            assert state == before
            assert restored == settings and rows == reviews
            current = state["queue"][state["index"]]
            wait_for(lambda text: current.encode() in text)

        session(executable, home, resume)
        assert saved_state(data) == (before, settings, reviews)
        print("PTY: 30 sample words, self-rating, page size, saved order and resume: OK")


if __name__ == "__main__":
    smoke(Path(sys.argv[1]))
