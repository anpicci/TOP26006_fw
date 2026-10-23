# Tutorial 8: recover from a stopped task

**Learning goal:** detect an unexpected local change, preserve its evidence, and define the next decision without silently altering the checkout.

The [observed scenario](../../examples/research_workflow_lifecycle/observed_scenario.md) records a deliberate stop in the *scratch analysis repository*. Expected and observed HEAD were both `c9f7c6b9e090fdc3ae3c29b34171cf3a7cb88ff4`, but `git status --porcelain=v1` showed ` M interpretation.md`.

1. At task preflight, read HEAD and task-scope status:

   ```sh
   git -C "$analysis" rev-parse HEAD
   git -C "$analysis" status --porcelain=v1
   git -C "$analysis" diff -- interpretation.md
   ```

2. Classify the exact mismatch: a tracked edit to the same note the task would use. Preserve the diff. The observed extra line was “unexpected local edit after accepted commit.”
3. **STOP.** The original continuation did not authorize adopting that edit. Do not reset, clean, stash, overwrite, or automatically retry. Ask the responsible owner to classify the edit's provenance and decide whether a new continuation may adopt it or must use a separate safe copy.
4. Keep the accepted arithmetic and methods evidence intact. The dirty state blocks this *new action*; it does not retroactively erase previously accepted evidence. The next task must state fresh HEAD/status, ownership of the edit, and its invalidation boundary.

**Checkpoint:** you can report detect → classify → preserve evidence → stop → new decision boundary. See [common stops](../how_to/diagnose_common_stops.md), then [handoff](09_transfer_work_to_a_collaborator.md).
