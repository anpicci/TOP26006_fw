# Tutorial 5: review and accept returned evidence

**Learning goal:** inspect a returned change and separate completion, evidence, interpretation, and acceptance.

- **You are:** a researcher reviewing a returned synthetic interpretation.
- **You want:** a defensible recommendation and an explicit human decision boundary.
- **You will use:** the maintained observed scenario and review-report template.
- **You will change:** only your own lesson review record outside maintained inputs.
- **You will not change:** returned evidence, fixtures, templates, scratch histories, data, code, or environment.
- **You should finish with:** a source-bound review recording a provenance finding, its reported repair, limits, and acceptance status.
- **Prerequisites:** read access to the linked files and somewhere to keep personal notes. Tutorial 4 execution, its shell variables, and its commits are not required.

## Identify the returned evidence

Open the [observed scenario](../../examples/research_workflow_lifecycle/observed_scenario.md). Use this maintained documentary artifact as the returned evidence for this exercise. Record its path and current SHA-256, obtained from your actual checkout root:

```sh
cd /absolute/path/to/TOP26006_fw
sha256sum examples/research_workflow_lifecycle/observed_scenario.md
cat examples/research_workflow_lifecycle/observed_scenario.md
```

Replace the absolute checkout path before running these read-only commands. The scenario's analysis seed is `803b07b22f32fb813257adbe9f74890fb31c7e3c`; its first returned note is `eb40d2703e74350e09e00c459459d706bbc8fa74`; its provenance repair is `c9f7c6b9e090fdc3ae3c29b34171cf3a7cb88ff4`. These identify historical stages in a separate scratch history. They are not commits you must possess or recreate, and they are not your checkout HEAD.

The entry condition is a readable scenario containing those stages and its simulated-review qualification. If it is missing or materially different, record that discrepancy before using it. Do not substitute an unidentified Tutorial 4 note. The scenario is a compact report, not the underlying full command receipt or full note diff; those limits constrain the review.

## Review four distinct things

Use the existing [review report](../../templates/review_report.md) as a read-only guide. Write your own record with the following distinctions:

| Layer | What you can record here |
| --- | --- |
| Executor result | The scenario reports completion of a first note, followed by a provenance repair. Completion is a claim to examine. |
| Observed evidence | You directly read the scenario's recorded identities, CSV hash, quantities, finding, and qualification. You have not directly inspected the historical Git objects or execution log. |
| Reviewer's interpretation | The reported missing source commit and CSV hash block acceptance of the initial note's provenance. That defect does not by itself invalidate the reported arithmetic. |
| Human acceptance decision | The historical research coordinator accepted the bounded task/evidence record after the reported provenance repair; that function was simulated, as recorded in the scenario. Your recommendation creates no real task/evidence acceptance or scientific acceptance; a real decision remains pending. |

Read the scenario's output row: five measurements; mean `10.060000`; model-based standard error `0.089443`; chi-square `4.300000`; four degrees of freedom. Keep its independent Gaussian assumption and synthetic descriptive scope attached. The CSV identity is `f6b9311f0ce6e675999c5ef31a14d82589179a9f8e82be917df6695c6893c294`.

Record the initial provenance finding separately from the reported repair. A repair can name an earlier source identity; a commit cannot cite its own final identity inside its own contents. The scenario reports that the numerical run was not repeated. Do not run it merely to complete this review lesson.

## If the returned task used the compiler

A [generated prompt and compilation receipt](../how_to/compile_governance_workflow.md)
can show the source contract, bound claims, translation and mechanical checks.
They prove neither execution nor independent review nor acceptance. Obtain the
actual returned evidence for the claim being reviewed. A hash records byte
identity; it does not prove correctness, containment or authorization. Lint PASS
does not establish governance completeness or semantic/scientific correctness.

Package-authored booleans do not constitute a reviewer/owner decision or close
a finding. The external caller/reviewer must own the controlling review manifest;
a required declared gate must actually resolve and evaluate the cited evidence.
A scalar gate evaluates exactly one evidence locator, and finding closure must
cite that exact evaluated operand in a required passing locator gate. Supporting
locators for manual, repository, count or patch-set checks cannot close an
unrelated finding. JSON equality preserves types: `true` differs from `1` and
`false` from `0`. Package contents remain inert; a passing package-authored
boolean cannot certify its own review.
The utility does not cryptographically authenticate human reviewer identity.
These distinctions do not change the fixed scenario or turn this exercise into
a compiler run or evidence-package execution.

