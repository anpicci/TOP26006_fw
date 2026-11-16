# Tutorial 7: coordinate a sequential two-repository change

**Learning goal:** transfer evidence across a genuine repository dependency while keeping each repository's authority, validation, and acceptance separate.

Use this lesson only when the task genuinely crosses two maintained repository boundaries. If one repository is sufficient, stay in one repository. This is an intermediate route after the everyday lifecycle, not a requirement for a newcomer. A second repository may remain read-only when it supplies an interface contract; both repositories need not change.

## Follow the dependency serially

Start with the question you can answer in one repository. Add a second repository only when that answer depends on its maintained result or interface. Call the repository supplying that result the **provider** and the repository using it the **consumer**. These roles belong to this dependency, not permanently to a project.

First identify each repository, its exact commit, relevant local changes, and its own policy and responsible human. State the precise claim to transfer. Attach the minimum evidence supporting it: source and input identities, relevant interface contract, check method and result, limitations, and provider review/acceptance status with its exact scope. A recorded PASS covers only the checks actually performed.

Then continue in the consumer under its own authorization. Reuse accepted provider checks while their sources, inputs, assumptions, and methods remain valid. The consumer still needs evidence that its selected provider revision works at the affected interface with its own configuration and downstream use. Agree the relevant local checks with the consumer's responsible human; provider PASS cannot replace them. Review and accept the consumer result separately. Recording two commits establishes identity, not compatibility or scientific validity.

| Item | Provider side | Consumer side |
| --- | --- | --- |
| Repository identity | Exact repository and commit; relevant local changes | Its own repository and commit; selected provider revision |
| Claim/evidence | State precisely what each artifact supports | State which claim is relied upon and its limits |
| Validation | Provider-local checks and observed results | Consumer-local compatibility and impact checks still required |
| Acceptance | Record responsible human, decision and claim ceiling | Separate responsible-human decision; acceptance does not migrate |
| Permissions | Handoff grants none | Obtain consumer-side authorization for the proposed action |
| Invalidation | Relevant source, input, assumption or method change; missing or contradictory evidence | Consumer configuration, dependency or interface drift may require a fresh local check |
| Repetition | Preserve accepted checks while evidence remains valid | Repeat only invalidated or directly coupled checks |

Provider then consumer is a sufficient normal sequence. If the consumer stops or a compatibility check fails, preserve valid provider evidence and report the unresolved consumer state. Separate histories have no global transaction and imply no automatic rollback. Neither write permission, repository authority, scientific acceptance nor automatic validation crosses with the evidence.

## Dated example: a shared correction interface

Suppose you need to understand what correction evidence to carry from TOPCOFFEA before changing or accepting its use in TOPEFT. The maintained documentation observed locally on **2026-11-02** describes TOPCOFFEA as providing reusable correction mechanisms and packaged shared payload interfaces, while TOPEFT selects their era/tag/payload, working point, enabled variations and analysis application. This is one correction-interface family example, not a choice of calibration or scientific policy.

The observation is bound to these separate local identities:

- Provider TOPCOFFEA: `7363c89a16c8e08632e2eac23040eb09324beb5a`.
- Consumer TOPEFT: `22f1ff174c10eb5cd4900ba08b1943b85e24b8a4`.

Read the native files at those revisions: TOPCOFFEA's `docs/correction_interfaces.md` (mechanism/policy boundary) and `docs/topeft_integration.md` (interface responsibilities and ref selection); TOPEFT's `docs/reference/shared_topcoffea_interfaces.md` (corrections and calibrated objects) and `docs/how_to/corrections_weights_and_systematics.md` (shared-mechanism route). Locate the checkouts through the [native-repository bridge](02_add_an_analysis_repository.md). Operational instructions remain in those native manuals.

Those docs say the consuming workflow selects an exact compatible TOPCOFFEA ref and both commits must be recorded. Similar branch names are not compatibility evidence. These observed commits identify the documentation read; they are **not a qualified compatible pair** or a timeless dependency prescription. No native execution or compatibility check supports this example.

For a future authorized correction change, hand over the exact provider revision, affected interface contract, provider check artifacts and their limits, plus actual review/acceptance status. If checks have not run or acceptance is pending, say so. TOPEFT can reuse still-valid provider evidence, but must verify its own selected dependency, dispatch and affected downstream use under native authority before accepting its result. That consumer check is pending in this reading example. A relevant provider interface or consumer configuration change invalidates the corresponding part of the handoff; simply introducing a second repository does not invalidate unrelated accepted work.

