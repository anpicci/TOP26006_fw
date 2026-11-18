import { McpServer } from '@modelcontextprotocol/server';
import { StdioServerTransport } from '@modelcontextprotocol/server/stdio';
import { z } from 'zod';
import { execFile } from 'node:child_process';
import { fileURLToPath } from 'node:url';

// Only the tunnel process needs its credential, not this MCP adapter.
delete process.env.CONTROL_PLANE_API_KEY;
const python = process.env.GLADOS_BRIDGE_PYTHON || 'python3';
const backend = fileURLToPath(new URL('./bridge.py', import.meta.url));
const state = process.env.GLADOS_BRIDGE_STATE;
const wrapper = process.env.GLADOS_BRIDGE_WRAPPER;
const prompt = process.env.GLADOS_BRIDGE_PROMPT;
const inbox = process.env.GLADOS_BRIDGE_INBOX;
const profile = process.env.GLADOS_BRIDGE_PROFILE;
const workspace = process.env.GLADOS_BRIDGE_WORKSPACE;
const codex = process.env.GLADOS_BRIDGE_CODEX;
// In-memory reconstruction/SQLite resource budget; not CPC semantics.
const max_prompt = 2097152;
const server = new McpServer({ name: 'glados-codex-bridge', version: '4.3.0' });
const project_methods = ['project_roots', 'project_list', 'project_manifest', 'project_file', 'project_git_tree', 'project_git_blob'];

function rpc(method, args) {
  return new Promise((resolve) => {
    // Profile-based admission/info/external reads need installed YAML.
    // Task bookkeeping and workers skip site initialization.
    const site_flag = profile && ['submit_task', 'submit_uploaded_task', 'finalize_prompt', 'finalize_content', 'server_info', 'evidence_manifest', 'evidence_file', ...project_methods].includes(method) ? '-s' : '-S';
    const argv = [...(wrapper ? [python] : []), site_flag, '-B', backend, ...(state ? ['--state', state] : []),
      ...(prompt ? ['--read-only-prompt', prompt, '--workspace', workspace, '--command-wrapper', wrapper] : []),
      ...(inbox ? ['--read-only-inbox', inbox, '--workspace', workspace, '--command-wrapper', wrapper] : []),
      ...(profile ? ['--governed-profile', profile, '--workspace', workspace, '--command-wrapper', wrapper] : []),
      ...(codex ? ['--codex', codex] : []), '--rpc'];
    const env = { ...process.env };
    for (const key of ['CONTROL_PLANE_API_KEY', 'OPENAI_API_KEY', 'CODEX_API_KEY']) delete env[key];
    const child = execFile(wrapper || python, argv, { env, timeout: 900000, maxBuffer: 6 * max_prompt + 8192 }, (error, stdout, stderr) => {
      if (stderr) process.stderr.write(stderr);
      let response;
      try { response = JSON.parse(stdout); } catch { /* Deliberate generic error below. */ }
      if (error || !response || response.ok !== true) {
        const transfer = ['prompt_upload', 'prompt_chunk', 'finalize_prompt', 'finalize_content'].includes(method);
        const external_read = ['evidence_manifest', 'evidence_file'].includes(method);
        const project_read = project_methods.includes(method);
        resolve({ isError: true, content: [{ type: 'text', text: response?.error ||
          (transfer ? 'TRANSFER_REPLY_UNKNOWN: reconcile prompt_upload and finalization with the SAME transfer ID and exact bytes; no execution was initiated. Never query task_status for a deposit.' : method === 'server_info' ? 'INFO_UNAVAILABLE: repeat information query; no execution initiated.' : project_read ? 'PROJECT_ACQUISITION_INCOMPLETE: backend unavailable or interrupted; preserve verified bytes and recheck root/repository binding, selection, inventory and file/commit/blob identities before continuing.' : external_read ? 'EVIDENCE_ACQUISITION_INCOMPLETE: backend unavailable or interrupted; preserve verified bytes and recheck selection, manifest and file identities before continuing.' :
            'BACKEND_UNAVAILABLE_OR_INTERRUPTED: inspect task_status with the SAME request_id before any new submission.') }] });
        return;
      }
      if (method === 'server_info') {
        response.result.node_version = process.version;
        response.result.mcp_sdk = '@modelcontextprotocol/server 2.4.0';
      }
      resolve({ content: [{ type: 'text', text: JSON.stringify(response.result) }], structuredContent: response.result });
    });
    child.stdin.on('error', () => {}); // Spawn/EPIPE error is reported by the callback.
    child.stdin.end(JSON.stringify({ method, args }));
  });
}