## A worked example: from compiled prompt to returned evidence

Suppose you need to understand the committed difference between a candidate
revision and the observed master revision before deciding whether to integrate.
The useful result is a record of their identities, ancestry and committed delta.
Finding that master is not an ancestor would answer the question too; obtaining
a favorable integration topology is not the success criterion.

This historical example followed that bounded question through compilation,
manual prompt review, execution, evidence review and bounded acceptance. Neither
checkout was integrated or modified by the inspection. Read it as a separate
case alongside the synthetic exercise above, not as another task to execute or
as permission to inspect or change your own project.

### Describe the question and bind its scope

The original feature was:

````gherkin
Feature: acquire the committed candidate and master integration facts
  ```text
  [G1] --> [W1] --> [T1]
  ```
  Scenario: inspect the exact committed integration operands
    Given [G1] the owner approved the bounded read-only reconnaissance
    When [W1] I inspect the committed candidate and current master integration facts
    Then [T1] the report cites evidence
````

The `Given` records a premise about approval; writing it does not create that
approval. The fenced `text` graph expresses the dependency from premise to
action to observable result. That fence was required by the supported source
representation. Omitting it can stop compilation before any native inspection;
such a compile failure says nothing about the underlying Git task's behavior.
This is one simple supported reader pattern, not full Gherkin or generic
orchestration.

The feature does not choose repository identity, permissions, worker, commands
or acceptance. Those details came from separately acquired bindings: records
connecting the task to its actual context and authority. These short excerpts
from the original binding file show the canonical repository and child scope:

```yaml
repositories:
  TOP26006_fw:
    repository_id: TOP26006_fw
    repository_class: COORDINATION_META_REPOSITORY
requested_effects: []
```

```yaml
prompt:
  prompt_mode: investigation_only
  branch_policy: read_only_current_branch
  allowed_to_modify: {}
  validation_ceiling: static_inspection_only
```

These are excerpts, not a complete reusable binding file. The candidate and
master were revisions in the same canonical repository, `TOP26006_fw`.
A local role such as “candidate checkout” does not create a second repository
identity. Use the typed identity from the maintained registry rather than
inventing one from a worktree's purpose.

The binding's evidence requirements also fixed where the result would return:

> Child authors the native report and material raw evidence only in its final
> response/tool-result channel.

The child therefore had no task-file write scope. One historical serialization
weakness needs to stay visible: `git_index_entries` described resolving the
native index paths through Git rather than embedding the resolved paths. The
child subsequently resolved and checked them. That bounded limitation belongs
to this historical record; it is not a binding template to copy.

### Review the prompt that will actually run

The first compilation prepared a prompt while manual review was still pending.
Its receipt recorded `dispatchable: false`, with the manual review as the only
unresolved evidence. This meant the prompt could not yet be issued for
execution; it did not mean that the task was semantically rejected or that the
owner had revoked approval.

The author inspected the generated prompt bytes against the task and current
master governance. After recording that review, the corresponding binding
changed from this prereview excerpt:

```yaml
binding_id: manual_review
acquisition: pending
```

to the final excerpt:

```yaml
binding_id: manual_review
acquisition: acquired
```

The complete final record cited the review artifact and exact prompt hash.
A second compilation then produced a prompt byte-for-byte identical to the
reviewed one and a receipt permitting entry to execution checks. The maintained
mechanical validator checked that exact final prompt: mechanical validity and
internal consistency were true, while governance completeness remained
`not_assessed`. Compilation and lint still did not prove execution or acceptance.

This two-compile sequence records how this case acquired its review. It is not
a universal ritual. The point is to preserve the connection between the governed
prompt, the bytes reviewed as required, the bytes actually dispatched and the
evidence later attributed to them. A changed prompt needs review of the change;
a familiar filename is not byte identity.

### Follow the evidence across responsibilities

One child assistant performed the native read-only Git inspection and returned
the report and raw command evidence through its response channel. The controller, the assistant directing the surrounding run,
captured that evidence and owned the separately authorized report and lifecycle
effects. In this qualification setup it also created and removed a temporary
compiler worktree, or carrier. A temporary worktree is not a prerequisite for
every read-only task, and a read-only child does not make the whole surrounding
workflow effect-free.

Review then compared the returned evidence with the claimed result. In this
historical case, the project owner held the bounded acceptance and later
integration decisions under the acquired project mandate. These were the
responsibility assignments for this case, not a universal taxonomy. The author's
pre-execution prompt review and the controller's capture were not independent
acceptance of the returned task.

