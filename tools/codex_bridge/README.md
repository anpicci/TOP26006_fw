# Governed MCP–Codex bridge

This maintained capability transports complete, self-contained, owner-authorized
CPC tasks from Work or Chat to the local Codex CLI and returns their evidence.
It also reads evidence produced by an external CLI without registering a task.
It is a reusable transport adapter, with this directory as its maintained home.
It does not grant authority, decide science, compile governance, accept results,
or replace author review and the executing agent's current-master preflight.

## Execution contract

The service operator selects the coordination Git root, YAML installation
profile, resolved wrapper/interpreter, private state directory, and CLI. The
caller selects the full CPC contract. `governed_task.py` uses the parser/linter,
profile resolver/schema, registry, model vocabulary and governance Git objects
from the current `refs/heads/master`. Their object identities are retained in
the receipt and rechecked before execution and after completion. Unrelated
master advancement is permitted when those identities remain unchanged.
Selected registry modules are also bound. The executor must read all applicable
native/nested instructions; transport admission is mechanical, not a governance
completeness or authorization check.

The authoritative mapping must be one fenced YAML mapping in the full prompt.
Ordinary adopted modes and flat repository-ID/path mappings are transported
subject to the concrete evidence-base and native-control limits below.
`allowed_to_modify` and `read_only` are lists; writable scope entries use
`repository_id:path` strings or singleton `repository_id: path` mappings.
Nested workflows, YAML aliases/anchors/tags/merges, duplicate keys, ambiguous
mapping blocks, unknown modes/profiles, unrecognized permission values and
unsupported CLI modes produce explicit refusals. Unknown documentary fields
are retained. The exact UTF-8 prompt bytes, including prose, remain unchanged
on stdin; the derived contract and model profile are recorded separately.

For orchestration, the outer envelope grants nothing. Each stage's complete
fields, branch/action contract and separate effect map pass unchanged to Codex.
The adapter checks the transport shape and scalar grant ceiling; the executor
must validate exact path/ref intersections, objective gates, stage sequencing,
repair edges and ledgers against current master. The invocation's network and
write capabilities cover possible authorized stages; they never constitute a
stage grant. An absent effect stays absent. Owner-manual production stages are
refused for execution, preserving the manual launch boundary. Prepare such a
handoff through a non-executing documentation contract instead.

One attempt has one caller-selected model/reasoning profile. There is no routing,
resume, fallback, automatic retry or in-attempt switch. CLI mode `ultra` has no
qualified native-exec mapping and is refused explicitly. Runtime model identity
is `not_observable` unless independent runtime evidence establishes it; requested
flags never become proof of runtime identity.
Contracts requiring exact runtime profile agreement are refused when that
proof cannot be observed; a contradictory supplied model_profile is also refused.

Governed invocations request workspace-write with the reserved evidence directory
as `--cd`, independently of the source prompt mode. Source read-only contracts
add no source write roots and use approval policy never. Mutating contracts add
only selected writable source repository roots via `--add-dir` and request the
CLI's automatic approval review (`--approve-for-me`). Invocation-local config
requests exclusion of native default temporary write roots. This permits requested diagnostic
file output without making a source read-only task a coding task. Codex must
read the source workspace's applicable instructions explicitly, since the
invocation workspace is the evidence directory; source paths remain in the
unaltered authored contract. The historical read-only adapter is unchanged.
No task can request danger-full-access,
ignore rules, bypass approvals, change authentication, or replace the installation
wrapper through RPC. The CLI retains project rules. Write roots are filesystem
capabilities, not exact file grants: Codex remains bound to the narrower prompt.
Web search/apps/browser/plugins/hooks stay disabled; separately authorized
outbound shell actions require the task/stage network grant. Disabling those
provider features is not proof of host-wide network isolation. Metadata checks
require the command options consumed by this adapter. The installed CLI version
is recorded as provenance and does not gate admission. Updating Codex does not
require updating a release allowlist. Successful metadata checks establish the
required option surface, not native runtime or sandbox behavior; an actual
unsupported option, failed command or protocol failure remains an error.
Local help/config-name inspection and simulated-Codex argv assertions establish
routing only. Native sandbox enforcement, effective approval behavior, binary
materialization by native Codex and live Work/Chat sessions need separate
qualification; no such success or failure is inferred from simulation. Exact
final-message capture can transport a report, but cannot manufacture arbitrary
diagnostic binaries if the native executor cannot write them.

## MCP interface, limits and recovery

All tools have strict object schemas. `request_id` is 1–64 ASCII characters,
letters/digits/underscore/hyphen, with an alphanumeric first character.

