---
name: correction-lib-prompt-contract
description: >-
  Draft or mechanically lint correction-lib prompts using bounded parsing,
  duplicate and placeholder detection, supplied-value normalization, and
  internal-consistency checks. Use as an authoring aid, not as certification
  of live workspace governance or authorization to execute the prompt.
---

# Prompt authoring and mechanical linting

Use this helper to draft or mechanically inspect a prompt. Never execute the
task represented by the submitted prompt.

## Authority boundary

The controlling workflow must read and apply all applicable live workspace
governance. This helper does not maintain a complete field catalog, policy
vocabulary, mode contract, or authorization model. Its result always records
that governance completeness was not assessed, and its output cannot create or
revoke authorization.

Unknown fields are accepted during ordinary linting. A helper failure is local
to this lint operation unless the controlling workflow explicitly requires its
artifact.

## Operations

- `authoring`: begin with the deliberately non-exhaustive
  [prompt template](assets/prompt_template.md), then add the currently required
  material by reading applicable live governance directly.
- `validation_only`: inspect the supplied prompt without editing it.
- `explicit_revision`: revise only when the user explicitly requests changes,
  then lint the revision again.

Do not silently fill missing task decisions or permission values.

## Mechanical lint

The helper checks only its intrinsic capabilities:

- strict UTF-8 and a bounded input size;
- fenced-block balance and simple `snake_case` mapping fields in unlabeled,
  `text`, `yaml`, or `yml` fences;
- duplicate top-level field names within each parsed mapping block;
- unresolved placeholder tokens in parsed mapping values;
- normalization of values actually supplied;
- a small set of contradictions derivable solely from supplied values.

It intentionally does not reject an unknown future field merely because this
helper does not know it. Repeated local keys in distinct mapping blocks are
kept separately, and non-mapping fences such as shell examples are not treated
as prompt-field namespaces.

For the OpenAI/Codex reference procedure, run it through the wrapper and
interpreter resolved from the local YAML profile and explicitly stated in the
controlling prompt. These paths are configuration, not prompt authorization:

```bash
wrap="<prompt-resolved-command-wrapper>"
python_env="<prompt-resolved-python-interpreter>"
workspace_root="<prompt-resolved-TOP26006_fw-path>"
"$wrap" \
  /bin/bash --noprofile --norc -c \
  'cd "$1" && "$2" \
   .agents/skills/correction-lib-prompt-contract/scripts/validate_prompt.py \
   --format human "$3"' prompt_lint \
  "$workspace_root" "$python_env" "<prompt_path>"
```

Use `--format json` for machine-readable output. Add `--json-out PATH` only
for an explicitly selected absent output path.

Exit codes:

- `0`: mechanical validity and internal consistency passed;
- `2`: CLI input or local helper-schema error;
- `3`: prompt mechanical or supplied-value consistency error;
- `4`: result output collision or write failure.

The JSON result reports helper support under `capabilities` and observed check
values under `results`. A supported check may have a false result. Report
`results.mechanical_validity`, `results.internal_consistency`, and
`governance_completeness: not_assessed` separately. Do not rename the first two
as policy validity, readiness, permission, or governance completeness.
