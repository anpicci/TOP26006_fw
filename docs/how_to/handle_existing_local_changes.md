# Handle existing local changes

**Problem:** preflight finds edits or untracked paths.

Record exact task-scope staged, unstaged, conflict, and colliding untracked state under the [dirty-worktree policy](../../AGENTS.md). Identify who owns each change and whether the prompt explicitly adopts it. Preserve unrelated user state. A relevant unknown edit, as in [Tutorial 8](../tutorials/08_recover_from_a_stopped_task.md), is a stop until its owner decides a safe continuation.

Do not reset, clean, stash, overwrite, or stage broad paths to make a check pass. Repository-path permission does not make pre-existing content task-owned. If no collision exists, unrelated untracked files can remain untouched under the applicable policy.