| Tool | Arguments and result |
| --- | --- |
| `server_info` | `{probe_execution?: false}`; access availability and limits without CLI; explicit true probes execution readiness, no inference/login check |
| `submit_task` | `{request_id, prompt}`; full strict UTF-8 prompt, maximum 2,097,152 bytes; exact-byte reservation and asynchronous receipt |
| `prompt_upload` | `{request_id, total_bytes, sha256}`; reserve size/digest, read received byte count; no execution |
| `prompt_chunk` | `{request_id, offset, data_base64}`; contiguous 1–24,576 decoded bytes, at most 32,768 base64 characters; exact duplicate chunks are idempotent |
| `finalize_content` | `{request_id}`; opaque exact-byte publication, fixed destination, no execution or semantic parsing |
| `finalize_prompt` | `{request_id}`; compatible UTF-8 adapter to the same publisher |
| `submit_uploaded_task` | `{request_id}`; verify complete size, SHA-256 and strict UTF-8, then use the ordinary submission path |
| `task_status` | `{request_id}`; persisted lifecycle and measured state; may reconcile bookkeeping, never launches |
| `task_output` | `{request_id, stream?, offset?, limit?}`; legacy result/events/stderr text view, byte pagination, default 8,192 and maximum 32,768 bytes |
| `task_artifacts` | `{request_id, offset?, limit?}`; allowlisted artifact manifest, item pagination, default/maximum 100 items |
| `task_artifact` | `{request_id, artifact_id, offset?, limit?}`; base64 bytes, exact identity/size, whole-file and page SHA-256; default 8,192 and maximum 32,768 bytes |
| `evidence_manifest` | `{directory, paths?, offset?, limit?, expected_manifest_id?}`; recursive inventory or explicit selected file set relative to one directory under profile `evidence_root`; default/maximum 100 items, same selection and manifest identity required after the first page |
| `evidence_file` | `{directory, path, expected_size_bytes, expected_sha256, offset?, limit?}`; lossless file bytes without a task; default 8,192 and maximum 32,768 bytes |

Direct submission now allows prompts beyond R6's 32,768-byte limit, up to the
2 MiB per-request memory/transaction budget. Chunk upload avoids relying on an
unverified client message limit. Split UTF-8 sequences across chunks are valid;
validation occurs after reconstruction. Oversize, incomplete, changed, invalid
UTF-8 and mismatched digest inputs are refused without spawning. Backend RPC
accepts at most 12,591,104 bytes including JSON escaping. The Node backend reply
buffer uses that same bound. Each serial CLI metadata probe (`--version`, then
`exec --help`) has a **300-second** startup allowance. Backend RPC timeout is
**900 seconds**; the maintained stdio test client waits **930 seconds**. These
finite operating budgets are independent of the asynchronous worker and do not
establish the cause of earlier startup delays. Metadata errors retain the phase
and argv, timeout or OS errno/filename or nonzero return code, and up to 2,048
characters of captured stderr where applicable. A metadata timeout leaves CLI
compatibility unestablished. A timeout is an ambiguous reply, never a failed
submission proof: retain the same ID and query status. No new ID may bypass an
active or uncertain task.

SQLite transactions reserve the task before spawning, and a process-owned lock
serializes workers across adapter restarts. Same ID/same bytes returns the original
receipt; changed bytes conflict even when a configuration has since broken.
`STARTING` and `RUNNING` are active; an orphan becomes `OUTCOME_UNKNOWN` and
blocks new execution. `COMPLETED`, `FAILED`, `START_FAILED` and legacy
`TIMED_OUT` remain distinct. Governed workers have no hidden ten-minute timeout
or 16 MiB log cap. The authored contract must supply relevant resource/time
bounds; Codex enforces those governed bounds. The legacy plain-text path retains
its explicit 600-second worker limit for R6 compatibility. Unknown outcomes
require separately authorized readback/recovery; no recovery API edits task state
or relaunches a task automatically.

The old state directory and seven-column `tasks` table are preserved. Additive
upload tables do not rewrite old rows. Existing R6 receipts, output streams,
reports and patches remain readable without binding a currently valid prompt,
profile or governance installation. No old state, source or deployed release is
migrated, deleted or overwritten by maintaining this directory.

## Evidence and artifact identity

For each governed task the installation profile resolves `evidence_root`.
An explicit authored `evidence_root` selects an existing custom root, absolute
or relative to the task's `workspace_root`. Its exact resolved identity must
match: parent traversal, symlink aliases and unavailable roots are refused.
The explicit destination describes authorized diagnostic output, not source,
production/storage or stage effects. Author and executor retain output-scope
review. Arbitrary per-file layouts (`report_path`, `patch_path`,
`evidence_directory`) are refused with a precise layout boundary; they are not
silently ignored or mapped to another destination.
Admission reserves `evidence_root/prompt_id/`, or the first unused
`prompt_id_rerun_00N/`, without overwriting a collision. The actual paths enter
invocation-local transport context, not the prompt bytes or a persistent user
configuration. Directory device/inode identity is checked at collection.
Codex writes the real `prompt_id_report.md`; when it supplies only
a final message, its exact final-message bytes are published as that report.
The bridge does not invent the report's conclusions or certify its completeness.
If neither an executor report nor a final-message file exists, the report stays
absent, with `report_producer: absent` and an evidence finding. A real empty
executor file remains distinct from absence. Process exit and completion/failure
events are recorded before collection; secondary collection errors are recorded
separately and prevent completion without replacing the original process facts.

