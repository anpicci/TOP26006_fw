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

## Recommend, qualify, and leave a decision

Your review should contain the artifact path/hash, stage identities, executor claims, direct observations, blocking and nonblocking findings, checks not performed, recommendation, and researcher responsible for the decision. Mark independent checks of the underlying historical note, diff, and runtime receipt as **not performed**. Same-person teaching review is not independent replication.

For this documentary exercise, recommend that the initial note remain unaccepted until its provenance defect is repaired and checked. Report the scenario's repair and simulated acceptance as historical evidence, not your own verification of the repaired Git contents. A real reviewer would need the returned note, exact parent/result diff, input identities, command/output evidence, and actual decision by the person with acceptance remit for the stated layer and scope, separately from the reviewer recommendation, following the [decision-layer distinction](../explanation/evidence_reproducibility_and_acceptance.md) before granting a stronger conclusion. Do not invent missing evidence or silently perform a repair during review.

## Preserve the review and restart

Save your review with the scenario identity and the last completed review step. If interrupted, reopen that record and the scenario, compare hashes, and resume at the first unanswered field. Unchanged evidence does not require recreating the first note, repeating arithmetic, or appending provenance again. Changed or unavailable evidence reopens only the affected finding; preserve the earlier review rather than overwriting it.

You finish with either a qualified teaching recommendation or an unresolved evidence request, never automatic acceptance. Continue to [Tutorial 6](06_continue_from_existing_evidence.md) to prepare the next task from documented closure. For additional practice making a bounded change, revisit [Tutorial 4](04_make_a_bounded_analysis_change.md). Return to the [tutorial learning path](index.md) for the wider route.
