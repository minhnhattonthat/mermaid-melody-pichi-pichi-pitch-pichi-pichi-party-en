-- Board-game macro: keep mashing (emu.py --mash) until the command menu (コマンド: Move / Use Card / Change Clothes /
-- View Map / System) opens for the AFTER-th time, then stop mashing and play SEQ (route steps separated by ';').
--   --var "SEQ='30 -;5 up;30 -;5 a;120 -;5 a'" [--var AFTER=1]
-- Menu detection: the text renderer 0x0803843C drawing a window with 7 chars per line at map x=18 (cmd entries).
-- Do not pass --mash: this script mashes A itself (every 40 frames after frame MASH_FROM) until it fires.
local after, seen, armed, last = AFTER or 1, 0, true, -100
local mash_from = MASH_FROM or 2400
L.on_frame(function(f)
  if armed and f >= mash_from and f % 40 == 0 and L.route_done() then L.press("a", 6) end
end)
L.on_exec(0x0803843C, 0x0803843C, function()
  if not armed then return end
  local c = emu.getState()["cpu.r0"]
  local n = emu.read16(c + 0x1C, emu.memType.gbaMemory)
  local x = emu.read16(c + 0x18, emu.memType.gbaMemory)
  local y = emu.read16(c + 0x1A, emu.memType.gbaMemory)
  if n == 7 and x == 18 and y == 3 and L.frame - last > 60 then
    last = L.frame
    seen = seen + 1
    L.log(string.format("f%d command menu #%d", L.frame, seen))
    if seen >= after then
      armed = false
      for step in SEQ:gmatch("[^;]+") do
        local f, spec = step:match("^%s*(%d+)%s+(%S+)%s*$")
        L.press(spec, tonumber(f))
      end
    end
  end
end)
