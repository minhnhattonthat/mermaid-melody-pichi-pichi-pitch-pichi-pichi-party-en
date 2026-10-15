-- Log text-window contexts passed to the renderer (0x0803843C) / map builder (0x08038904), once per distinct state.
--   emu.py ROM --script tools/lua/ctxlog.lua [--var FROM=0]
local from, seen = FROM or 0, {}
local function rd16(a) return emu.read16(a, emu.memType.gbaMemory) end
local function rd32(a) return emu.read32(a, emu.memType.gbaMemory) end
local function dump(tag)
  if L.frame < from then return end
  local c = emu.getState()["cpu.r0"] or emu.getState()["cpu.r[0]"]
  local s = string.format("%s ctx=%08X A=%d C=%d E=%d 4=%d 6=%d xy=%d,%d n=%d lines=%d v20=%X v24=%X pal=%d str=%08X",
    tag, c, rd16(c + 0xA), rd16(c + 0xC), rd16(c + 0xE), rd16(c + 4), rd16(c + 6), rd16(c + 0x18), rd16(c + 0x1A),
    rd16(c + 0x1C), rd16(c + 0x1E), rd32(c + 0x20), rd32(c + 0x24), rd16(c + 0x2A), rd32(c + 0x34))
  local k = s:gsub(" C=%d+ E=%d+ 4=%d+ 6=%d+", "")
  if LOGALL or not seen[k] then seen[k] = true; L.log(string.format("f%d %s", L.frame, s)) end
end
L.on_exec(0x0803843C, 0x0803843C, function() dump("R") end)
L.on_exec(0x08038904, 0x08038904, function() dump("M") end)
