"""English graphics for the title group: Konami/copyright screen, title logo, "press START", mode select and
title menus, name entry header.  Writes gfx/en/<name>.png from gfx/orig/<name>.png (palette-mode, colour indices).
    python -X utf8 tools/gfx/redraw_title.py            (report: docs/re/gfx_title.md)
Originals: export.py exports (OBJ sheets with --tw 32: these files are loaded 1:1 into 2D-mapped OBJ VRAM), except
title_logo.acg (8bpp OBJ + IS-ACG03 trailer), which this script exports itself (orig_acg()).
"""
import os, struct, sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import apply, fs, pixfont  # noqa: E402
import gfxfmt as gfx  # noqa: E402

FONTS = "C:/Windows/Fonts/"


# ------------------------------------------------------------------ io
def load(path):
    im = Image.open(os.path.join(apply.ORIGD, apply.name_of(path)))
    return np.array(im, dtype=np.uint8), im.getpalette()


def save(path, a, pal):
    im = Image.new("P", (a.shape[1], a.shape[0]))
    im.putpalette(pal)
    im.putdata(a.ravel().tolist())
    os.makedirs(apply.EN, exist_ok=True)
    im.save(os.path.join(apply.EN, apply.name_of(path)))


# ------------------------------------------------------------------ text masks
def ttf(text, font, size, thresh=128):
    """-> (mask, cap) : 1-bit mask whose row 0 is the cap top; cap = cap height (baseline row)."""
    f = ImageFont.truetype(FONTS + font, size, layout_engine=ImageFont.Layout.BASIC)
    top, base = f.getbbox("H")[1], f.getbbox("H")[3]
    bot = max(base, f.getbbox("gjpqy")[3])
    x0, _, x1, _ = f.getbbox(text)
    im = Image.new("L", (x1 - x0 + 4, bot - top + 2), 0)
    ImageDraw.Draw(im).text((2 - x0, -top), text, font=f, fill=255)
    m = (np.array(im) >= thresh).astype(np.uint8)
    cols = np.nonzero(m.any(0))[0]
    return m[:, cols[0]:cols[-1] + 1], base - top


def tiny(text):
    m = pixfont.render_tiny(text)
    return m, 5


def pix(text, bold=False):
    return pixfont.trim_rows(pixfont.render(text, bold=bold)), 7


def fit(text, maxw, fonts):
    """First (font, size) whose mask fits maxw."""
    for fn, s in fonts:
        m, cap = ttf(text, fn, s)
        if m.shape[1] <= maxw:
            return m, cap
    return m, cap


# ------------------------------------------------------------------ painting
def dil(m, r, diag=True):
    return pixfont.dilate(m, r, diag) if r else m


def put(dst, x, y, m, ink, only=None):
    """Paint mask m at (x, y); ink = index or f(abs_row) -> index; only = set of indices that may be overwritten."""
    H, W = dst.shape
    ys, xs = np.nonzero(m)
    for yy, xx in zip(ys + y, xs + x):
        if 0 <= yy < H and 0 <= xx < W and (only is None or dst[yy, xx] in only):
            dst[yy, xx] = ink(yy) if callable(ink) else ink


def styled(dst, x, y, m, fill, rings=(), shadow=None, diag=True):
    """Text mask m with its top-left at (x, y). rings = [(radius, ink), ..] from the glyph outwards;
    shadow = (dx, dy, ink[, only]) drawn under everything."""
    tot = sum(rg[0] for rg in rings)
    if shadow:
        dx, dy, ink = shadow[:3]
        put(dst, x - tot + dx, y - tot + dy, dil(m, tot, diag), ink, shadow[3] if len(shadow) > 3 else None)
    acc = tot
    for rg in reversed(rings):
        r, ink, outer = rg[0], rg[1], len(rg) > 2 and rg[2]
        d = dil(m, acc, diag)
        if outer:   # ring only on the outside: keep letter counters open
            inner = np.pad(dil(m, acc - r, diag), r)
            d = d & ~(ndimage.binary_fill_holes(inner) & ~inner.astype(bool))
        put(dst, x - acc, y - acc, d, ink)
        acc -= r
    put(dst, x, y, m, fill)


