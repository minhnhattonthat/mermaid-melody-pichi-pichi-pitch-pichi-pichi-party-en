"""English graphics for the title group: Konami/copyright screen, title logo, "press START", mode select and
title menus, name entry header.  Writes gfx/en/<name>.png from gfx/orig/<name>.png (palette-mode, colour indices).
    python -X utf8 tools/gfx/redraw_title.py            (report: docs/re/gfx_title.md)
Originals: export.py exports (OBJ sheets with --tw 32: these files are loaded 1:1 into 2D-mapped OBJ VRAM), except
title_logo.acg (8bpp OBJ + IS-ACG03 trailer), which this script exports itself (orig_acg()):
    export.py /mode/k_logo/logo.dcg ; export.py /mode/title/title_logo01.dcg ; export.py /mode/title/name.imb
    export.py /mode/title/title_obj.dcg|title_serect.dcg|title_menu.dcg --tw 32 --pal <menu dump>.pal.bin --obj --bank 11
(the --pal choice only colours the PNG for viewing; pixel values are what is written back).
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
    right = [(48, "New Game", 128), (64, "Continue", 128), (80, "Three Players", 125), (96, "Party Pitch", 125),
             (112, "All-Out Pitch", 125), (128, "Hard Rules", 125), (144, "Easy Rules", 125)]
    for y0, text, tx0 in right:
        pill_label(a, y0, tx0, 202, text)
    save(path, a, pal)


def title_menu():
    path = "/mode/title/title_menu.dcg"
    a, pal = load(path)
    heads = ["Mode Select", "Checking Link", "Players", "Character Select", "Game Length", "Load Save",
             "Story...", "Turn Order"]
    for i, text in enumerate(heads):
        header(a, 16 * i, text, 0, 160)
    save(path, a, pal)


def aa_text(text, font, size):
    """Anti-aliased coverage (0..1 float array), row 0 = cap top."""
    f = ImageFont.truetype(FONTS + font, size)
    top = f.getbbox("H")[1]
    bot = f.getbbox("gjpqy,")[3]
    x0, _, x1, _ = f.getbbox(text)
    im = Image.new("L", (x1 - x0 + 2, bot - top + 1), 0)
    ImageDraw.Draw(im).text((1 - x0, -top), text, font=f, fill=255)
    return np.array(im) / 255.0


def k_logo():
    """Copyright line 1 (OBJ 240x8 at rows 1-8, ramp: 15 paper .. 1 ink). The (C) glyph (x 3-15) moves 3 px left
    to make room for the English (Arial Narrow 9, anti-aliased onto the ramp)."""
    path = "/mode/k_logo/logo.dcg"
    a, pal = load(path)
    cg = a[0:11, 3:16].copy()
    a[0:11, 0:240] = 15
    a[0:11, 0:13] = cg
    c = aa_text("Kodansha, We've, TV Aichi / Pichi Pichi Pitch Production Committee", "ARIALN.TTF", 9)[:10]
    assert 13 + c.shape[1] <= 241, c.shape
    idx = np.rint(15 - c * 14).astype(np.uint8)
    h, w = idx.shape
    reg = a[1:1 + h, 13:13 + w]
    np.copyto(reg, np.minimum(reg, idx[:, :240 - 13]))
    save(path, a, pal)


def press_start():
    """/mode/title/title_logo01.dcg rows 0-15: "PUSH START" prompt; fill a/9/8/7, rings 2|1 then 1, shadow b."""
    path = "/mode/title/title_logo01.dcg"
    a, pal = load(path)
    a[0:16, 0:160] = 0
    m, cap = ttf("Press START!", "tahomabd.ttf", 15)
    fill = lambda row: 0xa if row <= 6 else 0x9 if row <= 8 else 0x8 if row <= 10 else 0x7
    inner = lambda row: 0x2 if row <= 8 else 0x1
    styled(a, 77 - m.shape[1] // 2, 12 - cap, m, fill, [(1, inner), (1, 0x1)], shadow=(-1, 2, 0xb, {0}))
    save(path, a, pal)


def nearest(pal, rgb, allowed=None):
    p = np.array(pal[:768], dtype=int).reshape(-1, 3)
    d = ((p - np.array(rgb)) ** 2).sum(1)
    if allowed is not None:
        mask = np.full(len(p), True)
        mask[list(allowed)] = False
        d[mask] = 1 << 30
    return int(d.argmin())


def name_entry():
    """/mode/title/name.imb (8bpp BG 240x160): header "カートリッジになまえをつけてね" (white letters in a dark
    teal block, rows 13-27) and the help bar words (1-px white font, rows 150-157). The kana grid stays."""
    path = "/mode/title/name.imb"
    a, pal = load(path)
    p = np.array(pal[:768], dtype=int).reshape(-1, 3)
    used = set(np.unique(a).tolist())
    white = 223
    # header: outline colour per row from the old block, then paint over by vertical interpolation of the sky
    ring = {}
    for y in range(13, 28):
        v = [int(x) for x in a[y, 40:200] if x not in (221, 222, 223)]
        ring[y] = max(set(v), key=v.count)
    y0, y1, x0, x1 = 12, 28, 26, 212
    for x in range(x0, x1):
        top, bot = p[a[y0, x]], p[a[y1, x]]
        for y in range(y0 + 1, y1):
            t = (y - y0) / (y1 - y0)
            a[y, x] = nearest(pal, top * (1 - t) + bot * t, used)
    m, cap = ttf("Name your cartridge!", "tahomabd.ttf", 15)
    top = 25 - cap
    ink = lambda row: ring[min(max(row, 13), 27)]
    styled(a, 120 - m.shape[1] // 2, top, m, white, [(1, ink)], shadow=(1, 1, ink))
    # help bar: words after "SELECT:", "A:", "B:"
    for (wx0, wx1), word in [((106, 133), "Title"), ((155, 182), "OK"), ((206, 234), "Back")]:
        a[148:159, wx0:wx1] = a[148:159, wx1:wx1 + 1]   # the bar is a vertical gradient: repeat the clean column
        mm, _ = pix(word)
        put(a, wx0 + 1, 150, mm, white)
    save(path, a, pal)


# ------------------------------------------------------------------ title logo (/mode/title/title_logo.acg)
# 8bpp OBJ, 2D mapping: the file is 128 px wide (16 tiles of 64 bytes per 1 KB VRAM row) followed by a 0x460-byte
# IS-ACG03 trailer (LINK/CMNT/MODE/SIZE/VER records), kept as pixels in the last rows. Palette title_logo.dcl
# (OBJ 0-239; 224-239 are overwritten by title_logo01's bank, so the logo only uses 0-223).
ACG = "/mode/title/title_logo.acg"
# (sheet x, y, w, h) -> canvas x, y, back to front. At rest the Party block (OAM 0-3, 256x64) is at screen (0, 48)
# and the Pitch block (OAM 4-8 at (32, 16), OAM 9-11 at (32.., 8) behind them) gives a 176x40 canvas at (32, 8).
PARTY = [(0, 0, 64, 64, 0, 0), (64, 0, 64, 64, 64, 0), (0, 64, 64, 64, 128, 0), (64, 64, 64, 64, 192, 0)]
PITCH = [(48, 160, 32, 16, 32, 0), (80, 160, 32, 16, 64, 0), (112, 160, 16, 8, 96, 0),
         (0, 128, 64, 32, 0, 8), (64, 128, 32, 32, 64, 8), (96, 128, 32, 32, 96, 8), (0, 160, 32, 32, 128, 8),
         (32, 160, 16, 32, 160, 8)]
# one canvas = screen (0, 8)-(256, 112); the Pitch cloud's bottom rows are drawn by the Party sprites
LOGO = [(x, y, w, h, cx + 32, cy) for x, y, w, h, cx, cy in PITCH] + \
       [(x, y, w, h, cx, cy + 40) for x, y, w, h, cx, cy in PARTY]


def orig_acg():
    rom = open(os.path.join(apply.ROOT, "work", "orig.gba"), "rb").read()
    o, s = fs.get(rom, ACG)
    data = rom[o:o + s] + bytes(-s % 1024)
    px = gfx.tiles_to_pixels(data, 8, 16)
    pal = gfx.palette(rom, "/mode/title/title_logo.dcl") + [(0, 0, 0)] * 16
    im = Image.new("P", (128, len(px)))
    im.putpalette([c for rgb in pal for c in rgb])
    im.putdata([v for row in px for v in row])
    im.save(os.path.join(apply.ORIGD, apply.name_of(ACG)))
    apply.save_layout(ACG, {"tw": 16, "bpp": 8})


def gather(a, rects, w, h):
    c = np.zeros((h, w), np.uint8)
    ok = np.zeros((h, w), bool)
    for x, y, rw, rh, cx, cy in rects:   # later sprites have priority where they are not transparent
        src = a[y:y + rh, x:x + rw]
        dst = c[cy:cy + rh, cx:cx + rw]
        dst[src != 0] = src[src != 0]
        ok[cy:cy + rh, cx:cx + rw] = True
    return c, ok


def scatter(a, c, rects):
    for x, y, rw, rh, cx, cy in rects:
        a[y:y + rh, x:x + rw] = c[cy:cy + rh, cx:cx + rw]


def logo():
    if not os.path.exists(os.path.join(apply.ORIGD, apply.name_of(ACG))):
        orig_acg()
    a, pal = load(ACG)
    P = np.array(pal[:768], dtype=int).reshape(-1, 3)
    used = set(int(v) for v in np.unique(a[:192])) - {0}
    used = {v for v in used if v < 224}
    col = lambda rgb: nearest(pal, rgb, used)
    c, ok = gather(a, LOGO, 256, 104)
    logo_party(c[40:], P, col)
    logo_pitch(c, ok, P, col)
    scatter(a, c, LOGO)
    save(ACG, a, pal)


def logo_party(c, P, col):
    """ぴちぴちパーティー on the ribbon -> "Pichi Pichi Party". The kana sit in one merged pink outline (3 px pink,
    1 px light blue, 1 px lavender). That outline blob becomes a pink plate (its outer 2 px kept) and the English
    letters (Bauhaus 93, yellow gradient, 1 px pink ring) are drawn inside it."""
    rgb = P[c]
    yellow = (rgb[..., 0] >= 232) & (rgb[..., 1] >= 176) & (rgb[..., 2] <= 200) & (c != 0)
    lab, n = ndimage.label(yellow)
    core = np.zeros_like(yellow)
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        if len(ys) >= 30 and ys.min() >= 8:
            core |= lab == i
    blob = ndimage.binary_dilation(core, iterations=3, structure=np.ones((3, 3))) & (c != 0)
    plate = col((232, 56, 144))
    c[blob] = plate
    ys, xs = np.nonzero(blob)
    bx0, bx1, by0, by1 = xs.min(), xs.max(), ys.min(), ys.max()
    text = "Pichi Pichi Party"
    size = 34
    while True:
        m = ttf(text, "BAUHS93.TTF", size)[0]
        if m.shape[1] <= bx1 - bx0 - 6:
            break
        size -= 1
    # stretch to the kana's height (chunky like the original lettering)
    th = min(by1 - by0 - 8, m.shape[0] * 6 // 5)
    m = np.array(Image.fromarray(m * 255).resize((m.shape[1], th), Image.NEAREST)) // 255
    cy0, cy1 = np.nonzero(core.any(1))[0][[0, -1]]
    x = (bx0 + bx1 + 1 - m.shape[1]) // 2
    y = (cy0 + cy1 + 1 - m.shape[0]) // 2
    grad = [(248, 248, 200), (248, 248, 160), (248, 240, 120), (248, 240, 64), (248, 232, 24), (248, 216, 32),
            (248, 192, 48)]
    gi = [col(g) for g in grad]
    h = m.shape[0]
    fill = lambda row: gi[min(len(gi) - 1, max(0, (row - y) * len(gi) // h))]
    # where the English needs more plate than the kana had: plate edge as the original (light blue, lavender)
    notplate = set(range(256)) - {plate}
    put(c, x - 5, y - 5, dil(m, 5), col((200, 168, 208)), notplate)
    put(c, x - 4, y - 4, dil(m, 4), col((136, 216, 248)), notplate)
    styled(c, x, y, m, fill, [(1, col((240, 88, 160))), (2, plate)])


def logo_pitch(c, ok, P, col):
    """Pitch block: マーメイドメロディー (rainbow kana) / Pichi Pichi Pitch (small) / ぴちぴちピッチ (big pink) on a
    white cloud with a cyan rim. The cloud keeps its rim; inside: "Mermaid Melody" (rainbow letters) and
    "Pichi Pichi Pitch" (big pink, Bauhaus 93)."""
    win = np.zeros_like(ok)
    win[0:48, 30:212] = True
    lab, _ = ndimage.label(ndimage.binary_fill_holes((c != 0) & win))
    cloud = lab == lab[24, 128]
    # big line "Pichi Pichi Pitch" (rows 21-39) and "Mermaid Melody" above it, both centred on screen x 120
    big = pixfont.trim_rows(ttf("Pichi Pichi Pitch", "BAUHS93.TTF", 21)[0])
    bx, by = 120 - big.shape[1] // 2, 40 - big.shape[0]
    text = "Mermaid Melody"
    ms = [ttf(ch, "BAUHS93.TTF", 13)[0] if ch != " " else np.zeros((1, 4), np.uint8) for ch in text]
    ms = [g[:np.nonzero(g.any(1))[0].max() + 1] if g.any() else g for g in ms]   # drop empty descender rows
    w = sum(g.shape[1] for g in ms) + len(ms) - 1
    hh = max(g.shape[0] for g in ms)
    tx, ty = 120 - w // 2, by - 1 - hh
    assert ty >= 11, ty   # rows 0-7 exist only left of x 112 (OAM 9-11)
    # the cloud grows to hold the English (old outline kept where it is larger), 1 px blue rim, white inside
    grow = np.zeros_like(cloud)
    grow[by:by + big.shape[0], bx:bx + big.shape[1]] |= big.astype(bool)
    grow[ty:ty + hh, tx:tx + w] = True
    yy, xx = np.mgrid[-5:6, -5:6]
    grow = ndimage.binary_dilation(grow, structure=yy * yy + xx * xx <= 22)   # round corners
    lim = np.zeros_like(ok)
    lim[0:44, 36:205] = True
    cloud = ndimage.binary_fill_holes(cloud | (grow & lim)) & ok
    inner = ndimage.binary_erosion(cloud, structure=np.ones((3, 3)))
    c[cloud] = col((0, 168, 240))
    c[inner] = col((248, 248, 248))
    pinks = [col((240, 120, 176)), col((240, 88, 160)), col((232, 40, 144)), col((216, 16, 120))]
    h = big.shape[0]
    styled(c, bx, by, big, lambda row: pinks[min(3, max(0, (row - by) * 4 // h))], [(1, col((168, 16, 104)))])
    # one colour per letter, as the kana of マーメイドメロディー
    rainbow = [col(v) for v in [(232, 32, 32), (248, 144, 56), (216, 176, 0), (96, 184, 48), (0, 160, 232),
                                (136, 88, 208), (232, 32, 136)]]
    k, x = 0, tx
    for ch, g in zip(text, ms):
        if ch != " ":
            put(c, x, ty, g, rainbow[k % len(rainbow)])
            k += 1
        x += g.shape[1] + 1


GROUPS = {"title_obj": title_obj, "title_serect": title_serect, "title_menu": title_menu, "k_logo": k_logo,
          "press_start": press_start, "name_entry": name_entry, "logo": logo}
# /system/common/modetitle.dcg (board ribbons, verified on the board) is drawn by redraw_board.py.

if __name__ == "__main__":
    for g in (sys.argv[1:] or GROUPS):
        GROUPS[g]()
        print("redrew", g)
