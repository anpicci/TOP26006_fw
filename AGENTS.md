# AGENTS.md — TOP26006_fw Codex operating policy

`TOP26006_fw` is the TOP-26-006 project and coordination meta-repository. Its
local checkout remains `/users/apiccine/work/correction-lib`. It coordinates
independent implementation, document, dependency, and evidence repositories;
the accepted typed inventory is in `governance/repositories.md`. The checkout
directory name does not change the project identity. Never treat nested Git
repositories as one repository or combine their histories.

---

## 0. Policy precedence

1. `AGENTS.md` controls execution, repository permissions, branch behavior,
   Git hygiene, validation, artifacts, commits, remote publication, and merge
   authorization.
2. `CPC.md` controls how ChatGPT constructs Codex prompts.
3. `CONTRIBUTING.md` controls PR/MR titles, descriptions, squash messages,
   reviewer notes, validation language, and other reviewer-facing prose.
4. The selected `governance/modules/<repository>.md`, when named by the typed
   registry, adds TOP26006_fw repository-specific project rules under these
   common files. Applicable repository/upstream-native policy also binds the
   action; a module cannot weaken common safety or create authorization.
5. A user instruction overrides these files only when explicit.
6. On conflict, stop and report the conflict. Do not guess.

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
* `one_round_one_decision` means one substantive decision boundary, not one
  activity type. Multiple ordered activity types belong in one round only
  through `orchestrated_workflow` and only when their transitions are
  predeclared and mechanically determined by objective gates.
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
* Coding and tracked-documentation work normally ends in a prompt-local commit.
  For tracked mutation, `do_not_commit: yes` requires explicit owner
  authorization for that exact round.
* Available network access, credentials, executables, or remotes are technical
  capabilities only. The prompt must authorize each network capability and
  remote mutation separately.

### Reusable capability lifecycle

Before creating a script, helper, validator, runner, launcher, converter, or
execution utility, establish whether an applicable maintained capability or
owner already exists. Decide in this order: reuse the existing maintained
capability; use configuration or composition; make the minimum compatible
extension; create a new capability only when the maintained architecture cannot
own the requirement cleanly. `reuse_before_create` does not require reuse at any
cost: historical, retired, unsupported, or semantically incompatible tooling
need not be reused.

Classify newly needed tooling as `EPHEMERAL_DIAGNOSTIC` or
`REUSABLE_CAPABILITY`, using expected reuse and ownership as the discriminator.
One-off evidence extraction, temporary comparisons or tables, bounded
hypothesis checks, and temporary provenance extraction may remain
diagnostics-local. Capabilities with plausible reuse beyond the current round,
such as production launchers, resumable runners, retry or recovery machinery,
manifest generators, package builders, durable validators, format converters,
and reusable analysis helpers, require an appropriate maintained home. As
applicable, define the canonical owner and repository surface, supported
interface, usage contract, appropriate tests, failure semantics,
provenance/output contract, and documentation needed for that capability. Do
not leave de facto maintained infrastructure in a diagnostics directory.
`canonicalize_reusable_capabilities` does not promote every diagnostic into
repository source.

If a round expected an ephemeral helper and evidence shows that the needed
functionality is reusable, preserve the evidence, stop scope expansion, record
the reusable-capability gap, and decide whether a separate bounded coding round
is earned. Apply the existing `one_round_one_decision`,
`minimum_sufficient_scope`, and `no_silent_scope_expansion` rules; do not create
a second scope-control framework.

---

## 2. Workspace and repository boundaries

The local coordination checkout is `/users/apiccine/work/correction-lib` and
is a distinct Git meta-repository named `TOP26006_fw`. Select a task repository
by `repository_id` from `governance/repositories.md`, then read its applicable
module and path-applicable nested `AGENTS.md` before acting. The registry
defines stable roles, ownership, path status and consumers; fresh Git and
remote readback establish volatile operational state. Do not infer a repository
from a directory name or use registry text as a current HEAD, branch or remote
ref. The coordination repository is the authoritative source-control owner of:

```text
AGENTS.md
CPC.md
CONTRIBUTING.md
```

The registry and its four dedicated modules are also root-owned governance
files. Nested Git histories remain independent. Root Git operations must not
stage nested repositories, unrelated root artifacts, reports, backups,
payloads, or local tools without explicit authorization. Governance commits
stage intended exact paths only.

TOP26006_fw is the single TOP-26-006 project operational and prompt/agentic
governance owner. Repository-native or upstream policy remains owned by that
repository/upstream project; effective actions satisfy both. Scientific and
technical content remains with the native semantic owner and authorized lane.
Project governance does not claim upstream branch or publication policy.

The ANDOCS checkout currently at `/users/apiccine/work/ANDOCS` remains under
its local transitional governance. `governance/modules/andocs.md` is the
central successor, not yet a claim of path applicability at that external
location. Its physical rehome and legacy-rule retirement require a later gate.

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

Default in the absence of exact mutation authorization: selected
non-coordination repositories are `read_only`; `topcoffea` and `EFTFit` have
additional module-specific read-only posture. A prompt must explicitly name
the writable repository, paths, and effects. Registry membership neither
grants a write nor permanently prohibits an otherwise validly authorized one.

This read-only default is an intentional centralized multi-repository
governance tightening; the earlier `topeft` writable default was not
semantically identical. TOP26006_fw grants no implicit write to its tracked
content. Tracked root content may be changed when an exact round authorizes
the relevant root paths and effects under the applicable branch and commit
rules; the round need not be classified as root governance. Diagnostics,
report, and evidence outputs under the root workspace follow separately
declared output and storage permissions, not the tracked-content write grant.
A non-coordination repository may be changed when the exact round authorizes
its repository, paths, and effects and applicable repository/upstream-native
policy permits the action. This default does not make nested repositories
immutable, supersede native policy, or transfer implementation ownership to
TOP26006_fw governance. Centralized project governance does not make the
coordination repository a monorepo or centralize implementation ownership.

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
* Generic force and `--force` are forbidden. The sole guarded rewrite is the
  action-specific `normalize_declared_post_squash_staging_ref` contract, which
  requires exact user authorization and `force_push_allowed: yes` for its
  exact old-SHA lease.
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

Repository selection is execution context, not authorization. For `git`, use
either the native process working directory at the exact prompt-authorized
repository or `git -C <exact_prompt_authorized_repository_path> ...`; do not
use a `cd ... && ...` wrapper. For `gh` or `glab`, use either the native
repository working directory, an explicit repository selector such as
`--repo <owner/repository>`, or an explicit repository-qualified API/resource
endpoint when supported. The prompt or stage must independently authorize the
exact repository and action. Repository-selection syntax does not prove
identity or authorization and must not widen writable scope; read back
repository identity when it is decision-material.

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
integration_only
branch_maintenance_only
orchestrated_workflow
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
prompt-local tracked changes unless the owner explicitly authorizes
`do_not_commit: yes` for that exact round.

### `validation_only`

Allowed: bounded diagnostics, approved workflow runs, pkl inspection, plotting
checks, and reports.

Forbidden: tracked source/test edits, commits, and remote mutation.

### `test_alignment_only`

Allowed only when direct evidence proves the runtime contract is intentional
and tests are stale. If runtime intent is ambiguous, stop.

### `documentation_only`

Allowed when behavior is established and only tracked documentation changes.
Commit unless the owner explicitly authorizes `do_not_commit: yes` for that
exact tracked-mutation round.

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

