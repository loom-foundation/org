# Loom Logo

**Color Palette: The Loom Spectrum**

The palette uses a "Cyber-Fantasy" aesthetic, combining the deep, dark tones of the night sky with the vibrant neon of digital creation.

| Color Name | HEX | RGB | CMYK |
| :---- | :---- | :---- | :---- |
| **Deep Space Navy** | \#0A1B3D | (10, 27, 61\) | 98, 85, 45, 52 |
| **Electric Cyan** | \#00E5FF | (0, 229, 255\) | 65, 0, 10, 0 |
| **Vibrant Magenta** | \#D600FF | (214, 0, 255\) | 35, 80, 0, 0 |
| **Mystic Purple** | \#8A2BE2 | (138, 43, 226\) | 70, 85, 0, 0 |

**Typography**

The L and the M are Montserrat Bold at 69 px in the marks' own coordinate system, giving a 48.3 px cap height. The infinity between them is a stroked path rather than a letter, so the mark needs two glyphs and no more.

Those two glyphs ship as a 2.4 KB subset, `fonts/loom-wordmark.woff2`, embedded in each SVG as a data URI. The marks therefore carry their own typeface: the letterforms are identical whether a file is opened directly, placed in an `img` tag, or inlined in a page, and they do not depend on Montserrat being installed. `fonts/README.md` covers the contract for sites that inline the mark and supply the face themselves.

The PNG exports carry the same letterforms as outlines, since the rasteriser resolves fonts through the system and would otherwise substitute one.

**Files**

| File | Use |
| :---- | :---- |
| `loom-wordmark.svg` | The wordmark, for light grounds. |
| `loom-wordmark-inverted.svg` | The wordmark, for dark grounds. |
| `loom-logo.svg` | The full mark, warp and weft in the circle, wordmark beneath. |
| `loom-logo-inverted.svg` | The full mark, for dark grounds. |
| `favicon.svg` | The infinity alone, on parchment, at 32 px. |

Each SVG has a PNG beside it at three times the viewBox, on a transparent ground, for contexts that cannot take vector.
