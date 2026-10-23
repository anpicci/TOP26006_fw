# Report and evidence contract

[AGENTS.md sections 19–21](../../AGENTS.md) define evidence integrity, canonical artifacts, report fields, patch kinds, and diff visibility. A normal prompt has a Markdown report and a patch under the deterministic diagnostics directory for its prompt ID. An orchestrated workflow also has a compact stage ledger. Report actual runtime identity as observed or not_observable, exact paths, command results, claims versus observations, incomplete stages, branch/HEAD, effects, and caveats.

Current patch kinds in the live source are prompt_local, cumulative, touched_file_cumulative, and empty_no_changes. Do not call a cumulative diff prompt-local. Report and patch are evidence containers; their filenames do not prove acceptance. [Review](../how_to/review_returned_evidence.md) and [result acceptance](../how_to/record_a_result_acceptance.md) remain separate human acts.