### `integration_only`

Allowed only for one explicitly declared local branch-integration decision:
read-only ancestry, ref, tree, and worktree checks; switching to the declared
local integration target; integrating exactly one declared local source feature
branch; post-integration local readback; and report/patch artifacts. The
default `integration_method` is `ff_only`, which creates no new commit.

Forbidden by default:

```text
source/test/config/documentation edits
new development commits
remote reads or writes
push
PR/MR creation, update, or merge
remote or local feature-branch deletion
reset
restore
stash
clean
rebase
cherry-pick
force update
history rewriting
```

An integration target or reference branch remains a non-development surface;
this mode may advance it only by the explicitly declared integration action and
does not authorize later development commits there. The source feature branch
remains present unless deletion is separately authorized in another round.

A non-fast-forward method, including a merge commit or squash, is never
implied. It requires the exact method and explicit user authorization in a
separate one-decision integration round, a declared resulting local-commit
behavior, and compliance with existing commit, diff, and readback rules. A
rebase or other history rewrite is never an implicit alternative.

### `branch_maintenance_only`

Allowed only for one explicitly authorized local branch/ref lifecycle decision.
Individually declared actions may create one preservation feature branch at an
observed local HEAD, switch among declared local branches, rename one declared
local branch, move or restore one declared local branch ref to a named
authoritative local commit/ref, verify ancestry and reachability before and
after the action, and produce bounded diagnostics. Safety-critical local
branch/ref commands must be listed exactly in the prompt.

Forbidden by default:

```text
tracked source/test/config/documentation edits
new development commits
integration/merge/squash
rebase
cherry-pick
working-tree reset/restore/stash/clean
local or remote branch deletion
force push
push
PR/MR operations
remote mutation
```

Before any action moves a local branch ref away from a historical development
HEAD, record that observed HEAD; create or prove one named preservation ref;
verify that ref resolves to the exact historical HEAD and that every intended
commit is reachable from it; and reopen serialized evidence. After the move,
fresh readback must prove the historical HEAD remains reachable, the moved ref
equals its named authoritative source, no unintended local ref moved, and the
tracked/index/worktree state is safe. A branch name alone is not preservation
evidence.

Choosing this mode does not authorize a non-fast-forward ref move, force move,
rename, or deletion-like lifecycle action. A prompt must declare the action,
affected local branches, expected preserved head, preservation ref, reference
restore source, and whether non-fast-forward movement is authorized. Any
non-fast-forward ref move requires explicit user authorization for that exact
decision; absent it, stop before the move. This is not authorization for
rebase, reset, deletion, or history rewriting of commits. Local and remote
branch deletion both default to `no` and require separate authorization.

This mode owns local branch/ref normalization only. It does not replace
development modes, `integration_only`, `commit_preparation`, or
`pr_publication`.

### `orchestrated_workflow`

This is a composition meta-mode for one pre-authorized workflow that implements
one substantive decision through ordered stages. Each stage's existing prompt
mode remains normative; this mode does not copy, replace, or broaden those
contracts.

An orchestrated workflow may compose only:

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

`production_execution` remains excluded, and a stage must not use
`orchestrated_workflow`; nested workflows are forbidden. A `pr_publication`
stage is allowed only for an exact non-merge `publication_action` whose remote
effects are pre-authorized by the user, bounded by the outer workflow envelope
and stage-local permissions, and mechanically selected from validated observed
evidence. An orchestrated publication stage must not use:

```text
publication_action: merge_existing_pr_or_mr
pr_or_mr_merge: yes
merge_allowed: yes
generic force or `--force`
remote branch deletion
history rewriting outside the action-specific
`normalize_declared_post_squash_staging_ref` contract below
automatic merge
```

The normalization action is the sole force-with-lease exception inside
orchestration. It does not relax any other force, history-rewriting,
publication, merge, or deletion boundary.

PR/MR merge remains a separate substantive decision round. Allowing
`pr_publication` as a stage does not lend its network or remote-write
permissions to any other stage.

An orchestrated prompt must declare the conditional workflow fields:

```text
workflow_goal
workflow_stages
workflow_stop_policy
workflow_stage_ledger_path
```

The default stop policy is
`stop_on_failed_gate_or_new_decision_boundary`. Each ordered stage must declare,
when applicable:

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

Omit `stage_permissions` only when the stage requests no positive capability;
omission means every capability is denied at that stage, including any positive
capability in the outer envelope. When a stage needs a capability, name its
exact positive grant locally and keep all mode-required action fields. Fixed
denials need not be repeated unless the selected stage mode requires their
explicit declaration. The first stage may omit `stage_inputs_from_prior` because
no prior stage exists; later stages must state their observed bindings or `none`.

Mode-specific fields remain required inside the stage that owns them. A stage's
effective permissions are the intersection of the outer workflow permission
envelope, its stage-local permissions, the stage mode's normative permissions,
and explicit user authorization. Permissions, repository write scope,
branch/ref movement, and storage or network capabilities cannot be borrowed
across stages, and the outer envelope must not be enlarged after execution
begins.

A later stage may begin only after the prior stage completed, serialized its
required evidence, performed any mode-required readback, passed its declared
acceptance gate from observed evidence, and introduced no new substantive
decision. A new substantive decision is a choice whose next action was not
preauthorized and mechanically selected by the declared gates; stop with
`blocked_new_decision_boundary` and report the unresolved choice. Failed or
indeterminate gates and missing stage permissions likewise stop all remaining
mutation, publication, commit, execution, and scope expansion without an
improvised fallback.

When a mutating stage consumes a semantic contract established by a prior
stage, the transition gate must prove that the required semantic surface is
complete as well as that the intended diff is isolated. Diff isolation alone
must not certify semantic completeness. This additional proof is conditional;
it is not required when the later stage consumes no prior-stage semantic
contract.

When publication-grade review was preauthorized for the workflow, a failed or
indeterminate gate may instead enter an explicitly declared terminal read-only
completeness-review tail. This narrow tail is the only exception to stopping
all remaining stages. It may continue safe read-only inspection of the
already-authorized evidence surface, populate the publication-grade review
buckets, and identify unresolved risks and surfaces not yet evaluated. It must
not mutate, enlarge the evidence scope, satisfy or bypass the failed gate,
transition back into execution, or authorize publication, merge, commit, or
production. Ordinary `stop_on_failed_gate_or_new_decision_boundary` behavior
continues to govern every non-terminal-review stage.

Later stages may bind inputs to validated observed outputs from earlier stages,
for example `expected_source_head: stage_1.resulting_head`. They must consume
the read-back value, not an expected placeholder. These bindings are local
workflow evidence, not persistent global state.

Before an orchestrated `pr_publication` stage begins, its exact
`publication_action`, repository, remote, local ref, remote ref, and expected
local HEAD must be resolved from explicit immutable inputs or reopened observed
evidence. The outer permission envelope and stage-local permissions must both
contain only the capabilities needed by that action, and explicit user
authorization must cover every remote write. An unresolved divergence,
merge-versus-rebase choice, ambiguous commit ownership, or other unbound remote
decision stops with `blocked_new_decision_boundary`; a missing capability stops
with `blocked_stage_permission`, and failed or indeterminate evidence stops
with `blocked_stage_gate`.

