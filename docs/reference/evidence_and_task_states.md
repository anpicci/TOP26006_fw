# Evidence and task states

The authority and reporting rules are in [AGENTS.md — Authority and invariants](../../AGENTS.md#authority-and-invariants) and [Compact reporting and artifacts](../../AGENTS.md#compact-reporting-and-artifacts); [Review, evidence and claim integrity — Closure layers](../../governance/contracts/review_and_evidence.md#closure-layers) distinguishes accepted scopes. Keep these distinct:

| State | Meaning |
| --- | --- |
| executor completion | A task actor reports its actions and outputs. |
| observed evidence | Direct inputs, commands, results, identities, and limits. |
| review finding | Independent comparison and blocking/nonblocking classification. |
| task/evidence acceptance | The research coordinator explicitly records acceptance of returned evidence or a bounded task layer after the required review, for a stated scope; this neither authorizes new effects nor chooses scientific method. |
| scientific acceptance | The responsible scientific lead decides whether evidence supports a scientific claim or interpretation; task/evidence acceptance does not confer this decision. |
| continuation | A new bounded task reusing accepted closure while its invalidation boundary holds. |
| stopped task | A failed gate or new decision boundary with evidence preserved and later stages not started. |

An executor success field, test PASS, validator PASS, or commit does not confer task/evidence or scientific acceptance. For orchestrated status literals and failure handling, consult [Orchestration — Objective gates and failure behavior](../../governance/contracts/orchestration.md#objective-gates-and-failure-behavior); this table is conceptual, not a second status schema.

## Evidence possession and inspection: descriptive concepts

These are distinctions for describing evidence, not enum values or a second
task/status schema. They can apply separately to the same object.

| Situation | Supported statement |
| --- | --- |
| A report or source says a file exists | You have an attestation from that source, with its provenance and limits. |
| A locator/path and hash are known | You can identify a claimed object/version; this alone does not prove you opened or preserved its bytes. |
| Bytes were actually opened, read, or inspected | You can claim that inspection with its actual coverage; inherited summaries and checksums do not substitute for it. |
| A copy is actually possessed or preserved and its hash checked | You can separately claim possession or preservation and byte-integrity verification. |
| A remote deposit is attested | You can claim the attested remote deposit within that evidence; this does not automatically mean you possess a local copy. |

A path plus hash is not a backup. Indexed or searchable material is not thereby
personally inspected or acquired in full. An inherited checksum is not your
own semantic inspection. Conversely, checking a preserved copy's hash supports
byte integrity, not the correctness of its scientific interpretation.
