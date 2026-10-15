# Graphics group "title"

Generator: `python -X utf8 tools/gfx/redraw_title.py [part ..]` (parts: title_obj title_serect title_menu k_logo
press_start name_entry logo). Test ROM: build/gfx_title.gba. Shots: work/gfx_title/final_*/ (zoomed checks in
work/gfx_title/*.png).

Layout facts found here:
- title_obj, title_serect, title_menu are OBJ sheets loaded 1:1 into 2D-mapped OBJ VRAM: export with `--tw 32`.
- title_logo.acg is **8bpp** OBJ (2D, 128 px per 1 KB row) plus a 0x460-byte IS-ACG03 trailer (file 0x8460 bytes,
  not a multiple of 64). export.py cannot export it (it drops the last half tile), so redraw_title.py writes
  gfx/orig/mode__title__title_logo.acg.png itself (128x272, 8bpp, trailer kept as pixels; apply.py round-trips it).
  At rest: Party block = OAM 0-3 (256x64 at y 48), Pitch block = OAM 4-8 (y 16) + 9-11 (y 8); the Pitch cloud's
  bottom rows are drawn by the Party sprites. OBJ palette 224-239 belongs to title_logo01, so the logo uses 0-223.
- logo.dcg (Konami/copyright) is OBJ 2D, 240x24 used: line 1 rows 1-8, line 2 rows 12-18; grey ramp 15..1.

| file | content | screen / route | status |
|---|---|---|---|
| /mode/k_logo/logo.dcg | (C)講談社・ウィーヴ・テレビ愛知／ぴちぴちピッチ製作委員会 -> "(C) Kodansha, We've, TV Aichi / Pichi Pichi Pitch Production Committee" (Arial Narrow 9, anti-aliased on the ramp; (C) moved 3 px left) | cold boot f850 | done, verified (final_title/f000850.png) |
| /mode/title/title_logo.acg | logo: マーメイドメロディー / ぴちぴちピッチ / ぴちぴちパーティー -> "Mermaid Melody" (rainbow letters) / "Pichi Pichi Pitch" (pink, cloud enlarged) / "Pichi Pichi Party" (yellow on the pink plate, ribbon kept); small romaji "Pichi Pichi Pitch" line dropped (now the big line) | title (route 2100 -;5 start) | done, verified (final_logo/f002300.png, t2/f002300.png) |
| /mode/title/title_logo01.dcg | スタートボタンをおしてね -> "Press START!" | title | done, verified |
| /mode/title/title_obj.dcg | header モードセレクト -> Mode Select; Solo / Party / Link / All-Out / Dress-Up Pitch; pills 1/2/3プレイヤー, コンピューター -> Player 1/2/3, Computer | main menu, character select | done, verified (final_title/f002550.png, final_solo/f002650.png) |
| /mode/title/title_serect.dcg | Lucia, Hanon, Rina; けっていする♪ -> Confirm ♪; エピソード -> Episodes; Two/Three Players; mode names; Practice; New Game, Continue; Hard Rules, Easy Rules; むずかしい/ふつう/かんたん -> Hard/Normal/Easy | char select, players, rules, game length, story | done; all verified except Hard/Normal/Easy (no route found that shows them) |
| /mode/title/title_menu.dcg | headers: Mode Select, Checking Link, Players, Character Select, Game Length (エピソードのかず), Load Save, Story... (おはなしの・・・, over New Game/Continue), Turn Order | menus after START | done, all 8 verified (final_*) |
| /mode/title/name.imb | header カートリッジになまえをつけてね -> "Name your cartridge!"; help bar タイトル/けってい/もどる -> Title / OK / Back (kana grid left as is) | MODE=0x0829B0F0 | done, verified (final_name/f002400.png) |
| /mode/title/title_num.dcg | digits 0-9 | game length | no text, unchanged |
| /system/common/save_number.dcg | save slot icons 1-3 | load save | no text, unchanged |
| /system/common/modetitle.dcg | board ribbons (コマンド, カード, ...) and space banners | board game | owned by redraw_board.py (board group drew it too); title script does not touch it |