Remote inspection, mechanically safe synchronization, and post-action
validation may share one orchestrated publication stage only when the
synchronization direction and action are fully determined by predeclared
objective topology rules. The workflow must stop before overwriting divergent
history, except for the exact guarded normalization action below; choosing
merge versus rebase; merging a PR/MR; or making a documentation-content
decision that requires human review.

Completed stage effects remain after a later block. Automatic rollback is
forbidden; do not reset, restore, rebase, stash, clean, delete, or rewrite to
simulate atomicity. A rollback may occur only as an explicitly preauthorized
stage that is itself valid under an existing stage mode. Report:

```text
completed_stages
blocked_stage
not_started_stages
persistent_effects_from_completed_stages
```

Each mutating stage must independently obey its branch lifecycle and commit
contract. Stage boundaries do not authorize parallel active feature branches,
and the workflow itself implies no extra final commit.

Produce one overall report, one overall patch, and one compact serialized stage
ledger. The ledger records observed stage identity, mode, start/completion
state, effective permissions, preconditions, acceptance gate and evidence,
gate result, resulting branch and HEAD, generated artifacts, and persistent
effects. Reopen it and derive workflow progress before classification; it is
evidence, not a prefilled verdict table. Use the minimum statuses needed:

```text
orchestrated_workflow_complete
blocked_stage_gate
blocked_new_decision_boundary
blocked_stage_permission
blocked_stage_governance_conflict
```

When this mode can express a deterministic sequence of existing modes, do not
create a sequence-specific compound mode. A new standalone mode still requires
a demonstrated semantic gap that neither one existing mode nor orchestration
can represent.

### `pr_publication`

Allowed: one explicitly declared remote publication action using already
validated local commits and evidence. Supported actions are:

```text
create_or_reuse_open_pr_or_mr
synchronize_declared_remote_branch
normalize_declared_post_squash_staging_ref
merge_existing_pr_or_mr
```

`merge_existing_pr_or_mr` remains a separate decision round and is forbidden
inside `orchestrated_workflow`. Publication fields and permissions are
action-specific; PR/MR-only fields are not globally required.

Required permissions for `create_or_reuse_open_pr_or_mr`:

```text
network_access: yes
remote_git_write: <yes_or_no; conditional source-ref synchronization>
pr_or_mr_write: yes
pr_or_mr_merge: no
remote_branch_deletion: no
force_push_allowed: no
merge_allowed: no
```

For this action, `remote_git_write: no` is valid only when the prompt requires
the advertised remote feature HEAD to already equal `expected_local_head`; if
the fresh advertised remote feature HEAD differs, stop before remote mutation.
Set `remote_git_write: yes` only when the prompt and explicit user
authorization allow at most one normal non-force explicit-refspec feature-branch
push when that fresh remote feature HEAD differs. In either case, when the
fresh advertised remote feature HEAD already equals `expected_local_head`,
classify `remote_branch_already_synchronized` and skip the push.

The action `synchronize_declared_remote_branch` owns one explicitly declared
local/remote branch synchronization boundary. It requires:

```text
publication_action: synchronize_declared_remote_branch
publication_platform
publication_repository
publication_remote
publication_local_branch
publication_remote_branch
publication_remote_tracking_ref
expected_local_head
network_access
remote_git_write
pr_or_mr_write
pr_or_mr_merge
remote_branch_deletion
force_push_allowed
merge_allowed
```

Its required safe defaults are:

```text
pr_or_mr_write: no
pr_or_mr_merge: no
remote_branch_deletion: no
force_push_allowed: no
merge_allowed: no
```

`remote_git_write` is `no` for live query and an explicitly authorized bounded
fetch of the declared remote branch into the declared local remote-tracking
ref. A fetch changes local tracking state, not the remote, and still requires
`network_access: yes`. Set `remote_git_write: yes` only when the prompt and
explicit user authorization allow one possible normal non-force push from the
declared local ref to the declared remote branch. The PR-specific fields
`publication_base_branch`, `publication_feature_branch`,
`duplicate_pr_or_mr_policy`, and `draft_allowed` are not required for this
branch-only action.

As separately authorized and mechanically selected from validated prior
evidence, `synchronize_declared_remote_branch` may perform:

```text
bounded live inspection of the declared remote branch
bounded fetch of that exact remote branch into its declared local tracking ref
one normal non-force push from the declared local ref to the declared remote branch
```

It must not create, update, or merge a PR/MR; choose merge versus rebase;
resolve or overwrite divergence; force push; delete a remote branch; use a
wildcard or implicit multi-ref refspec; or push an active feature into a
reference branch unless the prompt establishes that exact local ref as the
intended reference authority. Diverged or ambiguous topology is
`blocked_new_decision_boundary`, not authorization to improvise.

The action `normalize_declared_post_squash_staging_ref` owns one exact guarded
remote ref rewrite after a squash when tree equality or another explicit
identity basis establishes the intended normalization. It is optional, never
implied by a squash or by tree equality, and does not weaken
`synchronize_declared_remote_branch`, which remains normal non-force
synchronization. A genuinely multi-stage normalization should use
`orchestrated_workflow`; a genuinely atomic normalization may use a standalone
`pr_publication` round.

This action requires:

```text
publication_action: normalize_declared_post_squash_staging_ref
publication_platform
publication_repository
publication_remote
exact_remote_ref
exact_observed_old_sha
exact_target_sha
verified_local_archive_ref
verified_remote_archive_ref_when_remote_history_is_being_rewritten
archive_reachability
normalization_identity_basis
force_with_lease_argument: --force-with-lease=<ref>:<exact_old_sha>
network_access: yes
remote_git_write: yes
pr_or_mr_write: no
pr_or_mr_merge: no
remote_branch_deletion: no
force_push_allowed: yes
merge_allowed: no
generic_force: forbidden
lease_refresh_after_unexplained_remote_movement: forbidden
post_write_remote_readback: required
final_expected_identity_readback: required
```

The prompt and user authorization must identify the exact ref rewrite. Before
the write, direct evidence must prove that the local archive ref preserves the
observed old SHA, that the remote archive ref exists when remote history is
being rewritten, that the archived history is reachable, and that the target
meets the declared tree-equivalence or other identity basis. The write may use
only `--force-with-lease=<ref>:<exact_old_sha>` with an explicit single-ref
refspec. Generic force and `--force` remain forbidden everywhere. Unexpected
movement of the remote old SHA is a hard stop; do not refresh the lease after
unexplained movement. Fresh remote readback after the write and final readback
of every declared expected identity are mandatory. Command stdout alone is not
success evidence.

Forbidden unless separately authorized:

```text
source or test edits
new commits
amend
rebase
history rewriting outside the guarded normalization action
force push outside the exact old-SHA lease required by that action
remote branch deletion
automatic merge
PR or MR merge
```

A `create_or_reuse_open_pr_or_mr` round must:

1. verify local repository, branch, HEAD, reviewer material, and tracked/index
   state;
2. verify remote identity and repository permission;
3. query the live remote base;
4. query the live advertised remote feature HEAD;
5. query for an existing matching open PR/MR;
6. compare the remote feature HEAD with `expected_local_head`;
7. if equal, classify `remote_branch_already_synchronized` and do not push;
   otherwise, if `remote_git_write: yes`, perform exactly one normal non-force
   explicit-refspec push and freshly verify the advertised remote feature HEAD
   equals `expected_local_head`; otherwise stop before remote mutation;
