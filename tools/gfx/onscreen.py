"""Which graphics files are loaded in a VRAM dump? (tiles matched by content; blank/solid tiles ignored)
    python -X utf8 tools/gfx/onscreen.py DUMP.vram.bin [DUMP2 ..] [--rom work/orig.gba]
Prints per file: tiles matched, VRAM region (BG chars / OBJ), file tile range.
"""
import collections, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import fs  # noqa: E402
import gfxfmt as gfx  # noqa: E402

GFX_EXT = (".dcg", ".acg", ".imb", ".bst")


def index(rom):
    idx = collections.defaultdict(list)
    for p, i, e, o, s in fs.files(rom):
        if not p.endswith(GFX_EXT) or not s:
            continue
        base = o + (12 if gfx.has_header(rom[o:o + s]) else 0)
        for t in range(0, s - (base - o) - 31, 32):
            tile = rom[base + t:base + t + 32]
            if len(set(tile)) > 2:
                idx[tile].append((p, t // 32))
    return idx


def main():
    a = sys.argv[1:]
    rom = open(a[a.index("--rom") + 1] if "--rom" in a else "work/orig.gba", "rb").read()
    idx = index(rom)
    for d in [x for x in a if x.endswith(".vram.bin")]:
        v = open(d, "rb").read()
        hits = collections.defaultdict(list)
        for t in range(0, len(v), 32):
            for p, k in idx.get(v[t:t + 32], [])[:3]:
                hits[p].append((t, k))
        print("==", d)
        for p, h in sorted(hits.items(), key=lambda x: -len(x[1])):
            vr = "OBJ" if h[0][0] >= 0x10000 else "BG"
            print(f"{len(h):5d} {vr} vram {h[0][0]:#07x}-{h[-1][0]:#07x} tiles {min(k for _, k in h)}-{max(k for _, k in h)}  {p}")


if __name__ == "__main__":
    main()
