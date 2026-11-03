---
description: Film-grade sequence: scene planning, characters, storyboard, camera direction, lighting, grade and continuity.
argument-hint: <story/idea> [length] [genre] [aspect]
disable-model-invocation: true
---
<!-- generated from data/commands.json by `python scripts/catana.py docs` — edit the JSON -->
Use the **catana** skill in **cinematic** mode (Cinematic video) for this request:

$ARGUMENTS

1. Read `${CLAUDE_PLUGIN_ROOT}/SKILL.md` (rules and workflow), then `${CLAUDE_PLUGIN_ROOT}/references/studios/cinematic.md`, `${CLAUDE_PLUGIN_ROOT}/references/director.md`.
2. Do this:
   - Logline, beats, characters in the bible (@id), named grade and lens package
   - `catana.py plan new --domain cinematic`, fill shots with continuity (screen direction, eyelines, motivated light)
   - Compile → keyframe + video prompts per shot, QC, sequence continuity
   - Execute shot by shot (reference the previous frame for continuity) or deliver the pack
3. Engine CLI: `python ${CLAUDE_PLUGIN_ROOT}/scripts/catana.py <subcommand>` (standard library only).
4. Honesty: never report a generation without a returned asset; quote cost and get approval before any paid
   connector; sound stays free (VoiceStudio / CATANA mixer / user's music).
5. If the request above is empty, ask only for: story or idea.

Limitations to state when relevant: Character consistency across many AI shots needs reference images and multi-reference models.
