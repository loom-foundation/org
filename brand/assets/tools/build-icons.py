#!/usr/bin/env python3
"""Build the raster icons the platforms insist on.

An SVG favicon is the sharp one and covers most of the field, but not all of it:
Safari reads it only from version 26, and older versions look for an .ico or
nothing at all. iOS never reads it. A home screen icon is PNG at 180 px, and a
site without one gets a screenshot of itself on the reader's home screen.

Both are cut from `favicon.svg`, so the icons follow the mark rather than being
drawn a second time. Each size is rendered from the vector rather than resampled
from a larger raster, which at 16 px is the difference between a legible mark
and a smudge.

The home screen icon loses the mark's corner radius. iOS masks the icon to its
own shape, and a rounded source inside that mask leaves the corners transparent,
which iOS fills with black.

Usage:
    build-icons.py

Requires Pillow and rsvg-convert (brew install librsvg).
"""

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent
SOURCE = ASSETS / "favicon.svg"

# The sizes Windows and older browsers ask an .ico for.
ICO_SIZES = [16, 32, 48]

# Apple's own recommendation, and the size every device downsamples from.
TOUCH_SIZE = 180

RADIUS_RE = re.compile(r'(<rect[^>]*?)\srx="[\d.]+"')


def rasterise(svg: Path, size: int, out: Path) -> Path:
    subprocess.run(
        ["rsvg-convert", "--width", str(size), "--height", str(size), str(svg), "-o", str(out)],
        check=True,
    )
    return out


def build(tmp: Path) -> None:
    source_text = SOURCE.read_text()

    layers = [
        Image.open(rasterise(SOURCE, size, tmp / f"icon-{size}.png")).convert("RGBA")
        for size in ICO_SIZES
    ]
    # The largest layer leads: Pillow drops any requested size bigger than the
    # image it is handed, and takes the rest from the ones supplied by name.
    ico = ASSETS / "favicon.ico"
    layers.sort(key=lambda layer: layer.size, reverse=True)
    layers[0].save(
        ico,
        format="ICO",
        sizes=[(size, size) for size in ICO_SIZES],
        append_images=layers[1:],
    )

    written = sorted(size for size, _ in Image.open(ico).ico.sizes())
    if written != sorted(ICO_SIZES):
        sys.exit(f"error: {ico.name} holds {written}, expected {sorted(ICO_SIZES)}")

    print(f"  favicon.svg -> {ico.name} ({', '.join(f'{s}px' for s in ICO_SIZES)}, "
          f"{ico.stat().st_size:,} bytes)")

    squared = tmp / "favicon-squared.svg"
    squared.write_text(RADIUS_RE.sub(r"\1", source_text))
    touch = ASSETS / "apple-touch-icon.png"
    rasterise(squared, TOUCH_SIZE, touch)
    print(f"  favicon.svg -> {touch.name} ({TOUCH_SIZE}px square, "
          f"{touch.stat().st_size:,} bytes)")

    if Image.open(touch).convert("RGBA").getchannel("A").getextrema()[0] != 255:
        sys.exit("error: the home screen icon has transparent pixels; iOS fills those black")


if __name__ == "__main__":
    if not shutil.which("rsvg-convert"):
        sys.exit("error: rsvg-convert not found. Install with: brew install librsvg")
    if not SOURCE.is_file():
        sys.exit(f"error: source not found: {SOURCE}")

    with tempfile.TemporaryDirectory() as tmp:
        build(Path(tmp))
