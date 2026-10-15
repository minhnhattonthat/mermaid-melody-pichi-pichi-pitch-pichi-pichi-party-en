-- Force the next event script load: 0x0803A228(n) builds "/event/ev%06d.bin"; r0 <- EV on its first call(s).
--   --var EV=5150 [--var TIMES=1] [--var EV_FROM=2200]
local left, from = TIMES or 1, EV_FROM or 2200
L.on_exec(0x0803A228, 0x0803A228, function()
  if left <= 0 or L.frame < from then return end
  left = left - 1
  local s = emu.getState()
  s["cpu.r0"] = EV
  emu.setState(s)
  L.log(string.format("f%d event <- %d", L.frame, EV))
end)