**Checkpoint:** explain why this question needs two authorities, which evidence can be reused, which consumer check remains, and who may authorize and accept that consumer action. Use the [handoff template](../../templates/handoff.md) to record the unresolved boundary.

## Optional documentary practice: prepare an evidence transfer

You are preparing evidence for the person responsible for the methods record. Decide which analysis claim that person can reuse and what they must still establish. Prepare a **personal evidence-transfer draft** using the existing [handoff template](../../templates/handoff.md) as a read-only guide. You need read access to that template and the [observed scenario](../../examples/research_workflow_lifecycle/observed_scenario.md), plus a place for your draft. No previous tutorial execution, scratch repository, shell variables or historical Git objects are required. A saved [Tutorial 6](06_continue_from_existing_evidence.md) draft is optional.

### Select the documented transfer stage

Use the scenario's analysis-to-methods stage: **after provenance repair, at the methods evidence record, before the later intentional stop**. Locate the rows “Review finding”, “Provenance repair HEAD”, and “Methods evidence HEAD”, and read the qualification paragraph below the table. Do not import the later dirty analysis state into this earlier transfer.

Record the scenario and template paths, the version or file hash available from your reading source, and the selected stage in your personal draft. If source version information is unavailable, record that limit rather than inventing it. Historical commits in the scenario identify its separate teaching histories; you need not possess or interrogate them. They do not identify your present checkout.

### Write and justify the transfer

Fill the relevant handoff fields in your own words. Make these selections explicit:

| Entry in your draft | Selection and explanation to produce |
| --- | --- |
| Claim and two roles | Choose the bounded synthetic arithmetic claim the methods record relies on. Explain why analysis supplies evidence and methods receives it for this dependency, and why their responsibilities remain separate. Quote the reported quantities and independent Gaussian assumption with their synthetic limits. |
| Source and input identities | Extract the analysis seed, first bounded note, provenance repair, methods evidence and CSV identifiers from their named scenario rows. Label each stage separately: a repaired note's commit is not proof that its contents cite that same final commit. Identify what the summary actually reports and what underlying contents you have not inspected. |
| Review and acceptance | Explain the initial provenance omission and the reported repair without a repeated numerical run. Attribute bounded task/evidence acceptance of the repaired arithmetic record to the scenario's simulated research coordinator after review; no independent human scientific acceptance or real-data qualification is established. |
| Evidence to reuse | Select the reported arithmetic and repaired provenance record, while keeping source, input, assumption and review limits attached. Explain why unchanged accepted checks need not be replayed simply because methods receives the evidence. |
| Receiving-side checks | Identify what methods must still establish: the actual selected analysis revision, readable full evidence, suitability for its intended use, affected interface/configuration checks where relevant, and its own review and responsible-human acceptance. The historical methods commit alone proves none of these for a new task. |
| Missing information and decision | List unavailable original notes, full command receipts or attachments, actual repository paths/branch/HEAD/status, current permissions and responsible humans. Explain which proposed action each gap prevents. Propose the smallest authorized evidence-acquisition step for a real transfer and name the human decision needed before it can proceed. |

The compact scenario does not supply the full original notes, compatibility results or current repository states. Mark an item unavailable when it is absent; do not reconstruct it as original evidence. Writing this draft changes neither maintained inputs nor a methods repository and grants no permission for the real task it describes. Evidence crosses the boundary; write authority and acceptance do not.

### Reopen, check and continue

Save your draft with its input locators, selected stage, completed entries and unresolved items. To restart, reopen that draft and the named scenario/template. Compare the recorded source version or hash if available; otherwise retain the unresolved identity limit. Resume at the first incomplete entry. A changed source requires reviewing only the affected claim. To enter directly or start afresh, use the same documented stage and a new personal draft; no prior shell or repository state is needed.

**Checkpoint:** compare every entry with the scenario rows and template. Can you explain why two responsibilities matter, which evidence travels, which authority does not, and which checks and human decision remain with the recipient? Have you kept the later stop separate and identified missing originals rather than inventing them? The output is an assessable documentary draft; it demonstrates no executed Git operation or newly accepted consumer result.

## Optional BTV practice: from reference to bound proposal

