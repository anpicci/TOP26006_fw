---
name: correction-lib-codex-prompt-preflight
description: Preflight a manually pasted correction-lib Markdown task prompt in the current Codex session before task-specific repository action. Use when the first nonblank line of the visible user message begins with `# Prompt` and a `prompt_id` appears in `Task metadata` or `Metadata and governance`; capture the visible message, preserve author-owned content, validate shared decisions, generate skill-owned governance, run the installed prompt-contract validator, and gate same-session continuation.
---

# Correction-lib Codex prompt preflight

Preflight the current visible Markdown prompt without executing its task. Treat
live `AGENTS.md` and `CPC.md` as normative and the bundled JSON files as derived,
versioned projections.

## Trigger boundary

Invoke this skill only when the first nonblank line of the current visible user
message begins with `# Prompt` and `prompt_id` is present in a `Task metadata`
or `Metadata and governance` section. Do not trigger for conversation, quoted
excerpts, mentioned files, or inert review of a generated canonical prompt.

The visible message is authoritative. Hidden interface or transport bytes are
unavailable, not required, and never claimed.

## Same-session workflow

1. Read complete live `AGENTS.md`, `CPC.md`, and applicable nested governance.
2. Confirm diagnostics output authorization and choose an absent output root.
3. Materialize the normalized visible message as a diagnostics-local UTF-8
   source capture. The user does not need to create a prompt file.
4. Run `scripts/preflight_prompt.py` through `codex-run.sh`, a non-login shell,
   and the pinned interpreter.
5. Reopen all seven generated artifacts and inspect blocking diagnostics,
   repairs, hashes, semantic-value records, validator input hash, and state.
6. Continue this same Codex session only when `preflight_state.json` ends in
   `ready_for_same_session_execution` with zero blocking errors.
7. Before the first task-specific action, have orchestration call the script's
   readiness assertion or equivalently reopen and verify the state. Record
   `execution_started` in orchestration evidence; the renderer never executes
   the task.

Canonical invocation:

```text
/users/apiccine/work/correction-lib/codex-run.sh /bin/bash --noprofile --norc -c '<pinned-python> .agents/skills/correction-lib-codex-prompt-preflight/scripts/preflight_prompt.py --workspace-root /users/apiccine/work/correction-lib --output-root <absent_diagnostics_root> --continuation <yes|no|unknown> --evidence-round <yes|no|unknown> --user-run-handoff <yes|no|unknown> <captured_visible_prompt.md>'
```

Use argument arrays when invoking this command. Never pass prompt content to a
shell or use it as an executable, module, callback, import, command, or argv
fragment.

## Ownership and ambiguity

Read `references/section_ownership.json` for the complete version-1 registry,
aliases, diagnostic catalog, permission-bearing terms, and state transitions.
Read `references/preflight_schema.json` when diagnosing generated artifacts.

- Preserve every author-owned and safe unknown section exactly and in source
  order. Never rewrite, summarize, normalize internally, or complete it.
- Preserve every shared-structured source section and semantic-value manifest.
  Validate values without inventing or silently changing them.
- Generate only skill-owned sections. Replace authored skill-owned sections in
  the canonical prompt and record the discrepancy.
- Block unknown permission-bearing sections and semantic ambiguity before any
  task-specific repository action.

## Outputs

Require an absent output root. The renderer writes exactly:

```text
authored_prompt.md
canonical_prompt.md
section_manifest.json
shared_value_manifest.json
prompt_contract_validation.json
preflight_state.json
preflight_report.md
```

Reopen every artifact. For every author-owned section require matching source
and canonical SHA-256 and `preserved_exactly: true`. Require the installed
prompt-contract validator's input SHA-256 to equal `canonical_prompt.md` and
its error count to be zero.

## Execution boundary

The renderer may use only fixed, shell-false, read-only Git queries and the
fixed installed prompt-contract validator. It has no task callback, shell
hook, Codex command, nested-session launcher, arbitrary import, patch path,
publication path, or prompt-authored execution path.

Do not require a Bash submission wrapper, environment variable, JSON primary
prompt, inline marker, pre-existing user-created file, or second Codex session.
Do not refresh governance bindings automatically during preflight.

## Blocking handoff

When blocked, retain the generated report and ask for clarification only after
reporting the diagnostic IDs. Do not perform task-specific repository action.
An existing output root is `PROMPT-PREFLIGHT-E012` and must not be overwritten
or resumed.
