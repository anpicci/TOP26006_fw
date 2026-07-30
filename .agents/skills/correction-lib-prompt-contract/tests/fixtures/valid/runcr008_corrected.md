# Prompt `RUNCR008_SYNTHETIC_CORRECTED` — corrected synthetic contract

## Metadata and governance

```text
prompt_id: RUNCR008_SYNTHETIC_CORRECTED
short_title: corrected_synthetic_contract
prompt_mode: coding
preferred_codex_model: gpt-5.6-terra
reasoning_level: high
delegation_policy: forbidden
model_selection_rationale: bounded synthetic coding fixture
workspace_root: /users/apiccine/work/correction-lib
repo_locations:
  meta_repo: /users/apiccine/work/correction-lib
  topeft: /users/apiccine/work/correction-lib/topeft
  topcoffea: /users/apiccine/work/correction-lib/topcoffea
allowed_to_modify:
  meta_repo: /tmp/synthetic_source.py
read_only:
  topeft: entire repository
  topcoffea: entire repository
branch_policy: continue_existing_branch
current_checked_out_branch: synthetic_branch
reference_branch: none, no new branch
target_branch: synthetic_branch
feature_branch: none, no new branch
current_baseline_branch: synthetic_branch
comparison_baseline: synthetic baseline
integrated_baseline_mode: yes
dirty_worktree_policy: allow_declared_preexisting_changes
preflight_profile: compact_preflight
preflight_scope_paths:
  - /tmp/synthetic_source.py
validation_ceiling: targeted_unit_test
heavy_command_permissions:
  defaults: all_no
  overrides: none
source_control_policy: inherit_AGENTS_defaults
do_not_commit: no
commit_expected: yes
commit_message_policy:
  format: conventional_commit
goal: implement one synthetic behavior
decision_question: can the synthetic behavior be implemented safely?
out_of_scope:
  - all real analysis and production
report_path: /tmp/correction_lib_prompt_contract/report.md
patch_path: /tmp/correction_lib_prompt_contract/diff.patch
patch_kind_expected: prompt_local
final_chat_deliverable:
  - synthetic implementation verdict
```
