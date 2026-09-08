---
name: correction-lib-diagnostics-execution-copy
description: Validate and materialize a bounded, provenance-rich diagnostics copy of explicitly selected UTF-8 files using exact hashes, optional exact-count literal replacements, strict path containment, destination absence, secret blocking, and atomic publication. Use when a diagnostic or execution setup must be copied for inspection or later separately authorized work. Never execute, submit, retry, resume, or render commands for copied files.
---

# Diagnostics execution copy

Prepare an inspectable copy and provenance package without changing the source
or authorizing execution. The controlling workflow applies applicable live
workspace governance; this helper owns only copy safety and artifact consistency.

## Boundary

Never execute, import, source, submit, monitor, retry, resume, overwrite,
delete, clean, or render a command for a copied file. Never infer permission
from skill availability or destination existence. A later independently
authorized workflow may consume the copy through any compatible capability.

Use only explicit strict-UTF-8 regular files. Reject directory expansion,
binary or other encodings, symlinks, hard links, special files, arbitrary
templates, regex, shell filters, callbacks, redaction, and implicit reruns.

## Create a manifest

Start from `assets/copy_manifest_template.json`. Read
`references/copy_schema.json` before authoring or diagnosing a manifest.
Require:

- one to eight absolute source roots;
- absolute source paths and relative normalized destination paths;
- expected lowercase SHA-256 and expected Git state per entry;
- `exact_copy` with no transforms, or `declared_text_transform` with one to
  sixteen ordered `exact_text_replacement` operations;
- positive limits no greater than 64 entries, 16 MiB per file, and 64 MiB
  total;
- the fixed non-execution boundary and additive secret policy.

Built-in secret path, filename, and PEM-header checks cannot be weakened.
Manifest path-component additions are blocking and additive.

## Validate or materialize

Use the workspace wrapper, non-login shell, and pinned interpreter:

```bash
/users/apiccine/work/correction-lib/codex-run.sh \
  /bin/bash --noprofile --norc -c \
  'cd /users/apiccine/work/correction-lib &&
   /users/apiccine/work/miniconda3/envs/clib-env/bin/python \
   .agents/skills/correction-lib-diagnostics-execution-copy/scripts/prepare_execution_copy.py \
   --format human "$1"' copy \
  <manifest.json>
```

Add `--validate-only` to perform complete source, hash, transformation,
provenance, secret, path, limit, and collision checks without creating any
destination or staging artifact. Use `--format json` for machine-readable
output and `--json-out PATH` only for an explicitly authorized diagnostics
path.

Exit codes:

- `0`: validation or materialization completed;
- `2`: manifest or schema contract error;
- `3`: blocking source, path, type, size, hash, transform, secret, collision,
  provenance, or execution-boundary diagnostic;
- `5`: staging, artifact, reopening, incomplete-preservation, or atomic
  publication failure.

## Safety behavior

The renderer opens source and destination components using descriptor-relative
no-follow operations. It records device and inode, checks source stability
during the read including link count, and reopens every source before
publication. Immediately before publication, every source must still be a
regular file with exactly one hard link, the same device and inode, the same
size and mode class, and the same SHA-256. It performs all preflight checks
before staging.

Final `<destination_root>/<copy_id>` must be absent. The renderer creates one
exclusive sibling staging directory, writes normalized `0640` or `0750` files,
reopens all copied bytes and generated artifacts, rechecks sources, and
publishes the staging directory with a Linux atomic no-replace primitive.
Renderer version `1.0.1` fails closed when that primitive is unavailable and
never falls back to a replacing rename. A post-staging failure is preserved as
`.incomplete_<copy_id>_<nonce>` with blocking validation evidence when
possible; it is never resumed or classified as complete.

## Review output

Reopen:

```text
copy_manifest.resolved.json
copy_inventory.csv
copy_provenance.json
copy_diff.patch
copy_validation.json
materialized/
```

Confirm manifest-order inventory, hashes, sizes, modes, Git state, warnings,
transformation counts, and execution boundary agree. `copy_diff.patch` must be
zero bytes for an all-exact copy. For transformed entries it must contain a
timestamp-free, entry-ordered unified diff.

State plainly that the copy was prepared but no copied file was executed and
that the helper did not authorize execution.
