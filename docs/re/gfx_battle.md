# Graphics: battle group

Script: `python -X utf8 tools/gfx/redraw_battle.py` (regenerates every PNG below). Test ROM: build/gfx_battle.gba.
Reach: battle mode MODE=0x0829C50C (+ `--mash 60`); other battles by forcing byte 0x0201EBE1 (tools/debug/scenes.md).
All files are 4bpp 2D sheets, 32 tiles wide (export `--tw 32`). Fonts: Arial Narrow Bold (labels, turn banners,
header bars), Arial Rounded Bold (enemy attack bars), pixfont (MISS). No abbreviations.

| file | content | screen / route | status |
|---|---|---|---|
| /battle/battle_bg_off.dcg | BG3 labels: アタックボイス / まもりのリズム / かわしステップ -> Attack Voice / Guard Rhythm / Dodge Step; ルーレットでまもれるよ / ルーレットでこうげき！ -> Guard with Roulette / Attack with Roulette!; ○～○でかわせるよ -> ○~○ to dodge (digit circles and ~ kept, digits are patched in by the game); ポイント / ダメージ plates -> Points / Damage | command menus of every battle (attack and defend turns); Damage plate after hits | done; verified (Points plate not seen on screen) |
| /battle/battle_bg_def.dcg | かわしステップ / まもりのリズム (pink variant) -> Dodge Step / Guard Rhythm | not referenced by name in code (nor b_def_bg.asc); looks unused | done for completeness, not seen |
| /battle/battle_call_bar.dcg | turn banners るちあ/はのん/リナ の ターン -> Lucia's Turn / Hanon's Turn / Rina's Turn; enemy call bars イズール/エリル/ユーリ/マリア/ガイト のこうげき, ハプニング！ -> Izuru's / Eriru's / Yuri's / Maria's / Gaito's Attack, Mishap! (both copies) | start of each turn; call bar when the enemy attacks / a mishap happens | done; verified |
| /battle/battle_def_bar_name.dcg | header bars: <enemy>のこうげき -> <enemy>'s Attack; ふりつけ / りょうり / デッサン / じゃれつき / やさしく -> Dance Moves / Cooking / Sketching / Playing / Gently | header during the defend phase (enemy battles) and contest rounds | done; verified Maria's Attack, Dance Moves, Sketching, Gently |
| /battle/battle_def_bar_icon.dcg | ミス burst (big + small) -> MISS; other icons have no text | contest rounds (missed steps) | done; verified |
| /battle/battle_bg.imb, battle_all, battle_all_cha, battle_cha_eff, battle_def_eff, battle_off_eff, battle_star | backgrounds, faces, digits, effects | all battles | no text |
| result_battle (MODE=0x0829B874) | no own graphics: the post-battle screen is /bg/*.imb + font text, then /mode/result/ screens (results group) | after a battle | nothing to do |
| /bastup/c22_00..c22_14.bst | contest STEP panels (STEP1 むずかしいステップ / STEP2 とちゅうのなんしょ / STEP3 さいごのキメポーズ etc., one file per contest) | right side of contest battles (ids 1, 12, 16, 18 seen) | NOT DONE: outside /battle/ and .bst unsupported by gfxfmt/export/apply (header 0xB0: section table {0x1C,0x80}{0x9C,8}{0xA4,0x640C}; tiles start at 0xB0, 800 tiles) |

Shots (work/gfx_battle/): zv1.png (turn banner, Attack Voice / Attack with Roulette!, Damage, Maria's Attack, Guard
Rhythm / Guard with Roulette), zv3.png (Dodge Step, 6~8 to dodge), zv6.png (blue "Maria's Attack" call bar), zep3.png
(Mishap!, Dance Moves), zmiss.png (MISS row; the bursts overlap each other as the original ミス ones do), zq.png (Sketching, Gently, MISS, untranslated STEP panels).