def bands(*spec):
    """bands((row_limit, idx), ...) -> f(row): idx of the first band with row <= limit (relative to y0 set later)."""
    def mk(y0):
        def f(row):
            for lim, idx in spec:
                if row - y0 <= lim:
                    return idx
            return spec[-1][1]
        return f
    return mk


# ------------------------------------------------------------------ menu labels (2D OBJ sheets, 16-px rows)
# Pill labels (title_obj modes, title_serect): text rows 3-12, fill 8/7/6 by row, outline f; pill indices 9 a b c.
PILL_TEXT = {0x6, 0x7, 0x8, 0xd, 0xe, 0xf}
LABEL_FONTS = [("tahomabd.ttf", 11), ("tahomabd.ttf", 10), ("ARIALNB.TTF", 12), ("ARIALNB.TTF", 11)]


def pill_row(vals):
    """Pill colour of one row: the most common non-text index; b wins over c (c on b is the kana's drop shadow)."""
    v = [int(x) for x in vals if x not in PILL_TEXT]
    if not v:
        return 0
    if 0xb in v and 0xc in v:
        return 0xb
    return max(set(v), key=v.count)


def pill_label(a, y0, tx0, tx1, text, align="c"):
    """Erase the text between columns tx0..tx1 of the 16-px label at row y0 and write English.
    Text pixels (and the kana's c-on-b drop shadow) become the pill's row colour."""
    col = [pill_row(a[y0 + y, tx0:tx1]) for y in range(16)]
    for y in range(16):
        for x in range(tx0, tx1):
            v = a[y0 + y, x]
            if v in PILL_TEXT or (v == 0xc and col[y] == 0xb):
                a[y0 + y, x] = col[y]
    m, cap = fit(text, tx1 - tx0 - 2, LABEL_FONTS)
    w = m.shape[1]
    x = tx0 + 1 if align == "l" else tx1 - 1 - w if align == "r" else (tx0 + tx1 - w) // 2
    top = y0 + 11 - cap   # baseline on row 11 (as the kana bottoms)
    fill = lambda row: 0x8 if row - y0 <= 6 else 0x7 if row - y0 <= 9 else 0x6
    styled(a, x, top, m, fill, [(1, 0xf)], shadow=(0, 1, 0xc, {0xb}))


