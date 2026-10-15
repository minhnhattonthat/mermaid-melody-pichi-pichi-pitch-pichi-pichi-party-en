-- Log every graphics chunk decode (src ROM addr, size) and the DMA that copies the decode buffer out (dest).
-- Lines: "f<frame> DEC src=<rom> n=<size> add=<add>" and "f<frame> DMA sad=.. dad=.. cnt=.. ctl=..".
-- [--var FROM=..]
local from = FROM or 0
L.on_exec(0x03000BA4, 0x03000BA4, function()
  if L.frame < from then return end
  local s = emu.getState()
  L.log(string.format("f%d DEC src=%08X n=%X add=%X dst=%08X", L.frame, s["cpu.r1"], s["cpu.r2"], s["cpu.r3"], s["cpu.r0"]))
end)
local reg = {}
L.on_write(0x040000B0, 0x040000DF, function(addr, v)
  local o = (addr & 0xFF) - 0xB0
  local ch, k = o // 12, o % 12
  reg[ch] = reg[ch] or {}
  local r = reg[ch]
  if k == 0 then r.sad = v return elseif k == 4 then r.dad = v return end
  local cnt
  if k == 8 then cnt = v & 0xFFFF; v = (v >> 16) & 0xFFFF elseif k == 10 then cnt = r.cnt or 0 else return end
  r.cnt = cnt
  if (v & 0x8000) == 0 or L.frame < from then return end
  local sad = r.sad or 0
  if sad < 0x03006900 or sad >= 0x03007900 then return end
  L.log(string.format("f%d DMA sad=%08X dad=%08X cnt=%04X ctl=%04X", L.frame, sad, r.dad or 0, cnt, v))
end)
