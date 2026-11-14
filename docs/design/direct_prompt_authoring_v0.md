# Direct prompt authoring — documentary candidate v0.2.0

## Status, sources and minimum design

**Proposed contract; inactive.** This document and its two linked inactive selection guides contain the proposed
rules, an authoring aid, complete inert examples, reusable procedure contents,
record placement and exact migration proposals. It neither changes current
policy nor authorizes its examples. Current CPC remains the dispatch contract.
No compiler retirement, qualification, adoption, integration or publication is
claimed. An owner decision on the returned evidence remains separate.

Design basis: TOP26006_fw master
`5ba30bcc367d39e3131335a0eb55fdbc5bc54ce4`, acquired from local Git objects.
The execution report preserves the consumed source bytes and blob identities.
Relevant sources are [CPC](../../CPC.md), [AGENTS](../../AGENTS.md),
[repository registry](../../governance/repositories.md),
[Git lifecycle](../../governance/contracts/git_lifecycle.md),
[orchestration](../../governance/contracts/orchestration.md),
[evidence](../../governance/contracts/review_and_evidence.md),
[autonomy](../../governance/contracts/autonomy_and_blocker_classification.md),
[model policy](../../governance/model_policy.md),
[prompt reference](../reference/prompt_contract.md),
[report reference](../reference/report_contract.md),
[manual authoring](../how_to/write_a_prompt_manually.md),
[continuation](../how_to/prepare_a_continuation.md), and the four local skill
contracts under `.agents/skills/`. The applicable repository module is root;
there is no nested AGENTS under the new document's path at this base.

The fixed design direction is direct consumption by the agent, flexible
semantic blocks, optional reusable methods, attempt records in existing
reports, a mandatory derived documentary graph, and explicit reproducibility.
The minimum design here adds no component system, parser, registry, database,
runner or installed skill. The maintained classic CPC manual path is the
comparison baseline. No compiler rejection, impossibility proof, fresh
architecture evaluation or performance benchmark is asserted.

Responsibilities: the author fixes the mandate, inputs, method, conventions,
permissions and criteria, then selects and communicates each run configuration.
The executor applies that configuration and records observations; the reviewer
challenges the result and its limits without accepting it. Inputs are the retained
task bytes, actual input/method contents, applicable governance and the selected
guide versions. Outputs are the local candidate, guides and evidence in the
existing report. Reuse preserves the task bytes across intentional profile changes.
The installation YAML resolves tooling/paths; it is not the run configuration.

A two-field nucleus (`prompt_id`, `decision_question`) indexes an idea but cannot
bind an actionable task. The eight universal task identifiers below arose from
consumer responsibilities, not a target field count. Concrete model/reasoning
selection belongs outside the reusable task. The [common selection guide](model_selection_common_v0.md)
owns candidate common criteria; the [OpenAI guide](providers/openai_selection_v0.md)
owns candidate native choices and dated source distinctions. Both are inactive.
There is no new wrapper, planner, service or parallel instruction mandate.

## P — proposed prompt construction contract

### P1. One mandate and flexible semantic blocks

Deliver one versioned `CODEX_PROMPT*.md`, consumed directly by the executor.
The blocks may be prose, tables or fenced mappings. Their order is flexible;
logical bindings must be unambiguous. Use canonical field names for actual
interfaces. Each value has one authoritative definition; a scoped stage key
is a distinct definition for that stage, never an alias or inherited grant.
The prompt must let its consumer locate goal, inputs, effects, result and
continuation without recovering another task mandate from a chat or companion
plan. External governance, configuration, data, prior reports and a resolved
stable method are permissible inputs with explicit roles and preserved contents.
A referenced method supplies procedure, never a missing task decision.

The universal named task inputs are:

1. `prompt_id`: stable task identity, not acceptance or a run identity.
2. `task_revision`: explicit revision of the exact task instruction bytes.
3. `decision_question`: one substantive decision and its owner boundary.
4. `prompt_mode`: existing activity boundary, never an effect grant.
5. `delegation_policy`: task authorization for delegation, including any required
   independent review; a run cannot weaken or enlarge it.
6. `allowed_to_modify`: exact typed repository and path/resource scope bounding grants.
7. `read_only`: actual inputs and protected surfaces, consistent with writable descendants.
8. `validation_ceiling`: maximum validation; actual checks may be narrower.

Authority provenance, inputs/conventions, method if selected, result, failure
behavior and acceptance criteria remain required semantic content. Conditional
contracts still add exact scopes and grants. No field count substitutes for them.
The model is not an ordinary task field. If a named model is genuinely the
scientific object or an experimental criterion, retain that explicit constraint
in the task; an incompatible run cannot satisfy it by changing configuration.

One separately retained run configuration references this task and records
provider/product, author-selected native model/reasoning, rationale and consumed
guide versions. It is configuration data, not another instructive prompt.
Use the existing report as its retention surface, with a reachable Git object
or bounded retained bytes; no required configuration file or new schema is added.
The run cannot supply missing science, permissions, retry/upload/production
authority, a new method or broader delegation. A task requiring independent
review keeps that requirement even when the run identifies concrete executors.

### P2. Defaults, consumers and conditional precision

| Content | Author responsibility | Executor/consumer responsibility and proposed default |
| --- | --- | --- |
| Governance | Bind TOP26006_fw and the selected repository role; explicit owner overrides identify rule and scope | Acquire current master and the union of applicable router contracts before dependent actions; candidate policy cannot validate itself |
| Installation | Name selected repository IDs and the exact profile input; explicit paths if no usable profile or a physical target is material | Resolve existing YAML profile and verify root/repository identity before effects; record resolved `workspace_root` and `repo_locations` in the attempt workbook |
| Targets | Explicit repository-relative source/output paths; explicit absolute external resource/worktree paths and refs when relevant | A profile cannot select science, activate an inactive repository or choose a new target; ambiguity stops its consumer |
| Capabilities | Explicit exact positive grant map plus scope/action, with required denials | Omitted capabilities denied; mode, graph, method and profile confer none |
| Branch | Applicable outer `branch_policy`, or each branch-relevant `stage_branch_policy`, and exact lifecycle/commit fields | Current Git contract unchanged; acquire volatile facts where consumed, preserve foreign work |
| Preflight | Declare alternatives and non-derivable minimum scope | Existing `compact_preflight` and `require_clean_worktree`; these defaults are unchanged |
| Result | Task-specific result content and any delivery exception | Standard existing report fields, one actual patch, derived evidence path/collision rule and final result/evidence/limits/next-boundary response |
| Patch | State an exceptional comparison surface if needed | Derive `patch_kind_expected` from authorized delta: `prompt_local` for task-owned mutation; `empty_no_changes` for no tracked change; explicit cumulative alternatives when requested. Record actual kind and creation method |
| Short title | Supply only if a real consumer needs a distinct title | Optional display title derived from question; it never selects a target or authority |
| Language/format | State a nonstandard language, format, recipient or handoff when material | Standard result content above; no universal duplicate `final_chat_deliverable` paragraph |
| Method | Select a compatible method revision and bind its inputs/conventions, or use none | Resolve actual content before use; unresolved method blocks that method's claim, not unrelated evidence |
| Review | Required depth from actual risk and contract | Same independent-review default and omission rule; no universal second model or new approval gate |

The root/repository locations are **relocated observed facts**, not guessed
paths. Name an explicit physical path in the prompt whenever relocating it
would leave target ownership or identity ambiguous. The profile is data, not
an instructional companion. Its pre-existing maintenance burden counts in the
benefit test. Installation values must be serialized before an effect consumes
them, not retroactively asserted as verified.

For non-orchestrated work, `heavy_command_permissions` remains the sole
positive capability map. Outer `allowed_to_modify` bounds it. For
`orchestrated_workflow`, outer `branch_policy` and `heavy_command_permissions`
remain prohibited; `workflow_effect_envelope` only caps and each
`stage_effect_permissions` alone grants stage effects. Exact action/path/ref
contracts remain additional requirements. Never pool grants or infer a retry.
All existing permission names and separate network, query, submit, storage,
delete, publication, merge and unblind boundaries survive.

