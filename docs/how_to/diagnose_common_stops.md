# Diagnose common stops

Use this guide after a research task fails a declared gate. Preserve direct evidence first; a failed gate does not erase earlier valid results.

## Before you start

Read the exact prompt, failed command, [AGENTS.md](../../AGENTS.md), [CPC.md](../../CPC.md), and completed-stage evidence. Do not reset, clean, stash, overwrite, or retry automatically.

## Procedure

1. Capture the exact observed failure, branch/HEAD, task-path status, relevant artifact hashes, and last completed stage.
2. Use the table to separate observation from inference and select a safe next decision.
3. Report the blocker, surviving evidence, unfinished stages, and responsible owner or external condition. Example: ` M interpretation.md` on the next task's input note means stop and request ownership classification; it does not invalidate a previously accepted calculation.

| Stop | What was observed | Do not infer | Safe evidence to collect | Resolution and reusable work |
| --- | --- | --- | --- | --- |
| Governance drift | Live file/hash differs from declared basis | Old contract still applies | Exact path and hash/diff | Prompt author/owner reauthorizes; earlier evidence survives unless invalidated |
| Branch/applicability mismatch | Current ref or candidates disagree | Name similarity proves applicability | Local heads, ancestry, relevant diff | Owner/prompt author reconciles; unrelated accepted results survive |
| Dirty/colliding state | Staged, unstaged, conflict, or untracked task path | Edit is task-owned | Exact status and diff/path contents | Owner classifies; preserve prior valid evidence |
| Missing evidence | Required report/input cannot be reopened | PASS label proves claim | Missing locator and available provenance | Reviewer/owner decides bounded reacquisition |
| Permission/authorization absence | Exact effect lacks grant | Tool access is permission | Prompt and owner decision locator | Owner grants or declines; completed read-only evidence remains |
| Unavailable capability | Required local tool/storage is absent | Claim has failed scientifically | Version/path/error and affected check | Environment owner resolves or task is replanned |
| Network/authentication failure | Authorized remote operation failed | Remote ref changed or local work failed | Command/error and local commit identity | Credential/network owner resolves; no automatic retry |
| Validator failure | Maintained lint returns error/warning | Prompt is governable from a filename | Exact input, exit code, output | Prompt author corrects and rereads |
| New scientific/architectural boundary | Evidence requires a new method/design choice | Executor may choose silently | Competing options and source evidence | Scientific/technical owner decides; valid completed stages survive |

## Verify the result

The report names an observed fact, a bounded stop reason, preserved evidence, and the next decision. See [Tutorial 8](../tutorials/08_recover_from_a_stopped_task.md).

## Stop instead of proceeding if...

The failure cannot be classified from available evidence. Do not convert an unknown into success or broaden the task to repair it.

## Generic example

A provenance note is dirty at preflight while the accepted arithmetic commit remains unchanged: preserve its status/diff and stop the new edit.

## What this does not establish

A stop does not automatically invalidate earlier accepted evidence or authorize cleanup.
