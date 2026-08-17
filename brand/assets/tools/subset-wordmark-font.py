#!/usr/bin/env python3
"""Build the wordmark web font: the two letterforms of the mark, and nothing else.

The Loom wordmark and logo set exactly two glyphs in Montserrat, an L and an M.
Shipping the whole family to render them costs 180 KB and leaves the letterforms
at the mercy of whatever the reader has installed. This produces a subset that
carries those two glyphs alone, small enough to inline in a stylesheet and exact
on every device.

The subset is renamed rather than shipped as "Montserrat": a face holding two
glyphs must never shadow the real family in a document that also sets prose in
it. The OFL copyright, licence, and licence URL travel with the file, as the
licence requires of a modified version.

A variable source is pinned to a single weight first, so the subset always holds
exactly one face and no browser is left to choose or to fake one.

Usage:
    subset-wordmark-font.py [source.ttf] [output.woff2] [--weight 700]

Defaults to ../fonts/montserrat.ttf and ../fonts/loom-wordmark.woff2,
resolved against this script. Requires fonttools with woff2 support:

    pip install "fonttools[woff]"
"""

import sys
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

# The wordmark's letterforms. The infinity between them is a path, not a glyph.
GLYPHS = "LM"

# The mark is drawn in Bold. A variable source is pinned here rather than left at
# its own default, which for Montserrat is Thin.
WEIGHT = 700

FAMILY = "Loom Wordmark"
POSTSCRIPT = "LoomWordmark-Regular"
DESCRIPTION = "Two-glyph subset of Montserrat (L, M) for the Loom wordmark."

HERE = Path(__file__).resolve().parent
FONTS = HERE.parent / "fonts"

# Name IDs the subset redefines. Everything the OFL requires to travel with a
# modified version (0 copyright, 13 licence, 14 licence URL) is left untouched.
NAME_OVERRIDES = {
    1: FAMILY,
    2: "Regular",
    4: FAMILY,
    6: POSTSCRIPT,
    10: DESCRIPTION,
    16: FAMILY,
    17: "Regular",
}


def build(source: Path, output: Path, weight: int | None) -> None:
    options = subset.Options()
    options.layout_features = []
    options.name_IDs = ["*"]
    options.name_legacy = True
    options.name_languages = ["*"]
    options.notdef_outline = True
    options.recalc_bounds = True
    options.flavor = "woff2"
    # The hinting program is four fifths of the file and exists to snap stems to
    # a pixel grid, which is the one thing a mark must not do differently from
    # one platform to the next. Dropped, so every rasteriser starts from the
    # same outlines.
    options.hinting = False

    # Without this the modification date is stamped afresh on every save, so an
    # unchanged font rebuilds to a different file and the marks it is embedded in
    # churn along with it.
    font = TTFont(source, recalcTimestamp=False)
    provenance = font["name"].getDebugName(3) or font["name"].getDebugName(4)

    if "fvar" in font:
        axes = {a.axisTag: a for a in font["fvar"].axes}
        if "wght" not in axes:
            sys.exit(f"error: {source.name} is variable but carries no wght axis")
        target = weight if weight is not None else WEIGHT
        axis = axes["wght"]
        if not axis.minValue <= target <= axis.maxValue:
            sys.exit(
                f"error: weight {target} is outside the source's wght axis "
                f"({int(axis.minValue)}–{int(axis.maxValue)})"
            )
        instancer.instantiateVariableFont(font, {"wght": target}, inplace=True, optimize=True)
    elif weight is not None and weight != font["OS/2"].usWeightClass:
        sys.exit(
            f"error: {source.name} is a static {font['OS/2'].usWeightClass} weight "
            f"and cannot be cut to {weight}. Supply a variable source, or the "
            f"static cut for that weight."
        )

    built_weight = font["OS/2"].usWeightClass

    subsetter = subset.Subsetter(options=options)
    subsetter.populate(text=GLYPHS)
    subsetter.subset(font)

    name = font["name"]
    overrides = dict(NAME_OVERRIDES)
    # The unique identifier keys font caches, so it must not collide with the
    # family it was cut from, while still recording which version it came from.
    overrides[3] = f"{POSTSCRIPT}; subset of {provenance}"
    for name_id, value in overrides.items():
        name.setName(value, name_id, 3, 1, 0x409)
        name.setName(value, name_id, 1, 0, 0)

    output.parent.mkdir(parents=True, exist_ok=True)
    font.save(output)
    font.close()

    print(f"  {source.name} -> {output.name}")
    print(f"  glyphs: {' '.join(GLYPHS)}")
    print(f"  weight: {built_weight} (declare this in the @font-face rule)")
    print(f"  size:   {output.stat().st_size:,} bytes from {source.stat().st_size:,}")


if __name__ == "__main__":
    args = sys.argv[1:]

    weight = None
    if "--weight" in args:
        i = args.index("--weight")
        try:
            weight = int(args[i + 1])
        except (IndexError, ValueError):
            sys.exit("error: --weight takes a number, e.g. --weight 700")
        del args[i : i + 2]

    if len(args) > 2:
        sys.exit(
            f"usage: {Path(sys.argv[0]).name} [source.ttf] [output.woff2] [--weight 700]"
        )

    source = Path(args[0]) if args else FONTS / "montserrat.ttf"
    output = Path(args[1]) if len(args) > 1 else FONTS / "loom-wordmark.woff2"

    if not source.is_file():
        sys.exit(f"error: source font not found: {source}")

    build(source, output, weight)
