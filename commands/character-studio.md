---
description: Create a consistent AI character: bible, turnaround sheet, expressions, and reuse across shots.
argument-hint: <character description> [style] [uses: ad|film|ugc]
disable-model-invocation: true
---
<!-- generated from data/commands.json by `python scripts/catana.py docs` — edit the JSON -->
Use the **catana** skill in **character** mode (Character studio) for this request:

$ARGUMENTS

1. Read `${CLAUDE_PLUGIN_ROOT}/SKILL.md` (rules and workflow), then `${CLAUDE_PLUGIN_ROOT}/references/studios/character.md`.
2. Do this:
   - Write the bible entry (identity, face, hair, body, wardrobe, marks, voice) as one locked description
   - Generate a turnaround/expression sheet (with approval) and save references
   - Reuse via @id tokens + references in every later shot; lint sequences for drift
3. Engine CLI: `python ${CLAUDE_PLUGIN_ROOT}/scripts/catana.py <subcommand>` (standard library only).
4. Honesty: never report a generation without a returned asset; quote cost and get approval before any paid
   connector; sound stays free (VoiceStudio / CATANA mixer / user's music).
5. If the request above is empty, ask only for: character description.

Limitations to state when relevant: No real-person likeness without consent; Perfect identity lock depends on the model's reference support.
