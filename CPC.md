# CPC.md — Codex Prompt Contract v2.1 for `correction-lib`

This contract governs how ChatGPT prepares Codex prompts for the
`correction-lib` workspace.

---

## 0. Policy precedence

1. `AGENTS.md` controls execution, repository permissions, branch behavior,
   validation, artifacts, commits, remote publication, and merge
   authorization.
2. `CPC.md` controls prompt construction.
3. `CONTRIBUTING.md` controls reviewer-facing text.
4. Explicit user instructions may override these rules.
5. A generated prompt must tell Codex to stop on conflict rather than guess.

---

## 1. Prompt design objective

Every prompt must be:

```text
consistent
actionable
branch_explicit
repo_boundary_aware
runtime_faithful
resource_proportionate
minimum_sufficient
decision_focused
evidence_first
falsifiable
authorization_explicit
remote_state_aware
```

The primary design rule is:

```text
one_round_one_decision
```

A prompt should contain only the information needed to answer its single
`decision_question` safely and audibly. One decision means one substantive
decision boundary, not necessarily one activity type; cross-mode stages require
the conditional `orchestrated_workflow` contract.

Do not bury the task under accumulated project history. Cite prior artifacts
instead.

Technical capability must remain separate from prompt authorization. The
default Codex session may have outbound network access available, but a prompt
must still authorize network reads, remote Git writes, PR/MR writes, merges,
and remote deletions separately.

---

## 2. Formatting and naming

* Use triple-backtick fenced blocks.
* Use one outer Markdown block only when Andrea explicitly requests a fully
  copy-pastable prompt or document.
* Prefer `snake_case` for prompt fields, helper names, local identifiers,
  report labels, and branch suffixes.
* Preserve real paths, branch names, CLI flags, APIs, filenames, and external
  names exactly.
* Use plain English headings in ChatGPT prose.
* Codex report section labels must follow `AGENTS.md` and use `snake_case`.
* Do not invent profile names, environment variables, or approval mechanisms
  inside a prompt.

---

## 3. Conversation bootstrap versus Codex prompt

### `conversation_bootstrap`

Use only to transfer durable context into a fresh chat. Include:

```text
workspace paths
repository paths
current baseline branch
standing constraints
one sentence about the next activity
```

Do not include a detailed execution plan unless the user also requests the
first Codex prompt.

### `cumulative_checkpoint`

Use a distinct cumulative, versioned checkpoint for evidence-heavy,
long-running work. It complements the small `conversation_bootstrap`; it does
not replace it. The minimum cumulative structure is:

```text
current_state
checkpoint_changelog
decision_history
evidence_history
operational_memory
operational_review_strategy
governance_snapshot
completed_project_closures
active_workstreams_and_external_gates
next_actions
persistence_protocol
prior_checkpoint_index
```

A new checkpoint supersedes stale current-state fields without deleting
history. Preserve rationale, provenance, and explicit reopen conditions. A
checkpoint is evidence and context, never authorization; prompt permissions
and live governance still control every action. Require fresh authoritative
readback for volatile branch, dirty-worktree, PR/MR, CI, permission, scheduler,
storage, and external-service state whenever a decision depends on it. Do not
add a checkpoint renderer, validator, registry, or skill without a separate
demonstrated need and authorization.

### `codex_prompt`

Use for an actionable investigation, coding, validation, documentation,
commit, PR preparation, PR publication, merge, or production round.

When the user asks for text to start a new chat, distinguish:

```text
conversation_bootstrap_only
conversation_bootstrap_plus_first_codex_prompt
```

---

## 4. Mandatory prompt decisions

Every Codex prompt must state:

```text
prompt_id
short_title
prompt_mode
preferred_codex_model
reasoning_level
delegation_policy
model_selection_rationale

workspace_root
repo_locations
allowed_to_modify
read_only

branch_policy
validation_ceiling

decision_question
report_path
patch_path
patch_kind_expected
final_chat_deliverable
```

`decision_question` is mandatory. Include `goal` only when it adds a distinct
execution objective beyond that question; omit a redundant restatement.
Omission does not widen scope or authority.

Use the live applicable `AGENTS.md` source-control policy without a routine
`source_control_policy: inherit_AGENTS_defaults` field. For ordinary prompts,
omission derives these fail-closed values:

```text
heavy_command_permissions: all_no
preflight_profile: compact_preflight
dirty_worktree_policy: require_clean_worktree
```

Every positive capability, expanded preflight, and alternative dirty-worktree
policy remains explicit. Omit `preflight_scope_paths` only when the exact
minimum task-path set is already fixed by an exact `authorized_commit_scope`
or `allowed_to_modify` target, explicitly named read-only targets, and
decision-relevant input, output, or artifact paths. A broad permission or
read-only declaration does not determine that set. State
`preflight_scope_paths` when the intended check differs, the named facts leave
multiple possible sets, or a special collision or dirty-state check names no
other path. Omission never widens inspection to a whole repository or unrelated
untracked files. Follow the preflight rule in `AGENTS.md`.
Require `out_of_scope` only when exclusions constrain the decision or safety
boundary; omission never widens `allowed_to_modify`, permissions, or mode
authority. Repository-facing commit-language prohibitions are inherited from
`AGENTS.md` and `CONTRIBUTING.md`; state exact commit subject or format when
decision-material. Action-specific publication, merge, and normalization
permission fields remain governed by their existing contracts.

Do not serialize `prompt_relationship`; derive it from `continuation_of`:

```text
continuation_of present and non-empty: continuation
continuation_of absent: standalone
```

For a continuation, `continuation_of` is required. Include other continuation
fields only when they carry actual non-empty state:

```text
continuation_of
delta_scope                 when work is explicitly scoped relative to prior work
accepted_prior_evidence     when prior evidence is reused
accepted_closure_layers     when non-empty closure layers are reused
invalidation_boundary       when accepted evidence/closure is preserved outside a reopened boundary
unresolved_checks_only     when unresolved checks are carried
checks_not_to_repeat        when accepted checks are protected from repetition
```

The derived relationship is orthogonal to `prompt_mode`; do not add a
continuation mode, relationship field, or alias. Omit inapplicable continuation
fields instead of serializing `none`, empty lists, or boilerplate placeholders.
Omission means no such state is asserted. Reuse accepted evidence outside its
invalidation boundary, and keep declared `checks_not_to_repeat` authoritative.

For evidence or audit rounds, also state:

```text
evidence_requirements
classification_rules
anti_self_certification_rules
evidence_validation_method
```

When exact `model_profile` identity is decision-material to the round, also
state:

```text
required_profile_agreement_evidence
profile_agreement_failure_policy: fail_closed
```

These fields are conditional. Do not make unavailable exact runtime identity a
universal prompt requirement for ordinary work.

For `pr_publication`, also state:

```text
publication_action
publication_platform
publication_repository
publication_remote
expected_local_head
network_access
remote_git_write
pr_or_mr_write
pr_or_mr_merge
remote_branch_deletion
force_push_allowed
merge_allowed
```

For `publication_action: create_or_reuse_open_pr_or_mr`, additionally state:

```text
publication_base_branch
publication_feature_branch
duplicate_pr_or_mr_policy
draft_allowed
```

For this action, permit `remote_git_write: no` only for a fail-closed
already-synchronized path that requires the fresh advertised remote feature
HEAD to equal `expected_local_head`; require a stop before mutation if it does
not. Permit `remote_git_write: yes` only when explicit user authorization
covers one possible normal non-force explicit-refspec feature-branch push. In
either case, require `remote_branch_already_synchronized` and no push when the
fresh advertised remote feature HEAD already equals `expected_local_head`.

