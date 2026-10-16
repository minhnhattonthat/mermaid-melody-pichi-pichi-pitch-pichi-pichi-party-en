-- Force an event script. Two entry points load scripts:
--   0x0803A228(n) builds "/event/ev%06d.bin" (title demo, some modes)  -> r0 <- EV
--   0x0803A27C(file) takes the file pointer (story episodes)          -> r0 <- EVPTR (0x08xxxxxx of the file)
-- Only calls at frame >= EV_FROM count, TIMES times in total (default 1).
--   --var EV=5150 --var EVPTR=0x08ABCDEF [--var TIMES=1] [--var EV_FROM=2400]
-- tools/qa_tour.py computes EVPTR from the ROM's file system (tools/fs.py).
local left, from = TIMES or 1, EV_FROM or 2400
local function set_r0(v, tag)
  local s = emu.getState()
  s["cpu.r0"] = v
  emu.setState(s)
  left = left - 1
  L.log(string.format("f%d %s <- %X", L.frame, tag, v))
end
local function in_title()  -- title demo / Konami logo modes also load scripts: never replace those
  local m = emu.read32(0x03006300, emu.memType.gbaMemory)
  return m == 0 or m == 0x0829B104 or m == 0x0829B118
end
L.on_exec(0x0803A228, 0x0803A228, function()
  if left > 0 and L.frame >= from and EV and not in_title() then set_r0(EV, "event number") end
end)
L.on_exec(0x0803A27C, 0x0803A27C, function()
  if left <= 0 or L.frame < from or not EVPTR then return end
  local s = emu.getState()
  local lr = s["cpu.r14"] or s["cpu.r[14]"] or 0
  if (lr & ~1) == 0x0803A266 then return end  -- called from 0x0803A228 (title demo): not a story load
  set_r0(EVPTR, "event file")
end)
