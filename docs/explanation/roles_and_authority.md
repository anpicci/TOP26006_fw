# Roles and authority

A researcher notices unexpected histogram bins. An assistant can suggest a
cause, inspect a setting, or prepare a change. Someone still has to decide
which question matters, whether the inspected material describes that figure,
and whether changing the bins would be scientifically justified. Those are
human responsibilities throughout the work, not a final approval click.

This page makes the [research workflow](research_workflow.md) concrete using
ChatGPT Chat, ChatGPT Work, Codex, and Git/GitHub. It follows the
[AI-assisted research foundations](../foundations/ai_assisted_research.md):
generated output needs support before you rely on it. The examples below are
illustrative, not findings about an existing analysis.

## Separate the research responsibilities

These are reader-facing responsibilities, not new normative governance roles.
Actual authority comes from live project governance and explicit decisions.

| Role | Responsibility and boundary |
|---|---|
| Research lead | Sets research/task priorities and authorizes bounded tasks and effects within the person's actual authority. This role is not by definition the task/evidence or scientific acceptor. |
| Research coordinator | Coordinates a bounded task/evidence layer and records its acceptance after the required review for the stated scope. This does not authorize new effects, choose scientific method or interpretation, or confer scientific acceptance. |
| Scientific lead | Decides scientific method and interpretation within actual authority and records scientific acceptance for scientific claims. Task/evidence acceptance does not confer this decision. |
| Responsible researcher | Takes responsibility for or performs a concrete bounded research task or workstream; is not automatically its coordinator, reviewer, research lead or scientific lead. |
| Reviewer | Independently challenges the relevant evidence and recommends a disposition; does not self-create task/evidence or scientific acceptance. |
| Executor | Performs the authorized work and returns actions, results and limits; completion does not accept its own result. A validator's PASS is likewise evidence, not acceptance. |
| Repository or technical maintainer | Maintains the repository or tooling within a bounded technical remit; gains no scientific authority from this role. |
| Designated integrator | Reconciles agreed contributions within an authorized integration scope; gains no scientific authority from this role. |

One person may hold several roles in a small project. State the responsibilities
separately, then record which roles that person holds and which decision they
are making. A research lead may authorize work while a different coordinator
accepts its evidence and a different scientific lead judges its scientific use.

## One reference workflow, with a human at each handoff

A substantial task might follow this path:

```text
Human researcher sets the question and limits
  → Chat helps frame a bounded request
  → Work prepares a substantial source-based investigation, when useful
  → Codex inspects or changes repository material, when needed
  → Git records the change; GitHub can support collaboration
  → a reviewer challenges the returned work
  → the research coordinator records bounded task/evidence acceptance or requests repair
  → the scientific lead separately decides scientific acceptance when needed
```

The arrows are handoffs of a question, sources, and evidence. They do not imply
automatic transfer between products or permission to start the next activity.
You check the returned work and supply the next participant with the relevant
material. A small question may end after discussion and your own source check.
Not every task needs Work, Codex, GitHub, or a separate reviewer; follow any
review requirements that apply to your project and the consequence of the claim.

| Person or tool | Concrete contribution | What you look for afterward |
|---|---|---|
| Human researcher | Defines the question, assumptions, limits, and standard of evidence | A question whose answer would inform a stated decision |
| ChatGPT Chat | Helps discuss the problem and draft a bounded request | A useful question, with guesses separated from observations |
| ChatGPT Work | Helps organize a longer investigation and its deliverable | A report whose claims can be checked against identified sources |
| Codex | Handles authorized repository inspection or technical changes | Exact files, a diff when changed, and relevant validation evidence |
| Git / GitHub | Records versions and supports review of changes | An identifiable revision and a discussion attached to the actual change |
| Reviewer | Challenges the work against the original request | Findings supported by evidence, including unresolved objections |
| Research coordinator | Judges the bounded task/evidence layer after required review | An explicit task/evidence decision with its scope and remaining limits |
| Scientific lead | Judges scientific method, interpretation and use | A separate scientific acceptance decision where needed |

The product descriptions are a dated reference: OpenAI describes distinct
uses for [Chat, Work, and Codex](https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex).
Checked on 2026-11-01. Availability and permitted access depend on the current
product and workspace; these names do not define project permissions.

## The researcher defines the question and stays involved

Before asking an assistant to work, explain what you are trying to learn and
what would count as an adequate answer. For the histogram, you might ask where
the current bin edges come from before deciding whether they should change.
Supply the figure's identity, the relevant source revision if known, and the
files or records you believe matter. Say which parts remain uncertain.

During the investigation, resolve questions about intent and stop a proposed
expansion if it would change the research problem. Afterward, compare the
answer with your original question. A discovered setting may explain a code
path without proving that it produced the figure you have. You decide whether
to accept that narrower finding, obtain missing provenance, or ask a new
question. The assistant must not choose a scientific method or selection on
your behalf.

## Chat helps turn uncertainty into a question

