# katana — a Claude skill for Katana-style motion films

Give Claude a product, a website or a brand plus a music track, and it builds a **beat-locked, high-energy motion
graphics film** in code. You get hard cuts on the beat, huge slam typography, slash transitions, shake, punch-ins, whips,
glitches, strobes and flashes, real UI and data, and a sound-effects mix on top of your track. The film renders
frame-exact to MP4.

No AI video generation and no credits: everything is HTML/CSS/SVG (with optional three.js), rendered by headless Chrome.

## What you get

- **A workflow Claude follows** (`SKILL.md`): gather real material, read the music, plan the film in beats, build shots,
  check stills, render, mix and run QC.
- **A project template** (`assets/template/`):
  - a deterministic `render(t)` page;
  - a shot and beat-grid kit;
  - slam, mask-rise, tracking, echo, counter and typewriter text;
  - a slash motif;
  - a WebGL finishing pass (shake, chromatic aberration, whip blur, slash split, glitch, invert, flash, grain, vignette);
  - a two-pass Puppeteer renderer;
  - a procedural SFX mixer;
  - QC and contact-sheet tools.
- **A music analyser** (`tools/music_scan.py`): finds the tempo and beat offset, prints a per-bar energy table and
  guesses the sections (intro / build / DROP / break / SILENCE).
- **Guides:**
  - motion language (section treatments, effect rates, type rules);
  - the API;
  - the render/audio pipeline;
  - adding a 3D model.

## Install

**Claude Code:** clone the repo into your skills folder; the folder name becomes the skill name.

```bash
git clone https://github.com/<your-username>/katana-skill.git ~/.claude/skills/katana
```

(Windows: `%USERPROFILE%\.claude\skills\katana`.) Restart Claude Code, and `katana` appears in the skills list.

**Claude.ai / Claude desktop:** download `katana.skill` from the Releases page and upload it under
Settings → Capabilities → Skills, or zip this folder and upload the zip.

## Requirements (on the machine that renders)

- Node.js 18+ and npm
- Python 3 with `numpy scipy soundfile pyloudnorm pillow` (`matplotlib` is optional, for the music plot)
- Google Chrome, Chromium or Microsoft Edge (found automatically; set `CHROME=/path` to override)
- `ffmpeg-static`, which `npm install` adds to each film project

## Use it

Ask in plain words:

> make a 30 second katana-style promo for my app *Name* — features …, tagline …, use this track: song.wav

> cut a vertical 9:16 hype reel of our dashboard to this music, use the screenshots in ./shots

> redo our launch video in katana motion style

Claude scaffolds a project with:

```bash
python ~/.claude/skills/katana/scripts/new_film.py my-film --music song.wav --duration 30
```

Then it writes `src/scenes.js`, checks stills, and renders `master_noaudio.mp4` plus `soundtrack.wav`, muxing them into
a final MP4 and a web copy.

## Good to know

- **Bring your own music.** The edit is built on a real track you have the rights to. The skill doesn't synthesise
  music; without a track it makes an SFX-only cut and says so.
- **Synthesised SFX.** Sound effects are made in code. Swap in recorded ones in `audio/mix.py` if you have them.
- **Check the downbeat.** The music scan's downbeat guess is the weakest step; the table makes it easy to correct
  (`--offset`).
- **Render time.** A 2-minute film takes about 7–9 minutes on 6 render workers; a 15–30 s film takes 2–5 minutes.
- **Honest content.** The skill tells Claude to use only real numbers and to label any illustrative visuals.

## License

MIT — see [LICENSE](LICENSE). The fonts (Anton, Inter, JetBrains Mono) are installed from npm under the SIL Open Font
License and are not bundled here.
