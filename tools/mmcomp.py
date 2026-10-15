"""Konami graphics codec used by Mermaid Melody (GBA): ARM routine at IWRAM 0x03000BA4 (ROM copy near 0x0051C0).

Stream = 1 flag byte, then commands until `size` output bytes are written:
  c>>6 == 0: (c&63)+1 literal bytes (a nonzero literal gets +add)
  c>>6 == 1: next byte d; copy (c&63)+2 bytes from distance d+1
  c>>6 == 2: copy 2 bytes from distance (c&63)+1
  c>>6 == 3: copy 1 byte  from distance (c&63)+1
flag bit0: after decoding, each 64-byte block gets 62 in-place swaps block[1+i] <-> block[TBL[i]],
TBL = ROM[0xEB0DA5 + (flag>>1):][:62] (IWRAM 0x03000B00.. is copied from ROM 0xEB0D80..).
Graphics are streamed as consecutive chunks: the routine returns the end of the chunk, the next chunk starts there.

    python -X utf8 tools/mmcomp.py dec ROM OFF SIZE [--n CHUNKS] [--add N] --out FILE
    python -X utf8 tools/mmcomp.py --selftest
"""
import argparse, sys

TBL_ROM = 0xEB0DA5


def _swaps(rom, flag):
    return rom[TBL_ROM + (flag >> 1):TBL_ROM + (flag >> 1) + 62]


def decompress(rom, off, size, add=0):
    """Decode one chunk at file offset `off`. Returns (bytes, end_offset)."""
    flag = rom[off]
    p = off + 1
    out = bytearray()
    while len(out) < size:
        c = rom[p]; p += 1
        n, t = (c & 63) + 1, c >> 6
        if t == 0:
            for b in rom[p:p + n]:
                out.append((b + add) & 0xFF if b else 0)
            p += n
        elif t == 1:
            d = rom[p] + 1; p += 1
            for _ in range(n + 1):
                out.append(out[-d])
        elif t == 2:
            out.append(out[-n]); out.append(out[-n])
        else:
            out.append(out[-n])
    out = out[:size] if len(out) > size else out
    if flag & 1:
        tbl = _swaps(rom, flag)
        for b in range(0, size - size % 64, 64):
            for i in range(62):
                j = b + tbl[i]
                out[b + 1 + i], out[j] = out[j], out[b + 1 + i]
    return bytes(out), p


def decode_cmds(rom, off, size):
    """Raw command count/overshoot check: returns produced length (may exceed size)."""
    p = off + 1; n_out = 0
    while n_out < size:
        c = rom[p]; p += 1
        n, t = (c & 63) + 1, c >> 6
        if t == 0: n_out += n; p += n
        elif t == 1: n_out += n + 1; p += 1
        elif t == 2: n_out += 2
        else: n_out += 1
    return n_out, p


def _encode_cmds(data):
    """Optimal (min bytes) parse of `data` into commands; no add, no shuffle. Returns list of commands."""
    N = len(data)
    INF = 1 << 30
    cost = [INF] * (N + 1)
    choice = [None] * (N + 1)
    cost[N] = 0
    # backwards DP; literal runs handled via lit-run choice of length k (cost 1+k)
    for i in range(N - 1, -1, -1):
        best, bc = INF, None
        # literals
        for k in range(1, min(64, N - i) + 1):
            c = 1 + k + cost[i + k]
            if c < best: best, bc = c, ('L', k)
        # matches: distance 1..256 for type1 (len 2..65), distance 1..64 for type 2 (len 2) / type 3 (len 1)
        for d in range(1, min(256, i) + 1):
            L = 0
            while i + L < N and L < 65 and data[i + L] == data[i + L - d]:
                L += 1
            if L >= 1 and d <= 64:
                c = 1 + cost[i + 1]
                if c < best: best, bc = c, ('S', d)
            if L >= 2 and d <= 64:
                c = 1 + cost[i + 2]
                if c < best: best, bc = c, ('D', d)
            for l in range(2, L + 1):
                c = 2 + cost[i + l]
                if c < best: best, bc = c, ('M', d, l)
        cost[i], choice[i] = best, bc
    cmds, i = [], 0
    while i < N:
        ch = choice[i]; cmds.append(ch)
        i += ch[1] if ch[0] == 'L' else (2 if ch[0] == 'D' else (1 if ch[0] == 'S' else ch[2]))
    return cmds


