"""Graphics files of the DFI file system -> indexed images and back.

Formats (found by size/headers; see docs/re/graphics.md):
  .imb  8bpp tiles (64 bytes each), 30 or 32 tiles per row (+ .plb palette, BGR555);
        4bpp when the .plb holds <= 16 colours (staff roll).
  .dcg  with header {u16 0x0400, u16 ?, u16 0, u16 ?, u16 w, u16 h} (12 bytes): w*h 4bpp tiles, row-major.
        without header: raw 4bpp tiles (OBJ/BG char data), shown 16 tiles per row.
  .dcl/.acl  BGR555 palettes (16 colours per bank).
    python -X utf8 tools/gfx/gfx.py survey OUTDIR [--grep TEXT]   PNG per image file (grey or own palette)
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import fs  # noqa: E402
from PIL import Image  # noqa: E402


def palette(rom, path):
    o, s = fs.get(rom, path)
    return [((c & 31) << 3, ((c >> 5) & 31) << 3, ((c >> 10) & 31) << 3) for c in struct.unpack_from("<%dH" % (s // 2), rom, o)]


def has_header(data):
    if len(data) < 12 or data[:2] != b"\x00\x04":
        return False
    w, h = struct.unpack_from("<HH", data, 8)
    return 12 + w * h * 32 == len(data)


def tiles_to_pixels(data, bpp, tw):
    tb = 32 if bpp == 4 else 64
    n = len(data) // tb
    th = (n + tw - 1) // tw
    px = [[0] * (tw * 8) for _ in range(th * 8)]
    for t in range(n):
        bx, by = (t % tw) * 8, (t // tw) * 8
        for y in range(8):
            row = data[t * tb + y * (tb // 8):t * tb + (y + 1) * (tb // 8)]
            for x in range(8):
                v = (row[x >> 1] >> (4 * (x & 1))) & 15 if bpp == 4 else row[x]
                px[by + y][bx + x] = v
    return px


def pixels_to_tiles(px, bpp):
    tw, th = len(px[0]) // 8, len(px) // 8
    out = bytearray()
    for t in range(tw * th):
        bx, by = (t % tw) * 8, (t // tw) * 8
        for y in range(8):
            if bpp == 4:
                for x in range(0, 8, 2):
                    out.append(px[by + y][bx + x] | (px[by + y][bx + x + 1] << 4))
            else:
                out += bytes(px[by + y][bx:bx + 8])
    return bytes(out)


def decode(rom, path):
    """-> (pixels, bpp, layout) ; layout = dict to re-encode."""
    o, s = fs.get(rom, path)
    data = rom[o:o + s]
    if path.endswith(".imb"):
        try:
            ncol = fs.get(rom, path[:-3] + "plb")[1] // 2
        except KeyError:
            ncol = 256
        bpp = 4 if ncol <= 16 else 8
        tb = 32 if bpp == 4 else 64
        n = s // tb
        tw = 30 if n % 30 == 0 else 32
        return tiles_to_pixels(data, bpp, tw), bpp, {"hdr": b""}
    if has_header(data):
        w, h = struct.unpack_from("<HH", data, 8)
        return tiles_to_pixels(data[12:], 4, w), 4, {"hdr": data[:12]}
    return tiles_to_pixels(data, 4, 16), 4, {"hdr": b""}


def encode(px, bpp, layout):
    return layout["hdr"] + pixels_to_tiles(px, bpp)


def to_image(px, pal=None, bank=0, bpp=4):
    h, w = len(px), len(px[0])
    im = Image.new("RGB", (w, h))
    if pal:
        base = bank * 16 if bpp == 4 else 0
        cols = [pal[base + v] if base + v < len(pal) else (255, 0, 255) for v in range(256 if bpp == 8 else 16)]
    else:
        cols = [(v * 17, v * 17, v * 17) for v in range(16)] if bpp == 4 else [(v, v, v) for v in range(256)]
    im.putdata([cols[v] for row in px for v in row])
    return im


def own_palette(rom, path):
    for ext in ("plb", "dcl", "acl"):
        try:
            return palette(rom, path.rsplit(".", 1)[0] + "." + ext)
        except KeyError:
            pass
    d = path.rsplit("/", 1)[0]
    for p, i, e, o, s in fs.files(rom):
        if p.startswith(d + "/") and p.endswith(".dcl"):
            return palette(rom, p)
    return None


if __name__ == "__main__":
    rom = open(os.path.join(os.path.dirname(os.path.dirname(HERE)), "work", "orig.gba"), "rb").read()
    if sys.argv[1] == "survey":
        out = sys.argv[2]
        g = sys.argv[sys.argv.index("--grep") + 1] if "--grep" in sys.argv else ""
        os.makedirs(out, exist_ok=True)
        for p, i, e, o, s in fs.files(rom):
            if g in p and p.endswith((".imb", ".dcg", ".acg")) and s:
                px, bpp, lay = decode(rom, p)
                pal = own_palette(rom, p)
                im = to_image(px, pal, 0, bpp)
                im.save(os.path.join(out, p.strip("/").replace("/", "_") + ".png"))
        print("ok")
