"""One entry point.
    python -X utf8 tools/build.py build [--marker] [--out PATH]   -> build/mmppp2_en.gba (32 MiB)
    python -X utf8 tools/build.py check                          -> identity + text lint (pre-commit)
Free space after expansion to 32 MiB:
  0x1000000-0x1800000  text files (relocated through the DFI directory), font, VWF code
  0x1800000-0x2000000  graphics
"""
import hashlib, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
ORIG = os.path.join(ROOT, "rom", "Mermaid Melody - Pichi Pichi Pitch - Pichi Pichi Party (Japan).gba")
SIZE = 0x2000000
TEXT_LO, GFX_LO = 0x1000000, 0x1800000


class Alloc:
    """Bump allocator over a free ROM window; raises when it would overflow."""
    def __init__(self, rom, lo, hi, align=4):
        self.rom, self.p, self.hi, self.align = rom, lo, hi, align

    def put(self, data, align=None):
        a = align or self.align
        self.p = (self.p + a - 1) & ~(a - 1)
        if self.p + len(data) > self.hi:
            raise RuntimeError(f"free space overflow at {self.p:#x} (+{len(data):#x} > {self.hi:#x})")
        off = self.p
        self.rom[off:off + len(data)] = data
        self.p += len(data)
        return off


def load_orig():
    import check_rom
    check_rom.check()
    return open(ORIG, "rb").read()


def build(marker=False, qa=None):
    import fs, text, font_en, vwf
    rom = bytearray(load_orig())
    rom += b"\xff" * (SIZE - len(rom))
    alloc = Alloc(rom, TEXT_LO, GFX_LO)
    import romdata
    adv, eng = font_en.tables()
    romdata.patch_rom(rom)
    qa = dict(qa or {})
    for sid, codes in romdata.sysstat_codes(rom, lambda s: text.encode(s, "jp")).items():
        qa.setdefault(sid, text.decode(codes))
    adv_off = vwf.install(rom, alloc, adv, eng, romdata.ext_codes(lambda s: text.encode(s, "en")))
    import patches
    patches.apply(rom, alloc, adv_off, lambda s: text.encode(s, "en"))
    orig = bytes(rom)
    en_of = text.marker_of if marker else None
    for jp, doc in text.load_all():
        new, bmh = text.rebuild(orig, doc, lang="en", en_of=en_of, qa=qa)
        o, s = fs.get(orig, doc["path"])
        if new != orig[o:o + s]:
            fs.set_file(rom, doc["path"], alloc.put(new), len(new))
        if bmh is not None:
            h = doc["path"][:-1] + "h"
            ho, hs = fs.get(orig, h)
            if bmh != orig[ho:ho + hs]:
                fs.set_file(rom, h, alloc.put(bmh), len(bmh))
    gfx = os.path.join(HERE, "gfx", "apply.py")
    if os.path.exists(gfx):
        import importlib
        importlib.import_module("gfx.apply").apply(rom, Alloc(rom, GFX_LO, SIZE))
    return rom


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    if cmd == "build":
        marker = "--marker" in sys.argv
        out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else \
            os.path.join(ROOT, "build", f"mmppp2_en{'_marker' if marker else ''}.gba")
        rom = build(marker)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "wb").write(rom)
        print("built", out, hashlib.sha1(rom).hexdigest())
    elif cmd == "check":
        import text
        r = text.identity()
        r |= text.lint()
        sys.exit(r)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