const readOnly = { readOnlyHint: true, destructiveHint: false, openWorldHint: false };
const id = z.string().regex(/^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$/);
server.registerTool('server_info', {
  description: 'Inspect reader/storage configuration independently. CLI readiness is NOT_PROBED unless probe_execution is true; that optional probe uses execution admission dependencies. No inference or login check. Reported configuration and lint create no authorization.',
  inputSchema: z.object({ probe_execution: z.boolean().default(false) }).strict(), annotations: readOnly
}, args => rpc('server_info', args));
server.registerTool('submit_task', {
  description: 'Execute one full self-contained owner-authorized prompt, up to 2097152 strict UTF-8 bytes. Check server_info admission mode first. Governed mode preserves repository IDs, modes, profiles, branch policies, ceilings and separate workflow stage grants. Caller must establish authority and master conformance; lint is mechanical only. Same ID and same bytes look up the original task; changed bytes conflict. On lost reply retain the SAME ID and inspect task_status. Never bypass BUSY/OUTCOME_UNKNOWN with a new ID. No automatic retry, session resume, production launch for execution_owner user, deployment or acceptance. Use chunked upload if the client message limit is smaller.',
  inputSchema: z.object({ request_id: id, prompt: z.string().min(1).max(max_prompt).refine(value => Buffer.byteLength(value, 'utf8') <= max_prompt, 'UTF-8 byte limit exceeded') }).strict(),
  annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: true, openWorldHint: true }
}, args => rpc('submit_task', args));
server.registerTool('task_status', {
  description: 'Read an existing task receipt; may reconcile bridge bookkeeping. Never launch or retry. COMPLETED is not scientific acceptance.',
  inputSchema: z.object({ request_id: id }).strict(), annotations: readOnly
}, args => rpc('task_status', args));
server.registerTool('task_output', {
  description: 'Read paginated result/events/stderr for this task only. No arbitrary file paths. Offset and limit count bytes; a split Unicode character can display a replacement character while source bytes stay intact.',
  inputSchema: z.object({ request_id: id, stream: z.enum(['result', 'events', 'stderr']).default('result'),
    offset: z.number().int().min(0).default(0), limit: z.number().int().min(1).max(32768).default(8192) }).strict(),
  annotations: readOnly
}, args => rpc('task_output', args));

