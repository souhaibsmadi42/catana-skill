"""Read a music track's structure for a beat-locked edit.
  python tools/music_scan.py assets/music.wav [--bpm 120]
Prints: tempo, beat-0 offset (first downbeat), a per-bar energy table (kick / hats / overall, dB), and a section guess
(intro, build, DROP, break, SILENCE, outro). Writes qa/music_scan.png (energy curves with the bar grid).
Put BPM and OFFSET into FILM (src/lib.js); then B(k) = OFFSET + k * 60 / BPM lands on the beat.
Always check the guesses against the plot — and by listening, when you can.
"""
import sys, os, argparse
import numpy as np, soundfile as sf
from scipy import signal

ap = argparse.ArgumentParser()
ap.add_argument('wav'); ap.add_argument('--bpm', type=float, default=None); ap.add_argument('--offset', type=float, default=None); ap.add_argument('--min', type=float, default=70); ap.add_argument('--max', type=float, default=180)
A = ap.parse_args()
x, sr = sf.read(A.wav, dtype='float64')
m = x.mean(1) if x.ndim > 1 else x
dur = len(m) / sr
HOP = 512
fps = sr / HOP

def band(lo, hi):
    if lo and hi: sos = signal.butter(4, [lo, hi], 'bandpass', fs=sr, output='sos')
    elif lo: sos = signal.butter(4, lo, 'highpass', fs=sr, output='sos')
    else: sos = signal.butter(4, hi, 'lowpass', fs=sr, output='sos')
    return signal.sosfiltfilt(sos, m)

def rms(y):
    n = len(y) // HOP
    return np.sqrt((y[: n * HOP].reshape(n, HOP) ** 2).mean(1) + 1e-12)

low, high, full = rms(band(None, 150)), rms(band(5000, None)), rms(m)
db = lambda v: 20 * np.log10(v + 1e-9)
# onset strength: positive change of log energy (kick-weighted)
on = np.maximum(0, np.diff(np.log(low + 1e-6), prepend=0)) + 0.5 * np.maximum(0, np.diff(np.log(high + 1e-6), prepend=0))
on = on - signal.medfilt(on, 31)
on = np.maximum(on, 0)

# tempo: autocorrelation peak inside [min, max] BPM, preferring 90–150
if A.bpm: bpm = A.bpm
else:
    ac = np.correlate(on, on, 'full')[len(on) - 1:]
    lags = np.arange(len(ac))
    best, bpm = -1, 120
    for L in range(int(fps * 60 / A.max), int(fps * 60 / A.min) + 1):
        b = 60 * fps / L
        w = 1.0 if 90 <= b <= 150 else 0.8
        v = ac[L] * w
        if v > best: best, bpm = v, b
    # refine to 0.01 BPM by scanning comb alignment
    cands = np.arange(bpm - 1.5, bpm + 1.5, 0.01)
    def comb(b):
        per = 60 * fps / b
        idx = (np.arange(0, len(on) / per - 1) * per).astype(int)
        return max(on[(idx + o) % len(on)].sum() for o in range(0, int(per), 2))
    bpm = cands[np.argmax([comb(b) for b in cands])]
beat = 60 / bpm
per = beat * fps
# phase: offset maximizing onset sum at beat positions
best, off = -1, 0.0
for o in np.arange(0, beat, 0.002):
    idx = ((o + np.arange(0, (dur - o) / beat) * beat) * fps).astype(int)
    idx = idx[idx < len(on)]
    v = on[idx].sum()
    if v > best: best, off = v, o
# downbeat: sections start on bar lines, so pick the beat phase where energy jumps (in or out) are largest
E = db(full)
def win(t0, t1):
    i0, i1 = max(0, int(t0 * fps)), min(len(E), int(t1 * fps))
    return E[i0:i1].mean() if i1 > i0 else E.mean()
ph = []
for p in range(4):
    sc = 0.0
    for t0 in off + (p + np.arange(1, (dur - off) / beat / 4 - 1) * 4) * beat:
        sc += abs(win(t0, t0 + 2 * beat) - win(t0 - 2 * beat, t0)) ** 2
    ph.append(sc)
order = np.argsort(ph)[::-1]
alts = [((off + int(p) * beat) % (4 * beat), ph[p] / max(ph)) for p in order]
off = alts[0][0]
if A.offset is not None: off = A.offset
print(f'tempo {bpm:.2f} BPM | beat {beat:.4f} s | bar {4 * beat:.3f} s | beat-0 offset {off:.3f} s | duration {dur:.2f} s')
print(f'FILM: BPM: {bpm:.2f}, OFFSET: {off:.3f}')
print('bar-phase candidates (offset, score): ' + ', '.join(f'{o:.3f} ({sc:.2f})' for o, sc in alts) + '  <- the downbeat guess is the weakest step: check that drops/silences start on a bar line in the table, or pass --offset')

# per-bar table + section guess
nb = int((dur - off) / (4 * beat))
rows = []
for k in range(nb):
    a, b = off + k * 4 * beat, off + (k + 1) * 4 * beat
    i0, i1 = int(a * fps), int(b * fps)
    rows.append((k, a, db(low[i0:i1].mean()), db(high[i0:i1].mean()), db(full[i0:i1].mean()), np.percentile(db(full[i0:i1]), 30)))
Q = np.array([r[5] for r in rows]); L = np.array([r[2] for r in rows]); Hh = np.array([r[3] for r in rows]); F = np.array([r[4] for r in rows])
lmax, fmax = np.percentile(L, 90), np.percentile(F, 90)
def tag(i):
    if Q[i] < fmax - 30 or L[i] < lmax - 35: return 'SILENCE'
    full_k = L[i] > lmax - 3 and Hh[i] > np.percentile(Hh, 50)
    if full_k: return 'DROP'
    if i + 1 < len(F) and F[i + 1] - F[i] > 4 and Hh[i] > Hh[max(0, i - 1)]: return 'build->'
    if L[i] < lmax - 8: return 'break'
    return 'groove'
print('\n bar  beat   time   kick   hats   full  section')
prev = None
for i, r in enumerate(rows):
    t_ = tag(i)
    mark = ' <' if t_ != prev else ''
    print(f'{r[0]:4d} {r[0] * 4:5d} {r[1]:6.2f} {r[2]:6.1f} {r[3]:6.1f} {r[4]:6.1f}  {t_}{mark}')
    prev = t_
try:
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    t = np.arange(len(full)) / fps
    fig, ax = plt.subplots(figsize=(22, 5))
    ax.plot(t, db(full), lw=.5, label='full'); ax.plot(t, db(low), lw=.5, label='<150 Hz (kick)'); ax.plot(t, db(high), lw=.5, label='>5 kHz (hats)')
    for k in range(nb + 1): ax.axvline(off + k * 4 * beat, color='k', alpha=.15 if k % 4 else .4, lw=.6)
    ax.set_ylim(-70, 0); ax.set_xlim(0, dur); ax.legend(); ax.set_title(f'{os.path.basename(A.wav)} - {bpm:.2f} BPM, offset {off:.3f} s (lines = bars, darker = 4 bars)')
    os.makedirs('qa', exist_ok=True); plt.tight_layout(); plt.savefig('qa/music_scan.png', dpi=60)
    print('\nwrote qa/music_scan.png')
except Exception as e:
    print('plot skipped:', e)
