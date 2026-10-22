"""Release: check -> build -> smoke -> leftover-Japanese scan -> BPS (re-applied and verified) -> README -> zip.
    python -X utf8 tools/release.py [--no-smoke]
Never publishes anything; the zip stays local (release/Mermaid_Melody_Pichi_Pichi_Party_EN_v<version>.zip = patch + README).
"""
import hashlib, os, subprocess, sys, zipfile, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SKILL = os.environ.get("SKILL", os.path.join(os.path.expanduser("~"), ".claude", "plugins", "marketplaces",
                                             "retro-translation", "skills", "translate-retro-game"))
VERSION = "1.0"
PY = [sys.executable, "-X", "utf8"]


def run(args):
    r = subprocess.run(PY + args, cwd=ROOT)
    if r.returncode:
        sys.exit(f"release gate failed: {' '.join(args)}")


def hashes(d):
    return {"crc32": "%08X" % (zlib.crc32(d) & 0xFFFFFFFF), "md5": hashlib.md5(d).hexdigest(),
            "sha1": hashlib.sha1(d).hexdigest(), "size": len(d)}


def main():
    run(["tools/check.py"])
    run(["tools/build.py", "build"])
    built = os.path.join(ROOT, "build", "mmppp2_en.gba")
    if "--no-smoke" not in sys.argv:
        run([os.path.join(SKILL, "scripts", "emu.py"), built, "--out", "work/qa/release_smoke",
             "--route", "tools/routes/mainmenu.txt", "--smoke"])
    run(["tools/jpscan.py", built])
    rel = os.path.join(ROOT, "release")
    os.makedirs(rel, exist_ok=True)
    patch = os.path.join(rel, f"Mermaid_Melody_Pichi_Pichi_Party_EN_v{VERSION}.bps")
    orig = os.path.join(ROOT, "rom", "Mermaid Melody - Pichi Pichi Pitch - Pichi Pichi Party (Japan).gba")
    run([os.path.join(SKILL, "scripts", "bps.py"), "make", orig, built, patch])
    check = os.path.join(ROOT, "work", "reapplied.gba")
    run([os.path.join(SKILL, "scripts", "bps.py"), "apply", orig, patch, check])
    b, c = open(built, "rb").read(), open(check, "rb").read()
    if b != c:
        sys.exit("re-applied patch differs from the build")
    o, p = hashes(open(orig, "rb").read()), hashes(b)
    ps = hashlib.sha1(open(patch, "rb").read()).hexdigest()
    readme = open(os.path.join(ROOT, "docs", "README.template.txt"), encoding="utf-8").read().format(
        v=VERSION, o=o, p=p, patch=os.path.basename(patch), psha=ps,
        issues=open(os.path.join(ROOT, "docs", "known_issues.txt"), encoding="utf-8").read().rstrip())
    rp = os.path.join(rel, "README.txt")
    open(rp, "w", encoding="utf-8", newline="\r\n").write(readme)
    zp = os.path.join(rel, f"Mermaid_Melody_Pichi_Pichi_Party_EN_v{VERSION}.zip")
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(patch, os.path.basename(patch))
        z.write(rp, "README.txt")
    print("release:", zp)
    print("patch sha1:", ps)
    print("patched rom:", p)


if __name__ == "__main__":
    main()
