# Validate a prompt before execution

Use this guide to mechanically lint a **completed** research-task prompt before dispatch. It complements a semantic reread; it cannot grant authority.

## Author validation and runtime state

This procedure concerns author/pre-dispatch validation when the final prompt
file is available to its author. The author should still lint the filled final
Markdown before dispatch. An executor receiving the task as prompt text does
not need to search for, reconstruct, or request a local `CODEX_PROMPT*.md` copy
merely to prove its own dispatch.

Runtime validation inspects the observable live dependencies required by the
task, such as current governance and repository state. A prompt-file path or
byte identity is a runtime input only when that file is explicitly supplied
as an input to the task. Author prompt-file lint and live-state checks answer
different questions; neither substitutes for the other.

## Before you start

Read the live [validator instructions](../../.agents/skills/correction-lib-prompt-contract/SKILL.md), [CPC.md](../../CPC.md), [AGENTS.md](../../AGENTS.md), registry and native policy. Resolve `wrap`, `python_env`, and `checkout` from the local profile. Use a filled prompt Markdown path, not an unresolved [template](../../templates/bounded_change_prompt.md).

## Procedure

1. Run human output with the maintained interface:

   ```sh
   "$wrap" /bin/bash --noprofile --norc -c \
     'cd "$1" && "$2" .agents/skills/correction-lib-prompt-contract/scripts/validate_prompt.py --format human "$3"' \
     prompt_lint "$checkout" "$python_env" "$prompt_path"
   ```

2. For structured evidence, repeat with `--format json` in the same invocation pattern. Use `--json-out PATH` only for an explicitly chosen absent output path.
3. Read exit code and each error/warning. Code 0 means the supported mechanical/internal checks passed; 2 is CLI/schema input error, 3 prompt mechanical/consistency error, 4 output collision/write failure. Correct the prompt or local invocation and rerun.
4. Adversarially reread the exact prompt against the research lead's mandate, branch applicability, repository scope, effects, stop gates, and evidence requirements.

## Verify the result

The validator output identifies `results.mechanical_validity`, `results.internal_consistency`, and `governance_completeness: not_assessed`. Record the exact prompt identity and reread result before dispatch.

## Stop instead of proceeding if...

Errors remain, required live policy is unreadable, or the mandate and prompt disagree. Validator PASS = mechanical support. Validator PASS != governance completeness, authorization, branch applicability, or scientific correctness.

## Generic example

A completed prompt for one synthetic note is linted in human and JSON modes, then compared with live branch and the research lead's mandate.

## What this does not establish

Mechanical PASS cannot prove governance completeness, authorization, branch applicability, or scientific correctness.
