# Prepare a continuation

Use this guide when valid accepted research evidence supports a further bounded task. Preserve the established result while asking only for delta evidence.

## Before you start

Have the accepted claim, review/owner decision locator, source identity, and a fresh task-scope status readback. Use the [continuation template](../../templates/continuation_prompt.md) with live [CPC.md](../../CPC.md).

## Procedure

1. Write **closure**: exact accepted claim, assumptions, source identity, and evidence locator.
2. Write **delta**: the new question or edit, exact paths/effects, and new evidence needed. Example: add missing CSV provenance to a synthetic interpretation note without changing the calculation.
3. Write **invalidation boundary**: input, method, assumption, environment, governance, Git identity, or task-path changes that would defeat reuse. Read current branch/HEAD/status again rather than copying yesterday's values.
4. Write **checks_not_to_repeat**: accepted numerical or source checks that remain valid while the boundary holds.
5. Specify fresh readbacks, permissions, validation ceiling, stop behavior, and how partial valid work survives a bounded failure.

   A compact field pattern is `closure: <claim + locator>; delta: <new effect>; invalidation_boundary: <drift that stops reuse>; checks_not_to_repeat: <accepted checks>`; fill it with observed identities, not placeholders, before dispatch.

## Verify the result

A successor can map each reused claim to provenance and each new check to the delta. The prompt stops if an invalidation fact changed.

## Stop instead of proceeding if...

Accepted evidence is unreadable or contradicted, relevant state drifted, or the new request exceeds authorization. Do not silently adopt existing edits or rerun an entire accepted analysis to compensate for a narrow provenance defect.

## Generic example

After a provenance-only repair, cite the accepted synthetic mean, request a methods-note transfer, and re-read analysis HEAD/status.

## What this does not establish

A continuation does not make stale Git state current or broaden owner acceptance.
