# AGENTS.md — TOP26006_fw operating policy

## Authority and invariants

TOP26006_fw is the TOP-26-006 coordination meta-repository. Its checkout name
does not change its identity. governance/repositories.md owns typed repository
roles; independent repositories retain separate histories, indexes, branches,
native policy and scientific ownership.

This file owns execution and delegates conditional rules to the contracts
below. CPC.md owns prompt construction; CONTRIBUTING.md owns reviewer prose.
Registry-named modules add repository-specific constraints. Applicable nested
AGENTS.md and upstream/native policy also bind the action. Explicit owner
instructions may override project rules; identify the exact override. Stop on
an unresolved conflict. A module, skill, tool, checkpoint or generated prompt
cannot create owner authorization or silently weaken an applicable rule.

The owner decides scope, effects and scientific decisions. Executor completion,
reviewer agreement, tests and tool approval are evidence, never self-acceptance.
One round answers one substantive decision_question. Multiple activity types
may share that decision through the orchestration contract. A genuinely new
choice stops unless its action and objective selection gate were preauthorized.

Use the minimum sufficient scope. Preserve foreign work. Do not expand scope,
clean up, add compatibility shims or rewrite history without exact authority.
Use snake_case for new local names unless an existing interface requires
otherwise. Expected values describe inputs or safety invariants, never desired
audit outcomes. Collect evidence, serialize it, reopen and validate it, then
classify and derive the verdict. Names are not runtime evidence.

Reuse accepted evidence unless relevant source/input/environment changed,
evidence is missing, unreadable, invalid or contradictory, the owner requests
revalidation, or current external state is material. Checkpoints are context,
not authority. Observe current branch, dirty state, permissions, CI, scheduler,
storage and service state when the decision depends on them. Tree identity
does not establish history identity.

## Required reading router

At task start read this core, CPC.md's compact contract, the selected registry
entry and its named module, and every path-applicable AGENTS.md. Record paths
read. Evaluate ALL following triggers against the requested actions, claims and
effects, not filenames, tier labels or prompt mode alone. Load the union of
applicable contracts before acting; a newly exposed trigger requires loading
its contract before the dependent action. If applicability or a needed contract
is unresolved, stop that dependent action; omission never waives a rule.

| Trigger | Additional required source |
|---|---|
| Tracked mutation/adoption/commit, branch, ref or linked-worktree lifecycle, integration, promotion, remote Git, publication or merge | governance/contracts/git_lifecycle.md |
| Orchestration, long-horizon work, delegation, independent reviewer or proposed parallel writes | governance/contracts/orchestration.md |
| Production/heavy execution, scheduler action, user-run production handoff, workflow configuration, production output/resume/recovery, or temporary payload/storage lifecycle | governance/contracts/production.md |
| Substantial work, audit/evidence classification, scientific/numerical/consumer comparison, sign-off, continuation closure, vendored dependency, or risk uncertainty | governance/contracts/review_and_evidence.md |
| Autonomous/adaptive execution, blocker classification, preauthorized fallback/repair, continuation after mechanism failure, or anti-artificial-blocker decision | governance/contracts/autonomy_and_blocker_classification.md |
| Selecting or changing model/reasoning, CLI dispatch, profile qualification or model-provenance dispute | governance/model_policy.md |
| Commit message, PR/MR, squash message or reviewer-facing prose | CONTRIBUTING.md |

Ordinary small work loads only the core/compact contract and applicable
repository policy plus contracts actually triggered. Contracts are normative
under this file; they do not grant effects. Read required referenced sections
even if a trigger begins inside another contract.

## Scope, effects and capability

Every prompt names repository IDs, preflighted paths, allowed_to_modify and
read_only. No repository is implicitly writable, including TOP26006_fw.
Diagnostics/storage grants do not authorize tracked edits. Unauthorized
cross-repository work stops with cross_repo_escalation_note; do not add a shim
to evade the boundary. Do not stage nested repositories in the coordination
history.

Keep existing permission names; do not create parallel aliases. The following
effect names are descriptive labels, not additional serialized permission keys.

| Effect | Canonical authorization surface |
|---|---|
| tracked_write | allowed_to_modify names exact repository, paths and write effects; selected mode permits them |
| local_git_ref_write | explicit branch/action/commit contract with exact repository and refs; branch policy alone does not grant an unspecified action |
| network_read | network_access in the applicable grant map plus exact service/read scope |
| remote_git_write | remote_git_write in the applicable grant map plus exact ref/action |
| scheduler_query | scheduler_query in the applicable grant map plus scheduler and bounded targets |
| scheduler_submit | condor_submission or work_queue_or_lobster_submission in the applicable grant map for the named backend and bounded action |
| production_storage_write | storage_writes in the applicable grant map plus exact outputs and production action |
| publication | pr_or_mr_write in the applicable grant map plus exact PR/MR action |
| merge | pr_or_mr_merge and merge_allowed in the applicable grant map plus exact separate merge decision |
| delete | exact delete action/paths; local_branch_deletion or remote_branch_deletion when applicable |
| unblind | unblind in the applicable grant map and exact scientific-owner authorization |

