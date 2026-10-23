# Define branch roles

**Problem:** a task needs a branch choice whose meaning is clear.

Describe roles before names: a **reference or integration branch** is the comparison or accepted aggregation surface; an **active feature branch** carries bounded development; a **read-only current branch** is observed without movement. Live [branch policy](../../AGENTS.md) and any applicable [repository module](../../governance/repositories.md) decide permitted actions. Fresh Git readback supplies branch, HEAD, ancestry, and relevant dirty state.

If one applicable active feature branch exists, continue it unless the owner grants an exact exception. If several or uncertain candidates remain, stop for reconciliation. A local branch spelling, remote alias, or profile path is not a role or a current ref. See [candidate branches](choose_between_candidate_branches.md).