For `publication_action: synchronize_declared_remote_branch`, additionally
state:

```text
publication_local_branch
publication_remote_branch
publication_remote_tracking_ref
```

Use these branch-only safe defaults:

```text
pr_or_mr_write: no
pr_or_mr_merge: no
remote_branch_deletion: no
force_push_allowed: no
merge_allowed: no
```

Use `remote_git_write: no` for exact live query/fetch/tracking-ref refresh only.
Use `remote_git_write: yes` only when an explicit user authorization covers a
possible normal non-force push from the declared local ref to the declared
remote branch. Do not require PR/MR-specific fields for this branch-only
action.

For `publication_action: normalize_declared_post_squash_staging_ref`, state
only its action-specific fields:

```text
exact_remote_ref
exact_observed_old_sha
exact_target_sha
verified_local_archive_ref
verified_remote_archive_ref_when_remote_history_is_being_rewritten
archive_reachability
normalization_identity_basis
force_with_lease_argument: --force-with-lease=<ref>:<exact_old_sha>
generic_force: forbidden
lease_refresh_after_unexplained_remote_movement: forbidden
post_write_remote_readback: required
final_expected_identity_readback: required
```

Also require `network_access: yes`, `remote_git_write: yes`,
`force_push_allowed: yes`, and safe `no` values for PR/MR write, merge, and
remote deletion. These fields are conditional on this exact action and must
not become global publication fields. Require exact user authorization for the
named ref rewrite and the complete AGENTS.md archive, identity, exact-lease,
unexpected-movement stop, and final-readback contract.

For `integration_only`, also state:

```text
integration_source_branch
integration_target_branch
integration_method
expected_source_head
```

Default:

```text
integration_method: ff_only
```

For a local `ff_only` integration, also state:

```text
network_access: no
remote_git_write: no
pr_or_mr_write: no
pr_or_mr_merge: no
remote_branch_deletion: no
force_push_allowed: no
```

Do not require publication platform, repository, remote, or PR/MR fields for
`integration_only`. A non-fast-forward method must state its exact method,
explicit user authorization, and resulting local-commit behavior; rebase and
history rewriting are not implicit alternatives.

When an `integration_only` stage must switch from the current branch to its
declared integration target, `stage_branch_policy: read_only_current_branch` is
invalid because that policy forbids switching. Construct the stage with:

```text
stage_branch_policy: continue_existing_branch
target_branch: <integration_target_branch>
```

The `integration_only` mode remains the owner of the exact integration action;
this rule creates no new branch-policy value or generic branch framework.

For `branch_maintenance_only`, also state:

```text
branch_maintenance_action
affected_local_branches
expected_preserved_head
preservation_ref
reference_restore_source
non_fast_forward_ref_move_authorized
local_branch_deletion
```

If a field is inapplicable, state `none` and why. Default:

```text
local_branch_deletion: no
remote_branch_deletion: no
```

Any non-fast-forward local ref move requires
`non_fast_forward_ref_move_authorized: yes` and exact user authorization for
that maintenance decision. Before moving a ref away from a historical
development head, require serialized proof that the preservation ref resolves
to it and retains every intended commit; require fresh reachability and
authoritative-ref readback afterward. Require exact direct Git commands for
safety-critical local branch/ref operations. Do not make these fields global,
and do not treat this mode as authorization for rebase, reset, deletion, or
history rewriting.

For `orchestrated_workflow`, also state:

```text
workflow_goal
workflow_stages
workflow_stop_policy
workflow_stage_ledger_path
```

Default:

```text
workflow_stop_policy: stop_on_failed_gate_or_new_decision_boundary
```

Declare stages in execution order. For each stage, require the applicable
compact contract:

```text
stage_id
stage_mode
stage_goal
stage_branch_policy
stage_allowed_to_modify
stage_read_only
stage_permissions
stage_preconditions
stage_acceptance_gate
stage_outputs
stage_inputs_from_prior
stage_on_failure
```

Omit genuinely irrelevant stage fields rather than filling them for symmetry,
but include every conditional field required by the selected stage mode. The
outer permissions are a maximum envelope; require stage-local authorization
and forbid permission pooling. Require each transition to use serialized,
mode-required read-back evidence and a passed objective gate. Prior-stage input
bindings must resolve to observed validated outputs, not expected placeholders.

Allow only these stage modes:

```text
investigation_only
coding
validation_only
test_alignment_only
documentation_only
commit_preparation
pr_preparation
integration_only
branch_maintenance_only
pr_publication
```

Forbid nested `orchestrated_workflow` stages and exclude
`production_execution`. A `pr_publication` stage must include all fields
conditionally required by its exact action and remains bounded by the outer
permission envelope, its stage-local permissions, validated reopened evidence,
and explicit user authorization. Forbid
`publication_action: merge_existing_pr_or_mr`, `pr_or_mr_merge: yes`, and
`merge_allowed: yes` inside orchestration, along with generic force, remote
branch deletion, history rewriting outside the action-specific
`normalize_declared_post_squash_staging_ref` contract, and automatic merge.
That normalization action is the sole exact force-with-lease exception inside
orchestration. Require
stop-on-new-decision-boundary behavior, partial-completion reporting, and a
compact observed-evidence stage ledger. Automatic rollback is forbidden unless
an explicitly preauthorized rollback stage is itself valid under an existing
stage mode. These fields are conditional only on `orchestrated_workflow`.

When a mutating stage consumes a semantic contract established by a prior
stage, require the transition gate to prove semantic completeness as well as
diff isolation. Do not impose this additional proof on stages that consume no
prior-stage semantic contract.

An orchestrated publication transition must resolve the exact action,
repository, remote, local ref, remote ref, and expected local HEAD from explicit
immutable inputs or reopened observed evidence; require the exact stage-local
network/write permissions and explicit authorization for any remote write; and
stop on divergence, ambiguous ownership, or a merge-versus-rebase choice.
Remote inspection, mechanically selected safe synchronization, and post-action
readback may share one stage only when predeclared objective topology rules
fully determine the action.

When publication-grade review is preauthorized, a stage may declare the
AGENTS.md terminal read-only completeness-review tail after a failed or
indeterminate gate. Require it to stay on the already-authorized evidence
surface, populate the five review buckets, and remain unable to mutate, enlarge
scope, satisfy the gate, resume execution, or authorize later effects.

Required defaults for `create_or_reuse_open_pr_or_mr`:

```text
publication_action: create_or_reuse_open_pr_or_mr
force_push_allowed: no
merge_allowed: no
draft_allowed: no
pr_or_mr_merge: no
remote_branch_deletion: no
```

For a separate merge round, also state:

```text
publication_action: merge_existing_pr_or_mr
pr_or_mr_number_or_url
pr_or_mr_merge: yes
merge_allowed: yes
remote_branch_deletion: <yes_or_no>
```

For `production_execution` and a user-run production handoff, also state:

```text
execution_owner: <codex_or_user>
intended_output_paths
overwrite_or_resume_policy
interruption_retry_policy
```

For a user-run handoff, additionally distinguish:

```text
codex_validated_configuration
user_executed_command
user_supplied_runtime_evidence
codex_post_run_interpretation
```

The default policy is no overwrite, no merge with existing output, and no
silent resume. A prompt must require an explicit bounded authorization before
overwriting or resuming an existing or indeterminate target.

