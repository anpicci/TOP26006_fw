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
- fenced-block balance and simple `snake_case` mapping fields;
- duplicate top-level field names;
- unresolved placeholder tokens;
- normalization of values actually supplied;
- a small set of contradictions derivable solely from supplied values.

It intentionally does not reject an unknown future field merely because this
helper does not know it.

Run it through the workspace wrapper and pinned interpreter:

```bash
/users/apiccine/work/correction-lib/codex-run.sh \
  /bin/bash --noprofile --norc -c \
  'cd /users/apiccine/work/correction-lib &&
   /users/apiccine/work/miniconda3/envs/clib-env/bin/python \
   .agents/skills/correction-lib-prompt-contract/scripts/validate_prompt.py \
   --format human "$1"' prompt_lint \
  <prompt_path>
```

Use `--format json` for machine-readable output. Add `--json-out PATH` only
for an explicitly selected absent output path.

Exit codes:

- `0`: mechanical validity and internal consistency passed;
- `2`: CLI input or local helper-schema error;
- `3`: prompt mechanical or supplied-value consistency error;
- `4`: result output collision or write failure.

Report `mechanical_validity`, `internal_consistency`, and
`governance_completeness: not_assessed` separately. Do not rename the first two
as policy validity, readiness, permission, or governance completeness.
