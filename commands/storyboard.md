---
description: A complete storyboard and shot list from an idea — no generation.
argument-hint: <idea> [length] [platform] [domain]
disable-model-invocation: true
---
<!-- generated from data/commands.json by `python scripts/catana.py docs` — edit the JSON -->
Use the **catana** skill in **storyboard** mode (Storyboard) for this request:

$ARGUMENTS

1. Read `${CLAUDE_PLUGIN_ROOT}/SKILL.md` (rules and workflow), then `${CLAUDE_PLUGIN_ROOT}/references/director.md`.
2. Do this:
   - `catana.py plan new`, fill concept, bible and every shot
   - `catana.py plan compile --out dir` → storyboard.md (keyframe + video prompt per shot, timing, camera, transitions, sound, edit sequence, QC)
   - Offer to execute any shot or the whole board next
3. Engine CLI: `python ${CLAUDE_PLUGIN_ROOT}/scripts/catana.py <subcommand>` (standard library only).
4. Honesty: never report a generation without a returned asset; quote cost and get approval before any paid
   connector; sound stays free (VoiceStudio / CATANA mixer / user's music).
5. If the request above is empty, ask only for: idea.

Limitations to state when relevant: Text storyboard; keyframe images only if the user then asks to generate them.
