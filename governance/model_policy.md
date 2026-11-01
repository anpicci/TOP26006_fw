# Model and reasoning policy

Catalog/routing policy extracted from accepted I1 on 2026-10-25 and updated by
owner decision on 2026-10-31. This is an owner-adopted local vocabulary, not a
claim of account availability or representative project qualification.
Stable authority and no-silent-switch invariants remain in AGENTS.md.


Every prompt must declare:

```text
preferred_codex_model
reasoning_level
delegation_policy
model_selection_rationale
```

Concrete Codex model labels:

```text
gpt-6-luna
gpt-6.1-sol
gpt-6-sol
gpt-6-astra
```

The current preferred labels for new prompts are `gpt-6-luna`, `gpt-6.1-sol`
and `gpt-6-astra`. `gpt-6-sol` remains recognized for historical reproducibility
and an explicitly selected transition; it is not an alias for `gpt-6.1-sol`.
For new ordinary and complex substantive work, `gpt-6.1-sol` is the current
owner-approved default under the routing table below. Representative local
evaluation is required before claiming broad migration, equivalence or
superiority over the historical `gpt-6-sol` workload; it is not a universal
per-prompt prerequisite. A broad migration of existing workloads also requires
an explicit project adoption decision. This policy update adopts prospective
defaults; it does not claim that a migration evaluation has occurred or
silently migrate an existing dispatch. The hardest open or adversarial
reasoning retains `gpt-6-astra` / `high` as its preferred default.

Legacy/fallback-only concrete labels, subject to the conditions below:

```text
gpt-5.6-luna
gpt-5.6-terra
gpt-5.6-sol
```

Concrete catalog membership is an allowed governance vocabulary, not an
empirical model ranking. The routing guidance below consists of adopted
operational defaults based on mixed attributed evidence and owner choice. The
closed pilot produced 6/6 usable reviews for each requested High configuration
but did not establish a winner, general equivalence, production-critical
routing qualification, cost or latency claims, or a reason for automatic
additional benchmarking.

Andrea together with `lane_governance` owns decisions and revisions for these
general rules. The owning lane's prompt author selects and motivates each
concrete model/reasoning pair under them. The central control plane receives
and preserves the rules in checkpoints; it does not author prompts, choose the
pair, or approve each compliant selection. Codex executes the dispatched
profile and may report a need to reclassify, but it must not silently switch.

`explicit_fallback` is a fallback selection and reporting state, not a concrete
model identity. It is not valid as `preferred_codex_model` for an execution-ready
dispatch, as `model_profile.model`, or as the value passed to `-m`, and it never
authorizes automatic runtime model selection. Before a fallback execution
attempt begins:

```text
owning_lane_prompt_author:
  selects_one_concrete_codex_model_label

new_attempt:
  preferred_codex_model: selected_concrete_label
  model_profile.model: selected_concrete_label
```

Record the fallback path through the existing `fallback_or_switch` provenance
surface. Do not create a second fallback mechanism or a persistent
`resolved_model` field.

Reasoning levels:

```text
low
medium
high
xhigh
max
```

Delegation:

```text
forbidden
allowed
required
```

For an execution-ready Codex CLI dispatch, derive `model_profile` from the
existing prompt fields:

```text
model_profile:
  model: preferred_codex_model
  reasoning_effort: reasoning_level
```

Both `preferred_codex_model` and `model_profile.model` must be one of the
concrete Codex model labels above. A fallback selection state is not
execution-ready until the owning lane's prompt author selects that concrete
label and issues a new explicit dispatch with the relevant owner authorization.

Do not create duplicate persistent model or reasoning fields to restate this
profile. `delegation_policy` and `codex_cli_mode` remain separate execution
controls and are not members of `model_profile`.

Materialize a governed Codex CLI profile invocation-locally:

```text
model:
  -m <concrete_codex_model_label>

reasoning_effort:
  -c 'model_reasoning_effort="<reasoning_level>"'
```

Never pass `explicit_fallback` to `-m`.

The governance allow-lists remain authoritative because the local CLI bootstrap
parser accepts arbitrary strings. Parser or bundled-catalog acceptance does not
prove runtime application, service availability, or account availability.

The atomic profile-governance boundary is:

```text
execution_attempt:
  one Codex execution attempt
  one immutable model_profile
```

This boundary does not redefine `one_round_one_decision`. A logical round,
workstream, or continuation may use later separately dispatched attempts, but a
material model or reasoning change never occurs silently inside the current
attempt.

