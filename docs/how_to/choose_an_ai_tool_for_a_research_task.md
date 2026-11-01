# How to choose an AI tool for a research task

Choose from the work you need done and the evidence you need back. A difficult
scientific question may benefit from a short discussion; a simple setting may
require careful repository inspection. Duration, source access, permitted
actions, and the desired result matter more than a ranking of tools.

The [roles and authority guide](../explanation/roles_and_authority.md) introduces
the reference workflow and the human decisions at each handoff. Here we apply
it to concrete research situations. The examples are invented teaching cases,
not observations or instructions to execute a native analysis.

## A. I have a scientific question and want to clarify it

Start with Chat when you want to think through the question with an assistant.
For example, a histogram has unexpected binning. Supply the figure or a precise
description, what you expected, and what you already know about its origin.
Ask Chat to distinguish questions about the configured edges, the code that
uses them, and the scientific reason for choosing them.

Discussion can return hypotheses and a bounded next question: “Which of these
identified files defines the edges, and where are they used?” It cannot turn
an explanation into an observation about files it has not seen. Check that the
proposed question preserves your intent. Retain the useful framing and its
assumptions, not just the most confident answer.

If a supplied, identified excerpt already answers your question, read it and
judge the answer yourself. You can stop there. If source inspection is needed,
pass the bounded request and relevant files to Codex, as in case C. There is
no need to add Work simply to complete a sequence.

## B. I need a longer investigation or a finished report

Start with Work when the task requires sustained comparison of several sources
and an organized deliverable. Suppose two analysis notes and a review comment
seem to give different reasons for the histogram bins. Supply their versions,
the exact question, the permitted source set, and the intended reader of the
report. Ask for a comparison that separates agreement, disagreement, and
missing information.

The useful return is a source-linked account you can challenge. Check whether
the cited passages support each comparison and concern the same analysis
version. A missing note must remain a gap, not a reconstructed quotation. Work
cannot decide which prescription is scientifically correct or whether it was
implemented in a particular run. Retain source identities, supporting passages,
the comparison, and unresolved questions. Then decide whether a native-source
inspection or consultation with the scientific owner is needed.

Work is not automatically better because a task is important. If one passage
and a short exchange suffice, discussion may be enough. If repository state
is the central evidence, start with case C instead.

## C. I need to inspect or modify repository material

Start with Codex when the question depends on actual source, configuration,
entrypoints, or a reviewable technical change. First distinguish inspection
from modification. “Where is this setting read?” authorizes neither a repair
nor an analysis run.

To trace a configuration into a workflow, provide the repository and revision,
the configuration file, and the relevant entrypoint and source files. Ask for
a read-only trace of the setting from its definition to its consumer, including
any defaults, overrides, or conditional branches visible in those files. If
the trace leaves the allowed files, the assistant should identify the missing
link and stop that part of the claim.

Expect cited locations explaining the source/configuration/entrypoint
relationship. Inspect those locations, or ask a reviewer to challenge the
trace. A source path that can consume a setting does not establish that a
particular historical job used it; that needs the corresponding run records.
Keep the source revision, locations, trace, and limits. You can accept a bounded
source-level conclusion without qualifying the native analysis or executing it.