The default `patch_producer: codex` requires the canonical
`prompt_id_worktree_diff.patch` from the executor. A present file is preserved
byte for byte. An authored `patch_producer: codex_or_host` additionally permits
host production of an absent patch from the measured tracked before/after task
delta, including task commits, executable modes and binary changes. This is a
producer choice, never a source-write or other effect grant. No transport
instruction tells Codex to omit a patch required by the authored prompt.
Absent required patches, incompatible kinds/bases and mismatches prevent
COMPLETED; existing conflicting bytes remain recoverable when regular files.
Reports and patch filenames are canonical, with no overwrite of foreign files,
symlinks, special files or a preexisting bridge-bookkeeping path.

Both executor and host patches are validated by the actual `finish_evidence`
consumer. It applies the measured and supplied patches to the same admission
baseline in private Git indexes/object storage and compares complete resulting
tree identities (paths, modes, symlinks, binary bytes and deletions). Equivalent
context/hunk encodings and compatible `-p1`/`-p2` conventions are accepted without
requiring byte equality. Multi-repository supplied patches need the existing
`# repository_id: ID` sections. No selected source index/ref/object is written
by this check. Supported kinds are `prompt_local` and `empty_no_changes`;
cumulative/touched-file patches require a separately bound comparison base and
are refused by this adapter, rather than mislabeled as prompt-local.

Clean baselines use the native Git binary diff from the initial HEAD;
explicitly permitted dirty baselines use private frozen tracked postimages.
Private baseline import hashes raw bytes without Git clean filters or EOL
conversion; `patch_consumer_checks` records the actual baseline and result trees.
Dirty-baseline patches retain native before_N/after_N labels to avoid rewriting
arbitrary filenames or patch content; apply those repository sections with
`git apply -p2`. Clean-baseline sections use the ordinary `-p1`. The measured
`patch_strip_components` map records the validated consumer convention in the
receipt/bookkeeping. Bookkeeping records the actual report/patch producer,
baseline, validation method and evidence findings. `executor_file` identifies
the file-present branch, not OS-level attribution of its writer.
Multiple repository patches have explicit repository-ID section comments and
must be applied separately in those independent repositories. The bridge never
stages nested repositories in coordination history. Untracked foreign files are
not inventoried or adopted. Coding tasks must commit new files for them to be
included in the tracked delta. HEAD, branch, refs, index identities and tracked
state are captured separately. Read-only state drift and observed writes outside
the outer file scope prevent successful completion; the bridge preserves all
observed effects and does not roll them back. Exact stage grants, commit closure,
foreign index/ref preservation and report semantics still require executor and
reviewer checks. An empty content patch can be legitimate for a ref-only action;
its snapshots must be reviewed for that action.

Canonical evidence includes bridge bookkeeping, distinct from the Codex report,
with actual FOLD/scp, prompt identity and before/after state. Needed artifacts
must be written inside the reserved evidence folder. Regular private files are
frozen into a task-only manifest and reopened to verify bytes, size and digest.
Symlinks/hardlinks are rejected. Artifact IDs are allowlist members, never paths.
Copies and integrity scans stream through a bounded memory buffer. Page requests
rehash the selected frozen file before reading that page; very large files may
therefore require substantial I/O within the explicit backend RPC timeout.
Second authorized sessions connected to the same service/state can recover them;
the host/service's access control owns session authorization. This is not a
multi-tenant authorization server. Legacy/active logs are labelled unfrozen and
can change; use a stable final manifest for an integrity claim.
When governed collection fails before freezing a manifest, listing and byte-page
reads also expose private regular files in the receipt-bound reserved evidence
directory. These rows carry `evidence_status: partial_unvalidated`; retrieval
does not validate their report or patch semantics. Directory identity and
no-follow component opens bind reads to that reservation. Links, special files,
directory replacement and caller-supplied paths are refused. Legacy history
without governed locators continues to use its existing private-state allowlist.

For lossless recovery, list artifacts, page each chosen ID, base64-decode and
concatenate pages in byte-offset order, then compare exact size and SHA-256.
Do not use the legacy text view for byte identity: split Unicode can display
replacement characters there. A changed frozen artifact fails integrity checks.

## External CLI evidence without a registered task

The ordinary owner workflow is to deposit the Markdown prompt, send its path
to an already active external CLI session, then acquire its diagnostic directory
through `evidence_manifest` and `evidence_file`. That CLI execution has no bridge
task receipt or inferred task status. The optional registered-task launcher below
is a separate route; external evidence does not require it or a new submission.

