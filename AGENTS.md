# AGENTS.md — `correction-lib` Codex operating policy

This workspace coordinates two independent Git repositories:

```text
topeft/     analysis code, processors, selections, workflow helpers, CLIs
topcoffea/  shared libraries, object selection, corrections, weights, utilities
```

The workspace root also contains governance, reports, diagnostics, and patch
artifacts. Never treat the two inner repositories as one Git repository.

---

## 0. Policy precedence

1. `AGENTS.md` controls execution, repository permissions, branch behavior,
   Git hygiene, validation, artifacts, commits, remote publication, and merge
   authorization.
2. `CPC.md` controls how ChatGPT constructs Codex prompts.
3. `CONTRIBUTING.md` controls PR/MR titles, descriptions, squash messages,
   reviewer notes, validation language, and other reviewer-facing prose.
4. A user instruction overrides these files only when explicit.
5. On conflict, stop and report the conflict. Do not guess.

Read every applicable nested `AGENTS.md` before acting and list the files read
in the report.

---

## 1. Core operating principles

Apply these rules unless the prompt explicitly overrides them:

```text
one_round_one_decision
minimum_sufficient_scope
evidence_before_verdict
accepted_evidence_is_reused_not_repeated
small_auditable_reversible_changes
no_silent_scope_expansion
no_unrequested_cleanup
no_compatibility_shims_by_default
one_writing_agent_per_file_surface
snake_case_for_new_local_names
technical_capability_is_not_task_authorization
remote_writes_require_explicit_permission
```

More specifically:

* Every round must have one explicit `decision_question`.
* Include only the context, checks, permissions, and artifacts needed to answer
  that question.
* Do not encode the desired answer as an expected result.
* Expected values may describe immutable inputs or safety invariants, not the
  verdict an audit is meant to determine.
* Collect and serialize direct evidence before classifications or verdicts.
* Prefer a smaller proven claim over a broader weakly supported claim.
* Filenames, branch names, output labels, and prompt names are not runtime
  evidence.
* Before adding persistent state, a registry, cache, compatibility bridge, or
  helper framework, first delete duplicated state, derive locally from the
  authoritative state, or reuse the existing owner. Add persistent state only
  for a demonstrated failure, and record the failure prevented, why local
  derivation and the existing owner are insufficient, its consistency or
  invalidation contract, and the simpler fail-closed alternative considered.
* Use `snake_case` for new helper names, functions, variables, report fields,
  prompt fields, and local scripts unless an existing API requires otherwise.
* Coding and tracked-documentation work normally ends in a prompt-local commit
  unless `do_not_commit: yes` is explicit.
* Available network access, credentials, executables, or remotes are technical
  capabilities only. The prompt must authorize each network capability and
  remote mutation separately.

---

## 2. Workspace and repository boundaries

Expected paths:

```text
workspace_root: /users/apiccine/work/correction-lib
topeft:        /users/apiccine/work/correction-lib/topeft
topcoffea:     /users/apiccine/work/correction-lib/topcoffea
```

`workspace_root` is also a distinct local Git meta-repository. It is the
authoritative source-control owner of this workspace's governance files:

```text
AGENTS.md
CPC.md
CONTRIBUTING.md
```

`topeft/` and `topcoffea/` remain independent nested Git repositories; root
ownership of governance does not combine them into one source-control unit.
Root-level Git operations must not stage nested repositories, unrelated root
artifacts, reports, backups, payloads, or local tools without explicit
authorization. Initial and later governance commits stage the intended
governance files by exact path only.

Treat each repository independently for:

```text
branch state
cleanliness
diffs
commits
tests
reports
remote refs
PR or MR preparation
PR or MR publication
merge readiness
```

Every prompt must declare:

```text
allowed_to_modify
read_only
```

Default when not explicitly overridden:

```text
topeft: writable
topcoffea: read_only
```

A read-only repository must not be modified. If a cross-repository change is
necessary but not authorized, stop before editing and include:

```text
cross_repo_escalation_note
```

Do not add a shim merely to avoid the repository boundary.

---

## 3. Codex runtime capability and approvals

The expected user-level Codex runtime is:

```text
sandbox_mode: workspace-write
network_access_technically_available: yes
approval_policy: on-request
approvals_reviewer: user
```

A publication-specific profile is not required. The ordinary Codex session
supports investigation, coding, validation, and bounded publication under the
same workspace-write sandbox.

This configuration provides capability only. It does not override this policy
or the current prompt.

Rules:

* Network use requires `network_access: yes`.
* A normal non-force Git push requires `remote_git_write: yes`.
* PR/MR creation or update requires `pr_or_mr_write: yes`.
* PR/MR merge requires `pr_or_mr_merge: yes`.
* Remote branch deletion requires `remote_branch_deletion: yes`.
* Force push requires explicit user authorization and
  `force_push_allowed: yes`.