For a modification, first decide the intended change yourself. Give Codex the
exact files it may edit, the approved new behavior, and the allowed validation.
Request a diff and evidence tied to that change, including checks not performed.
The [bounded setting example](ask_an_assistant_to_prepare_a_task.md#example-change-one-documented-setting)
shows how. Codex cannot decide a new selection or method because it seems to
improve a plot. Review the returned change before deciding to use it.

## D. I need a challenge after work is returned

Start with a reviewer and the evidence, rather than another request to “make
it better.” For important scientific claims, involve someone with the relevant
domain knowledge. A colleague can review directly; a separately tasked AI can
help find omissions and counterexamples, with the limits described in
[roles and authority](../explanation/roles_and_authority.md#a-reviewer-challenges-the-returned-work).

Give the reviewer the original request, exact returned revision or diff,
supporting sources, relevant validation, and unresolved questions. Ask them to:

1. Inspect what changed and compare it with the intended task.
2. Check whether the evidence covers the changed behavior and stated limits.
3. Challenge claims that exceed those observations, including scientific ones.
4. Return specific findings and recommend acceptance, repair, or rejection.

For example, a check may prove that a plot-setting file parses while failing to
show which setting was used for the figure. Preserve that finding and decide
whether it blocks your intended use. A reassuring review or passing test does
not settle the scientific question. Keep the findings and their resolution,
then make the human acceptance decision explicitly. A separate reviewer is
not necessary for every small question, but your responsibility to check an
answer before relying on it remains; project requirements may demand more.

## E. I need durable source, history, and collaboration

Use Git to record source revisions and changes; use GitHub when shared hosting
and review are useful for your collaborators. Supply the precise change, its
purpose, and evidence links. Compare the actual diff with the intended request
and keep review comments associated with the revision they assess.

This gives you a record that another person can revisit. It does not turn the
repository host into scientific authority, and sharing or merging is a separate
decision from preparing a local change. Retain the commit identity and relevant
review record, then hand them to the people who must assess or use the result.
For a source-inspection task, citing the existing revision may be sufficient;
not every answer needs a new commit or a GitHub discussion.

## One complete handoff: understand the bins before changing a setting

Imagine you want to know why a histogram's bins differ from an earlier draft.
You have two notes and a small set of repository files, but no proof yet that
they produced the displayed figure. The following is a possible exchange, not
an instruction to run these tools in order.

**You → Chat:** explain the discrepancy and ask for a bounded question. Chat
helps separate “what does the current source specify?” from “why was that
choice made?” You read the draft request, remove any implied permission to
repair the analysis, and approve a source comparison.

**You → Work, if the source comparison needs it:** provide the identified notes
and review comment. Request a report linking each binning rationale to its
source. Check the return for unsupported agreement or missing versions. Suppose
the notes disagree: keep both accounts and ask the scientific owner to resolve
the prescription; the report itself cannot choose one.

**You → Codex, if repository evidence is needed:** pass the question, the
relevant parts of the report, and a read-only file scope. Ask where the current
configuration enters the plotting code. Check the returned locations and any
override it identifies. This can establish a source relationship while leaving
the origin of the historical figure open.

**You decide whether a change is warranted:** suppose you subsequently approve
one documented setting for a future plot. Give Codex a new, bounded modification
request with the exact value and allowed checks. Codex returns the diff and
validation evidence. Git can record the change, and GitHub can carry the review
if collaboration calls for it. None of these steps settles the scientific merit
of the chosen value.

**You → reviewer → you:** provide the original intent, exact change, source
trace, and validation. The reviewer checks for unintended edits and unsupported
claims. You resolve consequential objections and record acceptance or rejection
for the specified use, retaining the unresolved historical-figure question.

At every arrow, carry the question, source identities, allowed actions,
observations, and open uncertainties. Do not assume another interface has the
previous conversation or the same file access. Stop once you have sufficient
evidence for your decision: the initial question may need discussion and
inspection only, with no report, modification, or separate reviewer.

## Use the reference without depending on its interface

These choices apply OpenAI's current [Chat/Work/Codex descriptions](https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex)
and [Codex overview](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan),
checked on 2026-11-01. The scenarios are this manual's research guidance, not
claims that products automatically perform these handoffs. Check current
access and permissions for the task; no plan, model, menu, or rollout is a
permanent part of this method.

The durable choices concern discussion, substantial research, repository work,
source history, challenge, and human acceptance. They can overlap in a tool or
be performed by people. The [provider limits](../explanation/provider_independence_and_limits.md)
explain why transferring the method requires checking the other environment,
rather than assuming equivalent products.

Continue with [preparing a task request](ask_an_assistant_to_prepare_a_task.md).
