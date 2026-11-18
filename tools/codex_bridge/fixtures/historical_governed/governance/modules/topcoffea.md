# topcoffea project-governance delta

Applies to TOP-26-006 project work in `topcoffea` selected through
[`../repositories.md`](../repositories.md). Root governance owns generic
lifecycle and permission rules; applicable topcoffea/upstream-native policy
remains independently binding. This module adds constraints and creates no
write, publication, merge, or deletion authorization.

`topcoffea` supplies shared corrections, libraries, object selection, weights,
and utilities. Its default project mutation posture is `read_only`; an exact
round must separately authorize any modification.

## Permanent branch roles

```text
permanent_live_development_branch: tc/dev-live
permanent_personal_reference_branch: run3_test_mmerged_anpicci
permanent_integration_branch: run3_test_mmerged
feature_development_namespace: tc/*
```

`tc/dev-live` is the permanent fork-local TOP-26-006 live development line.
Ordinary applicable TOP-26-006 development continues there after its authorized
creation. `run3_test_mmerged_anpicci` remains the personal/reference branch and
`run3_test_mmerged` remains the integration branch; neither is a development
surface.

The initial `tc/dev-live` transition is created from a freshly resolved
`run3_test_mmerged_anpicci` identity. A historical or previously observed SHA
does not pin the creation source. Do not merge or substitute
`run3_test_mmerged` merely to initialize the permanent live branch.

Other `tc/*` branches are exceptional feature/development branches rather than
the normal path for ordinary project work. Creating one requires the root
owner-authorized exception contract with a concrete isolation need,
relationship to `tc/dev-live`, and retirement condition.

For promotion from `tc/dev-live`, use an exact immutable source cut and
temporary carriers when required by the governing promotion round. Do not
publish a later-moving live HEAD as though it were the same promotion cut.

This module does not import TOPEFT's first-parent convergence contract merely
for symmetry. If a TOPCOFFEA promotion mechanism creates a history-convergence
need, establish the repository-native accepted-result and ancestry contract
from fresh evidence before authorizing that convergence. Until then, do not
invent a TOPEFT-style back-merge requirement.

`run3_test_mmerged_coffeadev` and any other historical or divergent local line
are not reclassified, deleted, merged, or retired by this module. Their
disposition requires separate evidence and authorization if they later become
decision-material.

Promotion carriers and dedicated worktrees are temporary by role, but their
retirement does not authorize deletion automatically.

For prompt construction, encode all four branch-role fields above in every
applicable TOPCOFFEA prompt. Resolve current refs/HEADs freshly when
decision-material. Branch names do not prove current commit identity,
applicability, publication authority, or permission.
