# Production, storage and recovery contract

## Exact production authorization

production_execution is required for production-like or heavy execution,
either as the standalone prompt mode or as the exact stage mode under the
orchestration contract. A production validation ceiling or positive capability
grant cannot substitute for that mode.

This contract applies to production_execution, production stages, scheduler
actions, heavy/output generation, manual handoffs, workflow configuration and
temporary payload lifecycle. It grants no execution permission.

A production prompt or stage must declare production_action, production_target,
input_lineage, effect_surface, execution_owner (codex or user),
intended_output_paths, overwrite_or_resume_policy, interruption_retry_policy,
and the objective output/readback criteria. input_lineage binds exact source,
configuration and inputs required for the decision; effect_surface names
scheduler/backend, commands, services, output paths and repository boundaries.
Use only applicable domain permissions from AGENTS.md in
heavy_command_permissions for a standalone production prompt or
stage_effect_permissions for an orchestrated production stage. In the latter,
workflow_effect_envelope is a non-authorizing ceiling and cannot launch an
effect on its own. Scheduler reads need
scheduler_query and, when outbound, network_access. Submit requires the named
backend's submission grant. Query, submit, cancel, delete, storage and unblind
are independent effects. A production mode, a successful test or a passed prior
stage never grants them.

For nontrivial resource use declare resource_ceiling and time_ceiling, including
jobs/concurrency/storage/runtime as relevant. For retries or resumes declare
retry_ceiling, idempotency_evidence, resume_boundary and recovery_action;
omission means no retries and no resume. The default output policy is no
overwrite, no merging with existing outputs and no silent resume. Before
launch inspect the exact targets and their material capacity constraints.
Existing or indeterminate output blocks launch unless an exact bounded owner
overwrite/resume authorization and state evidence cover it. A filename does
not prove completion.

The controller alone performs production/scheduler/storage effects by default.
An exception must explicitly name the agent, exact effect/targets and isolation;
it cannot be inferred from delegation_policy. Never overlap effect owners.
Read-only workers may analyze frozen evidence; they may not submit, resume,
retry, clean, cancel or mutate scheduler state.

## Production stages and transition gates

production_execution may be a stage only under orchestration.md and this
contract. The outer workflow_effect_envelope is a non-authorizing ceiling
over possible effects, including production and scheduler capabilities.
The outer immutable workflow contract must predeclare the action, target,
input contract, resource/time ceilings and allowed recovery choices; the
production stage must repeat its exact positive grants in
stage_effect_permissions and declare its exact production fields. An
envelope allowance alone cannot launch, submit, query or write.
Immutable values may be inherited by reference, but inputs selected from earlier output must be
observed, reopened and validated against that bounded contract before launch.
A stage must stop on new scientific choices, material input/configuration
drift, scope/target changes, indeterminate identity, missing permission or
resource bounds. Do not turn a data-dependent result into unbounded authority.

Immediately before each effect verify input/configuration identity,
output-collision policy, current scheduler/service state needed for safety and
the applicable stage gate. After the effect obtain independent authoritative
scheduler/process/output/service readback. Command exit/stdout alone does not
establish lifecycle completion. Preserve contradictory states explicitly.
Record partial effects and exact output paths. Reuse stable accepted evidence;
refresh volatile facts when the current decision depends on them.

## Interruption and recovery

Apply AGENTS.md's ambiguous-interruption rule to every possibly external
effect. Proven failure before execution is distinct from possible submission.
Before retry, establish directly that the action did not start or that repeating
it is idempotent, or obtain the already-declared exact bounded recovery authority
with known consequences. A timeout, no job identifier, missing receipt or
connection loss proves none of these. Respect the declared retry/resource
ceilings; exhausting them stops. Unknown active consumers or ownership blocks
cleanup and overwrite. Recovery must not silently change targets, lineage,
scientific tolerances, formulae or methods.

## Campaign validation and handoff