def _emit(data, cmds):
    out, i = bytearray(), 0
    for ch in cmds:
        if ch[0] == 'L':
            k = ch[1]; out.append(k - 1); out += data[i:i + k]; i += k
        elif ch[0] == 'M':
            d, l = ch[1], ch[2]; out += bytes([0x40 | (l - 2), d - 1]); i += l
        elif ch[0] == 'D':
            out.append(0x80 | (ch[1] - 1)); i += 2
        else:
            out.append(0xC0 | (ch[1] - 1)); i += 1
    return out


def _cmd_len(ch):
    return {'L': 1 + ch[1], 'M': 2, 'D': 1, 'S': 1}[ch[0]] if ch[0] != 'L' else 1 + ch[1]


def compress(data, target=None):
    """Compress raw bytes (flag 0, no add). With `target`, pad the stream to exactly `target` bytes by de-optimising
    the parse (split literal runs, turn short copies into literals); raises ValueError if it cannot fit."""
    cmds = _encode_cmds(bytes(data))
    body = _emit(data, cmds)
    if target is None:
        return bytes([0]) + bytes(body)
    need = target - 1 - len(body)
    if need < 0:
        raise ValueError(f"compressed {len(body) + 1} > target {target}")
    # expand: walk commands and replace with longer equivalents until need == 0
    pos = []  # data positions per cmd
    i = 0
    for ch in cmds:
        pos.append(i)
        i += ch[1] if ch[0] == 'L' else (2 if ch[0] == 'D' else (1 if ch[0] == 'S' else ch[2]))
    new = []
    for ch, p in zip(cmds, pos):
        if need <= 0:
            new.append(ch); continue
        ln = ch[1] if ch[0] == 'L' else (2 if ch[0] == 'D' else (1 if ch[0] == 'S' else ch[2]))
        # turning this command into single-byte literal runs costs 2 per byte
        cur = _cmd_len(ch)
        full = 2 * ln
        if full - cur <= need:
            new += [('L', 1)] * ln; need -= full - cur
        else:
            # partial: split into k one-byte literals + a literal run of the rest (rest stays as literal)
            # literal run of ln bytes costs 1+ln; each split adds 1 byte
            base = 1 + ln
            if base - cur > need:
                new.append(ch); continue
            need -= base - cur
            extra = need  # number of extra splits (each +1), at most ln-1
            k = min(extra, ln - 1)
            new += [('L', 1)] * k + [('L', ln - k)]
            need -= k
    if need:
        raise ValueError(f"cannot pad to {target} (left {need})")
    body = _emit(data, new)
    assert len(body) + 1 == target
    return bytes([0]) + bytes(body)


def _selftest():
    import random
    random.seed(1)
    for trial in range(20):
        data = bytes(random.choice([0, 0, 0, 1, 2, 0x11, 0x22]) for _ in range(0x800))
        z = compress(data)
        dec, end = decompress(z + b'\0' * 4, 0, len(data))
        assert dec == data and end == len(z), trial
        for t in (len(z), len(z) + 1, len(z) + 37):
            z2 = compress(data, t)
            assert len(z2) == t and decompress(z2, 0, len(data))[0] == data
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", nargs="?")
    ap.add_argument("rom", nargs="?")
    ap.add_argument("off", nargs="?")
    ap.add_argument("size", nargs="?")
    ap.add_argument("--n", type=int, default=1)
    ap.add_argument("--add", type=int, default=0)
    ap.add_argument("--out")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return _selftest()
    rom = open(a.rom, "rb").read()
    off, size = int(a.off, 16) & 0x1FFFFFF, int(a.size, 16)
    buf = bytearray()
    for _ in range(a.n):
        d, off = decompress(rom, off, size, a.add)
        buf += d
    open(a.out, "wb").write(buf)
    print(f"{len(buf):#x} bytes, end {off:#x}")


if __name__ == "__main__":
    sys.exit(main())