# Difficulty pills (title_serect right column rows 0-47): fill f/e/d, outline 1 (2 px); pill rows from a clean column.
def diff_label(a, x0, y0, text, cx):
    clean = a[y0:y0 + 16, x0 + 90].copy()
    a[y0:y0 + 15, x0 + 20:x0 + 84] = clean[:15, None]
    m, cap = ttf(text, "tahomabd.ttf", 14)
    top = y0 + 11 - cap
    fill = lambda row: 0xf if row - y0 <= 5 else 0xe if row - y0 <= 8 else 0xd
    styled(a, cx - m.shape[1] // 2, top, m, fill, [(2, 0x1)])


# Headers (title_menu, title_obj row 0): fill f/a/9/8, outline 2 px of 6 (upper) / 5 (lower), stars at the ends.
HEAD_FONTS = [("tahomabd.ttf", 13), ("tahomabd.ttf", 12), ("tahomabd.ttf", 11), ("ARIALNB.TTF", 13),
              ("ARIALNB.TTF", 12)]


def header(a, y0, text, xlo=0, xhi=256):
    band = a[y0:y0 + 16, xlo:xhi]
    star = np.isin(band, [0xb, 0xc, 0xd, 0xe]).any(0)
    cols = np.nonzero(star)[0] + xlo
    s1 = cols[cols < cols.min() + 20].max()      # left star's right edge
    s2 = cols[cols > s1 + 20].min()               # right star's left edge
    ex0, ex1 = s1 + 3, s2 - 2
    a[y0:y0 + 16, ex0:ex1] = 0
    m, cap = fit(text, ex1 - ex0 - 4, HEAD_FONTS)
    x = (ex0 + ex1 - m.shape[1]) // 2
    top = y0 + 12 - cap
    fill = lambda row: 0xf if row - y0 <= 5 else 0xa if row - y0 <= 7 else 0x9 if row - y0 <= 9 else 0x8
    ring = lambda row: 0x6 if row - y0 <= 8 else 0x5
    styled(a, x, top, m, fill, [(2, ring)])


# Player pills (title_obj x 152-192, rows 32-63, 8 px each): white 5-row text.
PLAYER = [(32, 0x4, 0x5, 0x6), (40, 0xa, 0xb, 0xc), (48, 0x7, 0x8, 0x9), (56, 0x1, 0x2, 0x3)]


def player_pill(a, y0, inner, rim, shade, text):
    for y in range(y0 + 1, y0 + 7):
        for x in range(154, 192):
            if a[y, x] == 0xf:
                a[y, x] = inner
    for x in range(156, 190):
        if a[y0 + 7, x] == shade:
            a[y0 + 7, x] = rim
    m, _ = tiny(text)
    x = 173 - m.shape[1] // 2
    put(a, x, y0 + 2, m, 0xf)
    put(a, x, y0 + 7, m[-1:], shade, only={rim})


def title_obj():
    path = "/mode/title/title_obj.dcg"
    a, pal = load(path)
    header(a, 0, "Mode Select", 0, 150)
    for y0, text in [(16, "Solo Pitch"), (32, "Party Pitch"), (48, "Link Pitch")]:
        pill_label(a, y0, 21, 98, text)
    for y0, text in [(0, "All-Out Pitch"), (16, "Dress-Up Pitch")]:
        pill_label(a, y0, 173, 248, text)
    for (y0, inner, rim, shade), text in zip(PLAYER, ["Player 1", "Player 2", "Player 3", "Computer"]):
        player_pill(a, y0, inner, rim, shade, text)
    save(path, a, pal)


def title_serect():
    path = "/mode/title/title_serect.dcg"
    a, pal = load(path)
    for y0, text in [(0, "Lucia"), (16, "Hanon"), (32, "Rina")]:
        pill_label(a, y0, 14, 98, text, align="l")
    pill_label(a, 48, 14, 81, "Confirm")          # the note (x 82-88) stays
    pill_label(a, 64, 40, 98, "Episodes", align="r")
    for y0, text in [(80, "Two Players"), (96, "Solo Pitch"), (112, "Link Pitch"), (128, "Dress-Up Pitch"),
                     (144, "Practice")]:
        pill_label(a, y0, 21, 98, text)
    for y0, text in [(0, "Hard"), (16, "Normal"), (32, "Easy")]:
        diff_label(a, 104, y0, text, 155)
    right = [(48, "New Game", 128), (64, "Continue", 128), (80, "Three Players", 126), (96, "Party Pitch", 126),
             (112, "All-Out Pitch", 126), (128, "Hard Rules", 126), (144, "Easy Rules", 126)]
    for y0, text, tx0 in right:
        pill_label(a, y0, tx0, 202, text)
    save(path, a, pal)


def title_menu():
    path = "/mode/title/title_menu.dcg"
    a, pal = load(path)
    heads = ["Mode Select", "Checking Link", "Players", "Character Select", "Episodes", "Load Save",
             "Story...", "Turn Order"]
    for i, text in enumerate(heads):
        header(a, 16 * i, text, 0, 160)
    save(path, a, pal)


GROUPS = {"title_obj": title_obj, "title_serect": title_serect, "title_menu": title_menu}

if __name__ == "__main__":
    for g in (sys.argv[1:] or GROUPS):
        GROUPS[g]()
        print("redrew", g)