8. repeat the duplicate query to handle races;
9. create at most one non-draft PR/MR when none exists;
10. query the created or existing PR/MR back;
11. verify repository, base, head, head commit, title, state, and draft status;
12. recheck local tracked/index state.

A `synchronize_declared_remote_branch` round must verify local repository,
branch/ref, expected HEAD, tracking ref, and tracked/index state; inspect the
exact live remote branch; perform only the predeclared action selected by the
validated topology gate; and freshly read back the exact live remote branch
after the selected fetch, push, or no-action outcome. After a fetch it must also
verify the declared local remote-tracking ref. Push or fetch stdout alone is
not success evidence. Every
`git fetch`, `git ls-remote`, `git push`, `gh`, and `glab` operation remains a
separate direct command under section 12, including the command-local glados
SSH override when applicable.

A `normalize_declared_post_squash_staging_ref` round must perform its archive,
reachability, old-SHA, target-identity, exact-lease, and final-identity gates in
the declared order. Each `git ls-remote`, `git fetch`, and `git push` operation
remains a separate direct command under section 12. Any missing archive,
indeterminate identity basis, unexpected remote movement, or post-write
readback mismatch stops the action without a retry, lease refresh, merge,
deletion, or improvised rewrite.

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
```

Branch policy selects which branch the round may use and whether it may
create or switch branches. Prompt mode controls which activity is allowed;
the commit contract controls whether tracked changes must be committed before
successful closure. Branch policy does not encode a commit phase.

### `create_feature_branch_from_reference`

Use to create a new feature branch only when the live development branch
lifecycle check permits creation. Declare `reference_branch` and
`feature_branch`, verify the reference, record its HEAD, create/switch to the
feature branch, and report the merge base.

### `continue_existing_branch`

Declare `target_branch`. Work directly on it and create no additional branch.

### `read_only_current_branch`

Inspect or publish the current branch without local editing, committing, or
switching. Remote mutation still requires explicit publication permissions.
Derive the current branch from fresh preflight Git state. Declare an expected
current branch only when its exact identity is a safety invariant; stop if the
observed branch differs.

### Development branch lifecycle

Before tracked repository work that requires a development feature branch,
fresh-read the live local Git branch state for the target repository and
workstream. This branch-selection gate is independent of file category and
does not apply to pure read-only inspection. Live Git state is the branch-state
authority; do not create a registry or cache. Determine applicability from
semantic and dependency continuity with the proposed work, not task names,
prompt IDs, file names, or campaign labels. Strong evidence includes a
feature-only dependency absent from the reference, continuity of the accepted
semantic surface owned by the feature, or a need to replay or duplicate accepted
feature work if starting from the reference. Sharing only a package, analysis,
or campaign is insufficient. `NO_APPLICABLE_ACTIVE_FEATURE_BRANCH` requires
positive bounded evidence; missing or contradictory evidence is
`BRANCH_APPLICABILITY_AMBIGUOUS` and stops branch selection. Uncertainty must
not be counted as zero applicable features. Exactly one applicable active
feature branch requires `continue_existing_branch` unless the owner explicitly
authorizes a named split,
supersession, or integration exception. With none,
`create_feature_branch_from_reference` may be used. With multiple, stop for
reconciliation unless the owner authorizes such an exception. A declared
reference or integration branch is a baseline, not a development surface: do
not accumulate new development commits directly on it. Contradictory or
ambiguous live state stops with the applicable branch-policy blocker and a
`branch_escalation_note`; do not silently change the declared branch policy.

An owner-authorized exception must identify the existing applicable branches,
why continuing one is insufficient, the new repository-facing branch, any
superseded branches, and any retirement condition. It does not authorize branch
deletion, publication, remote mutation, merge, force update, or cleanup; those
actions retain their separate permissions. Do not automatically rewrite
historical commits that predate this rule.

When creation is permitted, new branch names must describe the repository
change and follow its established naming conventions; do not encode internal
lane, prompt, Codex, control-plane, round or campaign identifiers unless
already established as a repository-facing convention. TOPEFT and topcoffea
namespace constraints, and TOPEFT's permanent branch roles, are in their
registry-named modules. The generic reuse-first lifecycle above remains
binding. A generic baseline field cannot override a module's permanent role.

Require `reference_branch` and `feature_branch` for
`create_feature_branch_from_reference`, and `target_branch` for
`continue_existing_branch`. For `read_only_current_branch`, omit synthetic
`none` branch fields and require an expected `current_checked_out_branch` only
when exact branch identity is a declared safety invariant. Require
`current_baseline_branch`, `comparison_baseline`, and
`integrated_baseline_mode` only when decision-material; omission does not
remove or reinterpret their contracts, change permanent TOPEFT roles, or
bypass the live applicable-feature lifecycle gate. If a decision-material
branch fact cannot be established, stop rather than infer authority.

If branch behavior is missing or ambiguous, stop and include:

```text
branch_escalation_note
```

When `integrated_baseline_mode: yes`, treat the declared integration branch as
current source of truth and do not reopen historical feature branches unless
explicitly requested.

For a repository with module-defined permanent roles, this instruction
concerns integration/source context only and does not change those roles or
reuse-first eligibility of an applicable active feature.

Remote branch commits are live state. Query them when current values matter;
do not reuse an old remote SHA as current-state evidence.

### Conditional integration and publication lifecycle

When a workstream uses the applicable surfaces, distinguish these review and
effect boundaries rather than treating them as one generic merge operation:

```text
feature_review
integration_or_reconciliation_review
upstream_publication
merge
post_merge_tree_readback
optional_history_normalization
```

This is a conditional lifecycle overview, not a mandatory fork-staging design.
Existing prompt modes retain ownership of each action: feature development and
review use their development contract, local integration uses
`integration_only`, remote publication and any guarded normalization use
action-specific `pr_publication`, and merge remains a separate authorized
decision. Reference and integration branches remain non-development surfaces.
One closure boundary does not authorize the next.

Integration or reconciliation review covers the complete reviewer-visible
delta, not only the latest conflict-resolution commit. When both sides of a
conflict carry meaningful behavior, do not blindly select `ours`, `theirs`, or
a whole-file replacement. Classify ownership using the minimum applicable,
non-exhaustive classes:

```text
feature_supersedes_equivalent_upstream
independent_upstream_behavior_survives
obsolete_surface_disappears
compatibility_contract_survives
```

An additional evidence-backed class is allowed when needed. After squash,
`tree_equality != history_equality`: tree identity may support accepted-evidence
reuse, but it does not establish commit-history identity or make history
normalization mandatory.

---

## 8. Model, reasoning, and delegation

Every prompt must declare:

```text
preferred_codex_model
reasoning_level
delegation_policy
model_selection_rationale
```

Concrete Codex model labels:

```text
gpt-6-luna
gpt-6-sol
gpt-6-astra
```

Legacy/fallback-only concrete labels, subject to the conditions below:

```text
gpt-5.6-luna
gpt-5.6-terra
gpt-5.6-sol
```

Concrete catalog membership is an allowed governance vocabulary, not an
empirical model ranking. The routing guidance below consists of adopted
operational defaults based on mixed attributed evidence and owner choice. The
closed pilot produced 6/6 usable reviews for each requested High configuration
but did not establish a winner, general equivalence, production-critical
routing qualification, cost or latency claims, or a reason for automatic
additional benchmarking.

Andrea together with `lane_governance` owns decisions and revisions for these
general rules. The owning lane's prompt author selects and motivates each
concrete model/reasoning pair under them. The central control plane receives
and preserves the rules in checkpoints; it does not author prompts, choose the
pair, or approve each compliant selection. Codex executes the dispatched
profile and may report a need to reclassify, but it must not silently switch.

`explicit_fallback` is a fallback selection and reporting state, not a concrete
model identity. It is not valid as `preferred_codex_model` for an execution-ready
dispatch, as `model_profile.model`, or as the value passed to `-m`, and it never
authorizes automatic runtime model selection. Before a fallback execution
attempt begins:

```text
owning_lane_prompt_author:
  selects_one_concrete_codex_model_label

