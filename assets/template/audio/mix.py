"""Katana film soundtrack: the recorded music track, unedited, plus SFX placed on the page's own cue list.
  node tools/page.mjs "src/index.html?dump=1" build/events.json && python audio/mix.py
Music path, BPM and offset are read from src/lib.js (FILM). Output: out/soundtrack.wav (48 kHz, 24-bit), -14 LUFS, -1 dBFS.
Cue kinds: impact boom hitS slash tick blip glitch pen whoosh whooshL scroll swell click type toggle step drop riser(d) outro.
The SFX are procedural (filtered noise + oscillators); swap in recorded stock SFX if the user supplies them.
"""
import os, json, re
import numpy as np
import soundfile as sf
from scipy import signal
import pyloudnorm as pyln

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "out")
SR = 48000
LIB = open(os.path.join(ROOT, "src", "lib.js"), encoding="utf8").read()
_g = lambda k, d: float(re.search(r"(^|[^A-Za-z_])" + k + r":\s*([0-9.]+)", LIB).group(2)) if re.search(r"(^|[^A-Za-z_])" + k + r":\s*([0-9.]+)", LIB) else d
DUR = _g("DURATION", 12.0)
BPM = _g("BPM", 120.0)
OFFSET = _g("OFFSET", 0.0)
MUSIC = re.search(r"MUSIC:\s*'([^']+)'", LIB).group(1) if re.search(r"MUSIC:\s*'([^']+)'", LIB) else "assets/music.wav"
N = int(DUR * SR)
rng = np.random.default_rng(2026)
tt = np.arange(N) / SR
EV = json.load(open(os.path.join(ROOT, "build", "events.json")))
BEAT = 60.0 / BPM
B = lambda k: OFFSET + BEAT * k

music = np.zeros((N, 2))
sfx = np.zeros((N, 2))
rev_send = np.zeros((N, 2))


def idx(t): return int(round(t * SR))


def add(bus, t0, x, gain=1.0, pan=0.0, send=0.0):
    i0 = idx(t0)
    if x.ndim == 1:
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        x = np.stack([x * l, x * r], 1) * np.sqrt(2)
    if i0 < 0:
        x = x[-i0:]; i0 = 0
    i1 = min(N, i0 + len(x))
    if i1 <= i0: return
    bus[i0:i1] += x[: i1 - i0] * gain
    if send > 0 and bus is sfx:
        rev_send[i0:i1] += x[: i1 - i0] * gain * send


