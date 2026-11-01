# Prepare a governance workflow prompt with the D8 compiler

The non-normative D8 compiler prepares an inspectable CPC prompt candidate and
a YAML compilation receipt. It does not dispatch a prompt, perform an effect,
evaluate execution evidence, or accept a result. D8 remains non-normative
during D8-E and D8-F.

Use the Python wrapper and interpreter resolved from the local YAML profile:

```bash
"$wrapper" "$python_interpreter" tools/governance_workflow_compiler.py \
  --feature task.feature --bindings task_bindings.yml \
  --prompt-out generated_prompt.md --receipt-out compilation_receipt.yml
```

Standard Gherkin is the human semantic contract: the feature and scenarios
describe premises, requested actions, observable results, and negative
boundaries. This implementation supports `Feature`, documentary `Rule` grouping, `Scenario`, `Given`,
`When`, `Then`, `And`, `But`, comments, blank lines, and feature/scenario tags.
`And` and `But` inherit the preceding step's role. Free-form descriptions may
contain the required ASCII diagram. Standard constructs whose semantics are
not implemented, including `Background`, `Scenario Outline`, and `Examples`,
stop with a line-referenced diagnostic; parser limits do not establish a
canonical capability boundary. This is a bounded subset,
not a full Gherkin implementation. Tags remain visible as classification and
routing hints; they never grant authority or select production by themselves.

The separate binding YAML supplies acquired authority and evidence facts,
repository identities, exact scopes, a CPC context, and, where needed,
requested effects and exact workflow identity facts. Each material binding
names its source identity, acquisition state, validity scope, and exact effect and target if it
authorizes an effect. Gherkin premises are not proof. A positive effect needs
an acquired owner binding plus the exact current CPC permission and
path/ref/action scope. The compiler selects the minimum supported execution
shape and mode from the behavior and bound context. For the bounded two-writer
and two-repository provider/consumer patterns, it constructs stage roles,
ordering, bodies, gates, commit closure, local grants and provenance. Any
supplied `stages` are an inert historical reference; their goals, modes, grants,
gates and ordering do not become the executable plan. Supply exact worker
branch/worktree/base identities in `worker_contract`, repository base and branch
identities in `repositories`, and exact deletion/preservation identities in
`retirement`. The planner binds later stages to prior observed outputs rather
than assuming requested candidate heads are observed facts. An independent
review stage requires compatible delegation. A supported tracked writer needs
an exact owner-bound local ref effect and index/ref scope for commit closure.
An authorized effect alone cannot request integration: the `When` must request
integration or advancement. Commit closure for a tracked edit is a necessary
governance mechanic even when the `When` does not say `commit`. Every generated
stage records its semantic role and whether it comes from requested behavior
or a necessary governance mechanic.

For every exact identity consumed by a generated Q03/Q05 plan, add an acquired
`repository_readback` or `accepted_evidence` binding with the repository in
`validity_scope` and an `observed_state` mapping of the exact form
`{identity_path: <field path>, value: <exact value>}`. For example, the worker
base field uses `worker_contract.writers.writer_a.base_oid`; a repository base
uses `repositories.topcoffea.base`. Identity-critical Git facts also need one
acquired relation binding: Q03 worker and controller carriers bind repository,
worktree, attached branch, head and base together; Q05 binds the permanent live
branch/head and candidate branch/worktree/head/base together. Individually
matching scalar bindings cannot replace that relation. An ancestry claim needs
an acquired exact relation result; two OIDs alone do not prove ancestry. Git
OIDs need 40 or 64 lowercase hexadecimal characters. Generic owner, review,
applicability or `source_identity` text does not bind a runtime literal. A prior
generated stage output such as `stage:provider_candidate:observed_commit_head`
remains a valid derived input.
Retirement readbacks bind the owned ref and its old OID together under
`retirement.owned_ref`; accepted preservation evidence binds the preservation
ref and expected head together under `retirement.preserved_ref`.
The compiler checks a bounded local-branch ref grammar before inserting a
temporary ref in its compare-and-delete command. The retired ref cannot be a
writer, controller, permanent target, or preservation ref. The preservation
ref may name the permanent target. Exact ref/OID bindings remain necessary.