For fields still required by their applicable contract, state `none` and why
when intentionally inapplicable. Do not add synthetic `none` values for the
conditional fields in this P0 schema.

For any prompt that will commit tracked changes, also state:

```text
authorized_commit_scope:
  - <exact tracked path permitted to enter the prompt-local commit>
explicitly_adopted_inherited_changes:
  - <exact inherited path/change and evidence, or none>
foreign_dirty_change_policy: preserve_and_exclude
staging_policy: exact_path_only
```

Derive ordinary commit behavior from tracked repository-file mutation or
explicit adoption. Routine prompts need not serialize `commit_expected` or
`do_not_commit`.

Except for an exact owner-authorized `do_not_commit: yes` round, require
successful round or workflow closure to include a prompt-local commit of all
intended task-owned or explicitly adopted tracked changes, with the task-scope
index and tracked worktree clean. An orchestrated workflow may defer
that commit only to a later declared commit stage in the same workflow; do not
require one commit per mutating stage. If a safe commit cannot be made in a
commit-required round, the round remains incomplete. `do_not_commit: yes` for
tracked mutation requires explicit owner authorization for that exact round,
cited in the prompt.
Read-only rounds that create no tracked changes do not require a commit.
Omission of `do_not_commit: yes` never authorizes uncommitted tracked changes.

`authorized_commit_scope` is the exact prompt-declared subset of
`allowed_to_modify` eligible for the prompt-local commit. It governs commit
eligibility only; it does not establish ownership or adopt inherited work. If
the prompt explicitly allows `commit_not_required`,
`authorized_commit_scope: none` may be used only when no tracked commit is
expected to be created.

Require ownership classification at preflight and again immediately before
staging and commit. A continuation may adopt inherited changes only through
the explicit field above; authorized scope or existing dirtiness does not
imply adoption. At runtime classify actual changes as:

```text
task_owned_changes:
  created by the current round inside authorized scope

explicitly_adopted_inherited_changes:
  exact inherited changes explicitly adopted by a continuation

foreign_dirty_changes:
  every other change
```

`explicitly_adopted_inherited_paths` are the exact paths containing
`explicitly_adopted_inherited_changes`. Derive the term from the exact adopted
changes; path membership does not adopt or confer ownership on any other
pre-existing or foreign change in the same path.

If a gate uses `task_owned_paths`, derive it only from the exact paths
containing proven `task_owned_changes`; the term is not an authorization field
and does not confer ownership on pre-existing or foreign changes in the same
path. Ownership or continuation adoption must not expand the declared
`authorized_commit_scope`. Require:

```text
staged_paths subset_of authorized_commit_scope
staged_paths subset_of task_owned_paths union explicitly_adopted_inherited_paths
staged_diff contains_only task_owned_changes or explicitly_adopted_inherited_changes
```

Prohibit `git add -A` and `git add .` unless an explicitly authorized
whole-worktree task proves every affected change task-owned. Even then, require
complete staged-path and staged-diff readback. Unconditionally prohibit
`git commit -a` for prompt-local commits because it can stage tracked changes
during the commit invocation after that readback; the commit must use an index
that was already fully materialized and reviewed. Require exact-path staging
by default. If a foreign path is staged, stop the commit and preserve its
working-tree content. A prompt may authorize the narrow AGENTS.md index-only
`git restore --staged -- <exact_foreign_path>...` recovery only with
conflict-free preconditions and before/after proof that working-tree content
is unchanged; it must not weaken the general reset, restore, discard, stash,
or cleanup prohibitions.

These commit-isolation rules do not prohibit concurrent work in independent
repositories or separate worktrees with separate indexes. Put a stronger
one-mutating-round-at-a-time rule for a shared working tree in the applicable
programme prompt or control-plane contract rather than treating it as a
universal ban.

---

## 5. Model, reasoning, and delegation selection

Declare model, reasoning, and delegation separately. Derive `model_profile`
from `preferred_codex_model` plus `reasoning_level` as defined by AGENTS.md
section 8; do not add duplicate profile state or fold `delegation_policy` or
`codex_cli_mode` into it. The concrete model-label and reasoning vocabularies
and the canonical routing matrix remain owned by AGENTS.md. Apply that matrix
to the current round's substantive decision, not its lane label, importance,
or file count, and explain in `model_selection_rationale` why the selected pair
fits. A prompt is execution-ready only when `preferred_codex_model` and the
derived `model_profile.model` contain a concrete Codex model label.

Andrea together with `lane_governance` owns the general policy. The owning
lane's prompt author selects and motivates each concrete pair. The central
control plane receives and preserves these rules in checkpoints; it does not
author prompts, select the pair, or approve each compliant prompt.

For governed Codex CLI dispatch, require invocation-local materialization:

```text
model:
  -m <concrete_codex_model_label>

reasoning_effort:
  -c 'model_reasoning_effort="<reasoning_level>"'
```

Require values from the AGENTS.md allow-lists. The local bootstrap parser's
acceptance of an arbitrary string does not establish a supported value, runtime
application, service availability, or account availability.

`explicit_fallback` is a selection/reporting state, not an executable
`preferred_codex_model`, `model_profile.model`, or `-m` value. Before a fallback
attempt, require the owning lane's prompt author to select one concrete label,
place it in `preferred_codex_model` and the derived profile, and record the
fallback path through `fallback_or_switch`. Do not add a persistent
resolved-model field.

Construct each dispatch as one immutable `model_profile` execution attempt
under AGENTS.md section 8. If the executor recommends any upward, downward,
model, or reasoning-only reclassification, require the current attempt to stop
and the owning lane's prompt author to issue a fresh explicit dispatch with the
relevant owner authorization. Do not construct automatic self-routing or silent
fallback. Treat `explicit_fallback` as a new selection path after stop/report;
the new explicit dispatch uses the concrete model selected by the prompt author,
not the sentinel.

Reports and prompts must keep model selection separate from model
observability. Distinguish `requested_or_dispatched_model`,
`requested_or_dispatched_reasoning_effort`,
`directly_selected_model_if_observable`,
`runtime_reported_model_label_if_observable`,
`runtime_reported_reasoning_effort_if_observable`, and `fallback_or_switch`
when applicable. Reuse `preferred_or_configured_model` and `reasoning_level`
when they already carry the requested/dispatched semantics rather than adding
duplicate aliases. Report an unavailable exact value as `not_observable`; do
not infer an exact model from a generic family label or promote CLI/provider
metadata to independently observed runtime identity.

If exact profile identity is decision-material, require the conditional section
4 profile-agreement fields and the AGENTS.md fail-closed rule. Otherwise require
honest requested/dispatched and available reported provenance without making
unknown runtime identity a universal blocker. An observed mismatch, fallback,
or switch requires stop and reclassification.

Use the one canonical default matrix and legacy/fallback conditions in AGENTS.md
section 8; do not maintain a second routing table here. Distinguish simple
formatting from documentation that implements an established substantive
decision. An explicit deviation uses `model_selection_rationale` and does not
require central control-plane approval or a new benchmark.

Treat `medium` and `high` according to the canonical task tiers in AGENTS.md;
do not describe every substantive round as requiring `high`. Apply only the
upper exceptions and their conditions authorized there, including explicit
exceptional owner/eval-driven selection for Astra `max`. Require a specific
reasoning need and a bounded scope or resource decision, without a prior
lower-tier failure. None of these choices changes evidence, correctness,
permissions, delegation, acceptance criteria, or production authorization.
Do not construct an automatic model or reasoning ladder. Preserve historical
benchmark/report labels and require a fresh explicit dispatch with honest
provenance for any legacy/fallback selection under AGENTS.md.

