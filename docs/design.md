# A quiet place for words

Sideword is a small reading surface inside a terminal, not a dashboard. It should
feel at home beside an editor: useful immediately, with very little ceremony.

## Identity

The web/documentation mark is a folded S: a turning page and a return to a word.
The lowercase wordmark uses Manrope 750 with tighter spacing, outlined into SVG
so it does not depend on fonts installed on a visitor's machine. Generate assets
with `scripts/render_brand.py`; Manrope's OFL notice accompanies the assets.
Website layout and tokens live in `site/DESIGN.md`.

The terminal keeps its compact ASCII `[/]` signature and the user's monospace face.
It appears in the first rendered header, not in a separate splash screen: no forced
delay or animation. Terminal rendering cannot display the website's vector logo.

Brand colors: ink `#163630`, paper `#ffffff`, teal `#14776b`; dark wordmarks
use text `#e9f3ed`. The application inherits
terminal foreground/background and its cyan ANSI accent instead of overriding a
user's theme. `NO_COLOR` leaves a readable monochrome interface.

## Layout

Left-aligned text, a two-column inset, one selection marker. Each list entry gets
a word/IPA line, a meaning line, and breathing room. Long definitions live in the
detail view. Selection, speech and self-assessment always refer to the same word.
The footer teaches only the actions available on the current screen.

Page size is a user preference, not a terminal-size calculation. A short terminal
scrolls the viewport inside the page. Review is deliberately single-word and hides
the answer until requested. Browsing never implies successful recall.

The documentation preview is generated from the actual renderer with original demo
data via `uv run python scripts/render_preview.py`; it is not an invented screen.
Visual acceptance remains a human judgment. Automated tests cover navigation,
clipping, small screens, command behavior and persistence.
