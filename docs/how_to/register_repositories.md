# Register a repository identity

Use this guide to **propose** a stable identity for a research repository that has a distinct scientific or technical owner. Drafting a row does not authorize a registry mutation.

## Before you start

Identify its native policy, owner, consumers, and whether it is an active repository, dependency, or pinned evidence. Read the [typed registry](../../governance/repositories.md), an adjacent row of the same class, and [AGENTS.md](../../AGENTS.md) repository boundaries.

## Procedure

1. Choose a durable `repository_id` independent of the checkout directory name. Confirm that no existing row already represents the same repository.
2. Choose the existing registry class and project role that describe how evidence flows. State the native scientific/technical authority and its upstream policy; project governance does not replace them.
3. Choose `repositories.<repository_id>.path` as the local-profile key. A user maps that key to a checkout path in their ignored profile; do not write a personal path into the registry.
4. Decide whether root rules suffice (`module: inherited`) or a bounded repository-specific [module](add_or_update_a_governance_module.md) is needed. Explain the concrete constraint, not merely a preference for another file.
5. Present a proposed row for review in the live table's eight-column order, for example: `sample_methods | PROJECT_IMPLEMENTATION_REPOSITORY | repositories.sample_methods.path — local path | Live resolution | read-only unless exact task grant | native methods owner | inherited | consumes qualified analysis evidence`. Match the registry's precise column meanings and vocabulary before an authorized edit.
6. Only after an owner-authorized governance task, inspect the exact registry diff, reread links/module path and profile-key consistency, and validate the resulting row against native policy.

## Verify the result

The reviewed row retains the same ID across checkout renames, names its owner and consumers, and has an intentional module decision. A later local-profile resolution and `git -C "$repo" rev-parse --show-toplevel` establish local installation state separately.

## Stop instead of proceeding if...

Ownership, class, native policy, or authorization is unclear, or the proposed ID duplicates an existing role. Do not register the [Tutorial 2](../tutorials/02_add_an_analysis_repository.md) scratch repository as a real project repository. A row cannot grant writes, scientific acceptance, or remote access.

## Generic example

Propose `sample_methods` as a native-owned methods repository with profile key `repositories.sample_methods.path` and an explicit evidence consumer.

## What this does not establish

A draft registry row does not create a checkout, grant writes, or confer scientific authority.
