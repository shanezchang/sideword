"""Render the real learning view to a portable SVG, without playing audio.

Run from the repository root: uv run python scripts/render_preview.py
"""

from html import escape
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from sideword.storage import Store
from sideword.ui.app import Desk
from sideword.ui.text import width
from sideword.vocabulary import Library


class Canvas:
    def __init__(self):
        self.lines = []

    def getmaxyx(self):
        return 24, 80

    def erase(self):
        self.lines.clear()

    def addstr(self, y, x, text, attr=0):
        self.lines.append((y, x, text, attr))

    def refresh(self):
        pass

    def keypad(self, enabled):
        pass

    def timeout(self, milliseconds):
        pass


def main():
    canvas = Canvas()
    with TemporaryDirectory() as directory:
        store = Store(Path(directory) / "progress.sqlite3")
        try:
            library = Library()
            voice = SimpleNamespace(stop=lambda: None, available=False, status="")
            with (
                patch("sideword.ui.app.curses.has_colors", return_value=False),
                patch("sideword.ui.app.curses.curs_set"),
                patch("sideword.ui.app.curses.set_escdelay"),
                patch("sideword.ui.app.Speaker", return_value=voice),
            ):
                desk = Desk(canvas, store, "sample", library, quiet=True)
            desk.study_state = {"queue": list(library.load("sample")), "index": 1, "mode": "all"}
            desk.render()
        finally:
            store.db.close()
    elements = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 504" role="img" aria-label="Sideword learning view with five words">',
        '<rect width="800" height="504" rx="8" fill="#171b1a"/>',
        '<g font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="14">',
    ]
    for y, x, text, attr in canvas.lines:
        color = "#7db7ad" if attr else "#e4e8e5"
        # Explicit cell positions preserve alignment across CJK fallback fonts.
        column = x
        for character in text:
            elements.append(
                f'<text x="{20 + column * 9.3:g}" y="{24 + y * 19}" fill="{color}">{escape(character)}</text>'
            )
            column += width(character)
    elements.extend(["</g>", "</svg>"])
    Path("docs/assets/preview.svg").write_text("\n".join(elements) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
