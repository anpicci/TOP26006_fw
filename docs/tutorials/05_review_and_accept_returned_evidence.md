# Tutorial 5: review and accept returned evidence

**Learning goal:** review your own synthetic result, repair a bounded provenance defect, and distinguish a teaching acceptance record from a real owner's decision.

Continue from [Tutorial 4](04_make_a_bounded_analysis_change.md). Reuse your `practice_root` and `analysis="$practice_root/analysis_repository"`. The note exists but is not yet committed. If you opened a new shell, set these variables to **your** scratch paths before running commands.

1. Capture the seed and first result in your repository. Read the note as the executor's claim, inspect its exact change, and commit only that note:

   ```sh
   analysis_seed_head="$(git -C "$analysis" rev-parse HEAD)"
   git -C "$analysis" status --porcelain=v1 -- interpretation.md
   cat "$analysis/interpretation.md"
   git -C "$analysis" add -- interpretation.md
   git -C "$analysis" diff --cached -- interpretation.md
   git -C "$analysis" commit -m 'docs: record first synthetic interpretation'
   first_result_head="$(git -C "$analysis" rev-parse HEAD)"
   git -C "$analysis" diff --name-only "$analysis_seed_head" "$first_result_head"
   ```

   Only `interpretation.md` should differ from the seed. If your Tutorial-4 state differs from that precondition, stop and inspect its provenance before committing.
2. Reopen the calculation and input provenance with the wrapper/interpreter from [Tutorial 4](04_make_a_bounded_analysis_change.md):

   ```sh
   "$wrap" "$python_env" "$analysis/analyze.py"
   csv_sha256="$(sha256sum "$analysis/data/measurements.csv" | cut -d ' ' -f1)"
   git -C "$analysis" show --stat --oneline "$first_result_head"
   ```

   Record the output: five rows, mean `10.060000`, standard error `0.089443`, chi-square `4.300000`, four degrees of freedom. The first note's missing source commit and CSV hash is blocking for the note's provenance, while the arithmetic remains reproducible. Put those distinct findings in the [review report](../../templates/review_report.md).
3. Make the bounded repair in the **scratch** note. Record the first result commit as the source identity; the repair commit cannot cite itself in its own contents.

   ```sh
   printf '\nSource analysis commit: %s\nInput CSV SHA-256: %s\nExecution: local wrapper and configured Python ran analyze.py.\nLimit: synthetic descriptive calculation; no real-data inference.\n' \
     "$first_result_head" "$csv_sha256" >> "$analysis/interpretation.md"
   git -C "$analysis" diff -- interpretation.md
   git -C "$analysis" add -- interpretation.md
   git -C "$analysis" diff --cached -- interpretation.md
   git -C "$analysis" commit -m 'docs: add synthetic result provenance'
   accepted_analysis_head="$(git -C "$analysis" rev-parse HEAD)"
   git -C "$analysis" status --porcelain=v1 -- interpretation.md
   ```

4. In a **simulated teaching owner role**, record acceptance only of the bounded synthetic arithmetic record after checking the repaired note and its source IDs. The variable `accepted_analysis_head` is an observed Git identity, not proof of owner acceptance. A separately tasked reviewer or coordinating Chat may perform adversarial project review. Same-executor simulated review is not independent scientific replication or human peer review; human scientific/owner acceptance remains a separate real decision boundary.

**Verified reference run:** the recorded [scenario](../../examples/research_workflow_lifecycle/observed_scenario.md) used first result `eb40d2703e74350e09e00c459459d706bbc8fa74` and repaired result `c9f7c6b9e090fdc3ae3c29b34171cf3a7cb88ff4`. Your IDs should differ.

**Checkpoint:** your record separates executor claim, direct observations, blocking provenance finding, repaired commit identity, and simulated teaching acceptance scope. Continue to [continuation](06_continue_from_existing_evidence.md).
