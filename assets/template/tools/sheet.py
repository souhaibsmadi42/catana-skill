# contact sheet of stills: python tools/sheet.py out.jpg [cols] files...
import sys
from PIL import Image, ImageDraw
out = sys.argv[1]; cols = int(sys.argv[2]); fs = sys.argv[3:]
W, H = (960, 540) if cols <= 2 else (640, 360)
rows = (len(fs) + cols - 1) // cols
im = Image.new('RGB', (W * cols, H * rows), (40, 40, 40))
d = ImageDraw.Draw(im)
for i, f in enumerate(fs):
    a = Image.open(f).convert('RGB').resize((W, H), Image.LANCZOS)
    x, y = (i % cols) * W, (i // cols) * H
    im.paste(a, (x, y)); d.rectangle([x, y, x + 120, y + 22], fill=(0, 0, 0)); d.text((x + 4, y + 4), f.split('t_')[-1][:-4], fill=(255, 255, 0))
im.save(out, quality=88)
