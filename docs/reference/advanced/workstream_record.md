# Workstream record

The [synthetic workstreams table](../../examples/advanced_parallel_workstreams/workstreams.md) illustrates a teaching record, not a live authority registry. A workstream ID is a record key for a research responsibility, never a branch, repository, agent, model, or session ID.

| Field | Meaning |
| --- | --- |
| `workstream_id` | Stable teaching key. |
| `research_question`, `scope`, `exclusions` | Claim pursued and boundaries. |
| `responsible_role`, `executor_if_relevant` | Accountable person or role and separate task executor. |
| `source_material_refs`, `expected_output_ids`, `dependency_refs` | Pinned inputs, intended outputs, and edges. |
| `permitted_effects` | Effects to request under actual governance; the row grants none. |
| `review_route`, `acceptance_route` | Separate check and owner decision paths. |
| `current_responsibility_source` | Effective authority reference, including transfer if applicable. |
| `coordination_record_ref` | Events that change state or assign follow-up. |

Record a stop boundary with the scope or its linked coordination event. The responsible owner must confirm any assignment, permission, or acceptance outside this illustrative file.