* Network reads do not imply writes.
* Publication does not imply merge.
* Merge does not imply remote branch deletion.
* A CLI approval does not replace prompt-level authorization.

When a task depends on network access or remote mutation, record the effective
sandbox and approval mode during preflight. If the required capability is
unavailable, stop and classify the blocker; do not weaken the sandbox or edit
user configuration.

Do not edit `~/.codex/config.toml`, `~/.codex/rules`, or shell startup files
unless the prompt explicitly requests configuration work.

---

## 4. Wrapper and shell policy

Every Python, pytest, compileall, correctionlib, NanoEvents, pkl-inspection, or
diagnostic Python command must use:

```bash
/users/apiccine/work/correction-lib/codex-run.sh
```

Canonical pattern:

```bash
wrap=/users/apiccine/work/correction-lib/codex-run.sh
python_env=/users/apiccine/work/miniconda3/envs/clib-env/bin/python

"$wrap" /bin/bash --noprofile --norc -c \
  'cd /users/apiccine/work/correction-lib/topeft && "$python_env" -m pytest -q'
```

Never use a login shell:

```bash
"$wrap" bash -lc '...'
```

Never invoke the pinned Python directly outside the wrapper.

`codex-run.sh` is infrastructure. Do not edit it unless explicitly requested.
A wrapper-change report must include `sys.executable`, `sys.path`, and NumPy
import/version checks.

### Direct-command exception for remote operations

Run `git`, `gh`, and `glab` network operations as separate direct commands.
Do not place them inside:

```text
login shells
nested shell wrappers
env wrappers
heredocs
large compound scripts
command substitutions that hide the external operation
combined control-flow blocks
```

Use the command working directory to select the repository rather than a
`cd ... && ...` wrapper.

---

## 5. Environment policy

Never mutate the software environment. Forbidden commands include:

```text
conda install
conda update
conda create
pip install
pip uninstall
mamba
apt-get
```

When an environment change is needed, report the reason and exact user-run
command. Do not execute it.

Pinned interpreter:

```text
/users/apiccine/work/miniconda3/envs/clib-env/bin/python
```

Use it only through the wrapper.

Do not persistently modify authentication files, credential helpers, SSH
configuration, or shell startup files unless explicitly requested.

---

## 6. Prompt modes

Every prompt must declare one `prompt_mode`:

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

### `investigation_only`

Allowed: inspection, reproduction, measurements, evidence extraction, reports,
and diagnostic artifacts.

Forbidden: tracked source/test edits, commits, fixes, cleanup, and remote
mutation.

### `coding`

Allowed: minimum source/test/config/doc changes, focused regression coverage,
validation, and a prompt-local commit.

Forbidden: unrelated refactors, speculative redesign, and uncommitted
prompt-local tracked changes unless `do_not_commit: yes`.

### `validation_only`

Allowed: bounded diagnostics, approved workflow runs, pkl inspection, plotting
checks, and reports.

Forbidden: tracked source/test edits, commits, and remote mutation.

### `test_alignment_only`

Allowed only when direct evidence proves the runtime contract is intentional
and tests are stale. If runtime intent is ambiguous, stop.

### `documentation_only`

Allowed when behavior is established and only tracked documentation changes.
Commit unless `do_not_commit: yes`.

### `commit_preparation`

Allowed: inspect intended dirty state, run bounded verification, stage explicit
paths, create logical commits, and produce report/patch artifacts.

Forbidden: runtime changes, unrelated staging, history rewriting, reset, clean,
or stash unless explicitly authorized.

### `pr_preparation`

Allowed: prepare PR/MR title, description, squash message, reviewer notes, and
other reviewer-facing text from established evidence.

Forbidden: code changes, commits, pushes, PR/MR creation or update, merge, and
remote deletion.

### `pr_publication`

Allowed: bounded live remote inspection, a normal non-force branch push, and
creation or update of one explicitly declared PR/MR using already validated
commits and reviewer-facing material.

Required permissions for branch publication and PR/MR creation:

```text
network_access: yes
remote_git_write: yes
pr_or_mr_write: yes
pr_or_mr_merge: no
remote_branch_deletion: no
force_push_allowed: no
merge_allowed: no
```

Forbidden unless separately authorized:

```text
source or test edits
new commits
amend
rebase
history rewriting
force push
remote branch deletion
automatic merge
PR or MR merge
```

A publication round must:

