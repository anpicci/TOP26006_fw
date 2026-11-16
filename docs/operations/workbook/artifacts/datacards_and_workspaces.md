# Datacards, ROOT templates and workspaces

Source IDs resolve in the [catalogue](../../source_catalog.md).
Use the native [package procedure route](../../playbook/index.md#prepare_cards_and_packages).

## cards_055

`cards_055` identifies two stages, `combined` and `standardized`, of the
unblinded 055 package. Each native manifest contains 258 ordered physical
mapping rows with era, `physical_name`, `combined_chN`, order and destination
TXT/ROOT names. The native `cards/` files, scalings and package-local fit config
supply the inputs; this page does not reproduce their membership or physics.
The standardized stage changes nuisance names and matching ROOT keys. Consume
the stage actually qualified for the task rather than pairing a card from one
stage with templates from another.

## cards_btv

`cards_btv` identifies the distinct BTV 059 R2 combined/standardized pair.
The same member count and same declared ordered-card-list digest as 055 do not
establish same card/template bytes or same downstream statistical model.
The standardized manifest digests differ (see catalogue). Package provenance
and native producer receipts must establish any requested PKL→card relationship;
this index does not infer it from the BTV name.

## workspace_binding

The native artifact ladder is completed matrix receipts → per-era package →
combined package → optional standardized/fit-input projection → EFTFit-owned
combined card → workspace → fit result. A package is neither a workspace nor a
fit. At every package stage use its `ordered_card_inputs.txt` and mapping;
do not glob/sort card names or infer order from `chN`.

For an authorized combination, the native guide requires a writable
consumer-owned copy of the package tree as cwd: ordered relative card paths and
card-local ROOT references then resolve together. Preserve the original package.
The guide owns the actual `combineCards.py` command and subsequent workspace
recipe; [the playbook](../../playbook/index.md#prepare_workspace_or_inference)
points to it instead of maintaining a second version.

A valid association records actual selected package identity/stage, ordered
card and ROOT/template/scaling identities, the supplied fit configuration,
combined-card receipt, workspace digest and consumer evidence. It also retains
blinding/stored `data_obs`, effective dataset, WC population, ranges and
normalization. `data_obs` exists for both Asimov and real-data cards and does
not select a fit dataset. The package-local config, not a prose WC table or
old hardcoded range, owns the actual fit input.

The `inference_r19` evidence identifies a workspace at
`/groups/klannon/apiccine/workspaces/eftfit/mva-crossrun-261011-v1/workspace.root`,
attested SHA-256 `7a3c46126c482c00f6b37a1d39f88a8b2ef743714e8d15d9b0418f7e80336092`.
It supports the recorded expected-SM scan, **not an inferred descendant of the
later 055 or BTV packages**. Exact linkage from either newly indexed package
to that existing workspace is unresolved in this acquisition. Wrong or stale
card/ROOT/workspace associations stop only their dependent consumption; keep
other qualified references available and do not regenerate data to fill the gap.
