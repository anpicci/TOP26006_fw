# Deliver a task and recover its evidence on Glados

Use this project-specific connection when an authorized researcher needs to
place a complete task on Glados, have the owner execute it in the already open
external Codex CLI, and recover originals for review. The introductory synthetic
exercises do not require this service. A public clone supplies neither private
diagnostics nor an operational connection.

## Prepare the complete delivery

Follow [manual authoring](write_a_prompt_manually.md) and
[prompt validation](validate_a_prompt_before_execution.md) under current
[CPC](../../CPC.md). Preserve the complete document: explicitly delimited reusable
task bytes and the author's complete run configuration outside those boundaries.
Transfer preserves bytes; it neither parses nor authorizes their instructions.
The author supplies the concrete model/reasoning pair. Before starting, the
owner applies it through the maintained controls of the already open CLI.
Reading a document does not change the session's model or reasoning settings.

Resolve the installation through the [profile procedure](configure_your_local_profile.md).
Check the relevant service binding, exposed tools and their current schemas.
`server_info` without an execution probe reports access configuration:
`execution_readiness: NOT_PROBED`, null CLI metadata such as `cli_compatible`
and `codex_version`, and `error: null` mean the CLI was deliberately not probed.
They are compatible with successful reading and depositing. `reader_available`
and `storage_available` describe configuration; the responses to actual operations
establish their success. Request `probe_execution: true` only when execution
readiness is relevant. Reading/depositing needs no universal CLI-ready gate,
authentication exercise, restart or new canary. Version `4.3.0` alone does not
identify this release; use bindings, capabilities and schemas.

The maintained technical interface is `tools/codex_bridge/README.md` and
`tools/codex_bridge/server.mjs` in the producer checkout on Glados. The capability
separation described here is sourced at full producer commit
`49341411d4854a855c74220742819215303ac6aa`. These local sources may be absent from
a public clone; obtain them through authorized project/Git access when exact
syntax matters. They own the interface details; this page teaches the manual
route. Automatic execution of new task/run deliveries is not qualified by the
accepted reader/deposit evidence.

## Deposit unchanged bytes and retain the receipt

A **receipt** is the returned record of an operation. **Byte identity** means
agreement of the original bytes' exact size and SHA-256, including whitespace
and encoding. Preserve those bytes before transferring them.

1. Call `prompt_upload` with `request_id`, `total_bytes` and lowercase `sha256`
   computed from the complete delivery. This reserves an immutable transfer and
   reports `received_bytes`. The request ID identifies the transfer; it need not
   equal the reusable document's internal `prompt_id` or any execution identity.
2. Send `prompt_chunk` with the same `request_id`, `offset` and `data_base64`.
   Encode slices of the original bytes as base64. Offsets count **decoded bytes**,
   not characters or base64 positions. Append contiguous slices from the reported
   received position, without gaps. A UTF-8 sequence may cross chunk boundaries.
3. Call `finalize_content` with the same `request_id`. It publishes opaque bytes.
   `finalize_prompt` remains the compatible UTF-8 adapter; neither operation
   interprets CPC or launches execution.
4. Preserve and inspect the final `DEPOSITED` receipt. Verify its concrete path,
   `transfer_id`/`request_id`, `size_bytes` and `prompt_sha256` against your preserved input and
   verify `execution_started: false`. A complete transfer with no execution is
   the intended result of this step.

Consult current schemas for limits. The documented producer permits up to
2,097,152 total bytes, chunks of up to 24,576 decoded bytes (32,768 base64
characters), and file pages up to 32,768 bytes. These are transport properties,
not permanent limits on scientific files/jobs/resources or effect grants.
Its request ID schema permits 1–64 ASCII letters, digits, underscores or hyphens,
starting with a letter or digit. The fixed destination uses
`reports/prompts/CODEX_PROMPT_<transfer_id>.md`; that transport name and extension
do not prove the content is a prompt. The caller does not select an arbitrary
destination or overwrite an existing conflicting file.

## Give the owner the concrete path

Return the verified receipt and its actual path directly to the owner. The owner
applies the supplied run configuration, then pastes the following message into
the already open CLI, replacing the illustrative locator with the receipt's
concrete path. This is a teaching example, not an attestation of a real deposit
or a completed runnable instruction:

```text
Leggi ed esegui integralmente il mandato contenuto in:
/illustrative/glados/workspace/reports/prompts/CODEX_PROMPT_example_transfer.md

Procedi fino al risultato autorizzato, rispettando scope, controlli runtime, riuso dei risultati validi e condizioni di stop del documento.
```

