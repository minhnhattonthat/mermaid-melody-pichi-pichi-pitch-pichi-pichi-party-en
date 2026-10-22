# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 9 done. Release v1.0 (2026-10-23): release/Mermaid_Melody_Pichi_Pichi_Party_EN_v1.0.zip, patch SHA-1
  aed2b439f43b79a549981d4170007dedf0152cc8, patched ROM SHA-1 5b2b3bd5392d7a742ce9142667cd14d15d0201dd (CRC32
  271B54DD). Published 2026-10-23: github.com/minhnhattonthat/mermaid-melody-pichi-pichi-pitch-pichi-pichi-party-en,
  release v1.0 (remote is HTTPS with gh's credential helper for minhnhattonthat).
- **Done:** text 6866/6866 units English (reviewed, sample review approved); graphics groups in docs/re/graphics.md;
  VWF with px budget, ext strings (tools/romdata.py), pop-up composer (tools/patches.py), Latin name entry.
  QA: tools/qa_tour.py; pop-ups via tools/lua/popup.lua. Repo restructured to fan-translation-template (2026-10-23).
  Graphics text redrawn with open fonts only (fonts/, docs/fonts.md, D9; 82 PNGs regenerated, checked side by side
  and in the QA tour: title, menus, board, results, staff roll, clothes, name entry).
- **Next:** player bug reports (GitHub issues).
- **Known issues** (docs/known_issues.txt, copied into the release README): in-story Change Clothes not reached by
  scripted runs; some board graphics only checked as images; compact labels; staff-name readings; "1 turns" on the
  status screen (unit is fixed text).
- **Open bugs:** none. Fixed 2026-10-23: System > View status header showed エピソード (builder 0x08032B88 writes
  glyph immediates; savestate `work/states/mp2_status.mss`, re-enter with B then A).
- **Waiting on the user:** nothing.
