# AI Director sample: Villa Saadiyat

Brief: *"Create a luxury cinematic commercial for a modern villa in Abu Dhabi."* 40 s, 16:9.

1. `python scripts/catana.py plan new "<brief>" --duration 40 --out plan.json` built the skeleton: 8 architecture beats
   with durations sized to each camera move.
2. Claude filled the creative layer in `plan.json`: logline, concept, visual direction, continuity bible (`@villa`,
   `@guest`, palette, negatives), and per-shot subject, action, environment, voiceover and SFX.
3. `python scripts/catana.py plan compile plan.json --out .` wrote `compiled.json` and **[storyboard.md](storyboard.md)**:
   a keyframe image prompt and a video prompt for every shot, the sound plan, the edit sequence and QC.
   **8/8 shots grade A, sequence ready, all VO lines fit their slots.**

Nothing here was generated with a paid service. It's the production pack you'd hand to a generator (Higgsfield, Runway…)
after approving the quoted cost, or shoot as a real film.
