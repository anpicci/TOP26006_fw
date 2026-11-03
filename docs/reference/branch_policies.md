# Branch policies

[Git lifecycle — Branch policy](../../governance/contracts/git_lifecycle.md#branch-policy) and [CPC.md — Construction](../../CPC.md#construction) govern branch behavior. The current literal policies are:

| Value | Required meaning |
| --- | --- |
| create_feature_branch_from_reference | Create the declared feature branch from a declared reference after applicability checks. |
| continue_existing_branch | Stay on the declared active feature branch. |
| read_only_current_branch | Observe the current branch without movement. |

Roles precede names. A reference or integration branch is not an ordinary development surface. Fresh branch, HEAD, ancestry, and relevant dirty-state evidence determine current state. An uncertain candidate comparison is not evidence that no applicable branch exists. See [branch roles](../how_to/define_branch_roles.md) and [candidate choice](../how_to/choose_between_candidate_branches.md).
