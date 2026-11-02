# Synthetic parallel research workstreams

This is a teaching case, not a live project registry, scientific result, agent configuration, or execution record. Read [workstreams](workstreams.md), [evidence dependencies](evidence-dependencies.md), and [coordination history](coordination.md) together. All events are constructed in sequential logical order; no concurrent agent or provider execution is represented. Read the case without executing commands, creating a notebook, or calculating new measurements.

## Three research responsibilities

The question is how a repeated-measurements result and its explanation survive a changed shared assumption. Imagine an instrument with a warm-up observation whose treatment needs correction:

- **Methods/analysis (`W_METHODS`):** identify the rule and the estimate it supports, without altering raw observations.
- **Independent checking (`W_CHECK`):** compare the fixed observation listing with its declared source for completeness. This is independent of the warm-up exclusion assumption only; it is not an independent estimate or validation of the physics result.
- **Results/methods explanation (`W_NOTE`):** explain the exact accepted methods result and its limitations; wait for its acceptance before using it.

`D_SHARED_R1` is the initial warm-up exclusion rule; `D_SHARED_R2` is its corrected revision. `D_RAW_R1` is the fixed raw listing. The IDs represent declared revisions, not files in the existing measurement example. No scientific code or data is changed. All roles are human-authored simulation roles; neither separate personnel nor model independence is demonstrated.

## Follow the revision change

The records contain the following story. Read each cited event and its dependency row before deciding what remains usable.

| Step | Recorded inputs and decision |
| --- | --- |
| C01–C03: first result | `E_METHODS_R1` consumes `D_RAW_R1` and `D_SHARED_R1`. It is delivered, then reviewed and accepted. Only afterward does `E_NOTE_R1` consume `E_METHODS_R1`, with its own review and acceptance. |
| C02: narrow check | `E_CHECK_R1` consumes `D_RAW_R1` only. Its accepted claim is listing completeness, excluding the rule and estimate. It could overlap methods work, though this exercise is sequential. |
| C04: rule revised | `D_SHARED_R2` supersedes R1. The direct edge to `E_METHODS_R1` and transitive edge to `E_NOTE_R1` make both stale for current use. Preserve their historical rows, reviews, and acceptances. |
| C05: unaffected evidence | `E_CHECK_R1` stays valid because `D_RAW_R1` is unchanged and the check has no path to the warm-up rule. Preserve its narrow acceptance; do not reuse it to confirm the revised estimate. |
| C06–C08: affected path reconciled | `E_METHODS_R2` consumes `D_RAW_R1` and `D_SHARED_R2`. Production and delivery precede separate review and owner acceptance at C08. |
| C09: explanation updated | `E_NOTE_R2` consumes accepted `E_METHODS_R2`, then receives its own review and acceptance. R1 evidence remains visible as superseded history. |
| C10: handoff | The receiver reopens accepted and stale references and reads back the next dependency check. A separate hypothetical owner decision makes responsibility transfer effective. |

**Intentional stale-input trap:** after C04, try proposing the already accepted `E_NOTE_R1` as the current note. The map records `E_NOTE_R1 → E_METHODS_R1 → D_SHARED_R1`, while the current rule is R2. Reject the proposal from those identities, not intuition about the note's wording. This counterexample adds no event or record system. Tutorial [02](../../tutorials/advanced/02_reconcile_a_shared_dependency_change.md#3-detect-the-stale-input-trap) walks through the repair.

Two methods outputs consume explicitly different rule revisions; each explanation names its consumed result. Only that dependency path needs reconciliation here. If the raw listing changed too, the check's preservation argument would fail and its claim would need revisiting.

## What the records establish

These three records help a human coordinator see responsibility, dependency, review, acceptance, and transfer decisions. They model neither a scheduler, lock service, scientific database, nor harness. The governing scientific owner and project authority still come from applicable governance and explicit task authorization. Records and executor completion cannot grant permissions or acceptance. The [serial handoff method](../../tutorials/09_transfer_work_to_a_collaborator.md) remains valid; a real repository boundary adds separate permissions and consumer checks, without a global transaction or automatic rollback of valid partial work.

This example requires no additional checkout or executor. In current TOP-26-006 practice, TOP26006_fw, TOPEFT, and TOPCOFFEA normally have at most one persistent active development worktree per repository/workstream, separate from the canonical checkout; fixture/test worktrees are temporary and separately authorized. This project rule is not universal Git behavior. Worktrees separate checkout/edit contexts, not security or scientific authority. Agents and harnesses are optional implementation aids with no qualification or adoption earned here; see the [advanced route's limits](../../advanced/index.md#optional-implementation-aids).
