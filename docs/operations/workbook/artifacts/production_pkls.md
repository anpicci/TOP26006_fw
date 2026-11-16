# Production PKL collections

Resolve source IDs in the [source catalogue](../../source_catalog.md).
Scientific payloads remain native. The unit sets below name distinct
collections; repeated snapshots of a unit are not additive populations.

## pre_fix_ten

Purpose: reproduce the pre-fix reference and understand its card/scaling or
plot descendants, with the original scientific qualifications. Exact source,
`nonprompt` final, sidecar, CFG and full-hash bindings are in `pkl_pre_fix`.

| Run | Exact unit membership |
| --- | --- |
| Run2 | `run2_block1`, `run2_block2`, `run2_block3`, `run2_block4`, `run2_block5` |
| Run3 | `run3_2l_mixed`, `run3_3l_m_offZ`, `run3_3l_p_offZ`, `run3_3l_onZ_tau`, `run3_3l_fwd` |

Each unit has a source→final relationship; ten finals plus their ten sources
are not twenty independent final inputs. The census report's negative
quadratic terms are not counts of BTV events. For its actual normalization,
selection, coefficient/WC order, sumw2 and lineage, consume the native
sidecars/configuration and qualified report, not a table copied here.
These pre-fix references remain useful for historical comparisons. BTV
references are a separate collection, not an automatic replacement for every
historical comparison or fit.

## btv_reference_ten

Purpose: locate the accepted BTV reference population for the current plotting
plan and native downstream preparation. `pkl_btv`'s revision-1 plan is the sole
selection inventory; `input_binding.yaml` supplies the source/final relationship
and per-family applicability. Membership is exactly:

| Run | Exact final-input unit membership |
| --- | --- |
| Run2 | `run2_prod_a`, `run2_prod_b`, `run2_prod_c`, `run2_prod_d`, `run2_prod_e` |
| Run3 | `run3_prod_a`, `run3_prod_b`, `run3_prod_c`, `run3_prod_d`, `run3_prod_e` |

Plan `units[].input_path` selects `nonprompt_output` primaries with combined
period view, not the linked `processor_output` sources. Final and source process
populations overlap; the linked sources also request data-driven products.
They fail the product-disabled/disjoint auxiliary contract and must not be
summed as independent auxiliaries. The source is valuable lineage evidence.

Identity is `qualification_source.input_sha256` plus the bound sidecar/receipt,
not `_np` or a path spelling. Those hashes are attested by reused producer/plan
evidence, not freshly computed on payloads by this workbook. Run2-e's final
receipt is present in the later plan evidence; do not inherit the earlier
missing-receipt gap. Native declarations specify categories and families; do
not create a category×variable Cartesian population.

For a scientific use, check the intended selection, weight/normalization,
nominal/EFT/sumw2 contents and applicability against that exact producer contract.
Same bytes with an incompatible selection or denominator do not establish
scientific applicability. The [binding recipe](../../playbook/prepare_bound_command.md)
keeps the input collection distinct from a downstream plotting plan.

## sr_extensions

Purpose: resume the existing approved SR CR-like extension coverage through its
native engine, or locate completed products, without confusing it with the BTV
production matrix. `sr_extension` records the exact existing campaigns.
Per run the twelve unit suffixes are `a_1`, `a_2`, `a_3`, `a_4`, `b_1`, `b_2`,
`c_1`, `c_2`, `d_1`, `d_2`, `e_1`, `e_2`, prefixed by `run2_sr_ext_` or
`run3_sr_ext_`. Native `sr_reco_default_plan.json` owns the scientific coverage.

Dated evidence: the global drain's final closure has Run2 `a_1`, `a_2`, `a_3`
completed and nine unattempted. Its initial `in_progress` text is historical.
The later Run3 R4 record reconciles original `a_1` as interrupted/failed,
with DD blocked and eleven units unattempted; it qualifies a future
10000/T50 configuration without launching it. It does not establish current
live completion. No new successful PKL is inferred from a dry-run command.
Resolve actual durable paths/receipts from native state. Source and data-driven
stages have separate identities; valid source work can survive downstream failure.

## top_ups

Tau5j is a separate five-jet-only input/plot population identified by `tau5j`,
with units `tau5j_run2` and `tau5j_run3`. Its Run3 selected finalization and
content check are distinct from a new producer campaign. SR extensions also
add histogram coverage for their declared use; they are not replacements for
all production inputs. Neither is silently summed with the BTV or pre-fix ten.
A new top-up belongs here only when a concrete qualified source establishes
its membership, overlap and use. This collection makes no complete-history claim.

Procedure ownership: TOPEFT `docs/how_to/production.md`,
`docs/how_to/sr_reco_pkl_campaign.md` and `docs/reference/histogram_artifacts.md`;
shared algebra remains topcoffea `docs/eft_interfaces.md`. See the
[production recipe route](../../playbook/index.md#produce_or_resume_histograms).
