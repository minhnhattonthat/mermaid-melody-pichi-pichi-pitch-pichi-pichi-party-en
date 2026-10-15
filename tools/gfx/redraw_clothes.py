"""Dress-up (きせかえ) graphics -> English (gfx/en/*.png). Rerun to regenerate all of them.
    python -X utf8 tools/gfx/redraw_clothes.py
Files: /mode/clothes/cls_obj.dcg (OBJ, 2D mapping, export --tw 32), /mode/clothes/cls_name.dcg (3 name tags 32x8,
copied at runtime over the cls_obj name slots). Report: docs/re/gfx_clothes.md.
"""
import os, sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import redraw  # noqa: E402
import pixfont  # noqa: E402

# 6-row pixel font for the small outlined labels (caps 6 rows, x-height 4)
_F6 = {
    'L': ["#..", "#..", "#..", "#..", "#..", "###"],
    'H': ["#..#", "#..#", "####", "#..#", "#..#", "#..#"],
    'R': ["###.", "#..#", "#..#", "###.", "#.#.", "#..#"],
    'I': ["###", ".#.", ".#.", ".#.", ".#.", "###"],
    'u': ["....", "....", "#..#", "#..#", "#..#", ".###"],
    'c': ["...", "...", ".##", "#..", "#..", ".##"],
    'i': ["#", ".", "#", "#", "#", "#"],
    'a': ["....", "....", ".###", "#..#", "#..#", ".###"],
    'n': ["....", "....", "###.", "#..#", "#..#", "#..#"],
    'o': ["....", "....", ".##.", "#..#", "#..#", ".##."],
    'd': ["...#", "...#", ".###", "#..#", "#..#", ".###"],
    'e': ["....", "....", ".##.", "####", "#...", ".###"],
    'f': [".##", "#..", "##.", "#..", "#..", "#.."],
}


def f6(text):
    cols = []
    for i, ch in enumerate(text):
        if ch == " ":
            cols.append(np.zeros((6, 3), np.uint8)); continue
        cols.append(np.array([[c == "#" for c in r] for r in _F6[ch]], np.uint8))
        if i + 1 < len(text) and text[i + 1] != " ":
            cols.append(np.zeros((6, 1), np.uint8))
    return np.concatenate(cols, axis=1)


def put(a, x, y, m, v):
    ys, xs = np.nonzero(m)
    a[ys + y, xs + x] = v


def label(a, x0, y0, w, text, ink, outline, shade):
    """Outlined 6-row label centred in an 8-row band [x0, x0+w): bottom glyph row in the shade colour."""
    a[y0:y0 + 8, x0:x0 + w] = 0
    m = f6(text)
    x = x0 + (w - m.shape[1]) // 2
    put(a, x - 1, y0, pixfont.dilate(m, 1, diag=True), outline)
    put(a, x, y0 + 1, m, ink)
    bot = m.copy(); bot[:-1] = 0
    put(a, x, y0 + 1, bot, shade)


def ttf_mask(text, font, size):
    f = ImageFont.truetype(redraw.FONTS + font, size, layout_engine=ImageFont.Layout.BASIC)
    im = Image.new("L", (int(f.getlength(text)) + 8, size * 2), 0)
    ImageDraw.Draw(im).text((2, 2), text, font=f, fill=255)
    m = (np.array(im) >= 128).astype(np.uint8)
    ys, xs = np.nonzero(m)
    return m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


# 5x12 two-pixel-stroke capitals for the ribbon title
_BIG = {
    'D': ["####.", "#####", "##.##", "##.##", "##.##", "##.##", "##.##", "##.##", "##.##", "##.##", "#####", "####."],
    'R': ["####.", "#####", "##.##", "##.##", "##.##", "#####", "####.", "##.##", "##.##", "##.##", "##.##", "##.##"],
    'E': ["#####", "#####", "##...", "##...", "##...", "####.", "####.", "##...", "##...", "##...", "#####", "#####"],
    'S': [".####", "#####", "##...", "##...", "###..", ".###.", "..###", "...##", "...##", "...##", "#####", "####."],
    'U': ["##.##"] * 10 + ["#####", ".###."],
    'P': ["####.", "#####", "##.##", "##.##", "##.##", "#####", "####.", "##...", "##...", "##...", "##...", "##..."],
    '-': ["...", "...", "...", "...", "...", "###", "###", "...", "...", "...", "...", "..."],
}


