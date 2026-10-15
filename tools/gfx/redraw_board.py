"""English graphics for the story board game (group "board"). Rerun to regenerate every gfx/en PNG of the group:
    python -X utf8 tools/gfx/redraw_board.py [part ..]      (default: all parts)
Originals come from gfx/orig (tools/gfx/export.py; tile widths: titlebar 21, mokuteki 16, yesno 8, map.imb 180,
the other OBJ sheets 32). Pixel values are colour indices; every drawing uses indices the original already uses.
Report: docs/re/gfx_board.md.
"""
import os, sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import apply  # noqa: E402
import pixfont  # noqa: E402
from redraw import EPISODES  # noqa: E402

FONTS = "C:/Windows/Fonts/"
BOLD = "tahomabd.ttf"  # hinted mono rendering of Tahoma Bold is crisp at 8-14 px


# ------------------------------------------------------------------ io
def load(path):
    im = Image.open(os.path.join(apply.ORIGD, apply.name_of(path)))
    return np.array(im, np.uint8), im.getpalette()


def save(a, pal, path):
    im = Image.fromarray(a.astype(np.uint8), "P")
    im.putpalette(pal)
    os.makedirs(apply.EN, exist_ok=True)
    im.save(os.path.join(apply.EN, apply.name_of(path)))


# ------------------------------------------------------------------ text
def mono(text, size=11, font=BOLD, track=0):
    """1-bit mask of text, hinted, no anti-aliasing. Row 0 = cap top, baseline row = cap height - 1.
    track = extra pixels between letters (negative = tighter)."""
    F = ImageFont.truetype(FONTS + font, size)
    asc, desc = F.getmetrics()
    w = int(F.getlength(text)) + 4 + max(0, track) * len(text)
    im = Image.new("1", (w, asc + desc + 2), 0)
    d = ImageDraw.Draw(im)
    d.fontmode = "1"
    x = 1.0
    for ch in text:
        d.text((x, 0), ch, font=F, fill=1)
        x += F.getlength(ch) + track
    a = np.array(im, np.uint8)
    a = a[F.getbbox("H")[1]:]
    cols = np.nonzero(a.any(0))[0]
    if len(cols):
        a = a[:, cols[0]:cols[-1] + 1]
    rows = np.nonzero(a.any(1))[0]
    return a[: rows.max() + 1] if len(rows) else a


def cap(size, font=BOLD):
    F = ImageFont.truetype(FONTS + font, size)
    return F.getmetrics()[0] - F.getbbox("H")[1]


def fit(text, maxw, sizes=(12, 11, 10, 9, 8), font=BOLD, tracks=(0, -1)):
    """Largest size (then tighter tracking) whose mask is <= maxw wide -> (mask, size)."""
    for t in tracks:
        for s in sizes:
            m = mono(text, s, font, t)
            if m.shape[1] <= maxw:
                return m, s
    raise ValueError(f"cannot fit {text!r} in {maxw}px")


def small(text, bold=False):
    """pixfont 5x7 (cap 7, row 0 = cap top)."""
    return pixfont.trim_rows(pixfont.render(text, bold=bold))


def tiny(text):
    return pixfont.render_tiny(text)


def _col(v, Y):
    return v(Y) if callable(v) else v


def paint(a, x, y, m, fill, ring=None, r=1, diag=True, shadow=None):
    """Draw mask m at (x, y) into index array a. fill / ring: index or function(absolute row) -> index.
    ring = r-pixel outline; shadow = (index, dx, dy) drawn under the ringed text."""
    H, W = a.shape
    def put(px, py, mm, v):
        for yy, xx in zip(*np.nonzero(mm)):
            X, Y = px + xx, py + yy
            if 0 <= X < W and 0 <= Y < H:
                a[Y, X] = _col(v, Y)
    o = pixfont.dilate(m, r, diag) if ring is not None else None
    if shadow is not None:
        si, dx, dy = shadow
        put(x - (r if o is not None else 0) + dx, y - (r if o is not None else 0) + dy, o if o is not None else m, si)
    if o is not None:
        put(x - r, y - r, o, ring)
    put(x, y, m, fill)


def bands(*spec):
    """bands((y0, idx), (y1, idx), ..) -> function(Y): index of the last band starting at or above Y."""
    def f(Y):
        v = spec[0][1]
        for y0, i in spec:
            if Y >= y0:
                v = i
        return v
    return f


def rowfill(a, x0, x1, y0, y1, src_x):
    """Erase a[y0:y1, x0:x1] with the colour each row has at column src_x (plain stripes behind text)."""
    for y in range(y0, y1):
        a[y, x0:x1] = a[y, src_x]


