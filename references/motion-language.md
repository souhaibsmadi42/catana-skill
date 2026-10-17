# Katana motion language

The film is a remix of energy, not of shots. These are the rules that made "The Cut" work, with the numbers.

## 1. Energy follows the music's sections

| Section (what the track does) | Picture | Cut rate | FX budget |
|---|---|---|---|
| **Cold open** (sparse kick, no hats) | near-black; short glimpses of the subject on each kick (3–10 frames), a hairline, small mono labels, typed text | a glimpse per beat | tiny hit per kick |
| **Intro words** (pulse) | one huge word per beat or two, staccato; subject faint behind | 1–2 beats | hit on each word, invert frame on the punchline |
| **Build / riser** | something accelerates: orbit speeding up, counter racing, strobes on 16ths in the last bar | 16ths at the end | rumble + chromatic ramp + glitch ramp; last ¼–½ beat goes black (anticipation) |
| **Drop** (full groove) | slash + flash on the downbeat; then a new picture every 1–2 beats, alternating layouts (left/right), hard camera changes | 1–2 beats | hit on every cut, punch on the offbeat, glitch every 3rd cut |
| **Breakdown** (energy falls) | one continuous move (a section plane descending, a slow orbit), text rises out of masks | 4–8 beats | almost none; maybe a swell |
| **Tension** (kick only) | UI close-ups, a cursor, typing on 16ths, camera pushes | 2–4 beats | micro punches on kicks |
| **Silence** (music stops) | nearly empty frame, one calm sentence in a smaller sentence-case font, grain up | none | none — the contrast sells the next drop |
| **Riser into a drop** | the subject creeps back, line charging, frame rumble, black on the last frame | — | rumble, caRamp, slash line lead 0.2 s |
| **Recap** (late drop) | one word per 2 beats with stutter echo, one long camera move running through all cuts | 2 beats | hit per word |
| **Outro** (music decays) | lockup: mark draw-on + wordmark tracking collapse, tagline, small label; ghost subject at very low alpha, one light sweep; fade the last ~1.5 s | hold | one slash on the downbeat, then nothing |

Rates that read as "Katana" at 1080p60: during drops ≥ 1 hit per beat, ≥ 1 picture change per 2 beats,
a flash/slash at every section start. Calm sections are deliberate — without them the drops don't land.

## 2. The motif
Pick one transition device and make it mean something for the subject. "The Cut": a gradient blade streaks across
(`addSlashLine`, 0.2 s lead), the frame splits along it on impact (`slash`), the gap glows. It opens the logo, every
drop and the outro. Use the brand's gradient for the line. Other motifs that fit the same engine: a scan line, a
shutter, a page-fold, a cursor click — but use one.

## 3. Typography
Three roles, never more:
- **DISPLAY** — Anton (or the brand's condensed face), uppercase, 150–620 px, tight leading (.86). Slams: scale 1.15–1.3 → 1 over 0.15–0.3 s outExpo, hard cut out. Outline variants (`.outline`) for echoes and giant numerals.
- **LABEL** — mono, 15–24 px, tracked .14–.3 em, dim. Timecode, chapter, "ELEMENT 53045 · DOOR", data captions. These give the "system" feel.
- **BRAND** — the real wordmark font (e.g. Inter 800 with a brand gradient). Reveal by tracking collapse (`track`), never letter by letter.
Rules: one idea per beat; put words where the picture is empty (alternate left/right); estimate Anton width ≈ chars × 0.45 × size; colour the punchline (accent or brand gradient); dark text on light (inverted) frames.

## 4. Effects vocabulary (post.js)
| Effect | Use | Typical |
|---|---|---|
| `hit(t,k)` | every hard accent | k 0.4–0.8 words, 1.0–1.5 drops |
| `punch(t,k,d)` | offbeats, counter ticks | k 0.01–0.04 |
| `flash(t,frames)` | drop downbeat, big reveal | 1–3 frames |
| `slash(t,ang,k)` + `addSlashLine` | section transitions | ang ≈ −0.42 (−24°) or +0.38 |
| `whip(t,dur,ang)` | scene change inside a section | dur 0.24–0.32, cut at t+dur/2 |
| `glitch(t,dur,k)` | fills, every 3rd cut, hand-offs | 0.1–0.25 s |
| `invert(t,2/60)` | strobes on 8ths/16ths in builds | 4–8 in a row |
| `rumble(t,dur)` + `caRamp` | the bar before a drop | 1–2 beats |
| `zoomBlur` | spins, explosions | 0.4 s |
| `gradeAt(t)` | per-section grain/vignette, speed blur `bx` for spins | grain .055 base, .085 silence |
Keep it on the beat: an effect off-grid reads as a mistake.

## 5. Picture sources (strongest first)
1. The product itself rebuilt as HTML/CSS (UI panels, tables, dropdowns, toggles) — crisp at any zoom; animate the real states (progress bars, counters, toggles flipping).
2. The product's own data as graphics: counters with real numbers, lists, drawings, charts.
3. A 3D model of the subject (three.js world) in graphic looks: flat solid + white edges, x-ray lines, white "paper" look, colour-coded categories.
4. Screenshots, cropped and pushed (only if rebuilding is impossible; keep them small or moving).
Show the real thing. Label illustrative content as such; don't put invented numbers on screen.

## 6. Copy
Write the film as ~25–40 short lines. Structure that works for products: hook number → the pain (2–3 words a beat) → the turn (logo) → what it does (feature per 2–4 beats with a proof number) → the quiet line (silence) → the payoff montage (verbs) → lockup + tagline. Sentence-case only in the silence and the outro sub-line.

## 7. Restraint checklist
- Is there a calm section before each big drop?
- Does every section start with a visible event (slash/flash/whip)?
- Is anything moving that shouldn't (UI jitter, text crawling)? Katana moves the *camera*, not the layout.
- Can every line be read in its time on screen (≥ 0.4 s for 1 word, ≥ 1 s for a sentence)?