const mutation = { readOnlyHint: false, destructiveHint: false, idempotentHint: true, openWorldHint: false };
server.registerTool('prompt_upload', {
  description: 'Reserve immutable opaque byte transfer identity without execution, independent of task IDs. Bind request_id to byte size and SHA-256, maximum 2097152 bytes. Repeat identically to read received_bytes; changed identity conflicts. Does not authorize execution.',
  inputSchema: z.object({ request_id: id, total_bytes: z.number().int().min(1).max(max_prompt), sha256: z.string().regex(/^[0-9a-f]{64}$/) }).strict(), annotations: mutation
}, args => rpc('prompt_upload', args));
server.registerTool('prompt_chunk', {
  description: 'Append contiguous exact bytes as base64, 1..24576 decoded bytes (at most 32768 base64 characters). offset counts decoded bytes. Identical retry is idempotent; different bytes at an existing offset conflict. UTF-8 may split across chunks. No execution.',
  inputSchema: z.object({ request_id: id, offset: z.number().int().min(0), data_base64: z.string().min(4).max(32768) }).strict(), annotations: mutation
}, args => rpc('prompt_chunk', args));
server.registerTool('submit_uploaded_task', {
  description: 'Verify complete uploaded size, SHA-256 and strict UTF-8, then submit under the same exact-byte contract as submit_task. Uses Codex quota. Caller authority required. Same ID lookup only after an ambiguous reply; never change IDs to retry.',
  inputSchema: z.object({ request_id: id }).strict(), annotations: { ...mutation, openWorldHint: true }
}, args => rpc('submit_uploaded_task', args));
server.registerTool('finalize_prompt', {
  description: 'Deposit the complete uploaded UTF-8 Markdown without execution, CLI probes, worker lock or task reservation. Verify size, SHA-256 and strict UTF-8 only; content is opaque, with no CPC parsing or task-ID inference. Publish CODEX_PROMPT_<request_id>.md under the installation workspace reports/prompts; no client path. Same ID/bytes reconcile; conflicts never overwrite. DEPOSITED authorizes no launch. Owner may later use the local manual command. Retain the same ID after a lost reply.',
  inputSchema: z.object({ request_id: id }).strict(), annotations: mutation
}, args => rpc('finalize_prompt', args));
server.registerTool('finalize_content', {
  description: 'Publish opaque uploaded bytes without execution or text/CPC interpretation. Fixed CODEX_PROMPT_<request_id>.md transport filename under reports/prompts; extension does not constrain contents. Same transfer/bytes reconciles one publication; different bytes refuse. Lost reply: reconcile upload/finalization using SAME transfer and bytes, never task_status or a new task. Receipt transfer_id is not reusable task identity.',
  inputSchema: z.object({ request_id: id }).strict(), annotations: mutation
}, args => rpc('finalize_content', args));
server.registerTool('task_artifacts', {
  description: 'List task-owned artifact identifiers, names, exact sizes and SHA-256 with item pagination. No arbitrary file paths. Available across authorized sessions sharing this service/state. manifest_frozen distinguishes completed snapshots from changing legacy/active logs.',
  inputSchema: z.object({ request_id: id, offset: z.number().int().min(0).default(0), limit: z.number().int().min(1).max(100).default(100) }).strict(), annotations: readOnly
}, args => rpc('task_artifacts', args));
server.registerTool('task_artifact', {
  description: 'Losslessly retrieve an allowlisted task artifact by exact artifact_id. Base64 bytes, byte offsets, whole-file and chunk SHA-256, exact size and has_more. Decode chunks, concatenate, verify size and digest. Text, Unicode and binary share this interface. No filesystem path input.',
  inputSchema: z.object({ request_id: id, artifact_id: z.string().min(1).max(160), offset: z.number().int().min(0).default(0), limit: z.number().int().min(1).max(32768).default(8192) }).strict(), annotations: readOnly
}, args => rpc('task_artifact', args));

const evidence_path = z.string().min(1).refine(value => !value.startsWith('/') && !value.includes('\0') &&
  value.split('/').every(part => part !== '' && part !== '.' && part !== '..'), 'Nonempty relative path required');
const sha256 = z.string().regex(/^[0-9a-f]{64}$/);
server.registerTool('evidence_manifest', {
  description: 'Inventory one authorized external directory relative to profile evidence_root. Optional nonempty unique paths selects only named relative regular private files without enumerating other entries; absent paths retains recursive inventory and unsafe-entry refusal. selection_mode is explicit_files or recursive; complete covers that set, not scientific sufficiency or an atomic snapshot. Keep the same selection and expected_manifest_id for pages and final recheck after size/hash file recovery. Infrastructure errors leave acquisition incomplete: preserve verified bytes, recheck selection/manifest/identities. No task, CLI, lock or state writes. Caller mandate required.',
  inputSchema: z.object({ directory: evidence_path,
    paths: z.array(evidence_path).min(1).refine(paths => new Set(paths).size === paths.length, 'Unique paths required').optional(),
    offset: z.number().int().min(0).default(0),
    limit: z.number().int().min(1).max(100).default(100), expected_manifest_id: sha256.optional() }).strict(),
  annotations: readOnly
}, args => rpc('evidence_manifest', args));
server.registerTool('evidence_file', {
  description: 'Read exact base64 byte pages from one authorized dossier file without a registered task. directory is relative to profile evidence_root; path is relative to that directory. Required expected size/SHA-256 bind each page; changes, links, traversal and special files fail closed. Decode, concatenate, verify whole size/hash, then recheck the manifest. Byte offsets and limits; empty/EOF return an empty chunk, beyond EOF is an error. No execution or state/report writes.',
  inputSchema: z.object({ directory: evidence_path, path: evidence_path,
    expected_size_bytes: z.number().int().min(0), expected_sha256: sha256,
    offset: z.number().int().min(0).default(0), limit: z.number().int().min(1).max(32768).default(8192) }).strict(),
  annotations: readOnly
}, args => rpc('evidence_file', args));

