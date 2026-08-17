#!/usr/bin/env python3
"""Rasterise the brand marks to PNG, with the letterforms as outlines.

rsvg-convert resolves fonts through fontconfig and ignores `@font-face` however
the font is supplied, external file or data URI alike. Handed a mark it renders
the L and M in whatever bold grotesque fontconfig offers, silently, and the PNG
comes out in a typeface the brand does not use.

So the text is converted to outlines before rasterising, and the outlines come
from the web font itself rather than from the family it was cut from: one file
feeds the browser and the raster exports, so the two cannot drift apart by a
rounding or a weight. The paths keep the `logo-text` class, so their fill still
comes from the mark's own stylesheet and light and inverted stay one rule apart.

Run after subset-wordmark-font.py.

Usage:
    render-marks.py [svg ...]

Defaults to the four marks in the parent directory, writing each alongside as .png
at three times the viewBox, matching the brand's other raster exports. Requires
fonttools and rsvg-convert (brew install librsvg).
"""

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent
SOURCE = ASSETS / "fonts" / "loom-wordmark.woff2"

# One SVG user unit becomes 3 px, per the design system's raster convention.
ZOOM = 3

DEFAULT_SVGS = [
    "loom-wordmark.svg",
    "loom-wordmark-inverted.svg",
    "loom-logo.svg",
    "loom-logo-inverted.svg",
]

TEXT_RE = re.compile(
    r'<text\s+x="(?P<x>[-\d.]+)"\s+y="(?P<y>[-\d.]+)"\s+'
    r'class="(?P<cls>[^"]+)"\s+text-anchor="(?P<anchor>[^"]+)">(?P<glyph>[^<]+)</text>'
)

# The size .logo-text sets. Read rather than assumed, so the outlines follow the
# stylesheet if it ever changes.
SIZE_RE = re.compile(r"\.logo-text\s*\{[^}]*font-size:\s*([\d.]+)px", re.DOTALL)


def outline(font: TTFont, svg_text: str) -> str:
    size_match = SIZE_RE.search(svg_text)
    if not size_match:
        sys.exit("error: no font-size found in the .logo-text rule")
    scale = float(size_match.group(1)) / font["head"].unitsPerEm

    glyph_set = font.getGlyphSet()
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]

    def replace(match: re.Match) -> str:
        glyph = match.group("glyph")
        if ord(glyph) not in cmap:
            sys.exit(
                f"error: the web font carries no '{glyph}'. Add it to GLYPHS in "
                f"subset-wordmark-font.py and rebuild."
            )
        name = cmap[ord(glyph)]
        pen = SVGPathPen(glyph_set)
        glyph_set[name].draw(pen)

        x = float(match.group("x"))
        if match.group("anchor") == "end":
            x -= hmtx[name][0] * scale

        # The y axis runs down in SVG and up in a font, so the glyph is flipped
        # about the baseline the text element sat on.
        return (
            f'<path class="{match.group("cls")}" '
            f'transform="translate({x:.4f} {match.group("y")}) '
            f'scale({scale:.6f} -{scale:.6f})" '
            f'd="{pen.getCommands()}"/>'
        )

    outlined, count = TEXT_RE.subn(replace, svg_text)
    if not count:
        sys.exit("error: no text elements found to outline")
    return outlined


def render(font: TTFont, svg: Path) -> None:
    outlined = outline(font, svg.read_text())

    with tempfile.TemporaryDirectory() as tmp:
        staged = Path(tmp) / svg.name
        staged.write_text(outlined)
        png = svg.with_suffix(".png")
        subprocess.run(
            ["rsvg-convert", "--zoom", str(ZOOM), str(staged), "-o", str(png)],
            check=True,
        )
        print(f"  {svg.name} -> {png.name} ({png.stat().st_size:,} bytes)")


if __name__ == "__main__":
    if not shutil.which("rsvg-convert"):
        sys.exit("error: rsvg-convert not found. Install with: brew install librsvg")
    if not SOURCE.is_file():
        sys.exit(f"error: {SOURCE} not found. Run subset-wordmark-font.py first.")

    args = sys.argv[1:]
    targets = [Path(a) for a in args] if args else [ASSETS / n for n in DEFAULT_SVGS]

    font = TTFont(SOURCE)
    for svg in targets:
        if not svg.is_file():
            sys.exit(f"error: svg not found: {svg}")
        render(font, svg)