def smoothstep(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


def mtof(m): return 440.0 * 2 ** ((m - 69) / 12)


# =========================================================================== MUSIC (unedited)
mp = os.path.join(ROOT, MUSIC)
if os.path.exists(mp):
    m, sr = sf.read(mp, dtype="float64")
    if sr != SR: m = signal.resample_poly(m, SR, sr)
    if m.ndim == 1: m = np.stack([m, m], 1)
    n = min(N, len(m))
    music[:n] = m[:n]
else:
    print("WARNING: no music at", mp, "- SFX only")

# =========================================================================== INSTRUMENTS
HAT_SOS = signal.butter(4, 7000, "highpass", fs=SR, output="sos")


def filtered_noise(dur, fc_keys, q_keys, amp_keys, stereo=True, seed=0):
    n = int(dur * SR)
    g = np.random.default_rng(seed)
    chans = []
    for c in range(2 if stereo else 1):
        x = g.standard_normal(n + 4096)
        f, fr, Z = signal.stft(x, SR, nperseg=2048, noverlap=1536)
        tf = fr - 1024 / SR
        fc = np.interp(tf, *zip(*fc_keys)); q = np.interp(tf, *zip(*q_keys))
        logf = np.log2(np.maximum(f, 20))[:, None]
        mask = np.exp(-0.5 * ((logf - np.log2(fc)[None, :]) / np.maximum(q, 0.05)[None, :]) ** 2)
        _, y = signal.istft(Z * mask, SR, nperseg=2048, noverlap=1536)
        chans.append(y[:n])
    y = np.stack(chans, 1) if stereo else chans[0]
    s = np.arange(n) / SR
    a = np.interp(s, *zip(*amp_keys))
    y = y / (np.max(np.abs(y)) + 1e-9)
    return y * (a[:, None] if stereo else a)


def whoosh(tc, dur=0.9, amp=1.0, up=True, seed=3, lo=500, hi=5000):
    a, b = (lo, hi) if up else (hi, lo * 0.8)
    y = filtered_noise(dur, [(0, a), (dur, b)], [(0, 0.9), (dur, 0.9)], [(0, 0), (dur * 0.55, 1.0), (dur, 0)], seed=seed)
    s = np.arange(len(y)) / SR
    pan = np.sin(np.pi * (s / dur - 0.5)) * 0.7
    y[:, 0] *= np.cos((pan + 1) * np.pi / 4) * 1.4
    y[:, 1] *= np.sin((pan + 1) * np.pi / 4) * 1.4
    add(sfx, tc - dur * 0.55, y * 0.2 * amp, send=0.3)


def riser(t_end, dur, amp=1.0, f0=300, f1=6000, seed=1, tone=True):
    y = filtered_noise(dur, [(0, f0), (dur, f1)], [(0, 1.2), (dur, 0.5)], [(0, 0), (dur * 0.7, 0.45), (dur, 1.0)], seed=seed)
    s = np.arange(len(y)) / SR
    if tone:
        fsw = 110 * 2 ** (3 * (s / dur) ** 1.6)
        y += (np.sin(2 * np.pi * np.cumsum(fsw) / SR) * (s / dur) ** 2 * 0.25)[:, None]
    add(sfx, t_end - dur, y * 0.35 * amp, send=0.35)


def suck(t_end, dur=0.8, amp=1.0, seed=5):
    y = filtered_noise(dur, [(0, 3500), (dur, 500)], [(0, 1.3), (dur, 0.8)], [(0, 0), (dur, 1)], seed=seed)
    add(sfx, t_end - dur, y * (np.linspace(0, 1, len(y)) ** 3)[:, None] * 0.45 * amp, send=0.25)


def impact(t0, amp=1.0, big=True, seed=9):
    d = 4.5 if big else 2.0
    s = np.arange(int(d * SR)) / SR
    f = 34 + 70 * np.exp(-s / 0.09)
    boom = np.tanh(2.2 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-s / (1.3 if big else 0.5)))
    crack = signal.sosfilt(signal.butter(2, 3500, "lowpass", fs=SR, output="sos"), rng.standard_normal(len(s))) * np.exp(-s / 0.16) * 0.5
    body = filtered_noise(d, [(0, 180), (d, 60)], [(0, 1.0), (d, 1.0)], [(0, 1), (0.25, 0.5), (d, 0)], seed=seed)
    x = np.stack([boom + crack, boom + crack], 1) * 0.5 + body * 0.35
    add(sfx, t0, x * 0.55 * amp, send=0.5)


def shimmer(t0, notes, dur=3.0, amp=1.0, spread=0.035):
    for i, mm in enumerate(notes):
        s = np.arange(int(dur * SR)) / SR
        f = mtof(mm)
        x = np.sin(2 * np.pi * f * s) + 0.3 * np.sin(2 * np.pi * 2.001 * f * s)
        x *= (1 - np.exp(-s / 0.01)) * np.exp(-s / (dur * 0.35)) * (1 + 0.2 * np.sin(2 * np.pi * 5.5 * s + i))
        add(sfx, t0 + i * spread, x * 0.05 * amp, pan=(i / max(1, len(notes) - 1)) * 1.4 - 0.7, send=0.6)


def click(t0, amp=1.0, f=3200, pan=0.1):
    d = 0.06
    s = np.arange(int(d * SR)) / SR
    x = np.sin(2 * np.pi * f * s) * np.exp(-s / 0.006) + 0.5 * np.sin(2 * np.pi * f * 0.5 * s) * np.exp(-s / 0.012)
    x += signal.sosfilt(HAT_SOS, rng.standard_normal(len(s))) * np.exp(-s / 0.002) * 0.4
    add(sfx, t0, x * 0.16 * amp, pan=pan, send=0.12)


def blip(t0, amp=1.0, f=1760, pan=0.0):
    d = 0.18
    s = np.arange(int(d * SR)) / SR
    fr = f * (1 + 0.5 * np.exp(-s / 0.01))
    x = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-s / 0.045) * (1 - np.exp(-s / 0.001))
    add(sfx, t0, x * 0.06 * amp, pan=pan, send=0.35)


