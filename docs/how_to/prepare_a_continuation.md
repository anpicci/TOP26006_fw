# Prepare a continuation

**Problem:** a valid prior task needs one more bounded step.

Write four sections: **closure** (exact accepted claim and artifact), **delta** (new change), **invalidation boundary** (facts whose drift would defeat reuse), and **checks not to repeat** (accepted checks protected while boundary holds). Add new evidence required, current branch/HEAD readback, exact scope and effects, and a stop on unexpected drift. Use the [continuation template](../../templates/continuation_prompt.md) and live [CPC.md](../../CPC.md).

A continuation does not rerun everything and does not silently adopt local edits. If the boundary is crossed, serialize what changed and return to the owner for a new decision.
