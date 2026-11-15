# Review returned evidence

Use this guide to assess a reported result before the responsible decision-maker considers acceptance. Executor completion, review, and acceptance are separate.

## Before you start

Read the authorized task, reported result, direct receipts, complete relevant diff, original inputs, and [review template](../../templates/review_report.md). Identify the exact claim and validation limit.

## Procedure

1. Bind the result under review to its exact repository, base and candidate revisions, inputs, and claim. List each reported claim beside its evidence locator.
2. Reopen serialized receipts, diffs, and observations before relying on a reported verdict. Check identity, scope, commands, omitted artifacts, and any uncertain effects against direct state.
3. Reuse earlier review only while the result identity, base, inputs, assumptions, and relevant interfaces remain valid. If one dependency changed, inspect that dependency and directly coupled interactions; preserve unrelated valid findings.
4. For a candidate assembled from frozen worker results, compare the composed bytes with their identified sources to establish provenance. Byte-for-byte agreement does not prove semantic or interface correctness. Review new coordinating edits, rewrites, and interactions in the assembled candidate.
5. When dependent repositories will be used together and compatibility matters, validate the exact set of their candidate revisions at the affected consumer or interface. Do not infer combined correctness from separate repository reviews.
6. Classify findings against the stated claim. Preserve and report valid partial results when another repository or step remains blocked; an incomplete combined result does not erase them.
7. If authorized destructive removal occurred, verify that the portable result and evidence were preserved first. Then read back the final state to confirm that only the exact temporary files, worktrees, or refs created for this task were removed and that permanent or unrelated state remains intact.
8. State which scientific, application, affected-consumer, test, and runtime checks were actually performed. Repository and workflow evidence alone does not certify those claims. Record unchecked boundaries and recommend acceptance, bounded repair, or stop to the decision-maker.

Before or alongside dense identifiers and status, explain what concrete result
was established, why it matters for the practical or scientific question,
which material limit remains, and what decision or boundary follows. Explain
a nonblocking or future-phase limit through its consequence: for example,
an uninspected configuration limits coverage to the inspected configuration.
Keep the exact evidence, classification, and full review depth supporting that
account. The [research writing explanation](../explanation/research_oriented_writing.md)
develops this practice; readable prose does not turn a recommendation into
acceptance.

## Review an inert evidence package

When an explicitly authorized local review uses the maintained
[evidence-package review skill](../../.agents/skills/correction-lib-codex-evidence-package-review/SKILL.md),
read its contract and provide an external reviewer-owned controlling manifest
and the exact carrier. Reviewed contents remain inert. Package-authored booleans
cannot certify authority, review or finding closure. The utility does not
cryptographically authenticate a human reviewer's identity.

A required declared gate must actually resolve and evaluate its cited evidence.
A scalar gate evaluates exactly one locator. Finding closure must cite that
same evaluated operand in a required passing locator gate; supporting locators
for manual, repository, count or patch-set checks cannot close an unrelated
finding. Equality preserves JSON types: `true` differs from `1`, and `false`
from `0`. A hash establishes byte identity, not correctness, containment or
authorization. These checks support bounded review; the human acceptance
decision remains separate. Reading this guide does not invoke the skill or
execute any package contents.

## Verify the result

Each finding cites direct evidence and explains its effect on the bounded claim. A recommendation is distinct from acceptance; the [acceptance guide](record_a_result_acceptance.md) owns the next step.

## Stop instead of proceeding if...

Required identity or evidence cannot be reopened, an effect remains uncertain, or a new scientific or technical choice appears. Preserve supported findings and report the precise boundary.
