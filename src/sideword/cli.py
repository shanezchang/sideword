"""Stable command entry point; diagnostic commands work without a TTY."""

import argparse
import curses
import json
import locale
import os
import sqlite3
import sys
from pathlib import Path

from sideword import __version__
from sideword.audio import Speaker
from sideword.config import data_directory, positive_int
from sideword.storage import Store
from sideword.ui.app import Desk
from sideword.vocabulary import Library


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        prog="sideword", description="Sideword — a quiet place for words."
    )
    result.add_argument("--version", action="version", version=f"sideword {__version__}")
    result.add_argument("--book", help="Book ID from --list-books")
    result.add_argument(
        "--page-size", type=positive_int, help="Words per page (any positive integer)"
    )
    result.add_argument(
        "--data-dir", type=Path, default=data_directory(), help="Local data directory"
    )
    result.add_argument("--quiet", action="store_true", help="Disable autoplay for this session")
    result.add_argument("--list-books", action="store_true", help="List available book IDs")
    result.add_argument(
        "--stats", action="store_true", help="Show spelling-test statistics as JSON"
    )
    result.add_argument("--check", action="store_true", help="Validate installed word books")
    result.add_argument(
        "--audio-check", action="store_true", help="Diagnose speech synthesis (plays audio)"
    )
    return result


def run(argv: list[str] | None = None) -> int:
    command = parser()
    args = command.parse_args(argv)
    library = Library(args.data_dir / "books")
    if args.check or args.list_books:
        for key, (label, _) in library.catalog.items():
            print(f"{key}\t{len(library.load(key))} words\t{label}")
        return 0
    if args.audio_check:
        okay, detail = Speaker(args.data_dir / "audio").check()
        print(detail)
        return 0 if okay else 1
    if args.book and args.book not in library.catalog:
        command.error(f"Unknown book: {args.book}. Use --list-books.")
    if not args.stats and (not sys.stdin.isatty() or not sys.stdout.isatty()):
        command.error("Run in an interactive terminal, or use --stats / --check.")
    if not args.stats and os.environ.get("TERM", "dumb") == "dumb":
        command.error(
            "A curses-compatible terminal is required (Terminal, iTerm, or a Linux terminal)."
        )
    store = Store(args.data_dir / "progress.sqlite3")
    try:
        preferred = "ielts" if "ielts" in library.catalog else "sample"
        store.apply_full_book_defaults(preferred)
        if args.page_size is not None:
            store.set_setting("page_size", args.page_size)
        book = args.book or store.setting("learning_book", preferred)
        if book not in library.catalog:
            book = preferred
        if args.stats:
            print(json.dumps(store.stats(book, library.load(book)), ensure_ascii=False, indent=2))
            return 0
        locale.setlocale(locale.LC_ALL, "")

        def launch(screen):
            desk = Desk(screen, store, book, library=library, quiet=args.quiet)
            desk.run()

        curses.wrapper(launch)
        return 0
    finally:
        store.db.close()


def main(argv: list[str] | None = None) -> int:
    try:
        return run(argv)
    except KeyboardInterrupt:
        return 130
    except (OSError, ValueError, sqlite3.Error, curses.error) as error:
        print(f"sideword: {error}", file=sys.stderr)
        return 1
