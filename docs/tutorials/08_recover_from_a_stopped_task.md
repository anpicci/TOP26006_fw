# Tutorial 8: recover from a stopped task

**Learning goal:** create and diagnose an intentional dirty-state stop in your own scratch analysis repository.

Continue after [Tutorial 7](07_coordinate_a_multi_repository_change.md). Keep `analysis`, `accepted_analysis_head`, and `methods_evidence_head` from your run. Do not edit the coordination checkout or the methods repository.

1. Establish the expected state before the next hypothetical task:

   ```sh
   expected_analysis_head="$accepted_analysis_head"
   observed_analysis_head="$(git -C "$analysis" rev-parse HEAD)"
   git -C "$analysis" status --porcelain=v1 -- interpretation.md
   test "$observed_analysis_head" = "$expected_analysis_head"
   ```

2. Deliberately introduce one **uncommitted** edit in your own scratch note, then read it back:

   ```sh
   printf '%s\n' 'unexpected local edit after accepted commit' >> "$analysis/interpretation.md"
   observed_analysis_head="$(git -C "$analysis" rev-parse HEAD)"
   git -C "$analysis" status --porcelain=v1 -- interpretation.md
   git -C "$analysis" diff -- interpretation.md
   ```

3. Classify the evidence: expected and observed HEAD agree, while the task path has ` M interpretation.md`. The next task did not authorize adopting that line. Record the exact diff and **STOP**. Do not reset, clean, stash, overwrite, commit, or retry merely to make Tutorial 9 pass.
4. Preserve the accepted synthetic arithmetic and methods record. The dirty state blocks the proposed next action; it does not retroactively erase prior evidence. The responsible owner must classify this edit's provenance and decide a new continuation.

**Checkpoint:** you can report expected HEAD, observed HEAD, status, diff, preserved evidence, and next decision. See [common stops](../how_to/diagnose_common_stops.md), then [handoff](09_transfer_work_to_a_collaborator.md).
