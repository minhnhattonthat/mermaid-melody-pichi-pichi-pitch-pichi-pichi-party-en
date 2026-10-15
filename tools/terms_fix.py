"""Glossary consistency sweep over the English in script/*/*.json (JSON load/dump; reports every change).
    python -X utf8 tools/terms_fix.py [--dry]
FIXES: (regex, replacement) for spellings that drifted between translation batches. Lines whose width then exceeds
the box are reported (fix them by hand).
"""
import glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import font_en  # noqa: E402

ROOT = os.path.dirname(HERE)
FIXES = [
    (r"\bFountain Square\b", "Fountain Plaza"),
    (r"\bA Present of Sweets\b", "A Gift of Sweets"),
    (r"\bStrong Heart\b", "Unbeatable Heart"),
    (r"\bLight Steps\b", "Nimble Steps"),
    (r"\bTest of Courage Night\b", "Night of Courage"),
    (r"\bMermaid Legend Cave\b", "cave of the mermaid legend"),
    (r"\"The Kitten's Wish\"", "\"A Kitten's Wish\""),
    (r"\"A Gentle Rain\"", "\"Gentle Rain\""),
    (r"Hymn That Wouldn't Start", "Hymn That Won't Start"),
    (r"\b[Tt]he Pearl Piari\b", "Pearl Piari"),
    (r"\bthe Cape Lookout\b", "Cape Lookout"),
]


def main(dry):
    n = 0
    for p in sorted(glob.glob(os.path.join(ROOT, "script", "*", "*.json"))):
        doc = json.load(open(p, encoding="utf-8"))
        changed = False
        for e in doc["strings"]:
            en = e.get("en") or ""
            new = en
            for rx, rep in FIXES:
                new = re.sub(rx, rep, new)
            if new != en:
                n += 1
                print(e["id"], repr(en), "->", repr(new))
                if max(font_en.line_widths(new)) > 212:
                    print("   WIDE:", font_en.line_widths(new))
                e["en"] = new
                changed = True
        if changed and not dry:
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                json.dump(doc, f, ensure_ascii=False, indent=1)
    print(n, "strings changed" + (" (dry run)" if dry else ""))


if __name__ == "__main__":
    main("--dry" in sys.argv)
