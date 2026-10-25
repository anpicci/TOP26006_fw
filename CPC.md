# CPC.md — TOP26006_fw compact prompt contract

## Construction

AGENTS.md owns authority, runtime safety and the required-reading router.
This file owns prompt construction. CONTRIBUTING.md owns reviewer-facing
prose; selected registry modules and applicable native policy add constraints.
Do not restate their procedures or maintain competing permission/model tables.
An explicit owner override must name the rule, exact alternative and scope;
an unresolved conflict stops emission or the dependent action.

Use one authoritative metadata block, one decision_question and exact scopes.
A goal is optional only when it adds distinct information. No expected audit
verdicts or zero-failure discovery targets. Cite prior artifacts/locators
instead of copying history. Use snake_case; preserve real paths, API names,
branches and flags. Use fenced blocks; one outer copyable Markdown block only
when requested. Do not invent profiles, environment variables or approvals.

Every actionable prompt contains:
prompt_id, short_title, prompt_mode, preferred_codex_model, reasoning_level,
delegation_policy, model_selection_rationale, workspace_root, repo_locations,
allowed_to_modify, read_only, validation_ceiling,
decision_question, patch_kind_expected and final_chat_deliverable.

Materialize selected typed repository IDs and resolved local paths; preflight
them. A missing profile needs explicit paths, not a guessed fallback.
Reference the applicable AGENTS router and contracts. A non-orchestrated
actionable prompt requires branch_policy and places every positive
capability/effect grant once in heavy_command_permissions, including
action-specific keys; omission denies them. An orchestrated_workflow MUST omit
outer branch_policy and outer heavy_command_permissions. It requires the
non-authorizing workflow_effect_envelope, stage_branch_policy for each
branch-relevant stage and stage_effect_permissions for every stage.
The envelope permits possible stage grants but grants nothing by itself.
Only each stage_effect_permissions grants positive stage effects, bounded by
the envelope and the applicable contract. Tables in action contracts list
the same canonical keys, never a second authority. Exact path/ref/action
authorization remains additionally required at the applicable location.

Defaults: compact_preflight, require_clean_worktree and all omitted capabilities
denied. Declare any alternatives. Include preflight_scope_paths when the
exact minimum set cannot be uniquely derived. Include out_of_scope only for
material exclusions. Canonical artifact paths derive from prompt_id; exact
custom paths are explicit. Runtime collision resolution is observed, never
assumed. A prompt must not confer filesystem capability or promise isolation.

Branch policies remain create_feature_branch_from_reference (reference_branch,
feature_branch), continue_existing_branch (target_branch), or
read_only_current_branch (fresh observed branch; expected
current_checked_out_branch only if identity is a safety invariant).
For orchestration, only stage_branch_policy carries one of these values;
its corresponding branch fields are in that stage, never at the outer level.
Mutating prompt authors fresh-resolve branch applicability under the Git
contract before emitting a mutation-ready prompt. If they cannot access live
state, emit a non-executing draft pending that preflight; do not assert an
applicable branch or invent zero candidates. Module permanent roles remain
mandatory. Baseline/comparison fields are conditional on decision materiality.

## Conditional field router

Apply the AGENTS trigger union before emission and execution. Include the
selected contract's conditional inputs, grants and gates rather than copying
the entire prompt template.

| Condition | Authoritative fields and rules |
|---|---|
| Tracked change/adoption/commit, refs, integration, publication or merge | governance/contracts/git_lifecycle.md, including authorized_commit_scope and exact adopted changes when committing |
| Ordered cross-mode dependencies or long-horizon work | governance/contracts/orchestration.md |
| Delegation or independent review | governance/contracts/orchestration.md; explicit delegation_policy forbidden, allowed or required |
| Production, handoff, scheduler, output/recovery/storage | governance/contracts/production.md |
| Audit, scientific comparison, substantial review, continuation | governance/contracts/review_and_evidence.md |
| Concrete model/reasoning selection, CLI dispatch or fallback | governance/model_policy.md |

Routine editing, validation and commit within one coding contract do not require
orchestration. Multiple meaningful mode/effect stages with dependent authorized
actions do. Independent substantive decisions remain separate. Production
stages are conditional under both production and orchestration contracts;
PR/MR merge remains a separate decision. A workflow_graph is optional plain
text, documentary only, self-contained and never parsed as authority.

For a continuation require continuation_of. Include accepted_prior_evidence
(claim/artifact/locator), accepted_closure_layers, invalidation_boundary,
delta_scope, unresolved_checks_only and checks_not_to_repeat only when they
carry real state. Relationship is derived, not a second field or mode.
Omission asserts no acceptance and does not authorize repeated accepted checks.
Use the evidence contract's materiality, claim ceilings and invalidation rules.

For evidence/audit work include evidence_requirements, classification_rules,
anti_self_certification_rules and evidence_validation_method. Conditional
required_profile_agreement_evidence and profile_agreement_failure_policy:
fail_closed apply when exact model profile is decision-material. Do not require
unavailable exact runtime identity for ordinary work.

## Handoffs and emission check

conversation_bootstrap transfers durable paths, repository identities,
baseline context, standing constraints and the next activity; it is not an
execution prompt. A cumulative_checkpoint preserves decision/evidence history,
current state, changes, operational lessons, governance sources, accepted
closures, active boundaries, next actions and prior-checkpoint references.
It does not replace live readback or grant authority. The orchestration
contract owns long-horizon checkpoints; no new renderer, registry or skill is
implied. Distinguish bootstrap alone from bootstrap plus actionable prompt.

Before emission verify one decision, router coverage, exact scope and branch
contract, explicit positive permissions, mode/ceiling fit, evidence-before-verdict,
accepted-evidence reuse, commit closure where required, objective transitions,
actual artifact handoff and material stop conditions. Expand only for independent
risks/constraints, not accumulated history. Exact commands are required only
when semantically or safety-critical under the selected contract. Omitted
documentary detail cannot conceal missing authorization or material evidence.