def tick_run(a, b, rate, amp=0.5, f=2600, accel=1.0):
    t0, k = a, 0
    while t0 < b:
        blip(t0, amp * (0.6 + 0.4 * rng.random()), f=f * (1 + 0.25 * ((k * 7) % 5) / 5), pan=rng.uniform(-0.6, 0.6))
        r = rate * (1 + (accel - 1) * (t0 - a) / max(b - a, 1e-3))
        t0 += 1.0 / r; k += 1


def zip_(t0, dur=0.25, amp=1.0, f0=900, f1=5200, pan=0.0):
    s = np.arange(int(dur * SR)) / SR
    f = f0 * (f1 / f0) ** (s / dur)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * s / dur) ** 1.5
    x += 0.3 * signal.sosfilt(HAT_SOS, rng.standard_normal(len(s))) * np.sin(np.pi * s / dur)
    add(sfx, t0, x * 0.05 * amp, pan=pan, send=0.4)


def scan(t0, dur=1.0, amp=1.0, down=False, seed=21):
    a, b = (4200, 900) if down else (900, 4200)
    y = filtered_noise(dur, [(0, a), (dur, b)], [(0, 0.35), (dur, 0.35)], [(0, 0), (0.15, 1), (dur - 0.15, 1), (dur, 0)], seed=seed)
    s = np.arange(len(y)) / SR
    fr = np.interp(s, [0, dur], [a, b]) * 0.5
    y += (0.18 * np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.interp(s, [0, 0.15, dur - 0.15, dur], [0, 1, 1, 0]))[:, None]
    add(sfx, t0, y * 0.13 * amp, send=0.35)


def sub_swell(t0, dur, amp=1.0, f=41.2):
    s = np.arange(int(dur * SR)) / SR
    x = np.sin(2 * np.pi * f * s) * smoothstep(s / dur) ** 2
    add(sfx, t0, x * 0.22 * amp)


def mech(t0, dur=0.9, amp=1.0, seed=31):
    y = filtered_noise(dur, [(0, 220), (dur, 120)], [(0, 0.6), (dur, 0.6)], [(0, 0), (0.1, 1), (dur, 0)], seed=seed)
    s = np.arange(len(y)) / SR
    y += (0.3 * np.sin(2 * np.pi * np.cumsum(90 - 30 * s / dur) / SR) * np.interp(s, [0, 0.1, dur], [0, 1, 0]))[:, None]
    add(sfx, t0, y * 0.25 * amp, send=0.2)


# ---- new: paper & drawing
def pencil(a, b, amp=1.0, seed=41, rate=7.0):
    """graphite on paper: band-passed noise with stroke rhythm"""
    d = b - a
    y = filtered_noise(d, [(0, 4200), (d, 3600)], [(0, 0.5), (d, 0.5)], [(0, 0), (0.08, 1), (d - 0.12, 1), (d, 0)], seed=seed)
    s = np.arange(len(y)) / SR
    g = np.random.default_rng(seed)
    ph = np.cumsum(rate * (1 + 0.35 * np.sin(2 * np.pi * 0.7 * s + g.random() * 6))) / SR
    stroke = 0.35 + 0.65 * np.abs(np.sin(np.pi * ph)) ** 0.6
    add(sfx, a, y * stroke[:, None] * 0.07 * amp, send=0.1)


def marker(t0, amp=1.0, seed=0):
    """highlighter tick: a quick felt squeak + tap"""
    d = 0.16
    y = filtered_noise(d, [(0, 2400), (d, 5200)], [(0, 0.35), (d, 0.35)], [(0, 0), (0.02, 1), (0.07, 0.6), (d, 0)], seed=50 + seed)
    s = np.arange(len(y)) / SR
    tap = np.sin(2 * np.pi * 900 * s) * np.exp(-s / 0.008)
    add(sfx, t0, (y * 0.12 + tap[:, None] * 0.05) * amp, send=0.1)


def paper_slide(t0, dur=0.5, amp=1.0, seed=60):
    y = filtered_noise(dur, [(0, 1600), (dur, 700)], [(0, 1.1), (dur, 1.1)], [(0, 0), (dur * 0.2, 1), (dur, 0)], seed=seed)
    add(sfx, t0, y * 0.16 * amp, send=0.15)


