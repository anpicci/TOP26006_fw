# OpenAI selection — candidate guide v0.1.0

**Inactive design; source observations 2026-11-14 UTC.** Apply the
[common criteria/responsibilities](../model_selection_common_v0.md) and
[task/run boundary](../direct_prompt_authoring_v0.md#p4-task-run-and-evidence-in-the-existing-workbook).
This is the candidate native guide, not activated policy, an account probe or
project performance qualification. It does not alter this round's dispatched
configuration. Future model_policy links here instead of duplicating catalogs
and routing tables; AGENTS keeps authority and immutable-attempt invariants.

## Dated local decisions and provider history

At master `5ba30bcc367d39e3131335a0eb55fdbc5bc54ce4`,
[model_policy](../../../governance/model_policy.md) attributes the general
defaults to owner decisions on 2026-10-31 and Terra specialization to 2026-11-05.
These are adopted local vocabulary/routing choices, not comparative measurements.
The reported closed pilot's usable reviews do not establish a winner, cost,
latency, availability or production qualification. The maintained
[OpenAI reference procedure](../../how_to/providers/openai_reference_procedure.md)
dates mechanism observations to 2026-11-02/03 and separates installation,
product, role and acceptance. This candidate consumes that distinction, not
its historical sources as a substitute for current access evidence.

The candidate retains these local choices as a reasoned starting point: fixed,
checkable work can use a lighter profile, while ambiguity and coupling justify
more reasoning/capability. Selection remains the author's, under common criteria;
importance or file count alone is insufficient.

| Local task characteristics | Candidate OpenAI/Codex default pair |
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

Retained local upper exceptions are Sol 6.1/xhigh, historical Sol 6/xhigh and
Astra/xhigh as rare motivated cases; Astra/max requires the explicit exceptional
owner/eval-driven decision. Every such exception needs representative benefit
evidence, specific need and bounded scope/resources, without a mandatory prior
lower-tier failure. The local legacy gpt-5.6-luna/terra/sol labels require actual
GPT-6 unavailability or exact historical reproducibility and fresh author-selected
dispatch. explicit_fallback is a reporting state, never a concrete model label.
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
to author or lint the inert records in the companion document.

Record requested/dispatched versus directly selected and runtime-reported
values with metadata source, using not_observable when unavailable. Do not
rename a CLI label as independently established runtime identity. An observed
mismatch or unavailable configuration stops that attempt for new author
selection/dispatch; no silent fallback. Missing exact identity limits only a
claim that needs it. This guide claims no empirical qualification, broad
migration, provider equivalence, greater portability or adoption.