Rules:

* Do not use Sol merely because a task is important.
* Do not rely on CLI defaults for serious work.
* Do not use Luna `max` to compensate for model fit.
* Preserve scope when recommending fallback; stop and require a new explicit
  dispatch with a concrete profile selected by the owning lane's prompt author.

Encode Ultra only when explicitly authorized:

```text
reasoning_level: max
delegation_policy: allowed
codex_cli_mode: ultra
```

Do not add `ultra` to the `reasoning_level` vocabulary. It remains the separate
CLI orchestration mode represented above.

Use `delegation_policy: required` instead when the exact workflow requires
delegation; both values remain members of the closed vocabulary.

Do not use Ultra for narrow controlled work, commit preparation, publication,
merge, or production execution.

---

## 6. Prompt modes

Allowed values:

```text
investigation_only
coding
validation_only
test_alignment_only
documentation_only
commit_preparation
pr_preparation
integration_only
branch_maintenance_only
orchestrated_workflow
pr_publication
production_execution
```

Select the smallest sufficient contract. Use `orchestrated_workflow` when one
substantive decision has two or more meaningful stages with distinct mode or
effect boundaries and a later authorized action depends on validated,
serialized evidence from an earlier stage. Routine editing, ordinary
validation, and a prompt-local commit inside one coherent `coding` contract do
not automatically require orchestration. Cross-repository mutation,
reconciliation, migration, behavior-dependent documentation, and nontrivial
publication are signals to test against this dependency rule, not
unconditional triggers.

* `investigation_only`: read-only diagnosis and evidence work.
* `coding`: tracked implementation/test/config changes.
* `validation_only`: bounded runtime validation without source edits.
* `test_alignment_only`: stale-test changes only after runtime intent is proven.
* `documentation_only`: tracked documentation changes.
* `commit_preparation`: stage and commit intended existing changes.
* `pr_preparation`: reviewer-facing text only.
* `integration_only`: explicitly declared local branch integration with the
  default `ff_only` method and no remote publication.
* `branch_maintenance_only`: explicitly authorized local branch/ref lifecycle
  normalization with preservation and reachability proof, no source edits, and
  no new commits.
* `orchestrated_workflow`: ordered composition of allowed existing modes inside
  one substantive decision boundary, with stage-local permissions, validated
  transition gates, and auditable partial completion.
* `pr_publication`: exact-branch remote synchronization, publication of an
  already validated branch and creation/update of the requested PR/MR, or a
  separately authorized remote PR/MR merge round.
* `production_execution`: production-like or heavy commands.

Do not combine `pr_publication` with source editing, new commits, history
rewriting, force push, remote deletion, or merge unless the exact action is the
single explicit decision and separately authorized. Generic force is never an
available action; the only guarded rewrite is the exact-lease post-squash
normalization contract.

Do not nest `orchestrated_workflow`. It excludes `production_execution` and
allows only non-merge, stage-local, explicitly authorized `pr_publication`
actions. `merge_existing_pr_or_mr` remains a dedicated separate decision round.

### Human-facing `workflow_graph`

For a nontrivial orchestrated prompt, normally include a small self-contained
plain-text projection:

```text
workflow_graph:
  representation: inline_plain_text
  self_contained_in_markdown: yes
  renderer_required: no
  external_asset_required: no
  normative: no
```

Atomic or trivial prompts normally omit it. The graph is a presentation aid
for the declared stages, gates, and stop paths; the structured stage contracts
remain normative. Do not parse the graph, derive execution authority from it,
mechanically compare it with the stage ledger, or create graph-specific
acceptance gates. An inaccurate graph is a documentation-quality defect, not
an alternative execution contract.

---

## 7. Branch policy

Every prompt must declare one of:

```text
create_feature_branch_from_reference
continue_existing_branch
read_only_current_branch
```

Branch policy selects which branch the round may use and whether it may create
or switch branches. Prompt mode controls the activity allowed in that round;
the commit contract controls whether tracked changes must be committed before
successful closure. Do not encode a commit phase in branch policy.

Require branch facts according to the selected policy:

```text
create_feature_branch_from_reference: reference_branch, feature_branch
continue_existing_branch: target_branch
read_only_current_branch: observed current branch from fresh preflight
```

For `read_only_current_branch`, declare an expected
`current_checked_out_branch` only when exact identity is a safety invariant;
stop on a mismatch. Require `current_baseline_branch`,
`comparison_baseline`, and `integrated_baseline_mode` only when
decision-material. Do not add synthetic `none` values. Omission of a branch
fact never authorizes creation, switching, integration, or reclassification;
an unresolved decision-material fact stops the prompt.

Before emitting a prompt that proposes `create_feature_branch_from_reference`
or may mutate tracked repository state, the prompt author must fresh-resolve
applicable active feature branches from live Git state for the target
repository and workstream, regardless of whether the tracked work is described
as coding, documentation, configuration, testing, maintenance, or another
repository activity. Base branch selection on whether the repository and
workstream need a development feature branch, not on a file-category list.
Use semantic/dependency continuity: a feature-only dependency, the same accepted
semantic surface, or replay/duplication of accepted feature work strongly
supports applicability. Package, analysis, or campaign proximity alone does
not. Require positive bounded evidence for
`NO_APPLICABLE_ACTIVE_FEATURE_BRANCH`; if evidence is insufficient or
contradictory, emit `BRANCH_APPLICABILITY_AMBIGUOUS` and stop rather than treat
uncertainty as zero.

With exactly one applicable branch,
require `continue_existing_branch` and name it as `target_branch` unless the
owner explicitly authorizes a named split, supersession, or integration
exception. With none, `create_feature_branch_from_reference` may be used. With
multiple, stop for reconciliation unless the owner authorizes such an
exception. Use the compact exception contract in `AGENTS.md`; do not create a
second branch-state registry or cache. `AGENTS.md` remains normative for runtime
branch behavior.

For TOPEFT, encode these permanent branch roles in every applicable prompt:

```text
permanent integration branch: run3_test_mmerged
permanent personal reference: run3_test_mmerged_anpicci
feature/development namespace: te/*
```

Every `te/*` branch remains feature/development, even when cumulative,
accepted, or the current source-writing authority. Count each applicable
cumulative `te/*` branch in the reuse-first gate: one applicable active
feature requires `continue_existing_branch`; multiple require stopping for
reconciliation unless the exact owner exception authorizes otherwise. Never
classify a `te/*` branch as a permanent reference or integration branch, or
exclude it from the active-feature count, based on its cumulative authority.

With zero applicable active TOPEFT features, ordinary new-feature creation may
use `create_feature_branch_from_reference` only when creation is authorized;
create `te/<repository_facing_name>` from `run3_test_mmerged_anpicci` by default.
Keep `run3_test_mmerged` as the permanent integration target. Generic baseline
fields and `integrated_baseline_mode` cannot override these roles or the
reuse-first gate. Explicit feature-to-feature consolidation leaves the
permanent roles unchanged. This TOPEFT rule preserves the generic three-policy
model and the existing `te/` and `tc/` namespace rules.

When creation is permitted, use `te/<repository_facing_name>` for a new
`topeft` feature branch and `tc/<repository_facing_name>` for a new `topcoffea`
feature branch. This namespace rule does not govern the `correction-lib`
meta-repository or unrelated repositories. Name new branches for the
repository-facing change, following established conventions rather than
internal lane, prompt, Codex, control-plane, round, or campaign identifiers
unless such identifiers already are an established repository-facing
convention. A prompt that proposes a parallel or new branch while an
applicable active feature branch exists without the exact owner-authorized
exception is invalid before execution: `PROMPT_INVALID_BRANCH_POLICY`.

