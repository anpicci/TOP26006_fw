# Git lifecycle, commit, integration and publication contract

Load for every trigger in AGENTS.md. This contract is normative for execution and prompt construction. Paths and explicit owner grants bound all actions. Permission names listed separately in tables/code blocks are keys of heavy_command_permissions for a non-orchestrated prompt or stage_effect_permissions for an orchestrated stage, never both. workflow_effect_envelope only caps possible stage grants. Retain action-specific explicit denials. A true capability flag alone never authorizes an action.

Never run git fetch unless explicitly authorized. Never use git pull in a publication round.

## Conditional prompt fields

For committing, declare authorized_commit_scope, explicitly_adopted_inherited_changes (exact changes and evidence, or none), foreign_dirty_change_policy: preserve_and_exclude and staging_policy: exact_path_only. A do_not_commit: yes exception requires exact owner authorization. For integration declare integration_source_branch, integration_target_branch, integration_method and expected_source_head. In an orchestrated integration stage, these are stage-local action fields, not outer fields or duplicate entries in stage_effect_permissions. The stage also declares stage_branch_policy: continue_existing_branch and stage-local target_branch matching integration_target_branch. Its stage_effect_permissions must grant the exact local index/ref effects for that action through allowed_to_modify; these positive effect grants do not replace the action fields. A non-orchestrated integration uses branch_policy: continue_existing_branch and target_branch at prompt level. read_only_current_branch cannot switch or move a ref.

For branch maintenance declare branch_maintenance_action, affected_local_branches, expected_preserved_head, preservation_ref, reference_restore_source, non_fast_forward_ref_move_authorized and local_branch_deletion. State none with a reason for an inapplicable identity, never for an unresolved required identity. local_branch_deletion and remote_branch_deletion default no. List safety-critical ref commands exactly.

For publication declare publication_action, publication_platform, publication_repository, publication_remote and expected_local_head. For create_or_reuse_open_pr_or_mr additionally declare publication_base_branch, publication_feature_branch, duplicate_pr_or_mr_policy: reuse_exact_open_match_else_create_one and draft_allowed: no unless explicitly authorized otherwise. An exact open match agrees on repository, base and feature branch; multiple or ambiguous matches stop. Each action below supplies its further required fields and permissions.

An exact authorized native Git branch, ref, or integration command may create
inseparable intrinsic local bookkeeping metadata, such as `ORIG_HEAD` or
reflogs. Treat that metadata as evidence of the command, not as a grant to move
an unrelated branch, tag, or remote-tracking ref. Every intended branch, ref,
or `HEAD` movement still requires the existing exact action and ref authority.
When material, record and read back observable intrinsic bookkeeping alongside
the authoritative refs. Unexpected authoritative ref movement is a discrepancy,
not bookkeeping; stop the dependent action. This observation does not authorize
reset, ref surgery, history rewrite, cleanup, force movement, or remote mutation.

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
separate direct command under this contract's Remote Git and publication policy on glados, including the command-local glados
SSH override when applicable.

A `normalize_declared_post_squash_staging_ref` round must perform its archive,
reachability, old-SHA, target-identity, exact-lease, and final-identity gates in
the declared order. Each `git ls-remote`, `git fetch`, and `git push` operation
remains a separate direct command under this contract's Remote Git and publication policy on glados. Any missing archive,
indeterminate identity basis, unexpected remote movement, or post-write
readback mismatch stops the action without a retry, lease refresh, merge,
deletion, or improvised rewrite.

Merge must be a separate decision round with `pr_or_mr_merge: yes` and
`merge_allowed: yes`.

## Branch policy

A non-orchestrated prompt declares one branch_policy per relevant repository.
An orchestrated workflow omits outer branch_policy; every branch-relevant
stage declares exactly one stage_branch_policy, whose authority ends with
that stage. Both use the same closed vocabulary:

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
namespace constraints and repository-specific permanent branch roles are in
their registry-named modules. The generic reuse-first lifecycle above remains
binding. A generic baseline field cannot override a module's permanent role.

Require `reference_branch` and `feature_branch` for
`create_feature_branch_from_reference`, and `target_branch` for
`continue_existing_branch`. For `read_only_current_branch`, omit synthetic
`none` branch fields and require an expected `current_checked_out_branch` only
when exact branch identity is a declared safety invariant. Require
`current_baseline_branch`, `comparison_baseline`, and
`integrated_baseline_mode` only when decision-material; omission does not
remove or reinterpret their contracts, change module-defined permanent branch roles, or
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

