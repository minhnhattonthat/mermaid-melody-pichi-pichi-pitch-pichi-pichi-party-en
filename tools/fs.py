"""DFI file system (Pichi Pichi Party): directory at ROM 0x2E0000 ("DFI\\0" header, then 16-byte entries).

Entry i at E = 0x2E0010 + 16*i: {s16 child (entries to first child, 0 = file), s16 next (entries to next sibling,
0 = last), u32 name (offset from E to a NUL-terminated name), u32 data (file offset = 0x2F0000 + 4*data), u32 size}.
Lookup by path: 0x08043E68 (root ptr in RAM 0x0201E464). Files are stored uncompressed, 4-byte aligned.

    python -X utf8 tools/fs.py ROM [--grep TEXT]        list path, entry index, file offset, size
    python -X utf8 tools/fs.py ROM --get PATH --out F   extract one file
"""
import struct, sys

FS, DATA = 0x2E0000, 0x2F0000


def entry(rom, i):
    e = FS + 0x10 + 16 * i
    child, nxt, n, d, s = struct.unpack_from("<hhIII", rom, e)
    name = rom[e + n:rom.index(b"\0", e + n)].decode()
    return e, child, nxt, name, d, s


def files(rom):
    """-> list of (path, entry index, entry offset, file offset, size)."""
    out = []

    def walk(i, path):
        while True:
            e, child, nxt, name, d, s = entry(rom, i)
            if child:
                walk(i + child, path + name.rstrip("/") + "/")
            else:
                out.append((path + name, i, e, DATA + 4 * d, s))
            if not nxt:
                return
            i += nxt
    walk(0, "")
    return out


def get(rom, path):
    for p, i, e, off, s in files(rom):
        if p == path:
            return off, s
    raise KeyError(path)


def set_file(rom, path, off, size):
    """Point `path` at a new file offset (must be >= DATA and 4-aligned) and size."""
    assert off >= DATA and off % 4 == 0, hex(off)
    for p, i, e, o, s in files(rom):
        if p == path:
            struct.pack_into("<II", rom, e + 8, (off - DATA) // 4, size)
            return
    raise KeyError(path)


if __name__ == "__main__":
    rom = open(sys.argv[1], "rb").read()
    if "--get" in sys.argv:
        off, s = get(rom, sys.argv[sys.argv.index("--get") + 1])
        open(sys.argv[sys.argv.index("--out") + 1], "wb").write(rom[off:off + s])
        print(hex(off), hex(s))
    else:
        g = sys.argv[sys.argv.index("--grep") + 1] if "--grep" in sys.argv else ""
        for p, i, e, off, s in files(rom):
            if g in p:
                print(f"{i:5d} {off:#08x} {s:#7x} {p}")
