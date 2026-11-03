# Social Media Studio — short-form and platform content

Content built for Instagram Reels, TikTok, YouTube Shorts, YouTube, LinkedIn and paid social: platform ratios,
hooks, scripts, scene templates and variations. Also covers **faceless video**. Use for `/catana:faceless-video`, social
requests, and platform cut-downs of other studios' work. Preset: **`social`** for vertical short-form (`ugc` when it
should look creator-made).

## Platform specs (from `data/platforms.json` — `catana.py platforms`)

| Platform key | Ratio | Ideal length | Hook by | Safe zone (keep text out of) |
|---|---|---|---|---|
| `instagram_reels` | 9:16 | 7–30 s | 1.5 s | top 14 %, bottom 20 %, right 12 % |
| `tiktok` | 9:16 | 9–34 s | 1.5 s | top 12 %, bottom 22 %, right 15 % |
| `youtube_shorts` | 9:16 | 15–50 s | 2 s | top 12 %, bottom 20 %, right 12 % |
| `instagram_feed` / `facebook_feed` | 4:5 | 6–30 s | 2 s | 5 % margins (FB bottom 12 %) |
| `instagram_story` | 9:16 | 5–15 s | 1 s | top 14 %, bottom 20 % |
| `youtube` | 16:9 | 30–600 s | 5 s | bottom 10 % |
| `linkedin` | 1:1 (4:5, 16:9 ok) | 15–90 s | 3 s | bottom 10 %; captions essential |
| `ads_vertical` | 9:16 | 6–20 s | 1 s | bottom 25 %; brand + offer by s3 |

Limits change; these are planning defaults. Pass `--platform <key>` to `enhance`/`plan new` and the ratio, fps and
length follow. For 1:1 or 16:9 platforms, rewrite the composition for that frame — the `social` preset's
composition text is written for vertical.

## Hook formulas (first 1–2 s, picture + on-screen text + VO agree)

- **Result first:** show the end state, then "here's how".
- **Pattern interrupt:** unexpected motion in frame 1 (whip pan, object into lens, crash zoom).
- **Direct callout:** "If you <audience trait>, stop scrolling."
- **Curiosity gap:** "Nobody tells you this about <topic>."
- **Contrast:** before/after split or "<common way> vs <better way>".
- **Number:** "3 <things> that <outcome>" — and deliver exactly 3.
- **Question:** a specific question the viewer answers in their head.

## Scene templates

| Template | Beats |
|---|---|
| Hook → payoff (engine default `social`) | hook (push_in) → payoff (whip_pan) → proof (tracking) → cta (static) |
| Listicle | hook → item 1 → item 2 → item 3 → cta (one shot per item, number on screen) |
| Tutorial | result → step 1 → step 2 → step 3 → result again (loop) |
| Before/after | before → transition (whip / match cut) → after → cta |
| Story | hook line → setup → twist → payoff |
| Loop | last frame matches the first so the clip replays seamlessly (`transition_out: "match cut to first frame"`) |

## Workflow

1. Script: hook (formula) + 2–4 beats + CTA; ≤ 2.5 words/s; one idea per beat; on-screen text ≤ 6 words per card.
2. `python <skill>/scripts/catana.py plan new "<idea>" --platform tiktok --out plan.json` → fill shots (`vo` = lines,
   `notes` = on-screen text), compile, fix `fits: false` VO lines.
3. Variations: 3 hooks × same body is the cheapest test; then angle variants (see the matrix in `studios/advertising.md`).
4. Cut-downs from a master: re-plan with another `--platform`; recompose rather than crop when going 16:9 → 9:16.
5. Captions burned in, inside the safe zone; first frame works as a thumbnail.

## Faceless video (`/catana:faceless-video`)

No presenter: narrated b-roll, kinetic typography, data, screen recordings.

- **Kinetic type / data / UI films** → the local CATANA motion engine (free, deterministic, any ratio):
  `python <skill>/scripts/new_film.py my-short --format 9:16 --duration 30 [--music track.wav]`, then follow
  `references/motion-film.md` (beat-locked cuts, slam type, real product UI). Voiceover: write the script in
  `build/compiled.json` form or call `catana.py voice speak --file script.txt --out build/vo.wav` and add a cue to
  `build/vo.json`; `audio/mix.py` ducks the music under it.
- **Narrated b-roll** → AI Director plan with `vo` per shot, b-roll shots from `enhance` (no faces, hands/objects/
  places), VoiceStudio VO (`catana.py voice plan`), captions per line.
- Voice: `catana.py voice archetypes "documentary narrator"` / `voice describe "calm male, low pitch, british"`.

## Verified prompt patterns (`catana.py enhance`, QC A 100)

```text
tiktok video of a barista pouring latte art in a bright cafe, whip pan, 5 seconds
instagram reel of a runner tying her shoes on a city bridge at sunrise, push in, 4 seconds
linkedin video of a founder presenting a product dashboard in a modern office, slow dolly in, 8 seconds, 1:1
```

(The LinkedIn example is detected as the `product` preset — the dashboard is the hero — and scores A; forcing
`--domain social` keeps vertical-framing text, so prefer the detected preset for 1:1/16:9.)

Pattern: `<platform> <video|reel> of <one subject doing one thing> <in a bright, specific place>, <energetic move>, <2–5 s>`.

## Camera

`push_in`, `whip_pan`, `zoom_in` (crash), `handheld`, `tracking`, `top_down` (hands/food/desk), `fpv_drone` (travel,
events), `static` (talking/loop). Something must move in frame 1.

## Provider routing

| Need | Operation | Options |
|---|---|---|
| Vertical shots | t2v, i2v | Higgsfield `kling3_0`, `seedance_2_0`, `grok_video_v15_lite` (fast), `minimax_h3` — verify, quote, approve |
| Reframe 16:9 → 9:16 | reframe | Higgsfield `reframe` (paid) or recompose; CATANA motion engine renders natively at any ratio (free) |
| Shorts packages | — | Higgsfield `shorts_studio_*` (paid, verify) |
| VO | tts | VoiceStudio (free) |
| Kinetic type / faceless | motion_graphics | CATANA motion engine (free) |

## QC checklist

- [ ] Ratio matches the platform; nothing important in the safe-zone margins
- [ ] Hook within the platform's hook time; motion in the first frame
- [ ] Length within `ideal_seconds`; VO lines fit
- [ ] Captions on; ≤ 6 words per text card; readable on a phone
- [ ] CTA single and visible; loop point if intended
- [ ] Variants named and differing on one axis

## Failure modes → fixes

| Symptom | Fix |
|---|---|
| Slow start | cut the first second; start on motion or the result |
| Text under UI | move into the safe zone (see table) |
| Too much per shot | one idea per 1–3 s |
| 16:9 crop looks wrong in 9:16 | recompose vertically (stack foreground/subject/sky) |

## Deliverables

Script with hook options · storyboard · platform cuts · captions file/text · VO (free) · thumbnails/first frames ·
variation list with names.
