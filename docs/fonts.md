# Fonts

Every font or glyph sheet the build reads ends up inside the released patch, so its licence must allow that. One row
per file; a font with no known licence doesn't go into a release. The graphics redraws (tools/gfx/redraw*.py) read
only `fonts/`; no system fonts.

| File | Source (URL, version) | Licence | Redistributable in a patch | Used for | Changes made |
|---|---|---|---|---|---|
| `tools/font_glyphs.py` | drawn for the prequel (sibling repo), carried over | MIT, same as repo | yes | VWF dialogue, menus, cards, items (`tools/font_en.py`, `tools/vwf.py`); name entry grid (`tools/gfx/redraw_name.py`) | - |
| `fonts/Nunito-ExtraBold.ttf`, `fonts/Nunito-Black.ttf` | https://github.com/google/fonts/blob/main/ofl/nunito/Nunito%5Bwght%5D.ttf (google/fonts 6049366, via the prequel's `fonts/Nunito.ttf`) | OFL 1.1 (`fonts/OFL-Nunito.txt`) | yes, as rendered glyphs | ExtraBold: episode title cards, results headings, battle bars (`redraw.py`, `redraw_results.py`, `redraw_battle.py`); Black: title logo (`redraw_title.py`) | static instances wght=800 / 900 (`python -m fontTools.varLib.instancer Nunito.ttf wght=800`) |
| `fonts/RobotoCondensed-Bold.ttf`, `fonts/RobotoCondensed-Regular.ttf` | https://github.com/google/fonts/blob/main/ofl/robotocondensed/RobotoCondensed%5Bwght%5D.ttf (google/fonts 45e3d52) | OFL 1.1 (`fonts/OFL-RobotoCondensed.txt`) | yes, as rendered glyphs | narrow labels: battle labels and STEP plates, title menu fallbacks, copyright line (`redraw_battle.py`, `redraw_title.py`) | static instances wght=700 / 400 |
| `fonts/DejaVuSansCondensed-Bold.ttf`, `fonts/DejaVuSansCondensed.ttf` | https://github.com/dejavu-fonts/dejavu-fonts/releases/tag/version_2_37 | Bitstream Vera / DejaVu licence (`fonts/LICENSE-DejaVu.txt`) | yes, as rendered glyphs | small hinted mono text 8-15 px: board labels, title menus, staff roll (`redraw_board.py`, `redraw_title.py`, `redraw_results.py`) | - |
| `fonts/LiberationSans-Bold.ttf` | https://github.com/liberationfonts/liberation-fonts/releases/tag/2.1.5 | OFL 1.1, Reserved Font Name Liberation (`fonts/OFL-Liberation.txt`) | yes, as rendered glyphs (unmodified file) | dress-up Yes/No (`redraw_clothes.py`) | - |
| Game font (ROM `/font/`) | original game | Konami; not in this repo | not redistributed | Japanese text | - |
