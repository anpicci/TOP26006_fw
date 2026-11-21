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
“Other configurations were not inspected” states a limit; “the scientific lead accepts this bounded interpretation within their scientific remit” records a scientific decision; task/evidence acceptance remains separate.
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

## Complete scientific note

A scientific note belongs to the project and serves the person, research actor
and AI agent. It connects the question, context, source versions, method,
assumptions, results, relevant alternatives and decision reasons. It explains
why work stopped and what evidence would permit resumption. Keep the reasons
in the note. Reuse an adequate existing note; the workbook can host it or link
its authorized location/version. Read the complete note and pertinent modules;
section links guide navigation without replacing that context. The note does
not duplicate the permissions register. See [roles and continuity](roles_and_authority.md#person-research-actor-and-ai-agent).

The following note translates the accepted researcher guide, content version 1
of 2026-11-20. Its English placement is candidate documentation pending human
acceptance. The synthetic example and guided R19 use have documentary and
teaching scope. They establish neither independent external usability, another
provider's operation, global scientific qualification nor automatic S5 execution.

### Question and scope

For five synthetic measurements, would more statistical information improve the
uncertainty on a common value more than improved calibration? The observations
have no physical observable or unit. Values and standard uncertainties share
one numerical scale; variances use its square. Accuracy would additionally
require characterization of calibration offset against a known reference.

### Data and provenance

| Measurement | Value, x_i | Statistical standard uncertainty, sigma_i |
| --- | ---: | ---: |
| m1 | 10.1 | 0.2 |
| m2 | 9.9 | 0.2 |
| m3 | 10.3 | 0.2 |
| m4 | 9.8 | 0.2 |
| m5 | 10.2 | 0.2 |

All five observations enter the combination. The [CSV](../../examples/repeated_measurements/data/measurements.csv),
[calculation](../../examples/repeated_measurements/analyze.py) and
[tutorial description](../../examples/repeated_measurements/README.md) are
identified here at TOP revision `662f2dc257119278e11ca0acc13c6490e4a214b5`.
The CSV supplies identifiers, values and uncertainties only. Acquisition-period
association and common calibration require additional sources for experimental
use. These numbers reuse the documented calculation; this note introduces no
new execution.

### Statistical model and combination

Assume independent Gaussian errors centered at zero and known statistical
standard uncertainties. With weights \(w_i=1/\sigma_i^2\),

\[
\widehat\mu=\frac{\sum_{i=1}^5w_ix_i}{\sum_{i=1}^5w_i},
\qquad s^2=\operatorname{Var}_{\rm stat}(\widehat\mu)
=\frac1{\sum_{i=1}^5w_i}.
\]

The equal uncertainties give normalized weights of \(1/5\) and

\[
\widehat\mu=10.060,\qquad s^2=0.008,\qquad s=0.089443.
\]

The residual dispersion is

\[
\chi^2=\sum_{i=1}^5\frac{(x_i-\widehat\mu)^2}{\sigma_i^2}=4.30,
\qquad \nu=5-1=4,\qquad\chi^2/\nu=1.075.
\]

Four degrees of freedom follow from five observations and one estimated common
parameter. This dispersion describes the stated model. An identical shift of
all observations leaves the residuals unchanged, so their agreement cannot
determine a common calibration component.

### Hypothetical common calibration

To expose that limitation, suppose

\[
x_i=\mu+b+\epsilon_i,\qquad
\operatorname{E}[b]=0,\qquad\operatorname{Var}(b)=c^2.
\]

The independent statistical errors \(\epsilon_i\) follow the tutorial model;
\(b\) is one additive residual calibration component shared by every measurement
and independent of those errors. Its standard uncertainty is \(c\). The zero
mean assumption describes a residual correction model and needs calibration
justification. The covariance matrix is

\[
V_{ij}=\sigma_i^2\delta_{ij}+c^2,
\]

where \(\delta_{ij}\) is one on the diagonal and zero elsewhere. The common
variance contributes off diagonal as well. Since normalized weights sum to one,

\[
u_0^2=s^2+c^2=0.008+c^2.
\]

Statistical uncertainty decreases through combination while the common variance
enters once in full. “Total” here includes only these two specified components.
The tutorial does not determine \(c\). Different calibration responses or partial
correlations would require their corresponding covariance matrix.

### More data or better calibration

Let \(k>1\) be the ratio of statistical information in the larger-data scenario
to the reference. For independent observations of equal quality it is the sample
size ratio. Assume statistical variance becomes \(s^2/k\) while \(c\) stays fixed.
The alternative keeps the sample and reduces \(c\) to \(c'\), with
\(0\leq c'<c\).

| Scenario | Statistical information | Common uncertainty | Estimate variance |
| --- | --- | --- | --- |
| Reference | Current | c | \(u_0^2=s^2+c^2\) |
| More data | Multiplied by k | c | \(u_{\rm data}^2=s^2/k+c^2\) |
| Better calibration | Current | c' | \(u_{\rm cal}^2=s^2+c'^2\) |

Compare variance reductions relative to the same reference:

\[
\Delta_{\rm data}=u_0^2-u_{\rm data}^2=s^2(1-1/k),
\qquad\Delta_{\rm cal}=u_0^2-u_{\rm cal}^2=c^2-c'^2.
\]

A larger reduction gives lower final uncertainty on the same quantity. For the
illustrative choice \(k=2\), statistical uncertainty falls from 0.089443 to
0.06325 and \(\Delta_{\rm data}=0.004\). Comparing calibration improvement
requires \(c\) and a justified estimate of \(c'\). The stated precision makes
the example reproducible without implying physical measurement precision.

This comparison assumes independently treatable interventions. If additional
data constrain calibration too, include that dependence in the larger-data
scenario. Practical priority also depends on achievable improvements, costs,
time and available resources.

### Usable conclusion, stopping point and reopening evidence

The five measurements give 10.060 with statistical standard uncertainty
0.089443 under the tutorial model. The hypothetical shared additive calibration
extends the variance to \(0.008+c^2\); agreement among measurements does not
measure \(c\). The statistical result remains reusable within its stated scope.
Priority between more data and better calibration remains open because shared
components, their covariance and achievable improvements have not been
quantified. Those inputs would allow final uncertainties and a justified
priority to be determined. This is why the comparison stops here.

### From the note to a bounded task

The researcher and research actor first consider whether the existing note
already answers the question. If work is needed, the [playbook](../operations/playbook/index.md)
routes to the native maintained procedure; the illustrative equations do not
prescribe an experimental calibration model. Give the agent the complete adopted
note, identified data, acquisition-period association, calibration documentation
and reference fit model. Agree the scenarios and read the scientific originals
on which their comparison depends. Verify access to those versions in each
receiving session.

Preparation may reconstruct correlations with their sources and prepare inputs
and configurations, identifying quantities to compare. Missing sources leave
the relevant judgment open. Executing fits requires its own researcher mandate.
Use the [task-preparation procedure](../how_to/ask_an_assistant_to_prepare_a_task.md).

### From the report to a decision

The report records the actual attempt, consumed inputs, outputs and evidence.
These four situations support different next decisions:

| What the report contains | What the researcher can decide |
| --- | --- |
| The agent read the data but could not open the calibration source in its session. | Make the authorized version accessible or contact its custodian. Correlation treatment remains unestablished. |
| The source covers the correct measurements but leaves a necessary correlation undetermined. | Request that information from the calibration maintainer. The statistical-only combination remains citable within scope. |
| Inputs and configurations are ready. | Check that the scenarios represent the chosen alternatives; decide who may execute the fits if numerical estimates are needed. |
| An executed comparison attributable to both scenarios is available. | Trace each scenario's inputs and assumptions, compare total-uncertainty reductions on the same quantity, and record the priority with its conditions. |

The first three situations inform acquisition or completion of evidence. A
quantitative judgment needs the executed comparison or an applicable analytic
derivation with all necessary parameters determined. The researcher considers
final uncertainty, assumptions and costs. Follow the existing [review procedure](../how_to/review_returned_evidence.md).

In the [teaching lifecycle](../../examples/research_workflow_lifecycle/observed_scenario.md),
review found missing code-revision and CSV identities. The repair supplied them
and reused the verified calculation. Review and acceptance there were simulated
by the same executor, within the example's model; the conditional executor
exercise was not activated. The accepted researcher guide and note retain that
scope and do not demonstrate independent external use.

### Continuity and source responsibility

The project maintains its note at the authorized location. The workbook hosts
it or identifies its version. Modules may divide a large note while preserving
the complete argument. The reference to CMS Analysis Notes concerns the care of
scientific reasoning; this example is synthetic and includes no internal material.

On resumption the person, actor and agent read the complete note and its modules
to recover objectives, premises, alternatives, decisions and open questions. The
actor carries continuing competence and agreed responsibility. The agent must
actually acquire the note and necessary reports; an earlier conversation does
not guarantee access in a new session. Use the [handoff](../../templates/handoff.md)
for attempts, accepted results and effects awaiting reconciliation. Keep decision
reasons in the note, linked to evidence. Calibration maintainers retain their
technical source; researchers with actual authority decide scientific adoption.
A changed calibration version reopens only conclusions that depend on it.

As a dated example of a result with a use condition, the [R19 reference](../operations/workbook/artifacts/plots_and_inference.md#inference_r19)
qualifies the right ctq8 limit at q = 1 because interpolation crosses missing
point 56. Preserve that condition when citing the profile. This guided reference
is not a new scientific qualification. Andrea's reading qualified the guide's
usefulness for his judgment; benefit to another researcher requires actual use.
The calibration values and fit results for a real application remain to be acquired.
