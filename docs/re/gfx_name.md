# Graphics group: name (name entry character grid)

| file | content | screen / route | status |
|---|---|---|---|
| /mode/title/name.imb | 5x12 kana grid -> Latin letters of tools/romdata.py NAME_ROWS (A-Z, a-z, ! ? . - ' &); space and OK cells kept. Header + help bar are redraw_title.py's work, untouched | name entry, `tools/debug/mode.lua --var MODE=0x0829B0F0` | done, verified in game |

Generator: tools/gfx/redraw_name.py. It calls `redraw_title.name_entry()` first (header + help bar), then repaints
the grid on that output (gfx/en/mode__title__name.imb.png), so running redraw_name.py alone regenerates the full PNG.
Order if both are run: redraw_title.py, then redraw_name.py (running redraw_title.py afterwards would restore the kana).

Style: MS Gothic 14 px full-width forms (embedded 1-bit strike, kana-sized, 1-px strokes) in white (223) with the kana's
dark drop shadow (2) right/below, centred on the original cell centres x = 24 40 55 72 87 111 127 143 159 175 200 216,
y = 71 87 103 119 135. Kana erased by colour diffusion of the panel background, mapped to colours the file already uses.
The old dakuten/handakuten/long-vowel cells now hold K, L, W, X (matching NAME_ROWS).

Verified: work/qa/gfx_name/final_x3.png (route A, right, A, down, A, down x2, A, right x3, A -> field shows "ABNlo"),
work/qa/gfx_name/f002440_crop.png (cursor box centred on B).
