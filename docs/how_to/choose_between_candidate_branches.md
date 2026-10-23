# Choose between candidate branches

Use this guide when several local branches might carry the same research workstream. The choice protects accepted feature evidence from accidental duplication.

## Before you start

Know the task's semantic surface, accepted prior commits, declared reference branch, and any repository-specific [module](../../governance/repositories.md). Read the live [branch policy](../../AGENTS.md).

## Procedure

1. Enumerate local candidates without network: `git -C "$repo" branch --list`, `git -C "$repo" branch --show-current`, and `git -C "$repo" show-ref --heads`.
2. For each candidate, record `git -C "$repo" rev-parse <candidate>`, `git -C "$repo" merge-base <reference> <candidate>`, and `git -C "$repo" diff --stat <reference>...<candidate>`. Inspect the relevant actual diff where a stat is insufficient.
3. Compare semantic and dependency continuity: would starting elsewhere replay accepted feature work or omit a feature-only dependency? Record positive evidence for applicability or non-applicability. Similar names or shared general topic are insufficient.
4. With exactly one applicable active feature, select `continue_existing_branch`. With none, creation from reference is possible only after the prompt author proves the live policy and owner authorization support it.

## Verify the result

A compact comparison records each candidate HEAD, ancestry, relevant content, native/module role, and conclusion. The prompt names the selected branch and fresh preflight checks.

## Stop instead of proceeding if...

Multiple candidates are applicable or any material candidate remains ambiguous. Request a branch reconciliation decision; do not create a parallel branch because its name looks clearer. This procedure makes no ref changes or remote reads.

## Generic example

Candidate `docs/evidence-guide` contains the accepted manual work; candidate `fix/plot-label` has no dependency or semantic continuity. Record both content comparisons.

## What this does not establish

A branch list alone does not establish applicability or authorize branch creation.
