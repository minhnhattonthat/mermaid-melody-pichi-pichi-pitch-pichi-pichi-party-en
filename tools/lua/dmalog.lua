-- GBA DMA log: each DMA start (CNT_H enable bit) logs channel, SAD, DAD, count, pc. DMA regs are write-only, so
-- SAD/DAD are tracked from the writes. --var FROM=.. --var TO=.. [--var DST_LO=0x02000000 --var DST_HI=0x02040000]
local from, to = FROM or 0, TO or math.huge
local dlo, dhi = DST_LO or 0, DST_HI or 0xFFFFFFFF
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
  if (v & 0x8000) == 0 or L.frame < from or L.frame > to then return end
  local dad = r.dad or 0
  if dad < dlo or dad >= dhi then return end
  L.log(string.format("f%d pc=%08X ch=%d sad=%08X dad=%08X cnt=%04X ctl=%04X", L.frame, L.pc(), ch, r.sad or 0, dad, cnt, v))
end)
