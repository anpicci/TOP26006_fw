# CPC.md — TOP26006_fw compact prompt contract

## Construction

AGENTS.md owns authority, runtime safety and the required-reading router.
This file owns prompt construction. CONTRIBUTING.md owns reviewer-facing
prose; selected registry modules and applicable native policy add constraints.
Do not restate their procedures or maintain competing permission/model tables.
An explicit owner override must name the rule, exact alternative and scope;
an unresolved conflict stops emission or the dependent action.

### Normative governance source for prompt validation

Validate every prompt against the current `TOP26006_fw` `refs/heads/master`
governance source at every applicable level: authoring, mechanical
lint/validator, dispatch preflight, pre-effect revalidation, continuation or
repair, and prompt-compliance review. When candidate and master worktrees or
branches differ, the candidate copy is never the normative validation source.
Use exact master Git objects or a checkout whose `HEAD` is freshly verified to
`refs/heads/master`. A changed master OID alone triggers revalidation but does
not invalidate a continuation when the decision-material governance
dependencies are unchanged. Revalidate affected actions after a material
dependency change; an unresolved applicable conflict or unreadable required
master rule stops only the dependent validation or dispatch. The maintained
validator is mechanical lint only and does not assess governance completeness.

Use flexible semantic blocks, one decision_question and exact scopes.
Each value has one authoritative definition; scoped stage keys define only
their own stage and never inherit grants.
A goal is optional only when it adds distinct information. No expected audit
verdicts or zero-failure discovery targets. Cite prior artifacts/locators
instead of copying history. Use snake_case; preserve real paths, API names,
branches and flags. Use fenced blocks; one outer copyable Markdown block only
when requested. Do not invent profiles, environment variables or approvals.

One authorized Codex task uses one self-contained, versioned `CODEX_PROMPT*.md`.
A second prompt, local instructional companion or reconstruction package of
previous prompt instructions must not be a runtime instruction dependency.
Canonical governance, source/configuration, actual data/input artifacts and
prior standalone Codex reports as evidence/provenance remain allowed inputs;
they do not supply a second task mandate. No filename hash gate is implied.

An optional reusable method may supply only stable procedure, with exact
revision, applicability, inputs/outputs, validation, limits and preserved
consumed content. It cannot supply task mandate, effects, target selection,
scientific choices or acceptance. An unresolved reference blocks only its
dependent use. Inline the contents when no retained resolvable source exists.
A playbook routes goals to maintained procedure; a skill is an optional
maintained package. The workbook separately collects qualified artifact
references and operational knowledge through docs/operations/index.md. The
report remains the case/attempt evidence record. Preserve material consumed
entry/source revisions in the run; none of these objects supplies authority
or duplicates the native owner of data or procedure.

Every actionable prompt contains prompt_id, task_revision, decision_question,
prompt_mode, delegation_policy, allowed_to_modify, read_only and
validation_ceiling. Ordinary model/reasoning selection, rationale and consumed
guide version belong to the separately retained author-selected run configuration
referring to the exact task. Deliver complete run configuration and reusable
task in one self-contained unit with explicit byte boundaries; configuration
stays outside task bytes. The author fixes concrete choices, sources/versions
and required authority before delivery. Do not defer a necessary profile or
approval to chat. This configuration is data, not a second mandate.
The task also states actual authority, inputs/conventions, observable result,
relevant failure behavior and acceptance boundary. Scientific choices and
exact targets cannot be supplied by a default or method. Flexible semantic
blocks are permitted; definitions must have one unambiguous authority.

Name selected typed repository IDs and exact scoped targets, and bind the
existing YAML installation profile input. The author fixes repository identity,
semantic branch/target roles, exact effects and material physical bindings;
the executor resolves, verifies, serializes and reopens workspace_root,
repo_locations and volatile applicability facts before each dependent effect.
Supply explicit paths when the profile is unusable or cannot uniquely bind the
authorized target. Dispatchable includes mandatory runtime preflight; author-side
observation of volatile facts is not universally required. Ambiguity of target
ownership or a real owner/scientific choice stops only its dependent effect.
The installation profile and run configuration grant no effect or science.
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
current_checked_out_branch only if identity is a safety invariant). For
orchestration, only stage_branch_policy carries one of these values; its
corresponding branch fields are in that stage, never at the outer level. The
author binds mandate, repository/worktree and branch/resource roles, semantic
target, exact effects, validation and material runtime checks under the Git
contract. When the target is unambiguous and Codex can safely acquire volatile
facts before their dependent effect, lack of author-side live access does not
force a non-executing draft. Codex performs that preflight at runtime; the
author must not claim unobserved state, invent zero applicable branches or
invent a target whose ownership or semantic role remains ambiguous. Such
ambiguity stops the dependent mutation for the required owner choice. Module
permanent roles remain mandatory. Historical identities are provenance; future
commit/ref/artifact identities flow through declared stage outputs. Require
current identity or live readback only at the effect that materially consumes
it, including destructive old-value guards. The owner need not relay read-only
facts Codex can acquire within the authorized path. Baseline/comparison fields
are conditional on decision materiality.