For a non-orchestrated actionable prompt, heavy_command_permissions is the
sole positive capability/effect-grant map. For orchestrated_workflow, the outer
heavy_command_permissions and branch_policy fields are prohibited:
workflow_effect_envelope is only a ceiling and stage_effect_permissions is
the sole positive grant map for each stage. The orchestration contract owns
stage_branch_policy. All positive grants are explicit and scope-bounded;
omitted capability keys mean no. For staged work the orchestration contract
requires separate local grants, including path/ref effects. network_access is required for every
outbound operation, including scheduler/API reads. Neither query nor submit
authorizes cancel/removal; those require the exact mutation and delete scope.
Retain xrootd_access, dbs_queries, cmssw_setup, scram_build,
large_pkl_production, plot_campaign, datacard_production,
correction_payload_generation and payload_installation when applicable.
One grant never implies another. Installation/environment flags cannot override
the environment prohibition below.

Project authorization != sandbox/tool approval != acceptance. Record observed
sandbox and approval capability, or not_observable, when material. Auto-review
may supply a tool-level check if available; it neither creates authority nor is
a prerequisite. Do not change sandbox settings, authentication, rules, remotes
or user configuration to bypass a failure. If unavailable capability prevents
an authorized action, stop that action and report the actual obstruction.
Technical network availability does not authorize use or prove isolation.

After a possibly side-effecting command has ambiguous terminal state, do not
automatically retry, overwrite, resubmit, delete or infer failure. Obtain
authorized process/scheduler/output/service readback. Retry only with direct
idempotence proof or exact bounded owner recovery authorization with known
consequences; inability to query does not permit retry.

## Local execution and preflight

Use the YAML installation contract in config/local_profile.example.yml and
config/local_profile.schema.yml. Bootstrap by inertly reading the local profile
for tooling.command_wrapper and tooling.python_interpreter, then run
tools/resolve_local_profile.py through that wrapper/interpreter with --profile,
--execution-ready and --format yaml. Verify its resolved facts locally. Without
a usable profile, supply and preflight explicit paths. No JSON fallback or
invisible substitution into an already-dispatched prompt is allowed. A profile
cannot activate an inactive repository or grant effects.

All Python, pytest, compileall, correctionlib, NanoEvents and pkl diagnostics use
the resolved wrapper and interpreter. Never use login shells or invoke the
pinned Python directly. The wrapper is protected infrastructure; an authorized
wrapper change reports sys.executable, sys.path and NumPy import/version.
Never mutate the software environment: do not install/update/create/remove
packages using conda, pip, mamba or apt-get. Report needed user-run commands.
Do not persist authentication, SSH, startup or Codex configuration changes
without explicit configuration-work authorization. Remote Git/gh/glab commands
follow the direct-command rules in the Git contract.

Default preflight_profile is compact_preflight; default dirty_worktree_policy
is require_clean_worktree (tracked/index/conflict clean, not physically empty).
Alternatives are work_on_dirty_branch_as_is, allow_declared_preexisting_changes
and commit_preparation_existing_changes; declare them explicitly.
expanded_preflight requires a reason. Inspect exact task paths, branch/HEAD,
needed references, staged/unstaged task changes and input/output collisions.
preflight_scope_paths may be derived only when the named exact surfaces
determine a unique minimum set. Never inventory unrelated untracked files.
Preserve all foreign changes; path write permission does not adopt them.
No reset, restore, stash, clean or checkout-discard without exact authority,
except the narrow foreign-index recovery defined in the Git contract.
Read back relevant final state.

## Modes and validation ceilings

Declare one prompt_mode. Modes bound activity and never grant effects.

| Mode | Activity boundary |
|---|---|
| investigation_only | Inspection, reproduction, measurements and diagnostic evidence; no tracked edits, fixes, commits, general cleanup or remote mutation |
| coding | Minimum source/test/config/doc change, focused validation and prompt-local commit |
| validation_only | Bounded authorized validation and reports; no tracked source/test edits, commits or remote mutation |
| test_alignment_only | Change stale tests only after direct evidence proves runtime intent; ambiguity stops |
| documentation_only | Established behavior, tracked docs and prompt-local commit |
| commit_preparation | Verify and commit declared existing changes; no runtime edits or unrelated staging |
| pr_preparation | Reviewer text only; no source changes, commit or remote effect |
| integration_only | Git contract's exact local integration |
| branch_maintenance_only | Git contract's exact local branch, ref or linked-worktree lifecycle |
| pr_publication | Git contract's exact publication action, including a separately authorized merge round |
| production_execution | Production contract's exact bounded effects |
| orchestrated_workflow | Orchestration contract's preauthorized ordered stages |

Tracked mutation or explicit adoption requires commit closure unless the owner
authorizes do_not_commit: yes for that exact round. A declared later commit
stage may commit earlier stages' changes; there is no mandatory commit per stage.
If safe commit is impossible, report incomplete and preserve the work.