Apply orchestration rules to ordered cross-mode/effect dependencies,
delegation, independent review and long-horizon work **across all modes**.
Use stage serialization only where the orchestration contract requires it.
Ordinary editing, checking and commit inside one coding contract stay ordinary.
Long-horizon fields remain `durable_objective`, `definition_of_done`,
`hard_boundaries`, `checkpoint_ledger`, `validation_loop`, `resume_semantics`,
and relevant resource/time ceilings. A different substantive decision stops.
A graph loop cannot create a repair edge, effect, iteration budget or permission.

Continuations retain `continuation_of`, and real-state
`accepted_prior_evidence`, `accepted_closure_layers`, `invalidation_boundary`,
`delta_scope`, `unresolved_checks_only`, `checks_not_to_repeat`. Acceptance
provenance and claim boundary must be explicit; scenario premises are not
historical owner acceptance. Evidence/audit work retains
`evidence_requirements`, `classification_rules`, `anti_self_certification_rules`,
`evidence_validation_method`. Model-profile proof fields remain conditional
on actual decision materiality; unobservable runtime identity is reported
honestly. An observed profile mismatch/switch stops the attempt. Git commit,
publication, production and recovery retain their current conditional fields.

### P3. Mandatory derived non-authoritative graph

Every prompt has a planned graph, including an atomic one-node view. Derive it
from source meaning after drafting the mandate. Nodes denote inputs, actions,
results or decisions. Distinguish data, prerequisite and alternative routes.
Each decisive relation has a source locator in the prompt/method/evidence;
use stable section/node labels, not a drawing's geometry, as locators.

Label relations `explicit`, `inferred` or `unresolved`. An inference states
its basis and must not silently choose an owner/scientific decision. Unresolved
relations remain visible and stop only what requires resolving them. List
order does not establish dependency; absent arrows do not establish independence.
An all-input join requires every named input; an alternative join states the
permitted alternatives. A failure/partial route names what remains valid.

Cycles may describe real iteration. Record attempt/stage instances and the
actual authorized repair boundary; never force the history into a DAG or
turn a cycle into automatic retry. Correct a graph contradicted by clear
source text. When the source itself is ambiguous, expose the missing decision
rather than making a prettier drawing. A graph defect does not annul an
independent supported result. A material source ambiguity still gates its
consumer. A one-node graph may annotate its input/result relations in prose.

The observed graph is a separate view recorded in the existing report, with
actual completed, failed, unknown and unstarted nodes and evidence locators.
It may be a status annotation of the planned view plus changed relations;
it must not mark a planned action as executed. Neither view grants effects.

### P4. Task, run and evidence in the existing workbook

Use existing `<evidence_root>/<prompt_id>/` collision rules, report, actual patch
and conditional ledgers. Distinguish attempts inside the report and preserve
separately dispatched attempts without overwriting earlier evidence. No new
workbook, database, registry or service is introduced. Optional methods remain
stable procedure; an atomic task need not select a skill.

| Object | Identity/content retained | Consumer |
| --- | --- | --- |
| Task | Exact prompt bytes, prompt_id/task_revision, Git commit/blob or retained bytes; input/method contents and configuration, conventions, permissions and criteria | Executor recovers one mandate; reviewer binds the compared task |
| Run | Unique attempt locator referring to that task; provider/product, concrete author-selected profile, rationale, common/provider guide revision plus retained content locator | Author communicates selection; executor configures; reviewer can reproduce the choice |
| Evidence | Supplied configuration versus observable selected/runtime metadata with source, actual outputs, limitations, decisions, commands, observed graph | Reviewer separates request from observation; owner decides acceptance |

A hash or filename alone does not preserve contents. Revisions identify exact
bytes; changing task bytes creates a new task revision. Input/method content,
parameters or denominator changes must be recorded as such even if their
references occur outside the task; they invalidate a same-input comparison.
Changing only the ordinary execution profile creates a new run configuration
and attempt, not a task revision. This corrects v0.1.0's contradiction: model
was inside instruction content, yet comparisons required invariant revision.

Record requested/dispatched values, directly selected values if observable,
and runtime-reported labels/effort separately, with actual metadata provenance.
Use `not_observable` for unavailable observations; never fill them from requests
or infer an exact model from a family label. One attempt has one immutable
profile. On an observed mismatch/switch, stop that attempt; a model that is
unavailable needs a new author selection and dispatch under existing authority,
never executor fallback. Exact proof gates only claims for which it is material.
An unresolved guide/version limits reproducibility of selection; it does not
prove the model is unavailable or erase independent task evidence.

For controlled comparisons hold exact task bytes, input bytes, method release
and parameters, conventions/denominators, scope, permissions and criteria fixed.
Record tool/service state, ordering, caches, context and stochastic variation.
If model and reasoning both vary, the compared factor is their pair, not model
alone. Multiple runs of one task are not independent scientific tasks. Never
attribute changed input/method/denominator to the model or infer empirical
quality, portability, cost or time gains from a static identity check.

Preserve valid continuation closure within its invalidation boundary and read
back ambiguous effects before authorized recovery. Unknown remote outcome
does not erase an independent local result or grant retry. Evidence acceptance
and scientific acceptance stay separate from execution and advisory review.

## A — authoring aid

This is a lightweight fillable aid, deliberately not a second normative
catalog. The complete examples below show finished cases. Square-bracketed
slots in this aid require replacement and are not dispatch-ready.

```text
prompt_id: [stable task identity]
task_revision: [explicit revision]
decision_question: [one decision, including owner boundary]
prompt_mode: [existing mode]
delegation_policy: [forbidden, allowed or required]
allowed_to_modify: [exact repository, paths and effects or empty map]
read_only: [exact inputs and protected resources]
validation_ceiling: [existing ceiling]
```

Retain a separate author-selected run configuration under P4; it grants no effects.
Then state, once each: mandate; selected repository/profile or explicit paths;
input contents and conventions; actual result; applicable branch/grant and
conditional contract fields; partial/stop behavior; acceptance boundary. Add a
method only when useful. Derive graph and title. Standard reporting and omitted
capability defaults come from P2, not an unspoken second mandate. Before a real
dispatch, acquire current rules, resolve all real decisions and check the full
prompt. This proposed aid is not an exception to current CPC.

## E1 — complete inert atomic example: cell counting

Everything between the E1 markers is one candidate-only example prompt. It is
not a current-CPC dispatch and creates no authority for filesystem writes.

The ordinary run profile is external to the task bytes below (P4/R).

<!-- example_e1_start -->
# Compare two supplied meanings of cell

```yaml
prompt_id: example_cell_count
task_revision: '2'
decision_question: What counting consequences follow from each supplied cell definition, leaving the scientific choice to the owner?
prompt_mode: investigation_only
delegation_policy: forbidden
allowed_to_modify:
  TOP26006_fw:
    diagnostics: /users/apiccine/work/correction-lib/reports/diagnostics/example_cell_count
read_only:
  - supplied_definitions_only
  - all_tracked_files_indexes_refs_and_external_resources
validation_ceiling: static_inspection_only
execution_not_authorized: true
branch_policy: read_only_current_branch
heavy_command_permissions:
  allowed_to_modify:
    TOP26006_fw:
      diagnostics: /users/apiccine/work/correction-lib/reports/diagnostics/example_cell_count
  network_access: false
```

**E1.S authority/input.** Inert supplied scenario, no owner execution grant.
Repository context is TOP26006_fw; installation input is
`/users/apiccine/work/correction-lib/.top26006/local_profile.yml`. No scientific input files
or application code are read. A hypothetical authorized attempt may read the
bound profile and current governance for preflight. Supplied definitions are A: “cell =
process/coefficient pair in one era”; B: “cell = bin/process/coefficient tuple
in one era”. The owner alone selects the scientific meaning.

