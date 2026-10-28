# Orchestration, delegation and long-horizon work

## Stage delta contract

An orchestrated_workflow composes existing modes within one preauthorized
substantive decision. Every mode in AGENTS.md may be a stage except
orchestrated_workflow itself. production_execution is conditional on
production.md. No nested workflows. PR/MR merge remains a separate substantive
decision; merge_existing_pr_or_mr, pr_or_mr_merge: yes, merge_allowed: yes,
automatic merge and remote branch deletion are forbidden inside orchestration.
Generic force is forbidden. The sole guarded history-rewrite action is
normalize_declared_post_squash_staging_ref under git_lifecycle.md's exact
archive/identity/old-SHA-lease contract. It authorizes no other rewrite.

The outer prompt declares workflow_goal, workflow_stages,
workflow_stop_policy, workflow_stage_ledger_path and workflow_effect_envelope.
workflow_effect_envelope uses the ordinary canonical capability/effect keys,
including allowed_to_modify for its maximum path/ref/effect scope,
and is a non-authorizing maximum ceiling: a positive value says only that
a stage could be granted that effect. A false or absent key cannot be granted
by any stage. Outer heavy_command_permissions and branch_policy MUST NOT
appear. The default stop policy is
stop_on_failed_gate_or_new_decision_boundary. Freeze repository identities,
read-only boundaries, validation ceiling, authorized scope and this envelope
at start. No enlargement after execution begins.

Every stage declares exactly this core:
stage_id, stage_mode, stage_goal, stage_effect_permissions, stage_inputs,
stage_acceptance_gate, stage_outputs, stage_failure_behavior.

stage_effect_permissions is the sole positive effect-grant location for a
stage. Use the same canonical capability/effect keys as ordinary permissions.
For tracked/storage/local index/ref effects, include allowed_to_modify with
exact stage-local repository, paths or refs, and named effects. This grant is
separate from the stage-local branch and action fields required by
git_lifecycle.md. Use an empty map for no effects. Do not serialize
stage_permissions as a second authority. A positive envelope key is a
ceiling, never a grant. Outer paths, modes and ceilings constrain rather
than grant stage effects. A stage with only storage_writes: yes cannot edit
a tracked path or move a ref.

Effective stage authority is the intersection of explicit owner
authorization, workflow_effect_envelope, that stage's
stage_effect_permissions, its exact path/ref/action contract, selected
stage_mode, validation ceiling and applicable native policy. An effect key
absent or false in the envelope cannot be granted by a stage; an effect
allowed by the envelope but absent or false in the stage map cannot be
performed by that stage. No grant is inherited or pooled from the envelope,
a prior stage, accepted evidence, stage outputs, delegation_policy or model
capability. A later stage repeats every positive grant it needs. This
repetition is intentional because the envelope is only a ceiling.

stage_inputs names exact immutable context and accepted-evidence references,
prior-stage observed bindings, and preconditions. This replaces
stage_inputs_from_prior and stage_preconditions. stage_failure_behavior
replaces stage_on_failure. Do not emit both old and new names.
stage_branch_policy is the sole branch-policy authority for every stage
whose repository inspection or action depends on branch posture. It uses
create_feature_branch_from_reference, continue_existing_branch or
read_only_current_branch. Declare corresponding reference_branch and
feature_branch, target_branch, or a current-branch safety invariant only
within that stage. Branch policy and branch fields do not pass to another
stage. Exact mode/action fields also remain stage-local, once each as
named fields rather than duplicated inside stage_effect_permissions.
They may bind by reference to one frozen outer immutable input, which
constrains the stage but creates no outer branch or effect authority.
An exact lifecycle action on a detached linked worktree is not branch-relevant
merely because it is a Git worktree action. If it selects or switches no branch
and moves or deletes no branch ref, bind its exact path, registration, HEAD and
action under git_lifecycle.md instead of inventing read_only_current_branch.
An attached controller or ref action remains branch-relevant when its safety
or effect depends on that branch or ref. Ordinary branch-aware inspection and
action still require stage_branch_policy.
Inherit unchanged non-effect context by explicit reference.
Every stage includes all necessary mode-specific fields, including
production bounds and publication identities. Do not copy the whole outer
prompt into each stage. A stage may read explicit outer read-only evidence
scope without repeating it; network reads still require a positive local
grant.

