# Mermaid Melody Pichi Pichi Pitch: Pichi Pichi Party (GBA, Konami 2004) English translation

Skill: translate-retro-game (Claude Code: plugin, enabled in .claude/settings.json; other agents: `<SKILL_DIR>/SKILL.md`; `$SKILL` = the directory holding its SKILL.md). Read it before ROM, text or QA work.

## Commands (run from repo root)
- Build:    `python -X utf8 tools/build.py build`  -> build/mmppp2_en.gba (checks the dump against `rom.sha1` first; `--marker` = marker build)
- Check:    `python -X utf8 tools/check.py`  (identity build, graphics apply, text lint; the pre-commit hook runs this)
- Smoke:    `python -X utf8 $SKILL/scripts/emu.py build/mmppp2_en.gba --out work/qa/smoke --route tools/routes/mainmenu.txt --smoke`
- Warp:     scene list in `tools/debug/scenes.md` (mode switch `tools/debug/mode.lua`, forced event `tools/debug/event.lua`); never ask the user to play to a scene
- Release:  `python -X utf8 tools/release.py` (patch + verify; never publish without the user; `$SKILL` env var overrides the plugin path)
- Clean:    `python -X utf8 tools/clean.py` (published projects: lists rebuildable/downloadable files; `--yes` deletes)

## Paths
- Original ROM: `rom/Mermaid Melody - Pichi Pichi Pitch - Pichi Pichi Party (Japan).gba` (gitignored; SHA-1 in `rom.sha1`, checked by `tools/check_rom.py`; copy at work/orig.gba). Emulator: this repo's own copy in `tools/mesen/` (MesenCE 2.2.1 via `fetch_emu.py mesen` + `gba-bios`; gitignored). Savestates: `work/states/`.
- Text: `script/event/*.json`, `script/bms/*.json` (tools/text.py dump/identity). Tables: `tbl/` (tools/mktbl.py). Glossary: `glossary.md`. RE notes index: `docs/re/README.md`. Fonts and their licences: `docs/fonts.md`. File system: tools/fs.py.
- Text pipeline: English via VWF (tools/vwf.py hooks renderer 0x0803843C + map builder 0x08038904; font tools/font_en.py + font_glyphs.py); ext strings for fixed-width code tables (tools/romdata.py); pop-up composer (tools/patches.py). Batches: tools/batches.py (split/check/merge/pairs/lint), work/tl/. Fixes: tools/fix.py TSV; terms: tools/terms_fix.py. Briefs: docs/translator-brief.md, docs/reviewer-brief.md, docs/style-reference.md.
- Graphics: tools/gfx/ (export.py, apply.py, redraw*.py), gfx/orig, gfx/en, gfx/layout; brief docs/gfx-brief.md; index docs/re/graphics.md, reports docs/re/gfx_*.md.
- Debug/QA: tools/qa_tour.py; pop-ups via tools/lua/popup.lua; text windows via tools/lua/ctxlog.lua + tools/winmap.py.

## Rulings
- Edit source files (.py .lua .asm .tbl .json) only with the file-edit tool; scripts here read and analyse, never `.replace()` and write back.
- The user's decisions, with the options and reasons: `docs/decisions.md`. Read it before asking the user anything; add each new ruling there the same session.
- Player bug reports: GitHub issues (`gh issue list --label bug`). Copy the attached save into `work/states/`, reproduce in the emulator, fix, commit with `Fixes #N`, and update `docs/status.md`.
- Prequel (read-only reference, never modify): sibling repo `../mermaid-melody-pichi-pichi-pitch`. Song lyrics shared with it must match its English (its script/text.json).
- Fixed-width Japanese also lives in code as immediates, not only in tables (e.g. the status header builder 0x08032B88): when a screen still shows Japanese after its table is patched, log the row in RAM and find the writer.
- Savestates carry the old code and VRAM: after code, font or graphics changes, re-enter the screen or cold boot.
- Release README text: `docs/README.template.txt` + `docs/known_issues.txt` (filled by tools/release.py).

## Status
`docs/status.md`: done, next, open bugs. Update it at the end of every session.
