"""Labelled contact sheets of PNGs: python -X utf8 tools/gfx/contact.py OUTPREFIX PNG.. [--cols 4 --per 12 --w 240]"""
import os, sys
from PIL import Image, ImageDraw

a = sys.argv[1:]
cols = int(a[a.index("--cols") + 1]) if "--cols" in a else 4
per = int(a[a.index("--per") + 1]) if "--per" in a else 12
W = int(a[a.index("--w") + 1]) if "--w" in a else 240
files = [x for x in a[1:] if x.endswith(".png")]
for k in range(0, len(files), per):
    chunk = files[k:k + per]
    ims = []
    for f in chunk:
        im = Image.open(f).convert("RGB")
        if im.width > W:
            im = im.resize((W, max(1, im.height * W // im.width)))
        if im.height > 2 * W:
            im = im.crop((0, 0, im.width, 2 * W))
        ims.append((os.path.basename(f), im))
    rows = (len(ims) + cols - 1) // cols
    hs = [max(im.height for _, im in ims[r * cols:(r + 1) * cols]) + 12 for r in range(rows)]
    sheet = Image.new("RGB", (cols * (W + 4), sum(hs)), (60, 0, 60))
    d = ImageDraw.Draw(sheet)
    y = 0
    for r in range(rows):
        for c, (n, im) in enumerate(ims[r * cols:(r + 1) * cols]):
            sheet.paste(im, (c * (W + 4), y + 12))
            d.text((c * (W + 4) + 2, y), n[-44:], fill=(255, 255, 0))
        y += hs[r]
    sheet.save("%s_%02d.png" % (a[0], k // per))
print((len(files) + per - 1) // per, "sheets")
