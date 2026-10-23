# Tutorial 9: transfer work to a collaborator

**Learning goal:** make a handoff from your own two scratch repositories and the intentionally stopped task.

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