Declare validation_ceiling: static_inspection_only permits reads, text/Git
inspection, diagnostics artifacts, authorized remote queries, and bounded
deterministic utility scripting, including wrapped Python, when used only for
static parsing, extraction, hashing, byte comparison, schema/text checks,
authorized file materialization, or report generation. Utility scripting grants
no write or other effect by itself; writes remain governed by the prompt/stage
mode, allowed_to_modify, and applicable effect permissions. It does not permit
import or execution of project application, scientific, or workflow code, tests,
workflow execution, scientific calculation, or production-like commands. Those
require the applicable higher validation ceiling and separately authorized
effects. lightweight_import_or_cli_probe additionally permits bounded wrapped
project/runtime imports, help/version/compile and small non-production probes.
targeted_unit_test adds named focused tests/fixtures.
workflow_dry_run_or_config_validation adds bounded no-submit workflow/config
probes and module-authorized native document build/render, never production or
large output generation. production_execution permits only separately
authorized capabilities. Report actual validation, which may be narrower.
Remote effect permission is independent of local validation ceiling.
For integration_only, the exact local integration action is governed by its
mode and Git contract; static_inspection_only limits auxiliary validation
probes to read-only inspection and is not a substitute for the stage's
local index/ref grant.

## Reuse, delegation and model provenance

Before new tooling/state, reuse a maintained owner, configuration or composition,
then consider a minimum compatible extension. Classify new tooling as
EPHEMERAL_DIAGNOSTIC or REUSABLE_CAPABILITY by expected reuse and ownership.
Reusable runners, validators, recovery utilities and converters require a
maintained home, interface, tests, failure/output/provenance contract and docs.
If an ephemeral task reveals that need, preserve evidence and stop scope
expansion. Add persistent state only for a demonstrated failure, with reasons
local derivation/existing ownership are insufficient, consistency/invalidation
rules and the simpler fail-closed alternative. No speculative shims.

For substantial work, use an independent read-only reviewer subagent by default;
small mechanical work may omit it. State a brief reason for substantial omission
and retain all material gates. The orchestration contract defines lane/effect
isolation. Reviewers advise; they do not accept work. No persistent specialist
registry or universal second-model requirement.

Prompts retain explicit preferred_codex_model, reasoning_level,
delegation_policy and model_selection_rationale. Distinguish requested,
selected and runtime-reported identity; unknown is not_observable. Do not infer
an exact model from a family label. One execution attempt has one immutable
profile; an observed mismatch or any model/reasoning switch stops that attempt
for fresh author-selected dispatch. Exact profile proof blocks only when
decision-material; model_policy.md owns concrete labels/routing, not effects.

Skills implement stable repeated workflows only when the maintained capability
lifecycle justifies them. They cannot own project authorization. Existing local
skills are correction-lib-prompt-contract, correction-lib-manual-production-handoff,
correction-lib-diagnostics-execution-copy and
correction-lib-codex-evidence-package-review. Read the triggered live
.agents/skills/<skill_name>/SKILL.md. Prompt lint is not certification; handoff
does not execute; copying does not execute; review does not execute, apply,
fix, invoke other skills or publish. A helper failure is local unless the
authorized workflow requires that exact output; it cannot revoke an independently
authorized underlying action.

## Compact reporting and artifacts

One final report and one actual patch per round/workflow; internal stages use
the stage ledger. Universal report fields are status, goal_or_decision, scope,
effects_performed, validation, material_findings, artifacts, remaining_boundary.
scope records applicable governance paths and permissions; validation records
methods, evidence locators and limits. Include observed branch/repo/HEAD and
dirty state when relevant; model provenance is brief and honest when dispatch
or identity matters. Never hide an effect or incomplete validation as ceremony.

Use <resolved evidence_root>/<prompt_id>/, or exact authorized custom paths,
and <prompt_id>_report.md plus <prompt_id>_worktree_diff.patch. Resolve collisions
with the first unused _rerun_00N directory and report actual paths. Default to
at most five additional nonduplicative artifacts. Patch kinds are prompt_local,
cumulative, touched_file_cumulative and empty_no_changes; name creation method
and changed paths. Distinguish task delta, cumulative history and pre-existing
work when applicable. A read-only round supplies the actual empty tracked diff.
For commits include exact commit, subject, changed paths and reviewable commit
delta; reuse the round patch only when proven equivalent.

Missing decision evidence blocks the dependent claim. Documentary defects are
recorded and repaired in the next naturally authorized continuation; they alone
do not earn a standalone round unless the owner requests one or a later effect
requires the missing evidence. Never relabel missing material evidence.

Conditional report sections: production (action/inputs/output/lifecycle),
publication (exact action/refs/remote readbacks), integration (source/target/
method/result/preservation), scientific_result (authority, semantics and claim
ceiling), recovery (interruption/state/idempotence/authorized action), multi_agent
(roles/inputs/outputs/effects/join/disposition). Load their routed contracts.
Final chat gives the decision result, decisive evidence, material limits,
actual artifacts, performed effects and next boundary. When diagnostics exist,
end with actual-directory FOLD and scp lines:
FOLD=<exact actual diagnostics directory>
scp -r apiccine@glados.crc.nd.edu:${FOLD} .
