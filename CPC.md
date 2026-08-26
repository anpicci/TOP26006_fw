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
`decision_question` safely and audibly.

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
current_checked_out_branch
reference_branch
target_branch
feature_branch
current_baseline_branch
comparison_baseline
integrated_baseline_mode

dirty_worktree_policy
preflight_profile
preflight_scope_paths
validation_ceiling
heavy_command_permissions

source_control_policy
do_not_commit
commit_expected
commit_message_policy

goal
decision_question
out_of_scope
report_path
patch_path
patch_kind_expected
final_chat_deliverable
```

For continuation rounds, also state:

```text
accepted_prior_evidence
unresolved_checks_only
checks_not_to_repeat
```

For evidence or audit rounds, also state:

```text
evidence_requirements
classification_rules
anti_self_certification_rules
evidence_validation_method
```

For `pr_publication`, also state:

```text
publication_action
publication_platform
publication_repository
publication_remote
publication_base_branch
publication_feature_branch
expected_local_head
network_access
remote_git_write
pr_or_mr_write
pr_or_mr_merge
remote_branch_deletion
duplicate_pr_or_mr_policy
force_push_allowed
merge_allowed
draft_allowed
```

Required publication defaults:

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

If a field is intentionally inapplicable, state `none` and why.

---

## 5. Model, reasoning, and delegation selection

Declare model, reasoning, and delegation separately.

Reports and prompts must keep model selection separate from model
observability. Record `preferred_or_configured_model`,
`directly_selected_model_if_observable`,
`runtime_reported_model_label_if_observable`, and `fallback_or_switch` when
applicable. An unavailable exact status-line label is reported honestly and is
not itself a blocker; do not infer an exact model from a generic family label.

Suggested defaults:

```text
simple documentation or formatting:
  gpt-5.6-luna medium

narrow read-only inspection:
  gpt-5.6-luna high or gpt-5.6-terra medium

structured validation or production:
  gpt-5.6-terra high

ordinary bounded coding:
  gpt-5.6-terra high

ambiguous cross-file or cross-repository coding:
  gpt-5.6-sol high

physics-policy interpretation or difficult architecture:
  gpt-5.6-sol high or xhigh

deep open-ended archaeology:
  gpt-5.6-sol max
```

Rules:

* Do not use Sol merely because a task is important.
* Do not rely on CLI defaults for serious work.
* Do not use Luna `max` to compensate for model fit.
* Use `xhigh` or `max` only when necessary.
* Preserve scope when falling back and record the switch.

Encode Ultra only when explicitly authorized:

```text
reasoning_level: max
delegation_policy: allowed_or_required
codex_cli_mode: ultra
```

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
pr_publication
production_execution
```

Use the narrowest mode that permits the work.

* `investigation_only`: read-only diagnosis and evidence work.
* `coding`: tracked implementation/test/config changes.
* `validation_only`: bounded runtime validation without source edits.
* `test_alignment_only`: stale-test changes only after runtime intent is proven.
* `documentation_only`: tracked documentation changes.
* `commit_preparation`: stage and commit intended existing changes.
* `pr_preparation`: reviewer-facing text only.
* `pr_publication`: publish an already validated branch, create/update the
  requested PR/MR, or perform a separately authorized merge round.
* `production_execution`: production-like or heavy commands.

Do not combine `pr_publication` with source editing, new commits, history
rewriting, force push, remote deletion, or merge unless the exact action is the
single explicit decision and separately authorized.

---

## 7. Branch policy

Every prompt must declare one of:

```text
create_feature_branch_from_reference
continue_existing_branch
read_only_current_branch
commit_preparation_on_existing_branch
```

New coding work defaults to `create_feature_branch_from_reference`.
Continuation work names the existing `target_branch`. Read-only work normally
uses `read_only_current_branch`. Commit preparation uses
`commit_preparation_on_existing_branch`.

For a prompt that will make tracked source, test, configuration, or
documentation changes, resolve live branch state for the declared workstream
before modification. If an applicable active feature branch exists, require
`continue_existing_branch`; otherwise require
`create_feature_branch_from_reference`. Reject direct development on the
declared reference or integration branch and creation of a parallel active
feature branch for the same workstream unless the user explicitly authorizes a
reported split or supersession. Do not use a second branch-state registry or
parallel branch-governance framework.

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