## Objective gates and failure behavior

Start a later stage only after the prior stage serialized evidence, performed
required readback, reopened and validated it, passed its objective gate and
introduced no new substantive choice. Bind later inputs to the observed value,
never to a requested success constant. A stage consuming prior semantic work
must prove semantic completeness as well as isolated intended diff before
mutating its consumer. Diff isolation alone does not prove semantic completeness.
Passing a preauthorized objective gate permits its already-authorized next
stage without a new approval solely for that transition. The gate creates no
new authority or owner acceptance. An interrupted effect with unresolved
outcome requires bounded observation of its actual state before retry or
recovery; an absent success message is not proof that the effect did not occur.
Use autonomy_and_blocker_classification.md for failure classification,
adaptation, expected fallback, authoring defects and real stop boundaries.

A failed or indeterminate gate stops effects and remaining stages, except an
explicitly declared repair/revalidation edge within the same authorized
decision, or a preauthorized terminal read-only completeness-review tail.
A repair edge must predeclare the failure class, exact owned repair surfaces,
action/mode/effect grants, objective revalidation gate, maximum iterations and
resource/time bounds when relevant. Each traversal is a recorded stage
instance. Do not repair foreign work, change scientific decisions, weaken tests,
change tolerances or widen targets to obtain a pass. Unclassified failure,
exhausted bounds, unresolved authority or material drift stops. This permits
predetermined repair cycles without an owner prompt at every iteration;
it does not authorize choosing a new solution surface.

The terminal review tail may inspect only the already-authorized evidence,
populate review_and_evidence.md's five review buckets and record limits.
It cannot mutate, enlarge scope, satisfy/bypass a failed gate, resume execution
or authorize any later effect. A tail must be explicitly declared; review
usefulness alone cannot create it.

Before publication bind exact action, repository, remote, local/remote refs
and expected HEAD from immutable inputs or reopened observations. Only
predeclared topology rules may select inspect/fetch/push/no-action. Divergence,
ambiguous ownership, merge-versus-rebase, an unbound ref, or a new documentation
choice stops. The action-specific Git contract still controls every command,
lease, duplicate guard and readback.

Completed effects persist after a later block. No automatic rollback. A
rollback is allowed only as an explicitly preauthorized stage valid under its
mode and exact effect grants. Do not reset/restore/stash/clean/delete/rewrite to
simulate atomicity. Tracked mutation obeys commit closure: a declared later
commit stage may commit earlier changes; no extra workflow-final commit or
mandatory per-stage commit is implied. A blocked workflow may retain owned
dirty work and must report it honestly.

One final report, one overall patch and one compact stage ledger. Record stage
identity/mode, start/completion state, effective grants, input bindings and
preconditions, gate evidence/readback, gate result, relevant branch/HEAD,
artifacts, persistent effects and iteration counts. Reopen the ledger before
deriving progress. Report completed_stages, blocked_stage, not_started_stages
and persistent_effects_from_completed_stages.

Statuses remain orchestrated_workflow_complete, blocked_stage_gate,
blocked_new_decision_boundary, blocked_stage_permission and
blocked_stage_governance_conflict. A status describes execution, never owner
acceptance. No new compound mode is needed for a deterministic composition of
existing modes.

## Delegation and independent review

delegation_policy is forbidden, allowed or required. Substantial work defaults
to an independent read-only reviewer; prompt authors normally select allowed
or required for it. If delegation is explicitly forbidden or a reviewer cannot
be used, record a brief omission reason and the resulting evidence limit;
never override the owner or pretend a controller self-check was independent.
Small/mechanical work may omit review. Apply review_and_evidence.md's risk
criteria and any stricter repository/task rule.

Independent means the reviewer did not author or execute the main change and
receives the coherent result, evidence and provisional conclusion to challenge.
The same model is allowed; a different model is neither required nor proof of
independence. Reviewer output is advisory evidence, not acceptance authority.
The controller dispositions every material finding by correction within scope,
an evidence-backed limitation or an explicit unresolved boundary.

