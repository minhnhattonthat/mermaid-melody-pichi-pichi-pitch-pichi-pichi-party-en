"""Name entry character grid (/mode/title/name.imb): kana -> the Latin letters of tools/romdata.py NAME_ROWS.

Runs redraw_title.name_entry() first (header + help bar, owned by that script), then repaints the 5x12 grid on
its output gfx/en/mode__title__name.imb.png, so rerunning this script alone always regenerates the full PNG.
Style of the kana: 1-px white strokes (223) with a dark drop shadow (2) right/below. Space and OK cells kept.
"""
import os, sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import apply, redraw_title, romdata  # noqa: E402

PATH = "/mode/title/name.imb"
WHITE, SHADOW = 223, 2
COLS = [24, 40, 55, 72, 87, 111, 127, 143, 159, 175, 200, 216]   # kana cell centres (x), from gfx/orig
ROWS = [71, 87, 103, 119, 135]                                   # (y)
FONT = ImageFont.truetype("C:/Windows/Fonts/msgothic.ttc", 14)   # embedded 1-bit bitmap strike: 1-px strokes


def glyph(ch):
    """-> (mask, top) ; top = row offset of the mask in a line box whose cap height is centred."""
    im = Image.new("L", (24, 24), 0)
    d = ImageDraw.Draw(im)
    d.fontmode = "1"
    if ch != "'":                   # full-width forms are kana-sized; the full-width apostrophe is a stray tick
        ch = chr(ord(ch) + 0xFEE0)
    d.text((4, 2), ch, font=FONT, fill=255)
    m = np.array(im) > 127
    ys, xs = np.nonzero(m)
    return m[ys.min():ys.max() + 1, xs.min():xs.max() + 1], ys.min()


def erase(a, pal, x0, y0, x1, y1):
    """Replace the kana pixels in the box by a diffusion of the surrounding panel colours."""
    box = a[y0:y1, x0:x1]
    hole = np.isin(box, (WHITE, SHADOW))
    p = np.array(pal[:768], dtype=float).reshape(-1, 3)
    rgb = p[box]
    for _ in range(80):
        pad = np.pad(rgb, ((1, 1), (1, 1), (0, 0)), mode="edge")
        avg = (pad[:-2, 1:-1] + pad[2:, 1:-1] + pad[1:-1, :-2] + pad[1:-1, 2:]) / 4
        rgb[hole] = avg[hole]
    allowed = sorted(set(np.unique(a).tolist()) - {WHITE, SHADOW})
    pa = p[allowed]
    for y, x in zip(*np.nonzero(hole)):
        box[y, x] = allowed[int(((pa - rgb[y, x]) ** 2).sum(1).argmin())]


def name_grid():
    redraw_title.name_entry()
    fn = os.path.join(apply.EN, apply.name_of(PATH))
    im = Image.open(fn)
    a, pal = np.array(im, dtype=np.uint8), im.getpalette()
    base = glyph("H")[1]            # cap top of the line box
    for r, (cy, row) in enumerate(zip(ROWS, romdata.NAME_ROWS)):
        for c, cx in enumerate(COLS):
            if r == 4 and c >= 10:
                continue            # space and OK cells stay
            erase(a, pal, cx - 9, cy - 7, cx + 9, cy + 7)
            if c >= len(row):
                continue
            m, top = glyph(row[c])
            x, y = cx - m.shape[1] // 2, cy - 5 + (top - base)   # cap height ~10 centred on the kana centre
            ys, xs = np.nonzero(m)
            for dy, dx in ((0, 1), (1, 0), (1, 1)):
                a[ys + y + dy, xs + x + dx] = SHADOW
            a[ys + y, xs + x] = WHITE
    out = Image.new("P", im.size)
    out.putpalette(pal)
    out.putdata(a.ravel().tolist())
    out.save(fn)


if __name__ == "__main__":
    assert [len(r) for r in romdata.NAME_ROWS] == [12, 12, 12, 12, 10], romdata.NAME_ROWS
    name_grid()
    print("redrew name_grid")
