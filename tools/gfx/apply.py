"""Graphics import: every gfx/en/<name>.png replaces the file it was exported from (same size, written in place).

<name> = file path with "/" -> "__" and the extension kept (e.g. system__title__ev000000.dcg.png).
PNGs are palette-mode ("P") images whose pixel values ARE the tile colour indices (4bpp: 0-15; 8bpp: 0-255);
their size must be the export size (tools/gfx/export.py), whose tile width is recorded in gfx/layout.json.
    python -X utf8 tools/gfx/export.py PATH [--tw N] [--pal PALFILE_OR_DUMP --bank B]   -> gfx/orig/<name>.png
    python -X utf8 tools/gfx/apply.py --check   (decode/encode roundtrip of every exported original; exit 1 on error)
"""
import glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import fs, gfx  # noqa: E402
from PIL import Image  # noqa: E402

EN = os.path.join(ROOT, "gfx", "en")
ORIGD = os.path.join(ROOT, "gfx", "orig")
LAYOUT = os.path.join(ROOT, "gfx", "layout.json")


def path_of(png):
    return "/" + os.path.basename(png)[:-4].replace("__", "/")


def name_of(path):
    return path.strip("/").replace("/", "__") + ".png"


def layout():
    return json.load(open(LAYOUT)) if os.path.exists(LAYOUT) else {}


def file_bytes(rom, path, png):
    """Encode PNG indices into the file's byte layout (header kept from the ROM)."""
    o, s = fs.get(rom, path)
    data = bytes(rom[o:o + s])
    lay = layout().get(path, {})
    hdr = data[:12] if gfx.has_header(data) else b""
    bpp = lay.get("bpp", 4)
    im = Image.open(png)
    if im.mode != "P":
        raise ValueError(f"{png}: must be a palette-mode PNG of colour indices")
    w, h = im.size
    px = [list(im.getdata())[y * w:(y + 1) * w] for y in range(h)]
    if bpp == 4 and max(max(r) for r in px) > 15:
        raise ValueError(f"{png}: index > 15 in a 4bpp file")
    body = gfx.pixels_to_tiles(px, bpp)
    n = s - len(hdr)
    if len(body) < n:  # export pads the last tile row; drop the padding
        raise ValueError(f"{png}: image smaller than the file ({len(body)} < {n})")
    if any(body[n:]):
        raise ValueError(f"{png}: drawing in the padding past the file end")
    return hdr + body[:n]


def apply(rom, alloc=None):
    n = 0
    for png in sorted(glob.glob(os.path.join(EN, "*.png"))):
        path = path_of(png)
        o, s = fs.get(rom, path)
        rom[o:o + s] = file_bytes(rom, path, png)
        n += 1
    return n


def check():
    rom = open(os.path.join(ROOT, "work", "orig.gba"), "rb").read()
    bad = 0
    for png in sorted(glob.glob(os.path.join(ORIGD, "*.png"))):
        path = path_of(png)
        o, s = fs.get(rom, path)
        try:
            if file_bytes(rom, path, png) != rom[o:o + s]:
                print("roundtrip differs:", path); bad += 1
        except ValueError as x:
            print(x); bad += 1
    for png in sorted(glob.glob(os.path.join(EN, "*.png"))):
        try:
            file_bytes(rom, path_of(png), png)
        except (ValueError, KeyError) as x:
            print("en:", x); bad += 1
    print("gfx check", "ok" if not bad else f"{bad} errors")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(check())
