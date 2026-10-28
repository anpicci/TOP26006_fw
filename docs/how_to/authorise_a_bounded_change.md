# Authorise a bounded change

Use this guide when a concrete result is ready to be assigned a permitted scope. The responsible decision-maker defines the objective and effects; the [execution policy](../../AGENTS.md) and [bounded change template](../../templates/bounded_change_prompt.md) provide the exact contract form.

## Before you start

Have the result to produce, supporting evidence, participating repository identities, each repository's own rules, and the claim that later review may assess.

## Procedure

1. State the exact result and target. Identify the inputs and the evidence needed to support the claim.
2. Fix the invariants: target identity, scientific or technical objective, authorized paths and actions, validation limits, and protection of unrelated changes or work belonging to another task or contributor.
3. Choose the smallest sufficient execution model: a serial task in one repository, separable parallel work with an explicit join, or dependent work across repositories. Use added coordination only when the dependencies require it.
4. Give each execution step explicit permission for its own paths and actions. The overall plan may limit what later steps can do, but it does not authorize any step by itself; permission for one step does not carry to another.
5. For every participating repository, bind its exact identity, base and candidate revisions, repository-specific rules, responsible decision-maker, and permitted paths and actions. A path or branch name alone does not authorize a change.
6. If compatibility across repositories matters, name the exact revision combination to validate and the consumer or interface where it will be checked. Set the dependency order without assuming a global Git transaction.
7. Declare any maintained fallback or local repair in advance. It must preserve the same invariants, have a bounded retry or repair limit, and repeat the affected validation gate. A new scientific or technical choice needs a separate decision.
8. State which concrete consequence stops a dependent action, what evidence must be read back, and which independent authorized work can continue. An uncertain side effect needs state inspection before any separately authorized retry.
9. When temporary state is used, preserve the portable result and evidence before removal. Authorize removal only for the exact temporary files, worktrees, or refs created for this task, then read back the final state to check that unrelated state remains intact.
10. Name the task-specific scientific, application, affected-consumer, test, and runtime checks that matter. Workflow correctness does not perform them automatically. Identify who may later accept which claim.

## Verify the result

Check that the authorization and executable instructions agree on every repository, revision, path, action, dependency, validation limit, and stop condition, and on who decides whether to accept which claim. [Contract guidance](../../CPC.md) supplies exact field syntax when needed.

## Stop instead of proceeding if...

The target, decision-maker, repository-specific rules, candidate combination, or scientific or technical choice is unresolved. Preserve valid results and seek a decision for the affected action. A local commit or executor report does not authorize another repository or acceptance.
