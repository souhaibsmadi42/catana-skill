"""Scaffold a Katana film project from the skill's template.
  python new_film.py <target_dir> [--music path/to/track.wav] [--duration 120] [--no-install]
Copies assets/template -> target_dir, installs node deps (puppeteer-core, three, ffmpeg-static, fonts),
copies the music to assets/music.wav, scans it and writes BPM / OFFSET / DURATION into src/lib.js.
Re-running on an existing directory refuses (nothing is overwritten).
"""
import argparse, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(os.path.dirname(HERE), 'assets', 'template')

ap = argparse.ArgumentParser()
ap.add_argument('target')
ap.add_argument('--music')
ap.add_argument('--duration', type=float)
ap.add_argument('--no-install', action='store_true')
a = ap.parse_args()

dst = os.path.abspath(a.target)
if os.path.exists(dst) and os.listdir(dst):
    sys.exit(f'{dst} exists and is not empty — pick a new folder')
shutil.copytree(TEMPLATE, dst, dirs_exist_ok=True)
for d in ('out', 'qa', 'build'):
    os.makedirs(os.path.join(dst, d), exist_ok=True)
print('template ->', dst)

if not a.no_install:
    npm = shutil.which('npm') or shutil.which('npm.cmd')
    if not npm: sys.exit('npm not found — install Node.js 18+, then run `npm install` in ' + dst)
    print('npm install ...')
    subprocess.run([npm, 'install', '--no-audit', '--no-fund', '--loglevel=error'], cwd=dst, check=True)

lib = os.path.join(dst, 'src', 'lib.js')
src = open(lib, encoding='utf8').read()
if a.duration:
    src = re.sub(r'DURATION: [0-9.]+', f'DURATION: {a.duration:g}', src)
if a.music:
    ext = os.path.splitext(a.music)[1].lower() or '.wav'
    name = 'music' + ext
    shutil.copy(a.music, os.path.join(dst, 'assets', name))
    src = re.sub(r"MUSIC: '[^']*'", f"MUSIC: 'assets/{name}'", src)
    r = subprocess.run([sys.executable, os.path.join(dst, 'tools', 'music_scan.py'), os.path.join(dst, 'assets', name)], cwd=dst, capture_output=True, text=True)
    print(r.stdout)
    m = re.search(r'FILM: BPM: ([0-9.]+), OFFSET: ([0-9.]+)', r.stdout)
    if m:
        src = re.sub(r'BPM: [0-9.]+', f'BPM: {m.group(1)}', src)
        src = re.sub(r'OFFSET: [0-9.]+', f'OFFSET: {m.group(2)}', src)
        print(f'set BPM {m.group(1)}, OFFSET {m.group(2)} (verify the downbeat in qa/music_scan.png)')
    else:
        print(r.stderr)
open(lib, 'w', encoding='utf8').write(src)
print('next: edit src/scenes.js, then  node render.mjs stills 1 2 3')
