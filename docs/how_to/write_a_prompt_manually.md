# Write a prompt manually

Use this expert fallback when a knowledgeable author prepares an exact research-task prompt without the novice [assistant preparation route](ask_an_assistant_to_prepare_a_task.md). Human manual authorship is optional; an authorized prompt author normally translates the research lead's mandate.

## Before you start

Obtain the research lead's task mandate, effect boundary and explicit permissions, and the scientific lead's purpose and interpretation boundary as applicable. Read live [CPC.md](../../CPC.md), [AGENTS.md](../../AGENTS.md), [registry](../../governance/repositories.md), applicable module/native policy, and accepted prior evidence before drafting.

## Procedure

1. Derive required CPC fields and literal closed vocabularies from the live sources. Do not copy an old prompt as if its branch, runtime, or permissions were current.
2. State one decision question; repository ID/resolved path; exact `allowed_to_modify` and `read_only`; prompt mode; branch policy and applicability; validation ceiling; network, environment, storage, commit and remote effects; evidence/report/patch; and stop gates. The [bounded change template](../../templates/bounded_change_prompt.md) is an aid, not another schema.
3. For continuation include `continuation_of`, accepted closure, `delta_scope`, invalidation boundary, `checks_not_to_repeat`, fresh volatile-state checks, and only new required evidence. Example: repair provenance in a synthetic note while preserving accepted arithmetic.
4. Reread adversarially: could the executor infer an unintended writable path, permission, scientific claim, or acceptance? Resolve ambiguity or stop for a decision by the responsible researcher.
5. Run the [maintained validator](validate_a_prompt_before_execution.md) on the **filled final Markdown** and reread its output and the exact final prompt.

## Verify the result

Label states precisely: `prepared` means drafted; `conformant` means checked against applicable contract; `authorized/dispatchable` requires a research lead's grant and live preconditions; `dispatched` means issued; `executed` means work/evidence returned; `accepted` requires a separate bounded task/evidence decision by the research coordinator or, for a scientific claim, a scientific decision by the scientific lead. The research lead authorizes the task; neither that authorization nor a reviewer recommendation is acceptance. In the TOP-26-006 reference deployment, the coordinating Chat performs the project-specific task/evidence acceptance function only under live governance and explicit project decisions. A mechanical PASS supports only part of conformance.

## Stop instead of proceeding if...

Authorization from the research lead, branch applicability, live governance, native policy, or evidence provenance is unresolved. Do not fill unknown permissions by analogy or treat a validator PASS as scientific correctness.

## Generic example

A prompt author translates a research lead's bounded synthetic-note mandate into exact path, mode, branch, evidence, and stop fields.

## What this does not establish

A drafted or conformant prompt is not automatically authorized, dispatched, executed, or accepted.
