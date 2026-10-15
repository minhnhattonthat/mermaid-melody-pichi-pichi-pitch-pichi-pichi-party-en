"""Export a graphics file as a palette-mode PNG of its colour indices (for editing; import: tools/gfx/apply.py).
    python -X utf8 tools/gfx/export.py PATH [--tw N] [--pal FSPATH.dcl|DUMP.pal.bin] [--bank B] [--obj] [--out PNG]
--tw     tiles per row (default: header width, 30/32 for .imb, else 16). For OBJ data use the sprite width.
--pal    palette: a palette file of the file system (.dcl/.plb/.acl) or a PPU dump (*.pal.bin, 0x400 bytes;
         --obj picks the OBJ half). --bank B = 16-colour bank (4bpp). Default: own .dcl/.plb, bank 0.
Writes gfx/orig/<name>.png (unless --out) and records {tw, bpp} in gfx/layout.json.
"""
import json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import fs, apply  # noqa: E402
import gfxfmt as gfx  # noqa: E402
from PIL import Image  # noqa: E402


def bgr(words):
    return [((c & 31) << 3, ((c >> 5) & 31) << 3, ((c >> 10) & 31) << 3) for c in words]


def main():
    a = sys.argv[1:]
    path = a[0]
    rom = open(os.path.join(apply.ROOT, "work", "orig.gba"), "rb").read()
    o, s = fs.get(rom, path)
    data = rom[o:o + s]
    px, bpp, lay = gfx.decode(rom, path)
    tw = len(px[0]) // 8
    if "--tw" in a:
        tw = int(a[a.index("--tw") + 1])
        body = data[12:] if gfx.has_header(data) else data
        px = gfx.tiles_to_pixels(body, bpp, tw)
    bank = int(a[a.index("--bank") + 1]) if "--bank" in a else 0
    if "--pal" in a:
        src = a[a.index("--pal") + 1]
        if src.endswith(".bin"):
            raw = open(src, "rb").read()
            raw = raw[0x200:0x400] if "--obj" in a else raw[:0x200]
            pal = bgr(struct.unpack("<256H", raw))
        else:
            pal = gfx.palette(rom, src)
    else:
        pal = gfx.own_palette(rom, path) or [(v * 17, v * 17, v * 17) for v in range(16)]
    base = bank * 16 if bpp == 4 else 0
    cols = (pal[base:base + (16 if bpp == 4 else 256)] + [(255, 0, 255)] * 256)[:256]
    im = Image.new("P", (len(px[0]), len(px)))
    im.putpalette([c for rgb in cols for c in rgb])
    im.putdata([v for row in px for v in row])
    out = a[a.index("--out") + 1] if "--out" in a else os.path.join(apply.ORIGD, apply.name_of(path))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    im.save(out)
    apply.save_layout(path, {"tw": tw, "bpp": bpp})
    print(out, f"{len(px[0])}x{len(px)} bpp{bpp}")


if __name__ == "__main__":
    main()
