---
name: correction-lib-manual-production-handoff
description: Prepare or validate a non-executing correction-lib production handoff with exact commands, resume boundaries, output-collision checks, logging, and evidence-return requirements. Use when Codex has validated a production plan that the user will run manually. Never execute, monitor, retry, or infer production completion.
---

# Manual production handoff

Prepare a user-owned production package from decisions and evidence already
supplied by the user or established by an accepted validation round. This skill
never authorizes or performs production.

## Authority and boundary

Read the complete live workspace-root `AGENTS.md` and `CPC.md` before using the
renderer. Treat them as normative. Treat
`references/handoff_schema.json`, this skill, and generated artifacts as
derived workflow material only.

Never:

- launch, monitor, stop, resume, retry, or inspect production;
- inspect processes, schedulers, Work Queue, logs, output directories, PKLs,
  sidecars, or current command progress;
- infer `completed_valid` from output existence, names, or timestamps;
- invent commands, activation steps, output suffixes, environment variables,
  retry authorization, overwrite policy, qualification evidence, or
  provenance gates;
- place credentials, tokens, private keys, or scheduler identifiers in a
  manifest or generated artifact;
- execute `handoff_wrapper.sh`.

Skill availability does not authorize production execution. A future prompt
must authorize any inspection or execution independently.

## Choose one operation

- `create_handoff_manifest`: copy `assets/handoff_manifest_template.json` and
  fill every decision from the explicit validated plan. Leave nothing implicit.
- `validate_handoff_manifest`: run the renderer against an existing JSON
  manifest and review all diagnostics.
- `render_runbook`: use `--runbook-only`; schema-valid manifests always support
  a runbook, including ambiguous or empty continuation boundaries.
- `render_execution_wrapper`: omit `--runbook-only` only when the requested
  execution set is mechanically safe.
- `render_continuation_wrapper`: mark accepted commands `completed_valid`; the
  renderer retains them in the runbook and excludes them from the wrapper.
- `review_handoff`: explain diagnostics while keeping schema validity separate
  from scientific, operational, and authorization approval.

## Build the manifest

Use argument arrays for commands. Never convert a free-form shell command into
`argv` without resolving and reviewing each argument. Preserve validated
command order exactly.

Read `references/handoff_schema.json` when creating or diagnosing a manifest.
Required decisions include:

- user execution ownership and the exact working-directory mode;
- environment and executable requirements without invented activation;
- explicit command status, expected output identities, and qualification
  evidence;
- fail-closed collision behavior for every output;
- persistent per-command logging or an explicit disabled decision;
- stop-on-first-failure, no-automatic-retry interruption behavior;
- evidence the user must return;
- provenance to record separately from provenance to enforce.

Classify commands only from accepted evidence or explicit user input:

- `completed_valid`: require qualification evidence; omit from execution.
- `pending` and `not_started`: execute in manifest order; every expected output
  must use `must_be_absent`.
- `failed_known`: execute only with `retry_authorized: true` and a nonempty
  `retry_reason`; every expected output must use `must_be_absent`.
- `interrupted_ambiguous`: block wrapper rendering; render a runbook and stop
  for classification.

Only `completed_valid` commands may use `allow_existing_qualified`. Supply both
explicit qualification artifacts for every such output and accepted
qualification evidence for the command. File existence alone is never
qualification. A reusable pre-existing artifact that is an input must not be
modeled as a runnable command's expected output.

Stable output diagnostics:

- `OUTPUT003`: a runnable command uses a collision behavior other than
  `must_be_absent`.
- `OUTPUT004`: a `completed_valid` command uses
  `allow_existing_qualified` without complete command evidence and output
  qualification artifacts.
- `OUTPUT005`: a collision behavior is inconsistent with command status.

## Select a working-directory mode

- `caller_managed`: state the required launch directory in `execution_cwd`;
  generate no `cd`.
- `fixed`: choose explicitly and supply an absolute `execution_cwd`; the
  wrapper changes to it.
- `script_relative`: supply an explicit relative target; the wrapper
  self-locates and changes to that target.

Do not turn recorded branch or commit values into gates. Set
`provenance.enforce.branch` or `provenance.enforce.commit` only when the user
explicitly requests strict enforcement and supplies the corresponding value.

## Validate and render

Use the workspace wrapper, non-login shell, and pinned interpreter:

```bash
/users/apiccine/work/correction-lib/codex-run.sh \
  /bin/bash --noprofile --norc -c \
  'cd /users/apiccine/work/correction-lib &&
   /users/apiccine/work/miniconda3/envs/clib-env/bin/python \
   .agents/skills/correction-lib-manual-production-handoff/scripts/render_handoff.py \
   --output-dir "$1" --format human "$2"' handoff \
  <output_dir> <manifest.json>
```

Add `--runbook-only` whenever a runnable wrapper was not requested or the plan
contains an ambiguous command. Use `--format json` for machine-readable
diagnostics and `--json-out PATH` only for an explicitly selected path.

Exit codes:

- `0`: requested artifacts rendered;
- `2`: manifest validation error;
- `3`: unsafe runnable-wrapper request;
- `4`: governance binding mismatch;
- `5`: output rendering error.

There is no execution option.

## Review generated artifacts

Reopen and inspect:

- `handoff_runbook.md`;
- `handoff_commands.json`;
- `handoff_validation.json`;
- `handoff_wrapper.sh`, when rendered.

Confirm the wrapper:

- uses `set -euo pipefail`;
- contains only the intended non-qualified commands in exact order;
- quotes every argument;
- checks only manifest-declared output identities;
- creates the selected log directory and records command, start/end time, and
  exit code once per command;
- stops on the first nonzero exit;
- contains no deletion, cleanup, automatic retry, undeclared environment
  dependency, unrequested Git gate, or unrequested `cd`.

For renderer version `1.0.1`, `tee_to_console=true` merges stdout and stderr,
displays the merged stream live, and saves it to the command log. This pipeline
does not preserve child TTY detection and may disable or degrade in-place
progress bars. TTY-preserving logging is not supported; it requires a separate
explicit design and implementation round.

Do not execute the wrapper as part of using this skill. Synthetic skill tests
are the only exception and must use inert commands and temporary directories.

## Handoff

Tell the user the required execution directory, artifacts to edit or inspect,
commands excluded as `completed_valid`, commands remaining in order, collision
and logging policies, stop conditions, and evidence to return. State plainly
that Codex did not execute or inspect production.
