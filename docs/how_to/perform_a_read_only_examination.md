# Perform a read-only examination

Use this guide to answer one research or provenance question before deciding whether a change is justified.

## Before you start

Have a narrow decision question, exact readable sources, validation ceiling, and evidence destination. Use `investigation_only` under [AGENTS.md](../../AGENTS.md); no tracked mutation is implied.

## Procedure

1. Write the question and expected discriminating observations, not an expected verdict. Example: “does the reported synthetic mean follow from the five input rows and stated weighting?”
2. Name exact read-only repository paths and permitted local checks. Exclude source edits, cleanup, remote writes, production, and acceptance.
3. Read stable source identity and fresh volatile facts only when material: `git -C "$repo" rev-parse HEAD`, `git -C "$repo" status --porcelain=v1 -- <task-paths>`, and input hashes where provenance matters.
4. Execute only the authorized lightweight calculation or inspection. Serialize command, input identity, output, errors, and what was not examined in the report.
5. Separate direct observation from executor qualification. Send any defect to a reviewer/owner for a new bounded decision.

## Verify the result

A reader can reproduce the observation from cited inputs and command, see uncertainty and limits, and identify the unanswered decision.

## Stop instead of proceeding if...

Necessary source/evidence is missing, live state contradicts the declared target, or a new scientific choice is required. A read-only observation does not authorize a fix or establish owner acceptance.

## Generic example

A researcher asks whether five synthetic CSV rows reproduce a reported mean; capture the CSV hash, calculation command, and output.

## What this does not establish

A reproduced number does not establish a real-data uncertainty model or authorize a code fix.
