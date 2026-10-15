"""Leftover-Japanese scan of a BUILT ROM, following the file system the game uses (pointer-reachable text only).
    python -X utf8 tools/jpscan.py BUILT.gba      exit 1 on any unexpected Japanese
Checks: every string of every event script and .bms file the DFI directory points at; the code-table slots of
tools/romdata.py; the name-entry grid. KNOWN lists text that stays Japanese on purpose.
"""
import os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fs, text, romdata  # noqa: E402

KNOWN = {  # path: reason
    "/event/ev000002.bin": "developer glyph-test script (unreachable)",
    "/event/ev000003.bin": "developer glyph-test script (unreachable)",
    "/event/ev000006.bin": "scrambled test data (unreachable)",
    "/event/ev000111.bin": "unterminated stub (unreachable)",
    "/event/ev990000.bin": "scrambled test data (unreachable)",
    "/system/textbin/numeric.bms": "digit glyph table (data)",
}
JP = re.compile(r"[぀-ヿ一-鿿]")


def main(path):
    rom = open(path, "rb").read()
    bad = 0
    for kind, p, data in text.containers(rom) + [("event", k, None) for k in ()]:
        if p in KNOWN:
            continue
        o = data[0]
        if kind == "event":
            hdr, offs = text.event_parts(rom, o)
            starts = [o + hdr[4] + x for x in offs]
        else:
            offs = data[2]
            starts = [o + x for x in offs] if offs is not None else [o + q for q, _ in text.strings_in(rom, o, data[1])]
        for a in starts:
            s = text.decode(text.read_codes(rom, a))
            if JP.search(s):
                print(f"{p} +{a - o:#x}: {s[:60]!r}"); bad += 1
    for off, n, en in romdata.ROM_SLOTS:
        s = text.decode(struct.unpack_from("<%dH" % n, rom, off))
        if JP.search(s):
            print(f"table {off:#x}: {s!r}"); bad += 1
    g = text.decode(struct.unpack_from("<60H", rom, romdata.NAME_GRID))
    if JP.search(g):
        print("name grid:", g); bad += 1
    print("jpscan:", "clean" if not bad else f"{bad} Japanese strings", f"({len(KNOWN)} known exceptions)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