These readers use AccessInbox and the shared maintained YAML installation resolver in access_only mode, then open only
the explicitly named dossier under its single `evidence_root`. They run before
bridge state initialization: no SQLite connection, state directory creation,
task/upload row, executor, worker lock or CLI metadata probe. The server launcher needs its configured workspace/profile and a working interpreter/wrapper to run Python. Access profile resolution does not require tooling keys or executable tooling, CPC/parser/model-policy objects, CLI metadata, or execution admission. The registry and profile schema remain current-master policy dependencies; access roots and private exclusions are unchanged.
The caller must hold authority for the selected directory; technical access
does not grant application permission to another lane's evidence.

For example, an external session can produce `example_r2/` under `evidence_root`.
The following requests illustrate the protocol (the returned identity is opaque):

```json
{"directory":"example_r2","offset":0,"limit":2}
```

`evidence_manifest` returns `directory`, `manifest_id`, `files` (relative `path`,
`size_bytes`, `sha256`), `total`, `offset`, `next_offset`, `has_more`, `complete`,
`omissions`, `selection_mode` and `manifest_frozen: false`. With no `paths`,
`selection_mode` is `recursive`: all entries are visited, and any unsafe entry
fails the inventory. An empty dossier has zero rows. With `paths`, the mode is
`explicit_files`: only those named files and necessary ancestors are opened;
excluded subtrees, symlinks and special files are not enumerated or read.
The returned `paths` is sorted and canonical, and `total` counts only that set.
For example, a report and package can be acquired despite unrelated raw fixtures:

```json
{"directory":"example_r2","paths":["report.md","change.patch","fixture_evidence.zip"],"offset":0,"limit":2}
```

`paths` must be a nonempty list of unique relative file paths, without globs
or implicit directories. Null, duplicates, traversal, missing or unsafe selected
files fail the entire acquisition; nothing is silently omitted. A file row for
an empty report is:

```json
{"path":"empty_report.md","size_bytes":0,"sha256":"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}
```

Continue at `next_offset` with the same `expected_manifest_id` until `has_more`
is false. It is required for nonzero offsets; it can also guard a fresh offset
zero read. Keep the same `paths` on every page and final recheck; request order
does not matter, but changing the set conflicts with the old identity.
Identity binds directory, selection mode, membership, byte sizes and SHA-256.
Recursive mode binds directory identity/metadata, including empty directories.
Explicit mode binds necessary ancestor inodes, selected parent inodes and file
identity/metadata; unrelated membership or volatile parent-directory metadata
does not invalidate a stable selected set. Replacing a selected parent or file
does. Every manifest page rehashes its full scoped file set in streaming buffers,
retaining metadata rather than whole file bodies.
There is no total dossier/file-size cap. Intrinsic filesystem,
descriptor, transport buffer and existing 900-second RPC limits still apply;
failure returns an error, never an inventory claiming omissions are absent.

Retrieve each row through `evidence_file`, for example:

```json
{"directory":"example_r2","path":"empty_report.md","expected_size_bytes":0,"expected_sha256":"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855","offset":0,"limit":32768}
```

The response has the same `directory`/`path`, actual `size_bytes`/`sha256`,
`encoding: "base64"`, `data`, `offset`, `chunk_size_bytes`, `chunk_sha256`,
`next_offset` and `has_more`. The example returns `data: ""`, zero chunk size,
the empty SHA-256 and `has_more: false`. Exact EOF behaves the same way;
offsets beyond EOF, negative/noninteger offsets and invalid limits are errors.
Unicode split across pages and binary bytes use exactly this route.

Decode every page as bytes, verify its size/hash and contiguous offsets,
concatenate to EOF, verify whole size/hash, then reacquire the manifest with
the original selection and `expected_manifest_id`. Changes to selected membership,
bindings or bytes conflict;
restart acquisition deliberately on the newly observed dossier if authorized.
`complete: true` describes an inventory with no omissions across **all** its
pages within `selection_mode`, not the first page alone, a frozen log or
scientific completeness. The lane chooses which evidence is necessary for
substantive review. Unsafe/unreadable entries in scope fail the entire
inventory explicitly rather than being omitted silently.

On external-reader infrastructure failure (spawn, invalid JSON or interruption),
acquisition is incomplete: preserve already verified bytes and recheck selection,
manifest and file identities before continuing. There is no bridge task ID to
reconcile for an external CLI dossier. Explicit input/conflict errors remain
errors; a missing reader reply does not establish failure of that CLI execution.
Existing task-based recovery still reconciles the true task ID after uncertainty.

Each RPC has fixed process/profile/governance costs. Selection reduces manifest
membership and bytes hashed, but does not eliminate paging costs. A file of B
bytes recovered in pages of P bytes currently requires two full hashes per page,
roughly `2 * B * ceil(B/P)` bytes processed by the hasher, plus transferred bytes
and fixed costs (the empty-file EOF page still runs). This is a code-derived
estimate, not a measurement of latency or physical I/O.

