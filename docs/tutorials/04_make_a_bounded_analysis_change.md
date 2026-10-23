# Tutorial 4: make a bounded analysis change

**Learning goal:** propose one change to a synthetic analysis record, run only its permitted calculation, and obtain evidence that another person can review.

Continue from [Tutorial 3](03_complete_a_first_read_only_task.md). The question is whether the five synthetic measurements support the reported weighted mean under the stated independent Gaussian model. The proposed change is an `interpretation.md` note, not a change to data, method, script, or tests.

1. In a new private practice directory under the coordination checkout's diagnostics area, copy [repeated measurements](../../examples/repeated_measurements/README.md) into an `analysis_repository` and initialize it as a *separate local scratch Git repository*. Set `checkout` to your coordination root, choose an absent `practice_root`, and use a local teaching identity:

   ```sh
   mkdir -m 700 "$practice_root"
   cp -R "$checkout/examples/repeated_measurements" "$practice_root/analysis_repository"
   analysis="$practice_root/analysis_repository"
   git -C "$analysis" init -q -b main
   git -C "$analysis" config user.name 'Synthetic Researcher'
   git -C "$analysis" config user.email 'synthetic@example.invalid'
   git -C "$analysis" add README.md analyze.py data/measurements.csv test_analysis.py
   git -C "$analysis" commit -qm 'test: establish synthetic analysis seed'
   ```

   The [observed scenario](../../examples/research_workflow_lifecycle/observed_scenario.md) records one such run; new scratch commit IDs will differ. Do not copy a real child repository.
2. Assign roles: the researcher owns the question and permitted effects; a prompt author translates them into the [bounded change template](../../templates/bounded_change_prompt.md); an executor runs the authorized task. Permit only `interpretation.md` in the scratch analysis repository. Fix `analyze.py`, `data/measurements.csv`, and `test_analysis.py`. Permit a local calculation and Git readback; no network, environment installation, production, or publication.
3. With `analysis` set to that scratch repository and `wrap`/`python_env` resolved from your [local profile](../reference/local_profile.md), observe the calculation:

   ```sh
   "$wrap" "$python_env" "$analysis/analyze.py"
   git -C "$analysis" status --short
   ```

   The observed output was five measurements, weighted mean `10.060000`, standard error `0.089443`, chi-square `4.300000`, and four degrees of freedom. The note may report those quantities and assumptions; it must say they are synthetic and descriptive.
4. Write `interpretation.md` in the scratch analysis repository. State the five-row result, independent Gaussian assumption, descriptive scope, and absence of real-data interpretation. In the recorded run, the initial note was:

   ```text
   The five synthetic measurements give weighted mean 10.060000 and model-based
   standard error 0.089443 under independent Gaussian uncertainties. The
   chi-square is 4.300000 for four degrees of freedom.
   These observations demonstrate arithmetic reproduction only.
   ```

5. Inspect the sole changed path and the note before considering a local commit:

   ```sh
   git -C "$analysis" status --short
   cat "$analysis/interpretation.md"
   ```

   A new untracked file is not shown by an ordinary Git diff, so read it directly before staging. In the recorded scenario, the new note was the only allowed path; after its first local commit the simulated review role found missing provenance. That finding did not invalidate the reproduced arithmetic.

**Checkpoint:** you can identify the research purpose, fixed inputs, allowed path, minimum environment, appropriate validation, and returned evidence. Local execution and an executor report do not establish scientific acceptance. Continue to [review](05_review_and_accept_returned_evidence.md).
