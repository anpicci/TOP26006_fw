# Review returned evidence

Use this guide when an executor reports completion and a separate review is needed before the human owner decides acceptance.

## Before you start

Read the owner mandate, exact dispatched prompt, executor report, direct receipt, diff, original inputs, and [review template](../../templates/review_report.md). The reviewer may be a separately tasked coordinating Chat; review identity and limits must be stated.

## Procedure

1. List each executor claim beside its actual evidence locator. Treat the report as a claim until reopened.
2. Check exact input/source identity, branch and task-path status, commands/results, full relevant diff, and omitted artifacts. Reproduce decision-material calculations where feasible under the authorized validation ceiling.
3. Test assumptions, uncertainty, scope, and possible counterexamples. For example, a correct synthetic mean can coexist with a missing CSV hash in the interpretation note.
4. Classify findings as blocking or nonblocking for the *stated* acceptance claim; preserve valid arithmetic while requesting a bounded provenance repair.
5. Record what was not checked and recommend acceptance, repair, or stop to the owner. The [acceptance guide](record_a_result_acceptance.md) owns the next decision.

   A useful finding entry is `claim: <exact statement>; observation: <source/command/locator>; classification: blocking|nonblocking; scope_effect: <why>; recommendation: <accept|repair|stop>`.

## Verify the result

Every finding cites an observed source and explains how it affects the bounded claim. A review recommendation is distinguishable from the human owner's decision.

## Stop instead of proceeding if...

Required evidence is missing, the prompt/mandate cannot be identified, or a new scientific choice appears. Same-executor self-review is not independent review; AI adversarial review is not human peer review or independent scientific replication merely because it challenges a claim.

## Generic example

A reviewer confirms the synthetic calculation but blocks acceptance of its first note until source commit and CSV hash are recorded.

## What this does not establish

A reviewer recommendation is not human owner acceptance or independent scientific replication.
