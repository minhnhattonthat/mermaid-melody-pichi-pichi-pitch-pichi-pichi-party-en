"""Generators for English graphics (one function per group). Each writes gfx/en/<name>.png (palette-mode indices)
from the exported original in gfx/orig/ (tools/gfx/export.py) so palettes and sizes stay exact.
    python -X utf8 tools/gfx/redraw.py [group ..]      (default: all groups)
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import apply  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

FONTS = "C:/Windows/Fonts/"


def load(path):
    im = Image.open(os.path.join(apply.ORIGD, apply.name_of(path)))
    return im


def save(im, path):
    os.makedirs(apply.EN, exist_ok=True)
    im.save(os.path.join(apply.EN, apply.name_of(path)))


def text_mask(text, font="comicbd.ttf", size=18, thresh=128):
    """1-bit mask (list of rows of 0/1) of text rendered without anti-aliasing (BASIC layout)."""
    f = ImageFont.truetype(FONTS + font, size, layout_engine=ImageFont.Layout.BASIC)
    x0, y0, x1, y1 = f.getbbox(text)
    im = Image.new("L", (x1 - x0 + 2, y1 - y0 + 2), 0)
    ImageDraw.Draw(im).text((1 - x0, 1 - y0), text, font=f, fill=255)
    w, h = im.size
    d = im.load()
    return [[1 if d[x, y] >= thresh else 0 for x in range(w)] for y in range(h)]


def dilate(m, r=1):
    h, w = len(m), len(m[0])
    out = [[0] * (w + 2 * r) for _ in range(h + 2 * r)]
    for y in range(h):
        for x in range(w):
            if m[y][x]:
                for dy in range(-r, r + 1):
                    for dx in range(-r, r + 1):
                        out[y + r + dy][x + r + dx] = 1
    return out


def stamp(im, x, y, m, ink):
    px = im.load()
    for yy, row in enumerate(m):
        for xx, v in enumerate(row):
            if v and 0 <= x + xx < im.width and 0 <= y + yy < im.height:
                px[x + xx, y + yy] = ink


def outlined(im, cx, cy, text, fill, ring, font="comicbd.ttf", size=18, r=1):
    """Draw text centred at (cx, cy) with an r-pixel ring."""
    m = text_mask(text, font, size)
    o = dilate(m, r)
    x, y = cx - len(o[0]) // 2, cy - len(o) // 2
    stamp(im, x, y, o, ring)
    stamp(im, x + r, y + r, m, fill)
    return len(o[0])


def fit_size(text, maxw, font, sizes):
    for s in sizes:
        m = text_mask(text, font, s)
        if len(m[0]) + 2 <= maxw:
            return s
    return sizes[-1]


# ------------------------------------------------------------------ groups
EPISODES = ["The Light of Love", "A Kitten's Wish", "Gentle Rain", "Flower Charm", "A Mermaid's Troubles",
            "Midsummer Mermaid", "The Hymn That Won't Start", "Summer Flowers", "Night of Courage", "Hippo's Secret",
            "A Gift of Sweets", "Cooked with Love", "Walking the Dogs", "Enchanting Melody", "Pajama Party",
            "Secret Time", "Colors of Flowers", "The Stolen Treasure", "A Gentle Song", "A Wish for Snow",
            "Beauty Contest Battle!", "Written Memories", "Love's Obstacle", "Love on the Run", "A Fiery Challenge",
            "The Vanished Penguin", "Romeo and Juliet", "Tanabata Wishes", "The Secret Letter",
            "The Valentine Ritual", "Gaito Returns", "The Final Battle"]


def wrap2(text, maxw, font, size):
    """One line if it fits, else the most balanced two-line split."""
    if len(text_mask(text, font, size)[0]) + 2 <= maxw:
        return [text]
    words = text.split()
    best = None
    for k in range(1, len(words)):
        a, b = " ".join(words[:k]), " ".join(words[k:])
        w = max(len(text_mask(a, font, size)[0]), len(text_mask(b, font, size)[0]))
        if best is None or w < best[0]:
            best = (w, [a, b])
    return best[1]


def ep_cards():
    """/system/title/evNNNN00.dcg: 208x96 episode title cards, index 0 background, 7 white fill, 1 red ring."""
    font = "comicbd.ttf"
    for n, title in enumerate(EPISODES):
        path = "/system/title/ev%04d00.dcg" % n
        orig = load(path)
        im = Image.new("P", orig.size, 0)
        im.putpalette(orig.getpalette())
        size = 25
        lines = wrap2(title, 200, font, size)
        while max(len(text_mask(l, font, size)[0]) for l in lines) + 2 > 204 and size > 14:
            size -= 1
            lines = wrap2(title, 200, font, size)
        if len(lines) == 1:
            outlined(im, 104, 50, lines[0], 7, 1, font, size)
        else:
            outlined(im, 104, 33, lines[0], 7, 1, font, size)
            outlined(im, 104, 64, lines[1], 7, 1, font, size)
        save(im, path)


GROUPS = {"ep_cards": ep_cards}

if __name__ == "__main__":
    for g in (sys.argv[1:] or GROUPS):
        GROUPS[g]()
        print("redrew", g)
