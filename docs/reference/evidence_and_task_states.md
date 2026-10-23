# Evidence and task states

The live state and report contracts are in [AGENTS.md sections 6, 18–20](../../AGENTS.md). Keep these distinct:

| State | Meaning |
| --- | --- |
| executor completion | A task actor reports its actions and outputs. |
| observed evidence | Direct inputs, commands, results, identities, and limits. |
| review finding | Independent comparison and blocking/nonblocking classification. |
| owner acceptance | An explicit human decision for a stated claim and scope. |
| continuation | A new bounded task reusing accepted closure while its invalidation boundary holds. |
| stopped task | A failed gate or new decision boundary with evidence preserved and later stages not started. |

An executor success field, test PASS, validator PASS, or commit is not owner acceptance. For orchestrated status literals and failure handling, consult [AGENTS.md section 6](../../AGENTS.md); this table is conceptual, not a second status schema.
