# Reconcile a shared dependency change

Continue the [synthetic case](../../examples/advanced_parallel_workstreams/README.md) after [Tutorial 01](01_coordinate_parallel_research_workstreams.md). Use the [dependency map](../../examples/advanced_parallel_workstreams/evidence-dependencies.md) and [coordination history](../../examples/advanced_parallel_workstreams/coordination.md). This remains a sequential reading exercise.

## 1. Trace the changed input

At C04, `D_SHARED_R2` corrects and supersedes `D_SHARED_R1`. Follow `consumed_input_ids`, rather than the names of workers: `E_METHODS_R1` directly consumes R1, and `E_NOTE_R1` consumes that methods result. Mark both historical evidence rows `stale_for_current_use`. Keep the old rows and their prior review and acceptance; those decisions still describe the old scope.

## 2. Preserve unaffected evidence

`E_CHECK_R1` consumes `D_RAW_R1` only. That raw listing did not change, so there is no dependency path from the changed rule to this check. C05 preserves its accepted listing-completeness claim. Do not promote it into a check of the estimate. Selective invalidation means revisiting only evidence reachable from the changed assumption, subject to its declared claim and any newly discovered dependencies.

## 3. Repair and reopen the gate

C06 produces `E_METHODS_R2` using `D_SHARED_R2`; C07 delivers it. At that point its execution and delivery are complete, while review and acceptance remain pending. At C08, a separate reviewer records `REV_METHODS_R2` and the scientific owner then records `ACC_METHODS_R2` for the estimate under R2. Only this accepted revision is ready for `W_NOTE` to consume. C09 updates `E_NOTE_R2`, obtains `REV_NOTE_R2`, and records `ACC_NOTE_R2`. The new rows supersede current use of R1 rows without erasing history.

## 4. Transfer responsibility and continue

At C10, sender A prepares accepted references, stale history, the last verified state, and unresolved effects. Receiver B acknowledges the scope and checkpoint; the hypothetical scientific owner makes `AUTH_TRANSFER_1` effective for future `W_METHODS` work. A message receipt alone would not transfer responsibility. Before any next task, B checks the current dependency identity and the authority for that bounded action. No interrupted external effect exists in this simulation.

## Check your result

The before/after state is: `E_METHODS_R1` and `E_NOTE_R1` stale for current use; `E_CHECK_R1` valid only for listing completeness; `E_METHODS_R2` accepted at C08; `E_NOTE_R2` accepted at C09; transfer effective at C10. The answer is selective repair, not a default rerun of every workstream.
