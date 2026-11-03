# How to ask an assistant to prepare a research task

A useful request tells the assistant what you are trying to learn, what it may
do, and what you will need to judge the result. This prevents a request for
understanding from becoming an unplanned repair. You can draft the request
yourself or ask Chat to help; read the proposed task before sending it onward.
Preparation is not permission to execute it.

The [tool-choice guide](choose_an_ai_tool_for_a_research_task.md) helps you choose
the recipient. Here, filenames, values, and task quotations are invented
teaching examples. They describe how to bound a request, not files inspected
or changes authorized in an existing analysis.

## Start with the decision the answer will help you make

Suppose you want to understand a histogram's binning before discussing a
possible change. Tell the assistant that purpose. A trace of where edges are
defined might answer the immediate question; choosing scientifically suitable
edges is a different task for the responsible researchers.

Ask for help finding the smallest useful investigation. If you do not know
which files matter, request a bounded discovery step within a named directory
and have the assistant propose the files to inspect. Do not invent file paths
or let “find the source” expand into unrestricted editing or execution.

## A vague request and a usable replacement

This request leaves both the problem and the permission unclear:

> Look at the repository and fix the analysis.

“Fix” assumes an error has been established. “The analysis” could include
source, settings, outputs, and scientific choices. Nothing tells you how to
judge whether the assistant changed the right thing.

A more useful request is:

> I need to understand why histogram X has this binning before I discuss a
> possible change with the analysis scientific lead. In the repository revision I have
> supplied, inspect only `plot_config.yaml`, `make_histogram.py`, and
> `plotting_notes.md`. Do not modify anything, run code or tests, access the
> network, or start jobs. Identify where the bin edges are defined, how the
> source uses them, and whether the note explains their rationale. Show the
> exact file locations and relevant passages you relied on. Distinguish
> observation from interpretation and tell me what remains uncertain. Return a
> short explanation and a source-to-claim list. If an answer requires another
> file, identify the missing evidence and stop that claim. I will judge the
> result by whether I can follow each claim to the supplied source. This task
> should not decide whether the binning is scientifically correct or claim
> that these files produced a historical figure without its run records.

Before using such a request, replace the illustrative names with sources you
actually have and identify their revision. Provide the relevant context and
files through an access route you are authorized to use. A pasted path does
not give the assistant access to its contents.

## Why each part of the request matters

**Goal and context.** Say what you want to understand and why. Mention the
observation that prompted the task, prior decisions, and relevant uncertainty.
This lets the assistant distinguish a request for explanation from a request
to alter the study. If it restates a different goal, correct that before work
begins.

**Relevant sources and files.** Identify the repository or documents, versions,
and allowed inspection area. Say which source owns the scientific explanation.
This makes the return traceable and reduces the risk of treating an old summary
as current evidence. If a source is inaccessible, the answer must disclose that
limit. An assistant should not present remembered content as an inspected file.

**Inspect or modify.** State the difference directly. A read-only task returns
observations. A modification task needs an approved change and exact writable
files. File access, a powerful model, or a suggested fix grants no permission
to change your project.

**Allowed and forbidden actions.** Explain whether the task may run anything,
use external sources, write outputs, change files, or share results. Choose
limits appropriate to the question; the inspection example needs none of those
extra actions. If a check outside those limits would help, ask the assistant
to identify it for a later decision, not carry it out automatically.

**Desired evidence and uncertainties.** Ask for source locations, input
identities, a diff for edits, and the results of any allowed checks. Require a
separation between observations and interpretations, with missing evidence and
conflicting sources left visible. “Tests passed” is incomplete without knowing
which tests, against what inputs, and which claim they address.

**Expected output and your judgment.** Choose a form you can review: a short
trace, a comparison, or a diff with its evidence. Say how you will assess it.
For the histogram, you want to follow the edges from the definition into the
consumer and distinguish the implementation from its documented rationale.
A long report is not a substitute for those links.

These are useful questions to settle, not words that make a prompt correct.
A small task can state them in a few sentences. Project-specific execution
rules may require additional detail; an assistant preparing a task should apply
the current rules without making you learn their terminology first.

## Review the prepared request, then the returned evidence

Before starting, read the assistant's draft as an instruction someone could
actually follow. Check the repository, files, question, permitted actions, and
stopping point. Replace guessed values and resolve any question that would
change the scientific intent. During the work, a missing file or unexpected
relationship may require your decision about a separately bounded follow-up.

Afterward, follow the evidence rather than accepting the summary alone.
A useful return might say: “This definition supplies the edges to this function;
the note describes a rationale, but the supplied files do not identify the run
that produced figure X.” The first two statements need source locations. The
last marks the limit of the inspection. Decide whether that is sufficient for
your immediate purpose, or whether you need the missing run record. Do not
silently upgrade it to an explanation of the historical figure.

For a configuration trace, use the same habit: ask where the value is defined,
loaded by the entrypoint, possibly overridden, and consumed. A reviewer can
challenge a missing connection. Reading that chain supports a source-level
account; it does not qualify an analysis workflow or prove a job ran with it.
The native repository's documentation and scientific owners remain the source
of domain-specific authority.

## Example: change one documented setting

Suppose the responsible researcher has decided that the next illustrative plot
should use 24 bins instead of 20. The task is to implement that decision, not
to ask the assistant which binning is scientifically preferable. A bounded
modification request could say:

> I have approved changing `plot_bins` from 20 to 24 for this teaching plot.
> In the identified repository revision, change only that setting in
> `plot_config.yaml` and its matching description in `plotting_notes.md`.
> First inspect those two files and `make_histogram.py` to confirm the meaning
> of the setting. Do not edit the source file, selection, data, or any other
> setting. Stop if the current value or meaning differs from this description,
> or if another edit is necessary. Return the exact diff and source locations
> showing where the setting is consumed. Validation is limited to reading the
> changed text, checking the matching descriptions, and inspecting the diff;
> do not execute code, tests, notebooks, or jobs, or access the network. Do not
> commit, publish, or merge. State that the plot was not regenerated and runtime
> behavior was not tested. I will review whether the diff implements exactly
> the approved change and ask a separate reviewer to challenge the evidence
> before deciding whether to accept it for the next step.

This example explicitly leaves commit preparation for later; a real project
may require committing authorized changes before the task can finish, so settle
that choice under its rules before execution. A request alone does not override
project requirements. No modification is performed by reading this page.

During the task, a different current value is a reason to return to the human,
not to overwrite it. On return, inspect both changed lines and any surrounding
context needed to understand them. Ask the reviewer whether the evidence covers
the setting's meaning and whether unrelated changes slipped in. With only the
stated static checks, you might accept the edit as prepared while withholding
any claim about the generated plot. Running or using it requires the next
appropriate decision and evidence.

## Keep a small, usable handoff

Retain the final request, source versions, returned work, relevant validation,
open questions, and review findings with your acceptance decision. Give the
next participant these concrete materials; do not rely on shared conversation
memory or on the word “done.” Reuse evidence while its sources and assumptions
remain applicable. You do not need to reproduce every action manually or create
a formal process for every conversation.

For the people behind these decisions, return to
[roles and authority](../explanation/roles_and_authority.md). The next lesson
will use this reference workflow to complete one bounded research task from
question to evidence. The existing [first read-only task](../tutorials/03_complete_a_first_read_only_task.md)
is the hands-on route; its execution sequence and notebook are outside this
preparation lesson.
