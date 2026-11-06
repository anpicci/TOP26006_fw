# Report and evidence contract

[AGENTS.md — Compact reporting and artifacts](../../AGENTS.md#compact-reporting-and-artifacts) defines canonical artifacts, report fields, patch kinds and diff visibility. [Review, evidence and claim integrity — Evidence integrity and anti-self-certification](../../governance/contracts/review_and_evidence.md#evidence-integrity-and-anti-self-certification) governs evidence integrity. A normal prompt has a Markdown report and a patch under the deterministic diagnostics directory for its prompt ID. An orchestrated workflow also has a compact stage ledger under [Orchestration — Objective gates and failure behavior](../../governance/contracts/orchestration.md#objective-gates-and-failure-behavior). Report actual runtime identity as observed or `not_observable`, exact paths, command results, claims versus observations, incomplete stages, branch/HEAD, effects, and caveats.

A report's opening should make the result understandable before the reader
parses dense technical state. For a substantive result, state the concrete
result, its practical or scientific meaning, material limit, and next real
boundary. For quantitative claims, define the relevant object, reference, or
denominator where needed to understand the number. The body still preserves
exact identities, commands, inputs/outputs, validation, formal states,
findings, hashes, and provenance under the authorities above. See
[research-oriented writing](../explanation/research_oriented_writing.md) for
interpretation guidance and [evidence states](evidence_and_task_states.md)
for the distinction between locating, inspecting, and preserving evidence.

Current patch kinds in the live source are `prompt_local`, `cumulative`, `touched_file_cumulative`, and `empty_no_changes`. Do not call a cumulative diff prompt-local. Reports and patches are evidence containers; filenames do not prove acceptance.

A separately tasked independent reviewer may [review returned evidence](../how_to/review_returned_evidence.md) and recommend acceptance, repair, or stop. Same-executor checking is not independent review, and AI review does not by itself constitute human peer review or independent scientific replication. The research coordinator records the bounded task/evidence acceptance decision after the required review for the stated scope. That decision does not authorize new effects or choose scientific method. The responsible scientific lead separately decides [scientific acceptance](../how_to/record_a_result_acceptance.md) of a claim or interpretation; accepting task evidence does not confer it.
