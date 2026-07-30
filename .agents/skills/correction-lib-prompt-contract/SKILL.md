---
name: correction-lib-prompt-contract
description: >-
  Create or validate correction-lib Codex prompts against the live AGENTS.md
  and CPC.md contract. Use when authoring, reviewing, linting, or diagnosing a
  correction-lib prompt, including prompt mode, repository scope, branch,
  dirty-state, validation, permission, commit, continuation, evidence,
  publication, merge, and production fields. Report missing or conflicting
  decisions without filling them, and do not execute the submitted task.
---

# Correction-lib prompt contract

Use this skill only to author or validate a correction-lib Codex prompt. Never
execute the task represented by the submitted prompt.

## Authority and version

Treat the live workspace-root `AGENTS.md` and `CPC.md` as the only normative
sources. Treat `references/prompt_schema.json` as a reviewed executable
projection, not policy. The validator and schema version is `1.0.0`.

Stop when `references/governance_binding.json` does not match the complete live
bytes of either governance file. Request a separately authorized schema-update
round; never regenerate the binding during validation.

## Choose the operation

Classify the request as exactly one of:

- `authoring`: collect every task-defining decision, draft with
  `assets/prompt_template.md`, and validate.
- `validation_only`: validate the supplied prompt without editing it.
- `explicit_revision`: validate, explain diagnostics, revise only because the
  user explicitly asked, and validate the revision again.

Do not revise a submitted prompt under `validation_only`.

Before authoring or semantic review, read live `AGENTS.md`, `CPC.md`, and every
applicable nested `AGENTS.md`. Do not copy their normative rules into the
prompt when a compact reference is sufficient.

## Obtain explicit context

Ask for or preserve explicit values for:

```text
continuation: yes | no | unknown
evidence_round: yes | no | unknown
user_run_handoff: yes | no | unknown
```

Use `unknown` when the author has not decided. Never silently turn `unknown`
into `no`.

For authoring, obtain every required decision named by live CPC, including
prompt mode, repository permissions, branch contract, dirty-state policy,
validation ceiling, heavy permissions, commit contract, artifact paths, and
any continuation, evidence, publication, merge, or production contract. Do
not suggest authorization values as defaults and do not infer decisions from
task prose.

## Run deterministic validation

Use only the workspace wrapper, non-login shell, and pinned interpreter:

```bash
/users/apiccine/work/correction-lib/codex-run.sh \
  /bin/bash --noprofile --norc -c \
  'cd /users/apiccine/work/correction-lib &&
   /users/apiccine/work/miniconda3/envs/clib-env/bin/python \
   .agents/skills/correction-lib-prompt-contract/scripts/validate_prompt.py \
   --workspace-root /users/apiccine/work/correction-lib \
   --continuation "$1" \
   --evidence-round "$2" \
   --user-run-handoff "$3" \
   --format human "$4"' prompt_contract \
  <continuation> <evidence_round> <user_run_handoff> <prompt_path>
```

Use `--format json` for machine-readable output. Add `--json-out PATH` only
when the user explicitly supplied that output path. Never add a fix, default,
execution, branch-inference, or permission-inference option.

Present all safe diagnostics together, ordered by source location and stable
identifier. A diagnostic identifies the missing or conflicting decision and
its governance locator; it never supplies the decision.

## Separate deterministic and semantic review

Label validator output `deterministic schema validation`. Schema validity
means only mechanical consistency with the selected contexts and bound
governance snapshot.

Perform a bounded model semantic review only when requested, label it
`optional semantic review`, and keep it separate. A semantic review may
identify ambiguity but must not invent authorization, choose a branch or
mode, inspect external state, or claim scientific, production, publication,
or merge readiness.

## Finish

Report the input SHA-256, final AGENTS/CPC SHA-256 values, validator version,
schema version, the three explicit context values, error count, warning count,
and `valid_schema`.

Never start the prompt's task, contact a remote service, inspect production,
modify governance, edit Codex configuration, or install anything while using
this skill.
