# Review, evidence and claim integrity

## Risk and review depth

Classify the highest applicable consequence before acting; risk describes
required assurance, never permission. Use only T0, T1, T2, T3 or T4. Uncertainty
requires the stronger plausible tier until bounded evidence resolves it.
Stricter repository, scientific, task and action-specific rules always control.
A small diff, a read-only tool, or a documentary label cannot downgrade a
high-consequence claim or input.

| Tier | Scope | Default review and owner/Chat acceptance evidence |
|---|---|---|
| T0 | Read-only/mechanical, no consequential new semantic conclusion | Direct bounded check and concise result; reviewer may be omitted |
| T1 | Bounded docs/config implementing established behavior | Focused diff and validation; reviewer may be omitted only when small/mechanical |
| T2 | Ordinary source/code or substantive semantic design | Independent reviewer by default; affected behavior/tests, residual risks and evidence-backed disposition |
| T3 | Production, scheduler mutation, remote write, integration, publication or consequential scientific/analysis sign-off | Independent reviewer by default; exact effect authority/targets, live readback, applicable completeness review and explicit claim limits |
| T4 | Destructive/irreversible, unblinding or high-consequence scientific decisions | Explicit exact owner/scientific authority; independent pre-effect review by default, post-effect readback and evidence for irreversible consequences |

Substantial work includes new semantics, multiple coupled surfaces, material
uncertainty, consequential sign-off or T2–T4 effects/claims. A substantive T1
governance/document design is substantial. Use orchestration.md for reviewer
independence, omitted-review reasons, findings and join rules. A reviewer is
not an acceptance authority, and omission does not waive any safety gate.
Tiers do not create new approval rounds where the existing owner authorization
already covers the exact mechanically gated action. Chat acceptance evaluates
the relevant tier's evidence; executor status cannot confer it.

### Parallel result composition and review reuse

For a parallel writer result, freeze each task-owned postimage with its exact
base, inputs, assumptions, interface and review identity. The worker result
and a controller candidate are evidence carriers, not permanent development
authority. Exact byte union proves only composition identity. Path and diff
isolation do not prove combined semantic or interface coverage.

Accepted writer review is reusable while its frozen base, inputs, assumptions
and interfaces remain valid. A new cross-file interaction requires bounded
integrated semantic review of the combined candidate. Any controller rewrite
of a worker result leaves the strict exact-union path and is new authorship;
review and validation must cover that changed content and its coupled
interfaces. No universal additional reviewer, model, pilot or approval follows
from composition alone; actual risk and the declared gate determine depth.

## Evidence materiality

Classify individual facts and claims using exactly:
IDENTITY_CRITICAL, DECISION_MATERIAL, DOCUMENTARY.

IDENTITY_CRITICAL means wrong identity can target the wrong repository/ref,
source/input/output/archive, violate lineage or invalidate an identity-specific
qualification. Exact authoritative hashes, refs, byte identity or equivalent
identity proof required by that contract are blocking for the dependent action.
A filename, directory adjacency, branch name or expected value is not proof.

DECISION_MATERIAL means omission or contradiction could change the conclusion,
authorization, scope, semantics or safety. It blocks the dependent claim/gate
until resolved. Use evidence appropriate to that claim; a hash cannot replace
a semantic or consumer check.

DOCUMENTARY means presentation/context whose absence cannot change the
decision, authorization, lineage or safety. Record and repair proportionately;
do not reopen accepted closure solely for it.

Classify from the dependent decision and stricter source contract. An executor
cannot downgrade an explicit exact-identity gate, production input lineage,
Git lease/archive identity, scientific input identity or module-required form
identity by relabeling it. Disputed materiality is at least DECISION_MATERIAL
until resolved. Observed mismatch remains material even where unavailable
runtime identity would otherwise be nonblocking. Exact model qualification
uses model_policy.md; ordinary work does not require unobservable identity.

For material findings, use autonomy_and_blocker_classification.md and
disposition each finding against the **current** decision boundary.
`AUTHORING_DEFECT` blocks the defective prompt or effect, not unrelated
accepted technical or scientific work. `EVIDENCE_OR_PROVENANCE_LIMIT` lowers
the dependent claim ceiling. Record `NONBLOCKING_FINDING` without blocking;
keep `FUTURE_PHASE_LIMIT` in the future and do not revive `SUPERSEDED_GATE`.
When a prompt defect is found after execution, evaluate actual impact on the
result and effects rather than automatically annulling or replaying valid work.

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
surface and terminal tail were preauthorized; orchestration.md's terminal-tail rule
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

Continuation reports include the following only when they carry actual reused or unresolved state:

```text
continuation_of
accepted_prior_evidence
accepted_closure_layers
invalidation_boundary
delta_scope
checks_intentionally_not_repeated
new_or_unresolved_checks_only
```

## Evidence integrity and anti-self-certification

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

## Vendored dependency policy

When a task touches vendored or copied dependencies:

* identify upstream source and version;
* inspect local modifications;
* avoid generated/vendor edits unless required;
* do not replace a local patch with a compatibility shim;
* report whether the dependency is authoritative, copied, generated, or
  read-only.

Include `vendored_dependency_check` when applicable.

## Compact conditional reporting

AGENTS.md owns the universal report core. For scientific_result record the
semantic authority, compared stages, authoritative input/consumer identities,
normalization and method, observed results, invalidation boundary, limitations
and supported claim ceiling. Implementation, tests, document build/render,
production, human physics review and collaboration acceptance are distinct.
Native document rules remain in their module, including stricter identity needs.

For substantial review report blocking_findings, nonblocking_findings,
counterexamples_tested, unsupported_claims, recommended_corrections,
residual_risks and a reasoned verdict. The controller records each disposition.
A finding cannot be closed by renaming it documentary when evidence is absent.

For recovery record the interrupted action, observed state, identity/ownership,
idempotence or exact recovery authority, action actually taken and readback.
Production and publication records use their action contracts; do not impose
PR fields on a branch-only synchronization.

For large/binary artifacts give path, size, timestamp, SHA-256, creation/source
method and who ran it. For ordinary documentary text, exact locator and relevant
content suffice unless identity is material. Commit reports retain exact
commit/delta and changed paths; file_stat is conditional on decision materiality.
No report or reviewer can certify its own authority.

## Historical governance evaluation

For a governance change, use a bounded, representative historical sample when
it can test claimed benefits or regressions. Record artifact and locator,
observed history and acceptance provenance separately, current versus proposed
contract behavior, retained authorization/safety/scientific gates and
uncertainty. Do not execute historical payloads or infer owner acceptance from
executor completion. Label contract_count separately from runtime measurements.
A concrete high-risk regression blocks readiness; unresolved high-risk
coverage requires an explicit implementation-time test or blocks the affected
claim. Missing documentary provenance cannot manufacture success or failure.