new_attempt:
  preferred_codex_model: selected_concrete_label
  model_profile.model: selected_concrete_label
```

Record the fallback path through the existing `fallback_or_switch` provenance
surface. Do not create a second fallback mechanism or a persistent
`resolved_model` field.

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

For an execution-ready Codex CLI dispatch, derive `model_profile` from the
existing prompt fields:

```text
model_profile:
  model: preferred_codex_model
  reasoning_effort: reasoning_level
```

Both `preferred_codex_model` and `model_profile.model` must be one of the
concrete Codex model labels above. A fallback selection state is not
execution-ready until the owning lane's prompt author selects that concrete
label and issues a new explicit dispatch with the relevant owner authorization.

Do not create duplicate persistent model or reasoning fields to restate this
profile. `delegation_policy` and `codex_cli_mode` remain separate execution
controls and are not members of `model_profile`.

Materialize a governed Codex CLI profile invocation-locally:

```text
model:
  -m <concrete_codex_model_label>

reasoning_effort:
  -c 'model_reasoning_effort="<reasoning_level>"'
```

Never pass `explicit_fallback` to `-m`.

The governance allow-lists remain authoritative because the local CLI bootstrap
parser accepts arbitrary strings. Parser or bundled-catalog acceptance does not
prove runtime application, service availability, or account availability.

The atomic profile-governance boundary is:

```text
execution_attempt:
  one Codex execution attempt
  one immutable model_profile
```

This boundary does not redefine `one_round_one_decision`. A logical round,
workstream, or continuation may use later separately dispatched attempts, but a
material model or reasoning change never occurs silently inside the current
attempt.

If the executor determines that the dispatched profile no longer fits the
remaining task, it may recommend a reclassification using:

```text
direction:
  upward
  downward

cause:
  model_capacity_mismatch
  reasoning_effort_mismatch
  both
```

The executor may recommend the change but must not materialize it. Any model
change, reasoning-only change, upward change, or downward change requires:

```text
current_execution_attempt: stop
next_profile: selected_by_owning_lane_prompt_author
continuation: new_dispatch_required
```

Automatic self-routing and silent in-attempt profile substitution are
forbidden. An explicit fallback is a new-attempt outcome only after the owning
lane's prompt author selects its concrete model; `explicit_fallback` may record
that selection path but is not the attempted model. A new model or reasoning
value, including `high` to `medium`, requires the current attempt to stop and a
fresh explicit dispatch with the relevant owner authorization. Stop and report
before any fallback dispatch.

Canonical default guidance:

| Task or decision characteristics | Default |
|---|---|
| Mechanical work with fixed inputs and directly checkable results | `gpt-6-luna` / `medium` |
| Focused, bounded structured work | `gpt-6-luna` / `high` |
| Ordinary substantive work | `gpt-6-sol` / `medium` |
| Complex substantive work | `gpt-6-sol` / `high` |
| The hardest open or adversarial reasoning | `gpt-6-astra` / `high` |

Classify the substantive decision, not the lane label, project importance, or
file count. Select the minimum sufficient model/reasoning pair directly.
Executing an already qualified production protocol does not redesign it, and
profile choice never qualifies or authorizes production or any other campaign.

These are the five canonical defaults. `gpt-6-astra` / `medium` is not a
canonical tier. Explain the selected pair in `model_selection_rationale`.

Upper exceptions are limited to:

| Model/reasoning pair | Condition |
|---|---|
| `gpt-6-sol` / `xhigh` | Rare motivated exception |
| `gpt-6-astra` / `xhigh` | Rare motivated exception |
| `gpt-6-astra` / `max` | Explicit exceptional owner/eval-driven exception only |

Each upper exception requires a specific reasoning need and a bounded scope or
resource decision, without requiring a prior lower-tier failure. It confers no
additional authority and does not relax evidence or acceptance criteria.

GPT-5.6 Terra, Sol, and Luna are legacy/fallback only. Their use requires either
actual GPT-6 unavailability or exact historical reproducibility, together with
a fresh explicit dispatch and honest provenance. Availability does not justify
silent substitution or a claim of superiority.

Do not require a Luna-to-Sol-to-Astra progression, a reasoning ladder, a
universal second-model review, or consensus seeking. No automatic model or
reasoning escalation is allowed. Missing evidence, an ambiguous gate, a
qualified warning, a short answer, service rejection, or another non-cognitive
failure does not by itself demonstrate reasoning insufficiency; address the
relevant cause.

Historical benchmark/report model and reasoning labels remain historical truth;
do not rewrite them prospectively. Historical evidence does not establish GPT-6
availability, comparative ranking, cost, latency, or production qualification.

While ANDOCS remains at its external transitional path, this file and the
external ANDOCS `AGENTS.md` must carry semantically identical project-common
model-routing policy. Each CPC.md applies its path-applicable AGENTS.md and
must not maintain a competing complete routing matrix. The central ANDOCS
module does not itself switch routing authority at the old path.
CONTRIBUTING.md is not a model-routing authority.

Do not use Sol merely because a task is important. Do not compensate for an
undersized model with excessive reasoning. Reports must distinguish these
semantic values:

```text
requested_or_dispatched_model
requested_or_dispatched_reasoning_effort
directly_selected_model_if_observable
runtime_reported_model_label_if_observable
runtime_reported_reasoning_effort_if_observable
fallback_or_switch
```

Reuse existing report fields instead of emitting parallel mandatory aliases:
`preferred_or_configured_model` may carry
`requested_or_dispatched_model`, and `reasoning_level` may carry
`requested_or_dispatched_reasoning_effort`, when the meanings are identical.
Do not rename provider- or CLI-reported metadata as independently observed
runtime identity. When an exact value is unavailable, report `not_observable`;
do not infer an exact model from a generic family label. Record an observed
mismatch, fallback, or switch and stop under the reclassification rule.

When exact `model_profile` identity is decision-material, the prompt must
declare `required_profile_agreement_evidence`, and execution must fail closed if
that evidence cannot be established. Empirical model-profile qualification is
one such case. Otherwise record the requested or dispatched profile and all
available CLI/runtime reporting honestly; unknown remains unknown. Unavailable
exact runtime identity is not a universal blocker for ordinary work, but any
observed profile mismatch or switch requires stop and reclassification.

`Ultra` is an orchestration mode, not a reasoning level. Encode it only when
explicitly authorized:

```text
reasoning_level: max
delegation_policy: allowed
codex_cli_mode: ultra
```

Use `delegation_policy: required` instead when the exact workflow requires
delegation; both values remain members of the closed vocabulary.

Do not use Ultra for narrow controlled work, commit preparation, publication,
or production execution.

---

## 9. Decision-focused task contracts

Every round must state one substantive question:

```text
decision_question
```

`goal` is optional. Include it only when it adds a distinct execution
objective that cannot be safely inferred from `decision_question`; omit it
when it merely restates that question. Omitting `goal` cannot widen scope or
authority.

Derive prompt relationship from `continuation_of`:

```text
continuation_of present and non-empty: continuation
continuation_of absent: standalone
```

Do not serialize `prompt_relationship` in author-facing prompt metadata or add
a second relationship field or alias. This derived relationship is orthogonal
to `prompt_mode`; continuation is not a prompt mode.

For a continuation, `continuation_of` is required. Include other continuation
fields only when they carry actual non-empty state:

```text
delta_scope                 when work is explicitly scoped relative to prior work
accepted_prior_evidence     when prior evidence is reused
accepted_closure_layers     when non-empty closure layers are reused
invalidation_boundary       when accepted evidence/closure is preserved outside a reopened boundary
unresolved_checks_only     when unresolved checks are carried
checks_not_to_repeat        when accepted checks are protected from repetition
```

`continuation_of` identifies the exact prior round or accepted artifact set.
`accepted_closure_layers` names only closure claims already established by
readable evidence. `invalidation_boundary` states what change or unresolved
condition can reopen that evidence. `delta_scope` states the changed, newly
unresolved, and directly coupled reachable surfaces to validate now.
Omit inapplicable continuation fields. Do not serialize `none`, empty lists, or
boilerplate placeholders. Omission means no such state is asserted; it must not
fabricate accepted, closure, invalidation, or deferred-check state. Reuse
accepted evidence outside its invalidation boundary, and keep any declared
`checks_not_to_repeat` authoritative; omission does not authorize repeating
accepted checks.

Rules:

* One round normally answers one decision question. `orchestrated_workflow`
  may compose multiple activity types only when they remain inside that one
  substantive decision boundary and advance through predeclared objective
  gates.
* Cite prior evidence by exact artifact and locator instead of copying reports.
* Do not rerun accepted checks unless source/input changed, evidence is missing
  or invalid, or the user requests it.
* Do not combine independent implementation-closure, archaeology, production,
  publication, merge, or campaign-planning decisions in one round.
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

### Reusable mechanism selection

Choose the smallest mechanism that matches the recurring contract:

```text
subagent:
  bounded independent perspective when delegation is explicitly authorized

