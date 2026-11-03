# Sample film: "CATANA 2.0" (motion engine)

A 15-second motion film made with CATANA's local motion engine, the same `scenes.js` rendered at three formats:

| 16:9 (1920×1080) | 9:16 (1080×1920) | 1:1 (1080×1080) |
|---|---|---|
| [▶ MP4](../../media/catana-2-sample-16x9.mp4) | [▶ MP4](../../media/catana-2-sample-9x16.mp4) | [▶ MP4](../../media/catana-2-sample-1x1.mp4) |

- 120 BPM beat grid, 30 fps, 7 shots: brief → slash to the wordmark → beat words → the real storyboard → proof numbers
  → QC D to A → lockup.
- On-screen facts are real: the storyboard rows are the actual `catana.py plan compile` output for the villa brief, and
  27 camera moves, 17 commands, 11 domain presets and 48/48 tests are this repo's numbers.
- Sound is SFX only, procedural, from the cue list. No music track was available. A VoiceStudio voiceover can be added
  with `build/vo.json` (see `references/motion-film.md`).
- Free and local: no AI generation and no credits.

## Render it yourself

```bash
python scripts/new_film.py my-sample --duration 15 --format 9:16 --fps 30
```
```bash
cp examples/catana-2-promo/scenes.js my-sample/src/scenes.js
```
Set `OFFSET: 0` in `my-sample/src/lib.js` (there is no music to align to). Then:
```bash
cd my-sample && node render.mjs video --workers 4 --name master_noaudio.mp4
```
```bash
node tools/page.mjs "src/index.html?dump=1" build/events.json && python audio/mix.py
```
Use `--format 16:9` or `--format 1:1` for the other cuts; the scene file lays itself out for each.
