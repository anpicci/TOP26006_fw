# Stop or resume one workstream

Use this when a workstream pauses, its conversation ends, or its inputs or authority become uncertain. A paused conversation does not stop a submitted job, external command, or another actor's work.

1. Identify the last verified input, output, review, acceptance, and external-effect state. If an effect may still be running or may have completed, mark it uncertain and inspect the authoritative external state before retrying.
2. State the stop reason, affected dependency edges, and which other workstreams can continue within their own scopes. Do not infer that one stream's stop invalidates unrelated accepted evidence.
3. Record accepted checks that remain valid and should not be repeated, plus the exact invalidation boundary that would reopen them.
4. Specify the next permitted action and checkpoint in the [coordination history](../../reference/advanced/coordination_record.md). Do not use the record as a scheduler or automatic retry instruction.
5. If responsibility changes, prepare a [handoff](../../reference/advanced/handoff_record.md) with unresolved effects, have the receiver acknowledge the scope, and cite the effective transfer authority. A new session or message receipt alone is not transfer.

Resume only after the responsible person confirms current input and authority identity. The [synthetic transfer at C10](../../examples/advanced_parallel_workstreams/coordination.md) contains no external effect, so its `none known` statement must not be copied to a real stopped job without inspection.
