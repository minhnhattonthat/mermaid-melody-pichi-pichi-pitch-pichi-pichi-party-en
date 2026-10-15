# Graphics workstream brief (one group per agent)

Repo: H:\translation\batch\projects\mermaid-melody-pichi-pichi-pitch-pichi-pichi-party. Read CLAUDE.md, glossary.md,
tools/debug/scenes.md, and the graphics reference H:\translation\batch\.claude\skills\translate-retro-game\references\graphics.md.
Use `python -X utf8`; in Git Bash prefix commands with `MSYS_NO_PATHCONV=1` when passing ROM paths like /system/... .
Edit/create source only with the file-write/edit tools (no sed, no heredocs into source files).

## Goal
Every Japanese text drawn as graphics in your group's screens becomes English, matching the original look
(colours, outline, size, position), and is verified in a zoomed emulator shot. Text inside dialogue/menus drawn by the
font engine is NOT yours (that is script text); only pixels stored in graphics files.

## Pipeline (do not edit these shared files; ask the controller in your report if one needs a change)
- Files live in the ROM's file system (tools/fs.py; listing: `python -X utf8 tools/fs.py work/orig.gba`).
  Formats: tools/gfx/gfxfmt.py (.dcg 4bpp tiles, some with a 12-byte header w×h; .imb 8bpp/4bpp tiles; palettes
  .dcl/.plb/.acl). Raw OBJ .dcg files hold sprites one after another (1D mapping, each sprite row-major): view them
  with the sprite's width in tiles (`tools/gfx/rawview.py PATH TW OUT.png ZOOM [BANK|-1]`, -1 = grey).
- Export: `tools/gfx/export.py PATH [--tw N] [--pal FSPATH.dcl | DUMP.pal.bin [--obj]] [--bank B]` writes
  gfx/orig/<name>.png (palette-mode PNG of colour indices) and gfx/layout/<name>.json.
- Your English versions: gfx/en/<name>.png, same size and tile width, palette-mode, pixel values = colour indices
  of the same bank (draw only with colours the original uses). Generate them with your own script
  tools/gfx/redraw_<group>.py (helpers you may import: tools/gfx/redraw.py text_mask/outlined/dilate/stamp,
  tools/gfx/pixfont.py hand-made 5x7 pixel font for small text). Rerunning your script must regenerate all your PNGs.
- `python -X utf8 tools/gfx/apply.py` validates every PNG (exit 0 required). Build your own test ROM:
  `python -X utf8 tools/build.py build --out build/gfx_<group>.gba` (never the default build/ path).
- Find what is on screen: `tools/lua/ppuevery.lua` (--var PPU_EVERY=N --var PPU_FROM=F) dumps PPU state;
  `tools/gfx/onscreen.py DUMP.vram.bin` lists the graphics files loaded; `tools/lua/oam.lua --var AT=F` lists sprites
  (x, y, shape/size, tile, palette bank). Palettes: OBJ bank = OAM pal; dump .pal.bin second half = OBJ palettes.
- Reach screens: `tools/debug/mode.lua --var MODE=...` (scenes.md), story board: MODE=0x0829AD48 + `--mash 50`;
  `tools/debug/event.lua --var EV=n` forces the next event script. Emulator: emu.py in the skill scripts (see CLAUDE.md).
  Never kill emulators by name; only your own by PID.

## Style
- English wording: glossary.md (names, places, episode titles, terms). Full words, no abbreviations; if space is truly
  impossible, shrink the font before abbreviating, and list any abbreviation in your report.
- Keep sprite/tile layout and file size: you only change pixels. If English needs more room than the graphic has,
  use smaller lettering, two lines, or tighter spacing; report anything that cannot fit.
- Zoom into every result (sheet.py --zoom 3 or PIL resize) before calling it done.

## Report (your final message)
Write docs/re/gfx_<group>.md: one row per file: | file | content | screen / route | status |. Then reply with: files
changed, screens verified (with shot paths), anything left Japanese and why, any shared-tool change you need.