def big(text):
    cols = []
    for i, ch in enumerate(text):
        cols.append(np.array([[c == "#" for c in r] for r in _BIG[ch]], np.uint8))
        if i + 1 < len(text):
            cols.append(np.zeros((12, 1), np.uint8))
    return np.concatenate(cols, axis=1)


def yes_no(a):
    """はい / いいえ pills (32x16 each at y16): white letters, 'd' shade one pixel right/down."""
    for x0, text in ((0, "Yes"), (32, "No")):
        box = a[17:31, x0 + 4:x0 + 28]  # old kana: rows 1..14 inside the pill border
        box[np.isin(box, (0xc, 0xd, 0xf))] = 0xa
        m = ttf_mask(text, "arialbd.ttf", 13)
        assert m.shape[1] <= 23, text
        x = x0 + 16 - (m.shape[1] + 1) // 2
        y = 23 - m.shape[0] // 2
        put(a, x + 1, y + 1, m, 0xd)
        put(a, x, y, m, 0xf)


def header(a):
    """きせかえ ribbon title, letters at x192..245 y16..31: white outline, row-gradient fill (3/2/6/2/e/1)."""
    reg = a[16:32, 186:250]
    for r in reg:
        fx = np.nonzero(r[6:] == 0xf)[0] + 6
        if len(fx):
            r[fx.min():fx.max() + 1] = 0
    m = big("DRESS-UP")
    m = np.insert(m, [2, 9], m[[2, 9]], axis=0)  # stretch to 14 rows, the original letter height
    x = 219 - m.shape[1] // 2
    put(a, x - 1, 16, pixfont.dilate(m, 1, diag=True), 0xf)
    grad = [3, 3, 3, 3, 2, 2, 6, 6, 2, 0xe, 0xe, 1, 1, 1]
    for r in range(14):
        row = np.zeros_like(m); row[r] = m[r]
        put(a, x, 17, row, grad[r])


def ribbon_name(a):
    """Name ribbon at x150..170 y4..11 (pink band '1', white letters, shade '3')."""
    a[4:12, 148:173][a[4:12, 148:173] != 0] = 1
    a[4, 147:150] = 0xf; a[4, 169:172] = 0xf  # band corners as in the original
    m = f6("Lucia")
    x = 160 - m.shape[1] // 2
    put(a, x, 5, m, 0xf)
    bot = m.copy(); bot[:-1] = 0
    put(a, x, 5, bot, 3)


def cls_obj():
    path = "/mode/clothes/cls_obj.dcg"
    im = redraw.load(path)
    a = np.array(im)
    yes_no(a)
    header(a)
    ribbon_name(a)
    label(a, 64, 0, 32, "Lucia", 0xf, 5, 0xa)   # name slots (overwritten from cls_name at runtime)
    label(a, 64, 8, 32, "Hanon", 0xf, 5, 0xa)
    label(a, 104, 16, 48, "Hide Info", 0xf, 5, 0xb)
    save(a, im, path)


def cls_name():
    path = "/mode/clothes/cls_name.dcg"
    im = redraw.load(path)
    a = np.array(im)
    for i, n in enumerate(("Lucia", "Hanon", "Rina")):
        label(a, i * 32, 0, 32, n, 0xf, 5, 0xa)
    save(a, im, path)


def save(a, im, path):
    out = Image.new("P", (a.shape[1], a.shape[0]))
    out.putdata(a.astype(np.uint8).ravel().tolist())
    out.putpalette(im.getpalette())
    redraw.save(out, path)


if __name__ == "__main__":
    assert f6("Lucia").shape == (6, 19) and f6("Hide Info").shape[1] <= 46 and big("DRESS-UP").shape[1] <= 50
    cls_obj()
    cls_name()
    print("redrew clothes")