skill:
  stable reusable transformation or validation protocol

orchestrated_stage_pattern:
  decision-specific gated work

checklist:
  presentation or review aid without execution authority
```

The controlling workflow or human retains decision authority. A mechanism must
not invent authorization, broaden scope, or become the sole owner of a
safety-critical rule. Do not create a specialized-agent registry merely to
record reusable role names.

Project-local capability helpers do not own workflow authorization. A helper's
failure, staleness, incompatibility, or unavailability is local to the artifact
or operation that helper owns unless the current explicitly authorized workflow
requires that exact helper output. A helper failure cannot revoke or block an
independently authorized underlying activity, and helper output cannot create
authorization.

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

For ordinary non-action-specific prompts, omitted
`heavy_command_permissions` means `all_no`. Every positive capability grant
must be explicit. Action-specific publication, merge, and normalization
permission contracts remain mandatory as written.

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

For Git-over-SSH commands executed by Codex on glados, select the exact
prompt-authorized repository with either its native process working directory
or `git -C <exact_prompt_authorized_repository_path>`, and use the
command-scoped override:

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

Canonical exact-branch fetch when explicitly authorized:

```bash
git \
  -C <exact_prompt_authorized_repository_path> \
  -c core.sshCommand='/usr/bin/ssh -F /dev/null' \
  fetch \
  <remote> \
  refs/heads/<remote_branch>:refs/remotes/<remote>/<remote_branch>
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
* Native process working directory and `git -C <exact_prompt_authorized_repository_path>`
  are both valid Git repository-selection mechanisms. For `gh` or `glab`,
  native repository working directory, an explicit repository selector, and an
  explicit repository-qualified API/resource endpoint are valid when supported.
  Command location and repository-selection syntax are execution context, not
  proof of authorization, repository identity, or publication correctness.
* The prompt or stage must independently authorize the exact repository and
  action. Repository selection must not widen writable scope, and
  decision-material repository identity requires readback.
* Use the override for `ls-remote`, fetch, and push.
* Never use `--force`. Use `--force-with-lease` only for the explicitly
  authorized `normalize_declared_post_squash_staging_ref` action and only in
  its exact `--force-with-lease=<ref>:<exact_old_sha>` form. Wildcard refspecs,
  implicit multi-ref pushes, and deletion remain forbidden unless separately
  authorized by their own applicable contracts.
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
conditional feature-branch push when the fresh remote feature HEAD differs
and `remote_git_write: yes`
remote feature HEAD verification
post-synchronization duplicate check
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

Omitted `preflight_profile` means `compact_preflight`; require explicit
`expanded_preflight` when needed. Omitted `dirty_worktree_policy` means
`require_clean_worktree`; any alternative must be explicit.

`preflight_scope_paths` may be omitted only when the exact minimum task-path
set is already determined by `authorized_commit_scope` or an exact
`allowed_to_modify` target, explicitly named read-only target paths, and
decision-relevant input, output, or artifact paths. A broad permission or
read-only declaration does not by itself determine that set. If the intended
preflight differs from the directly derivable set, the facts permit multiple
sets, or a special collision or dirty-state check concerns an otherwise
unnamed path, declare `preflight_scope_paths` explicitly. Omission never means
the whole repository, a broad untracked inventory, or permission to inspect
unrelated paths.

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

Unless a prompt explicitly requires a physically empty worktree for a stated
invariant, `require_clean_worktree` means no tracked worktree changes, no index
changes, and no conflict state. A task-scope untracked path that collides with
an intended input or output is material and must be resolved or explicitly
accepted before the action. Unrelated pre-existing untracked files are allowed
under a compatible dirty policy, must be preserved as-is, and must not be
inventoried without a task-specific reason. These defaults do not collapse the
other dirty policies: their declared treatment of known pre-existing tracked
or task-scope changes remains controlling.

Never use without explicit authorization:

```text
git clean
git reset
git restore
git checkout -- <path>
git stash
```

Do not stage with `git add .` or `git add -A` unless an explicitly authorized
whole-worktree task has established that every affected change is task-owned
under section 14. Stage intended files by exact path.

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

Derive ordinary commit behavior from tracked repository-file mutation or
explicit adoption. Except for an exact owner-authorized `do_not_commit: yes`
round, a round that creates or explicitly adopts such changes cannot close
successfully while its task-owned or explicitly adopted tracked-file changes
remain uncommitted.
Outside that exception, successful closure requires those changes to be
committed in prompt-local history, with the task-scope index and tracked
worktree clean. For an orchestrated workflow, intermediate stages may leave
those changes uncommitted only until a later declared commit stage in the same
workflow commits them.
This does not require one commit per mutating stage.

For tracked mutation, `do_not_commit: yes` is permitted only when the owner
explicitly authorizes that exception for the exact round. If a safe commit
cannot be created in a commit-required round, stop incomplete. Read-only
rounds that create no tracked changes do not require a commit.

When no tracked repository-file mutation or adoption occurs, no commit is
required. Routine prompts need not serialize `commit_expected` or
`do_not_commit`. Absence of `do_not_commit: yes` never permits uncommitted
tracked mutation. The exact owner exception remains explicit.

### Change ownership and index isolation

