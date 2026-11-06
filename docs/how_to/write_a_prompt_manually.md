# Write a prompt manually

Use this first-class governed route when an authorized author prepares an exact research-task prompt. It remains available when the [governance workflow compiler's supported patterns](compile_governance_workflow.md) cannot represent the task faithfully. Human manual authorship is optional; the [assistant preparation route](ask_an_assistant_to_prepare_a_task.md) can also translate the research lead's mandate. Choose the mechanism after defining the task, without changing its authority or evidence requirements.

## Before you start

Obtain the research lead's task mandate, effect boundary and explicit permissions, and the scientific lead's purpose and interpretation boundary as applicable. Read live [CPC.md](../../CPC.md), [AGENTS.md](../../AGENTS.md), [registry](../../governance/repositories.md), applicable module/native policy, and accepted prior evidence before drafting.

## Procedure

1. Derive required CPC fields and literal closed vocabularies from the live sources. Do not copy an old prompt as if its branch, runtime, or permissions were current.
2. State one decision question; repository ID/resolved path; exact `allowed_to_modify` and `read_only`; prompt mode; branch policy and applicability; validation ceiling; network, environment, storage, commit and remote effects; evidence/report/patch; and stop gates. The [bounded change template](../../templates/bounded_change_prompt.md) is an aid, not another schema.
3. For continuation include `continuation_of`, accepted closure, `delta_scope`, invalidation boundary, `checks_not_to_repeat`, fresh volatile-state checks, and only new required evidence. Example: repair provenance in a synthetic note while preserving accepted arithmetic.
4. Reread adversarially: could the executor infer an unintended writable path, permission, scientific claim, or acceptance? Resolve ambiguity or stop for a decision by the responsible researcher.
5. Run the [maintained validator](validate_a_prompt_before_execution.md) on the **filled final Markdown** and reread its output and the exact final prompt.

## Deliver one self-contained task

For one already-authorized task or continuation, deliver instruction Markdown
that lets the executor understand the whole job without the research lead
assembling another instruction package. Include the needed objective or
decision, mandate and scope, starting state, accepted evidence and later
corrections or supersessions, continuation delta, authorized effects, relevant
phases, checks and review, real stops, deliverable, and acceptance boundary.
Derive the applicable details from live [CPC.md](../../CPC.md).

Self-contained instructions do not mean embedding all data or copying live
governance into the prompt. Identify real external sources such as governance,
source code, configuration, scientific inputs, artifacts, and previous executor
reports, and explain their relevance. A prior report can carry accepted evidence
and closure; it is not a hidden companion instruction file and cannot anticipate
later owner decisions. State the new objective and delta in the new prompt.

Do not require the research lead to send a second prompt for the same authorized
job, construct a local instruction file, recover instructions from a prior chat,
or assemble a companion plan merely to make it understandable. A genuine new
decision still calls for a new bounded continuation.

In the TOP-26-006 reference deployment, new Codex prompt filenames begin with
`CODEX_PROMPT`. This is a project delivery convention, not a universal AI rule
or a new prompt-field schema. Human-facing references use the filename and a
link when available; hashes supply provenance and integrity evidence rather
than replacing the document name. This convention does not require an executor
receiving prompt text to find a local prompt file; see the [validation boundary](validate_a_prompt_before_execution.md#author-validation-and-runtime-state).

## Inspect maintained capability before proposing another

Before proposing a wrapper, bypass, API, or operational script, inspect the
maintained tool, entrypoint, configuration, or workflow that already performs
the same or nearest accepted job. Check supported options and routing, and
distinguish a wrongly chosen invocation from a missing capability. The first
incompatible command does not establish that the capability is absent.

If there is a real gap, describe it and the smallest necessary extension under
the proper mandate, keeping a refactor outside the task unless authorized.
Use live [execution policy](../../AGENTS.md#reuse-delegation-and-model-provenance)
for the normative reuse and capability lifecycle requirements.

## Verify the result

A drafted prompt still needs review against the applicable contract. Before
execution, establish the research lead's grant and author review of the task's
meaning and governance. The execution environment must then check the current
facts on which the task depends before any effect. Neither a draft nor its
review grants unconditional permission to change repository state.

The author fixes authority, repository/target roles, scope/effects, validation,
stop boundaries and real choices. Runtime verifies current applicability,
including consumed branch/HEAD, dirty/index/conflict, worktree and current-master
facts; it cannot select a new authority, widen scope or decide a scientific
choice. A failed applicability check stops the dependent effect.

`dispatched` means issued; `executed` means work/evidence returned; `accepted`
requires a separate bounded task/evidence decision by the research coordinator
or, for a scientific claim, a scientific decision by the scientific lead. The
research lead authorizes the task; neither that authorization nor a reviewer
recommendation is acceptance. In the TOP-26-006 reference deployment, the
coordinating Chat performs the project-specific task/evidence acceptance function
only under live governance and explicit project decisions. A mechanical PASS
supports only part of conformance.

## Stop instead of proceeding if...

Authorization from the research lead, branch applicability, live governance, native policy, or evidence provenance is unresolved. Do not fill unknown permissions by analogy or treat a validator PASS as scientific correctness.

## Generic example

A prompt author translates a research lead's bounded synthetic-note mandate into exact path, mode, branch, evidence, and stop fields.

## What this does not establish

A drafted or conformant prompt is not automatically authorized, dispatched, executed, or accepted.