Execution remains a separately authorized action with runtime preflight. This
ordinary route uses no second CLI session, `manual.sh submit/status`, fictitious
registration, `submit_task` or `submit_uploaded_task`. Communications and reports
for manual forwarding go directly to the owner; deposit them only when their
consumer and mandate require it.

## Select and recover original evidence

A **manifest** is the selected file inventory, with identities and integrity
metadata. Select the API by the source you actually need:

| Source | Acquisition route and identity |
| --- | --- |
| External CLI dossier under the resolved `evidence_root` | `evidence_manifest` then `evidence_file`; directory relative to that root, file path relative to the dossier |
| Authorized project file | `project_roots`, then relevant `project_list`/`project_manifest` and `project_file`; retain root binding, selection and `file_id` |
| Exact local Git revision | `project_git_tree` then `project_git_blob`; retain repository binding, full commit and expected blob object ID |
| Actual bridge-managed execution | `task_status` on its real executable `request_id`, then `task_artifacts` and `task_artifact` for allowlisted originals |

An external CLI run does not automatically appear in the bridge catalog. Its
transfer ID or internal prompt ID is not a bridge execution receipt. Read its
dossier by path; do not register or relaunch it to make reports accessible.
`task_output` is a text view and cannot replace lossless original recovery.

For a dossier, keep the same `directory` and explicit `paths` selection (or the
same recursive selection) across manifest pages. Retain `expected_manifest_id`
after the first page. Read the complete selected inventory, then bind each
`evidence_file` request to `expected_size_bytes` and `expected_sha256` from it.
For project files, discover configured roots and repository/worktree bindings,
respect exclusions, inventory the selected members, then pass `expected_file_id`
to `project_file`. A listed name alone does not acquire its bytes.

Manifest offsets count inventory items; file offsets count bytes. Decode each
base64 page, verify its offset, decoded size and page digest, concatenate only
contiguous verified pages, and verify the reconstructed file's total size and
whole-file digest. Follow pagination to completion, including EOF/`has_more`
semantics. Recheck the complete inventory with the same selection and identities
after acquiring mutable files. A changed binding, membership or content requires
reconciling that resource; do not silently splice new bytes into old pages.

For Git reads, bind the exact repository, full commit, path, binding ID and
expected object ID using the tree result and blob schema. Reconstruct original
blob bytes and verify the Git object ID with the repository's object hash over
`blob <byte_length>` followed by a NUL byte and those original bytes. Hashing a
JSON reserialization is not Git blob verification.

A complete selected manifest establishes coverage of that selection, not
scientific sufficiency or an atomic snapshot of multiple files. A frozen task
artifact manifest (`manifest_frozen`) differs from observed stable mutable
files. Preserve successful pages after an infrastructure failure. Request
attachments or a tarball only when appropriate authorized access cannot supply
the necessary originals; a path absent from a public clone can still be valid
on Glados.

## Recover at the affected boundary

| Observation | Safe next action |
| --- | --- |
| Upload, chunk or finalization reply lost | Keep the same transfer ID, total bytes and digest. Repeat identical `prompt_upload` to reconcile `received_bytes`; resume only the missing range or repeat idempotent `finalize_content`. Never use a new ID, changed bytes, overwrite, submit or `task_status` to resolve a transfer. Exact-byte conflicts cannot be repaired by relabelling them. |
| File read interrupted | Preserve verified pages; recheck the same selection, resource binding/identity and manifest, then resume valid missing pages. Changed files must be reconciled before reconstructing them. |
| Execution outcome uncertain | Obtain authorized readback of the existing execution and outputs under their real identity. Transfer recovery grants no executable retry or production action. |
| `mcp_initialization_required`, timeout or unavailable root | Record the specific access gap and retain valid evidence. This does not prove a missing file or invalid result and grants no restart/reconfiguration. Reconcile binding and identity before resuming the affected read. `NOT_PROBED` with null error is a different, intentional information state. |

For broader diagnosis use [common stops](diagnose_common_stops.md) and the
[continuation guide](prepare_a_continuation.md); their authority boundaries
continue to apply.

## Review the result and its limits

Use [review returned evidence](review_returned_evidence.md) against the exact
mandate, run configuration and materially required originals. State inherited
claims separately from what you personally read completely or partially.
Checksums establish integrity, not understanding or scientific correctness.
Successful reading does not qualify automatic task/run execution. A failed or
partial execution can still contain usable evidence; preserve and assess its
supported claims within scope.

Keep execution, collection, validation, independent review and acceptance
separate under the [evidence states reference](../reference/evidence_and_task_states.md).
Inspect actual images before visual claims; a planned Mermaid diagram is not
observed execution. Required review informs the responsible person's bounded
acceptance decision and does not decide scientific acceptance.