# ------------------------------------------------------------------ parts
def titlebars():
    """/system/common/titlebar0-2.dcg: 168x16 episode banners (pink bar at the top of the board), tw 21.
    Text fill F; ring B (rows 0-5), A (6-10), 9 (11+); bar stripes from column 167."""
    titles = EPISODES + ["Practice"]
    for f, base, n in (("titlebar0", 0, 16), ("titlebar1", 16, 16), ("titlebar2", 32, 1)):
        path = "/system/common/%s.dcg" % f
        a, pal = load(path)
        for k in range(n):
            t = a[k * 16:(k + 1) * 16]
            rowfill(t, 13, 168, 0, 16, 167)
            m, s = fit(titles[base + k], 150 - 16, sizes=(12, 11, 10))
            paint(t, 16, 2 if s >= 12 else 3, m, 15, ring=lambda Y: 11 if Y <= 5 else (10 if Y <= 10 else 9))
        save(a, pal, path)


MODETITLE_L = ["Command", "Cards", "Clothes", "View Map", "Save", "Shopping", "Info", "Card Set"]
MODETITLE_R = ["Mishap!", "Card!", "Shopping!", "Lucky!"]


def modetitle():
    """/system/common/modetitle.dcg (tw 32): window header ribbons. Left column (x 0-127, 8 x 16 rows): text on an
    A plate over a ribbon (1/2/3), fill 8 (top) 9 F (bottom). Right column (x 108-255, 4 banners): letters F/4/9 on a
    dark 1 plate with a 2 top edge and a 3/A extruded bottom, stars (6/7/8/F) at both ends."""
    path = "/system/common/modetitle.dcg"
    a, pal = load(path)
    TXT = {8, 9, 10, 13, 15}
    for k, word in enumerate(MODETITLE_L):
        t = a[k * 16:(k + 1) * 16, 0:106]
        cols = [x for x in range(106) if any(v in TXT for v in t[:, x])]
        x0, x1 = cols[0], cols[-1]
        rowfill(t, x0, x1 + 1, 0, 16, x0 - 1)
        m, s = fit(word, 76, sizes=(13, 12, 11))
        cx = (x0 + x1 + 1) // 2
        x = cx - m.shape[1] // 2
        y = 3 if cap(s) >= 9 else 4
        paint(t, x, y, m, bands((0, 8), (6, 9), (9, 15)), ring=10, r=2)
    for k, word in enumerate(MODETITLE_R):
        t = a[k * 16:(k + 1) * 16, 108:256]
        cols = [x for x in range(t.shape[1]) if any(v in (1, 2) for v in t[:, x])]
        x0, x1 = cols[0], cols[-1]
        left, right = t[:, :x0].copy(), t[:, x1 + 1:].copy()
        m, s = fit(word, 64, sizes=(12, 11, 10))
        w = m.shape[1] + 6
        cx = (x0 + x1 + 1) // 2
        nx0 = cx - w // 2
        t[:] = 0
        e = np.zeros((m.shape[0] + 4, m.shape[1]), np.uint8)
        for d in range(1, 5):
            e[d:d + m.shape[0]] |= m
        tx, ty = nx0 + 3, 3
        paint(t, tx, ty, e, 3, ring=10)                 # extruded bottom
        o = pixfont.dilate(m, 2)
        paint(t, tx - 2, ty - 2, o, lambda Y: 2 if Y <= 2 else 1)  # dark plate, light top edge
        paint(t, tx, ty, m, bands((0, 15), (7, 4), (10, 9)))
        def blit(src, x):
            for yy, xx in zip(*np.nonzero(src)):
                if 0 <= x + xx < t.shape[1]:
                    t[yy, x + xx] = src[yy, xx]
        blit(left, nx0 - left.shape[1])
        blit(right, nx0 + w)
    save(a, pal, path)


