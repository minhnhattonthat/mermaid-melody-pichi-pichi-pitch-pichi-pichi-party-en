# Mermaid Melody Pichi Pichi Pitch: Pichi Pichi Party (GBA) English translation

Skill: translate-retro-game (H:\translation\batch\.claude\skills\translate-retro-game\SKILL.md). Read it before ROM, text or QA work.
Batch brief: H:\translation\batch\projects\BATCH_BRIEF.md (all rulings pre-approved; never push/publish).
Prequel (read-only reference, never modify): H:\translation\batch\projects\mermaid-melody-pichi-pichi-pitch.

## Commands (run from repo root)
- Build:    `python -X utf8 tools/build.py build` -> build/mmppp2_en.gba
- Check:    `python -X utf8 tools/check.py` (pre-commit hook runs this)
- Smoke:    `python -X utf8 H:/translation/batch/.claude/skills/translate-retro-game/scripts/emu.py build/mmppp2_en.gba --out work/qa/smoke --route tools/routes/mainmenu.txt --smoke`
- Warp:     see tools/debug/scenes.md
- Release:  `python -X utf8 tools/release.py`

## Paths
- Original ROM: `rom/Mermaid Melody - Pichi Pichi Pitch - Pichi Pichi Party (Japan).gba` (copy work/orig.gba).
  Emulator: tools/mesen/ (MesenCE 2.2.1 via fetch_emu.py mesen + gba-bios).
- RE notes: docs/re/README.md. Glossary + rulings: glossary.md (copied from prequel). File system: tools/fs.py.

## Rulings
- Edit source only with Edit/Write tools. Honorifics dropped; Western name order; official English names (Lucia, Hanon, Rina).
- Credits English. All graphics text in scope. Full words, no abbreviations unless flagged.
- Song lyrics shared with the prequel must match the prequel's English (its script/text.json).

## Pipeline
- Text: script/event/*.json, script/bms/*.json (tools/text.py dump/identity; tbl from tools/mktbl.py). English via
  VWF (tools/vwf.py hooks renderer 0x0803843C + map builder 0x08038904; font tools/font_en.py + font_glyphs.py).
  Batches: tools/batches.py (split/check/merge/pairs/lint), work/tl/. Fixes: tools/fix.py TSV; terms: tools/terms_fix.py.
  Briefs: docs/translator-brief.md, docs/reviewer-brief.md, docs/style-reference.md.
- Graphics: tools/gfx/ (export.py, apply.py, redraw*.py), gfx/orig, gfx/en, gfx/layout; brief docs/gfx-brief.md;
  reports docs/re/gfx_*.md.
- Debug: tools/debug/mode.lua (mode switch), event.lua (force event), scenes.md.

## Status
- Done: all phases; v1.0 released locally (release/*.zip, patch SHA-1 636346ed1a64d7169b1484fc47f17b1049ed8367).
  Text 6866/6866 units English (reviewed, sample review approved); graphics groups in docs/re/graphics.md;
  VWF with px budget, ext strings (tools/romdata.py), pop-up composer (tools/patches.py), Latin name entry.
  QA: tools/qa_tour.py; pop-ups via tools/lua/popup.lua. Open: status screen (System > View) and in-story Change
  Clothes not reached by scripted runs (docs/known_issues.txt).
