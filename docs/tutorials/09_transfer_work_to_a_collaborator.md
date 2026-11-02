# Tutorial 9: transfer work to a collaborator

**Learning goal:** give a collaborator enough durable evidence and residual context to continue without reopening valid accepted work.

A handoff can stay inside one repository or span several. Use only the repositories the task actually needs. Start with the [handoff template](../../templates/handoff.md): state the purpose, exact repository identities, artifact locations and what each artifact establishes. Distinguish reviewed/accepted claims and their limits from last-observed state and unresolved work. A last-observed HEAD or clean status must be refreshed when continuation depends on it; it is not a permanent guarantee.

Describe what would invalidate reused evidence and which checks should not be repeated while that boundary holds. Reopen only the invalidated or directly coupled delta, rather than rerunning everything for confidence. Include relevant uncommitted changes as identified evidence, without adopting them or granting permission to change them.

The recipient first locates and reads the evidence, then checks decision-material current identities and local state. They confirm what is established, what is pending, and the next responsible-human decision. A handoff transfers context and evidence; it grants no write permission, repository authority, scientific acceptance or authorization to rerun closed work. Any residual action needs its own applicable authorization. Executor completion, repository-local validation and human acceptance are separate statuses.

For a provider-to-consumer handoff, record both commits and the claim relied upon using [Tutorial 7's transfer map](07_coordinate_a_multi_repository_change.md#follow-the-dependency-serially). Provider checks remain provider-local. The consumer must still verify its selected dependency and affected use and obtain separate acceptance. Preserve valid provider work if consumer work remains pending or fails; there is no global rollback.

**Recipient checkpoint:** without oral context, identify the accepted claim and evidence, last observation to refresh, unresolved delta, invalidation triggers, checks not to repeat, authorization still needed and next human decision. Confirm acquisition and understanding separately from sending the handoff.

## Optional scratch continuation

The exercise below uses your two scratch repositories and intentionally stopped task; they are not prerequisites for an ordinary one-repository handoff.

Continue from [Tutorial 8](08_recover_from_a_stopped_task.md) with your `analysis`, `methods`, `first_result_head`, `accepted_analysis_head`, `methods_evidence_head`, and `csv_sha256`. If variables were lost, recover them from **your** repository logs and notes; never substitute the recorded scenario's IDs.

1. Reopen identities and stopped-state evidence:

   ```sh
   git -C "$analysis" rev-parse HEAD
   git -C "$methods" rev-parse HEAD
   git -C "$analysis" status --porcelain=v1 -- interpretation.md
   git -C "$analysis" diff -- interpretation.md
   cat "$methods/methods_note.md"
   ```

2. Fill the [handoff template](../../templates/handoff.md) in a diagnostics-local file. Preserve the uncommitted diff separately, then write your own identities into the handoff:

   ```sh
   git -C "$analysis" diff -- interpretation.md > "$practice_root/stopped_analysis_note.patch"
   cat > "$practice_root/handoff.md" <<EOF
   # Synthetic handoff
   Scientific owner: human teaching role; real authority not acquired.
   Prompt author: coordinating role. Executor and reviewer: simulated teaching roles.
   First analysis result: $first_result_head
   Repaired analysis result: $accepted_analysis_head
   Methods evidence: $methods_evidence_head
   Input CSV SHA-256: $csv_sha256
   Observed: mean 10.060000; standard error 0.089443; chi-square 4.300000; four degrees of freedom.
   Review: arithmetic reproduced; first note provenance finding repaired.
   Acceptance: simulated teaching acceptance of synthetic arithmetic only.
   Superseded: first note without source commit and input hash.
   Stopped-state evidence: stopped_analysis_note.patch; analysis HEAD $accepted_analysis_head.
   Residual decision: classify ownership of the uncommitted note edit.
   Authorization: this handoff grants no edits, reruns, or acceptance.
   Invalidation: CSV, script, model, source identities, or task-path state drift.
   Checks not to repeat: accepted numerical run while boundary holds.
   Next decision: human owner classifies edit before any continuation.
   Recipient acquisition/comprehension: pending.
   EOF
   ```

   Check the file against the template and add exact evidence locators from your run. The saved file is a teaching record, not an authorization.
3. Record the residual question: who owns the uncommitted edit and how should it be handled? Include expected/observed analysis HEAD, the ` M interpretation.md` status, the exact diff, invalidation boundary, checks not to repeat, and the next owner decision. A real handoff can carry both committed identities and an uncommitted stopped-state diff when that diff is material evidence.
4. Ask a successor to reopen the cited artifacts and confirm understanding. Record “handoff sent” separately from acquisition/comprehension. The handoff itself transfers neither repository permission nor scientific authority.

**Verified reference run:** the [observed scenario](../../examples/research_workflow_lifecycle/observed_scenario.md) illustrates one other set of identities and a simulated review/owner decision; it is not your learner state.

**Checkpoint:** a successor can locate your own accepted teaching record, provenance, superseded wording, stop, and next decision without oral context. Return to the [manual index](../index.md).
