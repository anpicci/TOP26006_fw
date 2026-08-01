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
5. Reopen all eight generated artifacts and inspect blocking diagnostics,
   repairs, hashes, semantic-value records, validator input hash, and state.
6. Continue this same Codex session only when the complete immutable readiness
   package validates and reaches `ready_for_same_session_execution` with zero
   blocking errors.
7. Before the first task-specific action, have orchestration call the script's
   complete-package readiness assertion with the current visible-source hash,
   expected prompt ID, and expected output root. Record
   `execution_started` in orchestration evidence; the renderer never executes
   the task.

Canonical invocation:

```text
/users/apiccine/work/correction-lib/codex-run.sh /bin/bash --noprofile --norc -c '<pinned-python> .agents/skills/correction-lib-codex-prompt-preflight/scripts/preflight_prompt.py --workspace-root /users/apiccine/work/correction-lib --output-root <relative_absent_output_root> --continuation <yes|no|unknown> --evidence-round <yes|no|unknown> --user-run-handoff <yes|no|unknown> <relative_source_capture.md>'
```

Use argument arrays when invoking this command. Never pass prompt content to a
shell or use it as an executable, module, callback, import, command, or argv
fragment.

## Ownership and ambiguity

Read `references/section_ownership.json` for the complete version-1.0.2
registry, aliases, diagnostic catalog, conservative unknown-section policy,
closed branch tuples, and state transitions.
Read `references/preflight_schema.json` when diagnosing generated artifacts.

- Preserve the complete prompt preamble and every author-owned or safe unknown
  section exactly and in source order. Never rewrite, summarize, normalize
  internally, or complete them.
- Preserve every shared-structured source section in `authored_prompt.md` and
  its semantic-value manifest. Render each validated author-intent value once
  in canonical metadata; never copy legacy skill-owned values into executable
  canonical authority.
- Generate only skill-owned sections. Replace every fixed live observation and
  authored skill-owned section in the canonical prompt and record the
  discrepancy. Never use an authored branch, baseline, or permission value as
  a live observation.
- Require one fenced `text` mapping and only blank lines or restricted inert
  comments in every shared section. Reject prose or a second fence.
- Reject duplicate structured semantic paths, malformed indentation, stale
  repository baselines, incomplete branch tuples, transport-identity
  requirements, and unknown normative or capability-bearing sections.
- Block unknown permission-bearing sections and semantic ambiguity before any
  task-specific repository action.

## Outputs

Require relative source and output paths. Open the workspace diagnostics root
once and traverse, read, stage, reopen, validate, and publish through held
no-follow directory descriptors. Reject identity changes and every lexical,
resolved, symlink, rename, or replacement escape. A canonical prompt is
written only after semantic classification passes. A successful preflight
writes exactly:

```text
authored_prompt.md
canonical_prompt.md
section_manifest.json
shared_value_manifest.json
prompt_contract_validation.json
preflight_state.json
preflight_report.md
readiness_binding.json
```

Reopen and schema-validate every artifact before publishing success. For the
preamble and every author-owned section require matching source and canonical
SHA-256 and `preserved_exactly: true`. Require the installed prompt-contract
validator's input SHA-256 to equal `canonical_prompt.md` and its error count to
be zero. `readiness_binding.json` binds the exact artifact inventory, current
source and canonical hashes, validator result, governance, versions, state
path, prompt ID, workspace, and output identity. A standalone state file never
authorizes task action.

## Execution boundary

The renderer may use only fixed, shell-false, read-only Git queries and the
fixed installed prompt-contract validator. It has no task callback, shell
hook, Codex command, nested-session launcher, arbitrary import, patch path,
publication path, or prompt-authored execution path.

Do not require a Bash submission wrapper, environment variable, JSON primary
prompt, inline marker, pre-existing user-created file, or second Codex session.
Do not refresh governance bindings automatically during preflight.

## Blocking handoff

When blocked, retain diagnostic evidence and ask for clarification only after
reporting the diagnostic IDs. A semantic block does not publish an executable
canonical prompt. Do not perform task-specific repository action. An existing
output root is `PROMPT-PREFLIGHT-E012`; path escape is
`PROMPT-PREFLIGHT-E023`; neither may be overwritten, followed, or resumed.
