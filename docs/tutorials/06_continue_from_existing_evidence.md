# Tutorial 6: continue from existing evidence

**Learning goal:** prepare a bounded continuation that reuses valid evidence and names only the new work.

- **You are:** a researcher preparing the next local task.
- **You want:** to preserve prior closure without replaying an earlier process.
- **You will use:** the maintained observed scenario and continuation template.
- **You will change:** only your personal continuation draft; no repository change is executed here.
- **You will not change:** prior evidence, templates, data, method, code, or any Git history.
- **You should finish with:** a draft naming accepted prior state, delta, invalidation boundary, protected checks, unresolved evidence, and next action.
- **Prerequisites:** read access to the linked inputs and a place for your draft. No prior tutorial execution, scratch repository, or assistant context is required.

## Establish the prior state

Read the [observed scenario](../../examples/research_workflow_lifecycle/observed_scenario.md). From your own checkout, replacing the path, identify the documentary input:

```sh
cd /absolute/path/to/TOP26006_fw
sha256sum examples/research_workflow_lifecycle/observed_scenario.md
cat examples/research_workflow_lifecycle/observed_scenario.md
```

For this teaching draft, use the scenario's state immediately after provenance repair and before its later intentional stop. The analysis source is first-result commit `eb40d2703e74350e09e00c459459d706bbc8fa74`; the repaired record is `c9f7c6b9e090fdc3ae3c29b34171cf3a7cb88ff4`; the CSV hash is `f6b9311f0ce6e675999c5ef31a14d82589179a9f8e82be917df6695c6893c294`. These historical IDs identify evidence stages, not locally available refs.

**Accepted prior state:** the scenario reports task/evidence acceptance by the simulated research coordinator of the bounded synthetic arithmetic record under independent Gaussian assumptions after provenance repair. That is the only closure assumed in this teaching draft. It is neither a real human scientific decision nor proof of the current state of a live repository. Do not import the scenario's later dirty state into this earlier entry point.

If the documentary input lacks these identities or qualifications, stop drafting the dependent claim and identify the discrepancy. [Review returned evidence](05_review_and_accept_returned_evidence.md) explains the limits of the compact report; you need not repeat that lesson.

## Write the continuation

Use the existing [continuation template](../../templates/continuation_prompt.md) read-only. Prepare a personal draft with these explicit entries:

| Entry | Content for this single-repository exercise |
| --- | --- |
| Accepted prior state | The historical repaired synthetic record above, its source/input identities, the scenario path/hash, and simulated acceptance scope. |
| New delta | Propose adding one source-locator sentence to `interpretation.md` in the same scratch analysis repository, identifying the scenario used to explain its lifecycle. Preserve existing quantities, assumptions, and provenance. |
| Invalidation boundary | Changed CSV, script, method/assumptions, source identity, relevant governance, or unexpected live task-path state stops the dependent reuse or write. An unrelated change does not erase valid arithmetic evidence. |
| What must not be repeated | The reported numerical run and already closed provenance repair while their inputs and scope remain valid; no recreation of the first note or append of the old repair. |
| What remains unresolved | The actual repository path, live branch/HEAD/status, full repaired note contents, whether the proposed sentence already exists, current permission, and real authorization from the research lead. The historical summary cannot establish these. |
| Next bounded action | Obtain authorized read-only HEAD/status/note readback from the actual scratch repository and compare it with the declared prior state before proposing any write. |

The proposed sentence is a documentation delta, not a new calculation or evidence transfer to another repository. If it is already present, report that no write is needed. If it conflicts with the existing note or needs new scientific interpretation, stop that delta.

A real continuation may use the
[governance workflow compiler](../how_to/compile_governance_workflow.md) when
its supported workflow patterns faithfully represent the delta and protected evidence.
Otherwise use the [manual governed route](../how_to/write_a_prompt_manually.md).
An authoring-mechanism change alone neither invalidates accepted evidence nor
authorizes replay. Reopen only a changed material dependency and its consumers;
retain the same authority, invalidation boundary and protected checks in either
representation. This teaching draft remains non-executing.

## Review the draft before dispatch

The observable output is your saved continuation draft, including the scenario identity and an explicit unresolved-state list. Compare it with each template field. It must say who owns the next decision, which exact file may change after authorization, which evidence will demonstrate that delta, and what stops the action.

For a real execution prompt, replace unresolved local identities with fresh observations, obtain exact grants from the research lead, and apply live governance. Do not send this illustrative table as an execution-ready prompt. A later executor would return the exact note diff, preserved input identities, validation, and commit evidence; the reviewer advises, the research coordinator records bounded task/evidence acceptance after required review, and the scientific lead separately decides scientific acceptance. Neither acceptance authorizes new effects.

## Restart and choose the next step

Reopen the saved draft and its named scenario after interruption. If the source identity is unchanged, resume at the first unresolved entry; do not replay the historical run. If it changed, record which dependency is invalid and recheck only that dependency and its affected claims. Keep the previous draft as evidence.

To start afresh, use the documented scenario stage above and a new personal draft. No earlier shell state is needed. This exercise proves only that a continuation can be specified, not that its proposed write ran or was accepted.

Next in the learning path is [Tutorial 8: recovery](08_recover_from_a_stopped_task.md), which starts from its own documented stop. This continuation exercise has not created a stopped task; operational recovery is needed only when a real task is actually stopped. Return to the [tutorial learning path](index.md) for other choices. Only when a real task requires a second repository should you use [multi-repository coordination](07_coordinate_a_multi_repository_change.md); it is a later conditional route, not the ordinary next step.
