# Prompt `FIXTURE001` — `base_fixture`

## Task metadata

```text
prompt_id: FIXTURE001
short_title: base_fixture
prompt_mode: coding
preferred_codex_model: gpt-5.6-terra
reasoning_level: high
delegation_policy: forbidden
model_selection_rationale: bounded synthetic skill test
allowed_to_modify:
  meta_repo: /tmp/sentinel_scope
read_only:
  topeft: branch and HEAD only
  topcoffea: branch and HEAD only
branch_policy:
  meta_repo: continue_existing_branch
  topeft: read_only_current_branch
  topcoffea: read_only_current_branch
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
comparison_baseline: sentinel_baseline_0123456789abcdef
integrated_baseline_mode: yes
dirty_worktree_policy: allow_declared_preexisting_changes
preflight_profile: compact_preflight
preflight_scope_paths:
  - /tmp/sentinel_scope
validation_ceiling: targeted_unit_test
heavy_command_permissions:
  defaults: all_no
source_control_policy: inherit live AGENTS defaults
do_not_commit: no
commit_expected: yes
commit_message_policy:
  exact_subject: feat(governance): sentinel subject
goal: preserve every authored sentinel
decision_question: Can the synthetic prompt reach readiness without changing semantics?
out_of_scope:
  - all real task execution
patch_kind_expected: prompt_local
```

## Goal

````text
  Sentinel whitespace stays here.

```python
print("inert")
```
````

## Acceptance

The sentinel path, branch, commit, subject, whitespace, and code block remain unchanged.