**E1.R result/procedure.** Explain both meanings from supplied text. In a fixed
era, let S be the set of present process/coefficient pairs. A counts |S|.
Let T be the set of present bin/process/coefficient tuples. B counts |T|.
For a pair p, let B_p be its present bins; B counts the sum of |B_p| over
present pairs. If all P processes, C coefficients and B bins form complete
Cartesian populations, the counts are P*C and B*P*C. Do not assume completeness,
a shared bin population, or decide which definition applies to real analysis.
The counts agree when each present pair has exactly one present bin. With
multiple eras, sum the separately defined populations by era; do not erase era
identity or infer cross-era matching. This is conditional counting, not a
measurement. No method/skill is needed for this atomic task.

**E1.D delivery/stops.** Hypothetical result uses the existing report core and
actual empty tracked patch under the exact diagnostics scope, resolving a
collision by the existing observed rerun rule; final answer explains counts
and the unresolved scientific choice. Stop the affected conclusion if supplied
terms are ambiguous. Do not change tracked files, indexes, science, refs or external services.
A report or executor completion cannot select/accept the scientific definition.
During this documentary round the example is not executed, including diagnostics.

**E1.G planned graph.** One task node; its input and result relations are
explicit from E1.S and E1.R. There is no inferred external dependency, alternative
join or iteration. The unresolved owner definition is an output boundary, not
a prerequisite to explaining both alternatives.

```mermaid
flowchart LR
 c["Compare supplied definitions → conditional counts; owner choice open"]
```

**E1.O observed view.** Scenario only: the node is planned, no execution or
acceptance evidence. A future authorized attempt records its own observed view.
<!-- example_e1_end -->

## E2 — complete inert reuse example and method contents

The method below is an inline reusable playbook, not an installed skill. A
consumer may reuse its exact content rather than redesign it. This example
includes the full procedure so that it has no hidden instructional dependency.
A future maintained content reference is allowed only under P4; embedding or
preserving the method is counted as work, not credited as eliminated content.

The ordinary run profile is external to the task bytes below (P4/R).

<!-- example_e2_start -->
# Compare supplied synthetic weighted yields using a reusable procedure

```yaml
prompt_id: example_weighted_yields
task_revision: '2'
decision_question: What key coverage and signed-reference differences follow from the supplied compatible synthetic yields?
prompt_mode: investigation_only
delegation_policy: allowed
allowed_to_modify:
  TOP26006_fw:
    diagnostics: /users/apiccine/work/correction-lib/reports/diagnostics/example_weighted_yields
read_only:
  - supplied_synthetic_yields_and_method
  - all_tracked_files_indexes_refs_and_external_resources
validation_ceiling: static_inspection_only
execution_not_authorized: true
branch_policy: read_only_current_branch
heavy_command_permissions:
  allowed_to_modify:
    TOP26006_fw:
      diagnostics: /users/apiccine/work/correction-lib/reports/diagnostics/example_weighted_yields
  network_access: false
```

**E2.S authority/input.** Supplied inert scenario; no real execution grant.
Repository TOP26006_fw; installation input
`/users/apiccine/work/correction-lib/.top26006/local_profile.yml`.
These are synthetic compatible weighted event yields, same semantic stage and
normalization, with a unique key per row. Reference in supplied order:
`[(b1,5),(b2,0),(b3,-2)]`. Candidate in supplied order:
`[(b3,-1),(b1,6)]`. Compatibility is a supplied premise, not inferred from names.
No runtime calculation, scientific test or production execution is requested:
inspect and explain the supplied expressions/table as static documentary data.

**E2.M reusable method `aligned_weighted_yields`, version `1.0.0`.**
Applicability: two explicitly compatible finite weighted-yield populations with
identical key meaning, units and normalization. Inputs: actual ordered keyed
rows, compatibility basis, direction `candidate_minus_reference`, relative
normalization `signed_reference_percent`. Output: disjoint key sets, paired
absolute/relative differences, excluded/undefined rows and named coverage ratios.

Procedure and validation:

1. Validate unique keys separately in each input. Detect duplicates before
   alignment; never choose a row, sum duplicates or align by row position.
   Verify finite values, key meaning and supplied compatibility. Incompatibility
   stops numerical comparison; do not invent a normalization conversion.
2. Form common = reference intersect candidate, reference_only = reference
   minus candidate, candidate_only = candidate minus reference. Absence is
   not zero. Preserve original rows and name each population.
3. For each common key compute or inspect delta = candidate - reference and
   relative_percent = 100*delta/reference using the **signed** reference.
   When reference is zero, relative_percent is undefined, including 0/0.
   Do not fill absent rows, take an absolute denominator or emit infinity.
4. Report paired results and coverage as common/reference_population,
   common/candidate_population, and optionally common/union_population,
   each with numerator and denominator. Empty populations produce undefined
   coverage rather than a success percentage. Rounding never changes the
   stored expression; annotate displayed precision.
5. Validate the key partition is disjoint/exhaustive and each reported ratio
   has its named denominator. Check a missing row, duplicate key,
   incompatible normalization and zero reference explicitly. Reopen actual
   serialized inputs/results before classifying a future executed result.

Limits: descriptive comparison only; no tolerances, statistical test,
significance, production qualification, scientific acceptance, upload or retry.
Do not silently adapt a failed premise. A future computational execution needs
its own suitable validation ceiling/effects; this example is static explanation.
A skill could optionally package this method after maintained ownership,
interface/tests/failure/provenance/docs qualification. This document installs none.

**E2.R documentary result to check.** Unique-key alignment gives common={b1,b3},
reference_only={b2}, candidate_only={}. The common population size is 2;
reference=3, candidate=2, union=3. Thus reference coverage is 2/3 (about 66.67%),
candidate coverage 2/2 (100%), union coverage 2/3 (about 66.67%). “100% coverage”
without its candidate denominator would conceal the missing reference key.

| key | reference | candidate | delta | relative_percent |
| --- | ---: | ---: | ---: | ---: |
| b1 | 5 | 6 | 6-5=1 | 100*(1/5)=20% |
| b3 | -2 | -1 | -1-(-2)=1 | 100*(1/-2)=-50% |
| b2 | 0 | absent | undefined: missing row | undefined: no pair |

Negative controls, all static method checks: duplicate b1 in either input
invalidates unique alignment; a different per-event normalization makes the
numerical comparison incompatible; omitting b2 remains a missing row; supplying
candidate b2=0 would make a paired delta 0 and relative 0/0 undefined (candidate
b2=1 would give delta 1 with relative 1/0 undefined). A row with negative
reference retains its sign. An empty candidate has 0/3 reference coverage and
undefined 0/0 candidate coverage, not “fully covered”. None is a scientific test.

**E2.D delivery/stops.** Hypothetically use existing report/empty-patch paths
under the explicit diagnostics directory and record method contents, input rows,
conventions, undefined/missing cases and limits. No real writes occur in this
round. A mismatch in key meaning, uniqueness or normalization blocks only the
numerical claim that consumes it. The owner retains scientific acceptance;
completion/lint/review establish none.

**E2.G planned graph and relations.** E2.M steps 1–2 explicitly feed coverage;
steps 1–3 explicitly require both compatible inputs for paired differences.
This is an all-input join at `a`; row order adds no dependency. Failure to
establish compatibility leaves raw row descriptions available, not a validated
comparison. No alternative method or unresolved edge is supplied.

```mermaid
flowchart TD
 r["Reference rows"] -->|explicit E2.S| a["Validate both inputs and align unique keys: ALL"]
 c["Candidate rows"] -->|explicit E2.S| a
 m["Method 1.0.0 and conventions"] -->|explicit E2.M| a
 a -->|explicit E2.M.2| k["Coverage with named populations"]
 a -->|explicit E2.M.3; compatibility required| d["Paired signed differences"]
 a -->|explicit E2.D failed premise| p["Preserve raw descriptions; comparison unresolved"]
 k -->|explicit E2.D| o["Report: coverage and local numerical disposition, ALL for full result"]
 d -->|explicit E2.D| o
```

**E2.O observed view.** All actions remain unexecuted supplied scenario content.
The table is documentary expected reasoning, not runtime evidence or acceptance.
<!-- example_e2_end -->

## E3 — complete inert composed continuation

This is a continuation with distinct local numerical and remote-claim outcomes.
It is not automatically an orchestrated workflow: the only permitted activity
is static local explanation, with no upload action, Git mutation or ordered
cross-mode effects. P2 still applies to real orchestration/long-horizon triggers.