At preflight for a round that may commit, and again immediately before staging
and commit, classify current index and working-tree changes as:

```text
task_owned_changes:
  created by the current round inside its authorized scope

explicitly_adopted_inherited_changes:
  pre-existing or inherited changes that a continuation explicitly declares
  and accepts as part of its own decision surface

foreign_dirty_changes:
  every other index or working-tree change
```

Authorization to modify a path does not by itself make an existing change on
that path task-owned. Continuation adoption must identify the exact inherited
paths or changes and their evidence; do not infer adoption from dirtiness,
proximity, or shared workstream membership.

`task_owned_paths` are the exact paths containing proven
`task_owned_changes`. The term is derived from actual change provenance; path
membership or authorization does not confer ownership on pre-existing or
foreign changes in the same path.

`explicitly_adopted_inherited_paths` are the exact paths containing
`explicitly_adopted_inherited_changes`. The term is derived from the exact
adopted changes; path membership does not adopt or confer ownership on any
other pre-existing or foreign change in the same path.

When the round will commit tracked changes, the prompt must declare
`authorized_commit_scope`: the exact subset of `allowed_to_modify` authorized
for the current commit. It governs commit eligibility only. Ownership or
continuation adoption does not expand it.

For a prompt-local commit, all invariants are mandatory:

```text
staged_paths subset_of authorized_commit_scope
staged_paths subset_of task_owned_paths union explicitly_adopted_inherited_paths
staged_diff contains_only task_owned_changes or explicitly_adopted_inherited_changes
```

Stage exact declared paths only. `git add -A` and `git add .` are forbidden
unless an explicitly authorized whole-worktree task has established that every
affected change is task-owned. The complete staged path list and staged diff
must still be reopened afterward. A path that contains mixed owned and foreign
changes must not be staged as a whole; if the owned change cannot be isolated
safely, stop before commit.

`git commit -a` is unconditionally forbidden for prompt-local commits. It
stages tracked modifications during the commit invocation and can therefore
change staged content after the mandatory staged-diff readback. The commit
command must use an index that was already fully materialized and directly
reviewed.

Immediately before commit, reopen both the staged path list and the complete
staged diff. If either contains a foreign change, stop the commit and preserve
the working-tree content. In a conflict-free index, Codex may use only:

```bash
git restore --staged -- <exact_foreign_path>...
```

to unstage exact foreign paths after recording their index and working-tree
state. Reopen both states afterward and prove that working-tree content was not
modified. This is narrow authorization for that index-only operation; it does
not authorize `git reset`, `git restore` without `--staged`, checkout, discard,
cleanup, or conflict resolution. If index-only behavior or content
preservation is indeterminate, leave the index unchanged and stop.

These ownership rules apply per Git index and working tree. They do not
prohibit concurrent mutation in independent repositories or separate
worktrees with separate indexes. A programme may require stronger
serialization for rounds sharing one working tree; state that operational rule
in the applicable programme prompt or control-plane contract.

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

Also permits bounded no-submit workflow/configuration probes and, when an
applicable repository module requests it, a bounded repository-supported
document build/render validation. The prompt must separately authorize the
commands, outputs, and side effects under applicable root and native policy.
This ceiling forbids production submission and large campaign or output
generation; it does not imply analysis-output regeneration.

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

### Publication-grade review

Publication-grade review is the default for these sign-off surfaces:

```text
integration_or_reconciliation_sign_off
remote_publication_or_merge_sign_off
scientific_or_analysis_sign_off
migration_or_deprecation_sign_off
repository_history_normalization_sign_off
```

It is triggered by the sign-off claim, not by file count. Ordinary bounded
coding does not acquire publication-grade review overhead merely because it
touches multiple files or includes focused validation.

A publication-grade review report must classify:

```text
confirmed_blockers
additional_unresolved_risks
not_yet_evaluated
closed_with_evidence
confidence_in_completeness
```

Do not describe a finding as the `only blocker`, or use equivalent completeness
language, until the permitted review surface is exhausted. When membership
matters, report exact identity sets rather than counts alone. Safe authorized
read-only review should continue after the first blocker when the review
surface and terminal tail were preauthorized; section 6's terminal-tail rule
still forbids mutation, scope enlargement, gate bypass, or return to execution.

Correlate every applicable implementation, test, fixture, asset,
documentation, warning, skip, reviewer-claim, and live-remote-state surface.
Changed tests are evidence, not automatically semantic authority; a test is
authoritative only when the maintained contract for the decision identifies it
as such. Passing tests do not override the resolved maintained semantic,
specification, or consumer contract. Material warnings and skips are evidence
surfaces and require relevance and disposition. A deletion, migration, or
deprecation requires successor, ownership, and consumer classification, or
evidence-backed intentional retirement. When fixing a shared early exception
can unmask later failures, rerun the complete affected reachable surface and
classify each newly exposed failure independently.

### Closure layers

Use only the closure claims applicable to the decision:

```text
semantic_or_scientific_closure
test_closure
documentation_closure
publication_closure
upstream_merge_closure
repository_history_normalization_closure
```

One layer does not imply another, and a deficient layer does not automatically
invalidate an accepted layer. Reopen another layer only when its evidence is
inside the applicable invalidation boundary or a direct dependency between the
layers is established. Naming the vocabulary does not require every report to
emit all six layers or authorize an action belonging to another layer. A
publication-grade review still reports unresolved deficiencies in its five
evidence buckets and must not use layer independence to bypass a blocker that
is material to the sign-off claim.

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

Publication validation for `create_or_reuse_open_pr_or_mr` must establish:

```text
local branch and exact HEAD
local tracked/index state
live remote base
fresh remote feature HEAD equals the exact expected local HEAD
remote feature synchronization outcome: remote_branch_already_synchronized or pushed_non_force
duplicate PR/MR state
PR/MR repository, base, head, head commit, title, state, and draft status
absence of force push
absence of unauthorized merge or remote deletion
final local tracked/index state
```

Publication validation for `synchronize_declared_remote_branch` must instead
establish:

```text
local repository, declared local ref, and exact expected local HEAD
declared remote, remote branch, and local remote-tracking ref
initial exact live remote branch HEAD
the objective topology rule that selected query, fetch, push, or no action
fresh exact live remote branch HEAD after the action
declared local remote-tracking ref after any fetch
absence of force push, remote deletion, PR/MR mutation, and merge
final local tracked/index state
```

Publication validation for
`normalize_declared_post_squash_staging_ref` must instead establish:

```text
exact remote ref and freshly observed old SHA
exact target SHA and declared normalization identity basis
local archive ref identity and reachability
remote archive ref identity and reachability before rewriting remote history
exact force-with-lease argument bound to the observed old SHA
fresh remote ref readback after the write
final expected local, archive, staging, and upstream identities as declared
absence of generic force, lease refresh, PR/MR mutation, merge, or deletion
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

For a continuation, validate the delta: changed or newly unresolved behavior
plus directly coupled reachable surfaces. Inherit accepted validation outside
the declared invalidation boundary. The boundary expands when direct evidence
shows additional reachable coupling, so this rule never suppresses an
affected-surface rerun required elsewhere in this policy.

A cumulative checkpoint or other handoff is evidence and context, never
authorization. It may preserve stable accepted evidence, but any decision that
depends on volatile branch, dirty-worktree, PR/MR, CI, permission, scheduler,
storage, or external-service state requires fresh authoritative readback.

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
continuation_of
accepted_prior_evidence
accepted_closure_layers
invalidation_boundary
delta_scope
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
/users/apiccine/work/correction-lib/reports/diagnostics/<prompt_id>/
```