All directory components are opened relative to pinned descriptors from `/`
with no-follow semantics; file reads reuse the existing private regular-file
and streaming-hash primitives. Absolute/empty/dot/traversal paths, symlink
components/targets, hardlinks and special files are refused before content
hashing. Namespace bindings and file/directory metadata are checked again;
file pages rehash after reading the chunk to detect in-place writes.
No report content is interpreted or executed, and the reader writes neither
reports nor shared bridge state. Reads may have ordinary filesystem atime effects.

This is optimistic acquisition with change detection, not an atomic multi-file
snapshot. A change after the last check can always occur; an active log cannot
be called immutable. A dossier claim requires stable manifest membership and
every recovered file tied to its digest. Semantic review of required evidence
remains the reviewer's responsibility.

These APIs were introduced in 4.2.0; explicit selection and external-read
infrastructure recovery extend that implementation locally. Local tests, a separately
deployed service and definitions visible to a particular chat are distinct
layers. Deployment/catalog refresh and real consumer acquisition need separate
authorization and readback; changing this checkout activates none of them.
The registered-task readers retain their original signatures and behavior.

## Optional registered-task deposit and manual launch

The nonexecuting deposit workflow is `prompt_upload` → `prompt_chunk` →
`finalize_prompt({request_id})`. Finalization checks complete size, SHA-256,
strict UTF-8 only. Content is opaque: no CPC mapping or internal task ID is interpreted. It returns
`request_id`, `transfer_id`, absolute `path`, `size_bytes`, `prompt_sha256`,
`state: DEPOSITED`, `duplicate_deposit` and `execution_started: false`.
The reusable task ID inside the bytes is independent of the immutable transfer ID; two transfers may carry the same task. No semantic prompt_id is inferred. Receipts describe this publication only, even when a historical execution shares its ID. This is not admission, owner approval or execution.
Existing MCP submission operations remain available with their existing limits.

The installation workspace determines the only publication root:
`<workspace_root>/reports/prompts/`. ID `example_r2` maps exactly to
`CODEX_PROMPT_example_r2.md`; changed bytes require another immutable transfer ID. The .md extension is a historical transport naming convention, not a content restriction for the opaque core. Neither an
MCP client nor the local command can choose another file path. The original
upload tables remain the identity authority; no ready table, execution row,
worker lock or CLI metadata probe is needed for depositing. A busy worker or
missing CLI therefore does not prevent publication.

Publication uses atomic no-clobber hard linking in an opened directory,
after flushing/fsyncing a private pending file. Symlink directory components, symlink
targets, hardlinks, special files and different existing bytes are refused;
existing content is never overwritten. Equal bytes under the same ID reconcile
by reopening the target against the upload, including after a lost reply just
after publication. No separate ready flag can become stale. The existing state
database transaction serializes publication, independently of the worker lock.
The deterministic pending name is `.<filename>.pending`. An interrupted write
is extended only when its bytes are an exact prefix of the original upload;
conflicting content is preserved and refused. An interruption after linking
can leave two names for the same inode. Finalization rechecks both identities,
exact bytes, owner and link count before retiring only that proven pending
alias; the published file is never rewritten. A launcher refuses the partial
two-link state until finalization reconciles it. Other hardlinks remain refused.
Unsupported atomic linking fails closed, without an overwrite fallback.

In an owner shell, set the **same six installation bindings used by `start.sh`**:
`GLADOS_BRIDGE_WORKSPACE`, `GLADOS_BRIDGE_PROFILE`, `GLADOS_BRIDGE_WRAPPER`,
`GLADOS_BRIDGE_PYTHON`, `GLADOS_BRIDGE_STATE`, `GLADOS_BRIDGE_CODEX`.
Resolve the YAML profile through its wrapper/interpreter with the maintained
resolver (`--profile ... --execution-ready --format yaml`); workspace and
tooling must match it. State and CLI are explicit existing installation inputs,
not a second configuration registry. No tunnel shell, key or API credential is
needed. These are invocation/session bindings, not persistent settings.

From this maintained source directory (or the separately activated release):

```sh
./manual.sh submit example_r2
./manual.sh status example_r2
```

`submit` runs a normal child process using the configured wrapper/interpreter
and governed profile, through `bridge.py --rpc --prompt-file example_r2`.
It reads the deposited regular file once, bounds that snapshot by the original
upload size, checks exact bytes and UTF-8, then hands that in-memory text to
the existing `submit_task`. A later target replacement cannot change stdin.
Admission, CLI checks, busy lock, receipts, asynchronous worker and collector
remain the maintained implementation. A profile or CLI error at launch remains
an error even when deposit succeeded. The JSON `ok` field reports RPC success;
`result.state` reports execution state. The envelope includes the same ID and
an `observe_command`. Returning `STARTING`/`RUNNING` is not completion.

