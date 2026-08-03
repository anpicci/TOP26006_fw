---
name: correction-lib-codex-prompt-preflight
description: Preflight a manually pasted correction-lib Markdown task prompt in the current Codex session before task-specific repository action. Use when the first nonblank line of the visible user message begins with `# Prompt` and a `prompt_id` appears in `Task metadata` or `Metadata and governance`; create a diagnostics-local source capture, validate closed structured authority, render canonical Markdown, publish four observational audit artifacts, and gate only the immediate next phase of the same uninterrupted turn.
---

# Correction-lib Codex prompt preflight

Preflight the visible Markdown prompt without executing its task. Treat complete
live `AGENTS.md` and `CPC.md` as normative and the bundled registry and schema
as frozen executable projections.

## Workflow

1. Read complete live governance and applicable nested governance.
2. Create a regular UTF-8 `authored_prompt_input.md` under an authorized,
   diagnostics-local round directory. The trusted current session creates this
   file exclusively from the normalized visible message.
3. Select an absent diagnostics-relative audit root.
4. Invoke `scripts/preflight_prompt.py` through `codex-run.sh`, a non-login
   shell, and the pinned interpreter:

   ```text
   <wrapper> /bin/bash --noprofile --norc -c '<pinned-python> <script> --workspace-root /users/apiccine/work/correction-lib --source-path <diagnostics-relative-authored_prompt_input.md> --audit-root <diagnostics-relative-absent-root> --continuation <yes|no|unknown> --evidence-round <yes|no|unknown> --user-run-handoff <yes|no|unknown>'
   ```

5. Capture stdout directly. Continue only when that just-completed invocation
   returned exit 0, stdout is canonical Markdown, and the next orchestration
   phase begins immediately in this same uninterrupted turn.
6. Run a complete new preflight after a new message, interruption, resumed or
   new session, or deliberate governance/repository change.

Never place prompt content in argv, environment variables, shell input, an
executable path, imported module, callback, generated command, or nested Codex
session.

## Closed authority

Read `references/section_ownership.json` for `SKR-1.0-CLOSED`. It contains
exactly nine registered shared headings and 67 semantic paths.

- Require one section-body-top-level fenced `text` mapping in every registered
  shared section, with only blank lines or restricted inert HTML comments
  around it.
- Block an unknown heading with a top-level fenced `text` mapping.
- Preserve an unknown heading containing ordinary Markdown or another fence
  language exactly as author-owned prose with zero repository-authority effect.
- Treat block-quoted and list-indented fences as prose.
- Reject duplicate paths and unknown registered paths.
- Derive effective authority from the intersection of live governance,
  validated structured intent, and live capability.

Do not infer authority from natural-language permission phrases. Author prose,
legacy skill-owned metadata, and audit artifacts grant no repository authority.

## Outputs and readiness

Exit 0 writes exactly four observational artifacts:

```text
authored_prompt.md
canonical_prompt.md
preflight_result.json
preflight_report.md
```

Require `authored_prompt.md` to equal the source capture and
`canonical_prompt.md` to equal stdout byte-for-byte. Reopen and validate every
artifact before publishing the absent audit root with Linux
`renameat2(RENAME_NOREPLACE)`. Fail closed on missing/unsupported primitives,
collisions, or publication errors. Never fall back to an ordinary rename.

Audit files do not authorize. Exit 0 plus canonical stdout authorizes only the
immediate next orchestration phase in this uninterrupted turn. There is no
stored authorization capability or post-exit freshness command.

## Execution boundary

Use only fixed shell-false read-only Git observations and the fixed installed
prompt-contract validator. Do not refresh bindings, execute prompt-authored
code, perform task actions, launch Codex, apply patches, publish repositories,
or accept a prompt-supplied executable or validation command.
