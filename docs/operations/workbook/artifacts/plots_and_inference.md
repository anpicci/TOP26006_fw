# Plot and inference references

Source IDs resolve in the [catalogue](../../source_catalog.md). A planned figure,
a published PNG and a visually accepted scientific plot have distinct status.
No new figure was opened or rendered for this catalogue.

## reference10

The older 070 R2 `reference10` plan maps 258 package rows to 70 unique fit-plot
targets, 35 per run, masks the two `2los_onZ_1tau` ptz targets and retains 68.
These are planned target identities, not observed current PNG counts.
The later 071 source-path fixture found six membership mismatches: per run,
`3l_onZ_2b/lj0pt` admits 2j–5j instead of 2j–3j;
`3l_onZ_2b/ptz` admits 2j–5j instead of 4j–5j;
`3l_onZ_2b_fwd/lt` admits 1j–4j instead of 2j–4j.
It held the 070 handoff pending an owner fit-member contract. Fitting edge
compatibility alone does not supply variable-specific category membership.
Actual PKL membership was not deserialized in 071. Do not turn that fixture
into a fresh payload claim or release the held command.

The 072 monitoring UX repair changes human display only. It does not repair
that membership contract. Persisted campaign counters, scheduler observations,
worker terminality, storage publication and current content verification remain
distinct. Later production history cannot be reconstructed from the plan;
consult exact campaign receipts for a concrete historical figure request.

## btv_plot_plan

`btv_plot_plan` is the later bound BTV reference plan: ten final inputs,
`sr_datacard_run2_run3`, tag `top26006-l13-btv-ref-261105-001-261112-001`,
revision 1. Its sole proposed root is TOPEFT
`histos/TOP26006_BTV_SR_RECO_REFERENCE_261105_001_261112_001`.
The qualified no-production dry-run and manual handoff did not create that root
or new PNGs. Future existence/collision state must be read back.

The retained consumer uses fitting binning, merged PNG output and one worker;
nominal inclusive dileptonic/semileptonic ttbar stays in card-grouped ttll.
The four exact Run3 `TTto4Q_central` samples are excluded. The maintained
`--sr-display-diagnostics` flag is default-off and display-only; enabling it
does not restore excluded samples or change the retained Data/MC denominator.
These are source/qualified-record semantics, not new visual qualification.
The BTV plan's accepted scope does not automatically inherit or resolve every
reference10-specific owner question.

## tau5j

The `tau5j` top-up campaign is TOPEFT
`histos/TOP26006_tau5j_5j_only_plotting_261031_001`, profile
`sr_crlike_run2_run3`, tag `top26006-l13-tau5j-5j-only-261031-001`.
The 065 report independently checks the selected Run3 attempt_0002 completion
receipt and four canonical members: merged `2los_onZ_1tau` lj0pt, njets, ptz
and merged_njets njets, all fitting PNGs. Exact paths/hashes are receipt-owned,
not a guessed inventory from the variables. This is technical publication and
content evidence, not visual/scientific acceptance. Run2 needs its own content
evidence for a Run2 claim; the campaign-wide published summary is narrower proof.

## inference_r19

`inference_r19` records current expected SM-Asimov, nominal nuisance generation,
profiled other scientific WCs, 26 scientific and ten technical fixed-zero WCs.
The actual config owns their identities/ranges. The campaign/attempt/event and
workspace identity are in the catalogue; the native evidence owns every ROOT.
The current physical-point completeness is 2596/2600, not 2600/2600.
The seven candidate contracts are ctp, ctG, cQq81, cpQM, ctq8, cQl3i, ctlSi;
they are a follow-up shortlist, not the full 26-WC collection.

The maintained curve is q = 2*(raw deltaNLL − minimum available valid physical
grid deltaNLL). q=1 and q=4 are asymptotic 1/2 sigma references (q4 ≈95.45%),
not calibrated coverage or exact95%. The ctq8 q1 crossing bridges missing index56;
cQl3i:35 and ctlSi:28,71 are also missing. ctG:86 retains convergence_unproven.
Do not infer convergence from finite ROOT values or shared display normalization.

The 52 historical Wynona ROOT files support 25 qualified profiled/frozen pairs,
not 26: historical cpt mode is not acquired. Historical workspace digest
`6d142d84d394dffe19f0c03407f4b1f224f6a667f454a82940e479171d2ec4fa`
differs from the current workspace, and historical card/dataset lineage is not
established. Width comparisons are descriptive; no isolated freezing effect,
absolute-NLL nesting, or common dataset is implied.

The five WAITING_SERGIO questions and 1000-toy proposal describe that older
record only. They are superseded for the later implemented policy and acquired
ctG centers below; they must not be presented as the current execution state.
Future toy/fit, observed inference or impacts work retains its own decisions
and effect grants.
See [workspace/inference procedures](../../playbook/index.md#prepare_workspace_or_inference)
and [interpretation lessons](../knowledge/operational_lessons.md#identity_and_scientific_applicability).

## sergio_calibration

The four currently acquired ctG expected/frozen centers are q4neg, q4pos,
q1neg and q1pos, 500 attempted logical identities each. `sergio_calibration`
resolves their exact campaigns, output artifacts and successor scopes.
This is a new-start family: free target starts at its exact injection while
remaining free; conditional fixes it there; other scientific/technical WCs are
zero/frozen. It does not relabel old fixed-start q as new measurements.

| Center / qualified source | Finite q | Negative raw excluded | Selected q>=0 | Scientific fit failures | Operational unresolved |
| --- | ---: | ---: | ---: | ---: | ---: |
| q4neg / bounded recovery cut19 | 491 | 32 | 459 | 9 | 0 |
| q4pos / portable successor R9 | 487 | 21 | 466 | 13 | 0 |
| q1neg / portable successor R9 | 492 | 37 | 455 | 8 | 0 |
| q1pos / portable successor R9 | 494 | 32 | 462 | 6 | 0 |

These are report-attested closed populations, not a new computation. Quantiles
condition on selected qualified finite nonnegative q, with explicit linear
h=(N_selected-1)*p at Gaussian one/two-sigma probabilities. Known negatives
remain raw evidence and are not missing outcomes; finite-N and conditional
missing-outcome envelopes have different meanings. Operational recovery
completion does not erase scientific fit failures or establish interval coverage,
selection-bias bounds or qualified calibrated crossings.

Calibration uses paired same-toy q=2*(NLL_cond-NLL_free). Calibrated interval
consumption compares q_scan_raw-qcrit_raw and retains `likelihood_convention:
q_raw`; it does not subtract a sampled display minimum. Ordinary R19 display
normalization above remains separate. The newer R9 results supersede the
original three-center R6 calibrations for recovered accounting only; old
artifacts and the earlier four-anchor comparison remain historical. Do not
combine old R6 numbers with R9 quantiles into a newly claimed crossing.