Reject direct development on a declared reference or integration branch.
Read-only work normally uses `read_only_current_branch`. Commit preparation
on an existing feature branch uses `continue_existing_branch`.
For read-only investigation, report any future branch disposition as a bounded
conclusion without reclassifying a cumulative `te/*` feature as a reference.

PR/MR publication normally uses `read_only_current_branch` because it must
publish the exact already validated local branch without local mutation.

Never leave branch behavior implicit. Remote branch names do not freeze remote
commits; require a live query when current remote state matters.

---

## 8. Decision-focused prompt construction

Every prompt must contain one explicit question:

```text
decision_question:
  <the single question this round must answer>
```

Examples:

```text
Does direct source and commit evidence support the existing technical
readiness verdict?
```

```text
Are the new Run 3 central and private pkls compatible inputs for the
missing-parton derivation?
```

```text
Can the exact validated feature HEAD be published non-forcibly and represented
by exactly one open non-draft PR against the declared live base?
```

Rules:

* One prompt normally answers one decision question. An
  `orchestrated_workflow` may contain multiple activity types only when they
  implement that one substantive decision and every transition is already
  determined by an objective gate.
* Separate implementation closure, history review, campaign qualification,
  derivation, installation, PR preparation, publication, and merge.
* If a stage result creates a new unpreauthorized choice, require
  `blocked_new_decision_boundary`; report completed stages and stop.
* Do not include an expected successful conclusion for investigation,
  validation, audit, or publication.
* Expected values are allowed only for immutable inputs and safety invariants.
* Do not prescribe zero failures for checks designed to discover failures.
* Define evidence-based acceptance rules instead.

When the decision claims integration/reconciliation, remote publication or
merge, scientific/analysis, migration/deprecation, or repository-history
normalization sign-off, request the AGENTS.md publication-grade review and its
five buckets. Do not request that review merely because ordinary bounded
coding touches multiple files. Request only the applicable AGENTS.md closure
layers; one closure claim must not be presented as another.

Treat accepted closure layers independently unless the declared invalidation
boundary or direct dependency evidence reopens them. Publication-grade review
must still surface every deficiency material to its sign-off claim.

---

## 9. Continuation prompts and accepted evidence

Use compact exact references for state that applies:

```text
continuation_of: <prior_prompt_or_exact_artifact_set>

# Include only when prior evidence is reused:
accepted_prior_evidence:
  - claim: <already established claim>
    artifact: <exact path>
    locator: <row, key, or section>

# Include only when non-empty closure layers are reused:
accepted_closure_layers:
  - <accepted_layer_and_evidence_reference>

# Include only when accepted evidence/closure is preserved outside a reopened boundary:
invalidation_boundary:
  - <change_or_condition_that_reopens_accepted_evidence>

# Include when work is explicitly scoped relative to prior work:
delta_scope:
  - <changed_newly_unresolved_or_directly_coupled_reachable_surface>

# Include only when unresolved checks are carried:
unresolved_checks_only:
  - <genuinely unresolved check>

# Include only when accepted checks are protected from repetition:
checks_not_to_repeat:
  - <accepted check>
```

`continuation_of` is required for a continuation. Include `delta_scope` when
the current work is explicitly scoped relative to prior work. Include
`accepted_prior_evidence` only when prior evidence is reused,
`accepted_closure_layers` only when non-empty closure layers are reused,
`invalidation_boundary` only when accepted evidence or closure is preserved
outside a reopened boundary, `unresolved_checks_only` only when unresolved
checks are carried, and `checks_not_to_repeat` only when accepted checks are
protected from repetition. Omit inapplicable fields; do not use `none`, empty
lists, or placeholders. Omission asserts no such state and does not weaken
evidence reuse or invalidation protections.

Do not reproduce whole reports or long summaries.

A continuation is derived from `continuation_of`, not a prompt mode. Validate only
the declared delta: changed or newly unresolved behavior plus directly coupled
reachable surfaces. Inherit accepted validation outside the invalidation
boundary, but require the boundary and delta scope to expand when direct
evidence reveals additional coupling. This does not relax any AGENTS.md
affected-surface rerun rule.

Distinguish reporting defects when constructing continuation and evidence
work:

```text
decision_material_reporting_defect:
  bounded evidence completion may be scheduled.

non_blocking_reporting_defect:
  record; do not create a standalone repair round solely for it.
```

Do not construct a standalone prompt whose only decision surface is a
`non_blocking_reporting_defect`.

Do not rerun accepted checks unless:

```text
relevant_source_or_input_changed
evidence_missing_or_unreadable
method_proven_invalid
user_explicitly_requests_revalidation
live_remote_state_is_required
```

Live remote refs, PR/MR state, and repository permission are current-state
inputs. Query them when they are part of the decision.

When a squash-merged tree is directly proven identical to the accepted feature
tree, a continuation prompt may reuse accepted pre-merge implementation
validation under the AGENTS.md accepted-evidence standard. Require a rerun only
for changed relevant source, runtime input/configuration, environment or
dependency, required live external state, invalid evidence, or an explicit user
request. Still declare current branch, HEAD, and tree checks needed for the
decision.

---

## 10. Evidence-first prompt construction

For evidence, history, readiness, publication, or merge rounds, require:

```text
1. collect_direct_evidence
2. serialize_evidence
3. reopen_and_validate_evidence
4. classify_evidence
5. derive_verdict
```

Never reverse this order.

For source claims:

```text
unchanged:
  identical focused-block hash, empty focused diff, or equivalent direct proof

changed:
  focused hunk, responsible commit, before/after behavior, impact, and accepted
  output evidence when applicable
```

For publication claims:

```text
branch_published:
  remote ref readback equals the exact expected local HEAD

pr_or_mr_opened:
  remote API readback confirms repository, base, head, head commit, title,
  open state, and non-draft status

merge_completed:
  remote API readback confirms merged state and resulting commit as applicable
```

Prompts for evidence rounds must forbid:

```text
hardcoded_pass_fail_values
observed_values_copied_from_expected_values
classification_to_commit_lookup_tables
generic_evidence_ids_for_unrelated_gates
duplicate_whole_file_diffs_under_component_names
readiness_rows_created_before_evidence_validation
self_validation_without_reopening_serialized_artifacts
generic_behavior_descriptions
publication_success_inferred_only_from_command_stdout
```

When scripts are allowed, prefer separate collector and validator scripts. The
validator reopens artifacts and recomputes references, hashes,
classifications, counts, contradictions, and readiness inputs.

For an evidence round that compares artifacts, interprets numerical payloads,
depends on a downstream consumer, audits runtime behavior, or reads large
artifacts, request only the applicable compact checks: semantic stage
compatibility; consumer-side authority and availability; diagnostic aggregate
versus consumed decision object; authoritative numerical conventions and
per-artifact normalization; authority for any exact quantity; covariance and
statistical-model status for formal wording; frozen target identities and
bounded extraction; preserved decision scope after representation/resource
failure; runtime reachability; decision-required proof standard; and
like-for-like comparability. Do not turn this conditional checklist into
universal top-level fields.

Publication commands must remain direct commands, not hidden in a collector.

---

## 11. Minimum-sufficient scope and artifacts

Prompts should be complete but compact. Keep explicit:

```text
repo_and_branch_decisions
writable_and_read_only_surfaces
unique_dirty_state_constraints
validation_ceiling
heavy_permissions
decision_question_and_optional_distinct_goal
accepted_evidence_when_reused
unresolved_checks
exact_inputs_and_outputs
commit_expectation
unique_stop_conditions
publication_contract_when_applicable
```

Reference stable governance instead of copying it.

Default task-specific artifact limit:

```text
five_artifacts_plus_report_and_patch
```

Prefer one primary evidence artifact, one validation artifact, and one decision
summary over overlapping manifests.

For PR/MR publication, normally require only:

```text
reviewer_ready_body_or_existing_body_reference
direct_remote_evidence
one_report
one_empty_no_changes_patch
```

---

## 12. Publication prompt construction

AGENTS.md is the normative owner of publication, merge, authorization, and
remote-operation procedure. This section retains the fields, defaults,
direct-command constraints, live-state evidence, compact examples, and failure
classes needed to construct a valid prompt; it does not duplicate the full
operational procedure.

The default Codex workspace-write session may have outbound network access
enabled. Do not require a special publication profile and do not instruct
Codex to alter its sandbox, approval policy, user configuration, or rules.

Prompt authorization remains mandatory.

For each publication action, declare its action-specific fields from section 4
and its exact permissions and effect boundary from `AGENTS.md` section 6.
Encode the observed-state gate that selects any conditional push, fetch, or
no-action outcome. The prompt must require the action-specific fresh remote
readbacks and hard stops in `AGENTS.md`; omission of a grant never authorizes a
remote effect. For guarded post-squash normalization, name the exact rewrite
and lease in the prompt and use only its separate action contract.

### 12.1 glados Git-over-SSH rule

For Git-over-SSH from Codex on glados, require direct Git commands that select
the exact prompt-authorized repository with either its native process working
directory or `git -C <exact_prompt_authorized_repository_path>`, using:

```bash
git \
  -c core.sshCommand='/usr/bin/ssh -F /dev/null' \
  <subcommand> ...
```

This bypasses only the sandbox-rejected system SSH configuration for the
current command.

For `gh` or `glab`, permit the native repository working directory, an explicit
repository selector such as `--repo <owner/repository>`, or an explicit
repository-qualified API/resource endpoint when supported. Require the prompt
or stage to authorize the exact repository and action independently; command
location and repository-selection syntax are execution context, not proof of
authorization, identity, or publication correctness, and must not widen
writable scope. Require repository-identity readback when it is
decision-material.

Do not request:

```text
nested shells
login shells
env wrappers
heredocs
one large publication script
persistent core.sshCommand configuration
remote URL replacement
system SSH permission or ownership changes
```

### 12.2 Construction requirements and compact examples

Require the action-specific `AGENTS.md` publication sequence and one separate
direct command per network operation. Bind every conditional action to its
declared live-state gate and readback. Retain only the following concise
direct-command examples in the prompt when Git-over-SSH is used:

Canonical live-base query:

```bash
git \
  -c core.sshCommand='/usr/bin/ssh -F /dev/null' \
  ls-remote \
  <remote> \
  refs/heads/<base_branch>
```

Canonical exact-branch fetch when explicitly authorized:

```bash
git \
  -C <exact_prompt_authorized_repository_path> \
  -c core.sshCommand='/usr/bin/ssh -F /dev/null' \
  fetch \
  <remote> \
  refs/heads/<remote_branch>:refs/remotes/<remote>/<remote_branch>
```

Canonical normal push:

```bash
git \
  -c core.sshCommand='/usr/bin/ssh -F /dev/null' \
  push \
  <remote> \
  refs/heads/<feature_branch>:refs/heads/<feature_branch>
```

Use the action-specific `AGENTS.md` force, deletion, merge, refspec, and
readback restrictions. The examples above grant no effect by themselves.

### 12.3 Duplicate handling and failure classification

Default:

```text
duplicate_pr_or_mr_policy: reuse_exact_open_match_else_create_one
```

An exact open match agrees on:

```text
repository
base branch
feature branch
```

Require the `AGENTS.md` duplicate-check and readback sequence, including the
check after conditional synchronization and before creation.

Classify failures precisely:

```text
blocked_network_execution:
  the process could not reach the remote, or execution was rejected before the
  remote returned an authentication or authorization decision

blocked_authentication:
  the remote service explicitly rejected authentication

blocked_permission:
  authentication succeeded, but repository authorization was insufficient

blocked_remote_state:
  live branch, duplicate PR/MR, or ref state violated a safety invariant

blocked_local_state:
  local branch, HEAD, cleanliness, evidence, or reviewer material did not match
  the publication contract
```

Do not infer invalid credentials from DNS, socket, sandbox, SSH-config, or
pre-spawn failures.

### 12.4 Merge rounds and manual user merges

For an explicitly authorized merge, construct a separate `pr_publication`
round with one decision question and:

```text
publication_action: merge_existing_pr_or_mr
pr_or_mr_merge: yes
merge_allowed: yes
```

Require the `AGENTS.md` merge gate and immediate pre-merge readback of:

```text
open state
draft status
base branch
head branch
head commit
mergeability or conflicts
required checks or CI state when available
review state when required by repository policy
```

State the exact merge method:

```text
merge
squash
rebase
```

Remote source-branch deletion requires a separate declaration.

A user manual review and merge needs no Codex merge-readiness prompt. Do not
describe that manual action as Codex-validated or Codex-performed. A later
Codex prompt that depends on it must require the relevant current local or
remote state check and follow the normative AGENTS.md merge policy.

---

## 13. Compact Codex prompt template

### Prompt `<prompt_id>` — `<short_title>`

You are Codex working inside the user’s `correction-lib` workspace.

#### Optional distinct `goal`

```text
<include only when this adds information beyond the decision question>
```

#### Decision question

```text
<one question>
```

#### Metadata and governance

```text
prompt_id: <id>
short_title: <snake_case_title>
prompt_mode: <allowed mode>
preferred_codex_model: <model>
reasoning_level: <level>
delegation_policy: <policy>
model_selection_rationale: <brief rationale>

workspace_root: /users/apiccine/work/correction-lib
repo_locations:
  topeft: /users/apiccine/work/correction-lib/topeft
  topcoffea: /users/apiccine/work/correction-lib/topcoffea

allowed_to_modify: <exact surfaces>
read_only: <exact surfaces>

branch_policy: <allowed value>
validation_ceiling: <ceiling>

report_path: <absolute path>
patch_path: <absolute path>
patch_kind_expected: <kind>
```

Add `reference_branch` and `feature_branch` for branch creation, or
`target_branch` for an existing-branch round. Add an expected
`current_checked_out_branch` and baseline fields only when decision-material.
Add `do_not_commit: yes` only for an exact owner-authorized tracked-mutation
exception. Add explicit positive heavy permissions, `expanded_preflight`, an
alternative `dirty_worktree_policy`, `out_of_scope`, or exact commit-message
requirements when applicable. Add `preflight_scope_paths` when section 4
requires an explicit path set. The omitted ordinary values and inherited
prohibitions in section 4 still apply. Keep action-specific publication and
orchestrated-stage templates as written.

For `pr_publication`, append:

```text
publication_action: <action>
publication_platform: <github_or_gitlab>
publication_repository: <owner_or_namespace/repository>
publication_remote: <remote_name>
expected_local_head: <commit>
network_access: yes
remote_git_write: <yes_or_no>
pr_or_mr_write: <yes_or_no>
pr_or_mr_merge: <yes_or_no>
remote_branch_deletion: <yes_or_no>
force_push_allowed: no
merge_allowed: <yes_or_no>
```

