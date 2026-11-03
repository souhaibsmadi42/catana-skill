---
description: Build a professional camera-movement prompt (or explain a move) from the 27-move library.
argument-hint: <move or description> [subject] [duration] [speed]
disable-model-invocation: true
---
<!-- generated from data/commands.json by `python scripts/catana.py docs` — edit the JSON -->
Use the **catana** skill in **camera** mode (Camera movement) for this request:

$ARGUMENTS

1. Read `${CLAUDE_PLUGIN_ROOT}/SKILL.md` (rules and workflow), then `${CLAUDE_PLUGIN_ROOT}/docs/CAMERA_MOVEMENTS.md`.
2. Do this:
   - Look the move up (`catana.py camera show|find`), check combinations and minimum duration (`camera check`)
   - Phrase it with `camera phrase` and place it first in the video prompt
   - Explain best use, subject behaviour, mistakes and good combinations
3. Engine CLI: `python ${CLAUDE_PLUGIN_ROOT}/scripts/catana.py <subcommand>` (standard library only).
4. Honesty: never report a generation without a returned asset; quote cost and get approval before any paid
   connector; sound stays free (VoiceStudio / CATANA mixer / user's music).
5. If the request above is empty, ask only for: move id/name or a description.

Limitations to state when relevant: Models follow one or two simultaneous moves reliably; more are flagged.