For every bounded parallel-writer composition followed by integration, supply an
exact `common_validation_contract` with a named `tests/...py` `test_target` and
the composition branch as `target`. Add one acquired `accepted_evidence`
relation under `common_validation.target_relation` that binds the locator,
repository, controller worktree/branch, generated candidate head and claimed
coverage of exact union and common validation. The frozen outer validation
ceiling must be `targeted_unit_test`. The compiler derives the `must_pass` rule;
the caller cannot supply failure semantics. Missing, failed, unreadable or
candidate-mismatched results block dependent stages. The stage carries exact
branch, worktree and generated-head posture. Without the relation, or for an
unrecognized material `Then` clause, compilation fails closed.
This mechanic follows from the requested composition and permanent advancement,
represented as semantic dependency edges, even when
the assertion only requests review of the exact union, composed candidate, or
combined worker results. Mentioning validation in a title, comment or documentary
premise creates no gate. The verifier independently checks the candidate → common
validation → integration order and the explicit evidence dependency; missing
contracts or removed dependencies fail closed. Q05 validates its candidate tuple
and continues to reject permanent advancement outside its supported contract.
Workflow mode and effect inventory cannot supply that behavior. The bounded
two-writer action grammar recognizes editing/writing disjoint files, integrating
or advancing the target, and retiring/removing temporary branches. The assertion
must identify the reviewed exact union, composed candidate or combined worker
results. Mere mentions or negation do not request integration. A bounded partial
two-writer workflow emits only the requested composition/integration/retirement
roles. Unfamiliar clauses require semantic/architecture resolution. Q05 is an orchestrated plan
without this composition/integration dependency and emits no common-validation
stage. Generic assertions such as `success`, `output exists` or `result is ready`
require semantic/architecture resolution because they do not identify an evaluable evidence claim.

The supported Q04 continuation is one two-writer case: one accepted writer
result from an exact prior artifact and common base, one invalidated writer,
and disjoint protection and delta scopes. The accepted writer is absent from
executable stages; its exact reviewed portable result feeds the rebuilt union.
The historical writer branch, worktree and current HEAD are not reacquired or
serialized as join preconditions. Later carrier observations are documentary
unless an explicit invalidation rule makes them material; they cannot replace
the accepted result. The compiler repeats the invalidated writer and dependent
review, union, validation
and requested integration/retirement stages. Contradictory protection requires an owner decision; broader protected
continuations that the delta planner cannot express are implementation gaps.
Tracked paths are relative to their selected repository, including when two
repositories contain the same relative path.
Local carrier relations and global isolation are separate checks. For Q03 the
compiler compares normalized lexical worktree paths and repository-local mutable
refs across active writers and the controller, and excludes the permanent
integration target from those candidate refs before common validation. For Q05
it compares candidate worktrees with each other and with both repository roots;
repository roots may share a location when neither is a candidate carrier.
Candidate branches remain repo-local and follow their distinct native
namespaces. Equal branch strings in distinct repositories do not establish an
alias. The receipt records local
relation consistency, cross-role isolation and cross-repository isolation.
The lexical check does not follow symlinks or establish realpath identity; that
remains with acquired binder and runtime evidence. `acquisition: acquired` is
an upstream trust assertion, not compiler authentication. Unimplemented safe
cases fail locally and leave the manually governed workflow available.
The bounded Q05 provider/consumer planner starts from `NOT_STARTED` and stops
at a validated repo-local candidate pair. Each repository must already have an
authorized candidate carrier in its native feature namespace, with exact
permanent-start/candidate relation and local write/ref authority. The compiler
does not create a carrier or advance `tc/dev-live`, `te/datacard_sr_reco` or any
integration line. A `pair_validation_contract` names a test locator and covers
provider, consumer and common contract; an acquired tuple relation binds that
locator to both generated candidate heads. The validation stage must pass on
the exact pair. An observed partial or completed state yields a diagnostic
that preserves the supplied partial-effect record and requires a separately
bound continuation or recovery plan. It does not replay the initial stages.
Other dependent or unfamiliar action patterns fail closed as compiler
limitations. The author must inspect the generated Markdown and receipt
against live governance before any separately
authorized dispatch.

