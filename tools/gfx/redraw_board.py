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
from redraw import EPISODES, FONTS  # noqa: E402

BOLD = "DejaVuSansCondensed-Bold.ttf"  # hinted mono rendering is crisp at 8-14 px


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


def rowmode(a, x0, x1, y0, y1, skip=(15,)):
    """Erase a[y0:y1, x0:x1] row by row with the row's most common colour other than skip (text) colours."""
    for y in range(y0, y1):
        vals = [v for v in a[y, x0:x1].tolist() if v not in skip]
        if vals:
            a[y, x0:x1] = max(set(vals), key=vals.count)


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
        star_banner(a[k * 16:(k + 1) * 16, 108:256], word)
    save(a, pal, path)


def star_banner(t, word, maxw=64):
    """16-row banner with a star at each end: letters F/4/9 on a dark 1 plate (2 top edge), 3/A extruded
    bottom. The stars (everything left/right of the plate columns) move to hug the new text."""
    cols = [x for x in range(t.shape[1]) if any(v in (1, 2) for v in t[:, x])]
    x0, x1 = cols[0], cols[-1]
    left, right = t[:, :x0].copy(), t[:, x1 + 1:].copy()
    m, s = fit(word, maxw, sizes=(12, 11, 10))
    w = m.shape[1] + 6
    nx0 = (x0 + x1 + 1) // 2 - w // 2
    t[:] = 0
    e = np.zeros((m.shape[0] + 4, m.shape[1]), np.uint8)
    for d in range(1, 5):
        e[d:d + m.shape[0]] |= m
    tx, ty = nx0 + 3, 3
    paint(t, tx, ty, e, 3, ring=10)                 # extruded bottom
    paint(t, tx - 2, ty - 2, pixfont.dilate(m, 2), lambda Y: 2 if Y <= 2 else 1)  # dark plate, light top edge
    paint(t, tx, ty, m, bands((0, 15), (7, 4), (10, 9)))
    for src, x in ((left, nx0 - left.shape[1]), (right, nx0 + w)):
        for yy, xx in zip(*np.nonzero(src)):
            if 0 <= x + xx < t.shape[1]:
                t[yy, x + xx] = src[yy, xx]


