# Research-oriented writing

A research manual should lead with the question, source material, method, assumptions, uncertainty, evidence, review, and scientific interpretation. Those are the concepts a new researcher needs to judge a result. Git, prompts, wrappers, and branches remain necessary when they specify the exact operational mechanism, but they should appear at the point of use and be explained.

Diátaxis separates learning, problem solving, lookup, and conceptual understanding. A tutorial lets a learner complete an activity; a how-to answers one operational problem; a reference states current contracts and links to authority; an explanation discusses why the method works and where it stops. Mixing these roles can turn a teaching example into a false policy source.

## Define the object and quantities

Before interpreting a result, establish what the assertion refers to: for
example, a sample or process, period, selection or category, observable or bin,
fit parameter, job, task, output, or configuration. Explain the object once
and keep later references unambiguous; every sentence need not repeat it.

At first material use, define the quantity, unit, reference or baseline,
normalization, relevant sign convention, and uncertainty type. A count needs
the thing counted and the set within which it is counted. A percentage needs
its denominator. A difference needs its reference and orientation, such as
candidate minus baseline. A ratio needs numerator and denominator, including
how zero denominators are treated when relevant. An uncertainty needs the
object it describes and whether it is statistical, systematic, or another
specified kind. A formula helps when it exposes a distinction that prose hides.

A descriptive number alone does not support an inferential claim without the
required statistical model. In the existing [synthetic measurements example](../../examples/repeated_measurements/README.md),
chi-square per degree of freedom is a statistic under the stated uncertainty
model; it is neither a goodness-of-fit probability nor scientific acceptance.

## Connect numbers to their meaning

Explain what a number implies for the question. The frequency of a category
and its weighted contribution can answer different questions: a rare category
can carry substantial weight. State whether the evidence covers the fully
checked set, a sampled subset, or one example. None of those coverage claims
alone establishes a causal explanation. An explanation of one event does not
automatically explain a population. Display enough precision for the decision,
without digits that suggest unsupported physical precision.

Verb choice helps separate observation, hypothesis, conclusion, limit, and
decision. “The inspected outputs differ” records an observation; “a changed
normalization may explain the difference” proposes a hypothesis. “The traced
configuration accounts for this difference” needs evidence for that connection.
“Other configurations were not inspected” states a limit; “the responsible
researcher accepts this bounded explanation” records a decision with a remit.
Correlation is not automatically causation, and compatibility is not proof.
These distinctions guide an argument; they do not prescribe five report headings.

## Make method and operational state readable

Give enough method, assumptions, comparison, and coverage for the reader to
judge the claim. Open with the result and its significance before dense audit
vocabulary. Translate operational labels into action plus object: instead of
only “PASS”, say which check passed for which files or inputs. For “blocked”,
say which action cannot proceed, what evidence is missing, and which valid
result remains usable. Keep exact identifiers for traceability alongside this
account, so understanding does not depend on decoding them.

This is explanatory writing guidance. Live [execution policy](../../AGENTS.md)
and applicable contracts remain the authority for project-specific reporting
requirements.

The [manual route](../index.md) follows the synthetic question from calculation to bounded note, review, continuation, sequential evidence transfer, stop, and handoff. The current concrete agent procedure is OpenAI/Codex; [provider equivalence remains unverified](../reference/provider_compatibility.md).
