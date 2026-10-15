# Scene list (debug tool)

`EMU = python -X utf8 H:/translation/batch/.claude/skills/translate-retro-game/scripts/emu.py <rom>`
All from a cold boot. `tools/debug/mode.lua --var MODE=<struct> [--var AT=2150]` switches the game mode through the
mode manager (IWRAM 0x03006300 {current, next, phase=2}) and clears the retail flag 0x0201E968.
`tools/routes/mainmenu.txt` reaches the main menu (title -> START x3).

| scene | how |
|---|---|
| title, main menu, mode messages | `--route tools/routes/mainmenu.txt`, then up/down |
| story episode 1 (event ev000000, board game) | `--script tools/debug/mode.lua --var MODE=0x0829AD48` (mission_select), mash A |
| any event script | as above + `--script tools/debug/event.lua --var EV=5150` (forces the next event load) |
| ending / staff roll | MODE=0x0829AC84 (ending) |
| episode clear results | MODE=0x0829B888 (result_episodeend) |
| results: stage / kekka / battle / ev | MODE=0x0829B838 / 0x0829B84C / 0x0829B874 / 0x0829B810 |
| clothes (きせかえ) | MODE=0x0829B8B0 |
| link error | MODE=0x0829AD84 |
| name entry | MODE=0x0829B0F0 |
| title demo | MODE=0x0829B104 |
| save / continue | MODE=0x0829ACAC (sram) / 0x0829ACC0 (continue) |
| lobby | MODE=0x0829AD30 |

Mode structs {init, update, draw, 1, name} (ROM 0x29AC84..0x29B8FC): ending sram continue lobby mission_select
mission_loop mission_end linkerror bg_test d_mode_menu (black: needs the dev font) title name titledemo klogo commd
result_ev result_end result_stage result_kekka result_kekka2 result_battle result_episodeend clothes menu taguchi_menu.
Text windows: tools/lua/ctxlog.lua logs renderer calls; tools/winmap.py maps them to files.
