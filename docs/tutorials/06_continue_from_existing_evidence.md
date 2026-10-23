# Tutorial 6: continue from existing evidence

**Learning goal:** prepare a continuation from your repaired analysis state while reusing valid arithmetic.

Continue with `analysis`, `first_result_head`, `accepted_analysis_head`, and `csv_sha256` from [Tutorial 5](05_review_and_accept_returned_evidence.md). If a new shell lost variables, recover your own scratch path and inspect `git -C "$analysis" log --oneline -3`; identify the first-result and repair commits from their contents before resetting the variables.

1. Read live state and the repaired note:

   ```sh
   git -C "$analysis" rev-parse HEAD
   git -C "$analysis" status --porcelain=v1 -- interpretation.md data/measurements.csv analyze.py
   git -C "$analysis" show --format=fuller --stat "$accepted_analysis_head"
   cat "$analysis/interpretation.md"
   sha256sum "$analysis/data/measurements.csv"
   ```

2. Fill the [continuation template](../../templates/continuation_prompt.md) with four explicit entries:
   - **Closure:** the five-row synthetic arithmetic and its assumptions, source `first_result_head`, repaired provenance `accepted_analysis_head`, and **simulated teaching acceptance** scope.
   - **Delta:** the next bounded evidence transfer to a separate methods record; only qualified quantities and provenance may cross.
   - **Invalidation boundary:** CSV, script, independent Gaussian model, source identity, governance, or task-path state changes that defeat reuse.
   - **Checks not to repeat:** the accepted numerical run and already checked arithmetic while that boundary holds.
3. State new evidence needed: fresh Git status/HEAD, the repaired note's source IDs, and later the exact methods-note diff. Do not rerun arithmetic merely because a continuation is being written.

**Checkpoint:** your continuation points to your own source commits and tells a successor what is closed, what is new, and when to stop. The recorded [reference scenario](../../examples/research_workflow_lifecycle/observed_scenario.md) illustrates one run; its IDs are not inputs here. Continue to [sequential coordination](07_coordinate_a_multi_repository_change.md).
