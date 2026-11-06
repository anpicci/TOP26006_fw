# The task lifecycle

This page explains reuse and invalidation: a changed dependency reopens only
the dependent claim and its actual consumers. Independent valid evidence
remains reusable. Live governance determines permitted actions.

A task begins with the result that would close its question. The responsible decision-maker identifies that result, its dependencies, permitted actions, needed evidence, who will decide whether to accept it, and which claim that decision covers. The executable task then binds exact repositories, paths, inputs, revisions, validation limits, and stop conditions. Completion by an executor produces a result and provenance; review challenges the claim; acceptance remains a separate decision.

The smallest execution model that can produce that result is usually clearest. A short, tightly coupled task can stay serial in one repository. Multiple dependent steps can share one decision when each has a defined result to check and explicit permission for its own actions. Parallel work is useful for genuinely separable responsibilities with an explicit join and interaction review. Coordination across repositories is needed only when the result crosses their independent authority or compatibility boundaries. Choosing an execution model does not by itself authorize an action.

The lifecycle can continue without repeating valid work. Accepted evidence remains usable while its identity, inputs, assumptions, and relevant interfaces still hold. A changed dependency calls for review of that dependency and directly coupled interactions. A bounded local repair preserves unaffected valid results and repeats the affected check. If a new choice or unsafe uncertainty appears, record the direct state and stop only the dependent action; independent authorized work may continue. Requirements for a later phase do not automatically block a correct current result.

The authoring mechanism is a separate choice within this lifecycle. Use the
[governance workflow compiler](../how_to/compile_governance_workflow.md) only when its
supported workflow patterns faithfully represent the bounded task; otherwise use a
[manual governed prompt](../how_to/write_a_prompt_manually.md). Switching the
mechanism alone neither invalidates accepted evidence nor authorizes replay.
The author fixes authority, roles, scope/effects, validation, stops and real
choices. Before execution, establish those decisions and check the current
governance and resource facts consumed by the task before dependent effects.
Runtime cannot change those semantics. Compilation/receipt, dispatch, execution,
review and bounded or scientific acceptance remain distinct.

For documentation maintenance, follow two different semantic relationships.
First, a generic explanation supplies concepts to procedures and summaries:
[roles](roles_and_authority.md), [decision layers](evidence_reproducibility_and_acceptance.md)
and [scientific responsibility](scientific_responsibility.md) supply their
respective meanings. Second, a concrete decision record supplies facts about
that same event to other records, tutorials and summaries. A correct generic
definition does not ensure that these event projections agree.

Before changing an event fact, identify its result/decision identity, review
reference, acceptance layer, actor function and remit, scope, and validity or
invalidation state. Walk the actual passages that repeat or rely on the changed
field, including summaries without an explicit link, and compare those fields
across representations. A link alone is not a dependency on every fact in its
target. Preserve historical decisions within their original scope; mark only
affected current uses stale. A wording difference, changed unrelated Git state,
or a person holding several roles does not itself invalidate a decision.
Link and terminology checks help navigation but cannot detect every same-object
contradiction; compare the decision semantics before concluding consistency.

## When repeated patching calls for foundational diagnosis

A deeper diagnosis is useful when evidence shows that the same defect family
recurs after claimed closure, a local repair moves the problem to another
consumer, independently reconstructed representations of one fact diverge,
or local checks pass while required downstream behavior remains false. Even
one observed case can establish a structural contradiction; no ritual failure
count is needed. An isolated defect with a known cause and demonstrated local
repair can remain ordinary bounded work.

Start by defining the required behavior or result, its audience or consumer,
and the authority that determines correctness. Trace where the relevant fact
originates and how representations and consumers reinterpret it up to the real
effect. Separate candidate causes from invariants, and freeze positive cases
and counterexamples before selecting a repair. This prevents the proposed
repair from quietly defining its own success criterion.

Prefer the smallest shared repair that fixes the mechanism. Reuse an existing
maintained source or surface before adding abstraction. A canonical source
does not mean one giant file or universal centralization: semantic ownership
may be distributed across repositories and domains. For scientific behavior,
the invariant ultimately comes from the scientific model and qualified
scientific decision. Current code, a fixture, or a report narrative cannot
become the sole oracle merely because it is convenient.

Verify the actual consumer or effect, including both the dangerous case and
the allowed case. A flag, text search, or self-confirming local test alone
cannot establish downstream behavior when that behavior is the decision.
Requalify only what the changed dependency invalidates, preserving valid
closure and history.

Keep the bounded repair surface and predeclared closure criterion visible.
This method grants no project-wide audit, new framework, hidden refactor,
case-ID branches in maintained code or documentation, new approval gate, or
retest of every prior closure. Live authorization still bounds the work.

When temporary files, worktrees, or refs created for the task are to be removed, preserve portable results and evidence first, then remove only what is authorized after the required checks. The [synthetic lifecycle fixture](../../examples/research_workflow_lifecycle/README.md) illustrates the relationships. The [documentation routes](../index.md) lead to procedures and reference material, while [execution policy](../../AGENTS.md) governs live permissions.
