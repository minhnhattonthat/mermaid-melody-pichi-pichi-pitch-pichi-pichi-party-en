-- Switch the game mode: mode manager at IWRAM 0x03006300 {u32 current, u32 next, u8 phase (2 = leave current)}.
--   --var MODE=0x0829AF84 [--var AT=1500]   (mode structs: tools/debug/scenes.md)
-- Waits until frame AT and until the title screen ("titledemo" mode 0x0829B104) is current and idle, then switches once.
-- Also clears the retail flag 0x0201E968. Logs "mode <- X at fN": routes after it should wait on that, not on frames.
local at, done = AT or 1500, false
L.on_frame(function(f)
  emu.write32(0x0201E968, 0, emu.memType.gbaMemory)
  if done or f < at then return end
  local cur = emu.read32(0x03006300, emu.memType.gbaMemory)
  local phase = emu.read(0x03006308, emu.memType.gbaMemory)
  if cur == 0x0829B104 and phase == 1 then
    emu.write32(0x03006304, MODE, emu.memType.gbaMemory)
    emu.write(0x03006308, 2, emu.memType.gbaMemory)
    done = true
    L.log(string.format("mode <- %08X at f%d", MODE, f))
  end
end)
