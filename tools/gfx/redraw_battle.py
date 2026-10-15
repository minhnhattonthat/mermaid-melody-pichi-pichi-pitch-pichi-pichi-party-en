"""Battle mini-game graphics -> English (gfx/en/*.png). Rerun to regenerate all of them.
    python -X utf8 tools/gfx/redraw_battle.py
Files (all 4bpp, 2D sheets 32 tiles wide; exports: tools/gfx/export.py PATH --tw 32):
  /battle/battle_call_bar.dcg     OBJ: turn banners (128x32 at y 0/32/64) + enemy attack bars (128x24 cells at
                                  x 0, y 96+24k and x 128, y 32k)
  /battle/battle_def_bar_name.dcg OBJ: header bars 96x16 at y 16k (enemy attacks, contest kinds)
  /battle/battle_bg_off.dcg       BG3 labels (tile rows 4/6/8) and the Points / Damage plates (x 208-255)
  /battle/battle_bg_def.dcg       BG labels (tile row 4)
Labels are tile-mapped (maps built in code and /battle/b_def_bg*.asc): every text stays inside its original tiles.
Report: docs/re/gfx_battle.md. Reach: tools/debug/scenes.md (battle mode 0x0829C50C).
"""
import os, sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import redraw  # noqa: E402

NARROW = "ARIALNB.TTF"   # Arial Narrow Bold: the kana labels are tight, a narrow face keeps full words


# ------------------------------------------------------------------ helpers
def load(path):
    im = redraw.load(path)
    return np.array(im), im


def save(a, im, path):
    out = Image.new("P", (a.shape[1], a.shape[0]))
    out.putdata(a.astype(np.uint8).ravel().tolist())
    out.putpalette(im.getpalette())
    redraw.save(out, path)


def tmask(text, size, font=NARROW):
    """Unantialiased text mask -> (mask, cap_top_row): rows keep the font's frame, columns are trimmed."""
    f = ImageFont.truetype(redraw.FONTS + font, size, layout_engine=ImageFont.Layout.BASIC)
    w, h = int(f.getlength(text)) + 6, size * 2
    im = Image.new("1", (w, h), 0)
    d = ImageDraw.Draw(im)
    d.fontmode = "1"
    d.text((2, 2), text, font=f, fill=1)
    m = np.array(im, np.uint8)
    cols = np.nonzero(m.any(0))[0]
    m = m[:, cols.min():cols.max() + 1]
    return m, 2 + f.getbbox("H")[1]


def disc(m, r):
    """Round dilation (pads r on each side)."""
    o = np.pad(m, r)
    out = np.zeros_like(o)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dy * dy + dx * dx <= r * r + (1 if r > 1 else 2):
                out |= np.roll(np.roll(o, dy, 0), dx, 1)
    return out


def put(a, x, y, m, v):
    """v: index or function(row of a) -> index."""
    H, W = a.shape
    for yy, xx in zip(*np.nonzero(m)):
        X, Y = x + xx, y + yy
        if 0 <= X < W and 0 <= Y < H:
            a[Y, X] = v(Y) if callable(v) else v


def row_modes(sub, sel):
    out = {}
    for y in range(sub.shape[0]):
        v = sub[y][sel[y]]
        if len(v):
            out[y] = int(np.bincount(v).argmax())
    return out


def nearest(d, default=0):
    ks = sorted(d)
    return (lambda y: d[min(ks, key=lambda k: abs(k - y))]) if ks else (lambda y: default)


def row_bg(sub, struct):
    """Per-row background of a box: the most common index away from the text structure (0 if none)."""
    m = row_modes(sub, ~disc(struct.astype(np.uint8), 1)[1:-1, 1:-1].astype(bool))
    return np.array([[m.get(y, 0)] * sub.shape[1] for y in range(sub.shape[0])])


def voted_bg(a, cells, struct_set):
    """Clean background shared by equal cells (x, y, w, h): per pixel the most common value among the cells where
    that pixel is away from text; pixels covered in every cell fall back to the row's background."""
    w, h = cells[0][2], cells[0][3]
    stack = np.array([a[y:y + h, x:x + w] for x, y, _, _ in cells])
    away = np.array([~disc(np.isin(s, struct_set).astype(np.uint8), 1)[1:-1, 1:-1].astype(bool) for s in stack])
    rb = row_bg(stack[0], ~away[0])
    out = rb.copy()
    for yy in range(h):
        for xx in range(w):
            v = stack[:, yy, xx][away[:, yy, xx]]
            if len(v):
                out[yy, xx] = np.bincount(v).argmax()
    return out


def relabel(a, box, text, size, letters, struct=(), rings=((2, "bg"),), bg=None, fill=None, align="c",
            dy=0, pad=0):
    """Replace the text in box (x0, y0, x1, y1) of index array a.
    letters: indices of the original letter fill (its per-row gradient is reused); struct: other indices that belong
    to the text (outlines) and are erased with it; rings: (radius, index | 'bg' | f(row)) outlines, outermost first
    ('bg' = the plate colour of that row, or of the nearest plated row); bg: replacement background for the box
    (default: per-row background); fill: {row: index} gradient override (rows of a)."""
    x0, y0, x1, y1 = box
    sub = a[y0:y1, x0:x1]
    L = np.isin(sub, letters)
    S = L | np.isin(sub, struct)
    ys = np.nonzero(L.any(1))[0]
    ftop = y0 + ys.min()
    grad = nearest(fill) if fill else nearest({y0 + k: v for k, v in row_modes(sub, L).items()})
    b = row_bg(sub, S) if bg is None else bg
    sub[:] = b
    plate = nearest({y0 + y: int(b[y].max()) for y in range(b.shape[0]) if b[y].max()}, 0)
    m, cap = tmask(text, size)
    r = max([rr for rr, _ in rings] + [0])
    w = m.shape[1]
    if align == "c":
        x = (x0 + x1) // 2 - w // 2
    elif align == "r":
        x = x1 - pad - r - w
    else:
        x = x0 + pad + r
    y = ftop - cap + dy
    assert x - r >= x0 and x + w + r <= x1, (text, x - r, x + w + r, box)
    for rr, v in rings:
        put(a, x - rr, y - rr, disc(m, rr), plate if v == "bg" else v)
    put(a, x, y, m, grad)
    return x, x + w


