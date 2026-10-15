"""English proportional font for the VWF (tools/vwf.py). Glyph art: tools/font_glyphs.py (from the prequel repo;
12 rows, '#' body, '+' edge). Each glyph is drawn into a 16-row cell at row YOFF with a drop shadow at (+1, +1)
like the Japanese font (body nibble 1, shadow nibble 2). Advance = art width + 1; space = SPACE_W.

Codes: printable ASCII c -> 0x4000 | (c + 0x10) (the game's own half-width code space); EXTRA chars below use
free half-width slots. Digits 0x4000-0x4009 (the game's number glyphs) are drawn with our digits too.
"""
import os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from font_glyphs import G  # noqa: E402

YOFF = 2
SPACE_W = 3
EXTRA = {"é": 0x10, "…": 0x11, "♥": 0x12, "★": 0x13, "♪": 0x14, "×": 0x15}


def code_of(ch):
    if ch in EXTRA:
        return 0x4000 | EXTRA[ch]
    if 0x20 <= ord(ch) < 0x7F and ch in G:
        return 0x4000 | (ord(ch) + 0x10)
    return None


def h_map():
    """half-width slot -> glyph char."""
    m = {}
    for ch in G:
        c = code_of(ch)
        if c is not None:
            m[c & 0xFF] = ch
    for d in range(10):
        m[d] = str(d)
    return m


def advance(ch):
    if ch == " ":
        return SPACE_W
    return len(G[ch][0]) + 1


def cell(ch):
    """16 rows of 16 nibble values (0 empty, 1 body, 2 shadow)."""
    px = [[0] * 16 for _ in range(16)]
    for y, row in enumerate(G[ch]):
        for x, c in enumerate(row):
            if c in "#+":
                px[y + YOFF][x] = 1
    for y in range(15, -1, -1):
        for x in range(15, -1, -1):
            if px[y][x] == 1 and y + 1 < 16 and x + 1 < 16 and px[y + 1][x + 1] == 0:
                px[y + 1][x + 1] = 2
    return px


def tables():
    adv = bytearray(256)
    eng = bytearray(256 * 64)
    for h, ch in h_map().items():
        adv[h] = advance(ch)
        px = cell(ch)
        for y in range(16):
            v = 0
            for x in range(16):
                v |= px[y][x] << (2 * x)
            struct.pack_into("<I", eng, h * 64 + 4 * y, v)
    return bytes(adv), bytes(eng)


TOKEN = re.compile(r"\[[0-9A-F]{4}\]|\{[ih].{1,3}?\}|\n|.", re.S)


def line_widths(markup):
    """Pixel width of each line of an English markup string (full-width JP glyphs/icons count 12)."""
    ws, w = [], 0
    for t in TOKEN.findall(markup):
        if t == "\n":
            ws.append(w); w = 0
        elif t.startswith("[") and len(t) == 6:
            c = int(t[1:5], 16)
            w += 0 if c & 0x8000 else (8 if c & 0x4000 else 12)
        elif t.startswith("{h"):
            w += advance(" ") if t == "{h }" else 8
        elif t.startswith("{i"):
            w += 12
        elif t in G or t in EXTRA:
            w += advance(t)
        else:
            w += 12
    ws.append(w)
    return ws