* One prompt normally answers one decision question.
* Separate implementation closure, history review, campaign qualification,
  derivation, installation, PR preparation, publication, and merge.
* Do not include an expected successful conclusion for investigation,
  validation, audit, or publication.
* Expected values are allowed only for immutable inputs and safety invariants.
* Do not prescribe zero failures for checks designed to discover failures.
* Define evidence-based acceptance rules instead.

---

## 9. Continuation prompts and accepted evidence

Use compact exact references:

```text
accepted_prior_evidence:
  - claim: <already established claim>
    artifact: <exact path>
    locator: <row, key, or section>

unresolved_checks_only:
  - <genuinely unresolved check>

checks_not_to_repeat:
  - <accepted check>
```

Do not reproduce whole reports or long summaries.

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
exact_goal_and_decision_question
accepted_evidence
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

For publication, normally require only:

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

A branch-publication round must normally declare:

```text
network_access: yes
remote_git_write: yes
pr_or_mr_write: yes
pr_or_mr_merge: no
remote_branch_deletion: no
force_push_allowed: no
merge_allowed: no
draft_allowed: no
```

### 12.1 glados Git-over-SSH rule

For Git-over-SSH from Codex on glados, require direct Git commands executed
from the target repository working directory using:

```bash
git \
  -c core.sshCommand='/usr/bin/ssh -F /dev/null' \
  <subcommand> ...
```

This bypasses only the sandbox-rejected system SSH configuration for the
current command.

Do not request:

```text
git -C for publication commands
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

Require the applicable AGENTS.md publication sequence in the prompt. Encode
each network operation as a separate direct command, exact local branch/HEAD
and tracked/index checks, live base and feature-head readback, duplicate-PR/MR
checks before and after push, and final PR/MR metadata readback. Retain only
the following concise direct-command examples in the prompt when Git-over-SSH
is used:

Canonical live-base query:

```bash
git \
  -c core.sshCommand='/usr/bin/ssh -F /dev/null' \
  ls-remote \
  <remote> \
  refs/heads/<base_branch>
```

Canonical normal push:

```bash
git \
  -c core.sshCommand='/usr/bin/ssh -F /dev/null' \
  push \
  <remote> \
  refs/heads/<feature_branch>:refs/heads/<feature_branch>
```

Never include:

```text
--force
--force-with-lease
wildcard refspecs
implicit multi-ref pushes
remote branch deletion
automatic merge
```

unless the exact action is separately authorized. Push or creation stdout alone
is insufficient; the prompt must require live remote readback.

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

When a match exists, do not create another PR/MR. Read it back and report it.
Repeat the duplicate check after push and before creation to guard against a
race.

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

When Codex is authorized to merge, require a separate `pr_publication` round
with one decision question and:

```text
publication_action: merge_existing_pr_or_mr
pr_or_mr_merge: yes
merge_allowed: yes
```

Require immediate pre-merge readback of:

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

#### Goal

```text
<one precise testable sentence>
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
current_checked_out_branch: <expected or unknown_until_preflight>
reference_branch: <reference or none>
target_branch: <target or none>
feature_branch: <feature or none>
current_baseline_branch: <baseline or none>
comparison_baseline: <reference or none>
integrated_baseline_mode: <yes_or_no>

dirty_worktree_policy: <policy>
preflight_profile: compact_preflight
preflight_scope_paths:
  - <task path>
validation_ceiling: <ceiling>

source_control_policy: inherit_AGENTS_defaults
do_not_commit: <yes_or_no>
commit_expected: <yes_or_no>
commit_message_policy:
  format: <format_or_none>
  prompt_ids_allowed: no
  codex_jargon_allowed: no
  internal_workflow_labels_allowed: no

heavy_command_permissions:
  defaults: all_no
  overrides: <bounded yes entries or none>

