# A quiet place for words

Sideword is a small reading surface inside a terminal, not a dashboard. It should
feel at home beside an editor: useful immediately, with very little ceremony.

## Identity

The `[/]` mark combines two page edges with a diagonal cursor. The SVG is three
strokes; the terminal equivalent is three ASCII characters. The lowercase name
uses the terminal's existing monospace face. The mark appears in the first rendered
header, not in a separate splash screen: no forced delay or animation.

Documentation colors: ink `#242827`, paper `#ffffff`, teal `#247d73`; dark variants
use text `#e4e8e5`, canvas `#171b1a` and accent `#7db7ad`. The application inherits
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