1. verify local repository, branch, HEAD, and tracked/index state;
2. verify remote identity and repository permission;
3. query the live remote base;
4. query for an existing matching open PR/MR;
5. push with an explicit non-force refspec;
6. verify the advertised remote feature HEAD;
7. repeat the duplicate query to handle races;
8. create at most one non-draft PR/MR when none exists;
9. query the created or existing PR/MR back;
10. verify repository, base, head, head commit, title, state, and draft status;
11. recheck local tracked/index state.

Merge must be a separate decision round with `pr_or_mr_merge: yes` and
`merge_allowed: yes`.

### `production_execution`

Required for production-like or heavy execution. Every capability must be
explicitly authorized. One production permission does not imply another.

---

## 7. Branch policy

Every prompt must declare one branch policy per relevant repository:

```text
create_feature_branch_from_reference
continue_existing_branch
read_only_current_branch
commit_preparation_on_existing_branch
```

### `create_feature_branch_from_reference`

Use for new coding work by default. Declare `reference_branch` and
`feature_branch`, verify the reference, record its HEAD, create/switch to the
feature branch, and report the merge base.

### `continue_existing_branch`

Declare `target_branch`. Work directly on it and create no additional branch.

### `read_only_current_branch`

Inspect or publish the current branch without local editing, committing, or
switching. Remote mutation still requires explicit publication permissions.

### `commit_preparation_on_existing_branch`

Prepare commits from intended existing changes on the declared branch. Do not
rewrite, clean, reset, stash, or include unrelated files.

### Development branch lifecycle

Before tracked source, test, configuration, or documentation work, resolve the
live branch and workstream state. When an applicable active feature branch
exists, continue it; otherwise create the declared feature branch from the
verified reference before the first development commit. A declared reference or
integration branch is a baseline, not a development surface: do not accumulate
new development commits directly on it or create a parallel active feature
branch for the same workstream merely for convenience. A split, supersession,
or other deviation requires explicit user authorization and must be reported
before modification; otherwise stop with a branch-policy blocker. Do not
automatically rewrite historical commits that predate this rule.

Required branch fields when applicable:

```text
current_checked_out_branch
reference_branch
target_branch
feature_branch
current_baseline_branch
comparison_baseline
integrated_baseline_mode
```

If branch behavior is missing or ambiguous, stop and include:

```text
branch_escalation_note
```

When `integrated_baseline_mode: yes`, treat the declared integration branch as
current source of truth and do not reopen historical feature branches unless
explicitly requested.

Remote branch commits are live state. Query them when current values matter;
do not reuse an old remote SHA as current-state evidence.

---

## 8. Model, reasoning, and delegation

Every prompt must declare:

```text
preferred_codex_model
reasoning_level
delegation_policy
model_selection_rationale
```

Supported model labels:

```text
gpt-5.6-luna
gpt-5.6-terra
gpt-5.6-sol
explicit_fallback
```

Reasoning levels:

```text
low
medium
high
xhigh
max
```

Delegation:

```text
forbidden
allowed
required
```

Default guidance:

```text
simple mechanical work:                     luna medium
narrow read-only evidence extraction:       luna high or terra medium
structured validation or production:        terra high
ordinary bounded coding:                    terra high
ambiguous cross-file or cross-repo coding:  sol high
physics-policy or difficult architecture:   sol high or xhigh
deep open-ended archaeology:                sol max
```

Do not use Sol merely because a task is important. Do not compensate for an
undersized model with excessive reasoning. Reports must distinguish:

```text
preferred_or_configured_model
directly_selected_model_if_observable
runtime_reported_model_label_if_observable
fallback_or_switch
```

An unavailable exact status-line model label is not by itself a blocker. Record
that limitation honestly; do not infer an exact model from a generic family
label. Record an observed fallback or switch when one occurred.

`Ultra` is an orchestration mode, not a reasoning level. Encode it only when
explicitly authorized:

```text
reasoning_level: max
delegation_policy: allowed_or_required
codex_cli_mode: ultra
```

Do not use Ultra for narrow controlled work, commit preparation, publication,
or production execution.

---

## 9. Decision-focused task contracts

Every round must state:

```text
decision_question
accepted_prior_evidence
unresolved_checks_only
checks_not_to_repeat
```

The last three fields are required for continuation rounds.

Rules:

* One round normally answers one decision question.
* Cite prior evidence by exact artifact and locator instead of copying reports.
* Do not rerun accepted checks unless source/input changed, evidence is missing
  or invalid, or the user requests it.
* Do not combine implementation closure, archaeology, production,
  publication, merge, and campaign planning in one round.
* Do not create artifacts that do not support the decision.
* Besides the mandatory report and patch, default to no more than five
  task-specific artifacts.
* Do not prescribe expected zero-failure counts for discovery-oriented audits.

Preferred evidence order:

```text
collect_direct_evidence
serialize_evidence
reopen_and_validate_evidence
classify_evidence
derive_verdict
```

---

## 10. Multi-agent policy

