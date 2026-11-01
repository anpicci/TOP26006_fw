# AI-assisted research foundations

Imagine that a histogram in a draft looks different from the one you expected.
You remember one set of bin edges, but the figure shows another. You could ask
an AI assistant, “Why does this plot look wrong?” It might offer a sensible
explanation immediately. It might even name a configuration file. The useful
research question is more demanding: which inputs and settings produced this
particular figure, and what evidence would distinguish a mistake from an
intentional choice?

AI assistance can help you answer that question. It can read material you
provide, trace relationships between files, suggest explanations, compare
versions, and help prepare a small change. Its response becomes useful research
work when you can check what it relied on, what it actually did, and where its
conclusion stops. A convincing explanation by itself does not establish what
happened in your analysis.

This chapter develops that way of working. You need no special software or
knowledge of this project to read it. The examples are illustrative; filenames,
sample names, and quoted task requests below are invented teaching examples,
not instructions to run an analysis. We will follow a question through context,
evidence, a bounded task, verification, and a human decision.

## What assistance can contribute

A language model generates responses using patterns learned during training
and the information available in the current interaction. Those patterns can
support useful reasoning: explaining a difficult paragraph, comparing two
arguments, proposing a calculation, or identifying a likely inconsistency in
code. The model has not thereby observed your experiment or established that
its proposed explanation is true.

For example, you might provide two short descriptions of an event selection
and ask where they differ. An assistant can organize the comparison and point
out that one description includes a threshold absent from the other. That can
save careful reading time. Whether the threshold was applied to the actual
events still requires evidence from the relevant configuration, code, and
recorded processing. The comparison generates a useful lead; it does not
settle the history of the data.

Some AI systems also have tools. A tool can read a file, search a collection of
documents, or carry out a calculation when that action is available and
permitted. The assistant may use the returned information to revise its answer.
This extends what it can do beyond composing text. It also introduces separate
questions: did it read the intended file, did the calculation use the intended
inputs, and did the result answer the research question?

Good uses often involve work with a visible end point: extracting assumptions
from a paper you supplied, locating where a value is defined, drafting an
explanation for review, or checking whether a small change matches a stated
requirement. Exploratory uses are valuable too. Asking for possible reasons
for an unexpected distribution can broaden an investigation, provided you keep
those possibilities separate from established findings.

Output quality depends on the question, relevant context, quality of evidence,
and tools actually available. A clearer request can improve the work, but no
wording guarantees correctness. Assistance extends your working process. It
does not transfer scientific responsibility to the system.

## Why an answer can be convincing and wrong

Fluent language is a poor test of reliability. A model can generate a smooth
explanation for a fact that is false, complete an unfamiliar citation with
plausible details, or resolve an ambiguous question by silently assuming one
meaning. Its tone can sound equally assured when it has strong evidence and
when it has guessed. Confidence in the wording is not evidence for the claim.

Suppose you ask which paper introduced a correction method. The response names
credible authors, a journal, and a year, but the paper does not exist. Or the
paper exists but discusses a different method. Both errors matter: a fabricated
citation wastes time, while a real but irrelevant citation can give an
unsupported statement the appearance of scholarly support. You need to open
the source and inspect the relevant passage.

A numerical answer can fail in a less visible way. An assistant might make an
arithmetic error while combining measurements. It might instead compute a
weighted mean correctly while treating correlated uncertainties as independent.
The latter answer can be perfectly reproducible and still unsuitable for your
question. Arithmetic, assumptions, and scientific applicability need different
checks.

File interpretation creates another family of errors. An assistant may read a
sample label in a configuration and assume that it determines the processed
events, missing a later override. It may confuse similarly named files, report
an old default from remembered documentation, or read a commented example as
an active setting. All can produce a coherent account of a process that never
ran.

Missing context can also change the question being answered. “Why did the yield
increase?” could refer to more input events, a change in selection efficiency,
or a change in normalization. A correct explanation of one possibility is not
an answer about your particular yield. An overly simple explanation may erase
the very distinction your research depends on.

