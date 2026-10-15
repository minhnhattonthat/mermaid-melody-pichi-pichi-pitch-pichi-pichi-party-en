-- Log visible OAM entries, DISPCNT and BGxCNT at frame AT (GBA Mesen).  --var AT=1234
L.on_frame(function(f) if f == AT then
  for i = 0, 127 do
    local a = 0x07000000 + i * 8
    local a0 = emu.read16(a, emu.memType.gbaMemory)
    local a1 = emu.read16(a + 2, emu.memType.gbaMemory)
    local a2 = emu.read16(a + 4, emu.memType.gbaMemory)
    if (a0 & 0x0300) ~= 0x0200 and (a0 & 0xFF) < 160 then
      L.log(string.format('%3d y=%d x=%d shape=%d size=%d tile=%X pal=%d prio=%d', i, a0 & 0xFF, a1 & 0x1FF,
        a0 >> 14, a1 >> 14, a2 & 0x3FF, a2 >> 12, (a2 >> 10) & 3))
    end
  end
  L.log(string.format('DISPCNT %04X', emu.read16(0x04000000, emu.memType.gbaMemory)))
  for b = 0, 3 do L.log(string.format('BG%dCNT %04X', b, emu.read16(0x04000008 + 2 * b, emu.memType.gbaMemory))) end
end end)
