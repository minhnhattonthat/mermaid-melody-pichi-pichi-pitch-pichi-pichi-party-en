# Graphics group "results" (episode clear, results, today's heroine, staff roll)

Generator: `python -X utf8 tools/gfx/redraw_results.py` (regenerates every PNG below). Test ROM: build/gfx_results.gba.
Shots: work/gfx_results/ (n_epend, n_kekka, n_stage, n_battle, q_stage, n_ending, v2_epend; zooms z_*.png).

| file | content | screen / route | status |
|---|---|---|---|
| /mode/result/res_ep_bg_0.imb (8bpp BG) | エピソードクリア！ -> "Episode Clear!" (white letters, blue per-row outline, pale halo; old text inpainted row-wise) | episode clear, MODE=0x0829B888 | done, verified |
| /mode/result/cmd_res.imb (8bpp BG) | けっかはっぴょう -> "Results"; bar エピソード/るちあ/はのん/リナ -> Episode / Lucia / Hanon / Rina | results, MODE=0x0829B84C (also after 0x0829B888/B838/B874) | done, verified |
| /mode/result/cmd_stag.imb (8bpp BG) | 今日のヒロイン -> "Today's Heroine" (yellow on wooden plate) | today's heroine (MODE=0x0829B838 or 0x0829B888, no mash) | done, verified |
| /mode/result/result_obj.dcg (OBJ, 2D mapping, export --tw 32) | name tags るちあ/はのん/リナ -> Lucia/Hanon/Rina (bank 0); ボードマップ/ラストバトル/ヒロインポイント -> Board Map / Last Battle / Heroine Points (bank 3); エピソード -> Episode (bank 3, no screen seen); ヒロインポイントごうけい -> Heroine Points / Total (bank 8, tab above the box removed) | episode clear + results | done, verified (Episode tag not seen on screen) |
| /mode/ending/staff_roll.imb (4bpp, 240x1600) | full credits re-laid out in English (Tahoma 11, ink 3 + white shadow 15 at +1,+1); all Japanese erased + inpainted | ending, MODE=0x0829AC84, 60-frame shots to f8500 | done, verified |

## Staff roll decisions (best effort; uncertain readings flagged ?)
Headings: 原作 Original Work, 原案 Original Concept, まんが Manga, シナリオ Scenario, キャスト Cast, 企画 Planning,
制作協力 Production Cooperation, スーパーバイザー Supervisor, 開発プロデューサー/ディレクター/プランナー Development
Producer/Director/Planner, メインプログラム Main Programming, プログラム Programming, サウンドデザイン Sound Design,
メイングラフィック Main Graphics, グラフィック Graphics, スクリプト Script, 原画協力 Key Art Cooperation, グラフィック協力
Graphics Cooperation, 音声収録 Voice Recording, キャスティング協力 Casting Cooperation, 解説書制作 Manual Production,
パッケージ・付録制作 Package and Extras Production (2 lines), イラスト制作 Illustration Production, HP制作 Website Production,
デバッグ Debugging, 挿入曲 Insert Songs, 作詞/作曲 Lyrics/Music, スペシャルサンクス Special Thanks, プロダクトコーディネーター
Product Coordinator, プロデューサー Producer, 制作 Production, 製作 Publisher.
Reused from the prequel: Kodansha, We've; Pink Hanamori; Michiko Yokote; (Serialized in Kodansha's Nakayoshi); cast
(Asumi Nakata, Hitomi Terakado, Mayumi Asano); Yukiko Mitsui, Tetsuya Ouchi, Koji Hayashi, Tetsuya Fukuda, Seiji Katsu;
Zack Promotion; Pony Canyon; Konami Computer Entertainment Japan; "Paradise of the Sun ~Promised Land~".
Flagged readings: 下道 隆 Takashi Shimomichi?, 井上 季郎 Toshiro Inoue?, 高橋 光規 Mitsunori?, 玉置 祐康 Hiroyasu?,
森井 剛 Tsuyoshi?, 椎名 恵水 Emi?, 正田 川太郎 Kawataro Shoda?, エルスウェア Elsewhere?, 川口 祐幸 Hiroyuki?,
神南スタジオ Jinnan Studio?, 八代 筆 (glyph looks like 筆; read as 肇 Hajime Yashiro?), 米堂 謙子 Kenko Yonedo?,
河本 清澄 Kiyosumi?, 白戸 雄之 Takeyuki Shirato?, 松隈 倫 Rin?, 中原 郁奈子 Kanako?, 百谷 あおい Aoi Momotani?,
大久 保政秋 read as 大久保 政秋 Masaaki Okubo, 岡村 憲明 Noriaki?. 夢のその先へ -> "Beyond Our Dreams" (no official title
known). 「」 -> "..."; the ♪ after "Rainbow Notes" was dropped (font has no glyph).
