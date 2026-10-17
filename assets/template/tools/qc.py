# QC: per-frame difference scan (1-4 frame glitches), black/flash detection, and 1 fps contact sheets.
#   python tools/qc.py out/video.mp4 [sheet_prefix] [fps]   (1-frame pops at beat flashes are usually intentional)
import sys, subprocess, numpy as np
from PIL import Image
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_cands = [os.path.join(_ROOT, 'node_modules', 'ffmpeg-static', n) for n in ('ffmpeg.exe', 'ffmpeg')]
FF = next((c for c in _cands if os.path.exists(c)), 'ffmpeg')
src = sys.argv[1]; pre = sys.argv[2] if len(sys.argv) > 2 else None
FPS = int(sys.argv[3]) if len(sys.argv) > 3 else 60
W, H = 240, 135
p = subprocess.Popen([FF, '-v', 'error', '-i', src, '-vf', f'scale={W}:{H}:flags=area', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
frames = []
while True:
    b = p.stdout.read(W * H * 3)
    if len(b) < W * H * 3: break
    frames.append(np.frombuffer(b, np.uint8).reshape(H, W, 3))
F = np.stack(frames).astype(np.float32)
n = len(F); print('frames', n)
g = F.mean(3)
d = np.abs(np.diff(g, axis=0)).mean((1, 2))          # frame-to-frame change
lum = g.mean((1, 2))
# isolated spikes: big change in, big change out, calm around (a pop)
flags = []
for i in range(2, n - 3):
    a, b = d[i - 1], d[i]                                # change into frame i, out of frame i
    calm = max(d[i - 2], d[i + 1] if i + 1 < len(d) else 0)
    if a > 6 and b > 6 and min(a, b) > 3.0 * (calm + 0.5):
        flags.append((i, i / FPS, round(float(a), 1), round(float(b), 1)))
print('isolated 1-frame pops:', len(flags))
for f in flags[:40]: print('  frame %d  t=%.3f  in=%.1f out=%.1f' % f)
# 2-4 frame blips: compare frame i with frames i-1 and i+k
blips = []
for k in (2, 3, 4):
    for i in range(1, n - k - 1):
        pre_post = np.abs(g[i - 1] - g[i + k]).mean()
        inside = np.abs(g[i] - g[i - 1]).mean()
        if inside > 10 and pre_post < inside / 4:
            blips.append((k, i, i / FPS, round(float(inside), 1), round(float(pre_post), 1)))
print('short blips (2-4 f):', len(blips))
for b in blips[:30]: print('  len %d frame %d t=%.3f inside=%.1f pre/post=%.1f' % b)
# big cuts (hard changes) for reference
cuts = [(i + 1, round((i + 1) / FPS, 3), round(float(v), 1)) for i, v in enumerate(d) if v > 25]
print('hard changes >25:', len(cuts), cuts[:40])
blk = [i / FPS for i in range(n) if lum[i] < 4]
print('near-black frames:', len(blk), (blk[:3], blk[-3:]) if blk else '')
if pre:
    for s0 in range(0, n // FPS, 30):
        tiles = [Image.fromarray(F[min(n - 1, (s0 + k) * FPS)].astype(np.uint8)) for k in range(30) if (s0 + k) * FPS < n]
        sheet = Image.new('RGB', (W * 6, H * 5), (30, 30, 30))
        for k, im in enumerate(tiles): sheet.paste(im, ((k % 6) * W, (k // 6) * H))
        sheet = sheet.resize((W * 6 * 2, H * 5 * 2), Image.NEAREST) if False else sheet
        sheet.save(f'{pre}_{s0:03d}.png')
    print('sheets written')