Use multiple agents only when delegation is allowed and work separates cleanly.

Preferred lanes:

```text
evidence_lane
fix_lane
validation_lane
```

Rules:

* Read-only lanes may run in parallel.
* Use one writing agent per repository/file surface.
* Do not run overlapping writing agents.
* Report which lane diagnosed, changed, validated, and committed.
* Avoid multi-agent overhead for small tasks.
* One controlling agent must execute publication operations sequentially. Do
  not parallelize duplicate checks, pushes, PR/MR creation, merge, or deletion.

---

## 11. Command and capability permissions

Lightweight local read-only commands are allowed by default, including:

```text
pwd
ls
rg
grep
cat
head
tail
sed
awk
find with bounded paths
git status
git diff
git log
git show
git rev-parse
git merge-base
git branch
sha256sum
```

Every prompt must declare:

```text
heavy_command_permissions:
  defaults: all_no
  overrides: ...
```

Capabilities requiring explicit `yes` include:

```text
network_access
remote_git_write
pr_or_mr_write
pr_or_mr_merge
remote_branch_deletion
xrootd_access
dbs_queries
cmssw_setup
scram_build
condor_submission
work_queue_or_lobster_submission
storage_writes
large_pkl_production
plot_campaign
datacard_production
correction_payload_generation
payload_installation
package_installation
environment_mutation
```

Permission meanings:

```text
network_access:
  bounded outbound network use described by the prompt, including read-only
  API requests and remote-ref inspection

remote_git_write:
  normal non-force push of explicitly declared refs

pr_or_mr_write:
  create or update the explicitly declared PR or MR

pr_or_mr_merge:
  merge or squash-and-merge the explicitly declared PR or MR

remote_branch_deletion:
  delete the explicitly declared remote branch
```

No permission is implied by another. `network_access: yes` does not authorize
push, PR/MR writes, merge, deletion, installation, submission, or storage
writes.

Never run `git fetch` unless explicitly authorized. Never use `git pull` in a
publication round.

---

## 12. Remote Git and publication policy on glados

The Codex workspace-write sandbox on glados exposes the system SSH
configuration with remapped ownership. OpenSSH therefore rejects:

```text
/etc/ssh/ssh_config.d/50-redhat.conf
```

even though the host file has correct ownership and permissions.

For Git-over-SSH commands executed by Codex on glados, run from the target
repository working directory and use the command-scoped override:

```bash
git \
  -c core.sshCommand='/usr/bin/ssh -F /dev/null' \
  <git_subcommand> ...
```

Do not persist this override. Do not modify:

```text
/etc/ssh files
~/.ssh/config
repository remotes
global Git configuration
repository core.sshCommand
system file permissions or ownership
```

Canonical read-only query:

```bash
git \
  -c core.sshCommand='/usr/bin/ssh -F /dev/null' \
  ls-remote \
  <remote> \
  refs/heads/<branch>
```

Canonical publication push:

```bash
git \
  -c core.sshCommand='/usr/bin/ssh -F /dev/null' \
  push \
  <remote> \
  refs/heads/<local_branch>:refs/heads/<remote_branch>
```

Rules:

* Execute Git, `gh`, and `glab` network operations as separate direct commands.
* Use the command working directory rather than `git -C` for publication
  commands so the canonical approval rule remains matchable.
* Use the override for both `ls-remote` and push.
* Never use `--force`, `--force-with-lease`, wildcard refspecs, implicit
  multi-ref pushes, or deletion unless explicitly authorized.
* Do not change an SSH remote to HTTPS merely to bypass the sandbox.
* Do not infer invalid credentials from DNS, socket, sandbox, SSH-config, or
  pre-spawn failures.
* Query live remote refs during publication. Recorded SHAs are historical
  evidence, not current-state evidence.

Use separate commands for:

```text
identity and authentication check
repository permission check
live base resolution
initial duplicate PR or MR check
reviewer-material validation
branch push
remote feature HEAD verification
post-push duplicate check
PR or MR creation or update
PR or MR readback
final local-state check
```

Failure classifications:

```text
blocked_network_execution:
  the command could not reach the remote, or execution was rejected before the
  remote service returned an authentication or authorization decision

blocked_authentication:
  the remote service explicitly rejected authentication

blocked_permission:
  authentication succeeded, but repository authorization was insufficient

blocked_remote_state:
  live refs, duplicate PR/MR state, or another remote invariant made the
  operation unsafe

blocked_local_state:
  local branch, HEAD, cleanliness, evidence, or reviewer material did not match
  the publication contract
```

---

## 13. Preflight and dirty-worktree policy

Every prompt must declare:

```text
preflight_profile
dirty_worktree_policy
preflight_scope_paths
```

Allowed profiles:

```text
compact_preflight
expanded_preflight
```

### `compact_preflight`

Default for known repositories and bounded tasks. Record only:

```text
repository path
current branch
HEAD
required reference commits
merge-base or ancestry checks needed by the task
staged changes in task-scope paths
unstaged changes in task-scope paths
task-scope untracked collisions
unique artifact checksums or existence checks
```

Do not dump unrelated untracked inventories.

For publication, also record:

```text
configured publication remote
local feature branch
expected local feature HEAD
tracked/index cleanliness
reviewer material paths and checksums
```

### `expanded_preflight`

Use only when branch identity is uncertain, dirty state is broad and relevant,
artifact collision risk is high, or explicitly required. State why.

Allowed dirty policies:

```text
require_clean_worktree
work_on_dirty_branch_as_is
allow_declared_preexisting_changes
commit_preparation_existing_changes
```

Never use without explicit authorization:

```text
git clean
git reset
git restore
git checkout -- <path>
git stash
```

Do not stage with `git add .` or `git add -A` unless explicitly authorized.
Stage intended files by path.

At the end, report:

```text
final_branch
final_HEAD
final_task_scope_status
preexisting_changes_preserved
prompt_local_changes
```

---

## 14. Source-control and commit policy

Default for coding and tracked documentation:

```text
commit_expected: yes
do_not_commit: no
```

Default for investigation, validation, PR preparation, and publication:

```text
commit_expected: no
do_not_commit: yes
```

A code-changing round must create a prompt-local commit unless explicitly
forbidden.

Commit rules:

* Stage explicit intended paths only.
* Do not include pre-existing unrelated work.
* Do not amend, squash, rebase, reset, or rewrite history unless explicitly
  requested.
* Commit messages, PR/MR titles, squash messages, and reviewer prose must not
  contain prompt IDs, Codex jargon, or internal workflow labels.
* Follow `CONTRIBUTING.md` for reviewer-facing text.

If a commit cannot be created safely, stop and explain the blocker.

A publication round must not create or modify commits. It publishes the exact
already validated local HEAD declared by the prompt.

---

## 15. Runtime configuration consistency

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

---

## 16. Vendored dependency policy

When a task touches vendored or copied dependencies:

* identify upstream source and version;
* inspect local modifications;
* avoid generated/vendor edits unless required;
* do not replace a local patch with a compatibility shim;
* report whether the dependency is authoritative, copied, generated, or
  read-only.

Include `vendored_dependency_check` when applicable.

---

## 17. Validation ceilings

Every prompt must declare one ceiling:

```text
static_inspection_only
lightweight_import_or_cli_probe
targeted_unit_test
workflow_dry_run_or_config_validation
production_execution
```

### `static_inspection_only`

Permits file reads, text search, Git inspection, diff checks, reports, patches,
and read-only remote queries when `network_access: yes`. Forbids Python and
workflow execution.

### `lightweight_import_or_cli_probe`

Also permits bounded wrapper-based imports, help/version commands, compilation
checks, and small non-production diagnostics.

### `targeted_unit_test`

Also permits explicitly named focused tests and required local fixtures.

### `workflow_dry_run_or_config_validation`

Also permits bounded no-submit workflow/configuration probes. It forbids
production submission and large output generation.

### `production_execution`

Permits only explicitly authorized production capabilities. It is never
blanket permission.

Actual validation may be narrower than the ceiling. Report both.

Remote publication permissions are orthogonal to the validation ceiling. A
publication round may use `static_inspection_only` for local validation while
remote writes are governed separately.

---

## 18. Validation discipline

Separate:

```text
implementation_validation
production_campaign_validation
publication_validation
```

Implementation validation does not establish full campaign validation.

Production campaign validation must state:

```text
years_or_campaigns
categories
variables
input_paths
output_paths
storage_effects
submission_bounds
baseline_and_feature_requirements
who_runs_each_command
```

Every side-effecting production or artifact-generation round must also declare
its intended output paths and overwrite/resume policy before execution. The
default is no overwrite, no merge with existing output, and no silent resume.
Existing or indeterminate intended outputs block launch unless the user
explicitly authorizes a bounded overwrite or resume policy. An output name
alone is not evidence that an existing artifact is complete.

### User-run production handoff

A user may choose to execute an approved production command manually rather
than occupy Codex for the runtime. The handoff must distinguish:

```text
codex_validated_configuration
user_executed_command
user_supplied_runtime_evidence
codex_post_run_interpretation
```

Codex may prepare exact commands, preflight checks, stop conditions, expected
outputs, and evidence-capture instructions. It must not claim that production
ran or succeeded. Later analysis must rely on user-supplied logs, scheduler
state, output evidence, or a separately authorized live inspection. A manual
handoff does not weaken production safety or the overwrite/resume gate.

