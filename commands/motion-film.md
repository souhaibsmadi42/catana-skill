---
description: CATANA's original engine: a beat-locked, code-rendered motion graphics film cut to a music track, rendered locally to MP4.
argument-hint: <product/site> [music file] [length] [format 16:9|9:16|1:1|4:5]
disable-model-invocation: true
---
<!-- generated from data/commands.json by `python scripts/catana.py docs` — edit the JSON -->
Use the **catana** skill in **motion** mode (Motion film (Katana style)) for this request:

$ARGUMENTS

1. Read `${CLAUDE_PLUGIN_ROOT}/SKILL.md` (rules and workflow), then `${CLAUDE_PLUGIN_ROOT}/references/motion-film.md`.
2. Do this:
   - Follow references/motion-film.md: scaffold, read the music, plan in beats, build shots, stills QC, render, mix, deliver
   - Optional free voiceover via VoiceStudio, ducked under music
3. Engine CLI: `python ${CLAUDE_PLUGIN_ROOT}/scripts/catana.py <subcommand>` (standard library only).
4. Honesty: never report a generation without a returned asset; quote cost and get approval before any paid
   connector; sound stays free (VoiceStudio / CATANA mixer / user's music).
5. If the request above is empty, ask only for: subject: product, site or brand.

Limitations to state when relevant: No AI footage (by design); needs Node 18+, Python 3 audio packages and Chrome; Bring your own music; SFX are procedural.