`status` invokes existing `task_status`, never submits, and works without
reloading a later broken admission profile. After a lost reply use that command
with the original ID. Equal duplicate submissions return the original task;
changed bytes conflict. Busy/unknown state requires readback, never a new ID.
Closing the observing shell does not replay or cancel the detached worker.
Existing MCP `task_status`, `task_artifacts` and `task_artifact` work with the
same state and ID for locally launched tasks. Process outcome and collection
outcome stay separate, including failed tasks with partial evidence.

The operator must separately deploy the new sources and refresh the consumer
catalog for the deposit API (introduced in 4.1.0) and external evidence APIs
(introduced in 4.2.0). Updating this checkout
does not update an installed release or register the new tool. Fixtures cover
this flow with simulated execution, not native inference or live service use.

## Local verification and deployment boundary

Run Python only through the wrapper/interpreter resolved by the maintained YAML
profile contract. `-s` disables user-site loading for the invocation and `-B`
avoids bytecode writes. Tests use a separate explicit fixture wrapper and a
simulated Codex executable, plus real temporary Git repositories, serialized
files, and local RPC consumers. They do not infer or execute scientific work.
Standard-library-only workers and task retrieval RPCs use `-S` to skip site
loading; governed admission and external readers keep the configured
environment's existing YAML package. External-reader fixtures need no temporary
Git repository and can retain their private namespaces via
`GLADOS_BRIDGE_READER_FIXTURES` for evidence readback.

```
GLADOS_BRIDGE_TEST_NODE_MODULES=/path/to/existing/node_modules \
  /resolved/command_wrapper /resolved/python -s -B \
  -m unittest discover -s tools/codex_bridge -p 'test_*.py' -v
node --check tools/codex_bridge/server.mjs
```

The optional SDK fixture links an existing dependency directory into its own
private temporary namespace and exercises the actual SDK server with a JSON-RPC
consumer. It removes only that fixture namespace unless retention is selected.
It never installs packages.
Without that existing dependency directory the SDK fixture reports an explicit
skip. Python requires the already configured PyYAML dependency used by the
maintained profile resolver. Dependencies stay pinned in package files; their
presence, account access and native CLI approval behavior require site checks.

This implementation does not deploy, install, restart a tunnel/service, edit
credentials/startup/Codex settings, register a provider catalog, push, publish or
merge. `start.sh` is a local stdio entry point, not the historic tunnel launcher.
After separate deployment authorization, the operator must prepare a fresh
release with these maintained sources and the pinned existing dependencies,
resolve the installation profile through its wrapper/interpreter, and set:

```
GLADOS_BRIDGE_WORKSPACE=/exact/coordination/root
GLADOS_BRIDGE_PROFILE=/exact/local_profile.yml
GLADOS_BRIDGE_WRAPPER=/resolved/command_wrapper
GLADOS_BRIDGE_PYTHON=/resolved/python
GLADOS_BRIDGE_STATE=/existing/private/glados-codex-bridge-r1
GLADOS_BRIDGE_CODEX=/exact/qualified/codex
```

Do not overwrite the R6 package, deployed server or existing state. Point the
separately governed tunnel/service command at the fresh release's `start.sh`.
Do not put credentials in these files or task RPC arguments. The tunnel runtime
credential remains owned by the external site launcher and is filtered from the
adapter/backend/worker environments along with incidental API credentials.

The provider must explicitly refresh/re-register its tool catalog. Relative to
4.1.0, `evidence_manifest` and `evidence_file` are new; the existing ten tools
and their schemas remain. Earlier consumers predating deposit/upload/artifact
support additionally need those releases' schema updates. Local `tools/list`
evidence does not prove Work or Chat registration. After a separately authorized
switch, verify server_info and the two definitions in the actual consumer,
recover an existing external CLI dossier without registering or rerunning it,
and compare complete membership/bytes/hashes before substantive review.
Registered-task checks remain separate and retain the original ID after a
timeout. Neither local tests nor historical unchanged smoke evidence qualify
deployment, live inference, provider limits or owner acceptance.

## Project files and exact local revisions (4.3.0)

The maintained reader exposes six additional read-only tools in governed mode:
`project_roots`, `project_list`, `project_manifest`, `project_file`,
`project_git_tree`, and `project_git_blob`. These operations run before Bridge
construction: no task registration, state directory, SQLite, worker lock, CLI
probe, authentication or executor is needed. A deposited prompt is still only
a prompt. The owner can execute it in an existing CLI, and a lane can read its
original inputs and outputs through these APIs without submitting it again.