def stamp(t0, amp=1.0):
    d = 0.5
    s = np.arange(int(d * SR)) / SR
    th = np.sin(2 * np.pi * (62 + 50 * np.exp(-s / 0.03)) * s) * np.exp(-s / 0.09)
    sl = signal.sosfilt(signal.butter(2, [300, 2500], "bandpass", fs=SR, output="sos"), rng.standard_normal(len(s))) * np.exp(-s / 0.025)
    add(sfx, t0, (th * 0.6 + sl * 0.5) * 0.4 * amp, send=0.25)


def flap(t0, amp=1.0, seed=70):
    d = 0.22
    y = filtered_noise(d, [(0, 900), (d, 400)], [(0, 1.0), (d, 1.0)], [(0, 0), (0.015, 1), (d, 0)], seed=seed)
    s = np.arange(len(y)) / SR
    th = np.sin(2 * np.pi * 110 * s) * np.exp(-s / 0.03)
    add(sfx, t0, (y * 0.18 + th[:, None] * 0.12) * amp, send=0.2)


def crinkle(t0, dur=0.3, amp=1.0, seed=80):
    g = np.random.default_rng(seed)
    t, end = t0, t0 + dur
    while t < end:
        d = 0.012
        s = np.arange(int(d * SR)) / SR
        x = signal.sosfilt(signal.butter(2, [1500, 7000], "bandpass", fs=SR, output="sos"), g.standard_normal(len(s))) * np.exp(-s / 0.003)
        add(sfx, t, x * 0.12 * amp * g.uniform(0.4, 1.0), pan=g.uniform(-0.4, 0.4), send=0.15)
        t += g.exponential(0.014)


def knock(t0, amp=1.0, f=180, dec=0.05, pan=0.0):
    d = 0.35
    s = np.arange(int(d * SR)) / SR
    x = np.sin(2 * np.pi * f * s) * np.exp(-s / dec) + 0.4 * np.sin(2 * np.pi * f * 2.3 * s) * np.exp(-s / (dec * 0.5))
    x += signal.sosfilt(signal.butter(2, [600, 3000], "bandpass", fs=SR, output="sos"), rng.standard_normal(len(s))) * np.exp(-s / 0.006) * 0.4
    add(sfx, t0, x * 0.22 * amp, pan=pan, send=0.25)


def clink(t0, amp=1.0, base=1180, pan=0.0):
    d = 1.2
    s = np.arange(int(d * SR)) / SR
    x = sum(np.sin(2 * np.pi * base * r * s) * np.exp(-s / (0.35 / r ** 0.5)) * w for r, w in [(1, 1), (2.76, 0.5), (5.4, 0.25), (8.9, 0.12)])
    add(sfx, t0, x * (1 - np.exp(-s / 0.0008)) * 0.05 * amp, pan=pan, send=0.5)


def plop(t0, amp=1.0):
    d = 0.25
    s = np.arange(int(d * SR)) / SR
    f = 320 + 700 * np.exp(-s / 0.03)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-s / 0.06) * (1 - np.exp(-s / 0.002))
    add(sfx, t0, x * 0.12 * amp, send=0.35)


def swish(t0, dur=0.45, amp=1.0, seed=90):
    y = filtered_noise(dur, [(0, 5000), (dur, 1800)], [(0, 0.8), (dur, 0.8)], [(0, 0), (dur * 0.3, 1), (dur, 0)], seed=seed)
    add(sfx, t0, y * 0.1 * amp, send=0.3)


def toggle(t0, amp=1.0):
    click(t0, 0.7 * amp, f=2500); click(t0 + 0.035, 0.5 * amp, f=3800)


def pad_chord(t0, notes, dur, amp=1.0):
    s = np.arange(int(dur * SR)) / SR
    x = np.zeros_like(s)
    for i, mm in enumerate(notes):
        f = mtof(mm)
        for det in (-0.07, 0.0, 0.07):
            x += np.sin(2 * np.pi * f * (1 + det / 100 * 12) * s + i) * (0.5 if det else 1.0) / (1 + 0.15 * i)
    env = (1 - np.exp(-s / 0.015)) * np.exp(-s / 2.6)
    add(sfx, t0, x * env * 0.035 * amp, send=0.7)



