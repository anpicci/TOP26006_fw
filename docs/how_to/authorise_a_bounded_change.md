# Authorise a bounded change

Use this guide when a scientific or methodological correction has evidence but its permitted effect is not yet defined. The human owner decides the purpose and effect boundary.

## Before you start

Have the research question, evidence locator, repository identity, applicable native policy, and proposed result claim. Read [AGENTS.md](../../AGENTS.md) for execution limits and the [bounded change template](../../templates/bounded_change_prompt.md) as an aid.

## Procedure

1. State the purpose and intended scientific/technical effect in one sentence.
2. Name the exact writable repository and paths, fixed/read-only inputs, branch role, allowed local effects, network/environment/storage limits, and validation ceiling. Example: “add only `interpretation.md` in a synthetic scratch analysis repository; read the fixed CSV/script; local calculation and commit allowed; no network.”
3. Define what evidence would support the claim and what would stop work: unexpected input hash, branch mismatch, dirty task path, missing authorization, or a new scientific choice.
4. State who may make the later acceptance decision and which claim it may cover. The authorization permits execution within limits; it does not pre-accept the result.
5. Have the coordinating Chat or another authorized prompt author translate this mandate into a live [CPC.md](../../CPC.md) contract. Reread the completed prompt against the owner's words before dispatch.

## Verify the result

The mandate and prompt agree on repository, effects, exclusions, validation, evidence, and stop conditions. The executor can identify the grant without inferring it from tool availability.

## Stop instead of proceeding if...

Ownership, method choice, native policy, or branch applicability is unresolved. A local commit, test result, or executor report does not authorize another repository, production, publication, or scientific acceptance. See [Tutorial 4](../tutorials/04_make_a_bounded_analysis_change.md).

## Generic example

The owner allows only a synthetic `interpretation.md` note after a reproduced calculation and requests an exact note diff and source identity.

## What this does not establish

Authorization to make that note does not accept its claim or permit a second repository edit.
