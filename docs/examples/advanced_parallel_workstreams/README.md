# Synthetic parallel research workstreams

This is a teaching case, not a live project registry, scientific result, agent configuration, or execution record. Read [workstreams](workstreams.md), [evidence dependencies](evidence-dependencies.md), and [coordination history](coordination.md) together. All events were constructed and checked sequentially; no concurrent agent or provider execution occurred.

The question is how a repeated-measurements result and its explanation survive a changed shared assumption. `D_SHARED_R1` is the initial rule for excluding an instrument warm-up reading; `D_SHARED_R2` is its corrected revision. The IDs represent declared revisions, not files in the existing measurement example. No scientific code or data was changed.

The dependency graph is `D_SHARED_R1 → E_METHODS_R1 → E_NOTE_R1`. A separate check `E_CHECK_R1` tests the completeness of the fixed raw-observation listing `D_RAW_R1`; it does not test the warm-up exclusion rule or the resulting estimate. When the rule changes, the first two evidence rows become stale for current use. The raw-listing check remains valid only for its narrow property. `E_METHODS_R2` and `E_NOTE_R2` are new, separately reviewed and accepted revisions; historical rows remain visible.

These three records help a human coordinator see responsibility, dependency, review, acceptance, and transfer decisions. The governing scientific owner and project authority still come from the applicable project governance and explicit task authorization. The records cannot grant permissions or acceptance by themselves.
