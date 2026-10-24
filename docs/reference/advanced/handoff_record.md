# Handoff record

A [handoff](../../examples/advanced_parallel_workstreams/coordination.md) preserves continuity when a responsible person or role changes. It does not itself confer authority.

| Field | Required content |
| --- | --- |
| Sender and receiver | Named roles or people; distinguish executor from responsible role. |
| Scope | Workstream question, exclusions, dependency identities, and transfer boundary. |
| Accepted evidence refs | Exact revisions, acceptance actors, and scopes. |
| Unresolved questions and effects | Open decisions, running or uncertain external effects, and owners of follow-up. |
| Last verified state | What was directly checked, when, and with what evidence. |
| Next permitted action | Bounded continuation after the receiver checks current state. |
| Sender preparation/acknowledgment | Evidence that the sender assembled the handoff. |
| Receiver acknowledgment (`receiver_ack`) | Acknowledgment of receipt and stated scope; this alone does not prove comprehension. |
| Recipient readback (`receiver_readback_or_comprehension_ref`) | Evidence of which cited artifacts the receiver reopened and how they restated accepted and superseded evidence, unresolved effects, the last verified state, and the next permitted action. A generic assertion of understanding is insufficient. |
| Effective transfer authority ref | Explicit owner decision or governance reference making responsibility transfer effective. |

A message receipt, receiver acknowledgment, recipient readback, and effective authority transfer are distinct records. Follow the core [transfer guide](../../how_to/transfer_project_responsibility.md) and [handoff template](../../../templates/handoff.md) for the full procedure. If any effect is uncertain, verify its external state before retrying. The synthetic C10 event illustrates a transfer with no running effect; real handoffs need their own observation.
