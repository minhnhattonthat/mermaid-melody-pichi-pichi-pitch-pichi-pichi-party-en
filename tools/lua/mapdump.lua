-- Print the text-window map shadow 0x0202520C (32x32 u16, rows Y0..Y1) at frames AT (comma list).
--   emu.py ROM --script tools/lua/mapdump.lua --var "AT={2400,2650}" [--var Y0=14 --var Y1=20]
local at, y0, y1 = AT or {}, Y0 or 14, Y1 or 20
local want = {}
for _, f in ipairs(at) do want[f] = true end
L.on_frame(function(f)
  if not want[f] then return end
  for y = y0, y1 do
    local t = {}
    for x = 0, 31 do t[#t + 1] = string.format("%04X", emu.read16(0x0202520C + (y * 32 + x) * 2, emu.memType.gbaMemory)) end
    L.log(string.format("f%d y%02d %s", f, y, table.concat(t, " ")))
  end
end)
