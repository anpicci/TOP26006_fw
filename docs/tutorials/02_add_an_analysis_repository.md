# Tutorial 2: connect an analysis repository

**Learning goal:** follow a research repository from its project identity to a separate local checkout, then inspect a maintained analysis entry point without running the analysis. This lesson uses TOPEFT, an existing TOP-26-006 repository. It does not register a new repository or qualify TOPEFT runtime behavior.

The example installation below uses `/home/alice/work/TOP26006_fw` for the coordination checkout, `/home/alice/work/topeft` for the separate TOPEFT checkout, and `/home/alice/work/topeft-tutorial-output` as a named output location in a printed command. Replace these paths with your own. They are examples, not observed project paths.

1. From the coordination checkout, read the [project repository map](../../governance/repositories.md). Its `topeft` row identifies the analysis repository and says that the local profile resolves `repositories.topeft.path`. The map owns the stable role; it does not prove that a checkout exists or grant permission to run it. The [TOPEFT module](../../governance/modules/topeft.md) adds project branch roles, while TOPEFT's own documentation index at `docs/README.md` and native policy own the technical workflow. Open that repository-relative path in the profile-resolved TOPEFT checkout.

2. Make sure your ignored `.top26006/local_profile.yml` maps `topeft` to the actual separate checkout. For this example, the relevant YAML is:

   ```yaml
   repositories:
     TOP26006_fw:
       path: .
     topeft:
       path: /home/alice/work/topeft
   ```

   Add the `topeft` key only if your profile does not already have it. Resolve the profile from your coordination checkout using the wrapper and prepared interpreter chosen in [Tutorial 1](01_prepare_a_research_project.md):

   ```sh
   checkout=/home/alice/work/TOP26006_fw
   repo=/home/alice/work/topeft
   cd "$checkout"
   "$wrap" "$python_env" tools/resolve_local_profile.py \
     --profile .top26006/local_profile.yml --execution-ready --format yaml
   git -C "$repo" rev-parse --show-toplevel
   git -C "$repo" branch --show-current
   git -C "$repo" rev-parse HEAD
   git -C "$repo" status --short --untracked-files=no
   ```

   **Representative checkpoint:** the resolver's `repositories.topeft.path` and Git's top level both identify `/home/alice/work/topeft`. The branch, commit hash, and status are live values that vary. If the path is absent, belongs to a different Git root, or has unexpected changes, stop and resolve that discrepancy before planning work there. Path agreement alone gives no write or scientific authority.

3. In the profile-resolved TOPEFT checkout, read its analysis workflow tutorial at `docs/tutorials/analysis_workflow.md` and entry-point reference at `docs/reference/entrypoints.md`. For one 2022 signal-region block, the maintained entry point is `analysis/topeft_run2/fullR3_run.sh`. From that directory, this **example command** asks the wrapper to resolve its request and print it:

   ```sh
   cd "$repo/analysis/topeft_run2"
   ./fullR3_run.sh -y 2022 -t tutorial_2022 --sr \
     -p /home/alice/work/topeft-tutorial-output --dry-run
   ```

   The shell script's current source selects three 2022 SR cfg files: `NDSkim_2022_background_samples.cfg`, `NDSkim_2022_data_samples.cfg`, and `NDSkim_2022_mc_signal_samples_sr.cfg`, all under `input_samples/cfgs/`. The `_sr` suffix is used for the signal cfg, not the background cfg. It derives `2022SRs_tutorial_2022`, the `ana` histogram list, and a delegated `run_analysis.py` request. A **source-derived representative excerpt**, not a transcript from this documentation round, is:

   ```text
   OUT_NAME: 2022SRs_tutorial_2022
   Resolved years: 2022
   Resolved CFGS: ../../input_samples/cfgs/NDSkim_2022_background_samples.cfg,../../input_samples/cfgs/NDSkim_2022_data_samples.cfg,../../input_samples/cfgs/NDSkim_2022_mc_signal_samples_sr.cfg
   Resolved region: SR
   Resolved histogram list: ana
   Running the following command:
   python run_analysis.py ... --years 2022 --hist-list ana --skip-cr ... -p /home/alice/work/topeft-tutorial-output
   ```

   The ellipses abbreviate options; inspect the full command your checkout prints before any separate execution decision. `fullR3_run.sh` prints the assembled request and returns at its `--dry-run` check before calling Python. Its output path is a string in that request; this lesson does not create or inspect an analysis artifact. TOPEFT's production how-to at `docs/how_to/production.md` (section “Run one block with `fullR3_run.sh`”) explains the wrapper's scope and why a one-block command has no campaign resume state. Open it in the profile-resolved TOPEFT checkout.

4. Trace the ownership boundary: `fullR3_run.sh` selects cfgs, years, region, histogram family, and output naming; `run_analysis.py` owns active input loading, executor and processor construction, and artifact publication when separately run. The analysis processor at `analysis/topeft_run2/analysis_processor.py` in the profile-resolved TOPEFT checkout owns analysis behavior. A printed request is not a scientific result or a production qualification. Keep TOPEFT commands subject to its native policy and a separately authorized task.

For branch roles, TOPEFT's permanent live development line is `te/datacard_sr_reco`; `run3_test_mmerged_anpicci` is its personal/reference line and `run3_test_mmerged` its integration line. `te/dev-live` is not part of the adopted TOPEFT model. TOPCOFFEA has the distinct canonical `tc/dev-live` development role, with `run3_test_mmerged_anpicci` as personal/reference and `run3_test_mmerged` as integration. Operational creation and migration of `tc/dev-live` remain pending; do not infer that the ref exists from the role. A profile path or current branch name does not replace fresh Git evidence or authorize a mutation. TOPEFT-specific accepted-result convergence rules do not automatically apply to TOPCOFFEA.

**Checkpoint:** you can identify the repository, the actual checkout, and the maintained one-block dry-run chain while keeping execution and acceptance separate. Continue to [Tutorial 3](03_complete_a_first_read_only_task.md) for a self-contained synthetic calculation you can inspect without TOPEFT.
