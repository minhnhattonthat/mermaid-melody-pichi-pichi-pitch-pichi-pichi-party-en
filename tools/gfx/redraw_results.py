"""Results / episode clear / staff roll graphics -> English (gfx/en/*.png). Rerun to regenerate all of them.
    python -X utf8 tools/gfx/redraw_results.py
Files: /mode/result/{res_ep_bg_0,cmd_res,cmd_stag}.imb (8bpp BG pictures), /mode/result/result_obj.dcg (OBJ, 2D
mapping, 32 tiles per row), /mode/ending/staff_roll.imb (4bpp, 240x1600). Exports: tools/gfx/export.py (result_obj
with --tw 32). Report: docs/re/gfx_results.md.
"""
import os, sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import redraw  # noqa: E402
import pixfont  # noqa: E402

FONTS = redraw.FONTS
ROUND = "ARLRDBD.TTF"  # Arial Rounded MT Bold: closest to the game's rounded headings


# ------------------------------------------------------------------ helpers
def load(path):
    im = redraw.load(path)
    return np.array(im), np.array(im.getpalette()[:768]).reshape(-1, 3), im


def save(a, im, path):
    out = Image.new("P", (a.shape[1], a.shape[0]))
    out.putdata(a.astype(np.uint8).ravel().tolist())
    out.putpalette(im.getpalette())
    redraw.save(out, path)


def tmask(text, font, size, thresh=128):
    """Unantialiased text mask with a fixed vertical frame: returns (mask, cap_top, baseline) in mask rows."""
    f = ImageFont.truetype(FONTS + font, size, layout_engine=ImageFont.Layout.BASIC)
    asc, desc = f.getmetrics()
    w = int(f.getlength(text)) + 4
    im = Image.new("L", (w, asc + desc + 2), 0)
    ImageDraw.Draw(im).text((1, 1), text, font=f, fill=255)
    m = (np.array(im) >= thresh).astype(np.uint8)
    cols = np.nonzero(m.any(0))[0]
    m = m[:, cols.min():cols.max() + 1] if len(cols) else m[:, :0]
    h = Image.new("L", (40, asc + desc + 2), 0)
    ImageDraw.Draw(h).text((1, 1), "H", font=f, fill=255)
    rows = np.nonzero((np.array(h) >= thresh).any(1))[0]
    return m, rows.min(), rows.max()


def dil(m, r, diag=True):
    return pixfont.dilate(m.astype(np.uint8), r, diag)


def put(a, x, y, m, v):
    """v: an index, or a per-row function y -> index."""
    H, W = a.shape
    for yy, xx in zip(*np.nonzero(m)):
        X, Y = x + xx, y + yy
        if 0 <= X < W and 0 <= Y < H:
            a[Y, X] = v(Y) if callable(v) else v


def nearest(pal, rgb, allowed):
    d = ((pal[allowed] - np.array(rgb)) ** 2).sum(1)
    return allowed[int(d.argmin())]


def inpaint_rows(a, pal, mask, allowed):
    """Fill masked pixels row by row: linear blend of the nearest unmasked pixels left and right, snapped to the
    nearest allowed palette colour (the backgrounds here are vertical gradients, so rows interpolate cleanly)."""
    allowed = np.array(allowed)
    H, W = a.shape
    for y in range(H):
        xs = np.nonzero(mask[y])[0]
        if not len(xs):
            continue
        row = a[y].copy()
        x = 0
        while x < W:
            if not mask[y, x]:
                x += 1
                continue
            x0 = x
            while x < W and mask[y, x]:
                x += 1
            L = pal[row[x0 - 1]] if x0 > 0 else None
            R = pal[row[x]] if x < W else None
            if L is None:
                L = R
            if R is None:
                R = L
            n = x - x0 + 1
            for i in range(x0, x):
                t = (i - x0 + 1) / n
                a[y, i] = nearest(pal, L * (1 - t) + R * t, allowed)
    return a


def fill_holes(m):
    """Mark pixels enclosed by m (not reachable from the border through ~m)."""
    H, W = m.shape
    seen = np.zeros_like(m, bool)
    st = [(y, x) for y in range(H) for x in (0, W - 1)] + [(y, x) for x in range(W) for y in (0, H - 1)]
    while st:
        y, x = st.pop()
        if 0 <= y < H and 0 <= x < W and not seen[y, x] and not m[y, x]:
            seen[y, x] = True
            st += [(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)]
    return ~seen