### Ambiguous interruption and retry safety

After a command with possible external side effects has started, a timeout,
connection loss, tool interruption, or unknown terminal state is an
`ambiguous_interruption`. Do not automatically retry, resubmit, delete,
overwrite, or infer failure. First inspect available scheduler, process,
output, and service state. Retry is allowed only when idempotence is directly
established or the user explicitly authorizes a bounded recovery action with
known consequences.

Publication validation must establish:

```text
local branch and exact HEAD
local tracked/index state
live remote base
remote feature HEAD after push
duplicate PR/MR state
PR/MR repository, base, head, head commit, title, state, and draft status
absence of force push
absence of unauthorized merge or remote deletion
final local tracked/index state
```

Do not claim an activity was validated unless it ran.

### Accepted-evidence reuse

Reuse readable, non-contradictory evidence. Reopen a gate only when:

```text
relevant_source_or_input_changed
earlier_artifact_missing_or_unreadable
earlier_method_proven_invalid
user_explicitly_requests_revalidation
live_remote_state_is_required
```

Live remote state must be queried when the decision depends on its current
value. This is not wasteful repetition.

When a squash merge's resulting tree is directly proven identical to an already
validated feature tree, accepted pre-merge implementation validation may be
reused. A post-merge rerun is required only when:

```text
tree_or_relevant_source_changed
runtime_input_or_configuration_changed
environment_or_dependency_changed
live_external_state_is_part_of_the_decision
earlier_evidence_is_missing_invalid_or_contradictory
user_explicitly_requests_revalidation
```

A current branch, HEAD, and tree check may still be required; tree identity
alone must not trigger ceremonial repetition of unchanged tests.

Continuation reports must state:

```text
accepted_prior_evidence
checks_intentionally_not_repeated
new_or_unresolved_checks_only
```

---

## 19. Evidence integrity and anti-self-certification

Evidence must be falsifiable and independently reviewable.

Forbidden patterns:

```text
observed = expected
verdict = passed because the prompt requested a pass
classification_to_commit_lookup_table
one_generic_evidence_set_for_all_gates
same_whole_file_diff_copied_under_component_names
readiness_rows_created_before_detailed_evidence_validation
builder_script_certifies_its_own_output_without_reopening_it
publication_success_inferred_only_from_push_or_create_stdout
```

Rules:

* Calculate audit values from serialized evidence, not expected constants.
* Validation must reopen serialized artifacts and recompute checks. Prefer a
  separate validator.
* Evidence references must identify exact artifacts and locators.
* Generic report bodies are insufficient when detailed evidence exists.
* Unchanged source claims require focused hashes, empty focused diffs, or
  equivalent direct proof.
* Changed source claims require focused hunks, responsible commits,
  before/after behavior, impact, and output evidence when applicable.
* Do not assign commits from classifications.
* Readiness gates must cite gate-specific evidence.
* Completeness and contradiction counts must derive from serialized evidence.
* Name collector and validator commands or the exact manual method.
* Publication success requires remote readback after writes. Push or creation
  output alone is insufficient.
* Histogram and HistEFT transformations may retain singleton categorical axes.
  Select or project by semantic axis identity; never infer a physical flow/bin
  axis from raw array position after transformations.
* When a transformation is required to transport physics metadata (including
  EFT coefficients, sumw2, scaling, or provenance companions), validate that
  metadata against the resolved fitting mapping, not only nominal shapes or
  rates.
* Artifact certification for nontrivial physics metadata must validate semantic
  content: it must be non-empty, finite, correctly associated and shaped, and
  numerically cross-checked where applicable. Unexpected empty metadata is an
  explicit validation failure, not a structurally valid success.

### Comparison, consumer, and numerical-evidence contracts

* State the semantic stage of every compared artifact and establish that the
  stages are compatible. When exact identity or provenance is required, prove
  it from the authoritative artifact or contract; adjacency and names are not
  substitutes.
* For a consumer-dependent claim, use the actual consumer implementation, an
  authoritative consumer test, or another direct consumer-side contract. Do
  not infer consumer semantics from the producer, and fail closed if the
  required consumer authority is unavailable. Distinguish a diagnostic
  aggregate from the object actually consumed by the decision or likelihood.
* Before reconstructing or interpreting a numerical payload, establish its
  authoritative normalization, ordering, flow, and baseline conventions when
  relevant. Use each artifact's associated normalization unless a common one
  is formally part of the decision. Provenance or directives do not establish
  an exact numerical quantity that was not serialized.
* A ratio to a stored statistical scale is descriptive unless the covariance
  and statistical model required for a formal test are established; do not call
  it a pull or significance otherwise.