These are general reliability concerns, not limitations unique to one
provider. For example, OpenAI's [guidance on ChatGPT's reliability](https://help.openai.com/en/articles/8313428-does-chatgpt-tell-the-truth)
warns that answers can be inaccurate or misleading, including when expressed
confidently, and advises checking important information against reliable
sources. The practical lesson is to judge an answer by its support and the
consequences of being wrong, rather than by how polished it sounds.

## What the assistant has actually seen

A model's learned knowledge and the current state of your project are different
sources of information. Familiarity with a common library does not reveal which
version you installed. Familiarity with typical analysis layouts does not reveal
the contents of your repository, meaning the collection of project files and
their recorded versions. Even a previously accurate account may describe an
older revision.

If you paste a configuration into a conversation, the assistant can discuss
that text. It has not automatically inspected the files that configuration
imports. If a file-reading tool is available, it may be able to inspect those
files, but the tool might be restricted to a particular directory or checkout.
A search tool might return only some documents. Tool availability does not
establish access to every relevant source, and access does not establish that
a source was actually read.

In the histogram example, a useful starting description identifies the figure,
the project copy and revision, the likely plotting entry point, and the files
you believe define the bins. An entry point is the script or function through
which the task starts. A revision identifies a recorded version of the project.
Together these details help distinguish “this setting exists somewhere” from
“this setting belongs to the path that could have produced this figure.”

Ask the assistant to say which sources it inspected and which it could not
access. If it only has a pasted excerpt, its conclusion should be limited to
that excerpt. When evidence is missing, a useful response can identify the
next file or record needed; it need not manufacture a complete answer.

Context should be relevant and explicit. Include important units, definitions,
data versions, and assumptions. Explain whether a number is an observed count,
a simulated prediction, or a normalized estimate. A large pile of unrelated
files can obscure these distinctions. More text is not automatically better
context, and a longer prompt is not automatically a better task request.

Choose what to share as carefully as you would with any external service or
collaborator. Check the rules that apply to unpublished results, personal data,
and restricted material before providing them. A small permitted excerpt or
synthetic example may be sufficient to explain a problem. The assistant's
ability to receive material does not decide whether you may share it.

## From a claim to evidence and a decision

Consider the statement, “This configuration selects sample X.” That is a
**claim**: something that could be true or false. A configuration file at a
specified revision is a **source** you can inspect. Finding the exact line
`sample = "X"` is an **observation** about that source. These are related, but
they are not interchangeable.

The line alone might not establish the claim. It could be unused, overridden,
or interpreted differently by the code that reads it. You would also want the
exact entry point, the relevant configuration-reading logic, and the source
version. If the question concerns an actual run, a recorded output or parser
trace can help establish which value was used, provided it can be tied to the
same inputs and version. Static reading supports a claim about the inspected
code; it does not by itself prove what an earlier run did.

An assistant might then explain, “The entry point reads this file, the parser
assigns this value, and the recorded selection reports X.” That explanation is
an **interpretation** of the evidence. Check each connection. A record from a
different run would break the connection even if all the quoted text were real.
A generated explanation is verified only to the extent that its important
steps withstand those checks.

A **calculation** derives a quantity from inputs using a method. Counting the
selected events, for example, can add evidence about the result. It needs its
own input identity and method, and it cannot replace missing evidence about
which sample was selected. A correct count of the wrong sample does not answer
the original question.

Finally, you make a **decision** about sufficiency. For a note explaining a
configuration option, exact source reading might be enough. For a claim about
a published plot, you may also need processing records and a connection to the
plot's input. The required evidence depends on the claim and its consequences.
The assistant can explain these limits; the researcher decides whether the
support is adequate for the intended use.

Keeping a source, its version, the observation, and the method alongside the
result preserves **provenance**: the record of where a result came from. It lets
a colleague inspect the argument without relying on your memory or trusting
the assistant's summary. This is why checkable research work returns evidence
and limitations along with a conclusion.

## A research interaction from beginning to end

The following loop can fit in a short conversation or span several carefully
bounded tasks. It is a way of thinking about work, not a demand for formal
paperwork at every step. Scale the record and review to the importance of the
result.

### Formulate the question and define a useful answer

Start with the uncertainty you need to resolve. In our example, “Why are these
histogram bins different?” becomes “Which bin edges produced this figure, and
where were they specified?” This wording separates a question about provenance
from the later question of whether the binning is scientifically appropriate.
That separation prevents an investigation from quietly becoming a redesign.

Next decide what an answer must establish. Here, a useful answer would identify
the relevant source version, the configuration or code defining the edges, and
the connection to the figure. It would say whether those facts were observed
or only inferred. If the connection to the figure cannot be established, a
partial answer should expose that gap rather than claim the mystery is solved.
This step gives you a way to evaluate the response before seeing its conclusion.

### Identify evidence and provide the necessary context

Gather the sources likely to resolve the question: the figure's provenance
record, the plotting entry point, and the configuration. You need not know the
answer before asking for help. If you do not know which files matter, make the
first task a bounded search for candidates and ask why each candidate is
relevant. Searching for evidence and interpreting it can be separate tasks.

Then explain the context the files cannot supply on their own. State which
figure you mean, what you expected, and whether the goal is historical
explanation or preparation for a future change. Mark uncertain recollections
as uncertain. “I think the older plot used equal-width bins” is a lead to
investigate, not a fact the assistant should adopt without checking.

### Ask for a bounded task and inspect the result

Give the assistant a task with an observable finish. For example: inspect three
named files, trace the bin definition, make no changes, and return the exact
source passages with an explanation and unresolved questions. State whether
execution is allowed. Reading code and running it produce different evidence
and can have different costs or effects.

When the answer arrives, inspect whether the requested work was actually done.
Does it name files that exist? Are the quotations accurate? Does it distinguish
what the source contains from what might have happened at runtime? A neat
report can still omit the central connection. Check the result against the
useful-answer criteria you set, rather than accepting its completion statement
as proof.

### Challenge the claims and record what supports them

Focus your challenge on the claims that matter most. Ask what would make the
explanation false: could another configuration override the bins, or could the
figure come from a different revision? Request the evidence needed to resolve
those alternatives. Asking the same assistant “Are you sure?” may produce a
more emphatic version of the same mistake. A source check, an independent
calculation, or another person's review can add genuinely different evidence.

Preserve the useful result so the next person can check it. For this example,
record the question, file paths and revision, relevant source lines, any
execution that actually occurred, and the unresolved connection to the figure.
Line numbers are convenient locators but may move; keep the revision and enough
context to identify the passage. A short note with these details can be more
useful than a long transcript with no clear conclusion.

### Decide what is accepted and whether to continue

You might accept that the current code defines particular bin edges while
leaving the history of the old figure unresolved. State that distinction.
Acceptance can be narrow: evidence sufficient for one claim need not support a
stronger one. Important scientific interpretations may require a colleague's
domain review before you use them in an analysis or publication.

Now choose the next step. If a missing record is available, inspect it. If a
bounded correction is justified, specify that correction as a new task. If the
next step would require choosing a scientific method, stop for that decision.
If the available evidence cannot resolve the question, record the limit. More
AI responses will not substitute for a missing observation.

## Asking for useful work

A useful request explains the goal, context, permitted actions, and the form of
evidence you need. It also makes room for uncertainty. You are describing work
to a collaborator whose knowledge of your situation is incomplete. You are not
trying to discover a perfect phrase that forces a correct answer.

Compare these requests about the histogram:

> “Look at this repo and fix the analysis.”

> “I need to understand why histogram X has these bins. In the project revision
> identified in my note, inspect only `plot_x.py`, `binning.yml`, and
> `figure_record.txt`. Do not modify files or run the analysis. Show the exact
> evidence for the bin edges and their connection to the figure. Separate
> observations from interpretation. If another file is needed, identify it and
> explain why before expanding the task.”

The first request leaves both the problem and a successful repair undefined.
The second defines an investigation you can review. Its filenames would need
to be replaced with real, verified paths before use. The boundary is useful
because you can see what was checked and notice what remains outside it.

For literature work, compare:

> “Tell me the accepted explanation for this effect.”

> “Using these three papers, summarize the explanations they actually discuss.
> Cite the sections supporting each important claim, distinguish evidence from
> speculation, and identify disagreements and missing information. Do not infer
> field-wide consensus from this small collection.”

Here, the scope limits the conclusion as well as the reading. Ask for a short
research outline first when a topic is broad: which subquestions matter, which
sources could answer them, and how their quality will be assessed? An outline
helps you correct the direction before investing effort in a long synthesis.
Citations for key claims and a section on what is missing make the synthesis
easier to challenge; they still need checking.

For numerical work, compare:

> “Calculate the best value and tell me whether the measurements agree.”

> “Using the supplied measurements, units, and uncertainty assumptions, explain
> the proposed combination method before calculating. Identify any missing
> information about correlations. If the method is appropriate and calculation
> is permitted, return the inputs, method, result, and a practical cross-check.
> Leave the scientific interpretation of agreement for review.”

The improved request prevents a missing assumption from being hidden inside a
number. It also gives you a chance to reject an unsuitable method before the
calculation. A request to explain a method is not automatically permission to
run a costly workflow.

Modification needs an equally clear boundary. Compare:

> “Clean up the plotting code while you are there.”

> “The axis label in `plot_x.py` omits the unit. Change only the label from
> `Energy` to `Energy [GeV]`, using the unit documented in the supplied data
> description. Preserve the data, bin edges, and numerical operations. Show the
> exact diff and how you checked that only the label changed. Do not run the
> analysis. If the documented unit conflicts with the code, report the conflict
> before editing.”

This is a teaching example of a bounded modification, not a request to perform
one here. A **diff** is the comparison showing what changed between versions.
It helps you review the edit directly. Notice that the assistant is asked to
surface a contradiction rather than silently choose a unit.

After the first response, refine the task using what you learned. You might
correct a mistaken assumption, supply a missing source, or narrow a question
that proved too broad. OpenAI's [prompting guidance](https://help.openai.com/en/articles/10032626-prompt-engineering-best-practices-for-chatgpt)
supports clear requests, relevant context, and iterative refinement. Research workflows can also benefit from planning the research,
supporting important claims with evidence, checking source quality, and
identifying gaps. These are useful general practices, not rules tied to a particular
interface or guarantees of a reliable answer.

## Verification that matches the claim

For a factual claim, inspect a source capable of establishing the fact. A
secondary summary can help you find an original measurement or publication,
but may omit qualifications. Check dates, definitions, and the population or
conditions to which a statement applies. If a fact could have changed, old
training knowledge or an old summary is insufficient evidence of its current
state.

For a citation, verify both identity and support. Does the source exist with
the stated authors and title? Does the cited passage actually support the
claim, with the same qualifications? A valid link can point to an irrelevant
page. A quotation can be accurate while its interpretation is wrong. The fact
that a model supplied a citation is not itself verification.

For a code claim, inspect the exact source and the path through which it is
used. A function definition may never be called by the entry point you care
about. Relevant tests or recorded behavior can strengthen the claim, but check
what they cover. A test of one input does not establish correctness for every
case, and passing a test does not establish scientific suitability.

For a numerical claim, check inputs, units, formula, and assumptions. Reproduce
the calculation or calculate it independently when practical. A simple limiting
case, an order-of-magnitude check, or a trusted reference value can expose a
problem quickly. Repeating the same code with the same wrong assumptions may
reproduce the error; choose a check that could reveal the suspected failure.

For a repository claim, identify the project copy, revision, exact path, and
actual content. A repository may contain several scripts with similar names.
Uncommitted local changes can also make the current file differ from the
recorded revision. If those differences matter, preserve a description of them
with the evidence. A remembered layout or branch name cannot establish current
content.

For a scientific interpretation, ask whether the method's assumptions fit the
measurement or simulation, whether uncertainties are treated appropriately,
and whether alternative explanations remain. This is where domain judgment is
essential. A successful tool call establishes only what its observed result
supports. A command finishing without an error is not scientific validation.

Verification should be proportionate. You need not manually reproduce every
sentence in a rough brainstorming note or rerun an expensive analysis to check
a label change. Concentrate on claims that affect the decision and reuse sound
evidence when its inputs and assumptions still apply. For consequential
results, independent review can catch assumptions you and the assistant share.
Ask the reviewer to examine the evidence and possible counterexamples, not
merely whether the explanation sounds reasonable.

## Recognizing failure in an ordinary research interaction

The following situations show how useful work can go off course. Each begins
with a plausible response. The remedy is to expose the missing evidence or
choice and give the next task a clearer boundary.

### A path was invented

The assistant says the bins are defined in `config/histograms.yml`, but that
path does not exist in the project copy under discussion. The name may fit a
common layout, which makes the claim easy to overlook. Following it can send
you searching for a nonexistent source or lead to an unnecessary new file.
Check the exact path in the identified checkout. Ask next: “Which observed
file supports that path? If you inferred it, say so. Locate candidate bin
definitions within the agreed search area without creating anything.”

### A branch was invented

The assistant recommends a fix supposedly already on `analysis_update`. A
branch is a named line of work in a version-controlled project; its name alone
does not prove that it exists or contains a particular change. An invented
branch can make you believe evidence or a repair is available when it is not.
Check the relevant branch listing and the commit containing the claimed change.
Ask: “Show the observed branch and commit evidence. Distinguish what you checked
locally from any remote state you have not inspected.” Do not create the branch
merely to make the earlier answer appear consistent.

### Documentation describes an older behavior

A guide says a default threshold is 20, while the current configuration uses
25. The assistant repeats the guide and treats the code as wrong. The guide
may be stale, or the configuration may be an intentional exception; neither
should win solely because it looks more authoritative. Compare versions and
inspect the relevant source and change history. Ask: “Identify the discrepancy,
the versions involved, and evidence for the intended behavior. Do not change
either value until that intent is established.”

### A similar filename hides the wrong file

The answer quotes `plots/config.yml`, but the figure uses `validation/config.yml`.
Both contain plausible bin settings. The quoted text is real, so a superficial
citation check passes, yet the explanation concerns the wrong process. Trace
the file from the entry point or the figure's provenance record instead of
matching only the basename. Ask: “Show how this exact path is selected by the
entry point for this figure. If that connection is missing, limit the claim to
what the file contains.”

### The arithmetic is right under the wrong assumptions

An assistant combines measurements using independent uncertainties even though
they share a calibration uncertainty. The formula and arithmetic can both be
correct under independence, while the reported combined uncertainty is
inappropriate for the data. Inspect the stated uncertainty model and ask which
terms are shared. Ask: “List the assumptions used and identify what correlation
information is missing. Do not silently set unknown correlations to zero.” The
researcher must establish an appropriate model before accepting a new result.

### A successful command becomes a validation claim

A plotting script exits successfully and creates an image. The assistant says
the analysis is validated. The command may have plotted the wrong sample,
ignored an empty category, or used a stale input. Finishing proves much less
than the report suggests. Inspect the recorded inputs, relevant output
properties, and checks actually performed. Ask: “Separate command completion,
output checks, and scientific conclusions. What evidence supports each, and
what remains unchecked?” A generated image is an output to inspect, not an
automatic validation certificate.

### The requested method changes silently

You ask for a comparison using a fixed selection. The assistant removes an
awkward category or changes the fitting method to obtain a cleaner result.
The new method may be defensible, but it answers a different question and can
hide the difficulty you wanted to study. Compare the reported procedure and
diff with the requested method. Ask: “Identify every methodological departure
and its consequences. Preserve the original evidence and present alternatives
for human review before making further changes.”

### A local repair grows into a redesign

A request to correct an axis label produces a new plotting abstraction and
changes several configuration files. The assistant may be trying to improve
the project, but the larger edit is harder to review and may affect unrelated
figures. Inspect the changed path list and the complete diff against the
request. Ask: “Stop expanding the change. Explain which edits are needed for
the label correction and which are optional proposals.” Decide separately how
to handle the extra edits; do not discard work blindly, especially where other
people's changes may be present.

### Expensive work is repeated without a reason

A continuation begins by rerunning a large simulation even though a relevant
result and its provenance are already available. This can waste resources,
create confusing duplicate outputs, or overwrite useful evidence. Before any
new run, compare the existing result's inputs, version, method, and limitations
with the current question. Ask: “Which earlier evidence remains applicable,
what changed, and what smallest additional check would resolve the gap?” A
rerun can be necessary when inputs change or evidence is unreliable; it should
answer a specific unresolved need.

### A previous summary overrides current source

An old conversation summary says a correction is enabled. The current
configuration disables it, but the assistant keeps citing the summary. A
summary is convenient context and may accurately describe an earlier state;
it cannot establish a later one. Compare the summary's date and revision with
the source relevant to the question. Ask: “Resolve this discrepancy using the
identified source version. State whether the summary was historical, mistaken,
or about a different configuration, and update only the supported conclusion.”

### An inaccessible source is treated as read

The assistant cannot open a paper or file but still describes its contents as
if inspected. A plausible reconstruction can be especially misleading when the
source is familiar by title. Check the access result and request the passage
supporting the claim. Ask: “Which material did you actually see? Separate any
secondary account from direct inspection and state what cannot be concluded.”
You may provide an authorized excerpt or choose another source; missing access
is a reason to narrow the answer, not to guess.

### A scientific decision is handed to the assistant

You ask which events to exclude and the assistant chooses a cut because it
improves an apparent signal. That choice may introduce bias or conflict with
the measurement's design. The danger is not just a wrong number: the purpose
and method of the study have changed. Examine the justification and whether
the choice uses information that should not drive the selection. Ask: “Lay out
the alternatives, assumptions, possible biases, and evidence needed to compare
them. Leave the selection decision to the responsible researchers.” Assistance
can clarify a scientific choice without making it on your behalf.

## Continuing with people and tools

Different AI interfaces are useful for different kinds of work. The next
lesson will make this workflow concrete by showing which people and tools
perform each part in the reference setup. For now, the existing [guide to
people and AI tools](../how_to/choose_an_ai_tool_for_a_research_task.md) provides
a short orientation; you do not need its operational detail to understand this
chapter.

When you want to connect these ideas to a small example, read the [synthetic
repeated-measurements case](../../examples/repeated_measurements/README.md).
The existing [first read-only task](../tutorials/03_complete_a_first_read_only_task.md)
is the hands-on route when you are ready for its local setup. The [research
workflow](../explanation/research_workflow.md) offers a brief recap, and
[Getting started](../getting_started.md) keeps the reading and setup routes
together.

## The research decision remains human

AI can help investigate a question, carry out bounded work when permitted, and
review an argument or result. Those contributions can save time and make
assumptions easier to see. They are most useful when the result carries enough
evidence for someone to challenge it. Neither a confident answer, a successful
tool action, nor another AI's agreement confers scientific authority.

As the researcher, you decide what question matters, whether the assumptions
fit the study, how much evidence is sufficient, and what the result means.
For important claims, that responsibility includes obtaining appropriate domain
review and respecting the decisions of the people responsible for the research.
You may accept a narrow finding, request another check, or stop because the
necessary evidence is unavailable. A useful AI interaction leaves you better
able to make that decision, with its reasons and limitations visible.