short_title is an optional display value derived from decision_question unless
a distinct consumer requires an explicit title. For an ordinary task-owned
tracked delta derive patch_kind_expected as prompt_local; for no tracked
change use empty_no_changes. Explicitly select any cumulative comparison or
other material exception, and always report the actual patch and method.
Use the existing standard report/patch/final-response contract without
repeating final_chat_deliverable; state any material language, format,
recipient or product exception explicitly. Task-specific result content
remains mandatory. Record exact task revision, consumed method/input/config
contents, immutable attempt configuration, outputs, evidence and decisions
in existing reports/checkpoints; a hash or path alone does not preserve bytes.

MCP storage preserves opaque bytes; it does not authorize, validate, interpret
or rewrite the task/run instructions. Preserve the complete delivery and its
separately identifiable task/run byte ranges and versions. Keep the transfer's
`request_id`/`transfer_id`, reusable `prompt_id`/`task_revision` and actual
execution identity distinct. Equality is not universal; a particular qualified
execution consumer may require an explicit binding. Do not move run configuration
into task bytes to satisfy transport. The author remains responsible for complete
instructions and real authority; a deposit receipt supplies neither. The ordinary
[manual route](docs/how_to/use_glados_mcp.md) returns the verified locator for
owner launch in the already-open CLI under AGENTS; storage does not register an
external execution or apply its profile. Evidence/recovery rules belong to the
[evidence contract](governance/contracts/review_and_evidence.md#mcp-acquisition-and-recovery).

## Conditional field router

Apply the AGENTS trigger union before emission and execution. Include the
selected contract's conditional inputs, grants and gates rather than copying
the entire prompt template.

| Condition | Authoritative fields and rules |
|---|---|
| Tracked change/adoption/commit, refs, linked worktrees, integration, publication or merge | governance/contracts/git_lifecycle.md, including authorized_commit_scope and exact adopted changes when committing |
| Ordered cross-mode dependencies or long-horizon work | governance/contracts/orchestration.md |
| Delegation or independent review | governance/contracts/orchestration.md; explicit delegation_policy forbidden, allowed or required |
| Production, handoff, scheduler, output/recovery/storage | governance/contracts/production.md |
| Audit, scientific comparison, substantial review, continuation | governance/contracts/review_and_evidence.md |
| Autonomous adaptation, blocker classification, preauthorized fallback/repair, or continuation after mechanism failure | governance/contracts/autonomy_and_blocker_classification.md; use existing continuation, scope and effect fields |
| Author-selected run configuration, native model/reasoning selection, CLI dispatch or new author-selected fallback | governance/model_policy.md and its versioned common/provider guide references. Run data is external to exact task bytes; task permissions and independence remain authoritative. |

Routine editing, validation and commit within one coding contract do not require
orchestration. Multiple meaningful mode/effect stages with dependent authorized
actions do. Independent substantive decisions remain separate. Production
stages are conditional under both production and orchestration contracts;
PR/MR merge remains a separate decision.

Every task has a mandatory derived planned workflow_graph, even one-node work.
Mermaid is its only visualization format in the direct path. Every represented
semantic block/subblock has an ID unique in the task revision; each node uses
that same ID and resolves to the text defining meaning, inputs, result and
conditions. No second letter vocabulary, fixed alphabet or node count is
required. A node needs a textual referent; not every section needs a node.
Section order and command order create no dependencies; transversal sections
need not become artificial actions. Text defines data, precedence, alternatives,
ALL versus alternative joins, partial outcomes and genuine iterations. Preserve
their actual meaning and source locators. Distinguish inferred or unresolved
relations when present; do not invent them to fill a taxonomy. An inference
states its basis and cannot choose an owner/scientific decision. An unresolved
material relation stops only its dependent consumer. Missing arrows prove no
independence. Keep diagrams short, readable and clearly labelled; use vertical
layout or a justified split for larger views. Mapping/state tables may explain
the view; no ASCII graph, second visualization or mandatory intermediate
language is required. The graph is derived and non-authoritative: it grants
no permission, authority or retry. Correct a view contradicted by clear text;
material ambiguity in the text stops only its consumer for the required decision.
Iterations require their real authorized repair/attempt boundaries, not automatic
retries. Preserve independent supported results. Reports distinguish planned
and observed views; an observed view may annotate the planned Mermaid with
actual states/differences and the same IDs where they correspond, without a
redundant second drawing when the distinction is clear. Planned is never
executed evidence. Orchestration triggers remain activity-based across modes;
routine editing/checking/commit in one coding contract remain ordinary.

For a continuation require continuation_of. Include accepted_prior_evidence
(claim/artifact/locator), accepted_closure_layers, invalidation_boundary,
delta_scope, unresolved_checks_only and checks_not_to_repeat only when they
carry real state. Relationship is derived, not a second field or mode.
Omission asserts no acceptance and does not authorize repeated accepted checks.
Use the evidence contract's materiality, claim ceilings and invalidation rules.
When applicable, retain these continuation fields instead of inventing a
second field vocabulary. A hard stop in a prompt must name the concrete wrong,
unsafe, unauthorized or irrecoverable consequence it prevents and the
authoritative rule or owner boundary behind it. Mechanism inconvenience alone
is not a hard gate when an already-authorized invariant-preserving alternative
exists. The autonomy contract classifies findings; its labels are not required
outer YAML fields or effect grants.

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
