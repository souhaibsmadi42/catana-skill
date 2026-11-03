---
description: Turn a reference image into a directed video shot (optionally to a last frame).
argument-hint: <image> [what moves] [camera move] [duration] [last frame image]
disable-model-invocation: true
---
<!-- generated from data/commands.json by `python scripts/catana.py docs` — edit the JSON -->
Use the **catana** skill in **i2v** mode (Image to video) for this request:

$ARGUMENTS

1. Read `${CLAUDE_PLUGIN_ROOT}/SKILL.md` (rules and workflow), then `${CLAUDE_PLUGIN_ROOT}/docs/VIDEO_GENERATION.md`, `${CLAUDE_PLUGIN_ROOT}/docs/CAMERA_MOVEMENTS.md`.
2. Do this:
   - Spec with a first_frame reference (and last_frame if given) and an explicit preserve list
   - Choose one primary camera move that fits the duration; one action per ~2.5 s
   - Lint, select provider (i2v or first_last), quote, execute, verify against the start frame
   - Fallback: prompt pack
3. Engine CLI: `python ${CLAUDE_PLUGIN_ROOT}/scripts/catana.py <subcommand>` (standard library only).
4. Honesty: never report a generation without a returned asset; quote cost and get approval before any paid
   connector; sound stays free (VoiceStudio / CATANA mixer / user's music).
5. If the request above is empty, ask only for: start image.

Limitations to state when relevant: Geometry and text can drift at high motion intensity — keep it low for architecture/products.
