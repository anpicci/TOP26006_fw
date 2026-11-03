# The task lifecycle

This page explains reuse and invalidation: a changed dependency reopens only
the dependent claim and its actual consumers. Independent valid evidence
remains reusable. Live governance determines permitted actions.

A task begins with the result that would close its question. The responsible decision-maker identifies that result, its dependencies, permitted actions, needed evidence, who will decide whether to accept it, and which claim that decision covers. The executable task then binds exact repositories, paths, inputs, revisions, validation limits, and stop conditions. Completion by an executor produces a result and provenance; review challenges the claim; acceptance remains a separate decision.

The smallest execution model that can produce that result is usually clearest. A short, tightly coupled task can stay serial in one repository. Multiple dependent steps can share one decision when each has a defined result to check and explicit permission for its own actions. Parallel work is useful for genuinely separable responsibilities with an explicit join and interaction review. Coordination across repositories is needed only when the result crosses their independent authority or compatibility boundaries. Choosing an execution model does not by itself authorize an action.

The lifecycle can continue without repeating valid work. Accepted evidence remains usable while its identity, inputs, assumptions, and relevant interfaces still hold. A changed dependency calls for review of that dependency and directly coupled interactions. A bounded local repair preserves unaffected valid results and repeats the affected check. If a new choice or unsafe uncertainty appears, record the direct state and stop only the dependent action; independent authorized work may continue. Requirements for a later phase do not automatically block a correct current result.

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

When temporary files, worktrees, or refs created for the task are to be removed, preserve portable results and evidence first, then remove only what is authorized after the required checks. The [synthetic lifecycle fixture](../../examples/research_workflow_lifecycle/README.md) illustrates the relationships. The [documentation routes](../index.md) lead to procedures and reference material, while [execution policy](../../AGENTS.md) governs live permissions.