const project_path = z.string().min(2).refine(value => value.startsWith('/') && !value.includes('\0') &&
  value.slice(1).split('/').every(part => part !== '' && part !== '.' && part !== '..'), 'Exact absolute path required');
const object_id = z.string().regex(/^(?:[0-9a-f]{40}|[0-9a-f]{64})$/);
const item_paging = { offset: z.number().int().min(0).default(0), limit: z.number().int().min(1).max(100).default(100),
  expected_inventory_id: sha256.optional() };
const byte_paging = { offset: z.number().int().min(0).default(0), limit: z.number().int().min(1).max(32768).default(8192) };
server.registerTool('project_roots', {
  description: 'Discover configured project/evidence roots, verified active registered repositories and linked worktrees, binding identities and unavailable surfaces. Current master registry exclusions and private account/Git paths apply through parent roots. No arbitrary root, task, CLI probe, state or execution. Technical reach never supplies caller authority.',
  inputSchema: z.object({}).strict(), annotations: readOnly
}, args => rpc('project_roots', args));
server.registerTool('project_list', {
  description: 'Paginate immediate directory names in a bound project root. Entries distinguish file/directory/symlink/special and scope_allowed; no target or file bytes acquired. No symlink following. Complete covers directory entries, not recursive bytes or scientific sufficiency. Keep expected_inventory_id after first page; recheck after acquisition.',
  inputSchema: z.object({ directory: project_path, ...item_paging }).strict(), annotations: readOnly
}, args => rpc('project_list', args));
server.registerTool('project_manifest', {
  description: 'Acquire metadata/size/SHA-256/file_id for an explicit unique relative file selection beneath an absolute project directory. Hardlinks allowed; links/specials refused as content. Sorted selection and ancestor/file/root identity bound; unrelated sibling changes harmless. Complete covers selected metadata, not file bytes; optimistic, no atomic snapshot. Keep selection and expected_inventory_id for pages and final recheck.',
  inputSchema: z.object({ directory: project_path,
    paths: z.array(evidence_path).min(1).refine(paths => new Set(paths).size === paths.length, 'Unique paths required'),
    ...item_paging }).strict(), annotations: readOnly
}, args => rpc('project_manifest', args));
server.registerTool('project_file', {
  description: 'Read lossless base64 byte pages of an absolute bound project file using file_id from project_manifest. Verify chunk offsets/size/hash, whole size/hash and EOF, then recheck manifest. Changed root, parent, inode or bytes conflicts. Links are unconsumed objects; specials refused before open. No task/state/CLI. On infrastructure failure preserve verified bytes and recheck binding and identity.',
  inputSchema: z.object({ path: project_path, expected_file_id: sha256, ...byte_paging }).strict(), annotations: readOnly
}, args => rpc('project_file', args));
server.registerTool('project_git_tree', {
  description: 'Resolve a local revision of a configured verified active repository to exact commit/tree and inventory a literal subtree recursively (including tree, symlink blob and gitlink identities). Empty subtree selects whole tree names. Complete covers entries, not bytes. Use returned full commit as revision, same subtree, binding_id and expected_inventory_id on subsequent pages/final check; advancing refs never changes frozen objects. No checkout/fetch/filter/textconv/task/state.',
  inputSchema: z.object({ repository_id: z.string().min(1), revision: z.string().min(1),
    subtree: z.union([z.literal(''), evidence_path]).default(''), expected_binding_id: sha256.optional(),
    ...item_paging }).strict(), annotations: readOnly
}, args => rpc('project_git_tree', args));
server.registerTool('project_git_blob', {
  description: 'Read exact lossless local blob byte pages at full commit/path, requiring repository binding_id and expected object ID from tree inventory. Verify membership and Git object hash plus SHA-256; worktree/HEAD changes irrelevant. Symlink blob returns link text without following; gitlink is not blob. No lazy fetch, replace objects, checkout, task or execution. Preserve verified bytes and recheck identities after infrastructure failure.',
  inputSchema: z.object({ repository_id: z.string().min(1), commit: object_id, path: evidence_path,
    expected_binding_id: sha256, expected_object_id: object_id, ...byte_paging }).strict(), annotations: readOnly
}, args => rpc('project_git_blob', args));

await server.connect(new StdioServerTransport());
