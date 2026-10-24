# Coordinate parallel research workstreams

This tutorial is a sequential paper simulation. Read the [case overview](../../examples/advanced_parallel_workstreams/README.md) and keep its three records open. You will make coordination decisions from recorded evidence; no simultaneous execution occurs.

## 1. Name the work and its limits

In [workstreams](../../examples/advanced_parallel_workstreams/workstreams.md), find `W_METHODS`, `W_CHECK`, and `W_NOTE`. Write down each question, exclusion, expected output, responsible role, review route, and acceptance route. `W_METHODS` derives an estimate, `W_CHECK` checks raw-listing completeness, and `W_NOTE` explains an accepted estimate. Their IDs identify responsibilities, not branches, repositories, models, agents, or sessions. A human or tool executing a bounded task does not automatically own the workstream.

## 2. Draw the dependency edges

Use `consumed_input_ids` in [evidence dependencies](../../examples/advanced_parallel_workstreams/evidence-dependencies.md). Before the rule change, `E_METHODS_R1` consumes `D_RAW_R1` and `D_SHARED_R1`; `E_NOTE_R1` consumes `E_METHODS_R1`. `E_CHECK_R1` consumes only `D_RAW_R1`. `W_CHECK` can proceed while methods work is being prepared, but `W_NOTE` waits for an accepted methods revision. The shared raw listing and warm-up rule are dependency surfaces. If contributors edit the same mutable source, designate one writer or justified nonoverlapping partitions before work begins; separate conversations do not make writes safe.

## 3. Record a bounded result

Read events C01–C03 in [coordination](../../examples/advanced_parallel_workstreams/coordination.md). C01 records production and delivery of `E_METHODS_R1`, with exact inputs and a pending review. The separate `REV_METHODS_R1` review and `ACC_METHODS_R1` owner acceptance occur in C03. Only then does `W_NOTE` consume that revision. A completed task, delivered file, favorable review, accepted result, and downstream readiness are different states.

## 4. Test the checking claim

Read the independence statement below the workstream table. The dimension is independence from the **changed warm-up exclusion assumption**, because `E_CHECK_R1` compares the fixed raw listing against `D_RAW_R1`. The check shares that raw input and a human-authored simulation. It uses a different comparison method, saw the question but no prior methods result, and makes no claim of personnel, model, or agent independence. It cannot confirm the estimate. Compare this limitation with `ACC_CHECK_R1`'s exact listing-completeness scope.

## Check your result

Your dependency sketch should have `D_SHARED_R1 → E_METHODS_R1 → E_NOTE_R1` and a separate `D_RAW_R1 → E_CHECK_R1` edge. The note gate is acceptance of an exact methods revision. The check's valid claim is listing completeness only. Continue to [Tutorial 02](02_reconcile_a_shared_dependency_change.md) to see what changes when the rule is revised.
