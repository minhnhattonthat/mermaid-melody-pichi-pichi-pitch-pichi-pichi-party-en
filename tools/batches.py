"""Translation batches over script/*/*.json (unique Japanese strings; identical JP shares one English).
    python -X utf8 tools/batches.py split [--size 3500]   write work/tl/bNN.tsv + work/tl/bNN.terms.txt (untranslated)
    python -X utf8 tools/batches.py check bNN             validate work/tl/bNN.out.tsv (exit 1 on errors)
    python -X utf8 tools/batches.py merge bNN             check, then write English into script/*/*.json
    python -X utf8 tools/batches.py pairs bNN OUT         reviewer pairs file (JP / EN with neighbours)
    python -X utf8 tools/batches.py fit "text / line 2"   px per line
TSV in: id<TAB>speaker<TAB>form<TAB>limit<TAB>jp ; out: id<TAB>en. " / " = line break inside a box.
Tokens to copy exactly: [XXXX] raw codes, {iXXX} icons. {h } in the Japanese is a narrow space: write a plain space.
"""
import glob, json, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import text, font_en, fs  # noqa: E402

TL = os.path.join(ROOT, "work", "tl")
DLG_PX, DLG_LINES = 212, 2
# per-file window budgets (px per line, lines); measured windows: chars n -> 8*(3*(n//2)+2*(n%2)) px
BMS_WIN = {
    "cmd": (88, 1), "item": (96, 1), "card": (112, 1), "event": (112, 1),
    "title_msg": (204, 2), "cmd_msg": (DLG_PX, 2), "card_get": (DLG_PX, 2), "card_msg": (DLG_PX, 2),
    "card_info": (DLG_PX, 2), "card_use": (DLG_PX, 2), "info_msg": (DLG_PX, 2), "info_stat": (DLG_PX, 2),
    "item_msg": (DLG_PX, 2), "item_get": (DLG_PX, 2), "item_info": (DLG_PX, 2), "blk_info": (DLG_PX, 2),
}
DATA_FILES = {"/system/textbin/numeric.bms", "/event/ev000002.bin", "/event/ev000003.bin", "/event/ev000006.bin"}
SPEAKERS = {0: "Lucia", 1: "Hanon", 2: "Rina", 3: "Lucia", 4: "Hanon", 5: "Rina", 7: "Hippo", 0xA: "Kaito",
            0xB: "Taro Mitsuki", 0xC: "Taro Mitsuki", 0x12: "Lucia", 0x13: "Hanon", 0x14: "Rina", 0xFE: "narration/SFX"}
TOKS = re.compile(r"\[(?!FFB[23])[0-9A-F]{4}\]|\{i[0-9A-F]{3}\}")  # [FFB2]/[FFB3] = quote marks, may become "


def jp_px(line):
    return 12 * len(text.TOK.findall(line))


