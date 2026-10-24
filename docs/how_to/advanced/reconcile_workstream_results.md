# Reconcile workstream results

Use this after a result arrives or a dependency changes. Review the exact result revision and its [declared input edges](../../examples/advanced_parallel_workstreams/evidence-dependencies.md).

1. Record **execution status**: produced, failed, or uncertain, including any external effects. Delivery only shows that an artifact arrived.
2. Record **review disposition** separately: what was checked, by whom, against which claim, with what limitations. A provider trace or transcript may supplement this evidence but does not replace it.
3. Record **acceptance** by the appropriate owner for an exact result revision and scope. A favorable review does not silently become acceptance.
4. Decide **downstream readiness**: verify that the accepted result matches the consumer's needed claim and current input identities.
5. On a changed dependency, mark affected historical evidence stale for current use by direct or transitive paths. Keep unaffected evidence valid only for its original scope and state why.
6. Produce a new revision, obtain new review and acceptance, and link it as **superseding** current use of the stale revision. Preserve the old row and decision history.

The [R1-to-R2 tutorial](../../tutorials/advanced/02_reconcile_a_shared_dependency_change.md) shows each step without treating delivery, review, acceptance, and readiness as one state.
