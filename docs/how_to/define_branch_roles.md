# Define branch roles

Use this guide when a research task's source and destination branches need explicit meaning before a prompt can select a branch policy.

## Before you start

Read the live [branch contract](../../AGENTS.md), [branch reference](../reference/branch_policies.md), registry-named module if any, and native repository policy. Know the proposed scientific surface and accepted prior work.

## Procedure

1. Describe the **reference** branch as the comparison source, the **integration** branch as the accepted aggregation surface where applicable, a **personal** branch as a researcher's own working branch when native policy defines one, and a **feature** branch as the bounded development surface. A reference/integration branch is not automatically a development target.
2. Record actual local names separately from those roles. For example, `reference_branch: stable`, `feature_branch: docs/evidence-guide` is a local mapping, not a universal naming rule.
3. Read live state: `git -C "$repo" branch --list`, `git -C "$repo" branch --show-current`, and `git -C "$repo" rev-parse HEAD`. Check relevant ancestry and feature content before calling a branch applicable.
4. Select the literal branch policy from [AGENTS.md section 7](../../AGENTS.md): `continue_existing_branch`, `create_feature_branch_from_reference`, or `read_only_current_branch`. Check module-defined permanent roles before using a generic baseline assumption.

## Verify the result

The task contract names the semantic role, exact observed branch/HEAD, applicable policy, and evidence connecting the branch to the research workstream. A checkout path or remote alias supplies none of these meanings.

## Stop instead of proceeding if...

More than one active feature is applicable, any candidate is ambiguous, or local names conflict with native/module policy. Use [candidate-branch comparison](choose_between_candidate_branches.md); do not infer applicability from similar names or create a parallel branch to avoid reconciliation.

## Generic example

For a methods-guide task, record local `stable` as comparison and `docs/methods-guide` as the active feature only after checking its content.

## What this does not establish

Literal names do not establish role, authority, or current ref identity.