`dispatch_gate` may name three acquired binding IDs: `owner_authorization_binding`,
`manual_governance_review_binding`, and `live_applicability_binding`. Without
them, the receipt marks the candidate prepared while leaving conformance,
owner authorization, and dispatchability unestablished. A structural or authority
failure writes only a diagnostic receipt. A material `Given` without evidence
or a usable preflight may produce a prepared prompt, but its receipt excludes
the dependent effects, marks it non-dispatchable, and the CLI exits nonzero.

Map insertion order is inert. `candidate_pair_order` remains semantic: it must
name provider then consumer. Writer path unions are set-like and normalized in
the plan. A simple prompt's positive executable path/ref scope is checked in
reverse against the exact requested effect and repository-local authority
binding; an extra path or lifecycle category is rejected.

For effect-local readiness, `given_bindings` maps a `Given` source line to a
binding. The binding may name `dependent_effect_ids`, `material_reason`, and
`runtime_preflight`. Preflight prose is inert, including a string starting with
`verify`. Every premise is classified as `already_acquired_material_fact`,
`runtime_preflight_requirement`, `non_material_documentary_premise`, or
`unsupported_material_premise`. Documentary premises remain traced without gates.
A linked material premise names its dependent effects; unsupported properties
exclude only those effects and keep the prepared workflow non-dispatchable.

The bounded Git properties are `the selected commit branch is checked out`
(also `the current branch is the selected commit target`) and
`ref refs/heads/<branch> names commit <oid>` (also
`refs/heads/<branch> resolves to <oid>`). The compiler binds these to the same
repository and local ref consumed by the declared dependent ref effects.
It derives `git symbolic-ref --quiet HEAD` or `git rev-parse --verify <ref>`,
the effect carrier, expected value and exit/stdout comparison. Writers use their
worktree, composition uses the controller worktree, and Q05 uses the repo-local
candidate. A simple repository-local effect uses its declared repository path.
A Given on permanent integration needs a separate acquired
`worker_contract.integration_target_carrier` relation containing `repository`,
`worktree`, `attached_branch` and `head`; a repository root is not a fallback.
These are unexecuted verification descriptions, not acquired evidence or grants.
The check is emitted under `must_pass_before_effects` in stage inputs or simple
prompt evidence requirements, never as a post-effect stage acceptance gate.
An acquired material fact, from `repository_readback` or `accepted_evidence`,
must carry the exact `observed_state`: `property`, `repository_id`,
`working_directory`, `target`, `observed_value`, `argv`, `comparison`,
`source_identity`, `validity_scope`, and sorted `dependent_effect_ids`.
The observed value must equal the required value; mechanism and evidence context
must also match. Changing a locator without rebinding its observation is not
silent evidence equivalence. The emitted stage consumes this exact acquired
record without adding a redundant preflight. Contradictory acquired records,
including wrong-carrier observations, exclude only their dependent effects.
Pending, superseded or invalidated current-state observations need a fresh
compiler-derived check. Generic live-applicability evidence proves no exact fact.

Q04 also recognizes `accepted writer writer_b result names commit <oid>` (or
`writer_a` when that is the protected writer). Link it to the existing exact
`q04.accepted_writer_result` accepted-evidence relation, with dependencies on
the consuming exact-union effects. The source must be the continuation's exact
prior artifact, with the matching result/head/base/review identity and validity
scope. The accepted writer must remain outside the invalidation boundary.
This premise consumes the portable result, so movement or retirement of its
historical carrier triggers no new readback. It does not assert that the old
branch still has that value. Expired or contradictory portable evidence is
not reusable; a current repository readback cannot replace the accepted result.
Exact-plan premises (`isolated worktrees`, `exact bases`) continue to consume
the existing acquired carrier relations. Unknown unbound prose is documentary;
authors must bind material premises, and recognized identity assertions cannot
silently fall back to documentary status when unbound.
Generic HEAD/SHA placeholders are insufficient. Ordinary unrelated HEAD/hash
drift does not create a gate. Exact identity readbacks remain mandatory where a
plan consumes that identity. The supported negative assertion `no remote repository is
modified` rejects contradictory remote effects. Unrecognized negative
assertions stop at an unresolved semantic/architecture boundary rather than becoming decorative trace edges.

Every successful receipt binds the SHA-256 of the prompt, raw binding input,
compiler source, applicable live governance, and maintained validator source.
It records the validator locator and version. Regenerate affected final samples
after source changes; old receipts remain historical evidence.