For `publication_action: create_or_reuse_open_pr_or_mr`, also append:

```text
publication_base_branch: <branch>
publication_feature_branch: <branch>
duplicate_pr_or_mr_policy: reuse_exact_open_match_else_create_one
draft_allowed: no
pr_or_mr_write: yes
```

Require `remote_git_write: no` only for a fail-closed already-synchronized
path and `yes` only for one explicitly user-authorized possible normal
non-force explicit-refspec push. Require fresh advertised remote feature-head
comparison: equal means skip the push; mismatch with `yes` means push then read
back; mismatch with `no` means stop before mutation.

For `publication_action: synchronize_declared_remote_branch`, instead append:

```text
publication_local_branch: <branch>
publication_remote_branch: <branch>
publication_remote_tracking_ref: <remote_tracking_ref>
pr_or_mr_write: no
pr_or_mr_merge: no
remote_branch_deletion: no
force_push_allowed: no
merge_allowed: no
```

Use `remote_git_write: no` for exact live query/fetch only and `yes` only for
an explicitly user-authorized possible normal non-force push. Do not add
PR/MR-only fields to this branch-only action.

For `publication_action: normalize_declared_post_squash_staging_ref`, instead
append:

```text
exact_remote_ref: <refs/heads/exact_branch>
exact_observed_old_sha: <commit>
exact_target_sha: <commit>
verified_local_archive_ref: <exact_local_ref>
verified_remote_archive_ref_when_remote_history_is_being_rewritten: <exact_remote_ref>
archive_reachability: <required_evidence>
normalization_identity_basis: <tree_equivalence_or_other_explicit_basis>
force_with_lease_argument: --force-with-lease=<ref>:<exact_old_sha>
generic_force: forbidden
lease_refresh_after_unexplained_remote_movement: forbidden
post_write_remote_readback: required
final_expected_identity_readback: required
network_access: yes
remote_git_write: yes
pr_or_mr_write: no
pr_or_mr_merge: no
remote_branch_deletion: no
force_push_allowed: yes
merge_allowed: no
```

Require exact user authorization for the named ref rewrite. Do not add these
fields to other publication actions.

For `integration_only`, append:

```text
integration_source_branch: <local feature branch>
integration_target_branch: <local target branch>
integration_method: ff_only
expected_source_head: <commit>
network_access: no
remote_git_write: no
pr_or_mr_write: no
pr_or_mr_merge: no
remote_branch_deletion: no
force_push_allowed: no
```

For any non-fast-forward method, also require exact user authorization and the
declared resulting local-commit behavior.

For `branch_maintenance_only`, append:

```text
branch_maintenance_action: <one exact local lifecycle action>
affected_local_branches: <exact branch names>
expected_preserved_head: <commit_or_none_with_reason>
preservation_ref: <branch_or_ref_or_none_with_reason>
reference_restore_source: <authoritative_local_ref_or_commit_or_none_with_reason>
non_fast_forward_ref_move_authorized: <yes_or_no>
local_branch_deletion: no
remote_branch_deletion: no
```

For a non-fast-forward ref move, require exact user authorization, a
preservation/reachability proof before movement, fresh authoritative-ref and
reachability readback afterward, and exact direct Git commands. Do not use this
mode for rebase, reset, deletion, or history rewriting.

For `orchestrated_workflow`, append:

```text
workflow_goal: <one preauthorized workflow goal>
workflow_stages:
  - stage_id: <unique stage id>
    stage_mode: <allowed non-nested stage mode>
    stage_goal: <stage-local goal>
    stage_branch_policy: <applicable branch policy>
    stage_allowed_to_modify: <exact surfaces>
    stage_read_only: <exact surfaces>
    stage_permissions: <stage-local permissions>
    stage_preconditions: <observed gate inputs>
    stage_acceptance_gate: <objective pass condition>
    stage_outputs: <named observed outputs>
    stage_inputs_from_prior: <bindings_or_none>
    stage_on_failure: stop_remaining_stages
workflow_stop_policy: stop_on_failed_gate_or_new_decision_boundary
workflow_stage_ledger_path: <absolute compact ledger path>
```

Require mode-specific conditional fields inside each stage. Do not pool stage
permissions or preauthorize unknown future choices. Require read-back validated
output bindings, an observed-evidence ledger, explicit partial-completion
fields, and no automatic rollback. Exclude `production_execution` and nested
`orchestrated_workflow` stages. Permit `pr_publication` only with all
action-specific fields, stage-local permissions, validated transition evidence,
and explicit authorization; forbid `merge_existing_pr_or_mr`, generic force,
remote deletion, and automatic merge inside orchestration. Permit only the
exact force-with-lease form required by
`normalize_declared_post_squash_staging_ref`.

#### Inherited standing policy

Use compact references:

```text
- Follow AGENTS.md sections 2–8 for workspace, runtime capability, wrapper,
  modes, branches, and model policy.
- Follow AGENTS.md sections 9–13 for decision scope, permissions, remote Git,
  preflight, and dirty-state handling.
- Follow AGENTS.md sections 14–19 for commits, runtime consistency, validation,
  evidence integrity, and no-repeat rules.
- Follow AGENTS.md sections 20–25 for artifacts, diffs, reviewer-facing text,
  publication, merge, and final reporting.
- Follow CONTRIBUTING.md only for reviewer-facing material.
```

Read applicable nested `AGENTS.md` files and stop on conflict.

#### Accepted evidence and unresolved checks

For continuation rounds, always include `continuation_of`; include only the
non-empty state fields that apply:

```text
continuation_of: <prior_prompt_or_exact_artifact_set>

# only when prior evidence is reused
accepted_prior_evidence:
  - claim: <claim>
    artifact: <path>
    locator: <row_or_section>

# only when non-empty closure layers are reused
accepted_closure_layers:
  - <accepted_layer_and_evidence_reference>

# only when accepted evidence/closure is preserved outside a reopened boundary
invalidation_boundary:
  - <change_or_condition_that_reopens_accepted_evidence>

# when work is explicitly scoped relative to prior work
delta_scope:
  - <changed_newly_unresolved_or_directly_coupled_reachable_surface>

# only when unresolved checks are carried
unresolved_checks_only:
  - <check>

# only when accepted checks are protected from repetition
checks_not_to_repeat:
  - <accepted check>
```

#### Task-specific invariants

```text
must_be_true:
  - <safety invariant>

must_not_regress:
  - <protected behavior>

out_of_scope:
  - <exclusion>

stop_conditions:
  - <task-specific condition>
```

Do not put the desired audit conclusion in `must_be_true`.

#### Evidence or execution plan

```text
inspect:
  - <path_or_artifact>

evidence_to_collect_or_execution_steps:
  - <direct evidence or bounded execution>

evidence_validation:
  - <how serialized evidence is reopened and recomputed>

exact_commands:
  - <only safety-critical or semantically important direct commands>
```

For publication, require one direct command per remote operation and the
glados SSH override for Git-over-SSH.

#### Acceptance logic

State rules, not the expected outcome:

```text
acceptable_unchanged_claim:
  focused hashes match or focused diff is empty

acceptable_changed_claim:
  focused hunk, responsible commit, behavior, impact, and output evidence agree

acceptable_publication_claim:
  live remote readback proves the advertised feature head and exact PR/MR
  metadata required by the publication contract
```

For runtime tasks, provide objective output/readback criteria without
prescribing a pass.

