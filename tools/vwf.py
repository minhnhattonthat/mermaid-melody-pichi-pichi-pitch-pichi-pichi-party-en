"""VWF: replacement for the text renderer 0x0803843C and its tilemap builder 0x08038904 (Thumb, keystone).

Window context (ctx, r0): +0 active, +4 chars to show (typewriter target), +6 chars drawn, +0xA start word index,
+0xC current line word index (ours), +0xE pen x in pixels (ours), +0x18/+0x1A map x/y (tiles), +0x1C chars per line,
+0x1E lines, +0x20/+0x24 VRAM tile area (bytes; area word offset = (+0x24 - +0x20) / 4), +0x2A palette,
+0x2C full font, +0x30 half font, +0x34 string (u16 codes; 0x8000 end, 0x8001 newline).
Tile buffer 0x020221D0: per line, columns of 2 tiles (top, bottom); words per line = tiles_per_line * 8,
tiles_per_line = 2 * (3 * (n >> 1) + 2 * (n & 1)) for n chars (0x08038428). Pixel (x, y) of a line is word
line + (x >> 3) * 16 + y, nibble x & 7.
Glyphs: code & 0x4000 -> h = code & 0xFF: our proportional 2bpp glyph (table EN, 16 rows x u32) when ADV[h] != 0,
else the original 8x16 half-width glyph (advance 8). Other codes: the 16x16 full-width glyph, advance 12.
The map builder lays tiles out in the same regular order (top = area + line * tpl + 2 * col, bottom = top + 1).
"""
import struct
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB

RENDER, MAPB = 0x03843C, 0x038904

