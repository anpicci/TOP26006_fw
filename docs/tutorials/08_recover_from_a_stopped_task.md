# Tutorial 8: recover from a stopped task

**Learning goal:** preserve valid evidence and identify a safe next action after a bounded local task stops.

- **You are:** a researcher assessing an interrupted or stopped local change.
- **You want:** to recover without replaying a process or adopting an unknown edit.
- **You will use:** the maintained scenario's fixed intentional-stop record.
- **You will change:** only a personal recovery assessment.
- **You will not change:** stopped evidence, scratch repositories, tracked project files, data, environment, or remote state.
- **You should finish with:** last observations, preserved closure, unknowns, a safe readback request, and a bounded recovery decision.
- **Prerequisites:** read access to the scenario and a place for notes. Tutorials 4–7, a historical scratch history, and reproducing the stop event are unnecessary.

## Enter at the documented stop

Read the [observed scenario](../../examples/research_workflow_lifecycle/observed_scenario.md), replacing the checkout path below:

```sh
cd /absolute/path/to/TOP26006_fw
sha256sum examples/research_workflow_lifecycle/observed_scenario.md
cat examples/research_workflow_lifecycle/observed_scenario.md
```

Record that file's path/hash as the teaching input. Its fixed stop is already documented: expected and observed analysis HEAD both equal provenance-repair commit `c9f7c6b9e090fdc3ae3c29b34171cf3a7cb88ff4`; status is ` M interpretation.md`; the diff adds `unexpected local edit after accepted commit`; no retry or cleanup was performed.

These are historical observations from a simulated teaching lifecycle. Do not append that line yourself, recreate the stop, or treat the commit as your checkout HEAD. If the scenario is missing or differs materially, record the discrepancy and leave the dependent assessment unresolved.

## Separate what is known from what is missing

Write a recovery assessment with these distinctions:

| Category | Evidence or limit |
| --- | --- |
| Last observed evidence | The scenario's equal expected/observed HEAD, modified-note status, and recorded added line. Equality of HEAD does not make the working tree clean. |
| Known closure | The earlier repaired synthetic arithmetic record had simulated acceptance. The dirty line does not by itself invalidate its reported arithmetic or input identity. |
| Missing or unknown state | Current filesystem/index/process state, ownership of any real edit, complete diff, and whether an interrupted command produced additional effects. The compact scenario does not establish these. |
| Safe next readback | For a real task, inspect the exact authorized repository's HEAD, full task-scope status, staged and unstaged diff, note contents, and existing receipt before selecting a recovery action. |
| Bounded recovery | Preserve the edit and evidence; ask the person with actual authority over the proposed edit/effects to classify the line and authorize an exact continuation. This exercise makes no repair. |

The scenario's separate methods history is outside this local recovery question. No second repository, worktree, parallel agent, scheduler, production job, or distributed service is needed.

## Select the next action without replaying the original task

For the fixed teaching state, the next write is stopped because the task did not authorize adopting the added line. Your assessment should request ownership clarification and an exact decision about that edit. Do not reset, clean, stash, overwrite, commit, or retry simply to obtain clean status.

For your own separately authorized local case, the following are examples of readback commands, **not commands to run against the historical scenario**. Replace the path with the verified scratch repository, and bind any expected HEAD to your own saved evidence first:

```sh
git -C /absolute/path/to/your/analysis_repository rev-parse HEAD
git -C /absolute/path/to/your/analysis_repository status --porcelain=v1
git -C /absolute/path/to/your/analysis_repository diff -- interpretation.md
git -C /absolute/path/to/your/analysis_repository diff --cached -- interpretation.md
cat /absolute/path/to/your/analysis_repository/interpretation.md
```

Save outputs before making a decision. If another path changed, or the original command's outcome is ambiguous, request the additional bounded readback that resolves that state. A missing success message does not prove failure. Readback permits observation, not retry. Retry needs direct proof of safe repetition or exact recovery authorization from the person with actual remit over those effects, with known consequences.

The person with actual edit/effect authorization remit in a later task may authorize a bounded edit or adoption after establishing provenance. A responsible researcher may hold that remit, but the title alone does not grant it; see [responsibilities](../explanation/roles_and_authority.md). Such authorization is distinct from acceptance of the returned task evidence or a scientific claim. That would be a new authorized continuation with its own diff and review. Until then, “preserved, unresolved, next readback identified” is a useful recovery result; it is not task completion or acceptance.

## Restart and preserve closure

Save the assessment, source hash, last completed step, unknowns, and next decision. After interruption, reopen those notes and the source. If unchanged, resume at the missing assessment or readback; do not introduce the dirty line again. If changed, preserve both observations and re-evaluate only the affected boundary.

To repeat this lesson from the beginning, reread the same fixed scenario and start a new personal assessment. No mutation of the stopped state is necessary. The earlier reported numerical run and provenance repair are not repeated while their evidence remains valid; no fresh arithmetic reproduction or real human acceptance is proven here.

Use [common stops](../how_to/diagnose_common_stops.md) for diagnostic guidance, then [continuation](06_continue_from_existing_evidence.md) to prepare an authorized next local task. In the learning path, continue to [Tutorial 9: collaborator handoff](09_transfer_work_to_a_collaborator.md), whose practice has its own entry at the documented stop. An operational handoff remains optional, for when another person must take over. Return to the [tutorial learning path](index.md) for other choices.
