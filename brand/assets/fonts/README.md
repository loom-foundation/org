# Wordmark font

The Loom marks set exactly two letterforms, an L and an M, in Montserrat Bold. Everything in this directory exists so that those two shapes are the same on every screen and in every export, without depending on what the reader happens to have installed.

| File | What it is |
| :---- | :---- |
| `montserrat.ttf` | Montserrat 9.000, variable across a 100–900 weight axis. The source the marks are cut from. |
| `montserrat.license` | The SIL Open Font License 1.1 the family is released under. Travels with any copy. |
| `loom-wordmark.woff2` | Two glyphs at weight 700, 2.4 KB. The face the marks and the sites actually load. |

## Why a subset

A browser refuses to fetch external resources for an SVG used as an image, which is how the marks are used nearly everywhere. A `src: url('…')` rule is inert there, the letterforms fall back to whatever bold grotesque is at hand, and nothing reports a problem. A data URI is not an external resource, so the subset is embedded directly in each mark and the asset carries its own typeface.

That only works at a size worth embedding. The full family is 745 KB; the two glyphs the marks need are 2.4 KB, small enough to sit inside every SVG four times over and still be a rounding error on a page.

The subset drops the TrueType hinting program, which is four fifths of the file and exists to snap stems to a pixel grid differently on each platform. A mark should be the same shape everywhere, so the outlines are left unhinted.

## Why the family is renamed

The subset declares itself as `Loom Wordmark`, not as `Montserrat`. A face holding two glyphs must never shadow the real family on a page that also sets prose in it. The SIL Open Font License permits the renaming and requires the copyright notice, the license, and the license URL to travel with a modified version; the file carries all three in its name table, and `montserrat.license` sits beside it.

## Using it on a site

Sites that inline the mark supply the face themselves, so the letterforms take their colour from the page and the gradient can be driven by the project's own tokens:

```css
@font-face {
  font-family: 'Loom Wordmark';
  src: url('/fonts/loom-wordmark.woff2') format('woff2');
  font-weight: 700;
  font-style: normal;
  font-display: block;
}

.logo-text {
  font-family: 'Loom Wordmark', 'Montserrat', sans-serif;
  font-weight: 700;
  font-synthesis: none;
}
```

`font-synthesis: none` matters. The family holds one face, so every browser resolves to it, and the declaration stops any of them from thickening or slanting it to satisfy a request the family cannot meet.

## Rebuilding

The tools live in `../tools` and need `fonttools` with WOFF2 support, plus `rsvg-convert` for the raster step:

```bash
pip install "fonttools[woff]"
brew install librsvg
```

Run them in order. Each is idempotent, so a rebuild after any change to the source font is the three commands unchanged:

```bash
python3 ../tools/subset-wordmark-font.py
python3 ../tools/embed-wordmark-font.py
python3 ../tools/export-marks.py
```

The first cuts the subset, pinning the variable source to weight 700. The second writes it into the four marks as a data URI.

The third serves the two consumers that cannot load a font at all: design tools, which open an SVG without applying `@font-face`, and `rsvg-convert`, which resolves fonts through fontconfig and ignores the rule however the font is supplied. It converts the letterforms to paths, writes those as the `-outlined.svg` variants, and rasterises the variants to PNG. The outlines are read from the subset rather than from the source family, so every surface traces the same curves.

Changing the weight means changing `WEIGHT` in `subset-wordmark-font.py` and `FACE_WEIGHT` in `embed-wordmark-font.py` to match, then running all three.