# ---- Katana additions
def slash_sfx(t0, amp=1.0, seed=101):
    """blade: a bright metallic shing panning across, an air rip into it and a sub impact"""
    d = 1.6
    s = np.arange(int(d * SR)) / SR
    ring = sum(np.sin(2 * np.pi * f * s + i) * np.exp(-s / (0.5 / (1 + i * 0.6))) * w for i, (f, w) in enumerate([(2960, 1), (4410, 0.6), (6170, 0.35), (7900, 0.2)]))
    ring *= (1 - np.exp(-s / 0.002))
    pan = np.clip(np.linspace(-0.9, 0.9, len(s)) * 1.6, -0.9, 0.9)
    st = np.stack([ring * np.cos((pan + 1) * np.pi / 4), ring * np.sin((pan + 1) * np.pi / 4)], 1)
    add(sfx, t0, st * 0.06 * amp, send=0.5)
    rip = filtered_noise(0.22, [(0, 9000), (0.22, 2500)], [(0, 0.5), (0.22, 0.6)], [(0, 0), (0.12, 1), (0.22, 0)], seed=seed)
    add(sfx, t0 - 0.12, rip * 0.32 * amp, send=0.2)
    impact(t0, 0.75 * amp, big=True, seed=seed)


def glitch_sfx(t0, dur=0.15, amp=1.0, seed=111):
    g = np.random.default_rng(seed)
    t = t0
    while t < t0 + dur:
        d = g.uniform(0.008, 0.03)
        s = np.arange(int(d * SR)) / SR
        f = g.choice([220, 440, 880, 1760, 3520]) * g.uniform(0.9, 1.1)
        x = np.sign(np.sin(2 * np.pi * f * s)) * 0.5 + g.standard_normal(len(s)) * 0.3
        x = np.round(x * 6) / 6
        add(sfx, t, x * 0.05 * amp, pan=g.uniform(-0.8, 0.8), send=0.05)
        t += d + g.uniform(0, 0.012)


def hit_small(t0, amp=1.0, seed=121):
    d = 0.6
    s = np.arange(int(d * SR)) / SR
    f = 55 + 90 * np.exp(-s / 0.04)
    x = np.tanh(2.0 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-s / 0.16))
    x += signal.sosfilt(signal.butter(2, [1200, 6000], "bandpass", fs=SR, output="sos"), rng.standard_normal(len(s))) * np.exp(-s / 0.03) * 0.45
    add(sfx, t0, x * 0.22 * amp, send=0.25)


def typekey(t0, amp=1.0):
    d = 0.05
    s = np.arange(int(d * SR)) / SR
    x = signal.sosfilt(signal.butter(2, [1800, 6000], "bandpass", fs=SR, output="sos"), rng.standard_normal(len(s))) * np.exp(-s / 0.006)
    x += np.sin(2 * np.pi * 420 * s) * np.exp(-s / 0.01) * 0.4
    add(sfx, t0, x * 0.12 * amp, pan=rng.uniform(-0.3, 0.3), send=0.1)


