# Coordinate shared files and dependencies

Use this before workstreams consume a common input or edit a common target. List each dependency's exact revision and the evidence that consumes it, as in the [synthetic map](../../examples/advanced_parallel_workstreams/evidence-dependencies.md).

1. For shared mutable files, use one writer by default. If genuine nonoverlapping partitions are possible, define path and edit partitions, integration order, and who resolves conflicts before work starts.
2. Pin input identity with a revision, digest, or other appropriate locator. Record direct edges from each result to the inputs actually consumed. Add derived-result edges where an explanation consumes an accepted result.
3. Treat a worktree as a separate Git checkout and index, not universal write isolation. Shared files, caches, data locations, external jobs, and scientific assumptions can still collide.
4. When an input changes, trace reachable evidence and its exact claims. Pause only affected downstream uses, record unaffected evidence with a reason, and seek new review and acceptance for repaired results.
5. Record the decision and next permitted action in a [coordination record](../../reference/advanced/coordination_record.md). A parallel conversation alone establishes no safe simultaneous write or dependency boundary.
