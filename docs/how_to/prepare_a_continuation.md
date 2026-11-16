# Prepare a continuation

Use this guide when valid accepted research evidence supports a further bounded task. Preserve the established result while asking only for delta evidence.

## Before you start

Have the accepted claim, review and task/evidence or scientific acceptance decision locators, retained source identity and an unambiguous repository/target binding. Use the [continuation template](../../templates/continuation_prompt.md) with live [CPC.md](../../CPC.md). The executor acquires volatile task-scope state before the effect that consumes it. Author-side live readback is needed only when a particular author decision depends on it; lack of host access alone does not prevent a fully bound task from entering runtime preflight.

## Procedure

1. Write **closure**: exact accepted claim, assumptions, source identity, and evidence locator.
2. Write **delta**: the new question or edit, exact paths/effects, and new evidence needed. Example: add missing CSV provenance to a synthetic interpretation note without changing the calculation.
3. Write **invalidation boundary**: changes to consumed inputs, method, assumptions, environment, governance or target identity that defeat the particular reused claim. A changed OID alone does not invalidate unchanged dependencies. Read material current branch/HEAD/status before dependent effects rather than copying yesterday's values.
4. Write **checks_not_to_repeat**: accepted numerical or source checks that remain valid while the boundary holds.
5. Specify fresh readbacks, permissions, validation ceiling, stop behavior, and how partial valid work survives a bounded failure.

   A compact field pattern is `closure: <claim + locator>; delta: <new effect>; invalidation_boundary: <drift that stops reuse>; checks_not_to_repeat: <accepted checks>`; fill it with actual accepted-evidence identities and author-fixed choices before dispatch. Bind volatile observations to the executor's pre-effect checks rather than guessing them or requiring the author to relay them.

Deliver the complete continuation and its author-selected run configuration
together, with the reusable task clearly delimited and the configuration outside
it; use the [direct authoring guide](write_a_prompt_manually.md).
A new attempt retains prior evidence and records its new configuration without
overwriting earlier results. Derive the planned Mermaid from the actual new work:
show reused inputs, remaining work and independent partial results where relevant.
After execution, annotate what actually happened without implying that reused
work was repeated.

The field pattern above is an aid, not a complete prompt or a second continuation
vocabulary. In a governed task, use `accepted_prior_evidence` for claims and
locators and `delta_scope` for new work, together with `continuation_of` and
the other applicable [CPC fields](../../CPC.md#conditional-field-router).

## Verify the result

A successor can map each reused claim to provenance and each new check to the delta. A material invalidation stops the dependent reuse until revalidated; independent valid evidence remains available.

## Stop instead of proceeding if...

Accepted evidence is unreadable or contradicted, relevant state drifted, or the new request exceeds authorization. Do not silently adopt existing edits or rerun an entire accepted analysis to compensate for a narrow provenance defect.

## Generic example

After a provenance-only repair, cite the accepted synthetic mean, request a methods-note transfer, and re-read analysis HEAD/status.

## What this does not establish

A continuation does not make stale Git state current or broaden the scope of task/evidence or scientific acceptance.
