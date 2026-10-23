# Tutorial 6: continue from existing evidence

**Learning goal:** write a continuation that reuses a valid result and asks only for new evidence needed to close a bounded finding.

The [observed scenario](../../examples/research_workflow_lifecycle/observed_scenario.md) records arithmetic output from the first analysis commit and a provenance repair in a second commit. The calculation was not rerun for that repair. Its acceptance is an illustrative teaching decision, not external scientific review.

1. Fill the [continuation template](../../templates/continuation_prompt.md). **Closure:** five-row arithmetic under independent Gaussian uncertainty was reproduced. **Delta:** add source commit and CSV hash to `interpretation.md`. **New evidence:** inspect the repaired note and its exact diff.
2. State the **invalidation boundary**: if the CSV, script, assumed model, or relevant Git identity changed unexpectedly, the old calculation may no longer support the note; stop and reassess. Fresh Git readback is required even when prior evidence is accepted.
3. List **checks not to repeat** while the boundary holds: the accepted numerical run and its already-reviewed arithmetic. Rerunning everything, assuming old live state is current, or discarding valid arithmetic because the note lacked provenance would obscure the actual delta.
4. Compare the final note with its source identities. In the observed scenario, the simulated owner role accepted the bounded arithmetic record after this repair. That teaching decision did not cover real-data interpretation.

**Checkpoint:** a successor can state what is closed, what changed, what could invalidate closure, and which new evidence is required. Continue to [sequential repository coordination](07_coordinate_a_multi_repository_change.md).
