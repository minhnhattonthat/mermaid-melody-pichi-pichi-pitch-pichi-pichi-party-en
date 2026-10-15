"""View a graphics file at a given tile width: python -X utf8 tools/gfx/rawview.py PATH TW OUT.png [ZOOM] [BANK|-1]"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import fs  # noqa: E402
import gfxfmt as gfx  # noqa: E402

rom = open(os.path.join(os.path.dirname(os.path.dirname(HERE)), "work", "orig.gba"), "rb").read()
p, tw, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
z = int(sys.argv[4]) if len(sys.argv) > 4 else 2
bank = int(sys.argv[5]) if len(sys.argv) > 5 else 0
o, s = fs.get(rom, p)
d = rom[o:o + s]
if gfx.has_header(d):
    d = d[12:]
px = gfx.tiles_to_pixels(d, 4, tw)
pal = gfx.own_palette(rom, p)
im = gfx.to_image(px, pal if bank >= 0 else None, max(bank, 0), 4)
im.resize((im.width * z, im.height * z)).save(out)
print(out)
