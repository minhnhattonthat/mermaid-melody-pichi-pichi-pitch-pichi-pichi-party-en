-- Switch the game mode: mode manager at IWRAM 0x03006300 {u32 current, u32 next, u8 phase (2 = leave current)}.
--   --var MODE=0x0829AF84 [--var AT=2150]   (mode structs: tools/debug/scenes.md; d_mode_menu = 0x0829AF84)
-- Also clears the retail flag 0x0201E968 so the debug menus behave as in development.
local at = AT or 2150
L.on_frame(function(f)
  emu.write32(0x0201E968, 0, emu.memType.gbaMemory)
  if f == at then
    emu.write32(0x03006304, MODE, emu.memType.gbaMemory)
    emu.write(0x03006308, 2, emu.memType.gbaMemory)
    L.log(string.format("mode <- %08X", MODE))
  end
end)
