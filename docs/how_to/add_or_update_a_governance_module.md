# Add or update a governance module

Use this guide to propose a module when a registered repository has a demonstrated constraint that common project rules cannot express precisely. No module is created by following this guide alone.

## Before you start

Read [AGENTS.md](../../AGENTS.md), [CPC.md](../../CPC.md), the [registry](../../governance/repositories.md), the native repository policy, and an existing module with a similar role. Identify the affected research paths and consumers.

## Procedure

1. Write a one-sentence trigger: for example, “methods records in repository `sample_methods` require a native review artifact before a project task may cite them.” State why inherited rules are insufficient.
2. Choose the minimum repository-specific scope. Name exact repository ID, applicable paths, branch roles, validation limits, and native repository maintainer or scientific lead, according to the constraint. Put generic lifecycle rules in root governance, not a module.
3. Reuse literal prompt-mode, branch-policy, permission, and validation-ceiling vocabulary from the live sources. State which module facts a prompt author must materialize; do not invent a parallel prompt schema.
4. Check precedence: a module may strengthen common rules but cannot weaken safety, create authorization from the research lead, override native policy, or transfer scientific ownership.
5. Request an exact governance-change authorization. After that separate mutation, inspect the bounded diff, registry `module` locator, local links, and a sample prompt's applicability against the live rule.

## Verify the result

The module applies only to its declared repository/surface, its registry link resolves, and a prompt author can tell which constraint to include. The authoritative fields remain in [CPC.md](../../CPC.md).

## Stop instead of proceeding if...

The native repository maintainer, scientific lead, or policy conflicts with project governance, the constraint is generic, or mutation lacks authorization from the research lead. A proposed module is not a write grant or evidence of scientific acceptance.

## Generic example

A proposed `sample_methods` module limits a native methods-note path to a stated review level; the registry still names its native repository maintainer or scientific lead.

## What this does not establish

A module cannot grant writes or settle a scientific-method choice.