def row_modes(a, sel):
    """Per-row most common index among selected pixels -> dict y -> index (rows without any are left out)."""
    out = {}
    for y in range(a.shape[0]):
        v = a[y][sel[y]]
        if len(v):
            out[y] = int(np.bincount(v).argmax())
    return out


def by_row(modes):
    ks = sorted(modes)
    return lambda y: modes[min(ks, key=lambda k: abs(k - y))]


def fit(text, font, maxw, maxcap, sizes=range(30, 7, -1)):
    for s in sizes:
        m, top, base = tmask(text, font, s)
        if m.shape[1] <= maxw and base - top + 1 <= maxcap:
            return s
    return sizes[-1]


# ------------------------------------------------------------------ BG pictures (8bpp)
def banner(a, pal, box, text, fill_px=None):
    """res_ep_bg_0 / cmd_res heading: white letters, 3-px blue outline shaded per row, 1-px pale halo."""
    x0, y0, x1, y1 = box
    sub = pal[a] // 8
    blue = (sub[..., 2] >= 0x1e) & (sub[..., 0] <= 0x12) & (sub[..., 1] <= 0x1a)
    boxm = np.zeros(a.shape, bool)
    boxm[y0:y1, x0:x1] = True
    blue &= boxm
    inside = fill_holes(blue) & boxm
    white = inside & ~blue
    outline = by_row(row_modes(a, blue))
    fillc = int(np.bincount(a[white]).argmax())
    halo = nearest(pal, (232, 244, 248), np.arange(len(pal)))
    ys = np.nonzero(white.any(1))[0]
    ftop, fbot = ys.min(), ys.max()                        # white letter rows of the original
    region = dil(inside, 2).astype(bool)[2:-2, 2:-2]
    allowed = sorted(set(np.unique(a[~boxm]).tolist()))
    inpaint_rows(a, pal, region, allowed)
    size = fit(text, ROUND, x1 - x0 - 8, fbot - ftop + 1)
    m, top, base = tmask(text, ROUND, size)
    cx = (x0 + x1) // 2 - m.shape[1] // 2
    y = ftop - top
    put(a, cx - 4, y - 4, dil(m, 4), halo)
    put(a, cx - 3, y - 3, dil(m, 3), outline)
    put(a, cx, y, m, fillc)
    return size


def bar_labels(a, pal, labels):
    """cmd_res column labels on the pink bar: white->yellow letters, dark blue outline (both shaded per row)."""
    sub = pal[a] // 8
    size = min(fit(t, ROUND, x1 - x0 - 4, 10) for (x0, x1), t in labels)   # one size for the whole bar
    for (x0, x1), text in labels:
        y0, y1 = 54, 70
        diff = np.zeros(a.shape, bool)
        for y in range(y0, y1):
            diff[y, x0:x1] = a[y, x0:x1] != a[y, 1]
        yel = diff & (sub[..., 0] >= 0x18) & (sub[..., 1] >= 0x18)
        dark = diff & ~yel
        fillc, outc = by_row(row_modes(a, yel)), by_row(row_modes(a, dark))
        ys = np.nonzero(yel.any(1))[0]
        ftop, fbot = ys.min(), ys.max()
        inpaint_rows(a, pal, diff, sorted(set(a[y0:y1, 0:3].ravel().tolist())))
        m, top, base = tmask(text, ROUND, size)
        x = x0 + 2 if text == "Episode" else (x0 + x1) // 2 - m.shape[1] // 2
        y = ftop - top
        sh = dil(m, 2)
        put(a, x - 2, y - 1, sh, outc)                      # drop shade under the outline
        put(a, x - 2, y - 2, sh, outc)
        put(a, x, y, m, fillc)


