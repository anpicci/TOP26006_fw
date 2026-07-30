# Prompt `<author_must_supply_prompt_id>` — `<author_must_supply_short_title>`

You are Codex working inside the user's `correction-lib` workspace.

## Goal

```text
<author_must_supply_one_precise_goal>
```

## Decision question

```text
<author_must_supply_one_decision_question>
```

## Metadata and governance

```text
prompt_id: <author_must_supply_prompt_id>
short_title: <author_must_supply_snake_case_title>
prompt_mode: <author_must_choose_live_prompt_mode>
preferred_codex_model: <author_must_choose_live_model>
reasoning_level: <author_must_choose_live_reasoning_level>
delegation_policy: <author_must_choose_delegation_policy>
model_selection_rationale: <author_must_supply_rationale>

workspace_root: <author_must_supply_workspace_root>
repo_locations:
  meta_repo: <author_must_supply_path_or_none_and_reason>
  topeft: <author_must_supply_path_or_none_and_reason>
  topcoffea: <author_must_supply_path_or_none_and_reason>
allowed_to_modify:
  <author_must_classify_every_writable_surface>
read_only:
  <author_must_classify_every_read_only_surface>

branch_policy:
  meta_repo: <author_must_choose_branch_policy_for_meta_repo>
  topeft: <author_must_choose_branch_policy_for_topeft>
  topcoffea: <author_must_choose_branch_policy_for_topcoffea>
current_checked_out_branch:
  meta_repo: <author_must_supply_branch_or_unknown_until_preflight>
  topeft: <author_must_supply_branch_or_unknown_until_preflight>
  topcoffea: <author_must_supply_branch_or_unknown_until_preflight>
reference_branch:
  meta_repo: <author_must_supply_value_or_none_and_reason>
  topeft: <author_must_supply_value_or_none_and_reason>
  topcoffea: <author_must_supply_value_or_none_and_reason>
target_branch:
  meta_repo: <author_must_supply_value_or_none_and_reason>
  topeft: <author_must_supply_value_or_none_and_reason>
  topcoffea: <author_must_supply_value_or_none_and_reason>
feature_branch:
  meta_repo: <author_must_supply_value_or_none_and_reason>
  topeft: <author_must_supply_value_or_none_and_reason>
  topcoffea: <author_must_supply_value_or_none_and_reason>
current_baseline_branch:
  meta_repo: <author_must_supply_value_or_none_and_reason>
  topeft: <author_must_supply_value_or_none_and_reason>
  topcoffea: <author_must_supply_value_or_none_and_reason>
comparison_baseline: <author_must_supply_value_or_none_and_reason>
integrated_baseline_mode: <author_must_choose_yes_or_no>

dirty_worktree_policy: <author_must_choose_dirty_worktree_policy>
preflight_profile: <author_must_choose_preflight_profile>
preflight_scope_paths:
  - <author_must_supply_bounded_path>
validation_ceiling: <author_must_choose_validation_ceiling>
heavy_command_permissions:
  defaults: <author_must_supply_explicit_policy>
  overrides:
    <author_must_supply_bounded_permissions_or_none>

source_control_policy: <author_must_supply_policy>
do_not_commit: <author_must_choose_yes_or_no>
commit_expected: <author_must_choose_yes_or_no>
commit_message_policy:
  <author_must_supply_complete_commit_contract>

goal: <author_must_supply_goal>
decision_question: <author_must_supply_decision_question>
out_of_scope:
  - <author_must_supply_exclusion>
report_path: <author_must_supply_absolute_report_path>
patch_path: <author_must_supply_absolute_patch_path>
patch_kind_expected: <author_must_choose_patch_kind>
final_chat_deliverable:
  <author_must_supply_required_fields>
```

The repository-scoped branch form above is the default for a multi-repository
prompt. A scalar branch contract remains supported when one policy applies to
the prompt as a whole; in that form, all six branch fields are scalars rather
than repository mappings. Authors must choose every scalar or repository value
explicitly.

## Inherited standing policy

Read and follow the live tracked `AGENTS.md`, `CPC.md`, and
`CONTRIBUTING.md`. Stop on conflict rather than guessing.

## Acceptance logic

```text
<author_must_supply_evidence_based_acceptance_logic_without_desired_verdict>
```
