"""Fixed-width Japanese held in code tables and in sysstat.bms, made English through "ext" strings:
code 0x8100|k draws EXT[k] inline (tools/vwf.py); 0x8002 is a zero-width filler that keeps slot lengths.

ROM table 0x29E710.. (status/ranking builders 0x08032B..-0x08033B..; they copy fixed slots into RAM rows):
  0x29E710 names, 3 codes each (るちあ / 波音 / リナ); 0x29E722 and 0x29E732 エピソード glyph trio;
  0x29E742/0x29E74E ﾀｰﾝ, 0x29E748 pts (already Latin), 0x29E754 ﾏｽ, 0x29E758 ｺ;
  0x29E75A colours, 4 codes each: ﾅｼ (none) / ｱｵ / ﾑﾗｻｷ / ｷｲﾛ.
sysstat.bms: 16-code rows "label(9) {h}{h} [4000] unit(3)"; the game writes the number into [4000] by index, so
labels become [81kk] + 8 fillers and units [81kk] + 2 fillers.
"""
import json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
F = 0x8002
EXT = []  # list of English strings; index = k


def ext(s):
    if s not in EXT:
        EXT.append(s)
    return 0x8100 | EXT.index(s)


def slot(s, n):
    return [ext(s)] + [F] * (n - 1)


ROM_SLOTS = [  # (file offset, n codes, English)
    (0x29E710, 3, "Lucia"), (0x29E716, 3, "Hanon"), (0x29E71C, 3, "Rina"),
    (0x29E722, 3, "Episode"), (0x29E732, 3, "Episode "),
    (0x29E742, 3, " turns"), (0x29E74E, 3, " turns"), (0x29E754, 2, " spaces"), (0x29E758, 1, ""),
    (0x29E75A, 4, "None"), (0x29E762, 4, "Blue"), (0x29E76A, 4, "Purple"), (0x29E772, 4, "Yellow"),
]
JP_CHECK = {0x29E710: [0x11B, 0x0F1, 0x0D2], 0x29E722: [0x220, 0x221, 0x222], 0x29E742: [0x40D0, 0x40C0, 0x40ED]}

SYSSTAT = [  # label, unit (None = keep the row's tail as is)
    ("Notes", ""), ("Move exactly", " spaces"), ("Minimum move", " spaces"), ("Minimum: turns", " turns"),
    ("Maximum move", " spaces"), ("Maximum: turns", " turns"), ("Move 2 spaces", " turns"),
    ("Move 1 space", " turns"), ("Slow roulette", " turns"), ("Notes change", None), ("Max Notes", None),
    ("Stop anywhere", None), ("Move backward", None), ("Power up", " turns"), ("Shopping Slots x2", " turns"),
    ("Card Slots x2", " turns"), ("Extra turns", " turns"), ("Resting", " turns"),
    ("Cards have no effect", " turns"), ("Can't use cards", " turns"), ("Can't change clothes", " turns"),
    ("HP lost per step", None), ("HP loss", " turns"), ("HP gained per step", None), ("HP gain", " turns"),
    ("No space effects", " turns"), ("Fixed space type", None), ("Fixed space", " turns"),
]


NAME_GRID = 0x29AFD4  # name entry: 5 rows x 12 cells of codes (FFFE/FFFD dakuten keys, FFFC space, FFFF OK)
NAME_ROWS = ["ABCDEFGHIJKL", "MNOPQRSTUVWX", "YZabcdefghij", "klmnopqrstuv", "wxyz!?.-'&"]


def name_grid_codes():
    codes = []
    for r in NAME_ROWS:
        codes += [0x4000 | (ord(ch) + 0x10) for ch in r]
    return codes + [0xFFFC, 0xFFFF]


def patch_rom(rom):
    old = struct.unpack_from("<60H", rom, NAME_GRID)
    assert old[0] == 0xD2 and old[58:] == (0xFFFC, 0xFFFF), old[:3]
    struct.pack_into("<60H", rom, NAME_GRID, *name_grid_codes())
    for off, n, en in ROM_SLOTS:
        if off in JP_CHECK:
            assert list(struct.unpack_from("<%dH" % len(JP_CHECK[off]), rom, off)) == JP_CHECK[off], hex(off)
        struct.pack_into("<%dH" % n, rom, off, *slot(en, n))


def sysstat_markup(jp_markup_codes, label, unit):
    """jp codes (16 incl. trailing pad, no terminator) -> English codes keeping every position."""
    c = list(jp_markup_codes)
    c[0:9] = slot(label, 9)
    if unit is not None:
        c[12:12 + 3] = slot(unit, 3) if len(c) >= 15 else c[12:15]
    return c


def sysstat_codes(rom, encode_jp):
    """-> {string id: codes} for script/bms/system_textbin_sysstat.json (written by the build, not the JSON)."""
    doc = json.load(open(os.path.join(ROOT, "script", "bms", "system_textbin_sysstat.json"), encoding="utf-8"))
    out = {}
    for (label, unit), e in zip(SYSSTAT, doc["strings"]):
        out[e["id"]] = sysstat_markup(encode_jp(e["jp"]), label, unit)
    return out


def ext_codes(encode_en):
    return [encode_en(s) for s in EXT]