**Goal:** prepare an evidence-transfer record for the person who will assess a
proposed BTV reference plotting command, without executing it. This practice is
separate from the synthetic scenario above. You can enter here directly: read
the linked tracked pages and keep a personal draft using the
[handoff template](../../templates/handoff.md). No earlier tutorial run, TOPEFT
installation, original diagnostic report or payload access is required.

### Find the reference and its procedure

Start with this request: “Which qualified BTV inputs and maintained plotting
procedure support the existing proposal, and what must a future launcher still
check?” Follow this route, reading only the entries needed for that question:

1. Open the [operational entrance](../operations/index.md), then the workbook's
   [ten BTV finals](../operations/workbook/artifacts/production_pkls.md#btv_reference_ten)
   and [BTV plotting plan](../operations/workbook/artifacts/plots_and_inference.md#btv_plot_plan).
   The primaries are `run2_prod_a`–`run2_prod_e` and `run3_prod_a`–`run3_prod_e`,
   ten final `nonprompt_output` inputs with combined-period views. Linked
   `processor_output` sources describe lineage and have overlapping processes;
   they are not ten independent auxiliaries to add.
2. Follow [source catalogue `pkl_btv`](../operations/source_catalog.md#pkl_btv).
   It identifies the revision-1 plan, its digest and the qualified report.
   These identify the source behind the workbook entry; they do not make local
   originals available in a public clone.
3. Open [prepare or inspect plots](../operations/playbook/index.md#prepare_or_inspect_plots),
   then [prepare a bound command](../operations/playbook/prepare_bound_command.md).
   The playbook locates the procedure and supplies the cross-source binding
   recipe. TOPEFT owns `docs/how_to/plotting.md`, `docs/reference/plotting.md`,
   and `analysis/topeft_run2/run_plotter.sh` → `plot_campaign_manifest.py`.
   Those maintained guides and parser own syntax and lifecycle behavior;
   this lesson retains only this case's binding.

The collection and this lesson are candidate documentation, pending adoption.
Record their reading revision or available file identity in your draft. If
unavailable, say so. The installation snapshot below was checked as text on
**2026-11-16**, against TOPEFT `a5818965b4cf73459370b651f6bb5c97f31aa1d7`.
It is a dated proposal, not a command ready for every clone or a new authorization.

### Separate historical values from future checks

Copy this compact binding into your draft, retaining the source of each value.
“Binding” means assigning concrete paths and settings to the selected procedure.

| Source of value | Historical binding | What the recipient must still establish before a future launch |
| --- | --- | --- |
| Qualified plan | Revision `1`; profile `sr_datacard_run2_run3`; tag `top26006-l13-btv-ref-261105-001-261112-001`; the ten finals above | Exact plan/input/sidecar/receipt identities and scientific applicability for the intended use |
| Original plan identity | `/users/apiccine/work/correction-lib/reports/diagnostics/TOP26006_LANE13_BTV_PLAN_AND_MANUAL_HANDOFF_20261114_R1/btv_reference_plan_revision_1.json`; SHA-256 `2c7f0fc793b067c97fcec7ea81df79c4c83b5cd014d34060913ade895d49fa0e` | Readable retained original with that identity; payload digests remain attested by producer/plan evidence, not calculated in this exercise |
| Qualified historical proposal | Output `/users/apiccine/work/correction-lib/topeft/histos/TOP26006_BTV_SR_RECO_REFERENCE_261105_001_261112_001` | Current destination and ancestor safety/collision state under the native procedure; this lesson has not observed the live root |
| Historical handoff settings | `--dry-run --backend condor --resource-observer cgroup_v2 --hard-limit-bytes 245000000000` | Supported current options, separately authorized mode/effects, environment and applicable storage/allocation conditions; the byte limit is historical, not a global default selected by this lesson |
| Glados installation | Cwd `/users/apiccine/work/correction-lib/topeft`; wrapper `/users/apiccine/work/correction-lib/codex-run.sh`; interpreter `/users/apiccine/work/miniconda3/envs/clib-env/bin/python`; `PYTHONDONTWRITEBYTECODE=1` | Actual preflighted repository, source changes, wrapper/interpreter and permissions at the future time of use |

Here is the complete **unexecuted historical binding**, including cwd and the
wrapper environment. Read it as evidence for your record; do not run it, even
with `--dry-run`:

```bash
cd /users/apiccine/work/correction-lib/topeft
/users/apiccine/work/correction-lib/codex-run.sh env \
  PYTHON_BIN=/users/apiccine/work/miniconda3/envs/clib-env/bin/python \
  PYTHONDONTWRITEBYTECODE=1 \
  ./analysis/topeft_run2/run_plotter.sh \
  --campaign-profile sr_datacard_run2_run3 \
  --campaign-tag top26006-l13-btv-ref-261105-001-261112-001 \
  -o /users/apiccine/work/correction-lib/topeft/histos/TOP26006_BTV_SR_RECO_REFERENCE_261105_001_261112_001 \
  --plan /users/apiccine/work/correction-lib/reports/diagnostics/TOP26006_LANE13_BTV_PLAN_AND_MANUAL_HANDOFF_20261114_R1/btv_reference_plan_revision_1.json \
  --dry-run --backend condor --resource-observer cgroup_v2 \
  --hard-limit-bytes 245000000000
```

The qualified earlier native dry-run and manual handoff are reused evidence;
they did not create this root or new PNGs. Static reading of the maintained
parser confirms these options and an absent-root requirement even for a fresh
dry-run. It does not establish today's collision state or execute that check.
An unsupported option or occupied root limits a future launch: retain this
historical binding and the discrepancy, rather than selecting another root or
suggesting retry, resume or overwrite. Keep `--dry-run`; preparation, execution,
technical success and scientific or visual acceptance remain separate.

### Write, challenge and preserve your record

In your personal draft, state the request, selected reference/source versions,
procedure owner and dated binding. Separate what you read directly in tracked
pages from original evidence merely cited there. List the future checks above
as not performed, with the action each prevents and the responsible human's
next decision. The report of an actual task would retain its consumed versions,
assumptions, concrete proposal and performed/missing checks; this exercise
produces a draft, not another maintained report or a production handoff.

Challenge the proposed reuse with two cases in the same record:

- A request to release the older `reference10` fit-membership handoff encounters
  the [six-target 071 hold](../operations/workbook/artifacts/plots_and_inference.md#reference10).
  The later BTV reference does not resolve that contract. The fixture is not a
  new measurement of actual PKL membership; do not calculate one here.
- Compatible names in package055/BTV059 and workspace R19 do not establish
  [package-to-workspace lineage](../operations/workbook/artifacts/datacards_and_workspaces.md#workspace_binding).
  Require the actual package/card/ROOT/config/workspace receipt for that dependent
  use. Keep the qualified BTV proposal available without inventing the association.

Use the existing [population index](../operations/index.md#choose-by-need-and-population)
and [interpretation lessons](../operations/workbook/knowledge/operational_lessons.md#calibrated_raw_and_display_q)
when another request needs their qualifications. Do not combine pre-fix and BTV
collections, linked sources/finals, SR extensions and tau5j, package stages,
or R19 and Sergio snapshots into a new population for this exercise.

If later work already authorizes collection maintenance, a workbook update can
retain reusable knowledge from a new report with its source, conditions, limits
and precisely superseded use. A new report does not update it automatically or
turn a local observation into a universal result. Keep past consumed versions
in their reports and the playbook's procedure at its native owner's home; no
new approval per entry or scientific authority follows from maintenance. See
[continuation and maintenance](../how_to/prepare_a_continuation.md#keep-reusable-knowledge-within-its-evidence).

**Checkpoint:** reopen your draft and the linked entries. Can another reader
trace request → qualified reference → maintained procedure → concrete proposal,
distinguish historical values from checks not performed, and explain both
countercases? This establishes a reviewable documentary record, not reader
learning, new plots, scientific review or acceptance.

To restart, reopen that draft and compare only its consumed source versions;
revisit the affected entry if one changed, then resume at the first incomplete
part. You need no previous shell state or tutorial output.

**Optional local-source extension:** with separately authorized read access,
locate the original plan/report and native guides/parser through your profile
and the catalogue. Read them as text and record which claims you actually
checked; do not load PKL/ROOT or execute the command. If a locator is inaccessible,
retain its identity and qualify only the dependent claim. That local limit
does not prove global nonexistence. A public clone promises neither ignored
reports, scientific checkouts nor payloads; the tracked-page exercise above
remains complete without them.

Return to the [tutorial learning path](index.md) after either optional practice.
If you are following the complete curriculum, next read the
[advanced gateway](../advanced/index.md) and its criterion for entering the
parallel-work exercises.
