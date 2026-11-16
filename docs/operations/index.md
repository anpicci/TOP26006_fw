# Operational workbook and playbook

Use this entrance when a task needs an existing scientific reference, a recurring
procedure, or an evidenced operational lesson. Read the relevant row and follow
its source; the whole collection is not required reading for every task.
This candidate collection is inactive until separately adopted.

The **workbook** holds references in `workbook/artifacts/` and justified lessons
in `workbook/knowledge/`. The **playbook** routes goals to maintained procedures
and supplies the missing cross-source binding recipe. The **report** records
one task/run attempt and its evidence. A **skill** packages an optional maintained
capability. These objects have separate responsibilities; none grants effects.

## Choose by need and population

This is the membership of the initial operational collection, as acquired on
2026-11-16. A row identifies a collection rather than another inventory of its
members. Native manifests remain the exact member authority. See the
[source catalogue](source_catalog.md) for resolvable originals and qualifications.

| Need / collection | Owning source and consumer | Workbook entry / recipe | Coverage or unresolved boundary |
| --- | --- | --- | --- |
| Pre-fix ten production source/final pairs | `pkl_pre_fix`; histogram, card and comparison consumers | [Production PKLs](workbook/artifacts/production_pkls.md#pre_fix_ten); [production route](playbook/index.md#produce_or_resume_histograms) | All ten unit identities and source→final relationship; no renewed payload or event-level qualification |
| Ten final BTV reference inputs | `pkl_btv`; plotting and card consumers | [BTV collection](workbook/artifacts/production_pkls.md#btv_reference_ten) | Five Run2 + five Run3 finals; source pairs are lineage, not extra independent inputs |
| Current SR extension campaigns | `sr_extension`; source/data-driven producer and later plots | [SR extensions](workbook/artifacts/production_pkls.md#sr_extensions) | Twelve units per run; Run2 partial success, Run3 recovery/configuration evidence; future completion requires readback |
| Tau5j top-up and its plots | `tau5j`; native plot campaign consumer | [Top-ups](workbook/artifacts/production_pkls.md#top_ups), [plots](workbook/artifacts/plots_and_inference.md#tau5j) | Separate population; not silently added to either ten-input collection |
| Unblinded 055 cards and ROOT templates | `cards_055`; ordered package intake | [Cards and workspaces](workbook/artifacts/datacards_and_workspaces.md#cards_055) | Combined and standardized packages, native ordered membership |
| BTV 059 R2 cards and ROOT templates | `cards_btv`; ordered package intake | [BTV cards](workbook/artifacts/datacards_and_workspaces.md#cards_btv) | Combined and standardized packages, distinct identity; downstream workspace consumption not established here |
| Reference10 fit-distribution plotting | `reference10`; native plotting controller | [Reference10](workbook/artifacts/plots_and_inference.md#reference10) | 070 plan and later 071 hold distinguished; 072 UX is not scientific repair |
| BTV reference plotting | `btv_plot_plan`; native plotting controller | [BTV plan](workbook/artifacts/plots_and_inference.md#btv_plot_plan) | Validated plan/manual handoff; new figures and their acceptance unobserved |
| Current expected 1D inference and historical comparison | `inference_r19`; EFTFit result consumers | [Inference](workbook/artifacts/plots_and_inference.md#inference_r19) | 26 curves with missing-point/historical-context limits; old toy questions belong to that R19 snapshot, with later [Sergio results](workbook/artifacts/plots_and_inference.md#sergio_calibration) below |
| Current Sergio toy calibration and recoveries | `sergio_calibration`; raw calibrated consumers | [Sergio centers](workbook/artifacts/plots_and_inference.md#sergio_calibration) | Four exact ctG center populations and current successor artifacts; old policy and old R6 results remain distinct |
| Package→combined card→workspace association | `native_packages`, `inference_r19`; EFTFit/Combine | [Boundary and gaps](workbook/artifacts/datacards_and_workspaces.md#workspace_binding) | Requires actual receipt; package or shared filename does not prove a workspace descendant |
| Recurring commands and diagnostics | Native how-tos and existing framework skills | [Goal-oriented playbook](playbook/index.md), [binding recipe](playbook/prepare_bound_command.md) | Procedures linked once; preparation is not execution or a production handoff |
| Reuse after interruption, identity/selection and lifecycle lessons | Qualified records and native contracts | [Operational lessons](workbook/knowledge/operational_lessons.md) | Conditions and counterexamples accompany each indication |

## Use and maintain the collection

Resolve repository IDs and `workspace_root` through the task's preflighted YAML
profile and registry. Relative diagnostic locators below start at that resolved
coordination root; native paths start at their repository root. They are local
locators, not promises that ignored reports or scientific repositories ship with
a public checkout. If access fails, record the failing locator and local limit;
absence here does not prove global nonexistence or prohibit separately authorized
ordinary work.

Bind object identity separately from path, then selection/normalization and
qualification for the requested use. Follow [the binding recipe](playbook/prepare_bound_command.md)
before preparing a command. Preserve the entry revision and original source
revision/retained contents materially consumed in the run report. A Git revision
of this collection identifies its prose, not the payload it describes.

To practise this route using tracked pages alone, prepare the
[dated BTV evidence-transfer record in Tutorial 7](../tutorials/07_coordinate_a_multi_repository_change.md#optional-btv-practice-from-reference-to-bound-proposal).
It follows a qualified reference through its procedure owner to a concrete
unexecuted proposal; local originals are an optional read-only extension.

Update a reference or lesson in ordinary authorized work when new evidence changes
its applicable scope. State what it supersedes and for which use; preserve dated
historical qualifications. Do not promote the newest filename or duplicate a
native manifest. Framework maintainers own navigation; native maintainers and
scientific leads retain technical/scientific ownership and acceptance. No new
approval per card is introduced; each task's existing scope still governs edits.

For example, the BTV report retains the consumed revision-1 plan, assumptions,
proposed command and checks performed or missing. A later report does not itself
update this workbook. If subsequent authorized maintenance has new evidence,
cite its source and conditions in the relevant reference or lesson and name the
specific use it supersedes. A receipt for a BTV figure would not resolve the
separate reference10 hold or prove a package-to-workspace association. Keep the
earlier plan-only observation dated and preserve the versions consumed by past
reports. The playbook still links to the one native plotting procedure.
