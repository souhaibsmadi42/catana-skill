---
description: Build a multi-scene sequence with continuity: scenes, shots, transitions and consistent prompts.
argument-hint: <sequence description or plan.json> [scenes] [length]
disable-model-invocation: true
---
<!-- generated from data/commands.json by `python scripts/catana.py docs` — edit the JSON -->
Use the **catana** skill in **scenes** mode (Scene builder) for this request:

$ARGUMENTS

1. Read `${CLAUDE_PLUGIN_ROOT}/SKILL.md` (rules and workflow), then `${CLAUDE_PLUGIN_ROOT}/references/director.md`.
2. Do this:
   - Split into scenes, each with its own location/time of day; shots inherit the bible
   - Mark deliberate lighting changes as transitions; vary camera moves
   - Compile and run sequence QC (aspect, style, grade, time of day, character wording, total length)
3. Engine CLI: `python ${CLAUDE_PLUGIN_ROOT}/scripts/catana.py <subcommand>` (standard library only).
4. Honesty: never report a generation without a returned asset; quote cost and get approval before any paid
   connector; sound stays free (VoiceStudio / CATANA mixer / user's music).
5. If the request above is empty, ask only for: sequence description or an existing plan.json.

Limitations to state when relevant: Generation of each shot follows the provider rules (quote + approval).