Production campaign validation records years_or_campaigns, categories,
variables, input_paths, output_paths, storage_effects, submission_bounds,
baseline_and_feature_requirements and who_runs_each_command when applicable.
A canary or unit test does not establish full campaign validation.
A manual handoff includes exact commands, preflight, stop conditions, output
and evidence-return requirements. Distinguish codex_validated_configuration,
user_executed_command, user_supplied_runtime_evidence and
codex_post_run_interpretation. Preparing a handoff does not authorize Codex
execution, monitoring or retry. Interpret returned logs, scheduler/output
evidence or separately authorized inspection; do not infer success.

## Runtime configuration consistency

For workflow-related tasks, verify requested and resolved configuration agree:

```text
input files or datasets
years or campaigns
categories
variables or histogram keys
configuration files
output tags
output directories
submission mode
```

Do not infer behavior from filenames or tags alone. Inspect resolved commands
and configurations and, when authorized, produced artifact content.

The report must distinguish:

```text
requested_runtime_config
resolved_runtime_config
artifact_content_check
```

## Temporary filesystem hygiene

For temporary payloads that a round is authorized to create:

* Do not stage large, long-lived, or high-volume intermediates in generic
  `/tmp`. Choose a task-appropriate scratch or storage base already authorized
  by the round and applicable filesystem policy; no base is universal. Small
  runtime-managed or unavoidable temp use does not grant bulk task staging.
* Before writing payloads, identify a unique, nonreused, round-owned private
  namespace with restrictive permissions, its owner, and intended lifespan.
  Verify its path has no collision, confusion, or other-user/round ownership.
  A round that needs no temporary payload needs no new scratch directory.
* Dispose only of exact paths created by the current round as part of an
  explicitly authorized namespace lifecycle, or under a separately exact-
  authorized recovery action, after verifying scope and ownership. Where
  feasible, establish bounded exit and catchable-interruption handlers. Do not
  claim they cover `SIGKILL`, host loss, inaccessible leftovers, or forced
  termination. In `investigation_only`, such declared disposition of newly
  created, ownership-verified private paths is part of their authorized
  lifecycle; the mode's prohibition on general cleanup remains in force.
* Scope `TMPDIR`, `TMP`, and `TEMP` to authorized invocations when the tool
  honors them. For known bypasses, document a bounded authorized alternative
  or stop. Do not persist changes to Codex, runtime, or user environment or
  configuration. Invocation-scoped steering is not software-environment
  mutation and grants no new storage or network effect.
* Before temp-intensive writes, estimate the footprint and check available
  bytes, free inodes, and relevant quotas or capacity limits on the chosen
  authorized filesystem. If a material constraint is unavailable, select
  another authorized safe destination or stop; unknown capacity is not a pass.
* On completion, inspect exact round-owned temporary paths and report each
  cleaned or remaining path with identity, location, and disposition. After an
  interruption, do so only in a separately authorized recovery or readback.
  Label unreadable paths unresolved; preserve canonical reports and audit
  evidence.
* Never wipe generic `/tmp`, clean another user's paths or paths belonging to
  an active other round, delete Codex internal workspace or runtime files, use
  broad wildcards, or follow symlinks out of scope. Pre-existing or prior-round
  remnants remain protected by default and may be removed only through the
  separately exact-authorized recovery action above, after verifying original
  ownership, exact target and path scope, and absence of active consumers.
  Unknown ownership or consumer state fails closed. Artifact or storage grants
  alone do not authorize cleanup, and an exact task-level cleanup denial still
  controls.
* Stop the affected operation when required isolated ownership, relevant
  capacity, safe disposition, or residual accounting cannot be established.
  Report the obstruction without permission escalation, guessed deletion, or
  broader cleanup.

## Conditional reporting

Record the declared action, actual executor, exact lineage/targets, resolved versus requested configuration, resource/retry use, commands actually run, scheduler and output identities, lifecycle readbacks, overwritten/resumed state if authorized, persistent/temporary storage, interruption/recovery disposition and scientific claim ceiling. Exact hashes/refs are required where lineage or safety needs identity; an unknown material fact blocks its dependent claim. Report each exact remaining or disposed temporary path. No production completion or acceptance is inferred from implementation validation.
