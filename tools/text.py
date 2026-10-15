"""Text containers: dump to script/*.json, identity re-encode, and build translated files.

Containers (all in the DFI file system, tools/fs.py):
  event  /event/ev*.bin: {u32 3, (off,size) x3} bytecode | u32 string offsets (bytes into strings) | strings
  bms    *.bms (+ *.bmh = u32 byte offsets into the .bms); without .bmh the strings are read in sequence
Strings: u16 codes, 0x8000 ends, 0x8001 = newline.

Markup (jp and en): "\\n" = 8001; tbl/jp.tbl characters ({iXXX} icons, {hX} half-width); [XXXX] any raw code.
English: printable ASCII is encoded as the half-width codes 0x4000|(c+0x10), drawn by the VWF (tools/vwf.py).

    python -X utf8 tools/text.py dump [--force]     -> script/event/*.json, script/bms/*.json
    python -X utf8 tools/text.py identity           re-encode jp, compare with the ROM (exit 1 on mismatch)
    python -X utf8 tools/text.py stats
"""
import glob, json, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import fs  # noqa: E402
import mktbl  # noqa: E402

SCRIPT = os.path.join(ROOT, "script")
ORIG = os.path.join(ROOT, "rom", "Mermaid Melody - Pichi Pichi Pitch - Pichi Pichi Party (Japan).gba")
END, NL = 0x8000, 0x8001
SKIP = {"/event/ev000111.bin", "/event/ev990000.bin"}  # unterminated stub / scrambled test data: left as is

TBL = mktbl.table()
REV = {}
for _c, _ch in sorted(TBL.items()):
    REV.setdefault(_ch, _c)


# ------------------------------------------------------------------ codec
def decode(codes):
    out = []
    for c in codes:
        if c == NL:
            out.append("\n")
        elif c in TBL and REV[TBL[c]] == c and c != 0x4000 | 0x5B + 0x10:  # dup glyphs and half '[' stay raw
            out.append(TBL[c])
        else:
            out.append("[%04X]" % c)
    return "".join(out)


TOK = re.compile(r"\[[0-9A-F]{4}\]|\{[ih].{1,3}?\}|\n|.", re.S)


def encode(markup, lang="jp"):
    """-> list of codes (without the 0x8000 end)."""
    out = []
    for t in TOK.findall(markup):
        if t == "\n":
            out.append(NL)
        elif len(t) == 6 and t[0] == "[" and re.fullmatch(r"\[[0-9A-F]{4}\]", t):
            out.append(int(t[1:5], 16))
        elif lang != "jp" and len(t) == 1 and 0x20 <= ord(t) < 0x7F:
            out.append(0x4000 | (ord(t) + 0x10))
        elif t in REV:
            out.append(REV[t])
        else:
            raise ValueError(f"unencodable {t!r} in {markup[:40]!r}")
    return out


def read_codes(rom, p):
    out = []
    while True:
        c = struct.unpack_from("<H", rom, p)[0]
        if c == END:
            return out
        out.append(c)
        p += 2


def pack(codes):
    return struct.pack("<%dH" % (len(codes) + 1), *codes, END)


