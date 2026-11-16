# Playbook by objective

Resolve repository paths from the existing profile/registry. Native relative
paths below are exact entry locators, not shell commands to execute from this
candidate. The native owner maintains the command syntax and full procedure;
read that procedure selectively, then use the
[binding recipe](prepare_bound_command.md) to prepare a task-local command.
Preparation, execution, successful output and acceptance are distinct.

## produce_or_resume_histograms

Input: the authorized production collection/profile, native coverage/plan,
source and data-driven receipts, archive and exact output root.
Owner: TOPEFT `docs/how_to/production.md` and
`docs/how_to/sr_reco_pkl_campaign.md`; entry `analysis/topeft_run2/run_cr.sh`,
with `campaign_manifest.py` owning state/recovery. Output: native source/final
PKL+sidecar and receipt, not just a shell exit. Preserve a verified source when
only downstream work failed. Old schemas, changed archive digest, occupied
outputs, ambiguous writer and insufficient staging capacity follow the native
failure contract. The workbook's [PKL collections](../workbook/artifacts/production_pkls.md)
resolve the input populations; they do not authorize launch, resume or factories.

## prepare_cards_and_packages

Input: qualified PKLs/sidecars with declared channel/variable/systematic and
blinding choices, successful matrix receipts, and fresh destinations.
Owner: TOPEFT `docs/how_to/datacards_and_scalings.md` then
`docs/how_to/datacard_packages.md`. Entries: `analysis/topeft_run2/make_cards.py`,
`make_datacard_matrix_manifest.py`, `run_datacard_matrix_resumable.sh`,
`build_per_era_datacard_package.py`, `build_combined_datacard_package.py`,
`standardize_systematics.py`, and optional `build_fit_input_package.py`.
Output: stage-qualified TXT/ROOT/scalings and ordered native mapping.
Missing receipt coverage, incompatible nominal/sumw2 or nuisance pairing,
changed original-manifest hash or existing destination stops the dependent build.
See [package references](../workbook/artifacts/datacards_and_workspaces.md);
certification checks identity/structure, not scientific acceptance.

## prepare_or_inspect_plots

Input: exact native primary population and plan, scientific selection/blinding,
period, binning and output identity. Owner: TOPEFT `docs/how_to/plotting.md`
and `docs/reference/plotting.md`; entry
`analysis/topeft_run2/run_plotter.sh` → `plot_campaign_manifest.py` → renderer.
Output: resolved command/plan for preparation; for separately authorized real
work, attempt/lifecycle/publication receipts and actual figures.
`--status` uses an existing root; `--observe-scheduler` adds an independent
network/scheduler read requirement. `--dry-run` is preparation, not rendering
or qualification. Neither finalize nor resume is implied by a status observation.
Source selection, existing-root collision and a held scientific handoff are
material failure boundaries. See [plot references](../workbook/artifacts/plots_and_inference.md)
and the worked binding recipe. Do not add arbitrary flags to repair a plan.

## prepare_workspace_or_inference

Input: the exact selected package stage, ordered cards/ROOT/scalings, package-local
fit config, qualified workspace, dataset and scan/other-WC treatment.
Owners: TOPEFT `docs/how_to/datacard_packages.md` for package consumption;
EFTFit `docs/how_to/run_configured_1d.md`, `docs/how_to/campaigns.md` and
`docs/reference/current_contracts.md` for workspace/scan/result contracts.
Entries include `Fitter/python/workspace_build_recipe.py`,
`Fitter/scripts/eftfit_campaign.py`, and configured `EFTFitter.py` APIs as owned
by those native guides. Confirm the selected workspace recipe's actual CLI
before preparing it. Result: receipt-bound workspace/campaign and canonical
member-complete results, then separately qualified interpretation.
A package-name coincidence, missing ROOT member, stale workspace association,
ambiguous job-set identity or unresolved scientific config stops its dependent
operation. Use [known references and gaps](../workbook/artifacts/datacards_and_workspaces.md#workspace_binding)
and [inference qualifications](../workbook/artifacts/plots_and_inference.md#inference_r19).
Never recover fits or choose toy settings from this playbook.

## reuse_framework_procedures

| Goal and inputs | Sole maintained procedure | Recognizable result / limit |
| --- | --- | --- |
| Construct or lint a bounded task with supplied scope and effects | [Manual authoring](../../how_to/write_a_prompt_manually.md), [prompt validation](../../how_to/validate_a_prompt_before_execution.md), optional [prompt-contract skill](../../../.agents/skills/correction-lib-prompt-contract/SKILL.md) | Task/run separation and mechanical lint where applicable; lint does not assess governance completeness |
| Prepare an owner-run production handoff from an already validated plan | [Manual-production-handoff skill](../../../.agents/skills/correction-lib-manual-production-handoff/SKILL.md) | Nonexecuting runbook with exact binding, logging, collision/resume and evidence-return boundary; no production monitoring or retry |
| Materialize an explicitly selected diagnostics copy | [Diagnostics-execution-copy skill](../../../.agents/skills/correction-lib-diagnostics-execution-copy/SKILL.md) | Bounded provenance-rich copy; not permission to execute its contents |
| Review a returned package against a supplied external manifest | [Evidence-package-review skill](../../../.agents/skills/correction-lib-codex-evidence-package-review/SKILL.md), [review guide](../../how_to/review_returned_evidence.md) | Inert, bounded findings/verdict; no execution, fix, patch application or publication |
| Continue a task with accepted evidence | [Reuse prior evidence](../../how_to/reuse_prior_evidence.md), [continuation guide](../../how_to/prepare_a_continuation.md) | Same authorized decision, exact delta and invalidation boundary; no replay of unaffected qualified work |

Read a skill's live instructions only when actually applying it. This table
routes to owners rather than copying their procedures. Ordinary tasks retain
the applicable AGENTS/CPC and native policy, one report/patch and separate
scientific acceptance. Reuse each maintained procedure at its owning source;
keep only the task-specific binding in the report.