# =========================================================================== SFX TIMELINE (from the page's event list)
print("sfx...")
E = EV["events"]
for k, e in enumerate(E):
    t, kind, a = e["t"], e["kind"], e["k"]
    if kind == "impact": impact(t, 0.5 * a, big=a > 0.85, seed=9 + k % 7)
    elif kind == "boom": impact(t, 0.8 * a, big=True, seed=200 + k % 5)
    elif kind == "hitS": hit_small(t, a, seed=121 + k % 9)
    elif kind == "slash": slash_sfx(t, a, seed=101 + k % 4)
    elif kind == "tick": blip(t, 0.9 * a, f=2640, pan=rng.uniform(-0.4, 0.4))
    elif kind == "blip": blip(t, 0.9 * a, f=1760 * 2 ** ((k % 5) / 12 * 2), pan=rng.uniform(-0.5, 0.5))
    elif kind == "glitch": glitch_sfx(t - 0.05, 0.18, a, seed=111 + k)
    elif kind == "pen": marker(t, 1.6 * a, seed=k)
    elif kind == "whoosh": whoosh(t + 0.16, 0.55, 0.9 * a, up=True, seed=10 + k % 9, lo=500, hi=5200)
    elif kind == "whooshL": whoosh(t + 0.6, 1.3, 0.8 * a, up=True, seed=30 + k % 5, lo=300, hi=3600)
    elif kind == "scroll": tick_run(t, t + 1.8, 14, amp=0.3, f=2900, accel=1.6)
    elif kind == "swell": sub_swell(t, 3.6, 0.6 * a, f=41.2); shimmer(t + 0.05, [62, 69, 74, 78], dur=4.0, amp=0.5 * a)
    elif kind == "click": click(t, 0.9 * a, f=3000)
    elif kind == "type": typekey(t, a)
    elif kind == "toggle": toggle(t, a)
    elif kind == "step": knock(t, 0.8 * a, f=160 + 30 * (k % 6), dec=0.05, pan=-0.3 + 0.12 * (k % 6))
    elif kind == "drop": knock(t, 0.6 * a, f=110, dec=0.07); click(t + 0.01, 0.4 * a, f=3600)
    elif kind == "riser": riser(t + e.get("d", BEAT), e.get("d", BEAT), 0.6 * a, f0=400, f1=7000, seed=3 + k % 5); suck(t + e.get("d", BEAT) - 0.01, 0.45, 0.6 * a)
    elif kind == "outro": shimmer(t + 0.03, [62, 69, 74, 78, 81], dur=4.5, amp=0.9 * a); pad_chord(t, [38, 50, 57, 62, 66], 7.0, amp=0.7 * a)

# =========================================================================== REVERB
def make_ir(sec=3.2, seed=77):
    g = np.random.default_rng(seed)
    n = int(sec * SR); s = np.arange(n) / SR
    ir = np.zeros((n, 2))
    for c in range(2):
        x = g.standard_normal(n) * np.exp(-s / 0.8)
        lp1 = signal.sosfilt(signal.butter(2, 6000, "lowpass", fs=SR, output="sos"), x)
        lp2 = signal.sosfilt(signal.butter(2, 1500, "lowpass", fs=SR, output="sos"), x)
        w = np.clip(s / 1.5, 0, 1)
        ir[:, c] = lp1 * (1 - w) + lp2 * w
        ir[: int(0.012 * SR), c] = 0
    return ir / np.sqrt((ir ** 2).sum(0))



print("reverb...")
IR = make_ir()
wet = np.stack([signal.fftconvolve(rev_send[:, c], IR[:, c])[:N] for c in range(2)], 1)

# =========================================================================== MIX + MASTER
print("mix...")
sfx_bus = sfx + wet * 0.6
mix = music * 0.66 + sfx_bus * 0.9
fade_out = 1 - smoothstep((tt - (DUR - 1.6)) / 1.55)
mix *= fade_out[:, None]
env_ = np.sqrt(signal.lfilter([1 - np.exp(-1 / (0.3 * SR))], [1, -np.exp(-1 / (0.3 * SR))], (mix ** 2).mean(1)))
env_db = 20 * np.log10(env_ + 1e-9)
thr = -18.0
gr = np.where(env_db > thr, (env_db - thr) * (1 - 1 / 2.0), 0.0)
mix *= (10 ** (-gr / 20))[:, None]
meter = pyln.Meter(SR)
lufs = meter.integrated_loudness(mix)
mix *= 10 ** ((-14.0 - lufs) / 20)
ceil = 10 ** (-1.0 / 20)
mix = np.where(np.abs(mix) > 0.7 * ceil, np.sign(mix) * (0.7 * ceil + (0.3 * ceil) * np.tanh((np.abs(mix) - 0.7 * ceil) / (0.3 * ceil))), mix)
lufs2 = meter.integrated_loudness(mix)
print(f"loudness {lufs:.1f} -> {lufs2:.1f} LUFS, peak {20 * np.log10(np.max(np.abs(mix))):.2f} dBFS")
os.makedirs(OUT, exist_ok=True)
sf.write(os.path.join(OUT, "soundtrack.wav"), mix.astype(np.float32), SR, subtype="PCM_24")
print("wrote", len(mix) / SR, "s")