Canonical files:

```text
<prompt_id>_report.md
<prompt_id>_worktree_diff.patch
```

`prompt_id` is the deterministic round slug and must uniquely identify the
round; do not append a second title-derived slug. A prompt may declare exact
custom artifact paths when the canonical names do not fit its artifact kind.
These are expected locations only. Resolve the actual directory at runtime;
if it exists, use a deterministic `_rerun_00N` suffix and report the earlier
path. Record the actual report and patch paths, including that suffix, rather
than deriving collision outcomes from the prompt.

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
prompt_relationship
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
files_changed
implementation_or_evidence_summary
validation_commands_and_results
generated_artifacts
report_directory
patch_path
patch_kind
pre_existing_worktree_state
commit_summary
open_questions_or_caveats
recommended_next_action
final_cleanliness
```

Include `accepted_prior_evidence` and `checks_intentionally_not_repeated` only
when they carry actual prior evidence or protected checks. Include
`prompt_local_diff` when this round changes tracked files and
`branch_cumulative_diff` when a cumulative comparison is decision-material.
For a read-only no-mutation round, record `files_changed: none`,
`commit_summary: none`, and an `empty_no_changes` patch; do not invent diff
fields. These conditional omissions do not remove identity, effect,
validation, provenance, caveat, or actual artifact-path evidence.

Classify an incomplete or inaccurate report field as one of:

```text
decision_material_reporting_defect
non_blocking_reporting_defect
```

A `decision_material_reporting_defect` withholds evidence needed to establish
the substantive claim and blocks that claim until repaired. A
`non_blocking_reporting_defect` affects only descriptive or presentation
material whose absence cannot change the decision; repair it without reopening
accepted closure layers. Missing substantive evidence must not be relabeled as
a reporting-only defect or manufactured during a reporting repair.

A `non_blocking_reporting_defect` alone does not justify a new Codex round.
Record it in the durable report or supervisor state and repair it in the next
naturally authorized continuation, publication, integration, or documentation
round. Open an immediate evidence-repair round only when the user explicitly
requests it or a later authorized effect requires the missing canonical
evidence before it can proceed.

Reports for `create_or_reuse_open_pr_or_mr` or
`merge_existing_pr_or_mr` also include:

```text
publication_platform
publication_repository
publication_remote
publication_base_branch
publication_feature_branch
expected_local_head
live_remote_base_head
remote_feature_head
remote_feature_sync_outcome
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

For `create_or_reuse_open_pr_or_mr`, `remote_write_commands` may be empty only
when `remote_feature_sync_outcome` is `remote_branch_already_synchronized` and
the required fresh remote feature-HEAD readback equals `expected_local_head`.

Reports for `synchronize_declared_remote_branch` instead include:

```text
publication_action
publication_platform
publication_repository
publication_remote
publication_local_branch
publication_remote_branch
publication_remote_tracking_ref
expected_local_head
initial_live_remote_branch_head
final_live_remote_branch_head
remote_tracking_ref_head_after_fetch_when_applicable
remote_write_commands
force_push_used
pr_or_mr_write_performed
merge_performed
remote_branch_deleted
```

Reports for `normalize_declared_post_squash_staging_ref` instead include:

```text
publication_action
publication_platform
publication_repository
publication_remote
exact_remote_ref
exact_observed_old_sha
exact_target_sha
verified_local_archive_ref
verified_remote_archive_ref_when_remote_history_is_being_rewritten
archive_reachability
normalization_identity_basis
force_with_lease_argument
initial_live_remote_ref_head
final_live_remote_ref_head
final_expected_identity_readback
generic_force_used
lease_refreshed_after_unexplained_movement
pr_or_mr_write_performed
merge_performed
remote_branch_deleted
```

When publication-grade review applies, also include its five evidence buckets
from section 18. They are conditional review fields, not universal report
ceremony.

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
changed_paths
commit_patch_path
```

Also include `file_stat` when the decision question, an explicit gate, or a
repository-local review contract makes the insertion/deletion summary
decision-material. Otherwise it is recommended descriptive evidence and its
absence alone is non-blocking.

`changed_paths` and an exact reviewable commit delta remain mandatory.
`commit_patch_path` may reference the round's mandatory patch only when direct
comparison proves that patch is exactly equivalent to the commit delta;
otherwise create a separate commit patch.

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

`pr_publication` may synchronize one declared remote branch or publish an
already validated branch and create/update the requested PR/MR under sections
11–12. It must not change source, create commits, rewrite history, force-push,
delete remote branches, or merge unless the applicable action-specific
contract and exact user authorization allow that effect. Generic force remains
forbidden; only `normalize_declared_post_squash_staging_ref` may use its exact
old-SHA force-with-lease. PR/MR merge is forbidden inside
`orchestrated_workflow` even when other non-merge publication actions are
composed there.

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

The canonical report is the full evidence record. The final chat response is
its compact actionable projection; it must not repeat every report field.
Include the following when applicable:

```text
decision_question
final verdict or status
direct answer to the decision question
relevant repository, branch, HEAD, and commit identity
decisive validation or evidence result
actual report directory and report path
patch or artifact path and kind, when produced
remote, publication, merge, or destructive effect, when any
production or output effect and path, when any
material blocker or caveat
recommended next action
```

Keep the canonical report as the detailed record. A report path alone is not
the result handoff. `OPERATIVE_COMMANDS.md` carries input and launch
instructions; it does not hand results back.

Whenever an actual diagnostics directory exists, the final response MUST end
with these two lines, using the exact directory that was created. Preserve any
actual `_rerun_00N` suffix:

```bash
FOLD=<exact actual diagnostics directory>
scp -r apiccine@glados.crc.nd.edu:${FOLD} .
```

Do not omit or soften failure, blocked status, indeterminate identity, remote
mutation, merge, destructive or history-normalization effects, production or
output locations, or material unresolved caveats. This projection does not
change the canonical report schema.

PR/MR publication or merge responses also include:

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

Branch-only synchronization responses instead include:

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
non_force_explicit_refspec_used_when_push_performed
duplicate_pr_or_mr_guard_applied
remote_feature_head_verified
published_pr_or_mr_read_back
merge_not_performed_without_separate_authorization
remote_branch_not_deleted_without_separate_authorization
no_publication_success_claim_without_remote_readback
```

---

## 26. Project-local skill registry

The project-local skills are:

```text
correction-lib-prompt-contract
correction-lib-manual-production-handoff
correction-lib-diagnostics-execution-copy
correction-lib-codex-evidence-package-review
```

Resolve each installed skill from `.agents/skills/<skill_name>/SKILL.md` and
read its current `name` and description for identity and trigger. The live
`SKILL.md` owns its operation and safety boundary; live `AGENTS.md` and
`CPC.md` remain the normative governance sources. This registry does not
declare a package or executable version. Resolve a decision-material component
version from that component's own current artifact rather than a duplicated
registry value.

Skill availability alone authorizes no task action. In particular, the manual
handoff skill does not authorize production execution, the diagnostics-copy
skill does not authorize execution of copied files, and the evidence-review
skill does not authorize reviewed work, code execution, patch application,
fixes, other skills, or publication. The prompt-contract skill provides
mechanical authoring help, not governance certification.