The ordinary run profile is external to the task bytes below (P4/R).

<!-- example_e3_start -->
# Finish a local comparison while preserving an unknown upload boundary

```yaml
prompt_id: example_yields_continuation
task_revision: '2'
decision_question: What local numerical completion is supported while accepted parsing coverage and an unknown upload outcome retain their separate boundaries?
prompt_mode: investigation_only
delegation_policy: allowed
allowed_to_modify:
  TOP26006_fw:
    diagnostics: /users/apiccine/work/correction-lib/reports/diagnostics/example_yields_continuation
read_only:
  - supplied_scenario_coverage_evidence_and_rows
  - all_tracked_files_indexes_refs_and_external_resources
validation_ceiling: static_inspection_only
execution_not_authorized: true
branch_policy: read_only_current_branch
heavy_command_permissions:
  allowed_to_modify:
    TOP26006_fw:
      diagnostics: /users/apiccine/work/correction-lib/reports/diagnostics/example_yields_continuation
  network_access: false
continuation_of: supplied_synthetic_coverage_case
accepted_prior_evidence:
  - claim: parsing_and_key_coverage_only
    artifact: supplied_scenario_evidence
    locator: E3.C
accepted_closure_layers:
  - supplied_scenario_parsing_and_key_coverage_within_input_boundary
invalidation_boundary: Changed row content, key interpretation, parsing or compatibility premises reopen only the dependent coverage/numerical claim; upload status has its separate boundary.
delta_scope:
  - static_documentary_completion_of_local_signed_differences
unresolved_checks_only:
  - local_numerical_completion
  - upload_claim_requires_separately_authorized_reconciliation
checks_not_to_repeat:
  - unchanged_supplied_scenario_parsing_and_key_partition
```

**E3.S authority/input.** Inert scenario, no historical owner acceptance and
no grant to perform a real action. TOP26006_fw installation input:
`/users/apiccine/work/correction-lib/.top26006/local_profile.yml`.
Actual supplied synthetic rows are reference `[(b1,5),(b2,0),(b3,-2)]` and
candidate `[(b3,-1),(b1,6)]`, same compatible weighted-yield normalization and
semantic stage. These are present here without a dependency on another prompt.
Static explanation only; do not run a payload, calculation/test or external query.

**E3.C supplied scenario evidence.** The scenario accepts only parsing and
coverage for these exact rows and unique-key meaning: common={b1,b3},
reference_only={b2}, candidate_only={}. Numerical completion remains open.
A separate upload attempt has `outcome_unknown`, with no upload readback,
network access, retry, recovery or remote mutation granted. “Accepts” here is
an explicit scenario premise, not a claim about an actual owner decision.

**E3.M reusable method `aligned_weighted_yields`, version `1.0.0`.**
Applicability: two explicitly compatible finite weighted-yield populations with
identical key meaning, units and normalization. Inputs: actual ordered keyed
rows, compatibility basis, direction `candidate_minus_reference`, relative
normalization `signed_reference_percent`. Output: disjoint key sets, paired
absolute/relative differences, excluded/undefined rows and named coverage ratios.

Procedure and validation:

1. Validate unique keys separately in each input. Detect duplicates before
   alignment; never choose a row, sum duplicates or align by row position.
   Verify finite values, key meaning and supplied compatibility. Incompatibility
   stops numerical comparison; do not invent a normalization conversion.
2. Form common = reference intersect candidate, reference_only = reference
   minus candidate, candidate_only = candidate minus reference. Absence is
   not zero. Preserve original rows and name each population.
3. For each common key compute or inspect delta = candidate - reference and
   relative_percent = 100*delta/reference using the **signed** reference.
   When reference is zero, relative_percent is undefined, including 0/0.
   Do not fill absent rows, take an absolute denominator or emit infinity.
4. Report paired results and coverage as common/reference_population,
   common/candidate_population, and optionally common/union_population,
   each with numerator and denominator. Empty populations produce undefined
   coverage rather than a success percentage. Rounding never changes the
   stored expression; annotate displayed precision.
5. Validate the key partition is disjoint/exhaustive and each reported ratio
   has its named denominator. Check a missing row, duplicate key,
   incompatible normalization and zero reference explicitly. Reopen actual
   serialized inputs/results before classifying a future executed result.

Limits: descriptive comparison only; no tolerances, statistical test,
significance, production qualification, scientific acceptance, upload or retry.
Do not silently adapt a failed premise. A future computational execution needs
its own suitable validation ceiling/effects; this example is static explanation.
A skill could optionally package this method after maintained ownership,
interface/tests/failure/provenance/docs qualification. This document installs none.

**E3.K continuation configuration.** The method body above is identical to
E2.M; the E3 task selects its optional union coverage output. Reuse only the scenario-accepted parsing/key-coverage portions of steps 1–2
for unchanged rows/key meaning under E3.C. Compatibility remains the supplied
scenario premise, not an expanded accepted validation claim. Complete only
step 3 as static documentary reasoning and inspect the named output ratios.
A changed input, key interpretation or compatibility premise reopens only its
dependent claim. This configuration is distinct from a method release; no
second prompt is needed to recover the method or rows.

**E3.R local result/checks.** Complete only the supplied documentary reasoning:
b1 delta=6-5=1, relative=100*(1/5)=20%; b3 delta=-1-(-2)=1,
relative=100*(1/-2)=-50%. b2 remains missing, no paired delta or relative result.
Reuse coverage common/reference=2/3, common/candidate=2/2, common/union=2/3,
with named populations of sizes 3,2,3. This completion is local and descriptive.
A duplicate b1 invalidates unique alignment; a changed normalization blocks
numerical compatibility; an absent b2 is not zero; adding candidate b2=0 makes
its paired relative 0/0 undefined. Those controls do not reopen unchanged
scenario coverage or establish a scientific test.

**E3.U upload boundary.** State `outcome_unknown`. Exact authoritative
reconciliation is prerequisite to any upload-completion claim, and must be
separately authorized. No readback is performed here and no reconciliation
result, idempotence or permission is invented. Even evidence that an upload
failed would not itself grant retry. Preserve a valid local result independently.

**E3.D delivery.** A hypothetical attempt records the reused coverage scope,
new local numerical disposition, unknown upload and unperformed actions in the
existing report/workbook and actual empty tracked patch under the explicit
diagnostics scope. Lint, review and executor completion are not owner acceptance.
In this round the example creates no files or effects.

**E3.G planned graph.** Solid edges are explicit prerequisites from
E3.C/M/K/R/U/D. The dotted relation is unresolved, not an authorized action.
`j` requires ALL coverage + rows + conventions. `p` requires ALL local result
and known-as-unknown upload status; it produces the permitted partial report.
The future `f` requires ALL local result and an evidenced remote disposition.
`t` has alternative inputs: the present partial route OR a separately
authorized future report extension. It never waits for both. The future branch
is documentary, outside this example's effects. List order creates no upload
prerequisite for the local result.

```mermaid
flowchart TD
 c["Supplied coverage accepted within parsing/input boundary"] -->|explicit E3.C/K| j["Local completion: ALL coverage + rows + conventions"]
 i["Actual rows and signed-reference method"] -->|explicit E3.S/M| j
 j -->|explicit E3.R| l["Local numerical disposition"]
 l -->|explicit E3.D partial route| p["ALL local result + upload status"]
 u["Upload outcome_unknown"] -->|explicit E3.U| p
 p -->|explicit E3.D permitted partial alternative| t["Terminal report view: partial OR future extension"]
 u -. unresolved E3.U separate authority and readback required .-> r["Future reconciliation: not granted"]
 r -->|explicit E3.U if actual evidence later exists| q["Future upload claim disposition"]
 l -->|explicit E3.D retained local evidence| f["Future ALL local result + remote disposition"]
 q -->|explicit E3.U/D| f
 f -->|alternative future extension; separately authorized| t
```

