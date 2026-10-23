# Tutorial 7: coordinate a sequential two-repository change

**Learning goal:** carry qualified analysis evidence into a separate methods record without merging the two histories.

Continue from [Tutorial 6](06_continue_from_existing_evidence.md) with your `analysis`, `accepted_analysis_head`, `csv_sha256`, and `practice_root`. The [lifecycle fixture](../../examples/research_workflow_lifecycle/README.md) provides a methods seed. Both repositories here are diagnostics-local teaching copies, not real governed project repositories.

1. Verify the source before transfer:

   ```sh
   test "$(git -C "$analysis" rev-parse HEAD)" = "$accepted_analysis_head"
   test "$(sha256sum "$analysis/data/measurements.csv" | cut -d ' ' -f1)" = "$csv_sha256"
   git -C "$analysis" status --porcelain=v1 -- interpretation.md data/measurements.csv analyze.py
   cat "$analysis/interpretation.md"
   ```

   If a test fails or task paths are dirty, stop. The bounded evidence object is the calculation, input hash, source commit, repaired note, review finding, and **simulated teaching acceptance** of synthetic arithmetic.
2. Create your own separate methods repository only after the analysis record is qualified:

   ```sh
   cp -R "$checkout/examples/research_workflow_lifecycle/methods_seed" "$practice_root/methods_repository"
   methods="$practice_root/methods_repository"
   git -C "$methods" init -q -b main
   git -C "$methods" config user.name 'Synthetic Researcher'
   git -C "$methods" config user.email 'synthetic@example.invalid'
   git -C "$methods" add -- README.md
   git -C "$methods" commit -m 'docs: establish synthetic methods seed'
   ```

3. Under this teaching authorization, write only `methods_note.md`. Carry the qualified quantities and their limits; use your own source identity:

   ```sh
   cat > "$methods/methods_note.md" <<EOF
   # Synthetic methods evidence
   Analysis source commit: $accepted_analysis_head
   Input CSV SHA-256: $csv_sha256
   Observed local-wrapper result: five rows; weighted mean 10.060000;
   standard error 0.089443; chi-square 4.300000; four degrees of freedom.
   Assumption: independent Gaussian uncertainties and one common mean.
   Review: bounded provenance finding repaired in the analysis note.
   Acceptance: simulated teaching owner acceptance of synthetic arithmetic only.
   Limit: no real-data method, interpretation, production, or publication claim.
   EOF
   git -C "$methods" status --porcelain=v1
   git -C "$methods" add -- methods_note.md
   git -C "$methods" diff --cached -- methods_note.md
   git -C "$methods" commit -m 'docs: record qualified synthetic methods evidence'
   methods_evidence_head="$(git -C "$methods" rev-parse HEAD)"
   ```

4. Check `git -C "$methods" status --porcelain=v1` and `git -C "$analysis" rev-parse HEAD`. The methods commit must cite `accepted_analysis_head` while the analysis repository stays at its own head. Neither commit authorizes edits in the other repository.

**Verified reference run:** the [observed scenario](../../examples/research_workflow_lifecycle/observed_scenario.md) records different analysis and methods commit IDs for one prior run.

**Checkpoint:** your methods note cites your own analysis source and its qualified evidence. Continue to [the stopped task](08_recover_from_a_stopped_task.md).
