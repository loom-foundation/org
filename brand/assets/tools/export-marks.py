#!/usr/bin/env python3
"""Export the marks in the forms that cannot carry a font: outlined SVG, and PNG.

The marks embed their typeface, which covers every browser. Two consumers still
cannot use it. Design tools open an SVG without loading `@font-face` at all, so
Figma and Illustrator show a mark in whatever they substitute. rsvg-convert
resolves fonts through fontconfig and ignores the rule however the font is
supplied, external file or data URI alike, which is how PNGs of the mark came to
be set in a typeface the brand does not use.

Both are answered by the same conversion: the L and the M become paths, and the
mark stops needing a font at all. The outlines are read from the web font rather
than from the family it was cut from, so every surface traces the same curves.
The paths keep the `logo-text` class, so their fill still comes from the mark's
own stylesheet and light and inverted stay one rule apart.

A mark with no letterforms in it, the favicon, has nothing to outline and is
rasterised as it stands.

Run after subset-wordmark-font.py and embed-wordmark-font.py.

Usage:
    export-marks.py [svg ...]

Defaults to the four marks in the parent directory, writing each one's outlined
variant beside it and a PNG at three times the viewBox. Requires fonttools and
rsvg-convert (brew install librsvg).
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent
SOURCE = ASSETS / "fonts" / "loom-wordmark.woff2"

# One SVG user unit becomes 3 px, per the brand's raster convention.
ZOOM = 3

DEFAULT_SVGS = [
    "loom-wordmark.svg",
    "loom-wordmark-inverted.svg",
    "loom-logo.svg",
    "loom-logo-inverted.svg",
]

NOTE = (
    "  <!-- Letterforms as outlines, for tools that do not load @font-face.\n"
    "       Generated from the mark beside it; edit that one. -->\n"
)

TEXT_RE = re.compile(
    r'<text\s+x="(?P<x>[-\d.]+)"\s+y="(?P<y>[-\d.]+)"\s+'
    r'class="(?P<cls>[^"]+)"\s+text-anchor="(?P<anchor>[^"]+)">(?P<glyph>[^<]+)</text>'
)

# The size .logo-text sets. Read rather than assumed, so the outlines follow the
# stylesheet if it ever changes.
SIZE_RE = re.compile(r"\.logo-text\s*\{[^}]*font-size:\s*([\d.]+)px", re.DOTALL)

FACE_RE = re.compile(r"[ \t]*@font-face\s*\{.*?\}\n", re.DOTALL)

# Type properties in the stylesheet describe how to set the letters. Once they
# are paths there are no letters to set, and only the fill still applies.
TYPE_DECL_RE = re.compile(r"[ \t]*font-(?:family|weight|synthesis|size):[^;]*;\n")


def outline(font: TTFont, svg_text: str) -> str | None:
    if not TEXT_RE.search(svg_text):
        return None

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

    outlined = TEXT_RE.sub(replace, svg_text)
    outlined = TYPE_DECL_RE.sub("", FACE_RE.sub("", outlined))
    head, tag, tail = outlined.partition(">\n")
    return head + tag + NOTE + tail


def rasterise(svg: Path, png: Path) -> None:
    subprocess.run(
        ["rsvg-convert", "--zoom", str(ZOOM), str(svg), "-o", str(png)],
        check=True,
    )


def export(font: TTFont, svg: Path) -> None:
    outlined = outline(font, svg.read_text())

    source = svg
    if outlined is not None:
        source = svg.with_name(f"{svg.stem}-outlined.svg")
        if not source.is_file() or source.read_text() != outlined:
            source.write_text(outlined)
            print(f"  {svg.name} -> {source.name} ({len(outlined):,} bytes)")
        else:
            print(f"  {source.name}: already current")

    png = svg.with_suffix(".png")
    rasterise(source, png)
    print(f"  {source.name} -> {png.name} ({png.stat().st_size:,} bytes)")


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
        if svg.stem.endswith("-outlined"):
            sys.exit(f"error: {svg.name} is itself an export; pass the mark instead")
        export(font, svg)
