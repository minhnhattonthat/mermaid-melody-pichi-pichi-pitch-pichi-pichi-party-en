"""One-command check (pre-commit hook runs this): every step must exit 0.
    python -X utf8 tools/check.py
"""
import os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = [sys.executable, "-X", "utf8"]
STEPS = [["tools/build.py", "check"]] if os.path.exists(os.path.join(ROOT, "tools", "build.py")) else \
    [["tools/fs.py", "rom/Mermaid Melody - Pichi Pichi Pitch - Pichi Pichi Party (Japan).gba", "--grep", "/font/"]]

fail = 0
for s in STEPS:
    r = subprocess.run(PY + s, cwd=ROOT, stdout=subprocess.DEVNULL)
    if r.returncode:
        print("FAIL:", " ".join(s)); fail = 1
sys.exit(fail)
