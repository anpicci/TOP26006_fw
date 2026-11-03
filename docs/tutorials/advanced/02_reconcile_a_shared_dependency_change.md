# Reconcile a shared dependency change

Continue the [synthetic case](../../examples/advanced_parallel_workstreams/README.md) after [Tutorial 01](01_coordinate_parallel_research_workstreams.md). Use the [dependency map](../../examples/advanced_parallel_workstreams/evidence-dependencies.md) and [coordination history](../../examples/advanced_parallel_workstreams/coordination.md). This remains a sequential reading exercise; do not calculate an estimate or run workers.

## 1. Trace the changed input

At C04, `D_SHARED_R2` corrects and supersedes `D_SHARED_R1`, the warm-up exclusion rule. Follow `consumed_input_ids`, rather than the names of workers: `E_METHODS_R1` directly consumes R1, and `E_NOTE_R1` consumes that methods result. Mark both historical evidence rows `stale_for_current_use`. Keep the old rows and their prior review and acceptance; those decisions still describe the old scope, not permission to reuse the claims under R2.

Pause current use of these affected claims. Do not stop every workstream or restart the whole programme. Trace exact direct and transitive edges, and extend the affected set if newly discovered evidence reveals another relevant dependency.

## 2. Preserve unaffected evidence

`E_CHECK_R1` consumes `D_RAW_R1` only. That raw listing did not change, so there is no dependency path from the changed rule to this check. C05 preserves its accepted listing-completeness claim. Do not promote it into a check of the estimate. Selective invalidation means revisiting only evidence reachable from the changed assumption, subject to its declared claim and any newly discovered dependencies. If the raw listing itself changed, this reason for preserving the check would no longer hold.

## 3. Detect the stale-input trap

Deliberately propose reusing `E_NOTE_R1` as the current explanation after C04 because it was previously accepted. Read its `consumed_input_ids`: it cites `E_METHODS_R1`, which cites `D_SHARED_R1`. The current rule is R2. That recorded identity path rejects the reuse even if the prose still looks plausible. Giving the note a new filename or moving it to another worktree does not update its evidence. This is a reading counterexample, not an extra event in the historical record.

## 4. Repair and reopen the gate

C06 produces `E_METHODS_R2` using `D_RAW_R1` and `D_SHARED_R2`; C07 delivers it. At that point its execution and delivery are complete, while review and acceptance remain pending. At C08, a separate reviewer records `REV_METHODS_R2` and the scientific lead then records `ACC_METHODS_R2` for the estimate under R2. Only this accepted revision is ready for `W_NOTE` to consume. C09 updates `E_NOTE_R2`, obtains `REV_NOTE_R2`, and records `ACC_NOTE_R2`. The new rows supersede current use of R1 rows without erasing history.

Reconciliation therefore covers the affected methods-to-explanation path, with its review and acceptance gates. The listing check is retained for its unchanged narrow claim. A later blocked explanation does not erase valid methods evidence or trigger an automatic rollback.

## 5. Transfer responsibility and continue

At C10, sender A prepares accepted references, stale history, the last verified state, and unresolved effects. Receiver B acknowledges receipt and scope, then reopens the accepted R2 references and reads back which R1 revisions are stale, the last verified checkpoint, and the next dependency check. The hypothetical scientific lead separately makes `AUTH_TRANSFER_1` effective for future `W_METHODS` work. Receipt or acknowledgment alone does not prove comprehension or transfer responsibility. The handoff carries evidence; only the separate scientific lead's decision changes responsibility, and any next action still needs its own authority.

Before any next task, B checks the current dependency identity and the authority for that bounded action. No interrupted external effect exists in this simulation. In real work, a paused conversation is not evidence that an external process stopped; inspect its actual state under the applicable authorization before considering a retry. See [stop or resume one workstream](../../how_to/advanced/stop_or_resume_one_workstream.md).

## Check your result

The before/after state is: `E_METHODS_R1` and `E_NOTE_R1` stale for current use; `E_CHECK_R1` valid only for listing completeness; `E_METHODS_R2` accepted at C08; `E_NOTE_R2` accepted at C09; transfer effective at C10. Identify the exact edge that rejects the stale note, explain why the check is retained, and name the two human acceptance gates before the current explanation is ready. The answer is selective repair, not a default rerun of every workstream.
