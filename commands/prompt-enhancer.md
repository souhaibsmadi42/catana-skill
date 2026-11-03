---
description: Turn a basic prompt into a structured, specific production prompt with a QC report.
argument-hint: <prompt> [image|video] [provider]
disable-model-invocation: true
---
<!-- generated from data/commands.json by `python scripts/catana.py docs` — edit the JSON -->
Use the **catana** skill in **enhance** mode (Prompt enhancer) for this request:

$ARGUMENTS

1. Read `${CLAUDE_PLUGIN_ROOT}/SKILL.md` (rules and workflow), then `${CLAUDE_PLUGIN_ROOT}/docs/PROMPT_ENGINEERING.md`.
2. Do this:
   - `catana.py enhance "<prompt>" --json`, then replace defaults with specifics the user implied
   - Show the before/after, the 13-field breakdown, negatives and the lint report with fixes
3. Engine CLI: `python ${CLAUDE_PLUGIN_ROOT}/scripts/catana.py <subcommand>` (standard library only).
4. Honesty: never report a generation without a returned asset; quote cost and get approval before any paid
   connector; sound stays free (VoiceStudio / CATANA mixer / user's music).
5. If the request above is empty, ask only for: prompt.

Limitations to state when relevant: Defaults are good starting points, not the user's brand; ask for brand specifics when they matter.