report_path: <absolute path>
patch_path: <absolute path>
patch_kind_expected: <kind>
```

For `pr_publication`, append:

```text
publication_action: <action>
publication_platform: <github_or_gitlab>
publication_repository: <owner_or_namespace/repository>
publication_remote: <remote_name>
publication_base_branch: <branch>
publication_feature_branch: <branch>
expected_local_head: <commit>
network_access: yes
remote_git_write: <yes_or_no>
pr_or_mr_write: <yes_or_no>
pr_or_mr_merge: <yes_or_no>
remote_branch_deletion: <yes_or_no>
duplicate_pr_or_mr_policy: reuse_exact_open_match_else_create_one
force_push_allowed: no
merge_allowed: <yes_or_no>
draft_allowed: no
```

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

For continuation rounds:

```text
accepted_prior_evidence:
  - claim: <claim>
    artifact: <path>
    locator: <row_or_section>

unresolved_checks_only:
  - <check>

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

```text
final_status
decision_question
derived_verdict
branch_and_head
files_changed
commit_hash
validation_or_evidence_results
report_path
report_directory: <absolute parent directory when a report is produced>
patch_path
patch_kind
generated_outputs
unresolved_findings
recommended_next_action
final_cleanliness
```

For publication or merge, also require:

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
- reference_branch: <branch_or_commit>
- target_branch: <branch_or_none>
- feature_branch: <branch_or_none>
- current_baseline_branch: <branch_or_none>
- comparison_baseline: <reference_or_none>
- do_not_commit: <yes_or_no>
- dirty_worktree_policy: <policy>
- preflight_profile: <profile>
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

No override is implied by another.

---

## 16. Prompt-generation checklist

Before delivering a prompt, verify:

```text
one_decision_question
narrowest_prompt_mode
model_reasoning_and_delegation_explicit
repo_permissions_explicit
branch_policy_explicit
dirty_policy_and_preflight_explicit
validation_ceiling_explicit
heavy_permissions_explicit
technical_network_availability_not_treated_as_authorization
remote_write_permissions_explicit_when_applicable
accepted_evidence_referenced_not_repeated
only_unresolved_checks_scheduled
closed_checks_explicitly_not_repeated
no_expected_audit_or_publication_verdict
expected_values_limited_to_inputs_and_safety_invariants
evidence_collection_precedes_classification
anti_self_certification_rules_present_when_relevant
minimum_sufficient_artifacts
commit_expectation_explicit
report_and_patch_paths_explicit
absolute_report_directory_in_final_chat_when_report_is_produced
final_chat_deliverable_explicit
publication_mode_used_for_remote_publication
glados_ssh_override_encoded_when_applicable
direct_network_commands_required
live_remote_state_queried
duplicate_pr_or_mr_guard_required
force_push_forbidden_by_default
merge_separately_authorized
remote_branch_deletion_separately_authorized
publication_readback_required
```

If a mandatory decision is inapplicable, state why.

---

## 17. Prompt-preflight lifecycle policy

The following lifecycle state is normative:

```text
correction-lib-codex-prompt-preflight:
  lifecycle_status: experimental_paused
  qualification_status: unqualified
  operational_mode: advisory_only
  automatic_invocation: disabled
  authorization_effect: none
  persistent_readiness_authority: none
  live_qualification: cancelled
```

SKILLS012 through SKILLS014 remain archived design and implementation evidence.
Version 1.1.0 may remain installed for possible future study, but its output,
exit status, canonical Markdown, reports, hashes, audit artifacts, and any
historical readiness concept must not gate or authorize normal correction-lib
work. No claim is made that SKR-1.0 or BB-1.2 is fully implemented or qualified,
and BB023 and BB025 will not be run under this paused plan.

Invoke prompt-preflight only when the user explicitly requests its development,
investigation, regression study, or advisory validation. Resuming enforcement
or qualification requires an explicit new user decision and a fresh scoped
baseline. This section adds no replacement authorization or security engine.

The `correction-lib-prompt-contract` validator remains a separate mechanical
validator for structured governance prompts. A successful result validates
structure only and does not authorize repository work. Normal authorization
comes from the current visible user instruction, applicable repository
governance, and explicit tool permissions available to the current Codex
session.
