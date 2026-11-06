# Workflow compiler architecture

The compiler prepares inspectable prompts under canonical governance. Execution,
evidence evaluation and owner acceptance remain external. Its source inputs are
bounded Gherkin intent, explicit upstream binder claims and an acquired policy
repository. None of those roles can replace another.

## Supported patterns and canonical authority

The governance workflow compiler is an optional authoring aid for supported
workflow patterns, not a policy authority or a universal Gherkin implementation.
Use it when those patterns faithfully represent the task; otherwise use manual
governed authoring. Current `refs/heads/master` remains normative for prompt
validation. Compiler output cannot change that authority.

A compile, mechanical lint, author-side semantic review, dispatch, runtime
verification, execution, evidence review and acceptance are distinct results.
The [authoring route](../how_to/compile_governance_workflow.md#choose-the-authoring-route)
shows the compiler/manual choice and the exact author/runtime split. A manually
governed task remains first-class when the supported subset cannot represent it.

| Evidence or surface | What it establishes and its limits |
| --- | --- |
| `allowed_to_modify` | Contractual authority/scope, not an OS ACL or proof of sandbox capability. |
| Hash | Byte identity evidence, not correctness, containment or authorization. Source containment needs its own traversal controls. |
| Lint and receipt | Mechanical checks and compilation provenance, not governance/semantic/scientific correctness, dispatch, execution, review or acceptance. |
| Review package | Package-authored booleans cannot close findings. The external caller/reviewer owns the controlling manifest and the required gate must resolve/evaluate its evidence locator; the utility does not cryptographically authenticate human reviewer identity. |
| Command-directory collision checks | Declared directory → successful entry → checks in that context → command; no race-free or atomic publication claim. |
| Dependent validation | The generated dependency graph and synthetic dependent-consumer fixture show that mandatory FAIL leaves the dependency unsatisfied and blocks consumer entry; PASS satisfies it and permits entry. This does not qualify a real production/runtime executor. |

## Intent, bindings, planning and serialization

The architecture keeps four responsibilities separate:

| Layer | Owned meaning |
| --- | --- |
| Semantic intent | Gherkin actions, premises, observable outcomes and source dependencies |
| Authoritative bindings | Acquired owner/evidence claims, exact repository/target scope and independent positive effect authority |
| Governance planning | Supported physical schedule, local stage grants, required checks and commit/readback mechanics under the acquired policy |
| Serialized prompt/workflow | Inspectable execution contract, trace and graph for separate conformance review and authorized execution |

Each genuinely material premise needs its own source-honest representation and
consumer relation. A source Given may also trace a restatement of constraints
already owned by accepted task status, positive authority, negative scope or
canonical governance. That duplicate restatement needs no second monolithic
executable evidence binding. Its real obligations remain material in those
channels: prose cannot supply a missing grant, widen a target, relax a denial
or certify preservation of foreign work. Recognized live identity assertions
still require their explicit binding and supported verification path; unknown
unbound prose cannot manufacture an owner decision.

For the bounded controller-local fork/review/commit shape, independent semantic
writers can execute serially on one existing bound carrier with delegation
forbidden. Each writer has only its own disjoint tracked target and freezes a
separate outcome. One read-only join consumes both outcomes independently; a
later commit receives only the exact accepted union's index/ref mechanics.
Physical scheduling creates no source writer-to-writer dependency. Semantic
trace, positive effect authority, negative scope and runtime evidence remain
separate even when one executor performs all actions. Unsupported shapes stop
at their actual boundary rather than acquiring an invented stage or grant.

`governance_workflow_ir.py` owns the canonical policy snapshot and typed produced
results. `Policy_source_binding` reads exact master Git objects and records
consumed dependencies, including modules and validator bytes. It revalidates
those dependencies before returning a prepared prompt. A development checkout's
policy edits do not enter this snapshot. Repository selection is trusted
installation context; observed Git identities document acquisition and do not
grant authority.

The existing semantic partition owns source action assignment, resource identity
and source-level dependencies. The compiler lowers it into bounded stage
mechanics. `Result_ref` represents a produced output; `Stage_spec` declares
outputs and typed input references. `Result_graph` verifies availability and
provides the shared dependency projection used by trace and execution diagrams.
The existing stage string is transport syntax at this boundary. Structured
preconditions and evidence carry opaque provenance; a locator resembling a
stage reference cannot create an input dependency. Source graph
edges describe semantic steps; result graph edges describe lowered stages.
They have different granularity and neither creates an effect grant.

`Validation_relation` binds a supported predicate to exact ordered operand
pairs and frozen outcomes. Every operand must be an available declared input.
The generated contract, receipt graph and empirical test consume the same
relation. In the fixture for dependent repositories, the four tuples use provider
baseline, consumer baseline, the proposed consumer result and the provider result
established by ambiguous-effect readback. Expected outcomes remain PASS, PASS, FAIL_EXPECTED and PASS.

`governance_workflow_semantics.py` checks lifecycle safety directly from source
assignments and bound resources. It checks action coverage/order, preservation,
removal, absence, terminal deletion, exact command operands and unknown-effect
readback. It never calls a planner. Existing compiler checks independently
enforce owner bindings, repository locality, stage grants, carrier isolation,
continuation protection, bounded assertions and canonical vocabulary. Equality
between two planner invocations is not a semantic proof.

Serialization canonicalizes mappings while preserving meaningful source,
proposed result pair and validation-case order. Raw input hashes retain raw input
identity. Traces are sorted projections. Generic corruption tests challenge
planner output, policy-source changes and missing result dependencies.

The binder's acquired claims remain trust assertions. The compiler does not
authenticate arbitrary evidence or infer dispatch authority from a receipt.
The maintained validator reports mechanical consistency only. Functional checks
cover simple bounded execution and manual governed authoring, separable work and
join, continuation, accepted result preservation and lifecycle, dependent
repositories, and governed multi-action sequences. These checks concern the
supported patterns; they do not imply arbitrary workflow support or require
equivalence with historical manual workflows. Functional tests do not establish
execution or owner acceptance.

Identity and similar metadata track acquisition by default; only a concrete
consumed authority, safety, scientific or result property makes them a gate.
Authors bind unambiguous semantic targets and runtime checks rather than relay
volatile host facts. Once authority and author review are established, a prompt
may enter current execution checks without generic author-side live readback.
Before effects, the execution environment must still check current master and
the exact effect's resource, dirty/index state and material premises. Required conformance
evidence is not a duplicate owner approval. Unknown blocks its dependent
claim/effect; non-applicability is not failure, and a pertinent failure cannot
become PASS. Independent progression requires modeled independence; no gate
skipping follows. The compiler derives entry roots and static blocked ancestry
from the existing `Result_graph`; `stage_readiness` is a projection, not a second
executor. An unsupported Given becomes a `must_pass_before_effects` input on
its actual consumer. All stage inputs must pass before any local effect, and
blocked stages publish no outputs. Independent writer roots may therefore
progress while a later composition consumer and its descendants remain fenced.
A simple prompt remains atomic. Global owner and conformance bindings remain
required; eligible effects alone never permit a workflow to enter execution checks.
`COMPILED_CONFORMING_CANDIDATE` can describe that partial entry path; excluded
effects and unresolved evidence remain explicit and execution assertions stay
NOT_EVALUATED. Git-specific runtime prose is conditional on Git lifecycle effects.
Portable accepted results survive unrelated carrier/OID
drift, while consumed artifact bytes, repository-local grants, foreign-work
isolation, ambiguity readback and destructive compare-and-delete retain their
existing checks. The compiler prepares prompts; a separately authorized executor
performs effects, and the responsible humans decide evidence and scientific
acceptance.

The compiler receipt binds the hashes of the entrypoint and both internal
modules. Missing canonical validator bytes produce a diagnostic receipt.
Dependent continuations independently compare the remaining integration's
source, tuple, review and safety gates with the accepted effect state.


Reviewed artifacts have one internal `Artifact_spec`: repository-relative path,
SHA-256, review evidence and exactly one source. Bounded synthetic fixtures carry
UTF-8 literal content (at most 64 KiB); the digest must match those exact bytes.
Acquired artifacts carry a safe inert filesystem locator and digest, without
invented literal content. Legacy frozen locator/digest records normalize to the
same identity. Bare reviewed digests without a materialization source fail closed.
Locators are not fetched by compilation; an authorized executor must verify the
acquired bytes against the digest. Locator syntax excludes traversal and URLs.

Ordered stage declarations and the result graph project this relation. The
independent verifier compares source artifact evidence with generated records.
The empirical fixture obtains literal bytes from the generated contract, checks
exact Git blob readbacks for all four results, then evaluates the generated
validation tuples. Artifact identity proves no authority or historical equivalence.

Accepted related artifact comparisons normalize both the current and acquired
values through `canonical_artifact_relation` before exact structural equality.
Only the defined artifact subrelation is normalized; surrounding identity fields
remain exact. Compact acquired locator/digest records and their rich projections
therefore compare equally without dropping paths, locators, sources or review
identity. Generated accepted-review records use that same canonical projection.
Qualification bindings capture deep snapshots of completed observations, so a
later current-context mutation cannot silently rewrite accepted fixture evidence.