**E3.O observed scenario view.** Only the supplied parsing/coverage node `c`
has scenario-accepted status; `j`/`l` remain numerically open in that evidence;
`u` is unknown; `p`,`t` are planned reporting views; `r`,`q`,`f` are unperformed. The expressions in E3.R are proposed
completion content, not an invented executed history. No real upload or local
runtime result is asserted. A real iteration would be recorded as a cycle of
separately authorized attempt instances, never as a forced acyclic success path.
<!-- example_e3_end -->

## R — two simulated inert run records

These are authored configuration illustrations, not launches, inference outputs,
fallbacks or evidence of actual model availability. Both bind the exact E2 task
between its markers and its supplied input rows/method/conventions/criteria.
The evidence receipt extracts those bytes once and records their SHA-256 for
both records, along with retained guide/input/method bytes. The selected factor
is the model/reasoning pair. No cost or outcome is simulated.

```yaml
simulated_runs:
  - run_id: example_weighted_yields_run_a
    task: {prompt_id: example_weighted_yields, task_revision: '2', content_locator: E2_marker_bytes}
    inputs: E2.S_exact_rows
    method: E2.M_1.0.0_with_E2.R_denominators
    selection_author: scenario_prompt_author
    provider: OpenAI
    product: Codex_CLI
    preferred_codex_model: gpt-6-luna
    reasoning_level: high
    model_selection_rationale: Bounded keyed comparison with fixed adversarial conventions; simulated author selection using local focused-work guidance.
    guides: [model_selection_common_v0.md_v0.1.0, providers/openai_selection_v0.md_v0.1.0]
    selected_observation: not_observable
    runtime_observation: not_observable
    execution_status: not_executed
    output_status: no_model_output
  - run_id: example_weighted_yields_run_b
    task: {prompt_id: example_weighted_yields, task_revision: '2', content_locator: E2_marker_bytes}
    inputs: E2.S_exact_rows
    method: E2.M_1.0.0_with_E2.R_denominators
    selection_author: scenario_prompt_author
    provider: OpenAI
    product: Codex_CLI
    preferred_codex_model: gpt-6.1-sol
    reasoning_level: medium
    model_selection_rationale: Deliberate simulated alternative pair for controlled comparison of the same verifiable task; no superiority assumed.
    guides: [model_selection_common_v0.md_v0.1.0, providers/openai_selection_v0.md_v0.1.0]
    selected_observation: not_observable
    runtime_observation: not_observable
    execution_status: not_executed
    output_status: no_model_output
```

Guide references above resolve to the adjacent versioned candidate files,
retained in this revision's postimage and receipt. E1's hypothetical author can
select a profile externally without a method/skill. E3 likewise retains its
continuation authority/closure independently of any author-selected profile.

## B — accounting over consistent populations

The current master CPC population is fifteen universal labels (T). v0.1.0 had
eleven, including task_revision. v0.2.0 has eight task labels. This is a new
comparison with explicit populations, not another description of the old 15→11.

| Population/change | Count and actual interpretation |
| --- | --- |
| Master universal labels | 15: 7 retained task labels, 3 transferred run values, 5 derived/conditional values |
| Candidate task labels | 8: those 7 plus task_revision |
| Master→v0.2.0 task-label difference | 7 fewer per task; 21 across the three examples, contract_count only |
| v0.1.0→v0.2.0 task-label difference | 3 profile values transferred per task; no selection work eliminated |
| Values author avoids routinely transcribing | short_title, workspace_root, repo_locations, patch_kind_expected, final_chat_deliverable; explicit material exceptions still authored |
| Values recurring per run | Author's model, reasoning and rationale, plus provider/product, task binding, guide version/content locators; actual selected/runtime observations remain evidence |
| Fixed preparation/maintenance | Installation profile, common/provider guides and optional stable methods require real acquisition, review and updates |
| Per-task/per-attempt costs | Semantic mandate, grants, graph and review; run selection/configuration, preflight, preservation, observed graph and report; repeat runs are not new independent scientific tasks |

Derived titles/default delivery and runtime path binding reduce duplicate
transcription only where their consumers and inputs are unambiguous. The classic
route already supports concise prose, profile resolution, evidence reuse and
ordinary coding without artificial stages; these are not new benefits.
Moving selection outside the task enables byte-identical task reuse as a design
property. It does not demonstrate less total work or better empirical portability.
E1 pays for a mandatory one-node graph and has no demonstrated net effort saving.
E2's retained method still occupies content; E3's partial/unknown graph still
needs review. No time, tokens, costs, scientific trials or performance were measured.

## T — disposition of all fifteen current universal fields

| Current field | Candidate placement | Consumer / preserved responsibility |
| --- | --- | --- |
| prompt_id | Task | Stable identity and evidence path; attempts have separate locators |
| short_title | Derived, explicit for a distinct material consumer | Human display/search |
| prompt_mode | Task | Activity boundary/router, no grant |
| preferred_codex_model | OpenAI run configuration only | Author selection, dispatch derivation and comparison evidence |
| reasoning_level | OpenAI run configuration only | Native effort selection and immutable attempt |
| delegation_policy | Task | Authorized delegation and independent-review mandate; configuration cannot expand it |
| model_selection_rationale | Run configuration | Explain author selection against retained guide version |
| workspace_root | Runtime observation; explicit physical binding when needed | Installation resolver and pre-effect identity |
| repo_locations | Runtime observation; explicit binding when needed | Typed repositories and exact carrier/target identity |
| allowed_to_modify | Task | Scope ceiling over the sole positive grant map |
| read_only | Task | Inputs and protected surfaces |
| validation_ceiling | Task | Maximum validation, distinct from actual checks |
| decision_question | Task | One owner decision/acceptance boundary |
| patch_kind_expected | Derived ordinary default; explicit exception | Actual patch collector and reviewer |
| final_chat_deliverable | Standard report contract; explicit exception | Task-specific result and material language/format/recipient |

task_revision is the new task identifier consumed by P4. Runtime observations
never masquerade as author selection; the run adds no effect surface. Conditional
contracts remain activity-selected with no numerical field cap.

## N — exact proposed normative replacements and dependent consumers

These are proposed postimages/edits for a later authorized adoption round.
Only this candidate and the two linked candidate guides change now. Source-relative sections below
identify bounded edits; no governance or installed skill is modified here.

### N1. CPC replacements

Replace the `Every actionable prompt contains:` paragraph and its field list
with this exact text:

> Every actionable prompt contains prompt_id, task_revision, decision_question,
> prompt_mode, delegation_policy, allowed_to_modify, read_only and
> validation_ceiling. Ordinary model/reasoning selection, rationale and consumed
> guide version belong to the separately retained author-selected run configuration
> referring to the exact task. That configuration is data, not a second mandate.
> The task also states actual authority, inputs/conventions, observable result,
> relevant failure behavior and acceptance boundary. Scientific choices and
> exact targets cannot be supplied by a default or method. Flexible semantic
> blocks are permitted; definitions must have one unambiguous authority.

Replace `Materialize selected typed repository IDs and resolved local paths;
preflight them. A missing profile needs explicit paths, not a guessed fallback.`
with:

> Name selected typed repository IDs and exact scoped targets, and bind the
> existing YAML installation profile input. The author fixes repository identity,
> semantic branch/target roles, exact effects and material physical bindings;
> the executor resolves, verifies, serializes and reopens workspace_root,
> repo_locations and volatile applicability facts before each dependent effect.
> Supply explicit paths when the profile is unusable or cannot uniquely bind the
> authorized target. Dispatchable includes mandatory runtime preflight; author-side
> observation of volatile facts is not universally required. Ambiguity of target
> ownership or a real owner/scientific choice stops only its dependent effect.
> The installation profile and run configuration grant no effect or science.

Replace the model-selection row in the conditional router with:

> Author-selected run configuration, native model/reasoning selection, CLI
> dispatch or new author-selected fallback: governance/model_policy.md and its
> versioned common/provider guide references. Run data is external to exact task
> bytes; task permissions and independence remain authoritative.

Append to Construction, keeping the existing permission, branch, source and
preflight rules:

> short_title is an optional display value derived from decision_question unless
> a distinct consumer requires an explicit title. For an ordinary task-owned
> tracked delta derive patch_kind_expected as prompt_local; for no tracked
> change use empty_no_changes. Explicitly select any cumulative comparison or
> other material exception, and always report the actual patch and method.
> Use the existing standard report/patch/final-response contract without
> repeating final_chat_deliverable; state any material language, format,
> recipient or product exception explicitly. Task-specific result content
> remains mandatory. Record exact task revision, consumed method/input/config
> contents, immutable attempt configuration, outputs, evidence and decisions
> in existing reports/checkpoints; a hash or path alone does not preserve bytes.

Replace the optional `workflow_graph` sentence in the conditional router with:

> Every task has a derived planned workflow_graph, even a one-node task. It is
> documentary and non-authoritative. Preserve source locators and label
> explicit, inferred and unresolved relations, all-input and alternative joins,
> iterations and partial-delivery routes. Do not infer independence from absent
> arrows or dependencies from list order. Correct a drawing contradicted by
> clear source text; expose ambiguous source decisions. Reports keep a distinct
> observed view. Graph defects do not annul independent supported results or
> grant effects. Orchestration triggers remain activity-based across modes,
> including long-horizon work and delegation; routine editing/checking/commit
> within one coding contract remain ordinary.

Append to the one-self-contained-prompt paragraph:

> An optional reusable method may supply only stable procedure, with exact
> revision, applicability, inputs/outputs, validation, limits and preserved
> consumed content. It cannot supply task mandate, effects, target selection,
> scientific choices or acceptance. An unresolved reference blocks only its
> dependent use. Inline the contents when no retained resolvable source exists.
> A playbook is procedure; a skill is an optional maintained package; the
> workbook is the case/attempt record in existing reports, not a new registry
> or three copies of the same instructions.

### N2. AGENTS and model_policy dependent postimages

**AGENTS — replace the opening path paragraph in Scope, effects and capability:**

> Name selected typed repository IDs and exact scoped targets, and bind the
> existing YAML installation profile input. The author fixes repository identity,
> semantic branch/target roles, exact effects and material physical bindings;
> the executor resolves, verifies, serializes and reopens workspace_root,
> repo_locations and volatile applicability facts before each dependent effect.
> Supply explicit paths when the profile is unusable or cannot uniquely bind the
> authorized target. Dispatchable includes mandatory runtime preflight; author-side
> observation of volatile facts is not universally required. Ambiguity of target
> ownership or a real owner/scientific choice stops only its dependent effect.
> The installation profile and run configuration grant no effect or science.

Retain the following existing sentences about no implicit write permission,
diagnostics not granting tracked edits, cross_repo_escalation_note and nested
repository staging. The quoted path rule is literally identical to N1's proposed
CPC path paragraph. Current master already allows runtime binding; this is a
clearer common wording, not a new gate or an assertion that an exception was
needed for runtime binding.

**AGENTS — replace the paragraph beginning “Prompts retain explicit”:**

> Tasks retain delegation_policy and any requirement for independent review.
> The author selects and communicates each immutable run configuration outside
> the reusable task: provider/product, native model/reasoning, rationale and
> consumed common/provider guide versions with retained content locators.
> The executor applies that selection and records requested, directly selected
> and runtime-reported values distinctly; unknown is not_observable. Do not infer
> exact identity from a family label. An observed mismatch or switch stops the
> attempt for a fresh author-selected dispatch. Exact profile proof gates only
> when decision-material. Configuration cannot change science, permissions,
> methods, acceptance or delegation; a scientific model-object constraint stays
> in the task. model_policy owns common selection responsibilities; provider
> guides own native choices, not authority or availability claims.

**AGENTS — append to Compact reporting and artifacts:**

> The existing report is the task/run workbook. Preserve exact task bytes and
> revision, consumed input/method/configuration contents or retained immutable
> locators, author-selected run configuration and guide versions, actual
> selected/runtime observations with provenance, outputs, decisions and a distinct
> observed graph. Preserve before consuming dependent evidence/effects; a hash or
> path alone is not content retention. Derive ordinary delivery under CPC and
> state material exceptions. No report grants authority or acceptance.

**governance/model_policy.md — exact replacement of the universal declaration
list and the paragraphs deriving profile from prompt fields:**

> Common selection responsibilities and criteria follow the adopted common
> guide; provider-specific vocabulary and native recommendations belong in the
> corresponding provider guide. In the candidate these homes are
> docs/design/model_selection_common_v0.md and
> docs/design/providers/openai_selection_v0.md; adoption must establish their
> maintained normative homes without duplicate routing tables.
> The author selects an immutable run configuration outside the reusable task,
> retaining provider/product, native model/reasoning, rationale and exact guide
> versions/content. For the OpenAI/Codex procedure, preferred_codex_model,
> reasoning_level and model_selection_rationale are run configuration values.
> Derive model_profile.model and model_profile.reasoning_effort invocation-locally
> from that configuration; do not persist duplicate selection aliases. The task
> retains delegation_policy and scientific model-object constraints. One attempt
> has one profile; observed mismatch/switch stops it for new author selection and
> dispatch. Record requested, directly selected and runtime-reported values
> distinctly with not_observable where needed. Evidence or permission gaps are
> not remedied by a stronger model. Exact profile proof gates only material claims.

**Remaining model_policy consumer edits (bounded literal substitutions):**

- Replace “Every prompt must declare” and its four-value list with the paragraph
  above; retain delegation as a task contract rather than run profile membership.
- Replace “derive model_profile from the existing prompt fields” with “derive
  model_profile invocation-locally from the author-selected run configuration”.
- In the new_attempt fallback illustration, place preferred_codex_model in the
  new run configuration and derive model_profile.model; do not change fallback
  selection or new-dispatch authority.
- Replace “Explain the selected pair in model_selection_rationale” with “Explain
  the author-selected pair in the run configuration's model_selection_rationale”.
- The future OpenAI provider guide is the sole home of the current concrete
  vocabulary, five defaults, Terra specialization and upper/legacy exceptions.
  Replace their model_policy tables/catalog/CLI mapping with a versioned guide
  reference at adoption; preserve historical decisions as attributed history.
  The candidate OpenAI guide below carries those recommendations without
  activating them or changing this session's selected profile.
- Keep observation semantics, exact-proof materiality and no-silent-switch
  invariants; where report reasoning_level means requested effort, label that
  meaning and do not duplicate it as a task input. Ultra remains a separately
  authorized execution control, never provider equivalence or an effect grant.

Authority, permission maps, modes, master-source rule, scientific boundaries,
foreign-work preservation, commit closure and Git/production interfaces survive.
The compiler currently exists as historical/current implementation fact. The
successor program retires compiler/Gherkin; it has no future compatibility
requirement or adapter. No compiler code or normative file is removed here.

### N3. Templates, references and method surfaces

| Surface | Exact proposed dependent edit | Ownership/qualification limit |
| --- | --- | --- |
| templates/read_only_prompt.md | Replace illustrative body with A's eight-task-field aid and separate P4 run binding followed by authority/inputs/result/branch/grant/graph/acceptance slots; label it non-dispatch-ready | CPC owns requirements, not this aid |
| templates/bounded_change_prompt.md | Keep its separate authority/acceptance roles and scientific boundary; replace the mandatory observed-HEAD author slot with semantic repository/target/profile binding plus pre-effect readback; add task_revision and derived graph slots | Conditional commit/effect fields unchanged |
| templates/continuation_prompt.md | Keep closure/delta/invalidation/checks-not-to-repeat; add task_revision and planned/observed graph distinction; use runtime branch readback rather than implied historical freshness | No second continuation vocabulary |
| templates/review_report.md | Add consumed method/config contents, graph/source disagreement and observed-view checks to independent checks/limits; retain acceptance fields | Review remains advisory |
| docs/reference/prompt_contract.md | Replace universal-field summary with the exact eight-task-field list in N1; add P2's conditional installation/delivery defaults and mandatory graph statement; retain maps/router links | No competing schema |
| docs/reference/report_contract.md | Add the exact workbook paragraph in N3a, referring to AGENTS as authority | Reuse report paths, no new state database |
| .agents/skills/correction-lib-prompt-contract/assets/prompt_template.md | Replace its four-field scaffold with A's eight-task-field aid and separate P4 run binding and explicit conditional-contract/graph reminder | Authoring helper remains non-exhaustive |
| .agents/skills/correction-lib-prompt-contract/SKILL.md | Add: “Candidate direct-prompt fields and graphs require author semantic review; this helper does not certify them.” | Ordinary unknown-field acceptance remains valid; no new certification |
| prompt_schema.json and validate_prompt.py under that skill | No semantic enforcement change proposed; preserve bounded parsing and not_assessed result | A new semantic validator would be a separately scoped reusable capability, not an implied extension |
| Other three existing local skills | No payload/interface change; refer to their existing copy-only, handoff-only and inert-review limits when selected | Do not invoke them automatically or weaken their boundaries |
| Reusable method contents | Use E2.M as inline playbook content 1.0.0; future extraction has an explicit maintained home and ownership/validation decision | No mandatory skill, registry, tool or duplicated workbook |

