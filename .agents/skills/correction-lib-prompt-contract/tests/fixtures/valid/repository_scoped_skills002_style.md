# Prompt `SYNTHETIC_REPOSITORY_SCOPED` — repository-scoped branch contract

## Metadata and governance

```text
prompt_id: SYNTHETIC_REPOSITORY_SCOPED
short_title: repository_scoped_branch_contract
prompt_mode: coding
preferred_codex_model: gpt-5.6-terra
reasoning_level: high
delegation_policy: forbidden
model_selection_rationale: bounded repository-scoped synthetic fixture
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
branch_policy:
  meta_repo: continue_existing_branch
  topeft: read_only_current_branch
  topcoffea: read_only_current_branch
current_checked_out_branch:
  meta_repo: master
  topeft: run3_test_mmerged_anpicci
  topcoffea: run3_test_mmerged_anpicci
reference_branch:
  meta_repo: none
  topeft: none
  topcoffea: none
target_branch:
  meta_repo: master
  topeft: none
  topcoffea: none
feature_branch:
  meta_repo: none
  topeft: none
  topcoffea: none
current_baseline_branch:
  meta_repo: master
  topeft: current checked-out branch
  topcoffea: current checked-out branch
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
goal: implement one synthetic repository-scoped behavior
decision_question: can the repository-scoped synthetic behavior be implemented safely?
out_of_scope:
  - all real analysis and production
report_path: /tmp/correction_lib_prompt_contract/repository_scoped_report.md
patch_path: /tmp/correction_lib_prompt_contract/repository_scoped_diff.patch
patch_kind_expected: prompt_local
final_chat_deliverable:
  - synthetic implementation verdict
```