Read-only independent lanes may run in parallel within declared input scope.
The controller alone performs Git index/ref, remote, production, scheduler and
publication effects by default, sequentially. Delegate such an effect only
through exact owner authorization naming agent, effect, targets, isolation
and join gate; a general delegation grant does not suffice. Publication
duplicate checks, pushes, creation, merge and deletion remain sequential under
one controller; they may not be delegated for concurrent execution.

Source-writing lanes require explicitly assigned disjoint file/change surfaces,
one writing agent per surface, no overlapping autonomous authorship and a
controller join before shared-index staging or validation. Shared dependencies
and generated outputs count as surfaces. Shared-index operations remain with
the controller. Every lane preserves foreign/inherited changes. Unknown
overlap stops the affected lanes. Record roles, inputs, outputs, effects,
conflicts, joins and dispositions without a persistent agent registry.

Parallel-write worktrees are not adopted by default. A future explicitly
authorized ephemeral_agent_worktree use must bind repository/base/branch,
unique path/index ownership, disjoint surfaces, integration/validation gates,
resource/lifespan and exact retirement/deletion authorization. The workflow
must prove isolation and foreign-work preservation before writes. Merely
having separate directories does not authorize parallel feature branches,
integration or deletion; permanent-live exceptions still apply.

### Temporary worker results and controller candidates

A worker's result is its task-owned frozen postimage and evidence at an exact
base, not permanent development authority. The controller candidate is an
exactly bound composition carrier, not permanent development-authority
advancement. Preserve each worker result and its base, inputs, assumptions,
interfaces and review identity before applying it elsewhere. Separate indexes
and disjoint paths establish write isolation; they do not establish combined
semantic correctness.

An exact byte union establishes the identity of the composed candidate only.
It does not establish semantic or interface correctness. Reuse accepted worker
review only while its frozen identity, base, inputs, assumptions and interfaces
remain valid. Review new interactions in the combined candidate at their
actual boundary before promotion or consumer mutation. A controller rewrite of
a worker result leaves the strict exact-union path and is new authorship,
requiring review and validation for the rewritten surface. The evidence
contract owns review depth and claim limits.

### Adopted dependent multi-repository use

For a real task that needs dependent repository changes, apply the adopted
D6/D7 mechanics within each repository's local authority and exact grants.
Bind each base and candidate exactly. Validate the exact candidate tuple where
cross-repository compatibility is decision-material, with task-specific
scientific, producer/consumer, test and runtime checks as applicable. Advance
repositories in the order required by their compatibility dependencies.
Preserve valid partial state; there is no global transaction or automatic
global rollback. An `OUTCOME_UNKNOWN` effect requires exact readback before
any retry. Review material boundaries independently, preserve portable result
and evidence before destructive retirement, retire only exact authorized
task-owned temporary surfaces, and read back final noninterference. A later
scientific or application failure reopens infrastructure qualification only
when it identifies a defect in these mechanics.

### Terminal temporary-surface retirement

When a workflow creates temporary worktrees or refs and preauthorizes their
exact retirement/deletion inside the same substantive decision, terminal
retirement including deletion is the normal final lifecycle stage after
portable preservation and applicable semantic and validation gates. External
lane or owner acceptance after execution is not, by itself, a reason to keep
those temporary surfaces when exact deletion is already authorized. A separate
cleanup round is required only when a real boundary prevents safe deletion.
If one appears, preserve the completed result and residual state and stop;
do not blind-delete or roll back. Removal proves lifecycle closure, not
semantic success or owner acceptance. The Git contract owns exact path, state,
ref and command gates; the autonomy contract owns boundary classification.

## Long-horizon contract

For work expected to span execution attempts or extended checkpoints, declare
durable_objective, definition_of_done, hard_boundaries, checkpoint_ledger,
validation_loop and resume_semantics; add resource_ceiling/time_ceiling when
relevant. The objective remains one substantive decision. A checkpoint stores
observed progress, accepted evidence/invalidation, current boundaries,
performed/pending effects and the next predeclared gate, not a permission cache.

Resume only by binding the current request to the existing authorization,
reopening checkpoint evidence and refreshing decision-material volatile state.
If authorization expired, changed or is ambiguous, stop dependent effects.
Do not resume an ambiguous external command automatically. No checkpoint
extends resource bounds, adopts foreign work or authorizes new targets.
Predetermined repair/revalidation cycles use the bounded stage-edge rules
above. New choices stop; persistence does not make them mechanical.
