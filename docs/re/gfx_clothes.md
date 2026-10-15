# Graphics group "clothes" (dress-up mode きせかえピッチ / in-story Change Clothes)

Generator: `python -X utf8 tools/gfx/redraw_clothes.py` (regenerates both PNGs). Test ROM: build/gfx_clothes.gba.
Shots: work/gfx_clothes/final (z1700 main screen, z1850 Yes/No, zhide), n6/z.png (L/R switch: Hanon selected).
Exports: cls_obj.dcg with `--tw 32 --pal <dump>.pal.bin --obj` (OBJ, 2D mapping, DISPCNT 0x1100); cls_name.dcg default.

| file | content | screen / route | status |
|---|---|---|---|
| /mode/clothes/cls_obj.dcg (OBJ, tw 32) | header きせかえ -> "DRESS-UP" (hand 5x12 caps stretched to 14 rows, white outline, original row gradient 3/2/6/2/e/1, bank 15) | dress-up, MODE=0x0829B8B0 | done, verified |
| same | はい/いいえ pills -> "Yes"/"No" (Arial Bold 13, white + 'd' shade, old kana rows 1-14 cleared) | B on dress-up -> "Back to the menu?" | done, verified |
| same | せつめいけす -> "Hide Info" (6-row pixel font, outline 5, bank 14) | dress-up, bottom bar next to SELECT | done, verified |
| same | name slots るちあ/はのん (x64..96 y0..16) -> Lucia/Hanon | overwritten at runtime from cls_name.dcg | done (placeholder) |
| same | name ribbon るちあ (x147..172 y4..11) -> "Lucia" | not seen on any screen reached | done, not verified on screen |
| /mode/clothes/cls_name.dcg (96x16) | L/R tags るちあ/はのん/リナ -> Lucia / Hanon / Rina | dress-up, L/R tags beside the character | done, verified |
| /mode/clothes/_cls_obj.dcg | older copy of cls_obj (きせかえ in a white box) | no code references it (only the FS table) | left Japanese: unused |
| /mode/clothes/cls_b_bg00.imb/.dcg, cls_b_wnd00.dcg, cls_p_icon.dcg, cls_char*, cls_p_* | backdrop, window frame, category icons, character/clothing parts | dress-up | no Japanese |
