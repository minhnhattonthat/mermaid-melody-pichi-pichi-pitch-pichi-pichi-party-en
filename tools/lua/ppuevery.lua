-- Dump PPU (vram/pal/oam/io) every PPU_EVERY frames from PPU_FROM: <out>/p<frame>.*  (pair with --shot-every)
local every, from = PPU_EVERY or 300, PPU_FROM or 0
L.on_frame(function(f) if f >= from and f % every == 0 then L.dump_ppu(string.format("p%06d", f)) end end)
