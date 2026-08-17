#!/usr/bin/env python3
"""Embed the wordmark web font into the brand SVGs as a data URI.

A browser refuses to fetch external resources for an SVG used as an image, so a
`src: url('fonts/…')` rule is inert in exactly the place the mark is most often
used: `<img src="loom-wordmark.svg">`. The letterforms fall back to whatever
bold grotesque the reader happens to have, which is how the mark drifted from
Montserrat without anyone touching a file.

A data URI is not an external resource, so it survives that restriction. At
roughly 2.6 KB of base64 the whole family is two glyphs, and the asset becomes
self-contained: identical letterforms in an img tag, an object tag, a direct
open, or inlined in a page.

Run after subset-wordmark-font.py. The rule is rewritten in place on every run,
so re-running after a font change is the whole update.

Usage:
    embed-wordmark-font.py [svg ...]

Defaults to the four marks in the parent directory. Requires no third-party packages.
"""

import base64
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent
WOFF2 = ASSETS / "fonts" / "loom-wordmark.woff2"

DEFAULT_SVGS = [
    "loom-wordmark.svg",
    "loom-wordmark-inverted.svg",
    "loom-logo.svg",
    "loom-logo-inverted.svg",
]

# The weight the subset was cut at, and the weight the mark is drawn in. The
# family holds this one face, so no browser is left to choose between cuts, and
# `font-synthesis` in the .logo-text rule stops any from faking another.
FACE_WEIGHT = 700

FACE_RE = re.compile(r"[ \t]*@font-face\s*\{.*?\}\n", re.DOTALL)


def face_rule(indent: str, data_uri: str) -> str:
    body = [
        "@font-face {",
        "  font-family: 'Loom Wordmark';",
        f"  src: url('{data_uri}') format('woff2');",
        f"  font-weight: {FACE_WEIGHT};",
        "  font-style: normal;",
        "}",
    ]
    return "".join(f"{indent}{line}\n" for line in body)


def embed(svg: Path, data_uri: str) -> bool:
    text = svg.read_text()
    match = FACE_RE.search(text)
    if not match:
        print(f"  {svg.name}: no @font-face rule found, skipped")
        return False

    indent = re.match(r"[ \t]*", match.group(0)).group(0)
    updated = text[: match.start()] + face_rule(indent, data_uri) + text[match.end() :]

    if updated == text:
        print(f"  {svg.name}: already current")
        return False

    svg.write_text(updated)
    print(f"  {svg.name}: font embedded ({len(updated) - len(text):+,} bytes)")
    return True


if __name__ == "__main__":
    if not WOFF2.is_file():
        sys.exit(f"error: {WOFF2} not found. Run subset-wordmark-font.py first.")

    data_uri = "data:font/woff2;base64," + base64.b64encode(WOFF2.read_bytes()).decode()

    args = sys.argv[1:]
    targets = [Path(a) for a in args] if args else [ASSETS / n for n in DEFAULT_SVGS]

    for svg in targets:
        if not svg.is_file():
            sys.exit(f"error: svg not found: {svg}")
        embed(svg, data_uri)
