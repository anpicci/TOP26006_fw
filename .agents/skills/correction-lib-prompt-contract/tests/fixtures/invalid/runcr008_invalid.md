# Prompt `RUNCR008_SYNTHETIC_INVALID` — blocked synthetic contract

## Metadata and governance

```text
prompt_id: RUNCR008_SYNTHETIC_INVALID
short_title: blocked_synthetic_contract
prompt_mode: coding_implementation
preferred_codex_model: gpt-5.6-terra
reasoning_level: high
delegation_policy: forbidden
model_selection_rationale: bounded synthetic fixture
workspace_root: /users/apiccine/work/correction-lib
repo_locations:
  meta_repo: /users/apiccine/work/correction-lib
allowed_to_modify:
  meta_repo: /tmp/synthetic_source.py
read_only:
  nested_repositories: all
branch_policy: continue_existing_branch
current_checked_out_branch: synthetic_branch
reference_branch: none
target_branch: synthetic_branch
feature_branch: none
current_baseline_branch: synthetic_branch
comparison_baseline: synthetic baseline
integrated_baseline_mode: yes
dirty_worktree_policy: allow_dirty
preflight_profile: compact_preflight
preflight_scope_paths:
  - /tmp/synthetic_source.py
validation_ceiling: targeted_unit_test
heavy_command_permissions:
  defaults: all_no
source_control_policy: inherit_AGENTS_defaults
do_not_commit: no
commit_expected: yes
commit_message_policy:
  format: conventional_commit
goal: synthetic blocked round
out_of_scope:
  - all real analysis and production
report_path: /tmp/correction_lib_prompt_contract/report.md
patch_path: /tmp/correction_lib_prompt_contract/diff.patch
patch_kind_expected: prompt_local
final_chat_deliverable:
  - synthetic verdict
```