ASM = r"""
render:
    push {r4-r7, lr}
    mov r4, r8
    mov r5, r9
    mov r6, r10
    mov r7, r11
    push {r4-r7}
    sub sp, #48
    mov r8, r0
    ldr r1, lit_dmacnt
    ldrh r1, [r1]
    movs r2, #0xC0
    lsls r2, r2, #4
    cmp r1, r2
    bhi ret0
    ldr r1, [r0, #0x2C]
    cmp r1, #0
    beq ret0
    ldr r1, [r0, #0x34]
    cmp r1, #0
    beq ret0
    ldrh r1, [r0, #4]
    cmp r1, #0
    bne go
    b ret
ret0:
    movs r0, #0
    b ret
go:
    ldr r1, [r0, #0x24]
    ldr r2, [r0, #0x20]
    subs r1, r1, r2
    lsrs r1, r1, #5
    lsls r1, r1, #3
    str r1, [sp, #0]
    ldrh r0, [r0, #0x1C]
    bl tiles
    str r0, [sp, #4]
    lsls r1, r0, #2
    mov r9, r1
    mov r0, r8
    ldrh r1, [r0, #0x1E]
    ldr r2, [sp, #4]
    muls r2, r1, r2
    str r2, [sp, #8]
    ldr r1, lit_buf
    mov r10, r1
    ldrh r1, [r0, #6]
    cmp r1, #0
    bne cont
    ldrh r2, [r0, #0xA]
    strh r2, [r0, #0xC]
    movs r2, #0
    strh r2, [r0, #0xE]
    ldr r1, [sp, #0]
    lsls r1, r1, #2
    add r1, r10
    ldr r3, [sp, #8]
    lsls r3, r3, #5
clr:
    cmp r3, #0
    ble cont
    str r2, [r1]
    adds r1, #4
    subs r3, #4
    b clr
cont:
    mov r0, r8
    ldrh r1, [r0, #0xC]
    mov r11, r1
loop:
    mov r0, r8
    ldrh r6, [r0, #6]
    ldrh r1, [r0, #4]
    cmp r6, r1
    blo lp_go
    b done
lp_go:
    ldr r2, [r0, #0x34]
    lsls r3, r6, #1
    ldrh r5, [r2, r3]
    ldr r3, lit_8000
    cmp r5, r3
    bne lp_ch
    b done
lp_ch:
    adds r6, #1
    strh r6, [r0, #6]
    adds r3, #1
    cmp r5, r3
    bne notnl
    ldr r2, [sp, #4]
    lsls r2, r2, #3
    add r11, r2
    mov r1, r11
    strh r1, [r0, #0xC]
    movs r1, #0
    strh r1, [r0, #0xE]
    b loop
notnl:
    lsrs r3, r5, #15
    bne loop
    lsls r3, r5, #17
    lsrs r3, r3, #31
    beq full
    lsls r1, r5, #24
    lsrs r1, r1, #24
    ldr r2, lit_adv
    ldrb r7, [r2, r1]
    cmp r7, #0
    beq halforig
    lsls r1, r1, #6
    ldr r2, lit_en
    adds r6, r1, r2
    movs r4, #0
en_y:
    lsls r3, r4, #2
    ldr r3, [r6, r3]
    str r3, [sp, #16]
    movs r5, #0
en_x:
    ldr r3, [sp, #16]
    lsls r2, r5, #1
    lsrs r3, r3, r2
    movs r2, #3
    ands r2, r3
    beq en_nx
    mov r0, r8
    ldrh r0, [r0, #0xE]
    adds r0, r0, r5
    adds r1, r4, #0
    bl plot
en_nx:
    adds r5, #1
    cmp r5, r7
    blt en_x
    adds r4, #1
    cmp r4, #16
    blt en_y
    b advance
halforig:
    mov r0, r8
    ldr r6, [r0, #0x30]
    lsrs r2, r1, #4
    lsls r2, r2, #10
    adds r6, r6, r2
    movs r2, #15
    ands r2, r1
    lsls r2, r2, #5
    adds r6, r6, r2
    movs r2, #2
    lsls r2, r2, #8
    str r2, [sp, #20]
    movs r2, #8
    str r2, [sp, #24]
    movs r7, #8
    b draw4
full:
    mov r0, r8
    ldr r6, [r0, #0x2C]
    lsrs r2, r5, #4
    lsls r2, r2, #11
    adds r6, r6, r2
    movs r2, #15
    ands r2, r5
    lsls r2, r2, #6
    adds r6, r6, r2
    movs r2, #4
    lsls r2, r2, #8
    str r2, [sp, #20]
    movs r2, #12
    str r2, [sp, #24]
    movs r7, #16
draw4:
    movs r4, #0
d4_y:
    lsls r3, r4, #29
    lsrs r3, r3, #27
    adds r3, r3, r6
    cmp r4, #8
    blt d4_top
    ldr r2, [sp, #20]
    adds r3, r3, r2
d4_top:
    str r3, [sp, #16]
    movs r5, #0
d4_x:
    ldr r3, [sp, #16]
    cmp r5, #8
    blt d4_l
    adds r3, #32
d4_l:
    lsls r2, r5, #29
    lsrs r2, r2, #30
    ldrb r3, [r3, r2]
    lsls r2, r5, #31
    lsrs r2, r2, #29
    lsrs r3, r3, r2
    movs r2, #15
    ands r2, r3
    beq d4_nx
    mov r0, r8
    ldrh r0, [r0, #0xE]
    adds r0, r0, r5
    adds r1, r4, #0
    bl plot
d4_nx:
    adds r5, #1
    cmp r5, r7
    blt d4_x
    adds r4, #1
    cmp r4, #16
    blt d4_y
    ldr r7, [sp, #24]
advance:
    mov r0, r8
    ldrh r1, [r0, #0xE]
    adds r1, r1, r7
    strh r1, [r0, #0xE]
    b loop
done:
    mov r0, r8
    ldrh r1, [r0, #4]
    strh r1, [r0, #6]
    add r1, sp, #32
    movs r0, #1
    strb r0, [r1]
    ldr r0, [sp, #0]
    lsls r0, r0, #2
    add r0, r10
    str r0, [r1, #4]
    ldr r0, lit_vofs
    ldr r0, [r0]
    movs r2, #0xC0
    lsls r2, r2, #19
    adds r0, r0, r2
    mov r2, r8
    ldr r2, [r2, #0x24]
    adds r0, r0, r2
    str r0, [r1, #8]
    ldr r0, [sp, #8]
    lsls r0, r0, #5
    str r0, [r1, #12]
    ldr r0, lit_dmaq
    ldr r2, lit_queue
    bl callr2
    ldr r0, [sp, #44]
ret:
    add sp, #48
    pop {r4-r7}
    mov r8, r4
    mov r9, r5
    mov r10, r6
    mov r11, r7
    pop {r4-r7}
    pop {r1}
    bx r1
callr2:
    bx r2

plot:
    cmp r0, r9
    bhs plot_r
    lsrs r3, r0, #3
    lsls r3, r3, #4
    adds r3, r3, r1
    add r3, r11
    lsls r3, r3, #2
    add r3, r10
    lsls r0, r0, #29
    lsrs r0, r0, #27
    ldr r1, [r3]
    push {r4}
    movs r4, #15
    lsls r4, r0
    bics r1, r4
    lsls r2, r0
    orrs r1, r2
    str r1, [r3]
    pop {r4}
plot_r:
    bx lr

tiles:
    lsrs r1, r0, #1
    lsls r2, r1, #1
    adds r1, r1, r2
    movs r2, #1
    ands r2, r0
    lsls r2, r2, #1
    adds r1, r1, r2
    lsls r0, r1, #1
    bx lr

mapb:
    push {r4-r7, lr}
    mov r4, r8
    mov r5, r9
    push {r4, r5}
    sub sp, #8
    mov r8, r0
    ldrh r1, [r0]
    cmp r1, #0
    beq mb_ret
    ldr r1, [r0, #0x34]
    cmp r1, #0
    beq mb_ret
    ldrh r0, [r0, #0x1C]
    bl tiles
    str r0, [sp, #0]
    lsrs r6, r0, #1
    mov r0, r8
    ldrh r1, [r0, #0x18]
    adds r2, r1, r6
    cmp r2, #32
    ble mb_c
    movs r6, #32
    subs r6, r6, r1
mb_c:
    ldr r1, [r0, #0x24]
    lsrs r1, r1, #5
    ldrh r2, [r0, #0x2A]
    lsls r2, r2, #12
    orrs r1, r2
    str r1, [sp, #4]
    movs r4, #0
mb_line:
    mov r0, r8
    ldrh r1, [r0, #0x1E]
    cmp r4, r1
    bge mb_ret
    ldrh r2, [r0, #0x1A]
    lsls r3, r4, #1
    adds r2, r2, r3
    cmp r2, #31
    bge mb_ret
    lsls r2, r2, #6
    ldr r3, lit_map
    adds r2, r2, r3
    ldrh r3, [r0, #0x18]
    lsls r3, r3, #1
    adds r2, r2, r3
    ldr r3, [sp, #0]
    muls r3, r4, r3
    ldr r1, [sp, #4]
    adds r3, r3, r1
    movs r5, #0
mb_col:
    cmp r5, r6
    bge mb_nl
    strh r3, [r2]
    adds r3, #1
    adds r2, #64
    strh r3, [r2]
    subs r2, #62
    adds r3, #1
    adds r5, #1
    b mb_col
mb_nl:
    adds r4, #1
    b mb_line
mb_ret:
    add sp, #8
    pop {r4, r5}
    mov r8, r4
    mov r9, r5
    pop {r4-r7}
    pop {r0}
    bx r0

    .align 2
lit_dmacnt: .word 0x020221A0
lit_buf:    .word 0x020221D0
lit_8000:   .word 0x8000
lit_vofs:   .word 0x02025200
lit_dmaq:   .word 0x03006310
lit_queue:  .word 0x08035061
lit_map:    .word 0x0202520C
lit_adv:    .word ADV
lit_en:     .word ENG
"""


