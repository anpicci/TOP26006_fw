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
boundaries. This implementation supports `Feature`, `Scenario`, `Given`,
`When`, `Then`, `And`, `But`, comments, blank lines, and feature/scenario tags.
`And` and `But` inherit the preceding step's role. Unsupported standard
constructs, including `Rule`, `Background`, `Scenario Outline`, and `Examples`,
fail explicitly with a line-referenced diagnostic. This is a bounded subset,
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

For the bounded parallel-writer assertion `common validation passes`, supply an
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

The supported Q04 continuation is one two-writer case: one accepted writer
result from an exact prior artifact and common base, one invalidated writer,
and disjoint protection and delta scopes. The accepted writer is absent from
executable stages; its exact reviewed portable result feeds the rebuilt union.
The historical writer branch, worktree and current HEAD are not reacquired or
serialized as join preconditions. Later carrier observations are documentary
unless an explicit invalidation rule makes them material; they cannot replace
the accepted result. The compiler repeats the invalidated writer and dependent
review, union, validation
and requested integration/retirement stages. Ambiguous or broader protected
continuations remain unsupported.
Tracked paths are relative to their selected repository, including when two
repositories contain the same relative path.
Local carrier relations and global isolation are separate checks. For Q03 the
compiler compares normalized lexical worktree paths and repository-local mutable
refs across active writers and the controller. For Q05 it compares the two
repository roots and both candidate worktrees; the candidate branches remain
repo-local and follow their distinct native namespaces. Equal branch strings
in distinct repositories do not establish an alias. The receipt records local
relation consistency, cross-role isolation and cross-repository isolation.
The lexical check does not follow symlinks or establish realpath identity; that
remains with acquired binder and runtime evidence. `acquisition: acquired` is
an upstream trust assertion, not compiler authentication. Unsupported safe
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
owner authorization, and dispatchability unestablished. A failed compile writes
only a diagnostic receipt; it never writes a valid prompt.

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
