# Authorise a bounded change

Use this guide when a concrete result is ready to be assigned a permitted scope. The responsible decision-maker defines the objective and effects; the [execution policy](../../AGENTS.md) and [bounded change template](../../templates/bounded_change_prompt.md) provide the exact contract form.

## Before you start

Have the result to produce, supporting evidence, participating repository identities, applicable native policies, and the claim that later review may assess.

## Procedure

1. State the exact result and target. Identify the inputs and the evidence needed to support the claim.
2. Fix the invariants: target identity, scientific or technical objective, authorized paths and effects, validation limits, and protection of foreign work.
3. Choose the smallest sufficient execution model: a serial task in one repository, separable parallel work with an explicit join, or dependent work across repositories. Use added coordination only when the dependencies require it.
4. Give each execution step its own explicit paths and effects. An overall workflow scope sets a ceiling; it grants no step permission on its own, and permission from one step does not carry to another.
5. For every participating repository, bind its exact identity, base and candidate revisions, native policy, responsible authority, and writable paths and effects. A path or branch name is not a grant.
6. If compatibility across repositories matters, name the exact revision combination to validate and the consumer or interface where it will be checked. Set the dependency order without assuming a global Git transaction.
7. Declare any maintained fallback or local repair in advance. It must preserve the same invariants, have a bounded retry or repair limit, and repeat the affected validation gate. A new scientific or technical choice needs a separate decision.
8. State which concrete consequence stops a dependent action, what evidence must be read back, and which independent authorized work can continue. An uncertain side effect needs state inspection before any separately authorized retry.
9. When temporary state is used, require portable result and evidence preservation before retirement. Authorize removal only for exact task-owned temporary surfaces and require final noninterference readback.
10. Name the task-specific scientific, application, affected-consumer, test, and runtime checks that matter. Workflow correctness does not perform them automatically. Identify who may later accept which claim.

## Verify the result

The authorization and executable contract agree on every repository, revision, path, effect, dependency, validation limit, stop condition, and acceptance boundary. [Contract guidance](../../CPC.md) supplies exact field syntax when needed.

## Stop instead of proceeding if...

The target, authority, native policy, candidate combination, or scientific or technical choice is unresolved. Preserve valid results and seek a decision for the affected action. A local commit or executor report does not authorize another repository or acceptance.
