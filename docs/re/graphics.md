# Graphics text (index)

Pipeline: tools/gfx/export.py -> gfx/orig/<name>.png; generators tools/gfx/redraw*.py -> gfx/en/<name>.png;
tools/gfx/apply.py writes them into the file-system files in place at build time (and validates them in check).
Formats: tools/gfx/gfxfmt.py (.dcg/.acg 4bpp tiles, headered .dcg w x h, .imb 8bpp, .bst panels via header_len).
Most OBJ sheets use 2D mapping: export with --tw 32 (titlebar 21, mokuteki 16, yesno 8, c22 .bst 40 = 8bpp 20 wide).

| group | files | report |
|---|---|---|
| episode title cards | /system/title/ev0000..3100.dcg (32) | tools/gfx/redraw.py ep_cards |
| title, logo, copyright, mode select, menus, name header | /mode/title/*, /mode/k_logo/logo.dcg | docs/re/gfx_title.md |
| name entry grid (Latin) | /mode/title/name.imb (+ code table tools/romdata.py NAME_GRID) | docs/re/gfx_name.md |
| board HUD, banners, destinations, map, roulette events | /system/common/*, /system/event/roulet_ev*, /map/map.imb, map_l.imb | docs/re/gfx_board.md |
| battles, contest STEP panels | /battle/*.dcg, /bastup/c22_*.bst | docs/re/gfx_battle.md |
| results, staff roll | /mode/result/*, /mode/ending/staff_roll.imb | docs/re/gfx_results.md |
| dress-up mode | /mode/clothes/cls_obj.dcg, cls_name.dcg | docs/re/gfx_clothes.md |

Surveyed without Japanese: /bg/*.imb (233 backgrounds), /chr/*, /bastup/c00-c21 portraits, clothes item art,
event effects. Kept Japanese on purpose: /mode/clothes/_cls_obj.dcg (old copy, no code loads it).
