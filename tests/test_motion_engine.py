"""The original CATANA motion engine: format independence, fixed bugs, scaffold. Set CATANA_INTEGRATION=1 to also
render stills in 16:9 / 9:16 / 1:1 (needs Node 18+, Chrome and network for npm install)."""
import glob
import os
import re
import shutil
import subprocess
import sys
import unittest
import wave
import math
import struct

from helpers import ROOT, tmpdir

T = os.path.join(ROOT, "assets", "template")


def have(mod):
    try:
        __import__(mod)
        return True
    except ImportError:
        return False


class Static(unittest.TestCase):
    def read(self, rel):
        with open(os.path.join(T, rel), encoding="utf8") as f:
            return f.read()

    def test_no_hard_coded_frame_size_outside_film(self):
        for rel in ["src/index.html", "src/style.css", "src/scenes.js", "src/kit.js", "src/post.js", "src/main.js", "tools/page.mjs",
                    "tools/evalfx.mjs", "render.mjs"]:
            txt = self.read(rel)
            if rel == "src/style.css":
                txt = txt.replace("--W: 1920px; --H: 1080px;", "")
            txt = re.sub(r"[WH] / \d+", "", txt)        # scale ratios against a reference size are fine; literal frame sizes are not
            self.assertNotRegex(txt, r"\b1920\b|\b1080\b", rel)

    def test_flash_uses_film_fps(self):
        self.assertIn("frames / FILM.FPS", self.read("src/post.js"))

    def test_mixer_supports_voiceover_ducking(self):
        mix = self.read("audio/mix.py")
        self.assertIn("build\", \"vo.json\"", mix)
        self.assertIn("duck", mix)

    def test_film_reader(self):
        out = subprocess.run(["node", "-e", f"import('{T}/tools/film.mjs').then(m=>console.log(JSON.stringify(m.readFilm('{T}'))))"],
                             capture_output=True, text=True)
        if out.returncode != 0:
            self.skipTest("node not available")
        self.assertIn('"W":1920', out.stdout)
        self.assertIn('"FPS":60', out.stdout)


class Scaffold(unittest.TestCase):
    def wav(self, path, seconds=40.0, bpm=124):
        sr = 22050
        beat = 60 / bpm
        with wave.open(path, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
            frames = bytearray()
            for i in range(int(seconds * sr)):
                t = i / sr
                ph = (t - 0.1) % beat
                v = math.sin(2 * math.pi * 55 * ph) * math.exp(-ph * 25) if t > 0.1 else 0.0
                frames += struct.pack("<h", int(v * 20000))
            w.writeframes(bytes(frames))

    @unittest.skipUnless(have("numpy") and have("scipy") and have("soundfile"), "music scan needs numpy, scipy, soundfile")
    def test_scaffold_with_music_and_format(self):
        d = tmpdir()
        music = os.path.join(d, "track.wav")
        self.wav(music)
        proj = os.path.join(d, "film")
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "new_film.py"), proj, "--music", music, "--duration", "20",
                            "--format", "9:16", "--fps", "30", "--no-install"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)        # crashed before the fix (no assets/ dir)
        lib = open(os.path.join(proj, "src", "lib.js")).read()
        self.assertIn("W: 1080, H: 1920, FPS: 30", lib)
        self.assertIn("DURATION: 20", lib)
        bpm = float(re.search(r"BPM: ([0-9.]+)", lib).group(1))
        self.assertAlmostEqual(bpm, 124, delta=0.5)
        self.assertTrue(os.path.exists(os.path.join(proj, "assets", "music.wav")))

    def test_scaffold_rejects_bad_input(self):
        d = tmpdir()
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "new_film.py"), os.path.join(d, "f"), "--music", "/nope.wav",
                            "--no-install"], capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no such file", r.stderr)
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "new_film.py"), os.path.join(d, "f"), "--format", "7:3",
                            "--no-install"], capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)

    @unittest.skipUnless(have("numpy") and have("scipy") and have("soundfile"), "music scan needs numpy, scipy, soundfile")
    def test_music_scan_short_track_does_not_crash(self):
        d = tmpdir()
        p = os.path.join(d, "short.wav")
        self.wav(p, seconds=5)
        r = subprocess.run([sys.executable, os.path.join(T, "tools", "music_scan.py"), p], capture_output=True, text=True, cwd=d)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("unreliable", r.stdout)


@unittest.skipUnless(os.environ.get("CATANA_INTEGRATION") == "1", "set CATANA_INTEGRATION=1 to render (needs Node, Chrome, npm)")
class RenderIntegration(unittest.TestCase):
    def test_stills_in_three_formats(self):
        from PIL import Image
        base = tmpdir()
        nm = os.environ.get("CATANA_NODE_MODULES")
        for fmt, size in (("16:9", (1920, 1080)), ("9:16", (1080, 1920)), ("1:1", (1080, 1080))):
            proj = os.path.join(base, fmt.replace(":", "x"))
            r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "new_film.py"), proj, "--duration", "12", "--format", fmt]
                               + (["--no-install"] if nm else []), capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            if nm:
                os.symlink(nm, os.path.join(proj, "node_modules"))
            r = subprocess.run(["node", "render.mjs", "stills", "4.6", "9.3"], cwd=proj, capture_output=True, text=True, timeout=300)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertNotIn("[pageerror]", r.stdout)
            stills = glob.glob(os.path.join(proj, "out", "stills", "*.png"))
            self.assertEqual(len(stills), 2, f"{fmt}: stills not written")
            for f in stills:
                self.assertEqual(Image.open(f).size, size)


if __name__ == "__main__":
    unittest.main()
