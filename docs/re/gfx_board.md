# Graphics group "board" (story-mode board game)

Generator: `python -X utf8 tools/gfx/redraw_board.py [part ..]` (parts: board, board_map, map_goal, roulet_ev,
status_icons, titlebars, modetitle, map_mokuteki, mokuteki, destination, yesno, roulet_obj, map_rank, status_obj,
roulet_obj_drum). Test ROM: `build/gfx_board.gba`. Route: `tools/debug/mode.lua --var MODE=0x0829AD48 --mash 50`
from cold boot. Shots: work/qa/gfx_board/en3/ (0-24600), goal/ (to 34000), goal2/ (state goal/s030000.mss + 12000);
Japanese reference run: work/qa/gfx_board/orig/ (PPU dumps every 150 frames; the original reaches the episode goal at
~23850, the English run had not reached it by ~42000).

Findings
- OBJ VRAM uses 2D mapping (DISPCNT 0x1F00): most OBJ sheets are 32 tiles wide (export --tw 32); titlebar 21,
  mokuteki 16, yesno 8 (rows of two 32x16 bubbles). Palettes are OBJ banks of the dumps (titlebar 14, mokuteki 15,
  map_mokuteki 7, map_goal 12/13, modetitle 12/15, yesno 12/13, roulet_ev 11).
- /map/map.imb is the whole 1440x960 board (8bpp linear tiles, 180 tiles wide); the place-name pills are part of it.
- The destination banner is: tag (map_mokuteki arrow tag, fixed screen x 126) + name (mokuteki*, right-aligned,
  screen x 104-199, drawn over the tag) + destination.dcg tiles 0-4 ("へ ___ マス") + digits. The tag position does
  not depend on the name, so long names cover the tag (also in Japanese). English names get a dark plate so the
  cut is clean; the tag ("Go to" / "Goal!") shows beside short names.

| file | content | screen / route | status |
|---|---|---|---|
| /system/common/titlebar0.dcg, titlebar1.dcg, titlebar2.dcg | 33 episode banners (♪ + title) | pink bar at the top of the board | English (glossary episode titles, Practice), Tahoma Bold 10-12 |
| /system/common/modetitle.dcg | window header ribbons コマンド カード きがえ マップをみる きろく かいもの じょうほう カードセット; star banners ハプニング! カード! おかいもの! ラッキー! | Command / card / clothes windows, Lucky list | Command, Cards, Clothes, View Map, Save, Shopping, Info, Card Set; Mishap!, Card!, Shopping!, Lucky! |
| /system/common/map_mokuteki.dcg | name tags るちあ/はのん/リナ, destination pins もくてきち, arrow tags もくてきち, ゴール! | board pins above the destination, banner tag | LUCIA/HANON/RINA (tiny caps, 21 px), Here!, Go to, Goal! |
| /system/common/mokuteki.dcg, mokuteki_1.dcg, mokuteki_2.dcg, mokuteki_3.dcg | 49 destination names | banner under the episode bar | English (blk_info place names, shops as in dialogue) |
| /system/common/destination.dcg | へ ___ マス, ゴール! tag, banner copy, sample name | banner | へ dropped, マス -> "left" ("Shrine 7 left"), Goal!, The Light of Love, Surfing Beach |
| /system/common/yesno.dcg | はい/いいえ, つかう/すてる, きがえ/すてる bubbles | dialogue choices | Yes/No, Use/Toss, Wear/Toss |
| /system/common/roulet_obj.dcg | pink はい/いいえ, corner コンピューター, マップ, みる | board corner, Stop here? choice | Yes/No, COMPUTER, MAP, VIEW (tiny caps) |
| /system/common/map_rank.dcg | やったね!1位, いいかんじ!2位, がんばれ!3位 | status window rank | Yay! 1st, Nice! 2nd, Go for it! 3rd |
| /system/common/status_obj.dcg | やったね! 1 位 | status window | Yay! 1st |
| /system/common/roulet_obj_drum.dcg | ハプニング! banner, カードゲット! sign | Mishap list, card pickup | Mishap!, Got a Card! |
| /system/common/map_goal.dcg | とうちゃく!, ヒロインポイント ゲット!, ゴール!, 1 2 3 ちゃく, ゴールまで __ マス, ゴールした人だけボーナス, ペアボーナス, デートボーナス | arrival, points award, episode goal | Arrived!, Heroine Points / Up! verified; Goal!, 1st 2nd 3rd + Place, To Goal / left, BONUS FOR FINISHERS, Pair Bonus, Date Bonus drawn, episode goal not reached |
| /system/common/status_obj_icon.dcg, status_obj_goukei.dcg, status_obj_pts.dcg | stat names, ヒロインポイント ごうけい badge, ランダムポイント | stats screens (not reached on this route) | English, not seen on screen |
| /system/event/roulet_ev.dcg, roulet_ev0.dcg, roulet_ev1.dcg | せいこう! しっぱい……, stat strips, ごうけい strip (two stacked 32x8 sprites) | roulette challenge events | NIMBLE STEPS / UNBEATABLE HEART / TOTAL verified on screen; Success!, Failed..., SINGING POWER not reached |
| /map/map.imb | 19 place-name pills on the board | board scroll | English caps (pills widened where needed) |
| /map/map_l.imb | caption ぴちぴちピッチボードマップ | View Map | Pichi Pichi Pitch Board Map (Tahoma Bold 8; View Map not reached by the mash route) |
| card_level, mnote, map_frame, map_pageicon, cursor_anim, win_bg_hukidasi, evicon, map_l_ficon/ticon, effect*.dcg, roulet_obj_eventstar, roulet_suuji_big | icons, digits, frames ("Lv" already Latin) | | no Japanese, untouched |

Notes
- No abbreviations. Wording choices: もくてきち -> "Go to" (banner tag) / "Here!" (board pin: "Destination" does
  not fit 26 px); マス after the count -> "left" (16 px slot); ハプニング -> "Mishap" (as blk_info); すてる -> "Toss".
- ちゅうおうひろば label -> "Central Plaza" (the board pill ちゅうおうこうえん is "Central Park").
