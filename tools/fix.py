"""Apply reviewer fixes: a TSV of `id<TAB>English` (unit ids as in the batches, e.g. e700.3; " / " = line break)
is checked like a batch (tokens, encodable, width/lines) and written to every string sharing that Japanese.
    python -X utf8 tools/fix.py FIXES.tsv [--dry]
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import batches, text, font_en  # noqa: E402


def main(path, dry):
    us = {u["id"]: u for u in batches.units()}
    docs = {jp: doc for jp, doc in text.load_all()}
    errs = 0
    todo = []
    for p in batches.read_tsv(path, None):
        if len(p) != 2 or p[0] not in us:
            print("bad line/id:", p[:1]); errs += 1; continue
        u, en = us[p[0]], batches.from_tsv(p[1])
        if sorted(batches.TOKS.findall(u["jp"])) != sorted(batches.TOKS.findall(en)):
            print(p[0], "tokens differ"); errs += 1; continue
        try:
            text.encode(en, "en")
        except ValueError as x:
            print(p[0], x); errs += 1; continue
        ws = font_en.line_widths(en)
        if len(ws) > u["lines"] or max(ws) > u["px"]:
            print(p[0], "too wide/long", ws, u["px"], u["lines"]); errs += 1; continue
        todo.append((u, en))
    if errs:
        sys.exit(f"{errs} errors; nothing written")
    if dry:
        print(len(todo), "fixes ok (dry)"); return
    for u, en in todo:
        for jp, eid in u["ents"]:
            for e in docs[jp]["strings"]:
                if e["id"] == eid:
                    e["en"] = en
    for jp, doc in docs.items():
        for e in doc["strings"]:
            e.pop("_sid", None)
        with open(jp, "w", encoding="utf-8", newline="\n") as f:
            json.dump(doc, f, ensure_ascii=False, indent=1)
    print(len(todo), "fixes applied")


if __name__ == "__main__":
    main(sys.argv[1], "--dry" in sys.argv)