def map_mokuteki():
    """/system/common/map_mokuteki.dcg (tw 32), bank 7: name tags (rows 3-14), destination pins (rows 16-31) and
    arrow tags (rows 35-46) in pink/blue/green. Interiors are re-striped from their left edge column, text F."""
    path = "/system/common/map_mokuteki.dcg"
    a, pal = load(path)
    for k, name in enumerate(("LUCIA", "HANON", "RINA")):  # 21 px between the stars: tiny caps
        x0 = 48 * k
        rowfill(a, x0 + 13, x0 + 34, 5, 11, x0 + 14)
        m = tiny(name)
        paint(a, x0 + 24 - (m.shape[1] + 1) // 2, 6, m, 15)
    for k in range(6):  # pins: 3x destination ("Here!"), 3x goal; 26 px wide interior x 3-28, rows 18-24
        x0 = 32 * k
        rowfill(a, x0 + 3, x0 + 29, 18, 25, x0 + 2 if k % 3 else x0 + 3)
        m = small("Here!" if k < 3 else "Goal!")
        paint(a, x0 + 16 - (m.shape[1] + 1) // 2, 18, m, 15)
    for k in range(6):  # arrow tags (top banner): "Go to" / "Goal!"; interior x 2-26, rows 38-44
        x0 = 32 * k
        rowfill(a, x0 + 2, x0 + 27, 38, 45, x0 + 2)
        m = small("Go to" if k < 3 else "Goal!")
        paint(a, x0 + 15 - (m.shape[1] + 1) // 2, 38, m, 15)
    save(a, pal, path)


LABELS = {
    "mokuteki": ["Shopping Mall", "Pearl Piari", "Sports Center", "Library", "Hall", "Church", "Shrine",
                 "Aquarium", "Surfing Beach", "Beach House", "Seaside Park", "Street Stall", "Cape Lookout",
                 "Mermaid Cave", "School", "Kaito's House"],
    "mokuteki_1": ["Flower Shop", "Shoe Store", "Pharmacy", "Candy Store", "CD Shop", "Toy Store", "Herb Shop",
                   "Fruit Shop", "Sporting Goods Store", "Supermarket", "Home Center", "Rice Shop",
                   "Electronics Store", "Convenience Store", "Butcher Shop", "Greengrocer"],
    "mokuteki_2": ["Mr. Mitsuki's House", "Rina's House", "Fountain Plaza", "Central Plaza", "Izuru", "Eriru",
                   "Yuri", "Maria", "Gaito", "Mysterious Boy", "Hippo", "Herb Shop", "Stationery Store",
                   "Bookstore", "Penguin", "Bowling Alley"],
    "mokuteki_3": ["Fancy Goods Shop"],
}


def label(t, word, right=95, bands_=None, ring=1, ul=10, maxw=94):
    """Destination name label (128x16, right-aligned at x=right): bold text with ring, A underline rows 13-14."""
    m, s = fit(word, maxw, sizes=(11, 10, 9))
    x = right - m.shape[1] + 1
    y = 4 if cap(s) >= 8 else 5
    t[13, x - 1:right + 1] = ul
    t[14, x - 2:right + 1] = ul
    paint(t, x, y, m, bands_ or bands((0, 15), (7, 4), (10, 3)), ring=ring)


def mokuteki():
    """/system/common/mokuteki*.dcg (tw 16): 128x16 destination names (only x 0-95 is shown, right-aligned),
    fill F/4/3 top to bottom, ring 1, underline A."""
    for f, words in LABELS.items():
        path = "/system/common/%s.dcg" % f
        a, pal = load(path)
        a[:] = 0
        for k, w in enumerate(words):
            label(a[k * 16:(k + 1) * 16], w)
        save(a, pal, path)


def destination():
    """/system/common/destination.dcg (tw 32): "へ ___ マス" after the destination name (x 0-39: へ dropped, マス ->
    "left"), the episode banner copy (x 107-255, rows 0-15), "ゴール!" arrow tag (x 0-31, rows 16-31) and a sample
    name label (x 160-255, rows 16-31)."""
    path = "/system/common/destination.dcg"
    a, pal = load(path)
    a[0:13, 0:9] = 0                      # へ (rows 13-14 keep the underline)
    a[0:13, 22:40] = 0                    # マス
    a[13:15, 0:40] = 10
    m = mono("left", 9)
    paint(a, 39 - m.shape[1], 5, m, 15, ring=10)
    # episode banner copy: bar stripes from column 255, text as the titlebars (ring B/A/9)
    rowfill(a, 107, 256, 0, 16, 255)
    m, s = fit(EPISODES[0], 140, sizes=(12, 11))
    paint(a, 111, 2, m, 15, ring=lambda Y: 11 if Y <= 5 else (10 if Y <= 10 else 9))
    # ゴール! arrow tag: interior x 2-26 rows 22-28
    rowfill(a, 2, 27, 21, 29, 2)
    m = small("Goal!")
    paint(a, 15 - (m.shape[1] + 1) // 2, 21, m, 15)
    # sample label (inverted gradient: 9 top, 4, F bottom)
    t = a[16:32, 128:256]
    t[:, 32:] = 0
    label(t, "Surfing Beach", right=127, bands_=bands((0, 9), (7, 4), (10, 15)))
    save(a, pal, path)


PARTS = {"titlebars": titlebars, "modetitle": modetitle, "map_mokuteki": map_mokuteki, "mokuteki": mokuteki,
         "destination": destination}

if __name__ == "__main__":
    for p in (sys.argv[1:] or PARTS):
        PARTS[p]()
        print("redrew", p)
