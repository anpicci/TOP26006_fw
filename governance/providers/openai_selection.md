# OpenAI selection — guide v0.1.0

**Candidate normative home; pending adoption. Source observations 2026-11-14 UTC.**
Baseline: approved OpenAI guide v0.1.0 plus retained master conditions below.
Apply the [common guide v0.2.0](../model_selection_common.md) and
[CPC task/run boundary](../../CPC.md#construction). This is the native policy
home for future adoption, not an account probe or project qualification.
This branch does not activate policy for other lanes or change an existing
dispatch. [AGENTS](../../AGENTS.md) keeps authority and attempt invariants.

## Dated local decisions and provider history

At master `5ba30bcc367d39e3131335a0eb55fdbc5bc54ce4`,
[model_policy](../model_policy.md) attributes the general
defaults to owner decisions on 2026-10-31 and Terra specialization to 2026-11-05.
These are adopted local vocabulary/routing choices, not comparative measurements.
The reported closed pilot's usable reviews do not establish a winner, cost,
latency, availability or production qualification. The maintained
[OpenAI reference procedure](../../docs/how_to/providers/openai_reference_procedure.md)
dates mechanism observations to 2026-11-02/03 and separates installation,
product, role and acceptance. This candidate consumes that distinction, not
its historical sources as a substitute for current access evidence.

This guide retains these local choices as a reasoned starting point: fixed,
checkable work can use a lighter profile, while ambiguity and coupling justify
more reasoning/capability. Selection remains the author's, under common criteria;
importance or file count alone is insufficient.

| Local task characteristics | Local OpenAI/Codex default pair |
| --- | --- |
| Mechanical, fixed inputs and directly checkable outputs | gpt-6-luna / medium |
| Focused bounded structured work | gpt-6-luna / high |
| Ordinary substantive work | gpt-6.1-sol / medium |
| Complex substantive work | gpt-6.1-sol / high |
| Hardest open/adversarial reasoning | gpt-6-astra / high |

The recognized concrete local vocabulary is gpt-6-luna, gpt-6.1-sol,
gpt-6.1-terra, gpt-6-sol and gpt-6-astra. Historical gpt-6-sol is not an alias
for gpt-6.1-sol. Terra is a specialized local option for bounded visual reasoning,
computer use, concise writing and scoped code fixes: normally medium, high with
a useful task-specific rationale. No comparative superiority is implied.

Retained local upper exceptions are Sol 6.1/xhigh and Astra/xhigh as rare
motivated cases; historical Sol 6/xhigh is a legacy/transitional exception only.
Astra/max requires the explicit exceptional owner/eval-driven decision.
Every xhigh or max exception requires representative evidence that its quality
benefit justifies the added cost and latency, a specific reasoning need, and
a bounded scope or resource decision, without requiring a prior lower-tier
failure. It confers no additional authority and does not relax evidence or
acceptance criteria. The local legacy gpt-5.6-luna/terra/sol labels require actual
GPT-6 unavailability or exact historical reproducibility and fresh author-selected
dispatch. explicit_fallback is a reporting state, never a concrete model label.
The exact legacy labels are gpt-5.6-luna, gpt-5.6-terra and gpt-5.6-sol.
These local restrictions are not claims about all provider-supported combinations.

## Official source observations, distinct from local adoption

- [Model selection](https://developers.openai.com/api/docs/guides/model-selection),
  sections Meet the models / How to think / Experiment, observed 2026-11-14:
  vendor descriptions distinguish Luna, Sol 6.1, Terra 6.1 and Astra workloads
  and advise comparisons on fixed inputs. The page permits an Astra default
  when usage/time are unimportant and illustrates extra-high settings. Those
  suggestions do not replace the local five defaults or exception evidence.
- [Reasoning models](https://developers.openai.com/api/docs/guides/reasoning),
  Reasoning effort / Reasoning mode / Change reasoning mid-conversation,
  observed 2026-11-14: supported effort values and defaults depend on model;
  Sol 6.1 excludes none/minimal and defaults to medium. Mode and effort are
  distinct. Vendor-supported mid-conversation updates do not permit a local
  in-attempt switch. API documentation does not establish matching CLI controls.
- [Deployment checklist](https://developers.openai.com/api/docs/guides/deployment-checklist),
  Choose a model / Set up reasoning.effort, observed 2026-11-14: documents
  low/medium/high/xhigh/max for Astra, Sol 6.1, Sol 6 and Luna; Sol 6/Luna also
  support none. It recommends representative evaluation and measuring task
  success, latency, tokens and cost per success. API tool support is surface
  dependent; this is no permission to run evaluations or tools here.

These are dated page observations, not vendor release-version identities;
the evidence package retains acquisition notes and exact short excerpts.
The applicable subset for a selected model/product must be verified at use:
there is no claim here that Terra, ChatGPT, Codex CLI and API expose the same
efforts or features. No prices, complete catalog or account availability are
asserted. Model-selection prose, local recommendations, parser acceptance and
public documentation are not runtime evidence. The local stricter exceptions
and immutable-attempt rule are retained intentionally rather than importing
vendor defaults or switch behavior as owner decisions.

## Run configuration and observation

For the candidate OpenAI/Codex procedure retain provider/product and the
author's preferred_codex_model, reasoning_level, model_selection_rationale,
common/provider guide revisions and retained content locators outside the task.
Derive model_profile only invocation-locally. The existing native CLI mapping
is model to `-m` and effort to `-c model_reasoning_effort`; this is an interface
description, not a runnable command or proof of supported values/application.
Product/API options require their own documented native mapping. Delegation
authorization and independent-review requirements stay in the task; concrete
actor selection cannot enlarge them. No inference/account request is needed
to author or lint the inert records in the historical design examples.

Record requested/dispatched versus directly selected and runtime-reported
values with metadata source, using not_observable when unavailable. Do not
rename a CLI label as independently established runtime identity. An observed
mismatch or unavailable configuration stops that attempt for new author
selection/dispatch; no silent fallback. Missing exact identity limits only a
claim that needs it. This guide claims no empirical qualification, broad
migration, provider equivalence, greater portability or adoption.

## Retained native interface and local restrictions

Current preferred labels for new prompts are gpt-6-luna, gpt-6.1-sol and
gpt-6-astra. Historical gpt-6-sol also permits an explicitly selected transition.
The prospective defaults neither silently migrate an existing dispatch nor prove
migration evaluation. Representative local evaluation is required before broad
migration, equivalence or superiority claims about historical workloads; broad
migration also needs explicit project adoption. This is no universal per-task
evaluation gate. Local catalog membership is vocabulary, not an empirical ranking.
The historical closed pilot produced 6/6 usable reviews for each requested High
configuration; it established no winner, general equivalence, production-critical
routing, cost/latency claim or automatic additional benchmark requirement.

Classify the substantive decision rather than lane, importance or file count;
select the minimum sufficient pair directly. Do not use Sol merely because a
task is important or compensate for an undersized model with excessive effort.
Executing an already qualified production protocol does not redesign or qualify
it. gpt-6-astra/medium is not one of the five canonical defaults. Explain the
author-selected pair in the run configuration's model_selection_rationale.
An upper exception confers no additional authority or relaxed acceptance.
Availability cannot justify silent legacy substitution or superiority claims.

Recognized local reasoning vocabulary is low, medium, high, xhigh, max, subject
to the model/product subset and stricter exceptions above. Parser acceptance is
not evidence of support. Derive this profile invocation-locally from the complete
author-selected run configuration, outside reusable task bytes:

```text
model_profile:
  model: preferred_codex_model
  reasoning_effort: reasoning_level
```

Both model values must be concrete labels in this guide. A fallback state is
not execution-ready until the owning lane's author selects one concrete label
and issues a fresh explicit dispatch with relevant owner authorization.
Keep fallback_or_switch as the existing reporting surface, with no second
fallback mechanism or persistent resolved_model alias. Never pass
explicit_fallback to -m or use it as preferred_codex_model/model_profile.model.
delegation_policy remains in the task, separately from model_profile;
codex_cli_mode is a separate explicitly authorized execution control.

Native invocation mapping (interface description, not a runnable dispatch):

```text
model:
  -m <concrete_codex_model_label>
reasoning_effort:
  -c 'model_reasoning_effort="<reasoning_level>"'
```

The local bootstrap parser accepts arbitrary strings; local allow-lists remain
binding, and parser/bundled-catalog acceptance proves neither runtime application
nor service/account availability. An executor may recommend upward/downward
reclassification for model_capacity_mismatch, reasoning_effort_mismatch or both,
but cannot materialize it. Any change, including reasoning-only high to medium,
stops the current attempt for fresh author selection and dispatch under
[model_policy](../model_policy.md). Stop and report before fallback dispatch.
Missing evidence, an ambiguous gate, warning, short answer, rejection or other
non-cognitive failure alone is not reasoning insufficiency; address its cause.

Ultra is an orchestration mode, not a reasoning level. Only an explicitly
authorized run may encode reasoning_level max and codex_cli_mode ultra; the
task must separately authorize delegation_policy allowed (required when the
exact workflow requires it). Ultra cannot be used for narrow controlled work,
commit preparation, publication or production execution. This is no new effect
grant or provider equivalence.

## Preserved earlier source observations

Official OpenAI documentation was consulted on 2026-10-31. These are external
product descriptions, separate from the project routing decision above:

- The [GPT-6 guide](https://developers.openai.com/api/docs/guides/latest-model)
  distinguishes the current family and calls for migration review when moving
  from `gpt-6-sol` to `gpt-6.1-sol`.
- The [GPT-6.1 Sol model page](https://developers.openai.com/api/docs/models/gpt-6.1-sol)
  describes performance near Astra for complex coding and professional work at
  lower cost. It lists `medium` as the default effort. These vendor claims do
  not establish equivalent results, costs or latency on this project's tasks.
- The [GPT-6 Astra model page](https://developers.openai.com/api/docs/models/gpt-6-astra)
  positions Astra for demanding reasoning and coding work. This does not
  authorize routing every important task to Astra.
- The [deployment checklist](https://developers.openai.com/api/docs/guides/deployment-checklist)
  recommends workload-specific evaluation, comparing task success, latency,
  token use and cost per successful task. It reserves higher effort for
  measured benefits. The local routing table is an owner decision, not an
  inference from public benchmark scores or prices.
- The [reasoning guide](https://developers.openai.com/api/docs/guides/reasoning)
  distinguishes effort from execution mode. Pro mode is a possible future
  evaluation axis only: this revision adds no `reasoning.mode` prompt field or
  execution grant. External support for changing effort within a conversation
  does not override this project's immutable-attempt and new-dispatch rules.

These observations are preserved without a new lookup or availability claim.
Historical report labels remain historical truth; do not rewrite them prospectively.
