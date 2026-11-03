---
description: Narrated video without an on-camera person: b-roll or kinetic typography with voiceover and captions.
argument-hint: <topic/script> [platform] [length] [visual style: b-roll|kinetic|mixed]
disable-model-invocation: true
---
<!-- generated from data/commands.json by `python scripts/catana.py docs` — edit the JSON -->
Use the **catana** skill in **faceless** mode (Faceless video) for this request:

$ARGUMENTS

1. Read `${CLAUDE_PLUGIN_ROOT}/SKILL.md` (rules and workflow), then `${CLAUDE_PLUGIN_ROOT}/references/studios/social.md`, `${CLAUDE_PLUGIN_ROOT}/references/motion-film.md`.
2. Do this:
   - Write the narration (hook in the first 1.5 s) and split it into timed lines
   - Kinetic: build with the local motion engine (free) at the platform format; b-roll: plan shots and prompts per line
   - Render the narration with VoiceStudio (free) and mix it under the picture with ducking
   - Burn-in captions recommended for muted autoplay
3. Engine CLI: `python ${CLAUDE_PLUGIN_ROOT}/scripts/catana.py <subcommand>` (standard library only).
4. Honesty: never report a generation without a returned asset; quote cost and get approval before any paid
   connector; sound stays free (VoiceStudio / CATANA mixer / user's music).
5. If the request above is empty, ask only for: topic or script.

Limitations to state when relevant: AI b-roll shots need a connector (paid); kinetic/motion versions are free and local; The motion engine needs Node, Python and Chrome on the machine.
