# contact sheet of stills: python tools/sheet.py out.jpg [cols] files...
# Tiles keep the stills' own aspect ratio (16:9, 9:16, 1:1, 4:5), labelled with the time from the file name.
import sys
from PIL import Image, ImageDraw
if len(sys.argv) < 4: sys.exit('usage: python tools/sheet.py out.jpg cols still1.png [still2.png ...]')
out = sys.argv[1]; cols = int(sys.argv[2]); fs = sys.argv[3:]
w0, h0 = Image.open(fs[0]).size
TW = (960 if cols <= 2 else 640) if w0 >= h0 else (540 if cols <= 2 else 360)
W, H = TW, int(round(TW * h0 / w0))
rows = (len(fs) + cols - 1) // cols
im = Image.new('RGB', (W * cols, H * rows), (40, 40, 40))
d = ImageDraw.Draw(im)
for i, f in enumerate(fs):
    a = Image.open(f).convert('RGB').resize((W, H), Image.LANCZOS)
    x, y = (i % cols) * W, (i // cols) * H
    im.paste(a, (x, y)); d.rectangle([x, y, x + 120, y + 22], fill=(0, 0, 0)); d.text((x + 4, y + 4), f.split('t_')[-1][:-4], fill=(255, 255, 0))
im.save(out, quality=88)
print('wrote', out, im.size)