Tutorials remain unchanged in this step; an adoption round must qualify actual
author→executor→review consumers and update reached teaching material. The
compiler's current PROMPT_CORE consumes the old fifteen-field population and
does not supply task_revision. That fact is historical/current implementation,
not a future consumer requirement. The program retires compiler/Gherkin rather
than adapting or preserving them. This round neither runs nor removes them;
no coexistence exception or compiler compatibility qualification gates this delta.

| Candidate rule | Future owner / dependent consumer change |
| --- | --- |
| Task/run boundary, task bytes and derived graph | CPC construction; AGENTS execution/workbook; templates and references below |
| Common criteria and fixed/per-run cost accounting | Common selection guide, linked from model_policy; no provider catalog there |
| Native OpenAI labels/defaults/options and dated vendor distinctions | OpenAI guide as sole provider home; model_policy points to it rather than copying tables |
| Requested versus observed profile, immutable attempt and authority | AGENTS/model_policy invariants; reports retain distinct evidence |
| Installation path binding | Identical N1/N2 wording in CPC/AGENTS; no new author-side volatile-state gate |
| Compiler/Gherkin | Separate retirement implementation; no successor compatibility consumer |

The future normative path names require adoption; these three design files stay
inactive. Add a provider guide only for an actual need, with native options and
limits, sources/version, ownership and observed accessibility, never a fictitious
cross-provider mapping or empty stub.

### N3a. Literal dependent template and reference postimages

The following exact proposed file bodies complete the edit inventory above.
They remain inert text inside this candidate. Slots are intentional authoring
aid placeholders, not unfilled example decisions. No referenced root/skill file
is changed by including its proposed postimage here.

**templates/read_only_prompt.md — replace whole file:**

````markdown
# Read-only prompt — proposed authoring aid, not dispatch-ready

Fill against current master CPC and AGENTS. Replace every slot; select all
activity-triggered contracts. A field count or lint result is not authorization.

```text
prompt_id: [stable identity]
task_revision: [revision]
decision_question: [one decision and owner boundary]
prompt_mode: investigation_only
delegation_policy: [selection]
allowed_to_modify: [exact diagnostics scope or empty map]
read_only: [exact inputs and protected resources]
validation_ceiling: static_inspection_only
```

Run binding: [separate author-selected configuration, rationale and retained guide versions].
Mandate/authority: [actual provenance, no scientific choice inferred].
Repository/profile: [typed IDs, exact profile input; explicit material paths].
Branch/grants: [read_only_current_branch and exact positive capability map;
no tracked writes, no inferred network grant].
Inputs/procedure/result: [actual contents/conventions, observable deliverable].
Planned graph: [derived one-node or larger view with source locators, relation
status and join/partial semantics; no effect authority].
Evidence/stops: [bounded checks, limits and independent valid partial results].
Delivery: existing report and actual empty tracked patch, observed graph and
attempt contents; [any material language/format exception].
Acceptance: [responsible evidence and scientific roles; executor/reviewer do
not accept their own result].
````

**templates/bounded_change_prompt.md — replace whole file:**

```markdown
# Bounded change prompt — proposed authoring aid, not dispatch-ready

Use the eight named task inputs in the proposed CPC, including task_revision;
replace slots and add all applicable conditional fields before dispatch.

- Decision question: [one substantive decision and observable result].
- Research lead / effect authority: [role, scope and mandate provenance].
- Research coordinator / bounded evidence acceptance: [role and scope].
- Scientific lead / interpretation acceptance: [role or not applicable reason].
- Prompt author / executor / independent reviewer: [separate responsibilities].
- Run binding: [separately retained author-selected provider/product/profile,
  rationale and guide versions; task retains authorized delegation/independence].
- Repository/profile/targets: [typed IDs, exact profile, semantic branch role,
  exact paths/effects; explicit physical targets where decision-material].
- Mode/ceiling: [existing values; actual validation may be narrower].
- Branch/permissions: [applicable exact contract and sole positive grant map;
  for orchestration use stage policies/maps and non-authorizing envelope].
- Commit: [authorized_commit_scope, adopted changes or none,
  preserve_and_exclude, exact_path_only and existing commit-closure boundary].
- Inputs/conventions/exclusions: [actual contents and fixed scientific choices].
- Pre-effect readback: [relevant branch/HEAD/index/conflict, master, profile,
  target and collision facts; no author-invented live state].
- Planned graph: [derived relations, locators, join/partial/iteration semantics].
- Checks/evidence/stops: [actual consumers, failed/unknown boundaries, limits].
- Delivery: existing report/patch and observed graph/attempt contents;
  [explicit cumulative comparison or delivery exception when material].
- Acceptance: [evidence acceptance after review, scientific acceptance separate;
  neither creates a new effect grant].

No graph, method, profile, template or executor status supplies authority.
```

**templates/continuation_prompt.md — replace whole file:**

```markdown
# Continuation prompt — proposed authoring aid, not dispatch-ready

Use master authority and this inactive proposed eight-task-input contract, including
prompt_id, task_revision and decision_question; supply every applicable
conditional field. Preserve existing continuation names.

- Run binding: [separate immutable author-selected configuration and retained guide versions].
- continuation_of: [bounded prior task identity].
- accepted_prior_evidence: [claim, artifact, locator, validity and actual
  acceptance provenance; scenario evidence labelled as such].
- accepted_closure_layers: [only actually accepted layers].
- delta_scope: [new question/change, targets and exact effects].
- invalidation_boundary: [consumed dependencies that reopen each claim].
- checks_not_to_repeat: [unchanged accepted checks].
- unresolved_checks_only: [new evidence needed for this delta].
- Authority/inputs/conventions: [complete new mandate and actual sources,
  selected method revision/content/configuration; no companion instructions].
- Branch/permissions/preflight: [fresh consumed Git/resource facts, exact
  applicable contract and sole positive effect map; no replay from silence].
- Planned graph: [source-derived claim/action relations with join/partial and
  unresolved status; do not block local evidence on an independent remote gap].
- Stops/delivery: [preserve valid partial work, unknown-effect readback boundary,
  existing report/patch/checkpoint and distinct observed graph].
- Acceptance: [bounded evidence role and separate scientific decision role].

No checkpoint, accepted evidence, graph or lint result grants a new effect.
```

**templates/review_report.md — replace whole file:**

```markdown
# Review report — proposed teaching aid

- Decision question, exact task revision and source identities:
- Actual authority/consumer contracts consulted:
- Exact task bytes and consumed input/method contents and retention locators:
- Separate author-selected run configuration and retained guide versions:
- Requested versus directly selected/runtime-reported observations and metadata sources:
- Executor claims, distinct from direct observations:
- Independent checks, evidence locators and results:
- Graph/source disagreements, joins, partial routes and observed-view checks:
- Blocking and nonblocking findings, each with dependent consequence:
- Counterexamples, unsupported claims and recommended corrections:
- Not evaluated, residual risks and completeness/confidence limits:
- Reasoned advisory verdict and controller dispositions:
- Task/evidence acceptance decision and scope, separately scientific acceptance
  or pending decision; review alone confers neither:
- Reusable valid evidence, invalidation boundary and checks not to repeat:

Apply current AGENTS/CPC and native policy. This aid grants no effect,
certifies no governance completeness and creates no new acceptance layer.
```