def map_mokuteki():
    """/system/common/map_mokuteki.dcg (tw 32), bank 7: name tags (rows 3-14), destination pins (rows 16-31) and
    arrow tags (rows 35-46) in pink/blue/green. Interiors are re-striped from their left edge column, text F."""
    path = "/system/common/map_mokuteki.dcg"
    a, pal = load(path)
    for k, name in enumerate(("LUCIA", "HANON", "RINA")):  # 21 px between the stars: tiny caps
        x0 = 48 * k
        vals = [v for v in a[5:11, x0 + 13:x0 + 34].ravel().tolist() if v != 15]
        a[5:11, x0 + 13:x0 + 34] = max(set(vals), key=vals.count)
        m = tiny(name)
        paint(a, x0 + 24 - (m.shape[1] + 1) // 2, 6, m, 15)
    for k in range(6):  # pins: 3x destination ("Here!"), 3x goal; 26 px wide interior x 3-28, rows 18-24
        x0 = 32 * k
        rowmode(a, x0 + 3, x0 + 29, 18, 25)
        m = small("Here!" if k < 3 else "Goal!")
        paint(a, x0 + 16 - (m.shape[1] + 1) // 2, 18, m, 15)
    for k in range(6):  # arrow tags (top banner): "Go to" / "Goal!"; interior x 2-26, rows 38-44
        x0 = 32 * k
        rowmode(a, x0 + 2, x0 + 27, 38, 45)
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
    """Destination name label (128x16, right-aligned at x=right): bold text with ring, A underline rows 13-14.
    The "Go to"/"Goal!" tag sprite sits at a fixed x (screen 126-156) under labels wider than ~44 px (true in
    Japanese too), so the text gets a ring-coloured plate: the tag is cut off cleanly instead of showing through
    between letters."""
    m, s = fit(word, maxw, sizes=(11, 10, 9))
    x = right - m.shape[1] + 1
    y = 4 if cap(s) >= 8 else 5
    p = x - 2
    t[3:13, p:right + 1] = ring
    t[13:15, p:right + 1] = ul
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


def bubble(t, word, x0=4, x1=28, y0=1, y1=13, sizes=(11, 10, 9)):
    """Rounded A bubble (32x16) with F/D text: text pixels inside the box become A, new text F."""
    box = t[y0:y1, x0:x1]
    box[(box == 15) | (box == 13)] = 10
    m, s = fit(word, x1 - x0 - 1, sizes=sizes)
    paint(t, 16 - (m.shape[1] + 1) // 2, 7 - (cap(s) + 1) // 2 + 1, m, 15)


def yesno():
    """/system/common/yesno.dcg (tw 8): 64x16 rows of two answer bubbles: はい/いいえ, つかう/すてる, きがえ/すてる."""
    path = "/system/common/yesno.dcg"
    a, pal = load(path)
    for k, (l, r) in enumerate((("Yes", "No"), ("Use", "Toss"), ("Wear", "Toss"))):
        bubble(a[k * 16:(k + 1) * 16, 0:32], l)
        bubble(a[k * 16:(k + 1) * 16, 32:64], r)
    save(a, pal, path)


def roulet_obj():
    """/system/common/roulet_obj.dcg (tw 32): pink はい/いいえ bubbles (rows 16-31), corner labels
    コンピューター (C plate, split 32+8 px: rows 1-7 x 65-95 and rows 9-15 x 64-70), マップ (rows 16-23) and
    みる (rows 24-31) on 1 plates (text F top, 4 bottom)."""
    path = "/system/common/roulet_obj.dcg"
    a, pal = load(path)
    bubble(a[16:32, 0:32], "Yes")
    bubble(a[16:32, 32:64], "No")
    v = np.full((7, 38), 12, np.uint8)            # COMPUTER strip, then split into the two sprites
    m = tiny("COMPUTER")
    paint(v, 19 - (m.shape[1] + 1) // 2, 1, m, 15)
    a[1:8, 65:96] = v[:, :31]
    a[9:16, 64:71] = v[:, 31:]
    for y0, word in ((17, "MAP"), (25, "VIEW")):
        cols = np.nonzero((a[y0:y0 + 6, 64:90] != 0).any(0))[0] + 64
        xa, xb = cols[0] + 1, cols[-1]
        a[y0:y0 + 6, xa:xb] = 1
        m = tiny(word)
        paint(a, (xa + xb) // 2 - (m.shape[1] + 1) // 2 + 1, y0, m, bands((0, 15), (y0 + 3, 4)))
    save(a, pal, path)


RANKS = [("Yay!", "st"), ("Nice!", "nd"), ("Go for it!", "rd")]


def rank(t, phrase, suffix, y0, fillb, underline, d0, d1):
    """Rank strip (phrase, digit at columns d0-d1, 位): keep the digit, redraw phrase and 位 -> ordinal suffix."""
    d0, d1 = d0 + 1, d1 - 1
    cols = np.nonzero(t.any(0))[0]
    e0, e1 = cols[0], cols[-1]
    keep = t[:, d0 - 1:d1 + 2].copy()
    t[:, :] = 0
    if underline:
        t[14:16, e0 + 3:e1 - 1] = 5
    t[:, d0 - 1:d1 + 2] = np.where(keep != 0, keep, t[:, d0 - 1:d1 + 2])
    m, s = fit(phrase, d0 - e0 - 3, sizes=(11, 10, 9))
    paint(t, d0 - 2 - m.shape[1], y0, m, fillb, ring=1)
    m = mono(suffix, 9)
    paint(t, d1 + 3, y0 + 1, m, fillb, ring=1)


def map_rank():
    """/system/common/map_rank.dcg (tw 32): やったね!1位 / いいかんじ!2位 / がんばれ!3位, fill 8/4/3, ring 1,
    5 underline."""
    path = "/system/common/map_rank.dcg"
    a, pal = load(path)
    a2 = a.copy()
    for (phrase, suf), (x0, x1, d) in zip(RANKS, ((0, 71, 45), (71, 144, 119), (144, 220, 190))):
        rank(a2[:, x0:x1], phrase, suf, 4, bands((0, 8), (9, 4), (12, 3)), True, d - x0, d - x0 + 8)
    save(a2, pal, path)


def status_obj():
    """/system/common/status_obj.dcg (tw 32): やったね! 1 位 (rows 16-31, x 0-72) in the status window."""
    path = "/system/common/status_obj.dcg"
    a, pal = load(path)
    rank(a[16:32, 0:76], "Yay!", "st", 5, bands((0, 8), (24 - 16, 4), (27 - 16, 3)), False, 43, 52)
    save(a, pal, path)


def roulet_obj_drum():
    """/system/common/roulet_obj_drum.dcg (tw 32): ハプニング! star banner (rows 0-15, x 0-107) and the
    カードゲット! sign (rows 1-15, x 140-210: A plate, letters F/4/9)."""
    path = "/system/common/roulet_obj_drum.dcg"
    a, pal = load(path)
    star_banner(a[0:16, 0:108], "Mishap!")
    rowmode(a, 152, 207, 1, 13, skip=(15, 4, 9))
    m, s = fit("Got a Card!", 49, sizes=(10, 9, 8))
    paint(a, 177 - (m.shape[1] + 1) // 2, 3, m, bands((0, 15), (7, 4), (10, 9)))
    save(a, pal, path)


def disc(m, r):
    """Dilate by a round kernel (x*x + y*y <= r*r + r) so thick outlines keep rounded corners."""
    o = np.pad(m, r)
    out = np.zeros_like(o)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r + r:
                out |= np.roll(np.roll(o, dy, 0), dx, 1)
    return out


def big(t, x, y, m, layers, fill):
    """Layered display lettering: layers = [(radius, index, dy), ..] painted outermost first, then the letters."""
    for r, idx, dy in layers:
        paint(t, x - r, y - r + dy, disc(m, r) if r else m, idx)
    paint(t, x, y, m, fill)


def map_goal():
    """/system/common/map_goal.dcg (tw 32): end-of-trip banners. とうちゃく! (rows 4-39), ヒロインポイント ribbon +
    ゲット! (rows 48-90), ゴール! (rows 96-140), 1 2 3 ちゃく (rows 144-183), ゴールまで __ マス (x 160-222),
    ゴールした人だけボーナス (rows 200-207), ペアボーナス / デートボーナス (rows 210-223)."""
    path = "/system/common/map_goal.dcg"
    a, pal = load(path)
    # とうちゃく! -> Arrived! (hearts at x < 20 and x > 137 stay)
    a[0:42, 20:138] = 0
    a[0:15, 138:142] = 0
    m, s = fit("Arrived!", 100, sizes=(24, 22, 20, 18))
    h = cap(s)
    big(a, 79 - m.shape[1] // 2, 22 - h // 2, m, [(5, 15, 3), (5, 15, 0), (4, 3, 3), (4, 1, 0), (2, 15, 0)],
        bands((0, 5), (22 - h // 2 + h // 3, 6), (22 - h // 2 + 2 * h // 3, 7)))
    # ribbon: ヒロインポイント -> Heroine Points (F on the 5/6/7 striped plate)
    rowmode(a, 37, 124, 50, 63, skip=(15, 9))
    m, s = fit("Heroine Points", 82, sizes=(11, 10, 9))
    paint(a, 79 - m.shape[1] // 2, 53 if cap(s) >= 8 else 54, m, 15)
    # ゲット! -> Up! (stars left of x 76 and right of x 130 stay)
    a[64:90, 76:131] = 0
    m = mono("Up!", 18)
    big(a, 80, 70, m, [(3, 15, 2), (3, 15, 0), (2, 1, 2), (2, 1, 0)],
        bands((0, 4), (70 + cap(18) // 2, 3)))
    # ゴール! -> Goal!
    a[92:120, 31:142] = 0
    a[120:138, 31:132] = 0
    a[96:104, 26:31] = 0
    m, s = fit("Goal!", 84, sizes=(30, 28, 26, 24))
    h = cap(s)
    y = 117 - h // 2
    grad = [11, 12, 13, 14, 14, 13, 12, 11]
    big(a, 80 - m.shape[1] // 2, y, m, [(5, 15, 3), (5, 15, 0), (4, 4, 3), (4, 1, 0), (2, 15, 0)],
        lambda Y: grad[min(7, max(0, (Y - y) * 8 // max(1, m.shape[0])))])
    # 1 2 3 + ordinal suffix at the lower right of each digit; ちゃく -> Place
    for k, suf in enumerate(("st", "nd", "rd")):
        m = small(suf, bold=True)
        big(a, 30 * k + 30 - m.shape[1] // 2 - (0 if k == 0 else 4), 169, m, [(2, 5, 0), (1, 15, 0)], 1)
    a[142:186, 96:160] = 0
    m, s = fit("Place", 60, sizes=(16, 15, 14))
    big(a, 127 - m.shape[1] // 2, 164 - cap(s) // 2, m, [(3, 5, 1), (2, 15, 0)], bands((0, 7), (165, 5)))
    # ゴールまで -> To Goal ; マス -> left (F on dark 1 plates)
    rowmode(a, 166, 211, 148, 159, skip=(15, 3, 4))
    m = small("To Goal", bold=True)
    paint(a, 188 - m.shape[1] // 2, 150, m, 15)
    rowmode(a, 202, 220, 164, 171, skip=(15, 3, 4))
    m = small("left")
    paint(a, 211 - m.shape[1] // 2, 164, m, 15)
    # ゴールした人だけボーナス -> BONUS FOR FINISHERS (tiny caps on the 2 plate)
    rowmode(a, 162, 237, 201, 207, skip=(15, 4))
    m = tiny("BONUS FOR FINISHERS")
    paint(a, 199 - m.shape[1] // 2, 201, m, 15)
    # ペアボーナス / デートボーナス: F text with 3 bumps on the 2/1 bar
    for x0, x1, word in ((3, 73, "Pair Bonus"), (132, 205, "Date Bonus")):
        a[208:213, x0:x1] = 0
        rowmode(a, x0, x1, 213, 222, skip=(15, 4))
        m, s = fit(word, x1 - x0 - 4, sizes=(10, 9))
        paint(a, x0 + 3, 213, m, 15, ring=3)
        a[216:222, x0:x1][a[216:222, x0:x1] == 3] = 2
    save(a, pal, path)


STAR = (7, 9, 10, 11)  # yellow star colours of the roulette result banners


def success(a, dy):
    """せいこう! -> Success!: blue 3/2/1 letters on a white plate with a dark 1 drop; stars at both ends stay."""
    box = a[dy + 11:dy + 37, 22:113]
    box[~np.isin(box, STAR)] = 0
    m, s = fit("Success!", 78, sizes=(18, 17, 16, 14))
    h = cap(s)
    y = dy + 23 - h // 2
    big(a, 64 - m.shape[1] // 2, y, m, [(3, 1, 2), (3, 15, 0)], bands((0, 3), (y + h // 3, 2), (y + 2 * h // 3, 1)))


def strip(a, y0, word, x0=None, plate=12, tailc=14, m=None, ty=2):
    """Stat name strip: F text (default tiny caps) on a plate (rows y0+1..y0+8) ending in a tail of colour tailc."""
    row = a[y0 + 5]
    e = [x for x in range(a.shape[1]) if row[x] == tailc]
    tail = e[-1]
    while tail - 1 in e:
        tail -= 1
    if x0 is None:
        x0 = int(np.nonzero(a[y0:y0 + 9].any(0))[0][0])
    m = tiny(word) if m is None else m
    need = x0 + m.shape[1] + 4
    if need > tail:  # push the tail (and the strip's baseline) right to make room
        d = need - tail
        end = int(np.nonzero(a[y0:y0 + 10, tail:].any(0))[0][-1]) + tail + 1
        blk = a[y0:y0 + 10, tail:end].copy()
        a[y0:y0 + 10, tail + d:end + d] = blk
        a[y0 + 9, end:end + d] = plate
        tail = need
    a[y0 - 2:y0 + 1, x0:tail] = 0
    a[y0 + 1:y0 + 9, x0:tail] = plate
    t = a[y0 - 2:y0 + 9, tail:tail + 8]
    t[(t == 15) | ((t == plate) & (np.arange(t.shape[0])[:, None] < 6))] = 0  # last kana's strokes over the tail
    paint(a, x0 + 2, y0 + ty, m, 15)


def status_icons():
    """/system/common/status_obj_icon.dcg (tw 32): stat names (うたうちから, まけないこころ, けいかいなステップ,
    ヒロインポイント) as F text on a 1 plate with a 3/2 tail; status_obj_goukei.dcg (ヒロインポイント / ごうけい
    badge); status_obj_pts.dcg (ランダムポイント beside "pts")."""
    path = "/system/common/status_obj_icon.dcg"
    a, pal = load(path)
    for y0, w in ((4, "Singing Power"), (20, "Unbeatable Heart"), (36, "Nimble Steps"), (52, "Heroine Points")):
        m = small(w)
        if m.shape[1] > 52:
            m = tiny(w.upper())
        strip(a, y0, w, plate=1, tailc=3, m=m, ty=1 if m.shape[0] >= 7 else 2)
    save(a, pal, path)
    path = "/system/common/status_obj_goukei.dcg"
    a, pal = load(path)
    a[0:9, 9:54] = 0  # ヒロイン sticks out above the badge
    rowmode(a, 9, 54, 9, 23, skip=(15, 5, 6))
    for y, w in ((11, "HEROINE"), (17, "POINTS")):
        m = tiny(w)
        paint(a, 31 - m.shape[1] // 2, y, m, 15, ring=5)
    rowmode(a, 8, 54, 24, 38, skip=(15,))
    m = small("Total", bold=True)
    paint(a, 31 - m.shape[1] // 2, 27, m, 15, ring=5)
    save(a, pal, path)
    path = "/system/common/status_obj_pts.dcg"
    a, pal = load(path)
    a[5:19, 6:32] = 10
    for y, w in ((6, "RANDOM"), (12, "POINTS")):
        m = tiny(w)
        paint(a, 19 - m.shape[1] // 2, y, m, 15)
    save(a, pal, path)


BOARD = [  # (top row, x of the top edge run start/end, English) for every name pill on /map/map.imb
    (152, 56, 110, "Rina's House"), (166, 1180, 1266, "Pearl Piari"), (179, 563, 611, "Library"),
    (192, 784, 841, "Sports Center"), (215, 406, 476, "Concert Hall"), (340, 766, 806, "School"),
    (364, 280, 359, "Shopping Mall"), (386, 500, 569, "Fountain Plaza"), (441, 10, 58, "Church"),
    (574, 720, 802, "Central Park"), (613, 171, 214, "Shrine"), (617, 1218, 1299, "Mermaid Cave"),
    (647, 377, 437, "Kaito's House"), (730, 989, 1081, "Cape Lookout"), (735, 880, 960, "Seaside Park"),
    (764, 756, 811, "Beach House"), (779, 10, 104, "Mr. Mitsuki's House"), (783, 189, 254, "Aqua Place"),
    (789, 474, 563, "Surfing Beach")]


def board():
    """/map/map.imb (8bpp, tw 180 = 1440x960 board): blue name pills (05 edge, BF rim, 65 inside, BF text with
    05 ring, glyph rows y+3..y+9). Pills are rebuilt as wide as the English needs (5x7 caps), centred on the
    original; the original end caps are reused."""
    path = "/map/map.imb"
    a, pal = load(path)
    mid = np.array([5, 0xBF] + [0x65] * 9 + [0xBF, 5], np.uint8)
    for y, x0, x1, word in BOARD:
        lcap = a[y:y + 13, x0 - 2:x0 + 4].copy()
        rcap = a[y:y + 13, x1 - 3:x1 + 3].copy()
        m = small(word.upper())
        old = (x1 + 3) - (x0 - 2)
        w = max(old, m.shape[1] + 14)
        nx = min(max((x0 - 2 + x1 + 3) // 2 - w // 2, 0), a.shape[1] - w)
        for x in range(nx, nx + w):
            a[y:y + 13, x] = mid
        for src, x in ((lcap, nx), (rcap, nx + w - 6)):
            keep = src != 0  # caps carry the board art around the round corners: copy all of it
            a[y:y + 13, x:x + 6][keep] = src[keep]
        paint(a, nx + (w - m.shape[1]) // 2, y + 3, m, 0xBF, ring=5)
    save(a, pal, path)


def board_map():
    """/map/map_l.imb (8bpp 240x160, View Map): caption ぴちぴちピッチボードマップ (BF letters, 05 ring) above the
    BF/05 bracket line at rows 154-155. Old letters are filled from the art just above them."""
    path = "/map/map_l.imb"
    a, pal = load(path)
    for x in range(113, 234):
        for y in range(142, 154):
            if a[y, x] in (5, 0xBF):
                a[y, x] = 0x65 if y >= 147 else a[141, x]
    m = mono("Pichi Pichi Pitch Board Map", 8)
    paint(a, 173 - m.shape[1] // 2, 146, m, 0xBF, ring=5)
    save(a, pal, path)


def roulet_ev():
    """/system/event/roulet_ev.dcg, roulet_ev0.dcg, roulet_ev1.dcg (tw 32): roulette challenge results
    (せいこう! / しっぱい……) and stat strips (けいかいなステップ, まけないこころ, うたうちから)."""
    path = "/system/event/roulet_ev.dcg"
    a, pal = load(path)
    success(a, 16)
    strip(a, 12, "NIMBLE STEPS", x0=180)
    # ごうけい (roulette total) strip: two 8-row sprites stacked on screen, top = x 176-207, bottom = x 208-255
    # of rows 24-31. Rebuilt as one 48x16 strip, then split back.
    v = np.zeros((16, 48), np.uint8)
    v[0:8, 0:32] = a[24:32, 176:208]
    v[8:16] = a[24:32, 208:256]
    e = [x for x in range(48) if v[10, x] == 14]
    tail = e[-1]
    while tail - 1 in e:
        tail -= 1
    v[0:4, :tail] = 0
    v[4:13, :tail] = 12
    t = v[0:11, tail:]
    t[t == 15] = 0
    m = tiny("TOTAL")
    paint(v, 3, 6, m, 15)
    a[24:32, 176:208] = v[0:8, 0:32]
    a[24:32, 208:256] = v[8:16]
    save(a, pal, path)
    path = "/system/event/roulet_ev0.dcg"
    a, pal = load(path)
    for y0, w in ((12, "NIMBLE STEPS"), (36, "UNBEATABLE HEART"), (60, "SINGING POWER")):
        strip(a, y0, w)
    save(a, pal, path)
    path = "/system/event/roulet_ev1.dcg"
    a, pal = load(path)
    success(a, 0)
    a[46:72, 16:116] = 0
    m, s = fit("Failed...", 90, sizes=(16, 15, 14, 13))
    h = cap(s)
    y = 58 - h // 2
    big(a, 64 - m.shape[1] // 2, y, m, [(2, 5, 2), (2, bands((0, 7), (y + h // 3, 6), (y + 2 * h // 3, 5)), 0)],
        15)
    save(a, pal, path)


PARTS = {"board": board, "board_map": board_map, "map_goal": map_goal, "roulet_ev": roulet_ev, "status_icons": status_icons, "titlebars": titlebars, "modetitle": modetitle, "map_mokuteki": map_mokuteki, "mokuteki": mokuteki,
         "destination": destination, "yesno": yesno, "roulet_obj": roulet_obj, "map_rank": map_rank,
         "status_obj": status_obj, "roulet_obj_drum": roulet_obj_drum}

if __name__ == "__main__":
    for p in (sys.argv[1:] or PARTS):
        PARTS[p]()
        print("redrew", p)