def plate(a, pal, box, text):
    """cmd_stag 'Today's Heroine': yellow letters with a dark brown outline on the wooden plate."""
    x0, y0, x1, y1 = box
    sub = pal[a] // 8
    diff = np.zeros(a.shape, bool)
    for y in range(y0, y1):
        diff[y, x0:x1] = a[y, x0:x1] != a[y, x0 - 2]
    yel = diff & (sub[..., 0] >= 0x14) & (sub[..., 1] >= 0x12)
    dark = diff & (sub[..., 0] <= 0x0a)
    fillc = by_row(row_modes(a, yel))
    outc = int(np.bincount(a[dark]).argmax())
    ys = np.nonzero(yel.any(1))[0]
    ftop, fbot = ys.min(), ys.max()
    inpaint_rows(a, pal, dil(diff, 1).astype(bool)[1:-1, 1:-1] & (np.arange(a.shape[0])[:, None] >= y0)
                 & (np.arange(a.shape[0])[:, None] < y1), sorted(set(a[y0:y1, x0 - 3:x0 - 1].ravel().tolist())))
    size = fit(text, ROUND, x1 - x0 - 4, fbot - ftop - 1)
    m, top, base = tmask(text, ROUND, size)
    x = (x0 + x1) // 2 - m.shape[1] // 2
    y = (ftop + fbot) // 2 - (top + base) // 2
    put(a, x - 1, y - 1, dil(m, 1), outc)
    put(a, x + 1, y + 1, m, outc)                          # 1-px drop shade like the original
    put(a, x, y, m, fillc)


def bg_pictures():
    p = "/mode/result/res_ep_bg_0.imb"
    a, pal, im = load(p)
    banner(a, pal, (44, 13, 208, 38), "Episode Clear!")
    save(a, im, p)

    p = "/mode/result/cmd_res.imb"
    a, pal, im = load(p)
    banner(a, pal, (44, 13, 200, 38), "Results")
    bar_labels(a, pal, [((3, 61), "Episode"), ((83, 123), "Lucia"), ((141, 181), "Hanon"), ((210, 238), "Rina")])
    save(a, im, p)

    p = "/mode/result/cmd_stag.imb"
    a, pal, im = load(p)
    plate(a, pal, (52, 14, 188, 34), "Today's Heroine")
    save(a, im, p)


# ------------------------------------------------------------------ OBJ sprites (result_obj.dcg, 2D 256x112)
def name_tag(a, x0, y0, w, text):
    """るちあ/はのん/リナ tags (bank 0): white letters, 2-px outline 7/6/5 shaded by row."""
    a[y0:y0 + 16, x0:x0 + w] = 0
    m = pixfont.render(text, bold=True)[:7]
    x = x0 + (w - m.shape[1]) // 2
    y = y0 + 4
    shade = lambda Y: 7 if Y - y0 < 7 else (6 if Y - y0 < 11 else 5)
    put(a, x - 2, y - 2, dil(m, 2), shade)
    put(a, x, y, m, 15)


def word_plates(a, x0, y0, h, lines, ys):
    """Board labels / エピソード (bank 3): bold white letters on a word-shaped blue plate (the original's per-row
    gradient) with a dark edge at the bottom right. h = sprite height, ys = top row of each line."""
    sel = np.isin(a[y0:y0 + h, x0:x0 + 48], [1, 2, 3, 4, 5, 6])
    grad = by_row(row_modes(a[y0:y0 + h, x0:x0 + 48], sel))
    a[y0:y0 + h, x0:x0 + 48] = 0
    for t, ly in zip(lines, ys):
        m = pixfont.trim_rows(pixfont.render(t, bold=True))
        assert m.shape[1] + 4 <= 48, t
        x = x0 + (48 - m.shape[1]) // 2
        y = y0 + ly
        put(a, x - 1, y - 1, dil(m, 2), 7)                  # dark edge = plate shifted (+1, +1)
        put(a, x - 2, y - 2, dil(m, 2), lambda Y: grad(Y - y0))
        put(a, x, y, m, 15)


