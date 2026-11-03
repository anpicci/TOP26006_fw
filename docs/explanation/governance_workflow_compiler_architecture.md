# Workflow compiler architecture

The compiler prepares inspectable prompts under canonical governance. Execution,
evidence evaluation and owner acceptance remain external. Its source inputs are
bounded Gherkin intent, explicit upstream binder claims and an acquired policy
repository. None of those roles can replace another.

`governance_workflow_ir.py` owns the canonical policy snapshot and typed produced
results. `Policy_source_binding` reads exact master Git objects and records
consumed dependencies, including modules and validator bytes. It revalidates
those dependencies before returning a candidate. A development checkout's
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
relation. In H4 the four tuples use provider baseline, consumer baseline,
consumer candidate and the provider result established by ambiguous-effect
readback. Expected outcomes remain PASS, PASS, FAIL_EXPECTED and PASS.

`governance_workflow_semantics.py` checks lifecycle safety directly from source
assignments and bound resources. It checks action coverage/order, preservation,
removal, absence, terminal deletion, exact command operands and unknown-effect
readback. It never calls a planner. Existing compiler checks independently
enforce owner bindings, repository locality, stage grants, carrier isolation,
continuation protection, bounded assertions and canonical vocabulary. Equality
between two planner invocations is not a semantic proof.

Serialization canonicalizes mappings while preserving meaningful source,
candidate-pair and validation-case order. Raw input hashes retain raw input
identity. Traces are sorted projections. Generic corruption tests challenge
planner output, policy-source changes and missing result dependencies.

The binder's acquired claims remain trust assertions. The compiler does not
authenticate arbitrary evidence or infer dispatch authority from a receipt.
The maintained validator reports mechanical consistency only. Current D8-F
qualification uses 35 functional cases: Q01-Q20, H1-H5 and N01-N10. The five
complex capabilities are functional requirements; retrospective equivalence
with historical manual workflows is not a completion prerequisite. Q01, Q16
and Q20 retain simple bounded execution and the manual canonical governance
fallback. Functional tests do not establish execution or owner acceptance.

Identity and similar metadata track acquisition by default; only a concrete
consumed authority, safety, scientific or result property makes them a gate.
Authors bind unambiguous semantic targets and runtime checks rather than relay
volatile host facts. A candidate may be dispatchable without generic live
readback; execution must still preflight current master and the exact effect's
resource, dirty/index state and material premises. Required conformance
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
required, and eligible effects alone never make a workflow dispatchable.
`COMPILED_CONFORMING_CANDIDATE` can describe that partial entry path; excluded
effects and unresolved evidence remain explicit and execution assertions stay
NOT_EVALUATED. Git-specific runtime prose is conditional on Git lifecycle effects.
Portable accepted results survive unrelated carrier/OID
drift, while consumed artifact bytes, repository-local grants, foreign-work
isolation, ambiguity readback and destructive compare-and-delete retain their
existing checks. This describes the intended stable semantics; canonical
integration, real-task qualification and stable adoption remain separate owner
boundaries.

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