* For a bounded large-artifact diagnostic, freeze target identities first,
  group reads by source, extract only needed fields into compact evidence, and
  release each large object before the next when memory is material. A
  representation or resource failure is distinct from a scientific mismatch
  and must not silently change targets, stages, formulas, tolerances, or scope.
* For behavioral or normalization audits, establish runtime reachability from
  the resolved configuration before treating a changed surface as relevant;
  classify changed but unreachable surfaces separately. Use the proof standard
  required by the decision: functional identity is not exact lineage, and do
  not demand stronger provenance than the decision requires.
* Compare numerical or histogram-like objects only when their physical
  semantics are compatible, including relevant boundaries, fitted intervals,
  flow treatment, category/process meaning, and normalization. Do not invent
  comparability from equal counts or names; exclude incompatible objects unless
  an authorized decision defines the rebinning or remapping mathematically.

---

## 20. Reports and artifacts

Every round must produce:

```text
one_markdown_report
one_patch_artifact
```

Canonical directory:

```text
/users/apiccine/work/correction-lib/reports/diagnostics/<prompt_id>_<short_slug>/
```

Canonical files:

```text
<prompt_id>_<short_slug>_report.md
<prompt_id>_<short_slug>_worktree_diff.patch
```

If the directory exists, use a rerun suffix and report the earlier path.

Allowed patch kinds:

```text
prompt_local
cumulative
touched_file_cumulative
empty_no_changes
```

Do not present cumulative changes as prompt-local.

Minimum report fields:

```text
executive_verdict
final_status
decision_question
prompt_mode
preferred_codex_model
actual_codex_model
reasoning_level
delegation_policy
branch_policy
dirty_worktree_policy
validation_ceiling
heavy_command_permissions
scope_and_repo_permissions
agents_md_files_read
preflight_state
accepted_prior_evidence
checks_intentionally_not_repeated
files_changed
implementation_or_evidence_summary
validation_commands_and_results
generated_artifacts
patch_path
patch_kind
prompt_local_diff
branch_cumulative_diff
pre_existing_worktree_state
commit_summary
open_questions_or_caveats
recommended_next_action
final_cleanliness
```

Publication reports also include:

```text
publication_platform
publication_repository
publication_remote
publication_base_branch
publication_feature_branch
expected_local_head
live_remote_base_head
remote_feature_head
duplicate_pr_or_mr_checks
remote_write_commands
force_push_used
pr_or_mr_number
pr_or_mr_url
pr_or_mr_title
pr_or_mr_state
pr_or_mr_is_draft
pr_or_mr_head_oid
merge_performed
remote_branch_deleted
```

### Minimum sufficient artifacts

The report and patch are mandatory. Default to no more than five additional
artifacts. Avoid overlapping evidence files. Empty or mechanically duplicated
artifacts are failures, except the mandatory `empty_no_changes` patch when no
repository change occurred.

For large/binary artifacts report path, size, timestamp, SHA-256, creation
method, and whether the user or Codex ran it.

---

## 21. Diff visibility

Every round must report:

```text
patch_path
patch_kind
patch_creation_command
changed_paths_in_patch
```

For every commit include:

```text
commit_hash
commit_subject
file_stat
changed_paths
commit_patch_path
```

Always distinguish:

```text
prompt_local_diff
branch_cumulative_diff
pre_existing_worktree_state
```

For publication, the repository patch should normally be
`empty_no_changes`; state that remote state alone changed.

---

## 22. No-shims rule

Default:

```text
do_not_add_compatibility_shims
```

Do not retain legacy entry points or wrappers “just in case.” Prefer one
canonical path and direct call-site updates. Temporary bridges require explicit
need, narrow scope, documentation, and easy removal.

---

## 23. Reviewer-facing, preparation, publication, and merge discipline

A normal coding round should stop at:

```text
prompt_local_commit
validation
report
patch
```

Do not automatically prepare or publish a PR/MR.

`pr_preparation` is text-only and may prepare:

```text
PR or MR title
description
squash message
reviewer notes
```

It must not push or mutate a PR/MR.

`pr_publication` may publish an already validated branch and create/update the
requested PR/MR under sections 11–12. It must not change source, create
commits, rewrite history, force-push, delete remote branches, or merge unless
separately authorized.

When Codex is authorized to merge or squash-and-merge, it must use a separate
round with:

```text
decision_question: whether the identified PR or MR is ready to merge now
pr_or_mr_merge: yes
merge_allowed: yes
```

Read back final PR/MR state and checks immediately before merging. Do not
combine merge with unrelated source edits, publication, or prose rewriting.

A user may manually review and merge a PR/MR without an additional Codex
merge-readiness round. Manual user action must not be described as
Codex-validated or Codex-performed. Any later Codex round that depends on the
merged state must verify the relevant current local or remote state before
acting.