Use Chat as a discussion partner when you need to separate possible causes,
explain a passage, or prepare a manageable task. Give it the observation and
relevant context: “These bins differ from the earlier draft. Help me identify
what to inspect before considering a change.” Challenge assumptions during the
conversation, especially any suggestion that a plausible cause is established.

What comes back might be a list of hypotheses and a draft inspection request.
Check that the request asks for evidence you can actually obtain. Chat has not
inspected your repository merely because it names a likely file. Accept the
useful framing, revise it, then decide whether an inspection is needed.

For continuing discussions, [Projects in ChatGPT](https://help.openai.com/en/articles/10169521-projects-in-chatgpt)
can group conversations, files, and instructions (checked on 2026-11-01).
Keep a short record of your decisions and source versions there if useful.
Conversation continuity does not guarantee that an old attachment or summary
matches today's source; provide the relevant revision again at a handoff.

## Work helps assemble a substantial investigation

Choose Work when the useful result is an organized investigation across several
sources or a finished report. For example, ask it to compare the documented
binning rationale in two supplied notes with an earlier review comment. Give
the exact source set, question, exclusions, and desired form of the report.
Ask it to flag inaccessible sources and disagreements instead of filling gaps.

While it works, check whether the proposed comparisons address your question.
On return, follow the passages supporting the consequential claims. A polished
report or a citation alone does not verify them. Work can help expose a
contradiction; it cannot decide which scientific prescription your analysis
should adopt. You decide whether the report is sufficient or whether a
repository inspection or domain expert is needed next.

## Codex handles work tied to a repository

Codex is useful when an answer depends on specific files and their relationships,
or when you have decided on a bounded technical change. Its documented role is
coding assistance, including review; see [Using Codex with your ChatGPT plan](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan)
(checked on 2026-11-01). This reference workflow also uses it for read-only
source inspection. Running code, tests, or a calculation is a separate choice
that needs permission and appropriate inputs.

Supply the repository, revision, exact read or write scope, and the evidence
you expect. During the task, watch for a request to touch more files or run an
unplanned command. Afterward, inspect the cited source and any diff, and ask
what each check actually established. A successful command shows that an
operation completed; its relevance determines whether it validates a claim.
A passing test cannot choose the correct scientific interpretation. You decide
whether to request review or further bounded work, not whether to adopt the
result merely because Codex says it is done.

## Git and GitHub make a change inspectable over time

Git gives the source and its changes durable version identities. GitHub can
host that history and a collaborative review. Give collaborators the precise
revision or proposed diff and the reason for the change, with the evidence
needed to assess it. Check that comments concern the same revision you intend
to use; a later edit may invalidate an earlier review.

The return is a reviewable record, not a scientific endorsement. Neither a
commit nor a merged pull request proves that a method is appropriate. Decide
separately whether the change should be shared, integrated, and used. Local
Git may be enough for an individual task; reading a supplied passage needs
neither GitHub nor a new repository. Evidence can live in an appropriate
research record as long as the source and result remain identifiable.

## A reviewer challenges the returned work

For a consequential change, ask a colleague who did not produce it to compare
the original request, exact diff, supporting sources, and validation results.
For example: did changing a documented plot setting also change an unrelated
selection? Does the reported check cover the changed setting? Supply unresolved
questions rather than only the author's conclusion.

A separately tasked AI reviewer can assist this challenge. Independence means
it did not author or execute the work being reviewed; asking the same executor
to reconsider is a self-check. AI review is not human scientific peer review
or independent replication. Follow up findings with evidence and return any
repair for the relevant checks. Reviewer agreement advises the human decision;
it does not make that decision.

## Human acceptance names what is supported

At the end, the research coordinator reads the evidence and review objections
and records what is accepted at the bounded task/evidence layer and what remains
open. “The current source defines these bin edges” may be supported while
“those edges produced this historical figure” remains unresolved. Accepting the
first statement need not accept the second. The scientific lead separately
judges assumptions, interpretation and scientific use; domain or collaboration
approval may also be needed. Neither decision supplies new task/effect authority.

Retain the question, source identities, returned work, relevant checks, review
findings, and your decision together. You do not need to manually repeat every
action: choose checks that could reveal a consequential error and reuse valid
evidence. The [evidence and acceptance explanation](evidence_reproducibility_and_acceptance.md)
develops that distinction further.

## Keep the responsibilities when the products change

This is one concrete reference implementation. The lasting responsibilities
are discussion and continuity, substantial research, technical repository
work, durable source history, independent challenge when required, bounded
task/evidence acceptance, and human scientific acceptance. They may be carried
out with different tools or directly by people. Product capabilities can overlap; a more capable tool still receives
only the task you authorized.

Next, use [the tool-choice scenarios](../how_to/choose_an_ai_tool_for_a_research_task.md)
to decide which contributions your question needs, then
[prepare a task request](../how_to/ask_an_assistant_to_prepare_a_task.md).