**docs/reference/prompt_contract.md — replace whole file:**

```markdown
# Prompt contract

CPC.md owns construction; AGENTS.md owns authority, safety and the trigger
union. Universal named author inputs are prompt_id, task_revision,
decision_question, prompt_mode, delegation_policy, allowed_to_modify, read_only
and validation_ceiling. Model/reasoning selection, rationale and guide versions
are separately retained author-selected run configuration, referring to exact
task bytes; they cannot change task permissions, independence or science.
Actual authority, inputs/conventions, result, relevant
failure behavior and acceptance boundary remain required semantic content.

Name typed repository IDs, exact scoped targets and the installation profile.
Apply the identical CPC/AGENTS path-binding rule: author fixes semantic roles
and material physical bindings; executor resolves/verifies/serializes/reopens
workspace_root/repo_locations and volatile facts before dependent effects.
Supply explicit paths if no usable profile uniquely binds the authorized target;
author-side observation of volatile facts is not universally required.
Title and ordinary patch/final-response conventions derive under CPC;
material exceptions remain explicit. No scientific/effect decision is defaulted.

Non-orchestrated positive grants live only in heavy_command_permissions with
outer branch_policy. Orchestrated workflows prohibit those outer fields:
stage_branch_policy and stage_effect_permissions govern each stage and the
workflow_effect_envelope grants nothing. Activity-based orchestration,
long-horizon, production, Git, evidence and model triggers retain their fields.
Ordinary editing/checking/commit within one coding contract remain ordinary.

Every prompt includes a source-derived documentary graph, even one-node work,
with explicit/inferred/unresolved relations, joins, partial routes and real
iterations. It grants no authority; reports record a distinct observed view.
Continuations retain current closure/delta/invalidation/checks-not-to-repeat
fields. Optional methods supply preserved stable procedure, never a second
mandate or hidden permissions. Mechanical lint is not governance completeness,
execution, qualification or owner/scientific acceptance.
```

**docs/reference/report_contract.md — append this exact paragraph:**

> The existing report is the direct-prompt attempt workbook. Preserve exact
> task bytes/revision and consumed input/method/configuration contents or retained
> immutable content locators, separate author-selected run configuration and guide
> versions, requested/selected/runtime observations with provenance, output and
> decision evidence, and a distinct observed documentary graph. Record resolved
> workspace_root/repo_locations before dependent effects. A hash or filename
> alone does not preserve contents. Existing report, patch, collision and
> conditional stage/checkpoint mechanisms remain; no registry or parallel
> workbook is introduced. AGENTS and CPC remain the authority.

**.agents/skills/correction-lib-prompt-contract/assets/prompt_template.md —
replace whole file:**

```markdown
# Prompt authoring scaffold — proposed and non-exhaustive

Read current CPC/AGENTS and applicable native policy. Supply the eight named task
inputs explicitly: prompt_id, task_revision, decision_question, prompt_mode,
delegation_policy, allowed_to_modify, read_only, validation_ceiling. Preserve
a separate author-selected run configuration with provider/product, native
model/reasoning, rationale and consumed guide versions; it grants no effects.
Fill each from actual author decisions; no field count makes a task dispatchable.

State mandate/authority, selected typed repositories/exact targets/profile,
actual inputs/conventions, result and acceptance boundary. Add exact applicable
branch, effect, commit, continuation, evidence, orchestration, long-horizon,
production and model fields from the trigger union. Include the derived graph
with source locators, explicit/inferred/unresolved relations, joins and partial
routes. Preserve method/input/config contents and actual observed attempt state
in existing reports. Standard delivery and installation observations follow
CPC defaults; explicit material exceptions still require author selection.

Run mechanical lint on the exact filled prompt; it does not assess governance
completeness or authorize execution. Unknown future fields are not certification.
```

The exact SKILL.md insertion is the quoted sentence in N3's skill row, placed
at the end of its Authority boundary section. No script/schema replacement is
proposed. Method contents remain inline E2.M/E3.M; future extraction is separate.

### N4. Inert authoring, future use and qualification boundary

Writing the inactive candidate and linting inert examples requires no CPC
exception. The operational prompt for this round obeys current master. These
future-contract examples are not current-CPC dispatches: their model values are
external, several current universal values are derived, and graph/revision rules
are proposals. Mechanical acceptance does not activate them. Any future actual
use is a distinct owner-authorized task under its then-current governance; no
automatic exception, pilot, adoption or compiler compatibility gate is created.

The first unproven step remains efficacy in a real consumer. A separately
authorized evaluation can compare full classic/candidate authoring effort,
recovery of intent/permissions/inputs, ambiguity, review and partial-result
handling with fixed comparison factors. Static counts are not time/token/cost
measurements or evidence of greater portability. General adoption, integration,
merge/push, runtime experiments, compiler retirement and an integrated Akademia
audit/plan remain outside this round; Akademia requires separate owner GO.

## V — static semantic review checklist and disposition record

The controller checks this exact document and examples; independent review
findings and dispositions are preserved in the task's evidence directory.
The final execution report identifies the reviewed postimage and any corrections.
Review B1 corrects E3 joins/routes; B2 adds literal N3a postimages; B3 clarifies
E1 profile reads versus tracked-write exclusion; B4 preserves identical method
contents with the continuation configuration recorded separately. These are
authoring corrections within s2, not runtime qualification or owner acceptance.
B5 historically recorded the current compiler consumer; this revision supersedes
its proposed future compatibility requirement with the owner-decided retirement destination. The review record retains the process-order deviation and its
impact assessment; it does not claim retrospective strict conformance.
The following are discriminating checks, not claims that payloads were run:

| Counterexample | Candidate handling / locator |
| --- | --- |
| Same task, different profiles | R and P4 bind two inert run pairs to identical E2 task/input/method bytes |
| Guide/version unresolved | P4 limits reproducibility of the selection; does not fabricate current guide content |
| Model unavailable | P4 requires new author selection/dispatch, no silent fallback |
| Profile tries to grant effects | P1 denies added upload, retry, production or delegation; task grants remain sole authority |
| Atomic task needs no skill | E1.R uses direct supplied-text explanation, one-node graph; P4 makes methods optional |
| Unresolved method reference | P1/P4 require actual preserved contents before dependent use; E2/E3 inline their procedures |
| Different coverage denominators | E2.R names reference=3, candidate=2, union=3; P4 treats a changed denominator as a different method/input configuration, not a model effect |
| Graphic attempts to permit retry | P3 and E3.U deny graph authority; no readback/retry grant exists |
| Unknown upload blocks local result | E3.C/R/U/G preserve local coverage/numerics separately; only remote claim needs reconciliation |
| Conditional precision erases orchestration | P2 applies the trigger union across modes and long-horizon work, retaining exact stage grants and commit fields |
| Routine edit/check/commit over-staged | P2 and N1 preserve ordinary one-contract coding |
| Row order treated as correspondence | E2.M aligns unique keys, not positions |
| Missing row treated as zero | E2.R/E3.R keep b2 absent despite reference zero |
| Negative or zero reference mishandled | E2.R shows -50%; paired b2 zero controls remain undefined |
| Lint claimed as adoption | Status/N4 and E1–E3 deny current dispatch authority and acceptance |

Mechanical lint covers bounded text parsing, duplicates, placeholders and a
small supplied-value consistency surface. Its results are reported separately
as mechanical_validity, internal_consistency and governance_completeness:
not_assessed. Author/independent semantic review examines actual consumers and
meaning; it is design evidence. No example payload, scientific/runtime test,
compiler qualification or production has been executed to validate this design.

Continuation review qualifications retained: the earlier E1 reused_unchanged_lint
flag did not demonstrate reuse from its first attached sample because the bytes
differed; the final historical lint was on corrected bytes. No invocation count
is reconstructed and old evidence is not rewritten. Earlier P1 began s1 before
s0 serialization/reopening: this remains a procedural deviation, without proof
of a mandate defect. A rerun cannot cure that history. This continuation records
its own completed/reopened pre-effect readbacks and never claims retroactive cure.