If the executor determines that the dispatched profile no longer fits the
remaining task, it may recommend a reclassification using:

```text
direction:
  upward
  downward

cause:
  model_capacity_mismatch
  reasoning_effort_mismatch
  both
```

The executor may recommend the change but must not materialize it. Any model
change, reasoning-only change, upward change, or downward change requires:

```text
current_execution_attempt: stop
next_profile: selected_by_owning_lane_prompt_author
continuation: new_dispatch_required
```

Automatic self-routing and silent in-attempt profile substitution are
forbidden. An explicit fallback is a new-attempt outcome only after the owning
lane's prompt author selects its concrete model; `explicit_fallback` may record
that selection path but is not the attempted model. A new model or reasoning
value, including `high` to `medium`, requires the current attempt to stop and a
fresh explicit dispatch with the relevant owner authorization. Stop and report
before any fallback dispatch.

Canonical default guidance (owner-approved project policy):

| Task or decision characteristics | Default |
|---|---|
| Mechanical work with fixed inputs and directly checkable results | `gpt-6-luna` / `medium` |
| Focused, bounded structured work | `gpt-6-luna` / `high` |
| Ordinary substantive work | `gpt-6.1-sol` / `medium` |
| Complex substantive work | `gpt-6.1-sol` / `high` |
| The hardest open or adversarial reasoning | `gpt-6-astra` / `high` |

Classify the substantive decision, not the lane label, project importance, or
file count. Select the minimum sufficient model/reasoning pair directly.
Executing an already qualified production protocol does not redesign it, and
profile choice never qualifies or authorizes production or any other campaign.

These are the five canonical defaults. `gpt-6-astra` / `medium` is not a
canonical tier. Explain the selected pair in `model_selection_rationale`.

Upper exceptions are limited to:

| Model/reasoning pair | Condition |
|---|---|
| `gpt-6.1-sol` / `xhigh` | Rare motivated exception |
| `gpt-6-sol` / `xhigh` | Legacy/transitional exception only |
| `gpt-6-astra` / `xhigh` | Rare motivated exception |
| `gpt-6-astra` / `max` | Explicit exceptional owner/eval-driven exception only |

Every `xhigh` or `max` exception requires representative evidence that its
quality benefit justifies the added cost and latency, a specific reasoning need,
and a bounded scope or resource decision, without requiring a prior lower-tier
failure. It confers no
additional authority and does not relax evidence or acceptance criteria.

GPT-5.6 Terra, Sol, and Luna are legacy/fallback only. Their use requires either
actual GPT-6 unavailability or exact historical reproducibility, together with
a fresh explicit dispatch and honest provenance. Availability does not justify
silent substitution or a claim of superiority.

Do not require a Luna-to-Sol-to-Astra progression, a reasoning ladder, a
universal second-model review, or consensus seeking. The independent-reviewer
default in governance/contracts/orchestration.md concerns independent authorship, not a second model. No automatic model or
reasoning escalation is allowed. Missing evidence, an ambiguous gate, a
qualified warning, a short answer, service rejection, or another non-cognitive
failure does not by itself demonstrate reasoning insufficiency; address the
relevant cause.
Missing evidence or authorization is not solved by a stronger model.

## External documentation and local adoption

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

No comparative project model evaluation, production qualification, availability
probe or broad model migration was performed for this update. Missing account
availability evidence is not a universal workflow gate. A concrete unavailable
profile affects its own dispatch, under the existing fallback rules.

Historical benchmark/report model and reasoning labels remain historical truth;
do not rewrite them prospectively. Historical evidence does not establish GPT-6
availability, comparative ranking, cost, latency, or production qualification.

This file, delegated by AGENTS.md, owns project-common model-routing policy for work below the current
ANDOCS path. The retained local ANDOCS `AGENTS.md` is a transitional
compatibility layer and must not introduce a competing routing decision. Each
CPC.md applies its path-applicable AGENTS.md and must not maintain a competing
complete routing matrix.
CONTRIBUTING.md is not a model-routing authority.

Do not use Sol merely because a task is important. Do not compensate for an
undersized model with excessive reasoning. Reports must distinguish these
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

`Ultra` is an orchestration mode, not a reasoning level. Encode it only when
explicitly authorized:

```text
reasoning_level: max
delegation_policy: allowed
codex_cli_mode: ultra
```

Use `delegation_policy: required` instead when the exact workflow requires
delegation; both values remain members of the closed vocabulary.

Do not use Ultra for narrow controlled work, commit preparation, publication,
or production execution.
