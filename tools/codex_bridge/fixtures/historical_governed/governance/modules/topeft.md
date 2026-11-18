# TOPEFT project-governance delta

Applies to TOP-26-006 project work in `topeft` when the repository is selected
through [`../repositories.md`](../repositories.md). Root `AGENTS.md`, `CPC.md`,
and `CONTRIBUTING.md` retain generic safety, authorization, branch lifecycle,
prompt, and reviewer rules. Applicable TOPEFT-native/upstream policy also
applies. This module cannot grant write or publication permission.

`topeft` owns analysis code, processors, selections, workflow helpers, and
CLIs. Its scientific and technical behavior remains repository-native; this
module does not define implementation or physics semantics.

## Permanent branch roles

```text
permanent_live_development_branch: te/datacard_sr_reco
permanent_personal_reference_branch: run3_test_mmerged_anpicci
permanent_integration_branch: run3_test_mmerged
feature_development_namespace: te/*
```

`te/datacard_sr_reco` is the permanent fork-local TOP-26-006 live development
line. Its historical feature name is retained deliberately; permanent-live
semantics do not require a branch rename. Ordinary applicable TOP-26-006
development continues on this branch under the root reuse-first gate.

Other `te/*` branches remain feature/development branches but are exceptional
rather than the default path for ordinary TOP-26-006 work. Creating an
additional `te/*` branch requires the root owner-authorized exception contract,
including a concrete isolation need and retirement condition. Cumulative or
accepted work on another `te/*` branch does not silently create a second
permanent live line.

`run3_test_mmerged_anpicci` remains the permanent personal/reference interface.
`run3_test_mmerged` remains the permanent integration/upstream reference.
Neither is a development surface. Generic baseline or integrated-state prose
cannot redefine these roles.

For a TOPEFT promotion wave, select an exact committed `source_cut` from
`te/datacard_sr_reco`. PR1/reviewer publication uses a temporary carrier based
on the appropriate personal/reference state rather than publishing the moving
live branch directly. Later commits on `te/datacard_sr_reco` are outside that
wave unless separately selected.

After PR1 acceptance, acquire the exact accepted result. That accepted result,
not the later-moving live HEAD, is the authority for the same wave's downstream
upstream/integration promotion. Reconcile the accepted PR1 result back into
the permanent live development genealogy before selecting the next TOPEFT
`source_cut`.

For that TOPEFT convergence, preserve the pre-convergence live development
HEAD as first-parent history, make the exact accepted PR1 result an ancestor of
the resulting live line, preserve all intended post-cut development, and do not
rebase or rewrite the continuing live-development genealogy. Any semantic
conflict that cannot be resolved from bounded evidence is a new decision
boundary.

Before selecting `source_cut_(N+1)`, require the previous wave's exact accepted
PR1 result to be an ancestor of the current permanent-live HEAD, unless an
explicit owner decision declares that convergence contract inapplicable for
that wave.

Promotion carriers and dedicated worktrees are temporary by role. Define their
retirement condition at creation, but do not infer branch/worktree deletion
authorization from accepted promotion closure.

For prompt construction, encode all four branch-role fields above in every
applicable TOPEFT prompt. Resolve their current refs/HEADs freshly when
decision-material. Branch names do not prove current commit identity,
applicability, publication authority, or permission.
