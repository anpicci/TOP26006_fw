# Parallel work and dependency management

Concurrency is a property of dependency and effect boundaries. It does not follow from opening several conversations.

| Pattern | Useful condition | Boundary to record |
| --- | --- | --- |
| Independent parallel work | Separate outputs consume pinned, stable inputs. | Exact inputs and reviewers. |
| Parallel checking | A checker tests a declared property independently along a named dimension. | Shared inputs, shared code or method, prior-result exposure, and executor or model commonality. |
| Shared-dependency work | Outputs consume one mutable assumption or source. | Revision identity and downstream dependency edges. |
| Shared-write work | Contributors need the same mutable target. | Single writer by default, or explicit nonoverlapping partitions and integration owner. |
| Deliberate duplicate work | Independent methods are compared for a stated reason. | Independence dimensions, comparison rule, and separate acceptance. |
| Serial prerequisites | A downstream claim needs an accepted upstream result. | Acceptance gate before consumption. |

In the [synthetic case](../../examples/advanced_parallel_workstreams/evidence-dependencies.md), the revised warm-up rule reaches the methods result and note through recorded edges, but not the raw-listing check. Selective invalidation preserves the check's narrow claim. A separate session, agent, workspace, or worktree does not by itself establish scientific independence, safe shared writes, or a hard security boundary. A duplicate result exposed to the prior answer may be useful checking evidence, but its independence claim must say so.
