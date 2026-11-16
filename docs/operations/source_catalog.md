# Source catalogue for the operational collection

Acquired 2026-11-16. IDs below resolve to originals, not instructions from a
second mandate. `reports/diagnostics/...` means the resolved TOP26006_fw
workspace, even when the candidate worktree has no copy. Reports attest their
own bounded observations; read their final disposition, not just an initial
checkpoint. Consuming runs retain the material source contents/revisions.

## pkl_pre_fix

`reports/diagnostics/LANE08_PRE_FIX_TEN_PKL_AND_BTV_EVENT_CENSUS_008_R2/`:
`ten_pkl_scientific_worklist.tsv`, `ten_unit_full_sha256.tsv`,
`source_to_np_lineage_v2.tsv`, and
`LANE08_PRE_FIX_TEN_PKL_AND_BTV_EVENT_CENSUS_008_R2_report.md`.
The full-hash table/report qualify the earlier worklist's pending-hash labels;
those labels alone are not a completed byte check. The report completed the
PKL census, but stopped before the raw-event census. Its causal conclusions do
not extend to a global fraction of BTV versus EFT events.

## pkl_btv

`reports/diagnostics/TOP26006_LANE13_BTV_PLAN_AND_MANUAL_HANDOFF_20261114_R1/`:
`btv_reference_plan_revision_1.json`, `input_binding.yaml`, `raw_input_records.json`,
`plan_inventory.yaml` and the same-ID `_report.md`. Plan SHA-256, calculated in
that evidence: `2c7f0fc793b067c97fcec7ea81df79c4c83b5cd014d34060913ade895d49fa0e`.
Per-unit `qualification_source` binds final input and sidecar digests and exact
producer receipt. This is reused evidence: no fresh PKL hashing/deserialization
is claimed by the workbook. `input_binding.yaml` carries source/final roles,
applicability, configuration and normalization provenance. Owner consumption
acceptance is attributed by that report, distinct from executor validation.

## sr_extension

`reports/diagnostics/TOP26006_LANE12_GLOBAL_DRAIN_CHUNKSIZE10000_T50_20261114_R1/`:
same-ID `_report.md` **Final closure — owner-directed evidence-only conclusion**,
`ledger.jsonl`, `handoff.md` and `snapshots/closure_host_native_evidence.json`.
Later Run3-scoped record:
`reports/diagnostics/TOP26006_LANE12_RUN3_REBOOT_RECOVERY_AND_RESUME_GATE_20261115_R4/`,
same-ID `_report.md`, `before_after.json` and `dry_run.json`.
The latter qualifies recovery and future configuration, not completed production.
Native procedure: topeft `docs/how_to/sr_reco_pkl_campaign.md`.

## tau5j

`reports/diagnostics/TOP26006_LANE13_TAU5J_RUN3_FINALIZE_065_R1/`, same-ID
`_report.md`: Run3 completion receipt and exact four canonical PNG members;
the native finalize summary also lists both campaign units as published, but
only the selected Run3 content was independently checked there. Do not reuse
059 R2's earlier Run2 blocked-state verdict as the current campaign verdict.
Run2 content qualification and visual acceptance must be taken from their own
receipts/evidence, not inferred from the Run3 check. The campaign root and
receipt locators are in 065; no new image inspection is claimed here.

## cards_055

TOPEFT `datacard-packages/top26006_unblinded_055/{combined,standardized}/`:
`combined_mapping_manifest.json`, `ordered_card_inputs.txt`,
`package-provenance.json`, package-local `README.md`, `cards/`, `scalings.json`
and `config/TOP_26_006.yml`. The mapping and ordered file own the exact 258
members per package. Declared standardized manifest SHA-256:
`def4032b7139fae71db11bf48234ca1c952c7e6f498bbe303f795cc19cb254a9`.
This locator/metadata observation does not independently certify all payloads.

## cards_btv

TOPEFT `datacard-packages/top26006_btv_059_r2/{combined,standardized}/`, same
native members as `cards_055`. Declared standardized manifest SHA-256:
`a110be1a228c06b9330e41f2a2417baf9d47fb3c62df7a57f64028496ebc3576`.
Its provenance records 258 TXT and 258 ROOT templates; membership comes from
the manifest, not that count. A later local package does not by itself supersede
all uses of 055 or prove consumption by an existing workspace.

## reference10

`reports/diagnostics/top26006_lane13_reference10_continue_s2_to_manual_condor_handoff_070_r2/`:
`reference10_plan_revision_1.json`, `reference10_unique_plot_targets.tsv`,
`reference10_retained_targets.tsv` and uppercase same-ID `_report.md`.
Later limiting source:
`reports/diagnostics/top26006_lane13_reference10_six_target_fitting_membership_closure_071_r1/`,
uppercase same-ID `_report.md`, `six_target_runtime_membership.tsv` and
`all70_source_path_membership.tsv`. These fixtures prove an unresolved
fit-membership interface, not actual reference PKL membership.
`reports/diagnostics/TOP26006_LANE13_POST_REFERENCE10_CONTROLLER_UX_REPAIR_072_R2/`,
same-ID `_report.md`, changes human monitoring only and does not resolve 071.

## btv_plot_plan