def assemble(addr, adv, eng):
    ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)
    src = ASM.replace("ADV", hex(0x08000000 + adv)).replace("ENG", hex(0x08000000 + eng))
    enc, _ = ks.asm(src, 0x08000000 + addr)
    code = bytes(enc)
    check_thumb1(code)
    return code


def check_thumb1(code):
    """ARM7TDMI has no Thumb-2: keystone silently widens far branches (bhs.w); only BL pairs may be 32-bit."""
    hw = struct.unpack("<%dH" % (len(code) // 2), code)
    i = 0
    lit = code.index(struct.pack("<I", 0x020221A0))  # literal pool starts here (data, not code)
    while i * 2 < lit:
        top = hw[i] >> 11
        if top == 0b11110:
            assert hw[i + 1] >> 11 == 0b11111, f"32-bit Thumb-2 instruction at +{i * 2:#x}"
            i += 2
            continue
        assert top not in (0b11101, 0b11111), f"32-bit Thumb-2 instruction at +{i * 2:#x}"
        i += 1


MAPB_PROLOGUE = bytes.fromhex("f0b544464d4630b4")  # push {r4-r7,lr}; mov r4,r8; mov r5,r9; push {r4,r5}


def hook(rom, at, target):
    """ldr r3, [pc, #0] ; bx r3 ; .word target|1 at a 4-aligned Thumb function entry."""
    assert at % 4 == 0
    rom[at:at + 8] = bytes.fromhex("004b1847") + struct.pack("<I", 0x08000000 + target + 1)


def install(rom, alloc, adv_table, eng_table):
    """adv_table: 256 bytes; eng_table: 256 x 16 u32 rows (2bpp, pixel x at bits 2x)."""
    adv = alloc.put(bytes(adv_table), align=4)
    eng = alloc.put(eng_table, align=4)
    code = assemble(0, adv, eng)
    at = alloc.put(b"\0" * len(code), align=4)
    code = assemble(at, adv, eng)
    rom[at:at + len(code)] = code
    assert code.count(MAPB_PROLOGUE) == 1
    mb = at + code.index(MAPB_PROLOGUE)
    hook(rom, RENDER, at)
    hook(rom, MAPB, mb)
