# Coordination record

The [synthetic coordination history](../../examples/advanced_parallel_workstreams/coordination.md) records chronological project decisions. It is neither a scheduler, mailbox, nor automated authority engine.

| Field | Meaning |
| --- | --- |
| `event_id`, `time_or_sequence` | Stable event key and observed order. |
| `workstream_refs`, `actor`, `event_type` | Affected responsibilities and decision maker. |
| `decision_or_issue` | Task, delivery, review, acceptance, invalidation, handoff, or stop, stated precisely. |
| `before_responsibility_ref`, `after_responsibility_ref` | Source of responsibility before and after an event. |
| `sender_ack` | Sender preparation and acknowledgment of the bounded handoff. |
| `receiver_ack` | Receiver acknowledgment of receipt and stated scope only; it does not prove comprehension. |
| `receiver_readback_or_comprehension_ref` | Evidence of the cited artifacts the receiver reopened and the accepted/stale revisions, checkpoint, and continuation boundary they restated. |
| `unresolved_effects_or_blockers` | Known uncertainty, including external effects. |
| `continuation_checkpoint`, `next_permitted_action` | Last verified state and bounded next step. |
| `effective_transfer_authority_ref` | Owner-authorized reference that makes a transfer effective. |

Link each affected evidence revision to its actual inputs and review and acceptance records. Historical invalidation and supersession events stay visible; the latest row alone does not prove current validity.
