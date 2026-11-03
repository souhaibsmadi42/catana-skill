---
description: Apply a visual style to an image while preserving its subject and composition.
argument-hint: <subject image> <style image or description> [strength]
disable-model-invocation: true
---
<!-- generated from data/commands.json by `python scripts/catana.py docs` — edit the JSON -->
Use the **catana** skill in **style** mode (Style transfer) for this request:

$ARGUMENTS

1. Read `${CLAUDE_PLUGIN_ROOT}/SKILL.md` (rules and workflow), then `${CLAUDE_PLUGIN_ROOT}/docs/IMAGE_GENERATION.md`.
2. Do this:
   - Spec with a subject reference (preserve list) and a style reference/description
   - Operation style_transfer (one style ref) or multi_ref_image; lint; select provider; execute with approval
   - Compare output to the subject reference for drift
3. Engine CLI: `python ${CLAUDE_PLUGIN_ROOT}/scripts/catana.py <subcommand>` (standard library only).
4. Honesty: never report a generation without a returned asset; quote cost and get approval before any paid
   connector; sound stays free (VoiceStudio / CATANA mixer / user's music).
5. If the request above is empty, ask only for: subject image.

Limitations to state when relevant: Strong styles can alter identity/geometry — iterate with a stricter preserve list.