### Permanent live development and promotion cuts

A repository module may declare one
`permanent_live_development_branch`. That branch is the long-lived
TOP-26-006 development surface for that repository. It is distinct from
module-defined personal/reference and integration/upstream branches, which
remain non-development surfaces.

When a permanent live development branch is declared and is applicable to the
workstream, ordinary tracked TOP-26-006 development continues on that branch.
Do not create a new task/development branch merely to isolate ordinary work.
An additional development branch is exceptional and requires an explicit
owner-authorized exception identifying the concrete isolation need, branch
name, relationship to the permanent live line, intended successor or merge
target, and retirement condition. The exception does not itself authorize
publication, merge, deletion, force movement, cleanup, or another lifecycle
effect.

The permanent live branch remains subject to fresh branch, HEAD, dirty-state,
worktree and semantic-applicability readback. A permanent branch name is not a
durable commit identity and does not bypass repository-native policy or exact
round authorization.

When a promotion wave is defined from a moving permanent live line, select an
exact committed `source_cut` for that wave. The `source_cut` is the immutable
content identity for the promotion; later commits on the permanent live branch
do not enter that wave automatically. Publish or reconcile through an
explicitly temporary promotion carrier when the applicable repository module
or promotion contract requires one; the carrier does not become a continuing
development authority.

After a reviewer-visible promotion result is accepted, use that exact accepted
result as the downstream promotion authority for the same wave rather than a
later-moving permanent-live HEAD. If the applicable repository module requires
history convergence, reconcile that accepted result back into the permanent
live development genealogy under an explicit integration/reconciliation round
before selecting the next promotion cut. A module may impose stronger
repository-specific parentage, ancestry, or convergence requirements.

Promotion-carrier and worktree retirement conditions should be declared when
the carrier is created. Expected retirement is not advance deletion
authorization: local branch deletion, remote branch deletion and worktree
removal remain separately governed actions with fresh safety evidence.

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

## Remote Git and publication policy on glados

In an observed workspace-write configuration on glados, remapped ownership of
the system SSH configuration caused OpenSSH to reject:

```text
/etc/ssh/ssh_config.d/50-redhat.conf
```

even though the host file has correct ownership and permissions. This failure
is environment-dependent; an externally selected Full session may not need the
workaround. Do not run an SSH probe without independently authorized network
access.

For separately authorized Git-over-SSH commands on glados, select the exact
prompt-authorized repository with either its native process working directory
or `git -C <exact_prompt_authorized_repository_path>`. If the observed
environment needs the system-config workaround, use this command-scoped
override:

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

Conditional read-only query example, requiring `network_access: yes`:

```bash
git \
  -c core.sshCommand='/usr/bin/ssh -F /dev/null' \
  ls-remote \
  <remote> \
  refs/heads/<branch>
```

Conditional exact-branch fetch example when explicitly authorized:

```bash
git \
  -C <exact_prompt_authorized_repository_path> \
  -c core.sshCommand='/usr/bin/ssh -F /dev/null' \
  fetch \
  <remote> \
  refs/heads/<remote_branch>:refs/remotes/<remote>/<remote_branch>
```

Conditional publication push example when explicitly authorized:

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
* Use the override for `ls-remote`, fetch, and push only when the observed
  environment requires it; these examples do not authorize network or remote
  effects.
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

## Source-control and commit policy

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

## Reviewer-facing, preparation, publication, and merge discipline

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
already validated branch and create/update the requested PR/MR under AGENTS.md's effect permissions and this contract. It must not change source, create commits, rewrite history, force-push,
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

## Merge gate and manual provenance

For merge_existing_pr_or_mr declare pr_or_mr_number_or_url and exact merge method (merge, squash or rebase), and require explicit pr_or_mr_merge: yes and merge_allowed: yes. Remote source-branch deletion is a separate exact grant. Immediately before merge read back open state, draft status, base/head branches, exact head commit, mergeability/conflicts, required checks/CI where available and review state required by native policy. A missing required check is not a pass. After merge read back merged state and resulting commit. A user manual merge needs no additional Codex round; a later dependent action still verifies current relevant state.

## Publication reporting

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

## Integration and preservation reporting

Record source/target identities, method and explicit authority, preservation refs/reachability, resulting identities, complete reviewer-visible delta, relevant index/worktree state and remaining boundaries. Do not infer history equality from tree equality. An interrupted side effect uses AGENTS.md's ambiguous-interruption rule; publication cannot retry based solely on missing stdout.