def event_roles(rom, path):
    """string byte offset -> (form, speaker) from the bytecode (op 1 = dialogue, 58 = banner, 48 = choice)."""
    o, s = fs.get(rom, path)
    hdr, offs = text.event_parts(rom, o)
    bo, bs = hdr[0], hdr[1]
    w = struct.unpack_from("<%dH" % (bs // 2), rom, o + bo)
    roles, q = {}, 0
    while q + 1 < len(w):
        op, ln = w[q], w[q + 1]
        if op == 0xFFFF or ln < 2:
            break
        args = w[q + 2:q + ln]
        if op == 1 and len(args) >= 2 and args[1] < len(offs):
            roles.setdefault(offs[args[1]], ("dlg", SPEAKERS.get(args[0], "?")))
        elif op == 58:
            for a in args:
                if a < len(offs):
                    roles.setdefault(offs[a], ("banner", ""))
        elif op == 48:
            for a in args:
                if a < len(offs):
                    roles.setdefault(offs[a], ("choice", ""))
        q += ln
    return roles


def units():
    """Ordered unique-JP units: dict(id, jp, form, speaker, px, lines, ents=[(doc_path, ent)])."""
    rom = open(text.ORIG, "rb").read()
    docs = text.load_all()
    docs.sort(key=lambda d: (d[1]["kind"] != "event", d[1]["path"]))
    out, by_jp = [], {}
    for jp, doc in docs:
        if doc["path"] in DATA_FILES:
            continue
        roles = event_roles(rom, doc["path"]) if doc["kind"] == "event" else {}
        stem = os.path.basename(doc["path"]).rsplit(".", 1)[0]
        for e in doc["strings"]:
            if not re.search(r"[぀-ヿ一-鿿]", e["jp"]):
                continue
            if e["jp"] in by_jp:
                by_jp[e["jp"]]["ents"].append((jp, e["id"]))
                continue
            lines = e["jp"].split("\n")
            jw = max(jp_px(l) for l in lines)
            if doc["kind"] == "event":
                form, spk = roles.get(int(e["id"][-4:], 16), ("other", ""))
                if form == "dlg":
                    px, nl = DLG_PX, DLG_LINES
                elif form == "banner":
                    px, nl = max(jw, 120), 1
                else:
                    px, nl = max(jw, 96), len(lines)
            else:
                spk = ""
                if stem.startswith("battle_msg"):
                    form, px, nl = "dlg", DLG_PX, 2
                elif stem.startswith("cls_p_name"):
                    form, px, nl = "menu", 96, 1
                elif stem in BMS_WIN:
                    form = "menu" if BMS_WIN[stem][1] == 1 else "msg"
                    px, nl = BMS_WIN[stem]
                else:
                    form, px, nl = "fit", max(jw, 48), len(lines)
            u = {"id": e["_sid"], "jp": e["jp"], "form": form, "speaker": spk, "px": px, "lines": nl,
                 "ents": [(jp, e["id"])], "en": e.get("en", "")}
            by_jp[e["jp"]] = u
            out.append(u)
    return out


def to_tsv(s):
    return s.replace("\t", " ").replace("\n", " / ")


def from_tsv(s):
    return s.replace(" / ", "\n")


def split(size=3500, only=None):
    os.makedirs(TL, exist_ok=True)
    us = [u for u in units() if not u["en"]]
    if only:
        us = [u for u in us if re.search(only, u["ents"][0][0].replace("\\", "/"))]
    gl = open(os.path.join(ROOT, "glossary.md"), encoding="utf-8").read().split("\n")
    rows = [l for l in gl if l.startswith("|") and not l.startswith("|---") and not l.startswith("| JP")]
    batches, cur, n = [], [], 0
    for u in us:
        cur.append(u); n += len(u["jp"])
        if n >= size:
            batches.append(cur); cur, n = [], 0
    if cur:
        batches.append(cur)
    existing = sorted(glob.glob(os.path.join(TL, "b*.tsv")))
    start = 1 + max([int(re.search(r"b(\d+)", os.path.basename(p)).group(1)) for p in existing] or [0])
    for k, b in enumerate(batches):
        name = "b%02d" % (start + k)
        with open(os.path.join(TL, name + ".tsv"), "w", encoding="utf-8", newline="\n") as f:
            for u in b:
                f.write("\t".join([u["id"], u["speaker"] or "-", u["form"], "%dpx x%d" % (u["px"], u["lines"]),
                                   to_tsv(u["jp"])]) + "\n")
        blob = "".join(u["jp"] for u in b)
        terms = [r for r in rows if (lambda c: c and any(x and x in blob for x in re.split(r" / |、", c)))(r.split("|")[1].strip())]
        with open(os.path.join(TL, name + ".terms.txt"), "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(terms) + "\n")
        print(name, len(b), "entries", len(blob), "chars")


def read_tsv(path, cols):
    rows = []
    for line in open(path, encoding="utf-8-sig"):
        line = line.rstrip("\n").rstrip("\r")
        if not line.strip():
            continue
        p = line.split("\t")
        rows.append(p if cols is None else p[:cols] + ["\t".join(p[cols:])] if len(p) > cols else p)
    return rows


def check(name, quiet=False):
    inp = read_tsv(os.path.join(TL, name + ".tsv"), None)
    outp = os.path.join(TL, name + ".out.tsv")
    if not os.path.exists(outp):
        print("missing", outp); return 1, {}
    out = {}
    errs = []
    for p in read_tsv(outp, None):
        if len(p) != 2:
            errs.append(f"bad line (need id<TAB>en): {p[:1]}"); continue
        if p[0] in out:
            errs.append(f"{p[0]}: duplicate")
        out[p[0]] = p[1]
    ids = [p[0] for p in inp]
    for i in set(out) - set(ids):
        errs.append(f"{i}: not in batch")
    for p in inp:
        i, spk, form, lim, jp = p[0], p[1], p[2], p[3], p[4]
        if i not in out:
            errs.append(f"{i}: missing"); continue
        en = out[i]
        if re.search(r"[぀-ヿ一-鿿＀-￯]", en):
            errs.append(f"{i}: Japanese or full-width character"); continue
        if not en.strip():
            errs.append(f"{i}: empty"); continue
        if sorted(TOKS.findall(jp)) != sorted(TOKS.findall(en)):
            errs.append(f"{i}: tokens differ {TOKS.findall(jp)} vs {TOKS.findall(en)}")
        m = re.match(r"(\d+)px x(\d+)", lim)
        px, nl = int(m.group(1)), int(m.group(2))
        md = from_tsv(en)
        try:
            text.encode(md, "en")
        except ValueError as x:
            errs.append(f"{i}: {x}"); continue
        ws = font_en.line_widths(md)
        if len(ws) > nl:
            errs.append(f"{i}: {len(ws)} lines > {nl}")
        if max(ws) > px:
            errs.append(f"{i}: {max(ws)}px > {px}px  ({'|'.join(str(w) for w in ws)})")
        if re.search(r"\[[0-9A-F]{4}\](st|nd|rd|th)\b", en):
            errs.append(f"{i}: ordinal glued to a number")
    for e in errs:
        print(e)
    if not quiet:
        print("OK" if not errs else f"{len(errs)} errors")
    return (1 if errs else 0), out


def merge(name):
    r, out = check(name)
    if r:
        sys.exit("merge refused")
    us = {u["id"]: u for u in units()}
    docs = {jp: doc for jp, doc in text.load_all()}
    n = 0
    for i, en in out.items():
        for jp, eid in us[i]["ents"]:
            for e in docs[jp]["strings"]:
                if e["id"] == eid:
                    e["en"] = from_tsv(en); n += 1
    for jp, doc in docs.items():
        for e in doc["strings"]:
            e.pop("_sid", None)
        with open(jp, "w", encoding="utf-8", newline="\n") as f:
            json.dump(doc, f, ensure_ascii=False, indent=1)
    print("merged", len(out), "units ->", n, "strings")


def pairs(name, dst):
    inp = read_tsv(os.path.join(TL, name + ".tsv"), None)
    _, out = check(name, quiet=True)
    with open(dst, "w", encoding="utf-8", newline="\n") as f:
        for k, p in enumerate(inp):
            f.write(f">> {p[0]} [{p[1]}, {p[2]}] | {p[4]}\n   EN: {out.get(p[0], '(missing)')}\n")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "split":
        split(int(a[a.index("--size") + 1]) if "--size" in a else 3500,
              a[a.index("--only") + 1] if "--only" in a else None)
    elif a[0] == "check":
        sys.exit(check(a[1])[0])
    elif a[0] == "merge":
        merge(a[1])
    elif a[0] == "pairs":
        pairs(a[1], a[2])
    elif a[0] == "fit":
        print(font_en.line_widths(from_tsv(a[1])))
