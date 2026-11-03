# Evidence and task states

The authority and reporting rules are in [AGENTS.md — Authority and invariants](../../AGENTS.md#authority-and-invariants) and [Compact reporting and artifacts](../../AGENTS.md#compact-reporting-and-artifacts); [Review, evidence and claim integrity — Closure layers](../../governance/contracts/review_and_evidence.md#closure-layers) distinguishes accepted scopes. Keep these distinct:

| State | Meaning |
| --- | --- |
| executor completion | A task actor reports its actions and outputs. |
| observed evidence | Direct inputs, commands, results, identities, and limits. |
| review finding | Independent comparison and blocking/nonblocking classification. |
| owner acceptance | An explicit human decision for a stated claim and scope. |
| continuation | A new bounded task reusing accepted closure while its invalidation boundary holds. |
| stopped task | A failed gate or new decision boundary with evidence preserved and later stages not started. |

An executor success field, test PASS, validator PASS, or commit is not owner acceptance. For orchestrated status literals and failure handling, consult [Orchestration — Objective gates and failure behavior](../../governance/contracts/orchestration.md#objective-gates-and-failure-behavior); this table is conceptual, not a second status schema.
