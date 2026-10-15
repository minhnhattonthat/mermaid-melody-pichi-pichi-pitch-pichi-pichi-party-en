"""Map ctxlog.lua lines (renderer calls) to the text files their string pointer lies in, and list window variants.
    python -X utf8 tools/winmap.py LOG [ROM]   -> per (chars per line n, lines): files seen
"""
import collections, re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fs

rom = open(sys.argv[2] if len(sys.argv) > 2 else "work/orig.gba", "rb").read()
F = sorted((o, o + s, p) for p, i, e, o, s in fs.files(rom))
starts = [f[0] for f in F]
import bisect
win = collections.defaultdict(collections.Counter)
for line in open(sys.argv[1]):
    m = re.search(r" R ctx=(\w+) .* xy=(\d+),(\d+) n=(\d+) lines=(\d+) .* str=(\w+)", line)
    if not m:
        continue
    a = int(m.group(6), 16) & 0x1FFFFFF
    k = bisect.bisect_right(starts, a) - 1
    name = F[k][2] if k >= 0 and F[k][0] <= a < F[k][1] else ("RAM %08X" % int(m.group(6), 16) if m.group(6).startswith("02") or m.group(6).startswith("03") else "ROM %06X" % a)
    win[(int(m.group(4)), int(m.group(5)), m.group(2), m.group(3))][re.sub(r"\d{2}(\.|_)", r"##\1", name)] += 1
for k in sorted(win):
    print("n=%d lines=%d at %s,%s:" % k, dict(win[k]))