`project_roots({})` reports the supported roots, verified repository/common-dir
and linked-worktree bindings, `binding_id`, unavailable roots, and current-master
registry identity. Roots derive from the existing resolved profile: workspace,
evidence, configured active registered repositories (including external paths),
and their locally registered worktrees. No `read_roots` configuration is needed.
A missing or unverified configured repository is unavailable through its parent
workspace too; other verified roots remain usable. Unknown, inactive and known
out-of-scope repositories stay excluded, including `ANDOCS/AN-24-239` through
an ANDOCS/workspace parent. Git internals and private account components such as
`.git`, `.ssh`, `.aws`, `.codex`, `.gnupg`, `.netrc`, `.git-credentials`, `.env`
and `.env.*` cannot be consumed as project files. This component guard is not a
content scanner: callers must use their own mandate and avoid credentials in
otherwise ordinary project filenames. A path outside the reported roots returns
`PROJECT_PATH_NOT_COVERED`; the service never falls back to `/`.
An interrupted worktree discovery query appears in `discovery_limits` while the
verified main checkout remains readable. Nested unregistered checkouts cannot
inherit a parent root's grant; only necessary path ancestors are inspected.

For example, let `root` be the absolute `repo:TOP26006_fw` path returned by
`project_roots`. To discover and acquire documentation outside diagnostics:

```javascript
project_list({ directory: root + '/docs', limit: 100 })
// Continue each directory listing with the same expected_inventory_id and
// next_offset; descend into relevant directories using their exact paths.
project_manifest({ directory: root, paths: ['README.md', 'docs/index.md'] })
// Use actual names discovered above; an absent selected file is an error.
project_file({ path: metadata.requested_path, expected_file_id: metadata.file_id,
               offset: 0, limit: 32768 })
```

Directory listings paginate immediate entry names with `type` equal to `file`,
`directory`, `symlink`, or `special`, and `content_acquired: false`. Completeness
covers those entries only. Symlinks are inventoried without following targets;
this implementation refuses aliases as content, including aliases whose target
would be authorized. Select the target's concrete authorized path instead.
Devices, FIFOs and sockets cannot be opened as ordinary file content. Regular
hardlinks are allowed for project reads. Private task artifact and external
`evidence_*` defaults still require private regular files with one link.

`project_manifest` accepts a nonempty unique explicit selection of relative
paths; it sorts the selection and hashes the original bytes, without enumerating
unselected directories. Each row supplies requested/canonical absolute path,
root binding, ancestor and file identity, size, SHA-256 and `file_id`.
Filesystem identity tuples use decimal strings for device/inode/mode/link-count/
size/timestamps: 64-bit inode and nanosecond values exceed JavaScript's exact
integer range. The same serialized fields therefore reproduce each identity hash.
Continue metadata pages with the same selection and `expected_inventory_id`. A selected
unsafe/missing file fails the operation; there is no successful partial set.
Unrelated sibling changes do not invalidate stable selected files. Root, parent,
file inode, metadata or byte changes invalidate their consumed identity.

`project_file` returns base64, byte `offset`, `next_offset`, `chunk_size_bytes`,
`chunk_sha256`, whole `size_bytes`/`sha256`, `has_more` and `eof`. Empty files and
an offset exactly at EOF return an empty chunk; offsets beyond EOF fail. Decode
and concatenate contiguous pages, verify each chunk, total size/hash and EOF,
then recheck the selected manifest. Unicode split between pages and arbitrary
binary bytes use the same protocol. File hashing is streaming; each page hashes
the whole file before/after reading its bounded chunk. Acquisition therefore
costs proportional to the file bytes times its page count, plus profile/binding
and process startup costs. There is no persistent cache or atomic multi-file
snapshot. The lane chooses the scientifically sufficient set.

For exact unpublished local commit contents:

```javascript
project_git_tree({ repository_id: 'TOP26006_fw',
  revision: '6a99df0fb442731e35451b02cb0dfad7e93fcf02', subtree: 'docs', limit: 100 })
// Freeze the returned full commit. Keep subtree, binding_id and inventory_id.
project_git_tree({ repository_id: 'TOP26006_fw', revision: tree.commit,
  subtree: 'docs', offset: tree.next_offset, expected_binding_id: tree.binding_id,
  expected_inventory_id: tree.inventory_id })
project_git_blob({ repository_id: 'TOP26006_fw', commit: tree.commit,
  path: entry.path, expected_binding_id: tree.binding_id,
  expected_object_id: entry.object_id, offset: 0, limit: 32768 })
```

The tree inventory recursively includes every entry of the exact selected
subtree, including directory trees, symlink blob modes and gitlinks. Empty
`subtree` inventories the whole commit's entry names. It reports requested
revision, resolved full commit, root tree, selected tree, mode/type/object ID and
blob size. `complete` covers entries, never acquired bytes. Exact literal names
are used without pathspec magic or shell interpolation. Gitlinks identify another
commit and cannot be read as blobs; symlink blobs return their stored link text
with `type: symlink_blob`, without following it. Private/excluded paths can be
represented in a tree inventory but cannot be acquired as blob content.

