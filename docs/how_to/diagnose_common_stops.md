# Diagnose common stops

Use this guide when a task reports a failed gate or uncertain result. Preserve the direct evidence and any valid completed result.

## Before you start

Read the authorized task, the relevant [execution policy](../../AGENTS.md), the last completed result, and the observed command or artifact state. Do not reset, clean, overwrite, or retry an uncertain effect automatically.

## Procedure

1. Record the observed result, relevant branch and revision, task-path status, input identity, and completed steps. Separate observations from inferences.
2. Ask what continuing could make incorrect, unauthorized, identity-ambiguous, unsafe, or irreversible, and which current rule or dependency establishes that consequence.
3. Decide whether the missing item is mandatory for this action, optional with an authorized maintained fallback, or relevant only to a later phase. Bound any stop to the affected action; identify independent authorized work that can continue.
4. If an operation may have taken effect but its result is uncertain, inspect the actual process, repository, output, or service state before considering recovery. State inspection does not authorize a retry or compensation.
5. Report the consequence, observed evidence, surviving valid results, unfinished work, and the decision or external condition needed next.

| Observation | Check now | Disposition |
| --- | --- | --- |
| A file hash or HEAD differs from an earlier observation | Compare the exact changed dependency with the current task basis. | Drift is information until it changes a required identity, rule, or result; rebind only the affected decision. |
| A branch, task path, or input identity conflicts with the authorization | Read the exact ref, status, path, and governing scope. | Stop the dependent write or comparison; preserve unrelated valid work. |
| An optional artifact or convenience mechanism is unavailable | Check whether an authorized maintained fallback preserves the same target, effects, and validation. | Use and validate that fallback within its limit; do not block unrelated work. |
| An exact input needed for comparison is missing | Identify the comparison and its required source. | Stop that comparison; independently authorized acquisition can continue. |
| Scientific validation leaves a residual | Preserve the result, method, thresholds, and evidence. | Report the residual for the responsible scientific decision; do not hide it by changing the method or threshold. |
| A command ended without reliable confirmation of what it changed | Inspect the actual state where the command could have had an effect. | Leave retry or compensation pending until its separate authorization and consequences are clear. |
| A later repository step cannot proceed | Read back the valid earlier repository results and their interfaces. | Preserve and report the partial state; do not assume global rollback. |
| A requirement belongs to a later phase | Identify the phase and its dependency on the current result. | Report it at that boundary; do not invent a current blocker. |

## Verify the result

The report ties each stop to a concrete current consequence, preserves valid evidence, and names the next authorized decision. The [recovery tutorial](../tutorials/08_recover_from_a_stopped_task.md) shows a bounded example.

## Stop instead of proceeding if...

The consequence or applicable authority cannot be established. Do not turn uncertainty into a success claim or expand the task to repair it.
