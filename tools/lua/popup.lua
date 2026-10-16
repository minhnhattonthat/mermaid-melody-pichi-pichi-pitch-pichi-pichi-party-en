-- Screenshot the item/card pop-up (window ctx 0x02011AA8, composer 0x08039DCC..) 40 frames after it is drawn.
local pending, n = nil, 0
L.on_exec(0x0803843C, 0x0803843C, function()
  local c = emu.getState()["cpu.r0"]
  if c == 0x02011AA8 and not pending then pending = L.frame + 40 end
end)
L.on_frame(function(f)
  if pending and f >= pending then n = n + 1; L.shot(string.format("popup%02d_f%06d.png", n, f)); L.log("popup at f" .. f); pending = nil end
end)