Blob reads require the full frozen commit, repository binding and the object ID
associated with that exact commit/path. The reader checks membership, size,
canonical Git object hash and SHA-256 while streaming; only the requested byte
page enters JSON. HEAD, refs and dirty files do not substitute for commit
contents. Use full commit IDs after resolution: later tree pages reject mutable
revision spellings. There is no arbitrary object-database read, total review
size cap, checkout, fetch, filter, textconv, hook or ref/index mutation. Git
children use sanitized invocation-local configuration/environment, no lazy
fetch/replace objects/optional locks, no allowed transport protocol, and pinned
checkout/git/common directory descriptors. Missing objects fail locally; a
promisor remote does not grant network access. The installed Git must support
these read-only primitives; unsupported commands limit the affected operation.

Errors distinguish invalid input, uncovered/denied/unavailable scope, missing
Git objects/paths, identity conflict/change, and interrupted backend. On
`PROJECT_ACQUISITION_INCOMPLETE`, retain verified bytes, recheck root/repository,
selection/inventory and file/commit/blob identity, and continue only against the
same verified input. There is no task_status, registration or submission to
recover for a project read. Strict MCP schemas reject unknown fields; text and
structured success responses contain the same object.

Implementation and local targeted tests establish source behavior. Installation,
service activation, tunnel/catalog refresh, availability to an actual caller,
owner acceptance and scientific review remain separate results. Updating this
checkout alone does not expose these APIs in a previously installed service.

## Independent access and opaque publication

`prompt_upload` and `prompt_chunk` transfer arbitrary bytes; `finalize_content`
publishes those bytes through the same atomic no-clobber publisher. The legacy
`finalize_prompt` adapter additionally requires UTF-8. Neither path parses CPC,
run configuration or internal task identity. `submit_uploaded_task` and the
manual launcher retain execution admission and strict UTF-8 requirements.
A successful deposit grants no execution authority. Historical tasks are neither
rewritten nor consulted for deposit receipts. Transfer and execution ID namespaces
are independent; execution attempts keep their existing immutable task IDs.

Lost transfer reply: retain the transfer ID and original size/digest; query
`prompt_upload` with that binding, resume only missing contiguous chunks, then
repeat the appropriate finalization. Exact-byte recovery reopens one publication.
Never query an imaginary task or submit to recover a deposit. Read recovery
retains verified pages and repeats only identity-bound acquisition. Execution
recovery continues to use the actual registered task's status.

`server_info` defaults to `execution_readiness: NOT_PROBED`, `cli_compatible: null`
with reader/storage availability established by access configuration, not a CLI
probe. It does not claim successful publication, actual caller exposure, or
owner acceptance. `probe_execution: true` explicitly consumes execution
dependencies and probes CLI metadata; failure affects that readiness claim.
The plain pilot info path and local --check retain their historical probe.

The 2,097,152-byte total limit bounds per-request reconstructed Python bytes,
SQLite chunk retrieval and hashing under the current in-memory transport; it
is independent of semantic prompt lint. The 24,576-byte decoded chunk keeps
base64 at 32,768 characters; MAX_RPC reserves worst-case JSON escaping and
framing, and response buffers share that finite budget. These are service
resource limits, not owner content/authority limits or an unbounded storage grant.

Packaging selects committed files in this directory plus the shared
`tools/resolve_local_profile.py`, installed beside bridge.py as
`resolve_local_profile.py`. Reuse the existing pinned node_modules binding.
The resolver stays owned and tested in tools; the installed copy is a
producer-bound distribution artifact. No duplicate resolver implementation is
maintained here. Source tests and private SDK fixtures package the same input.

Filesystem byte pages additionally compare the returned page with a direct
descriptor read after the final hash, bypassing buffered reads. This catches
same-size page mutations even when filesystem timestamps share one clock tick.
Namespace, whole-file identity and final caller manifest checks remain required;
acquisition is optimistic, not an atomic multi-file snapshot.

Historical execution compatibility fixtures explicitly use the accepted
e308672 producer governance content as test data. This does not make it the
authority for current prompt validation or qualify new task/run execution.
Reader SDK tests continue to bind current master. Set GLADOS_BRIDGE_TEST_RELEASE
to exercise a separately prepared release through its start.sh with private
fixture state; GLADOS_BRIDGE_RETAIN_FIXTURES retains that state and protocol
evidence at an explicitly owned parent. Neither option activates a shared service.


### Portable historical test inputs

When the historical `e308672369d600f933a5a9fefa6de33e58a3f20f` commit is absent,
`GovernedTests.setUpClass` reads the exact 19 setup inputs from
`fixtures/historical_governed/`. Its manifest records the original path, Git
blob ID, size and SHA-256; the loader checks revision, complete membership and
each file's bytes before constructing the isolated historical repository.
The original Git-object route remains available when the pin exists.

These files, including their historical instruction documents and validator,
are compatibility test data. They are not current governance or an invoked
skill. Current-master admission and reader binding keep their existing inputs;
the fixture does not substitute old policy into those checks. No runtime
admission code or original test assertion changes are required for portability.