The compiler resolves each selected repository module from the live typed
registry. TOPEFT and TOPCOFFEA prompts carry all four native branch-role fields;
an out-of-role development branch or feature namespace fails closed. A matching
feature namespace never grants branch creation. The generated prompt also names
the applicable repository-native policy requirement. Conditional Git,
orchestration, evidence, recovery, model, production and reviewer-prose rule
families are recorded in the receipt with their live source hashes.

The compiler checks the current serialized closed fields against live sources:
typed repository IDs and their prompt scopes, prompt/stage mode, branch policy,
validation ceiling, model, reasoning, delegation, dirty-worktree and preflight
policy, patch kind, foreign-work and staging policy, workflow stop policy,
integration method, publication action and duplicate policy, and production
execution owner. When the applicable source cannot establish an allowed value,
compilation fails closed.
The receipt evaluates traceability across semantic steps, authority/effect
bindings, emitted stages and mechanics, and post-execution evidence paths;
missing material edges prevent a conforming prompt. It emits the evidence and
evaluation contract, but does not ingest execution evidence or evaluate
acceptance. `patch_kind_expected` is checked against the whole plan:
read-only plans use `empty_no_changes`, and supported tracked mutation plans
use `prompt_local`. Other patch kinds are unsupported until exact provenance
semantics are implemented. The maintained prompt validator checks mechanical
validity and internal consistency only; governance completeness remains unassessed. A
generated prompt, receipt, or validator PASS is neither execution nor
acceptance nor normative D8 adoption. Historical H1-H6 comparison belongs to
D8-F.

The compiler trusts the upstream acquisition/binder layer's `acquired` claim.
Gherkin text never creates acquisition or authority. `source_identity` records
provenance/locator identity; exact `observed_state` relations are required for
identity-critical planning. The compiler does not independently authenticate
or byte-verify each source. Keep that boundary visible in the later global
audit and D8-F before any normative adoption decision.

If the compiler cannot express a manually valid task, use the existing
[manual prompt guide](write_a_prompt_manually.md) and
[prompt validation guide](validate_a_prompt_before_execution.md). A compiler
limitation does not revoke an independently valid manual workflow.

## Execution shape and architecture boundaries

Behavior selects the execution shape before effect authority is checked. An
inventory of authorized effects cannot request an additional stage. Parallel
writers may end after independent review, after reviewed composition, or after
requested integration and terminal retirement. The first two shapes do not
invent common validation or integration. Composition followed by integration
requires common validation before the permanent target advances. The supported
assertion for independent results is `writer results are reviewed`.

The compiler distinguishes `SUPPORTED_EXECUTION_SHAPE`, `IMPLEMENTATION_GAP`,
`UNSUPPORTED_CANONICAL_CONSTRUCT`, and `ARCHITECTURE_BOUNDARY_UNRESOLVED`.
A rejected live closed-vocabulary value is a canonical boundary. Missing facts
and authority retain their corresponding NOT_READY results. Unknown semantic
clauses require an architecture/semantic resolution; they are not proof that
canonical governance forbids the behavior. A missing implementation for a
D8-supported pattern is an implementation gap. For example, permanent
advancement after the two-repository candidate plan remains an implementation
gap; it must not be relabeled canonically unsupported or emitted as a partial
implementation of the requested behavior.

Boundary receipts include the semantic pattern, affected steps and effects,
attempted execution shape, source/section, missing capability, decision options
and a precise next boundary. D8-B §§3–8,15,17 and D8-C Q03–Q06,Q18,Q20 establish
these distinctions; current canonical governance owns the actual permission
and vocabulary contracts. These compiler classes neither revoke a manually
valid workflow nor authorize its execution. A receipt can identify a gap
without claiming that the supported architecture has been fully implemented.

## Material evidence validity

A linked material Given records a `validity_relation`: claim, evidence identity,
validity scope, consumed property, dependent effects and exact carrier
comparisons. The compiler selects the carrier relation by the effect's generated
role. It projects only the property used by the premise and compares that with
the required observation. A generic live-applicability binding cannot supply
this relation. Conflicting observations exclude only dependent effects, even
when the old observation is acquired accepted evidence. Both accepted evidence
and repository readbacks can establish a premise within their validity scope.

