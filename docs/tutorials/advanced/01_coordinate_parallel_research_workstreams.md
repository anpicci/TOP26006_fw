# Coordinate parallel research workstreams

This tutorial is a sequential paper simulation. Read the [case overview](../../examples/advanced_parallel_workstreams/README.md) and keep its three records open. You will make coordination decisions from recorded evidence; no simultaneous execution occurs. The [serial lifecycle](../../explanation/task_lifecycle.md) remains sufficient when concurrency adds no useful evidence.

## 1. Decide before splitting the work

A workstream is a bounded research responsibility with a question and follow-through. It may contain several serial tasks. It is not a chat, agent, branch, repository, or model, and it need not have a dedicated executor.

Before choosing parallel work:

1. Identify the question each output answers and who would use it. Keep one stream if the split produces no independently useful output.
2. Draw the dependencies. If a question needs an accepted upstream result, give it a readiness criterion and wait; speculation is not completed evidence.
3. Fix input revisions and inspect effects. Shared read-only inputs can be consumed at the same pinned revision. A shared mutable target has one writer by default; use explicit nonoverlapping edits and a designated integrator only when justified. Two tasks editing the same file without that agreement stay serial. Include caches, services, and external outputs, not just source files.
4. Compare the evidence benefit with coordination, review, and contention costs. Choose serial work if these costs remove the benefit, even when more workers are available.

Distinguish the reason for concurrent work:

| Pattern | Purpose and evidence boundary |
| --- | --- |
| Independent parallel work | Answer separable questions from fixed inputs, with distinct outputs and permitted effects. Neither needs the other's unfinished answer. |
| Parallel checking | Challenge a specific property with a second method; state the independence dimension and shared assumptions, inputs, code, and prior-result exposure. |
| Deliberate replication | Repeat a specified result or method for an explicit reproducibility question. State the comparison rule and common dependencies; agreement need not provide an independent scientific check. |

Two agents sharing inputs and context are not automatically independent. Separate people, chats, models, or worktrees alone do not remove common assumptions. Name what could fail in common and what the second method can actually challenge.

## 2. Name the work and its limits

In [workstreams](../../examples/advanced_parallel_workstreams/workstreams.md), find `W_METHODS`, `W_CHECK`, and `W_NOTE`. Write down each question, scope and exclusions, responsible role, exact source/input revisions, expected output, permitted effects and write boundaries, stop condition, review route, and acceptance route. These must be agreed before work begins under the actual task authorization; the table grants no effects.

`W_METHODS` derives an estimate, `W_CHECK` checks raw-listing completeness, and `W_NOTE` explains an accepted estimate. Their IDs identify responsibilities, not execution contexts. A human or tool executing a bounded task does not automatically own the workstream. Reuse these existing records for this reading exercise; no new registry or infrastructure is needed.

## 3. Draw the dependency edges

Use `consumed_input_ids` in [evidence dependencies](../../examples/advanced_parallel_workstreams/evidence-dependencies.md). Before the rule change, `E_METHODS_R1` consumes `D_RAW_R1` and `D_SHARED_R1`; `E_NOTE_R1` consumes `E_METHODS_R1`. `E_CHECK_R1` consumes only `D_RAW_R1`. `W_CHECK` can proceed while methods work is being prepared, but `W_NOTE` waits for acceptance of the exact methods revision. The shared raw listing and warm-up rule are dependency surfaces, not reasons to create separate repositories.

If a real dependency crosses repositories, use the [serial evidence-transfer lesson](../07_coordinate_a_multi_repository_change.md). Each repository retains its own permission, validation, and acceptance. Parallel organization creates no global transaction or automatic rollback of valid earlier work.

## 4. Record a bounded result

Read events C01–C03 in [coordination](../../examples/advanced_parallel_workstreams/coordination.md). C01 records production and delivery of `E_METHODS_R1`, with exact inputs and a pending review. The separate `REV_METHODS_R1` review and `ACC_METHODS_R1` acceptance by the simulated scientific lead occur in C03. Only then does `W_NOTE` consume that revision. A completed task, delivered file, favorable review, accepted result, and downstream readiness are different states, even if one person records them all. Agent or harness completion supplies none of the later decisions automatically.

## 5. Test the checking claim

Read the independence statement below the workstream table. The dimension is independence from the **changed warm-up exclusion assumption**, because `E_CHECK_R1` compares the fixed raw listing against `D_RAW_R1`. The check shares that raw input and a human-authored simulation. It uses a different comparison method, saw the question but no prior methods result, and makes no claim of personnel, model, or agent independence. It cannot confirm the estimate. Compare this limitation with `ACC_CHECK_R1`'s exact listing-completeness scope.

## Check your result

Your dependency sketch should have `D_SHARED_R1 → E_METHODS_R1 → E_NOTE_R1` and a separate `D_RAW_R1 → E_CHECK_R1` edge. Explain why methods and listing checking could overlap, why the note must wait, and why neither parallelism nor more workers improve the check's claim ceiling. Continue to [Tutorial 02](02_reconcile_a_shared_dependency_change.md) to see what changes when the rule is revised.
