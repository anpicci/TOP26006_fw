# Prepare a governance workflow prompt with the D8 compiler

The non-normative D8 compiler prepares an inspectable CPC prompt candidate and
a YAML compilation receipt. It does not dispatch a prompt, perform an effect,
evaluate execution evidence, or accept a result. D8 remains non-normative
during D8-E and D8-F.

Use the Python wrapper and interpreter resolved from the local YAML profile:

```bash
"$wrapper" "$python_interpreter" tools/governance_workflow_compiler.py \
  --feature task.feature --bindings task_bindings.yml \
  --prompt-out generated_prompt.md --receipt-out compilation_receipt.yml
```

The feature file supports `Feature`, `Scenario`, `Given`, `When`, `Then`, `And`,
`But`, comments, blank lines, and ordinary tags. An unsupported or ambiguous
construct produces a line-referenced diagnostic and no prompt. This is a
bounded standard Gherkin subset, not a full Gherkin implementation.

The separate binding YAML supplies `bindings`, `repositories`, `prompt`, and,
when needed, `requested_effects`, `stages`, `continuation`, and safety/readback
constraints. Each material binding names its source identity, acquisition
state, validity scope, and exact effect and target if it authorizes an effect.
Gherkin sentences and tags never grant authority. A positive effect needs an
acquired owner binding plus the exact current CPC permission and path/ref/action
scope. The author must inspect the generated Markdown and receipt against live
governance before any separately authorized dispatch.

`dispatch_gate` may name three acquired binding IDs: `owner_authorization_binding`,
`manual_governance_review_binding`, and `live_applicability_binding`. Without
them, the receipt marks the candidate prepared while leaving conformance,
owner authorization, and dispatchability unestablished. A failed compile writes
only a diagnostic receipt; it never writes a valid prompt.

The compiler checks closed-vocabulary values against current governance text
and calls the maintained prompt validator. Its validator result is mechanical
lint only; it does not prove authority, scientific correctness, live
applicability, or governance completeness. The receipt records source hashes,
bindings, effects, traceability, unresolved boundaries, and `NOT_EVALUATED`
execution assertions. Historical H1-H6 comparison belongs to D8-F.

If the compiler cannot express a manually valid task, use the existing
[manual prompt guide](write_a_prompt_manually.md) and
[prompt validation guide](validate_a_prompt_before_execution.md). A compiler
limitation does not revoke an independently valid manual workflow.
