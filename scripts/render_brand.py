"""Generate outlined brand assets from the OFL Manrope font.

Run after `npm ci --prefix site`:
uv run --with fonttools --with brotli python scripts/render_brand.py
"""

from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parents[1]
MARK = """<path fill="#14776b" d="M52 10H26C16 10 10 16 10 24c0 7 4 11 13 14l16 4c3 1 4 2 4 4s-2 3-5 3H14L7 59h31c12 0 19-6 19-15 0-8-5-12-15-15l-15-4c-3-1-4-2-4-3 0-2 2-3 5-3h17z"/><path fill="#75bda5" d="m45 19 7-9v10l-7 9zM7 59l7-10v-9L7 50z"/>"""


def main():
    font_path = (
        ROOT
        / "site/node_modules/@fontsource-variable/manrope/files/manrope-latin-wght-normal.woff2"
    )
    font = instantiateVariableFont(TTFont(font_path), {"wght": 750})
    glyphs, cmap = font.getGlyphSet(), font.getBestCmap()
    paths = []
    x = 0
    for letter in "sideword":
        glyph = glyphs[cmap[ord(letter)]]
        pen = SVGPathPen(glyphs)
        glyph.draw(pen)
        paths.append(f'<path transform="translate({x} 0)" d="{pen.getCommands()}"/>')
        x += glyph.width - 18
    scale = 51 / font["head"].unitsPerEm
    width = round(90 + x * scale + 8)
    mark = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 68 68" width="68" height="68" role="img" aria-label="Sideword">{MARK}</svg>\n'
    for directory in (ROOT / "docs/assets", ROOT / "site/public/assets"):
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "mark.svg").write_text(mark)
        for name, color in (("wordmark.svg", "#163630"), ("wordmark-dark.svg", "#e9f3ed")):
            svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} 80" width="{width}" height="80" role="img" aria-label="Sideword"><g transform="translate(0 5)">{MARK}</g><g fill="{color}" transform="translate(85 57) scale({scale} {-scale})">{"".join(paths)}</g></svg>\n'
            (directory / name).write_text(svg)
    print("Generated mark and outlined wordmarks for docs and website.")


if __name__ == "__main__":
    main()
