"""Screen tour of a build: one cold-boot run per scene (debug warps), screenshots + one contact sheet per scene.
    python -X utf8 tools/qa_tour.py [ROM] [--only NAME,..] [--jobs 3] [--out work/qa/tour]
Scenes: SCENES below (name, emu.py args). Sheets: <out>/<name>/sheet.png; index printed at the end.
"""
import os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
S = r"H:\translation\batch\.claude\skills\translate-retro-game\scripts"
MODE = "tools/debug/mode.lua"


def mode(m, frames, mash=60, every=60):
    return ["--route-str", "1300 -", "--script", MODE, "--var", f"MODE={m}", "--frames", str(frames),
            "--mash", str(mash), "--shot-every", str(every)]


def event(ev, frames=4200):
    return mode("0x0829AD48", frames, 40, 50) + ["--script", "tools/debug/event.lua", "--var", f"EV={ev}"]


SCENES = [
    ("boot_title", ["--frames", "2400", "--shot-every", "50"]),
    ("mainmenu", ["--route-str", "2100 -;5 start;100 -;5 start;100 -;5 start;200 -;5 down;150 -;5 down;150 -;"
                  "5 down;150 -;5 down;150 -;5 a;300 -;5 b;200 -", "--shot-every", "50"]),
    ("story_ep1", mode("0x0829AD48", 16000, 40, 100)),
    ("results_episode", mode("0x0829B888", 4000)),
    ("results_kekka", mode("0x0829B84C", 4000)),
    ("results_stage", mode("0x0829B838", 4000, 0)),
    ("ending_staff", mode("0x0829AC84", 9000, 0, 120)),
    ("clothes", mode("0x0829B8B0", 4000, 0)),
    ("name_entry", mode("0x0829B0F0", 3000, 0)),
    ("linkerror", mode("0x0829AD84", 3000, 0)),
    ("continue_save", mode("0x0829ACC0", 4000)),
    ("sram", mode("0x0829ACAC", 3000, 0)),
] + [(f"ev{e}", event(e)) for e in (100, 500, 1500, 2500, 3100, 5000, 5100, 5150, 5500, 5600, 5640, 6000, 9000)]


def run(rom, out, name, args):
    d = os.path.join(out, name)
    cmd = [sys.executable, "-X", "utf8", os.path.join(S, "emu.py"), rom, "--out", d, "--timeout", "2400"] + args
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    subprocess.run([sys.executable, "-X", "utf8", os.path.join(S, "sheet.py"), d, "--cols", "6", "--max", "36",
                    "--changed", "0.03"], cwd=ROOT, capture_output=True)
    return name, r.returncode


def main():
    a = sys.argv[1:]
    rom = a[0] if a and a[0].endswith(".gba") else "build/mmppp2_en.gba"
    out = a[a.index("--out") + 1] if "--out" in a else "work/qa/tour"
    only = a[a.index("--only") + 1].split(",") if "--only" in a else None
    jobs = int(a[a.index("--jobs") + 1]) if "--jobs" in a else 3
    todo = [(n, x) for n, x in SCENES if not only or n in only]
    bad = 0
    with ThreadPoolExecutor(jobs) as ex:
        for name, rc in ex.map(lambda t: run(rom, out, *t), todo):
            print(f"{name:20s} exit {rc}  {out}/{name}/sheet.png")
            bad += rc != 0
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
