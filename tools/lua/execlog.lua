-- Log registers each time EXEC_AT runs (GBA Mesen). --var EXEC_AT=0x080005D6 [--var FROM=..] [--var MAXN=200]
-- [--var COND='function(r) return r[1]>=0x06017400 end'] (r[0..15] = r0..r15)
local from, maxn, n = FROM or 0, MAXN or 200, 0
local function regs()
  local s, r = emu.getState(), {}
  for i = 0, 15 do r[i] = s["cpu.r" .. i] or s["cpu.r[" .. i .. "]"] or 0 end
  return r
end
if DUMPKEYS then
  L.on_frame(function(f) if f == 10 then
    local ks = {}
    for k, v in pairs(emu.getState()) do if k:sub(1, 4) == "cpu." then ks[#ks + 1] = k .. "=" .. tostring(v) end end
    table.sort(ks); L.log(table.concat(ks, " "))
  end end)
end
if EXEC_AT then
  L.on_exec(EXEC_AT, EXEC_AT, function()
    if L.frame < from or n >= maxn then return end
    local r = regs()
    if COND and not COND(r) then return end
    n = n + 1
    local t = {}
    for i = 0, 14 do t[#t + 1] = string.format("r%d=%08X", i, r[i]) end
    L.log(string.format("f%d %s", L.frame, table.concat(t, " ")))
  end)
end
