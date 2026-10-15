"""Code/data patches for English (applied by tools/build.py after the VWF).

1. Item/card pop-up composer 0x08039DCC..0x0803A112 ("<name>を手に入れた", item/card full, all cards lost):
   - the 16-code buffer 0x02025A10 moves to free EWRAM 0x0203F800 and the 0xF code limits become 0x2F;
   - the suffix tables (ROM 0x29E7C6 "...を手に入れた", 0x29E7E6 "...をなくしたよ"; the code reads suffix code k
     at table + 2*(k+9)) and the whole-message strings (0x29E806 item full, 0x29E826 card full, 0x29E846 all cards
     lost) point at English strings in free space;
   - 0x0803A112 jumps to `popfix`, which sets the code budget (ctx+4 = 0x40) and recomputes r5 (the pop-up width in
     12 px units, used to size and centre the box) from the English pixel width, then returns to 0x0803A11C.
"""
import struct, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB  # noqa: E402
import vwf  # noqa: E402

BUF_OLD, BUF_NEW = 0x02025A10, 0x0203F800
COMPOSER = (0x039DC0, 0x03A112)
POPUP_TEXT = {  # English for the ROM data strings of the pop-ups
    "got": " is yours!",
    "lost": " was lost!",
    "item_full": "You can't carry any more items!",
    "card_full": "You can't hold any more cards!",
    "all_lost": "You lost all your cards!",
}


def lit_addr(rom, ins_off):
    """File offset of the literal loaded by a Thumb `ldr rX, [pc, #imm]` at file offset ins_off."""
    h = struct.unpack_from("<H", rom, ins_off)[0]
    assert h & 0xF800 == 0x4800, hex(ins_off)
    return (((0x08000000 + ins_off + 4) & ~3) + (h & 0xFF) * 4) - 0x08000000


POPFIX = r"""
popfix:
    ldr r4, l_ctx
    movs r0, #0x40
    strh r0, [r4, #4]
    ldr r2, [r4, #0x34]
    movs r3, #0
    movs r6, #0
pf_lp:
    ldrh r0, [r2]
    adds r2, #2
    ldr r1, l_8000
    cmp r0, r1
    beq pf_end
    cmp r0, #0
    bne pf_nsp
    adds r3, #12
    b pf_lp
pf_nsp:
    lsrs r1, r0, #14
    cmp r1, #1
    bne pf_full
    lsls r0, r0, #24
    lsrs r0, r0, #24
    ldr r1, l_adv
    ldrb r1, [r1, r0]
    cmp r1, #0
    bne pf_w
    movs r1, #8
pf_w:
    adds r3, r3, r1
    cmp r0, #0x30
    beq pf_lp
    adds r6, r3, #0
    b pf_lp
pf_full:
    adds r3, #12
    adds r6, r3, #0
    b pf_lp
pf_end:
    movs r5, #0
    adds r6, #11
pf_div:
    cmp r6, #12
    blt pf_dd
    subs r6, #12
    adds r5, #1
    b pf_div
pf_dd:
    cmp r5, #1
    bge pf_lo
    movs r5, #1
pf_lo:
    cmp r5, #16
    ble pf_hi
    movs r5, #16
pf_hi:
    lsls r0, r5, #1
    adds r0, r0, r5
    ldr r1, l_ret
    bx r1
    .align 2
l_ctx:  .word 0x02011AA8
l_8000: .word 0x8000
l_adv:  .word ADV
l_ret:  .word 0x0803A11D
"""


def apply(rom, alloc, adv_off, encode):
    lo, hi = COMPOSER
    # 1. buffer address in the composer's literal pools (pools sit inside the function range)
    n = 0
    for p in range(lo, hi + 0x100, 4):
        if struct.unpack_from("<I", rom, p)[0] == BUF_OLD:
            struct.pack_into("<I", rom, p, BUF_NEW); n += 1
    assert n == 5, n  # 5 pool words serve the 13 loads
    # 2. code limits 0xF -> 0x2F (cmp rN, #0xf)
    n = 0
    for p in range(lo, hi, 2):
        h = struct.unpack_from("<H", rom, p)[0]
        if h & 0xF8FF == 0x280F:
            struct.pack_into("<H", rom, p, (h & 0xFF00) | 0x2F); n += 1
    assert n == 19, n

    # 3. strings
    def put(s, pad_to=0):
        codes = encode(s) + [0x8000]
        codes += [0] * max(0, pad_to - len(codes))
        return alloc.put(struct.pack("<%dH" % len(codes), *codes), align=4)

    got, lost = put(POPUP_TEXT["got"]), put(POPUP_TEXT["lost"])
    for ins, tgt in ((0x039E5C, got), (0x039F10, lost), (0x039F16, lost), (0x039FCC, got),
                     (0x03A080, lost), (0x03A086, lost)):
        a = lit_addr(rom, ins)
        assert struct.unpack_from("<I", rom, a)[0] in (0x0829E7C6, 0x0829E7E6), hex(ins)
        struct.pack_into("<I", rom, a, 0x08000000 + tgt - 18)
    for ins, key, old in ((0x039DD0, "item_full", 0x0829E806), (0x039DF0, "card_full", 0x0829E826),
                          (0x03A0F4, "all_lost", 0x0829E846)):
        a = lit_addr(rom, ins)
        assert struct.unpack_from("<I", rom, a)[0] == old, hex(ins)
        struct.pack_into("<I", rom, a, 0x08000000 + put(POPUP_TEXT[key], pad_to=48))
    # 4. width/centring fix
    ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)
    at = alloc.put(b"\0" * 0x100, align=4)
    code, _ = ks.asm(POPFIX.replace("ADV", hex(0x08000000 + adv_off)), 0x08000000 + at)
    code = bytes(code)
    vwf.check_thumb1(code, end=code.index(struct.pack("<I", 0x02011AA8)))
    rom[at:at + len(code)] = code
    assert rom[0x03A112:0x03A11C] == bytes.fromhex("284c1020a08068004019"), rom[0x03A112:0x03A11C].hex()
    # 0x0803A112: ldr r0,[pc,#4]; bx r0; nop; .word popfix|1  (replaces ldr r4/movs/strh/lsls/adds)
    rom[0x03A112:0x03A11C] = bytes.fromhex("01480047c046") + struct.pack("<I", 0x08000000 + at + 1)
