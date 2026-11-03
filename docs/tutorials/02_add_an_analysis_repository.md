# Tutorial 2: connect an analysis repository

**You are** a physicist with a local TOPEFT checkout, starting from the TOP26006_fw coordination manual. **You want** to understand what one signal-region request would ask the analysis software to do before treating it as an executed analysis.

**You will use** the project repository map, local Git observations, and TOPEFT's own documentation and source. **You will change** only your reading notes and, if needed, your ignored local profile's checkout mapping. **You will not change** TOPEFT or run an analysis, including a native dry-run command. **You should finish with** a dated source observation, its branch and commit, and a clear account of the execution evidence still missing.

**Prerequisites:** the coordination checkout, an existing local TOPEFT checkout, basic Git familiarity, and the prepared wrapper/interpreter and YAML profile from [Tutorial 1](01_prepare_a_research_project.md). No event data or analysis output is needed. This lesson does not register a new repository or qualify its runtime. [Tutorial 3](03_complete_a_first_read_only_task.md) is a self-contained synthetic route and does not require this TOPEFT lesson.

## 1. Turn the physics question into a reading task

Ask: *For one 2022 signal-region (SR) request, where does the native software select the request, where would event processing begin, and what evidence would distinguish that plan from a produced result?*

TOP26006_fw helps frame and bound this question. TOPEFT owns the analysis implementation and native instructions. From the coordination checkout, read the [project repository map](../../governance/repositories.md) and find `topeft`. It identifies the analysis repository and the profile key `repositories.topeft.path`; a map entry alone proves neither a local checkout nor permission to execute it. The [TOPEFT project module](../../governance/modules/topeft.md) supplies applicable project constraints. Obtain current branch roles from that live policy and applicable native policy, then observe Git; this tutorial is not a branch manual.

## 2. Bind the separate checkout to local evidence

The following installation paths are illustrative. Replace them with your own; do not copy paths from the [dated project case study](../examples/top26006_reference_deployment.md) as current setup instructions.

```yaml
repositories:
  TOP26006_fw:
    path: .
  topeft:
    path: /home/alice/work/topeft
```

Check that your ignored `.top26006/local_profile.yml` already maps TOPEFT correctly before adding or changing a key. Resolve it with the prepared wrapper and interpreter from Tutorial 1, then inspect the checkout read-only:

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

Record the date, repository root, branch, full commit hash, and changes affecting the files you inspect. If the path belongs to another Git root, resolve that discrepancy before continuing. Unrelated dirty files need not prevent reading; preserve them. If an evidence file differs from HEAD, retain its exact bytes or diff and describe the observation as modified local content rather than attributing those bytes to the commit. A branch name is context, not proof of scientific validity or authority to change anything.

## 3. Follow one native route without invoking it

Open `docs/README.md` **inside the TOPEFT checkout**, then its analysis workflow tutorial, entrypoint reference, and production how-to. For the dated example below, those paths are `docs/tutorials/analysis_workflow.md` (Route B), `docs/reference/entrypoints.md`, and `docs/how_to/production.md` (“Run one block with `fullR3_run.sh`”). These are native repository paths, not files beneath this coordination manual. Start at the current native index if they move. Reading a production guide does not authorize running its commands.

> **Dated source observation — 2026-11-02, repository TOPEFT.** The local branch was `te/datacard_sr_reco`, HEAD `22f1ff174c10eb5cd4900ba08b1943b85e24b8a4`. The documentation and source files used below matched that commit. Other local edits were outside this evidence set. This is an example to compare with your own checkout, not a required branch or HEAD.

At that revision, inspect `analysis/topeft_run2/fullR3_run.sh`, especially `get_run3_cfgs_for_region_and_year`, `HIST_LIST_ARGS`, `OPTIONS`, and `RUN_CMD`. Consider a request for year **2022**, **SR**, tag **`tutorial_2022`**, with no input or histogram override. The source selects its per-year SR sample bundle and derives the following small request shape:

```text
output name: 2022SRs_tutorial_2022
histogram shorthand: ana
forwarded region option: --skip-cr
```

These are source-derived observations at the dated commit, **not terminal output**. For exact cfg names and a complete current command, return to the native docs and script in your checkout. Do not turn this excerpt into a launch command.

In the same script, find the print of `RUN_CMD`, followed by the `FLAG_DRY_RUN` return before `time "${RUN_CMD[@]}"`. If resolution succeeds, this wrapper's dry-run route prints the resolved years, cfgs, region, histogram list, output path, sample-role policy and assembled `run_analysis.py` command, then returns before calling Python. We have only read this control flow; we have not invoked even that route. The printed heading “Running the following command” would not, by itself, establish execution. This observation concerns this wrapper at this commit; inspect other entrypoints separately before assuming what their dry-run flags do.

Follow the same dated source route one step further: `analysis/topeft_run2/run_analysis.py` constructs `analysis_processor.AnalysisProcessor`, later calls `runner(flist, treename, processor_instance)`, and passes the resulting histograms to `write_histogram_artifact`. `analysis/topeft_run2/analysis_processor.py` contains the processor class and its `process(self, events)` method. These are pointers to the native execution and analysis owners, not a review of their physics or a promise that a request will succeed. The native entrypoint reference describes the source histogram PKL and metadata sidecar that a successful run would publish.

## 4. Write the evidence checkpoint and hand back to native authority

Your note should connect the **question -> exact source -> dated observation -> missing execution evidence -> human interpretation**. Record the inspected paths and relevant source locations alongside your branch, commit and any relevant local changes. State whether you read source or captured an actual command transcript; this lesson produces only a reading note.

Before a later task could claim execution or output, it would need separately authorized execution, the actual command and resolved inputs/options, source and environment provenance, completion/log evidence, and the actual artifact with its matching native metadata and checks. Use TOPEFT's current documentation to determine the exact output and receipt contract for the chosen route; a one-block request must not be assumed to have campaign receipts. No output or receipt was acquired in this lesson. Even a valid artifact still requires scientific checks and interpretation by the responsible scientific lead.

| Question or evidence | What TOP26006_fw teaches | Current technical or decision authority |
| --- | --- | --- |
| How do I frame a bounded AI-assisted research task? | Question, scope and evidence discipline | TOP26006_fw |
| Where is the analysis implementation and manual? | How to locate the separate native repository | TOPEFT |
| What does an entrypoint or configuration do? | A small dated source-reading example | TOPEFT docs/source at the recorded revision, with relevant local changes identified |
| Was analysis executed, and what was produced? | How to distinguish a plan from evidence | Actual native output, completion evidence, receipts where applicable, and provenance |
| Is a later result scientifically acceptable? | How to return evidence for a human decision | Responsible scientific lead |

**Finish when** you can identify your two repositories, the native files supporting your observation, its branch/commit, what the source proves, what remains unexecuted, where to obtain the current exact command, and who accepts a later scientific result. Continue to [Tutorial 3](03_complete_a_first_read_only_task.md) for the independent synthetic exercise.