# ------------------------------------------------------------------ BG labels
NAVY = dict(letters=[0xa, 9, 5, 8], rings=((2, "bg"),))      # battle_bg_off row 4 (bank 13): pink on navy
TEAL = dict(letters=[0xf, 0xa, 9, 8], rings=((2, "bg"),))    # battle_bg_off rows 6/8 (bank 12): white on teal
PINK = dict(letters=[8, 7, 6, 5], rings=((2, "bg"),))        # battle_bg_def row 4: pink on navy


def bg_off():
    p = "/battle/battle_bg_off.dcg"
    a, im = load(p)
    # row 4: cap tile (col 0) + 10 text tiles per command (cols 1-10, 11-20, 21-30), cap = col 0 flipped
    for c, t in ((1, "Attack Voice"), (11, "Guard Rhythm"), (21, "Dodge Step")):
        relabel(a, (c * 8, 32, c * 8 + 80, 48), t, 14, **NAVY)
    # row 6: "roulette" hints, 16 tiles each, the first 9 px are the bullet cap
    relabel(a, (9, 48, 128, 64), "Guard with Roulette", 14, **TEAL)
    relabel(a, (137, 48, 256, 64), "Attack with Roulette!", 14, **TEAL)
    # row 8: "[n]~[n] to dodge": the digit circles (cols 1-2, 5-6, replaced by digit tiles in game) and ~ stay
    relabel(a, (56, 64, 128, 80), "to dodge", 14, align="l", pad=1, **TEAL)
    # Points / Damage plates (cols 26-31): white-edged navy plate shaped around the letters over the pink bar
    bar = [0xf, 7, 7, 7, 6, 6, 6, 5, 5, 5, 0xf]
    for y0, t in ((0, "Points"), (16, "Damage")):
        bg = np.zeros((16, 48), int)
        for k, v in enumerate(bar):
            bg[5 + k, :] = v
        top = y0 + 3
        fill = {top + k: v for k, v in enumerate([0xf] * 4 + [4] * 3 + [3] * 3)}
        relabel(a, (208, y0, 256, y0 + 16), t, 12, letters=[0xf, 0xc, 4, 3], struct=[1, 2, 5],
                rings=((3, 0xf), (2, 1)), bg=bg, fill=fill, align="r", dy=0)
    save(a, im, p)


def bg_def():
    p = "/battle/battle_bg_def.dcg"
    a, im = load(p)
    for c, t in ((1, "Dodge Step"), (11, "Guard Rhythm")):
        relabel(a, (c * 8, 32, c * 8 + 80, 48), t, 14, **PINK)
    save(a, im, p)


# ------------------------------------------------------------------ OBJ banners
def call_bar():
    p = "/battle/battle_call_bar.dcg"
    a, im = load(p)
    # turn banners: white letters shaded c/d on the blue ribbon; stars at both ends stay
    turns = [(0, "Lucia's Turn"), (32, "Hanon's Turn"), (64, "Rina's Turn")]
    struct = [0xf, 0xc, 0xd, 0xe, 7]
    cells = [(18, y, 85, 32) for y, _ in turns]
    bg = voted_bg(a, cells, struct)
    for y, t in turns:
        relabel(a, (18, y, 103, y + 32), t, 15, letters=[0xf, 0xc, 0xd], struct=[0xe, 7], bg=bg,
                rings=((2, "bg"),))
    # enemy attack bars: pink-gradient letters, white then teal outline over the ribbon
    names = ["Izuru's Attack", "Eriru's Attack", "Yuri's Attack", "Maria's Attack", "Gaito's Attack", "Mishap!"]
    cells = [(0, 96 + 24 * k, 128, 24) for k in range(6)] + [(128, 32 * k, 128, 24) for k in range(6)]
    struct = [8, 7, 6, 9, 0xf, 0xa]
    bg = voted_bg(a, cells, struct)
    for (x, y, w, h), t in zip(cells, names + names):
        relabel(a, (x, y, x + 120, y + h), t, 15, letters=[8, 7, 6], struct=[9, 0xf, 0xa, 4], bg=bg[:, :120],
                rings=((2, 4), (1, 0xf)))
    save(a, im, p)


def def_bar_name():
    p = "/battle/battle_def_bar_name.dcg"
    a, im = load(p)
    names = ["Izuru's Attack", "Eriru's Attack", "Yuri's Attack", "Maria's Attack", "Gaito's Attack",
             "Dance Moves", "Cooking", "Sketching", "Playing", "Gently"]
    struct = [0xf, 9, 8, 5, 3, 2, 4]
    cells = [(2, 16 * k, 92, 16) for k in range(10)]
    bg = voted_bg(a, cells, struct)
    for k, t in enumerate(names):
        y0 = 16 * k
        ring = (lambda y0: lambda y: 4 if y - y0 < 2 else (3 if y - y0 < 9 else 2))(y0)
        relabel(a, (2, y0, 94, y0 + 16), t, 14, letters=[0xf, 9, 8], struct=[5, 3, 2, 4], bg=bg,
                rings=((2, ring),))
    save(a, im, p)


if __name__ == "__main__":
    bg_off()
    bg_def()
    call_bar()
    def_bar_name()
    print("redrew battle")
