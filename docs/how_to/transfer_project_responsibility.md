# Transfer project responsibility

Use this guide when a collaborator must continue a research workstream from recorded evidence rather than oral context.

## Before you start

Have the human owner/authority status, accepted results, source versions, reviews, live repository state, and [handoff template](../../templates/handoff.md).

## Procedure

1. Record scientific owner and who may authorize, author prompts, execute, review, and accept. Transfer of a document does not automatically transfer any authority.
2. List exact accepted claims, qualifications, decision locators, repository IDs, branch/commit identities, input hashes, and evidence paths. Mark superseded wording or artifacts.
3. Record residual mandate, deferred/blocking findings, invalidation boundary, `checks_not_to_repeat`, and the next owner decision.
4. Attach material stopped-state evidence when relevant: committed HEAD plus task-path status and exact uncommitted diff. For example, `git -C "$repo" rev-parse HEAD`, `git -C "$repo" status --porcelain=v1 -- interpretation.md`, and `git -C "$repo" diff -- interpretation.md`.
5. Ask the successor to reopen cited artifacts and report what they understood. Record receipt and comprehension separately.

## Verify the result

A successor can locate the accepted evidence, reproduce current-state readback, and state the next authorized question. [Tutorial 9](../tutorials/09_transfer_work_to_a_collaborator.md) gives a synthetic example.

## Stop instead of proceeding if...

An essential identity or acceptance locator is unknown, a live state is stale, or the successor cannot confirm understanding. “Handoff sent” does not prove acquisition, grant writes, or establish scientific acceptance.

## Generic example

A handoff cites the accepted synthetic result commit and an uncommitted note diff that stopped a later task.

## What this does not establish

Sending a handoff does not prove recipient comprehension or transfer write authority.
