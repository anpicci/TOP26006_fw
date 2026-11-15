# Model selection and immutable attempts

**Candidate policy; pending adoption.** This branch does not activate governance
for other lanes. Stable authority remains in [AGENTS](../AGENTS.md); construction
and same-delivery task/run boundaries remain in [CPC](../CPC.md).

Common selection responsibilities and criteria follow the
[common guide v0.2.0](model_selection_common.md). Provider-specific vocabulary,
defaults, Terra specialization, upper/legacy exceptions, dated vendor observations
and native configuration mappings belong solely in the
[OpenAI guide v0.1.0](providers/openai_selection.md). These maintained homes
replace inactive design references; no other provider is implied.

Under CPC’s complete single-delivery boundary, the author selects an immutable
run configuration outside the reusable task, retaining provider/product, native
model/reasoning, rationale and exact guide versions/content. For OpenAI/Codex,
preferred_codex_model, reasoning_level and model_selection_rationale are run
configuration values. Derive model_profile.model and
model_profile.reasoning_effort invocation-locally from that configuration;
do not persist duplicate selection aliases. The task retains delegation_policy,
independent-review requirements and scientific model-object constraints.
Configuration grants no authority or method change.

Andrea together with lane_governance owns decisions and revisions for the
general rules. The owning lane's prompt author selects and motivates each
concrete pair. The central control plane preserves the rules in checkpoints;
it does not author prompts, choose the pair or approve each compliant selection.
The executor applies the dispatched profile and may recommend reclassification,
never materialize a switch. A new model or reasoning value, upward or downward,
requires stopping the current attempt and a fresh author-selected dispatch with
relevant owner authorization. explicit_fallback remains a reporting state,
never a concrete model or automatic runtime selection.

One execution attempt has one immutable model_profile. This does not redefine
one_round_one_decision: separately dispatched attempts can belong to a logical
round or continuation. Any observed mismatch or switch stops the attempt for
new author selection and dispatch. An unavailable concrete configuration affects
its own dispatch; missing availability evidence is no universal workflow gate.
No automatic model/reasoning escalation, ladder, consensus or universal second
model is required. Independent review concerns authorship, not model difference.
Missing evidence, authority or an ambiguous external outcome is not solved by
a stronger model.

No comparative evaluation, production qualification, availability probe or broad
model migration is established by this policy. Historical benchmark/report labels
remain historical truth; they prove no new availability, ranking, cost, latency
or production qualification. Common/provider guide observations distinguish
vendor description, local adoption and actual observed availability.

This file, delegated by AGENTS.md, owns project-common model-routing policy for work below the current
ANDOCS path. The retained local ANDOCS `AGENTS.md` is a transitional
compatibility layer and must not introduce a competing routing decision. Each
CPC.md applies its path-applicable AGENTS.md and must not maintain a competing
complete routing matrix.
CONTRIBUTING.md is not a model-routing authority.

Reports must distinguish these
semantic values:

```text
requested_or_dispatched_model
requested_or_dispatched_reasoning_effort
directly_selected_model_if_observable
runtime_reported_model_label_if_observable
runtime_reported_reasoning_effort_if_observable
fallback_or_switch
```

Reuse existing report fields instead of emitting parallel mandatory aliases:
`preferred_or_configured_model` may carry
`requested_or_dispatched_model`, and `reasoning_level` may carry
`requested_or_dispatched_reasoning_effort`, when the meanings are identical.
Do not rename provider- or CLI-reported metadata as independently observed
runtime identity. When an exact value is unavailable, report `not_observable`;
do not infer an exact model from a generic family label. Record an observed
mismatch, fallback, or switch and stop under the reclassification rule.

When exact `model_profile` identity is decision-material, the prompt must
declare `required_profile_agreement_evidence`, and execution must fail closed if
that evidence cannot be established. Empirical model-profile qualification is
one such case. Otherwise record the requested or dispatched profile and all
available CLI/runtime reporting honestly; unknown remains unknown. Unavailable
exact runtime identity is not a universal blocker for ordinary work, but any
observed profile mismatch or switch requires stop and reclassification.