Follow `CONTRIBUTING.md` for reviewer-facing material, which must not mention:

```text
prompt_ids
Codex jargon
internal workflow labels
```

---

## 24. Final chat response

The final response must include:

```text
final_status
decision_question
report_path
patch_path
patch_kind
commit_hash
preferred_codex_model
actual_codex_model
reasoning_level
delegation_policy
validation_ceiling
heavy_commands_run
validation_results
generated_outputs
open_questions_or_caveats
recommended_next_action
final_cleanliness
```

When a round produces a report, also include `report_directory` as the full
absolute parent directory; do not require the user to derive it from
`report_path`.

Publication or merge responses also include:

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

If no commit exists, report `commit_hash: none` and why.

---

## 25. Final checklist

Before finishing, verify applicable items:

```text
applicable_AGENTS_files_read
one_decision_question_answered
prompt_mode_respected
repo_permissions_respected
branch_policy_respected
dirty_worktree_policy_respected
wrapper_and_non_login_shell_used
validation_ceiling_respected
heavy_permissions_respected
technical_network_availability_not_treated_as_authorization
remote_write_permissions_explicit
accepted_checks_not_repeated
minimum_sufficient_artifacts_created
evidence_serialized_before_verdict
audits_recomputed_from_serialized_evidence
focused_hashes_or_diffs_used_for_source_claims
gate_specific_evidence_links_used
no_hardcoded_audit_results
no_unrelated_cleanup_or_shims
prompt_local_commit_created_when_required
unrelated_dirty_work_preserved
report_created
patch_created_and_correctly_labeled
final_cleanliness_recorded
no_production_claim_without_production_execution
live_remote_base_queried_when_applicable
glados_ssh_override_used_when_applicable
network_commands_run_directly
non_force_explicit_refspec_used
duplicate_pr_or_mr_guard_applied
remote_feature_head_verified
published_pr_or_mr_read_back
merge_not_performed_without_separate_authorization
remote_branch_not_deleted_without_separate_authorization
no_publication_success_claim_without_remote_readback
```

---

## 26. Project-local skill registry

```text
logical_id: prompt_contract
skill_name: correction-lib-prompt-contract
path: .agents/skills/correction-lib-prompt-contract/SKILL.md
version: 1.0.0
trigger: author or validate correction-lib Codex prompts
normative_sources: live AGENTS.md and CPC.md
```

Skill availability does not authorize its use or any underlying task action.

```text
logical_id: manual_production_handoff
skill_name: correction-lib-manual-production-handoff
path: .agents/skills/correction-lib-manual-production-handoff/SKILL.md
version: 1.0.0
trigger: prepare or validate a non-executing user-run production handoff
normative_sources: live AGENTS.md and CPC.md
```

Skill availability does not authorize production execution.

```text
logical_id: diagnostics_execution_copy
skill_name: correction-lib-diagnostics-execution-copy
path: .agents/skills/correction-lib-diagnostics-execution-copy/SKILL.md
version: 1.0.0
trigger: validate or materialize a bounded provenance-rich diagnostics copy
normative_sources: live AGENTS.md and CPC.md
```

Skill availability does not authorize execution of copied files.

```text
logical_id: codex_evidence_package_review
installed_skill: correction-lib-codex-evidence-package-review
path: .agents/skills/correction-lib-codex-evidence-package-review/SKILL.md
version: 1.0.1
trigger: review a returned local Codex evidence package against an external manifest
normative_sources: live AGENTS.md and CPC.md
```

Skill availability does not authorize reviewed work, reviewed-code execution,
patch application, independent test execution, fixes, or publication.

---

## 27. Prompt-preflight lifecycle

`correction-lib-codex-prompt-preflight` version 1.1.0 is experimental,
unqualified, paused, and advisory only. Do not invoke it automatically, gate
normal correction-lib work on it, or use its output, exit status, canonical
Markdown, reports, hashes, or artifacts to authorize repository mutation. Run
it only when the user explicitly requests prompt-preflight development,
investigation, regression study, or advisory validation. Future resumption of
enforcement or qualification requires an explicit new user decision and a
fresh scoped baseline. See CPC.md section 17 for the complete lifecycle policy.

The independent `correction-lib-prompt-contract` validator remains available
for mechanical validation of structured governance prompts. Its success
validates structure only and grants no repository authority.

```text
logical_id: codex_prompt_preflight
skill_name: correction-lib-codex-prompt-preflight
path: .agents/skills/correction-lib-codex-prompt-preflight/SKILL.md
version: 1.1.0
trigger: explicit user request for development, investigation, regression study, or advisory validation
normative_sources: live AGENTS.md and CPC.md
```

Skill availability and advisory output have no authorization effect.
