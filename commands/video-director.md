---
description: Direct a complete production from one idea: concept to final edit, with execution through available providers.
argument-hint: <idea> [length] [platform] [references] [budget]
disable-model-invocation: true
---
<!-- generated from data/commands.json by `python scripts/catana.py docs` — edit the JSON -->
Use the **catana** skill in **director** mode (Video director) for this request:

$ARGUMENTS

1. Read `${CLAUDE_PLUGIN_ROOT}/SKILL.md` (rules and workflow), then `${CLAUDE_PLUGIN_ROOT}/references/director.md`.
2. Do this:
   - Deliver the 12 Director outputs: concept, visual direction, storyboard, shot list, camera moves, lighting, scene descriptions, image prompts, video prompts, transitions, sound design, edit sequence
   - Compile + QC; quote; execute approved shots; VO free via VoiceStudio; assemble via the edit list
   - Report generated vs prompt-only shots honestly
3. Engine CLI: `python ${CLAUDE_PLUGIN_ROOT}/scripts/catana.py <subcommand>` (standard library only).
4. Honesty: never report a generation without a returned asset; quote cost and get approval before any paid
   connector; sound stays free (VoiceStudio / CATANA mixer / user's music).
5. If the request above is empty, ask only for: idea.

Limitations to state when relevant: Final assembly of AI clips is an edit step (EDL provided); the motion engine can assemble type/graphics locally.
