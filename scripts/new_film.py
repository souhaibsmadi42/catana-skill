"""Scaffold a Katana motion film project from the skill's template (the CATANA motion engine).

  python new_film.py <target_dir> [--music track.wav] [--duration 120] [--format 16:9|9:16|1:1|4:5] [--fps 60]
                                  [--offset s] [--no-install]

Copies assets/template -> target_dir, installs node deps (puppeteer-core, three, ffmpeg-static, fonts), copies the
music to assets/ (converting mp3/m4a/aac to wav with ffmpeg when needed), scans it and writes BPM / OFFSET /
DURATION / W / H / FPS into src/lib.js. Re-running on a non-empty directory refuses (nothing is overwritten).
"""
import argparse, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(os.path.dirname(HERE), 'assets', 'template')
FORMATS = {'16:9': (1920, 1080), '9:16': (1080, 1920), '1:1': (1080, 1080), '4:5': (1080, 1350)}
NATIVE_AUDIO = {'.wav', '.flac', '.ogg', '.aiff', '.aif'}   # what soundfile reads without ffmpeg


def find_ffmpeg(dst):
    for c in (os.path.join(dst, 'node_modules', 'ffmpeg-static', n) for n in ('ffmpeg', 'ffmpeg.exe')):
        if os.path.exists(c): return c
    return shutil.which('ffmpeg')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('target')
    ap.add_argument('--music')
    ap.add_argument('--duration', type=float)
    ap.add_argument('--format', choices=sorted(FORMATS), default='16:9')
    ap.add_argument('--fps', type=int, choices=[24, 25, 30, 50, 60], default=60)
    ap.add_argument('--offset', type=float, help='beat-0 offset in seconds (overrides the scan guess)')
    ap.add_argument('--no-install', action='store_true')
    a = ap.parse_args(argv)

    if a.music and not os.path.isfile(a.music): sys.exit(f'--music: no such file {a.music}')
    if a.duration is not None and not (1 <= a.duration <= 600): sys.exit('--duration must be between 1 and 600 seconds')
    dst = os.path.abspath(a.target)
    if os.path.exists(dst) and os.listdir(dst):
        sys.exit(f'{dst} exists and is not empty — pick a new folder')
    shutil.copytree(TEMPLATE, dst, dirs_exist_ok=True)
    for d in ('assets', 'out', 'qa', 'build'):
        os.makedirs(os.path.join(dst, d), exist_ok=True)
    print('template ->', dst)

    if not a.no_install:
        npm = shutil.which('npm') or shutil.which('npm.cmd')
        if not npm: sys.exit('npm not found — install Node.js 18+, then run `npm install` in ' + dst)
        print('npm install ...')
        subprocess.run([npm, 'install', '--no-audit', '--no-fund', '--loglevel=error'], cwd=dst, check=True)

    lib = os.path.join(dst, 'src', 'lib.js')
    src = open(lib, encoding='utf8').read()
    W, H = FORMATS[a.format]
    src = re.sub(r'W: [0-9]+, H: [0-9]+, FPS: [0-9]+', f'W: {W}, H: {H}, FPS: {a.fps}', src)
    if a.duration:
        src = re.sub(r'DURATION: [0-9.]+', f'DURATION: {a.duration:g}', src)
    if a.music:
        ext = os.path.splitext(a.music)[1].lower() or '.wav'
        if ext in NATIVE_AUDIO:
            name = 'music' + ext
            shutil.copy(a.music, os.path.join(dst, 'assets', name))
        else:
            ff = find_ffmpeg(dst)
            if not ff: sys.exit(f'{ext} music needs ffmpeg to convert — install ffmpeg or pass a .wav file')
            name = 'music.wav'
            subprocess.run([ff, '-y', '-v', 'error', '-i', a.music, '-ar', '48000', '-ac', '2', os.path.join(dst, 'assets', name)], check=True)
            print(f'converted {os.path.basename(a.music)} -> assets/{name}')
        src = re.sub(r"MUSIC: '[^']*'", f"MUSIC: 'assets/{name}'", src)
        cmd = [sys.executable, os.path.join(dst, 'tools', 'music_scan.py'), os.path.join(dst, 'assets', name)]
        if a.offset is not None: cmd += ['--offset', str(a.offset)]
        r = subprocess.run(cmd, cwd=dst, capture_output=True, text=True)
        print(r.stdout)
        m = re.search(r'FILM: BPM: ([0-9.]+), OFFSET: ([0-9.]+)', r.stdout)
        if m:
            src = re.sub(r'BPM: [0-9.]+', f'BPM: {m.group(1)}', src)
            src = re.sub(r'OFFSET: [0-9.]+', f'OFFSET: {m.group(2)}', src)
            print(f'set BPM {m.group(1)}, OFFSET {m.group(2)} (verify the downbeat in qa/music_scan.png)')
        else:
            print('music scan failed — set BPM/OFFSET in src/lib.js by hand:\n' + (r.stderr or '').strip()[-800:])
    open(lib, 'w', encoding='utf8').write(src)
    print(f'format {a.format} {W}x{H} @ {a.fps} fps')
    print('next: edit src/scenes.js, then  node render.mjs stills 1 2 3')


if __name__ == '__main__':
    main()