def total_tag(a):
    """ヒロインポイントごうけい (bank 8, 64x48 at 144,48): pink box -> 'Heroine Points' small + 'Total' big."""
    x0, y0 = 144, 48
    s = a[y0:y0 + 48, x0:x0 + 64]
    s[7:10, 12:41] = 0                                     # drop the tab above the box
    for y, v in ((10, 15), (11, 7), (12, 6)):
        s[y, 11:41] = v
    star = np.zeros(s.shape, bool)                         # the two yellow stars on the box edges stay as drawn
    star[10:26, 0:11] = True
    star[10:26, 41:52] = True
    inner = np.zeros(s.shape, bool)
    inner[13:41, 3:47] = True
    s[inner & ~star] = 8
    for i, t in enumerate(("Heroine", "Points")):
        small = pixfont.render_tiny(t)
        xs = 26 - small.shape[1] // 2
        put(s, xs - 1, 13 + 6 * i, dil(small, 1), 5)
    for i, t in enumerate(("Heroine", "Points")):
        small = pixfont.render_tiny(t)
        put(s, 26 - small.shape[1] // 2, 14 + 6 * i, small, 15)
    m, top, base = tmask("Total", ROUND, fit("Total", ROUND, 34, 12))
    x = 25 - m.shape[1] // 2
    y = 27 - top
    put(s, x - 1, y - 1, dil(m, 1), 5)
    put(s, x + 1, y + 1, m, 6)
    put(s, x, y, m, 15)


def result_obj():
    p = "/mode/result/result_obj.dcg"
    a, pal, im = load(p)
    name_tag(a, 160, 0, 40, "Lucia")
    name_tag(a, 200, 0, 40, "Hanon")
    name_tag(a, 208, 64, 32, "Rina")
    for x0, lines in ((0, ["Board", "Map"]), (48, ["Last", "Battle"]), (96, ["Heroine", "Points"])):
        word_plates(a, x0, 16, 32, lines, (4, 19))
    word_plates(a, 208, 48, 16, ["Episode"], (4,))
    total_tag(a)
    save(a, im, p)


# ------------------------------------------------------------------ staff roll (4bpp, 240x1600)
SR_FONT, SR_SIZE = "tahoma.ttf", 11
A, B = 8, 128          # role column, name column

# (role, [names]) groups; '' role = continuation line. Tuples (x, text) place text freely on the line.
STAFF = [
    [("Staff", [])],
    [("Original Work", []), ("", [(-1, "Mermaid Melody Pichi Pichi Pitch")]),
     ("Original Concept", ["Kodansha, We've"]), ("Manga", ["Pink Hanamori"]), ("Scenario", ["Michiko Yokote"]),
     ("", [(-1, "(Serialized in Kodansha's Nakayoshi)")])],
    [("Cast", [(56, "Lucia Nanami"), (140, "Asumi Nakata")]), ("", [(56, "Hanon Hosho"), (140, "Hitomi Terakado")]),
     ("", [(56, "Rina Toin"), (140, "Mayumi Asano")])],
    [("Planning", ["Takashi Shimomichi"])],
    [("Production Cooperation", ["Atelier Double"])],
    [("Supervisor", ["Toshiro Inoue"]), ("Development Producer", ["Mitsunori Takahashi"]),
     ("Development Director", ["Katsuharu Suzuki"]), ("Development Planner", ["Satoshi Hirayae"])],
    [("Main Programming", ["Daisuke Taguchi"]), ("Programming", ["Hiroyasu Tamaki"]), ("", ["Tsuyoshi Morii"]),
     ("Sound Design", ["Ryohei Fujieda"]), ("Main Graphics", ["Kumiko Shimano"]),
     ("Graphics", ["Naoko Matsuda"]), ("", ["Kazuyuki Kurita"]), ("", ["Etsuko Kachi"]), ("Script", ["Hideki Fujii"])],
    [("Scenario", ["Elsewhere"]), ("", ["Toru Takasaki"]), ("", ["Mikan Takemoto"]), ("", ["Emi Shiina"]),
     ("", ["Haruka"]), ("", ["Kawataro Shoda"])],
    [("Key Art Cooperation", ["Marubatsu-gumi"]), ("", ["Hiroyuki Kawaguchi"]), ("", ["Makoto Takagi"]),
     ("", ["Hiroyuki Imai"])],
    [("Graphics Cooperation", ["Winds"]), ("", ["Hisashi Nanami"]), ("", ["Tomohiro Abe"])],
    [("Voice Recording", ["Jinnan Studio"])],
    [("Casting Cooperation", ["Zack Promotion"])],
    [("Manual Production", ["Hajime Yashiro"]), ("Package and Extras", ["Kenko Yonedo"]), ("Production", []),
     ("Illustration Production", ["Kenji Inoue"]), ("Website Production", ["Masato Ide"]),
     ("", ["Hiroaki Takahashi"])],
    [("Debugging", ["RMC"]), ("", ["Dreams"])],
    [("Insert Songs", [])],
    [("", [(16, '"Rainbow Notes"')]), ("", [(16, "Lyrics: Yukiko Mitsui"), (130, "Music: Seiji Katsu")])],
    [("", [(16, '"Legend of Mermaid"')]), ("", [(16, "Lyrics: Yukiko Mitsui"), (130, "Music: Koji Hayashi")])],
    [("", [(16, '"Beyond Our Dreams"')]), ("", [(16, "Lyrics: Yukiko Mitsui"), (130, "Music: Hiroyuki Ishida")])],
    [("", [(16, '"KIZUNA"')]), ("", [(16, "Lyrics: Tetsuya Fukuda"), (130, "Music: Seiji Katsu")])],
    [("", [(16, '"Paradise of the Sun ~Promised Land~"')]),
     ("", [(16, "Lyrics: Yukiko Mitsui"), (130, "Music: Tetsuya Ouchi")])],
    [("Special Thanks", [])],
    [("", [(40, "Kodansha")]), ("", [(40, "Kiyosumi Kawamoto"), (138, "Yuri Osawa")]),
     ("", [(40, "Takeyuki Shirato")])],
    [("", [(40, "Pony Canyon")])],
    [("", [(40, "We've")]), ("", [(40, "Hideyuki Kachi"), (138, "Rin Matsukuma")])],
    [("", [(40, "Konami")]), ("", [(40, "Masato Sakai"), (138, "Ayako Minagawa")]),
     ("", [(40, "Yuko Tamada"), (138, "Kanako Nakahara")])],
    [("", [(40, "Atelier Double")]), ("", [(40, "Tetsuo Tsuboi"), (138, "Aoi Momotani")]),
     ("", [(40, "Jun Kanda"), (138, "Masaaki Okubo")]), ("", [(40, "Atsutoshi Kojima"), (138, "Ayako Sorimachi")])],
    [("Product Coordinator", ["Noriaki Okamura"])],
    [("Producer", ["Takashi Shimomichi"])],
]
# the closing block keeps its original rows (centred)
FINALE = [(1486, "Production"), (1500, "Konami Computer Entertainment Japan"), (1522, "Publisher"),
          (1536, "Konami Corporation")]
PITCH, GAP, TOP, LIMIT = 13, 11, 160, 1478


def staff_lines():
    """-> [(y, [(x, text)])] ; y = row of the cap top."""
    out, y = [], TOP
    for g in STAFF:
        for role, names in g:
            items = [(A, role)] if role else []
            for n in names:
                items.append((B, n) if isinstance(n, str) else n)
            out.append((y, items))
            y += PITCH
        y += GAP
    assert y - GAP <= LIMIT, f"staff roll overflows: {y}"
    return out + [(fy, [("c", t)]) for fy, t in FINALE]


def staff_roll():
    p = "/mode/ending/staff_roll.imb"
    a, pal, im = load(p)
    ink = np.isin(a, [3, 4])
    near = np.zeros_like(ink)
    for dy in range(0, 3):
        for dx in range(-1, 3):
            near |= np.roll(np.roll(ink, dy, 0), dx, 1)
    erase = ink | (near & np.isin(a, [11, 14, 15]))
    inpaint_rows(a, pal, erase, [5, 6, 7, 8, 9, 10, 12, 13, 14, 15])
    for y, items in staff_lines():
        for x, t in items:
            m, top, base = tmask(t, SR_FONT, SR_SIZE)
            if x == "c":
                x = 120 - m.shape[1] // 2
            elif x == -1:
                x = 232 - m.shape[1]
            assert x + m.shape[1] <= 238, (t, x, m.shape[1])
            put(a, x + 1, y - top + 1, m, 15)               # white drop shadow (+1, +1)
            put(a, x, y - top, m, 3)
    # role column must not run into the name column
    for y, items in staff_lines():
        if len(items) > 1 and items[0][0] == A and items[1][0] == B:
            assert A + tmask(items[0][1], SR_FONT, SR_SIZE)[0].shape[1] < B - 2, items[0][1]
    save(a, im, p)


if __name__ == "__main__":
    bg_pictures()
    result_obj()
    staff_roll()
    print("redrew results")