#### Minimum deliverables

Require the mandatory report and patch plus only the task-specific artifacts
needed for the decision.

#### Final chat deliverable

Project the final chat from the canonical report as a compact actionable
summary. Include the verdict/status, direct decision answer, relevant
repository/branch/HEAD/commit identity, decisive validation/evidence result,
actual report directory and path, patch/artifact path and kind when produced,
remote/publication/merge/destructive effects when any, production/output
effects and paths when any, material blockers/caveats, and recommended next
action. Keep the canonical report as the full evidence record; a report path
alone is not a result handoff. `OPERATIVE_COMMANDS.md` is an input/launch
handoff.

Whenever an actual diagnostics directory exists, end the final response with
these exact two lines, using the exact actual directory and preserving any
`_rerun_00N` suffix:

```bash
FOLD=<exact actual diagnostics directory>
scp -r apiccine@glados.crc.nd.edu:${FOLD} .
```

Do not hide failure, blocked status, indeterminate identity, remote or
destructive effects, production/output paths, or material caveats. This is a
response projection only; do not change report requirements or schema.

For PR/MR publication or merge, also require:

```text
publication_repository
publication_base_branch
publication_feature_branch
published_head
pr_or_mr_number
pr_or_mr_url
pr_or_mr_state
merge_performed
remote_branch_deleted
```

For `synchronize_declared_remote_branch`, instead require:

```text
publication_repository
publication_remote
publication_local_branch
publication_remote_branch
expected_local_head
initial_live_remote_branch_head
final_live_remote_branch_head
remote_tracking_ref_head_after_fetch_when_applicable
remote_write_performed
force_push_used
pr_or_mr_write_performed
merge_performed
remote_branch_deleted
```

---

## 14. When to expand a prompt

Expand beyond the compact template only for genuinely independent constraints:

```text
production_execution_with_storage_or_submission_effects
multiple_independent_physics_policies
cross_repository_mutation
complex_dirty_worktree_separation
high_risk_installation_or_release
artifact_schema_whose_fields_are_the_actual_contract
publication_with_nontrivial_remote_state_or_multiple_authorized_writes
```

Expansion must follow independent decisions or risks, not the amount of
history available.

Even an expanded prompt must retain:

```text
one_authoritative_metadata_block
one_decision_question
accepted_evidence_references
minimum_sufficient_artifacts
no_expected_verdict
explicit_remote_permissions_when_applicable
```

---

## 15. CPC override syntax

Use a compact override block when needed:

```text
CPC overrides:
- preferred_codex_model: <model>
- reasoning_level: <level>
- delegation_policy: <policy>
- codex_cli_mode: <standard_or_ultra>
- allow_topcoffea_modifications: <yes_or_no>
- branch_policy: <policy>
- reference_branch: <branch_or_commit_when_applicable>
- target_branch: <branch_when_applicable>
- feature_branch: <branch_when_applicable>
- current_baseline_branch: <branch_when_decision_material>
- comparison_baseline: <reference_when_decision_material>
- do_not_commit: yes <only with exact owner authorization for tracked mutation>
- validation_ceiling: <ceiling>
- network_access: <yes_or_no>
- remote_git_write: <yes_or_no>
- pr_or_mr_write: <yes_or_no>
- pr_or_mr_merge: <yes_or_no>
- remote_branch_deletion: <yes_or_no>
- force_push_allowed: <yes_or_no>
- merge_allowed: <yes_or_no>
- xrootd_access: <yes_or_no>
- dbs_queries: <yes_or_no>
- condor_submission: <yes_or_no>
- work_queue_or_lobster_submission: <yes_or_no>
- storage_writes: <yes_or_no>
- large_pkl_production: <yes_or_no>
- plot_campaign: <yes_or_no>
- datacard_production: <yes_or_no>
- correction_payload_generation: <yes_or_no>
- payload_installation: <yes_or_no>
- package_installation: <yes_or_no>
- environment_mutation: <yes_or_no>
```

Include `dirty_worktree_policy` only for a requested alternative to
`require_clean_worktree`, and `preflight_profile` only for a requested
`expanded_preflight`. Supply the concrete value when either appears. No
override is implied by another.

---

## 16. Prompt-generation checklist

Before delivering a prompt, verify:

```text
one_decision_question
narrowest_prompt_mode
prompt_relationship_derived_from_continuation_of
goal_omitted_when_redundant_and_optional_when_distinct
model_reasoning_and_delegation_explicit
repo_permissions_explicit
branch_policy_explicit
live_applicable_feature_state_resolved_before_mutating_prompt
reuse_or_owner_exception_selected_from_zero_one_multiple_branches
new_nested_repository_branch_namespace_and_repository_facing_name_checked
unauthorized_parallel_branch_prompt_rejected_before_execution
dirty_policy_and_preflight_derived_or_explicit_when_exceptional
validation_ceiling_explicit
heavy_permissions_all_no_when_omitted_and_positive_grants_explicit
technical_network_availability_not_treated_as_authorization
remote_write_permissions_explicit_when_applicable
accepted_evidence_referenced_not_repeated
continuation_fields_nonempty_and_present_only_when_applicable
validation_delta_preserves_directly_coupled_reachable_surfaces
accepted_closure_layers_reopened_only_at_a_proven_invalidation_boundary
non_blocking_reporting_defect_does_not_spawn_standalone_round
only_unresolved_checks_scheduled
closed_checks_explicitly_not_repeated
no_expected_audit_or_publication_verdict
expected_values_limited_to_inputs_and_safety_invariants
evidence_collection_precedes_classification
anti_self_certification_rules_present_when_relevant
minimum_sufficient_artifacts
commit_expectation_derived_from_tracked_mutation_or_adoption
tracked_mutation_successful_closure_requires_prompt_local_commit_absent_exact_exception
do_not_commit_for_tracked_mutation_has_exact_owner_authorization
read_only_round_without_tracked_mutation_requires_no_commit
commit_ownership_classes_explicit_when_committing
staged_paths_and_diff_limited_to_owned_or_adopted_changes
exact_path_staging_and_complete_staged_diff_readback
foreign_staged_paths_removed_index_only_or_commit_stopped
report_and_patch_paths_explicit
absolute_report_directory_in_final_chat_when_report_is_produced
final_chat_deliverable_explicit
publication_mode_used_for_remote_publication
integration_contract_explicit_when_integration_only
ff_only_default_or_non_ff_user_authorization_explicit
branch_maintenance_contract_explicit_when_branch_maintenance_only
preservation_and_reachability_proven_before_ref_move
non_ff_ref_move_explicitly_authorized_when_applicable
orchestrated_workflow_contract_explicit_when_applicable
one_substantive_decision_boundary_across_all_stages
stage_modes_allowed_and_not_nested
stage_permissions_isolated_within_outer_envelope
stage_transition_requires_validated_observed_gate
semantic_completeness_proven_when_a_mutating_stage_consumes_a_prior_contract
prior_stage_bindings_use_read_back_outputs
new_decision_boundary_stops_remaining_stages
partial_completion_and_persistent_effects_reported
automatic_rollback_forbidden_by_default
orchestrated_publication_non_merge_and_stage_local
production_excluded_from_orchestration
glados_ssh_override_encoded_when_applicable
direct_network_commands_required
live_remote_state_queried
duplicate_pr_or_mr_guard_required_when_applicable
force_push_forbidden_by_default
merge_separately_authorized
remote_branch_deletion_separately_authorized
publication_readback_required
```

If a mandatory decision is inapplicable, state why.