# ------------------------------------------------------------------ containers
def event_parts(rom, off):
    n = struct.unpack_from("<I", rom, off)[0]
    assert n == 3
    (bo, bs), (to, ts), (so, ss) = [struct.unpack_from("<II", rom, off + 4 + 8 * k) for k in range(3)]
    offs = [struct.unpack_from("<I", rom, off + to + 4 * k)[0] for k in range(ts // 4)]
    return (bo, bs, to, ts, so, ss), offs


def strings_in(rom, base, size):
    """Sequential strings in [base, base+size): list of (rel offset, codes); stops at zero padding."""
    res, q = [], 0
    while q < size:
        if not any(rom[base + q:base + size]):
            break
        codes = read_codes(rom, base + q)
        res.append((q, codes))
        q += 2 * len(codes) + 2
    return res


def containers(rom):
    """-> list of (kind, path, data) where data describes the strings."""
    F = {p: (o, s) for p, i, e, o, s in fs.files(rom)}
    out = []
    for p, (o, s) in F.items():
        if p in SKIP:
            continue
        if p.startswith("/event/") and p.endswith(".bin"):
            hdr, offs = event_parts(rom, o)
            out.append(("event", p, (o, s, hdr, offs)))
        elif p.endswith(".bms"):
            h = p[:-1] + "h"
            offs = None
            if h in F:
                ho, hs = F[h]
                offs = [struct.unpack_from("<I", rom, ho + 4 * k)[0] for k in range(hs // 4)]
            out.append(("bms", p, (o, s, offs)))
    return out


def name_of(path):
    return path.strip("/").replace("/", "_").rsplit(".", 1)[0]


def json_path(kind, path):
    return os.path.join(SCRIPT, kind, name_of(path) + ".json")


def dump_one(rom, kind, path, data):
    if kind == "event":
        o, s, (bo, bs, to, ts, so, ss), offs = data
        strs = strings_in(rom, o + so, ss)
    else:
        o, s, offs = data
        strs = strings_in(rom, o, s) if offs is None else None
        if offs is not None:
            seen = sorted(set(offs))
            strs = [(q, read_codes(rom, o + q)) for q in seen]
    ents = []
    for q, codes in strs:
        idx = [k for k, x in enumerate(offs) if x == q] if offs is not None else []
        ents.append({"id": "%s:%04X" % (name_of(path), q), "idx": idx, "jp": decode(codes), "en": ""})
    return ents


def dump(force=False):
    rom = open(ORIG, "rb").read()
    n = 0
    for kind, path, data in containers(rom):
        jp = json_path(kind, path)
        if os.path.exists(jp) and not force:
            continue
        ents = dump_one(rom, kind, path, data)
        os.makedirs(os.path.dirname(jp), exist_ok=True)
        with open(jp, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"path": path, "kind": kind, "strings": ents}, f, ensure_ascii=False, indent=1)
        n += 1
    print(n, "files dumped")


def load_all():
    res = []
    for jp in sorted(glob.glob(os.path.join(SCRIPT, "*", "*.json"))):
        res.append((jp, json.load(open(jp, encoding="utf-8"))))
    return res


# ------------------------------------------------------------------ rebuild
def rebuild(rom, doc, lang=None, marker=False, en_of=None):
    """Return new file bytes for one container. lang None = jp (identity); en_of(ent) -> markup or None."""
    path = doc["path"]
    o, s = fs.get(rom, path)
    ents = doc["strings"]

    def codes_for(e):
        if lang:
            m = en_of(e) if en_of else e.get("en")
            if m:
                return encode(m, "en")
        return encode(e["jp"], "jp")

    blob, newoff = bytearray(), {}
    for e in ents:
        q = int(e["id"].rsplit(":", 1)[1], 16)
        newoff[q] = len(blob)
        blob += pack(codes_for(e))
    if doc["kind"] == "event":
        hdr, offs = event_parts(rom, o)
        bo, bs, to, ts, so, ss = hdr
        if lang is None:  # identity: keep the original padding
            blob += b"\0" * (ss - len(blob))
        else:
            blob += b"\0" * (-len(blob) % 16)
        table = b"".join(struct.pack("<I", newoff[x]) for x in offs)
        assert len(table) == ts
        out = bytearray(rom[o:o + so])
        out[to:to + ts] = table
        struct.pack_into("<II", out, 4 + 16, so, len(blob))
        out += blob
        return bytes(out), None
    # bms (+ bmh)
    h = path[:-1] + "h"
    try:
        ho, hs = fs.get(rom, h)
        offs = [struct.unpack_from("<I", rom, ho + 4 * k)[0] for k in range(hs // 4)]
    except KeyError:
        offs = None
    if lang is None:
        blob += rom[o + len(blob):o + s]
    bmh = b"".join(struct.pack("<I", newoff[x]) for x in offs) if offs is not None else None
    return bytes(blob), bmh


def identity():
    rom = open(ORIG, "rb").read()
    bad = 0
    for jp, doc in load_all():
        o, s = fs.get(rom, doc["path"])
        new, bmh = rebuild(rom, doc)
        if new != rom[o:o + s]:
            print("identity mismatch", doc["path"]); bad += 1
        if bmh is not None:
            ho, hs = fs.get(rom, doc["path"][:-1] + "h")
            if bmh != rom[ho:ho + hs]:
                print("identity mismatch", doc["path"][:-1] + "h"); bad += 1
    print("identity", "ok" if not bad else f"{bad} mismatches")
    return 1 if bad else 0


def stats():
    n = u = chars = done = 0
    seen = set()
    for jp, doc in load_all():
        for e in doc["strings"]:
            n += 1
            if e["jp"] not in seen:
                seen.add(e["jp"]); u += 1; chars += len(e["jp"])
            done += bool(e.get("en"))
    print(f"strings {n}, unique {u} ({chars} chars), translated {done}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "dump":
        dump("--force" in sys.argv)
    elif cmd == "identity":
        sys.exit(identity())
    elif cmd == "stats":
        stats()
    else:
        sys.exit(__doc__)