Use `pkl_btv`'s plan and report. It supersedes the blocked draft of
`reports/diagnostics/TOP26006_LANE13_BTV_REFERENCE_PLOTTING_PLAN_20261112_R1/`
for plan binding only; that earlier draft is explicitly not a valid native plan.
Source behavior/qualification:
`reports/diagnostics/TOP26006_LANE13_SR_CARD_ALIGNED_TTLL_AND_DIAGNOSTIC_DISPLAY_073_R4/`,
same-ID `_report.md`. Its test limitations remain: source/test evidence is not
production-render or visual acceptance.

## inference_r19

`reports/diagnostics/LANE09_WILKS_CROSSING_EVIDENCE_CONSOLIDATION_022B_R2/`:
same-ID `_report.md`, `candidate_reference_fit_contracts.yml` and
`final_evidence_manifest.yml`. Those originals own all 26 current curves,
missing-point membership, seven candidate contracts, historical comparison
and exact ROOT identities; do not reconstruct them from the shortlist.
Campaign `4939fa13fca441618ef631a9b4f727aa`, attempt
`ed2e6529bdac412d9702deb7722449a6`, event `event_00000043.json`.
This descriptive result is not fresh inference or owner acceptance. Its
pending design state is historical; `sergio_calibration` below owns the later
policy/production references for its scope.

## sergio_calibration

Policy/consumer source:
`reports/diagnostics/TOP26006_LANE09_SERGIO_METHOD_IMPLEMENTATION_AND_CALIBRATED_CONSUMER_REPAIR_20261109_R1/`,
same-ID `_report.md`, plus EFTFit `docs/reference/current_contracts.md`.
The new `sergio_gaussian_linear_v1` family is distinct from old fixed-start/
rounded-probability/ceiling-quantile results. Implementation alone is not a
new-start measurement.

q4neg final source:
`reports/diagnostics/TOP26006_LANE09_BOUNDED_RECOVERY_CONTINUATION_20261112_R1/`,
same-ID `_report.md`, `final_accounting.json` and `calibration_result.json`.
Result SHA-256 `a502d1017af55705b126fda69532aa9aad35a00309a68d4b2a92ec77c6a8498b`;
campaign `e0f54861070441b9a984b130ee8b61c4`, canonical cut19.
This final result supersedes the earlier incomplete q4neg/first-center results
for current accounting and selected calibration, not their historical evidence.

Other three centers: original scope/identities are in
`reports/diagnostics/TOP26006_LANE09_SERGIO_THREE_CENTER_NATIVE_WAVE_20261113_R1/`,
`input_references.json`, `center_results.json`, `four_anchor_comparison.json`
and same-ID `_report.md`. Current successor calibrations are in
`reports/diagnostics/TOP26006_LANE09_GLADOS_PORTABLE_THREE_CENTER_RECOVERY_20261115_R1_rerun_001/`,
`final_readback.json` and `TOP26006_LANE09_GLADOS_PORTABLE_THREE_CENTER_RECOVERY_20261115_R1_report.md`.
The report gives exact `/groups/.../execution/<successor>/calibration_result.json`
locators and byte digests. The original root-level R6 calibrations are retained;
they are not aliases for the successor R9 artifacts.

| Center | Campaign | Current successor | Attested result SHA-256 |
| --- | --- | --- | --- |
| q4pos | `0e2880e98ad04533b66ed01d091e29fa` | `0fe01ae5bae5861ae2cbc0bbe6079fd2` | `e6baec96ffac52240e2962ce0ed62fba8974615719ef69c0016a1b4622b0244b` |
| q1neg | `4afd3a317a464adba89e51b683676e5f` | `c54b832caa1eabd134a0e70a37314f65` | `335fba40d6fe391b1b80b4781e26690119167da67fb0b6106660a1be3d25ad64` |
| q1pos | `9b395fb5441d4e038d0370b5f2aa8b0d` | `81e363ae3200bccbbdfbcd5db808b8ca` | `a99eb74d82484be8390742edbf60b294503511d3550438e647ddd7fe62def892` |

These identities bind scientific JSON results, not a digest of a directory or
reserialization. No fit, ROOT recalculation or quantile computation is needed
to locate them. Their selected-sample claim limits remain in the originals.

## native_packages

TOPEFT `docs/how_to/datacard_packages.md`,
`docs/how_to/datacards_and_scalings.md`, `docs/reference/datacards_and_scalings.md`.
EFTFit `docs/how_to/run_configured_1d.md`, `docs/how_to/campaigns.md`,
`docs/reference/current_contracts.md`, with the actual supplied package-local
fit config. Documentation does not choose its WC ranges. A convenient
`EFTFit/Fitter/config/TOP_26_006.yml` locator was absent in this installation;
use the retained package binding, not a guessed replacement.

## Native software versions observed

| Repository | Acquired HEAD | Material source ownership |
| --- | --- | --- |
| topeft | `a5818965b4cf73459370b651f6bb5c97f31aa1d7` | production, sidecars, native packaging and plotting guides/parsers |
| topcoffea | `bb1ffb2c6f459ca6f2dd77ed5585a4643643e9a0` | shared HistEFT algebra/interfaces; `docs/eft_interfaces.md` |
| EFTFit | `d80a1185b24dbf0522ca1b7b6e457e3b140c5a03` | workspace/inference/result consumer contracts |

Local foreign changes exist in TOPEFT and EFTFit; these HEADs are provenance,
not an assertion of clean runtime implementations or authority to execute them.
Material sources used here were separately retained in the implementation
report evidence. A future run checks its actual consumed paths and dirty state.
