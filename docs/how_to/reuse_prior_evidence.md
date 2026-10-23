# Reuse prior evidence

Use this guide when a new research task depends on a reviewed result and the relevant assumptions may still hold.

## Before you start

Locate the accepted artifact, exact claim, input/source IDs, review finding, and owner acceptance scope. Read [AGENTS.md](../../AGENTS.md) evidence-reuse rules and [Tutorial 6](../tutorials/06_continue_from_existing_evidence.md).

## Procedure

1. Cite the accepted claim and its provenance, not merely a report filename or PASS label.
2. Define the invalidation boundary for inputs, method, model, environment, relevant Git identity, and governance. Distinguish stable checked evidence from volatile branch/status/permissions.
3. Re-read only volatile facts material to the new decision: for example, `git -C "$analysis" rev-parse HEAD`, `git -C "$analysis" status --porcelain=v1 -- interpretation.md`, and `sha256sum "$analysis/data/measurements.csv"`.
4. List `checks_not_to_repeat` while the boundary holds. Ask for delta evidence only, such as the exact note diff and provenance fields.

## Verify the result

The continuation states which prior arithmetic remains closed, which fresh facts were checked, and why the new evidence is sufficient. In the synthetic case, a missing source hash in the note requires a note repair, not an automatic numerical rerun.

## Stop instead of proceeding if...

A boundary fact changed, provenance cannot be reopened, or acceptance was broader than the evidence supports. A prior result cannot certify current live state or a new scientific interpretation.

## Generic example

Carry a checked synthetic mean into a methods note after confirming the CSV hash and source HEAD; inspect only the new note diff.

## What this does not establish

Prior numerical evidence does not prove today's task-path cleanliness or method suitability for real data.