For example, an accepted local-ref value A is stale when the same bound writer
carrier now has value B. Conversely, HEAD movement does not invalidate a premise
about the checked-out branch when that branch is unchanged. Movement in another
writer carrier is irrelevant. For a simple prompt an optional exact relation
`repositories.<repository_id>.current_carrier` carries `repository`, `worktree`,
`attached_branch` and `head`; it is compared only where the effect consumes the
corresponding property. No new observation is fabricated when that relation is
absent. Q04 portable accepted results have their own result/base/review scope;
historical branch movement or disappearance does not enter current-carrier
comparison and cannot force reacquisition of that retired carrier.

## Plain ASCII workflow diagrams

Each supported contract includes one Markdown `text` fence in a free-form
Feature, Rule or Scenario description, before its steps. Each step has a unique
ordinary prose label `[G1]`, `[W1]`, `[T1]`, or another ASCII identifier. These
labels are references, not Gherkin keywords or authority. The `derived_` prefix
is reserved for generated nodes. No renderer, external dependency, or separate
`Edges:` list is used.

````gherkin
Feature: bounded inspection
  ```text
  [G1] Given
    |
    v
  [W1] Inspect
    |
    v
  [T1] Evidence
  ```
  Scenario: inspect one document
    Given [G1] the document identity is acquired
    When [W1] I inspect the document
    Then [T1] the report cites evidence
````

The source diagram describes semantic dependencies at the granularity of the
steps. Given premises feed actions; observable assertions depend on their
scenario's actions. Independent assertions are separate branches, not serial
validation gates. Multiple scenarios have no invented cross-scenario edge.
A compound action remains one semantic node; its generated execution diagram
expands the internal roles. To expose the parallel branch and composition in
both diagrams, use separate ordinary action steps:

````gherkin
Feature: parallel writers
  ```text
                +--> [W1] Writer A --+
                |                    |
  [G1] Given ---+                    +--> [C1] Union --> [I1] Integrate --> [R1] Retire --> [T1]
                |                    |
                +--> [W2] Writer B --+
  ```
  Scenario: disjoint writers compose and integrate
    Given [G1] isolated worktrees
    When [W1] I edit writer_a disjoint files
    And [W2] I edit writer_b disjoint files
    And [C1] I compose the exact union
    And [I1] I integrate the composed candidate
    And [R1] I retire temporary branches
    Then [T1] exact union is reviewed
````

The binding YAML still supplies exact acquired carrier identities, authority and
validation contracts; `requested_by_step` and `given_bindings` refer to actual
source line numbers, including description lines. The diagram supplies none of
those facts. The separate writer clauses explicitly request disjoint writers;
the graph cannot turn a serial action into parallel work. Composition,
integration and retirement clauses may be omitted when their effects are not
requested. Their corresponding authority inventory must then omit those effects.

The standard-library parser recognizes bracketed IDs, inert captions, horizontal
and vertical connectors, diagonal `/` and `\` segments, `+` junctions and terminal
`>`/`v` arrows. Align with spaces. Crossings must have an explicit junction;
broken wires, dangling connectors, unclosed fences, ambiguous directions,
unknown IDs and missing or additional dependencies fail with
`WORKFLOW_GRAPH_INCONSISTENT`. Inputs are bounded to 100,000 characters and a
2,000 by 2,000 grid. Repeated diagram IDs reference the same node, useful for
separate failure panels; semantic step definitions remain unique. The compiler
never derives behavior or authority from geometry.

Each generated prompt includes a text diagram and documentary correspondence.
Each receipt has `workflow_visualization.source_graph`, `generated_graph`,
`semantic_mapping`, `execution_mapping` and `consistency`. Nodes surviving from
separate semantic actions retain their source IDs. Compiler stages receive
explicit derived IDs and source/governance mappings. Local preflight edges reach
only the consuming effect stage. Failure panels show stop/preservation exits;
`derived_external_acceptance` is an external evidence and owner boundary, not a
new executable stage. Q04 reused writer nodes denote portable results, with no
writer effect. The generated drawing is parsed again and compared against the
semantic/execution graph before a conforming candidate is returned. The receipt
retains the compiler, input, prompt and governance digests so that the graph and
its plan can be reviewed together.