To assess the result, connect each claim to its native observation: exact
commit identities, command operands, exit code, stdout and stderr. If execution
ends ambiguously, read back the owned evidence before considering a retry.
Repeating the task automatically can lose the distinction between the original
attempt and a later observation.

### Interpret one discriminating Git check

The direction of the ancestry query matters:

```text
git merge-base --is-ancestor <observed-master-oid> <candidate-oid>
```

The first operand is observed master; the second is the candidate. Exit `0`
means the first is an ancestor of the second. Exit `1` means it is not. Another
command error leaves an error to investigate; it does not establish divergence.
A valid negative result answers the inspection question and authorizes no
rebase, merge or repair.

For the historical operands, the recorded query returned exit `0`. A separate
`git rev-list --left-right --count <observed-master-oid>...<candidate-oid>`
observation returned the exclusive commit counts:

```text
master-only commits: 0
candidate-only commits: 18
```

These count commits present only on each side of that historical comparison.
They are not tests, percentages or commits created by this tutorial. The
returned committed-delta views (`git diff --name-status`, `--stat` and
`--summary`) identified what separated the revisions. Topology and a path
inventory do not by themselves establish semantic preservation.

### Keep the conclusion within the evidence

The bounded reader task succeeded and was later accepted at its bounded
ceiling after review. The observed local topology for those operands was
compatible with considering a later fast-forward-only integration, which would
advance master without a merge commit. No integration happened in this case.
The observations concern local refs, not remote freshness, and do not qualify
writer tasks, production, full Gherkin or arbitrary compiler workflows.

Technical execution, evidence review, bounded acceptance and authority to move
master remain distinct. Finalizing documentation on a candidate does not
activate the governance-workflow compiler on master. Any later integration
needs its own authorized action and actual readback. Use the same
[decision-layer distinction](../explanation/evidence_reproducibility_and_acceptance.md)
as in the synthetic review above when recording what has actually been accepted.

**Provenance note:** this is the retained real-use reader qualification
`TOP26006_LANE15_REAL_USE_GHERKIN_FF_RECONNAISSANCE_20261111_R3`, executed against
candidate `8b68fd9e4aa2b6028cd0367342bf16747a20b7c7` and observed local master
`3423f14e1fdbbdd24e034a8c265ea7c08175f448`. Its diagnostics retain `task.feature`,
`bindings_prereview.yml`, `bindings_final.yml`, both compilation receipts,
`author_review.yml`, the generated prompt and validator result, the child
response and original session stream, and the controller's lifecycle record.
The later tutorial handoff, section 10, records
`CLOSED_ACCEPTED_WITH_EXISTING_QUALIFICATIONS`; executor completion alone did
not establish that disposition. Those retained records support this account;
reading this tutorial does not independently reproduce their checks.

## Recommend, qualify, and leave a decision

Your review should contain the artifact path/hash, stage identities, executor claims, direct observations, blocking and nonblocking findings, checks not performed, recommendation, and researcher responsible for the decision. Mark independent checks of the underlying historical note, diff, and runtime receipt as **not performed**. Same-person teaching review is not independent replication.

For this documentary exercise, recommend that the initial note remain unaccepted until its provenance defect is repaired and checked. Report the scenario's repair and simulated acceptance as historical evidence, not your own verification of the repaired Git contents. A real reviewer would need the returned note, exact parent/result diff, input identities, command/output evidence, and actual decision by the person with acceptance remit for the stated layer and scope, separately from the reviewer recommendation, following the [decision-layer distinction](../explanation/evidence_reproducibility_and_acceptance.md) before granting a stronger conclusion. Do not invent missing evidence or silently perform a repair during review.

## Preserve the review and restart

Save your review with the scenario identity and the last completed review step. If interrupted, reopen that record and the scenario, compare hashes, and resume at the first unanswered field. Unchanged evidence does not require recreating the first note, repeating arithmetic, or appending provenance again. Changed or unavailable evidence reopens only the affected finding; preserve the earlier review rather than overwriting it.

You finish with either a qualified teaching recommendation or an unresolved evidence request, never automatic acceptance. Continue to [Tutorial 6](06_continue_from_existing_evidence.md) to prepare the next task from documented closure. For additional practice making a bounded change, revisit [Tutorial 4](04_make_a_bounded_analysis_change.md). Return to the [tutorial learning path](index.md) for the wider route.
