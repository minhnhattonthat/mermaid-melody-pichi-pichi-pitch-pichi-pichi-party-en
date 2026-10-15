# RE notes: Mermaid Melody Pichi Pichi Pitch: Pichi Pichi Party (GBA, Konami 2004, AGB-BM8J)

Base ROM: `rom/Mermaid Melody - Pichi Pichi Pitch - Pichi Pichi Party (Japan).gba`, 16 MiB,
SHA-1 79571b4d16098ff04f2c9ddb3880d67a01ade4a7. Header title PICHIPICHI2, code BM8J.
Different engine from the prequel (sibling repo): only the glossary and the English glyph art carry over.

## Game
Board game (sugoroku) with story events, mini-game "battles", cards, items, clothes. Text is font-rendered
(dialogue, menus, cards, items); title/menus also have graphics text.

## File system (tools/fs.py)
"DFI\0" directory at 0x2E0000, 16-byte entries {s16 child, s16 next, u32 name (rel. to entry), u32 data/4, u32 size};
file offset = 0x2F0000 + 4*data. Lookup by path 0x08043E68. Files are stored uncompressed.
Text-bearing files: /event/ev*.bin (201 scripts), /battle/msg/*.bms(+.bmh), /system/textbin/*.bms(+.bmh),
/mode/title/title_msg.bms, /mode/clothes/*.bms, /mode/linkerror/linkerror.bms. Strings in code: ~0x4D000-0x51000.

## Text encoding (16-bit LE codes)
- 0x000-0x20B: JIS X 0208 rows 1-8, defined cells only, in JIS order (0x000 = full-width space, 0x01B = ー,
  0x08F.. digits, 0x0D1 = ぁ, 0x124 = ァ). 0x20C-0x25E: NEC row 13 (①.. etc.), some cells replaced by game icons.
  0x25F-0x416: school kanji grades 1-3 in the official per-grade order; 0x417-0x41F: extra kanji (宝堂斗郎妖洞院..).
- 0x4000|h: half-width glyph h from /font/pfont12h.imb (h = ASCII + 0x10; 0x4030 = half space). JIS X 0201 kana at 0xB0+.
- 0x8000 end of string, 0x8001 newline.

## Fonts
/font/pfont12z.imb (0xC821DC, 0x21000): 1056 glyphs 16x16 4bpp, sheet 32 tiles wide (glyph c: tile (c//16)*64 +
(c%16)*2, bottom row +32 tiles). Colours 1 = body, 2 = shadow. /font/pfont12h.imb (0xC7E1D4): 256 glyphs 8x16,
sheet 16 tiles wide.

## Renderer
0x0803843C(ctx): draws ctx+0x34 string into the tile buffer 0x020221D0 (column-major, 2 tiles per column), full-width
advance 12 px, half-width 8 px; positions are 4-px granular (halfword shifts). ctx+4 chars to draw, +6 drawn so far,
+0xC/+0xE pen state, +0x2C full font, +0x30 half font.

## Event scripts (/event/ev%06d.bin, loader 0x0803A228(n) -> 0x0803A27C(file))
Header {u32 n=3, (off,size) x3}: bytecode (u16), string offset table (u32, byte offsets into section 2), strings.
