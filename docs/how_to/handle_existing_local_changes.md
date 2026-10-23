# Handle existing local changes

Use this guide when task preflight finds local edits. Their provenance matters to the research result and to exact-path commit ownership.

## Before you start

Know the intended task paths and read the [dirty-state policy](../../AGENTS.md). Run read-only Git commands in the exact repository; do not assume every local edit belongs to the new task.

## Procedure

1. Identify staged task-path changes: `git -C "$repo" diff --cached --name-status -- <task-paths>`; inspect with `git -C "$repo" diff --cached -- <task-paths>`.
2. Identify unstaged tracked edits: `git -C "$repo" diff --name-status -- <task-paths>`; inspect their exact diff.
3. Identify conflicts: `git -C "$repo" diff --name-only --diff-filter=U -- <task-paths>`.
4. Identify untracked task-path collisions with `git -C "$repo" status --porcelain=v1 -- <task-paths>` and inspect the exact target path before writing. Classify unrelated state separately without adopting or changing it.
5. Record path, staged/unstaged/conflict/untracked class, evidence, known owner, and whether exact continuation adoption was authorized. For example, ` M interpretation.md` in the path to be edited is a stop until its origin is decided.

## Verify the result

The task has a collision-free writable surface or an explicitly declared, provenance-backed adoption. Reopen task-path status immediately before staging.

## Stop instead of proceeding if...

A relevant change has uncertain owner or mixed task/foreign content, a conflict exists, or an untracked file would be overwritten. Preserve unrelated user state. Do not reset, clean, stash, restore, or broad-stage to make the gate pass. See [Tutorial 8](../tutorials/08_recover_from_a_stopped_task.md).

## Generic example

A new task would edit `interpretation.md`, but status shows ` M interpretation.md`; record the diff and owner before proceeding.

## What this does not establish

A path grant does not adopt pre-existing content or identify its author.
