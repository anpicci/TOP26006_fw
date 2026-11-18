// Real SDK server, local JSON-RPC consumer. Execution fixtures simulate Codex;
// external-reader fixtures forbid it. No tunnel/network.
import { spawn, spawnSync } from 'node:child_process';
import { createInterface } from 'node:readline';
import { readFileSync, writeFileSync, readdirSync, statSync, existsSync, unlinkSync, renameSync } from 'node:fs';
import { join } from 'node:path';
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';

const fixture = JSON.parse(readFileSync(process.argv[2], 'utf8'));
const sha = data => createHash('sha256').update(data).digest('hex');
function identity(value) {
  const sorted = v => Array.isArray(v) ? v.map(sorted) : v !== null && typeof v === 'object' ?
    Object.fromEntries(Object.keys(v).sort().map(key => [key, sorted(v[key])])) : v;
  return sha(Buffer.from(JSON.stringify(sorted(value)).replace(/[^\x00-\x7f]/g,
    character => '\\u' + character.charCodeAt(0).toString(16).padStart(4, '0'))));
}
const env = { ...process.env, GLADOS_BRIDGE_WORKSPACE: fixture.repo,
  GLADOS_BRIDGE_PROFILE: fixture.profile, GLADOS_BRIDGE_STATE: fixture.state,
  GLADOS_BRIDGE_PYTHON: fixture.python, GLADOS_BRIDGE_WRAPPER: fixture.wrapper,
  GLADOS_BRIDGE_CODEX: fixture.codex, CONTROL_PLANE_API_KEY: 'synthetic_key',
  OPENAI_API_KEY: 'synthetic_key', CODEX_API_KEY: 'synthetic_key' };
delete env.GLADOS_BRIDGE_PROMPT;
delete env.GLADOS_BRIDGE_INBOX;
let sequence = 0;
const lifecycle = [];

async function connect(server = fixture.server) {
  const command = fixture.entrypoint || process.execPath;
  const child = spawn(command, fixture.entrypoint ? [] : [server], { env, stdio: ['pipe', 'pipe', 'pipe'] });
  const process_record = { pid: child.pid, server };
  lifecycle.push(process_record);
  const waiting = new Map();
  let errors = '';
  child.stderr.on('data', data => { errors += data.toString(); });
  const lines = createInterface({ input: child.stdout });
  lines.on('line', line => {
    const message = JSON.parse(line);
    if (waiting.has(message.id)) {
      const pending = waiting.get(message.id);
      waiting.delete(message.id);
      clearTimeout(pending.timer);
      message.error ? pending.reject(new Error(JSON.stringify(message.error))) : pending.resolve(message.result);
    }
  });
  child.on('exit', code => {
    for (const pending of waiting.values()) {
      clearTimeout(pending.timer);
      pending.reject(new Error(`server exited ${code}: ${errors}`));
    }
  });
  function request(method, params = {}) {
    const id = ++sequence;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error(`test RPC timeout: ${method}: ${errors}`)), 930000);
      waiting.set(id, { resolve, reject, timer });
      child.stdin.write(JSON.stringify({ jsonrpc: '2.0', id, method, params }) + '\n');
    });
  }
  await request('initialize', { protocolVersion: '2025-11-25', capabilities: {}, clientInfo: { name: 'local_fixture', version: '1' } });
  child.stdin.write(JSON.stringify({ jsonrpc: '2.0', method: 'notifications/initialized' }) + '\n');
  return { request, close: async () => {
    lines.close();
    child.stdin.end();
    if (child.exitCode === null) child.kill('SIGTERM');
    await new Promise(resolve => child.exitCode === null ? child.once('exit', resolve) : resolve());
    Object.assign(process_record, { terminal: true, exit_code: child.exitCode, signal: child.signalCode });
  } };
}

let client;
async function call(name, args = {}) {
  return client.request('tools/call', { name, arguments: args });
}
function result(response) {
  assert.notEqual(response.isError, true, response.content?.[0]?.text);
  return response.structuredContent;
}

async function capabilities(catalog) {
  const calls = [];
  const request = async (name, args = {}) => {
    const response = await call(name, args);
    calls.push({ name, args, response });
    return response;
  };
  try {
    assert.ok(catalog.tools.some(t => t.name === 'finalize_content'));
    const info = result(await request('server_info'));
    assert.equal(info.execution_readiness, 'NOT_PROBED');
    assert.equal(info.cli_compatible, null);
    const roots = result(await request('project_roots'));
    assert.ok(roots.roots.length);
    const inventory = result(await request('project_manifest', { directory: fixture.repo, paths: ['payload.txt'] }));
    const file = inventory.files[0];
    const page = result(await request('project_file', { path: file.requested_path, expected_file_id: file.file_id }));
    assert.deepEqual(Buffer.from(page.data, 'base64'), readFileSync(file.requested_path));
    assert.equal(sha(Buffer.from(page.data, 'base64')), page.sha256);
    for (const [request_id, bytes] of [
      ['ordinary', Buffer.from('ordinary document without CPC')],
      ['binary', Buffer.from([0, 255, 254, 128, 10])],
      ['transfer_a', Buffer.from('```yaml\nprompt_id: reusable\n```\n```yaml\nrun: separate\n```')],
      ['transfer_b', Buffer.from('```yaml\nprompt_id: reusable\n```\n```yaml\nrun: separate\n```')]
    ]) {
      const binding = { request_id, total_bytes: bytes.length, sha256: sha(bytes) };
      assert.equal(result(await request('prompt_upload', binding)).execution_started, false);
      result(await request('prompt_chunk', { request_id, offset: 0, data_base64: bytes.toString('base64') }));
      const receipt = result(await request('finalize_content', { request_id }));
      assert.equal(receipt.execution_started, false);
      assert.equal(receipt.transfer_id, request_id);
      assert.equal(receipt.prompt_id, undefined);
      assert.deepEqual(readFileSync(receipt.path), bytes);
      assert.equal(receipt.size_bytes, bytes.length);
      assert.equal(receipt.prompt_sha256, sha(bytes));
      assert.equal(result(await request('finalize_content', { request_id })).duplicate_deposit, true);
      assert.equal((await request('prompt_upload', { ...binding, sha256: '0'.repeat(64) })).isError, true);
    }
    assert.equal((await request('finalize_prompt', { request_id: 'binary' })).isError, true);
    assert.equal((await request('submit_task', { request_id: 'unauthorized', prompt: 'ordinary document' })).isError, true);
    console.log(JSON.stringify({ capabilities: 'local SDK; missing execution tooling; no inference', calls }));
  } finally {
    if (fixture.observations) writeFileSync(fixture.observations, JSON.stringify(calls));
  }
}

async function external_evidence(catalog) {
  const calls = [];
  const request = async (name, args = {}) => {
    const response = await call(name, args);
    calls.push({ name, args, response });
    return response;
  };
  function inputs(root, prefix = '') {
    return readdirSync(root).sort().flatMap(name => {
      const path = join(root, name);
      return statSync(path).isDirectory() ? inputs(path, prefix + name + '/') :
        [{ path: prefix + name, data: readFileSync(path), mtime: statSync(path).mtimeMs }];
    });
  }
  const selection = fixture.paths ? { paths: fixture.paths } : {};
  const original = fixture.paths ? fixture.paths.map(path => ({ path,
    data: readFileSync(join(fixture.directory, path)), mtime: statSync(join(fixture.directory, path)).mtimeMs })) :
    inputs(fixture.directory);
  try {
    for (const name of ['evidence_manifest', 'evidence_file']) {
      const tool = catalog.tools.find(tool => tool.name === name);
      assert.ok(tool, name);
      assert.equal(tool.annotations.readOnlyHint, true);
      assert.equal(tool.inputSchema.additionalProperties, false);
    }
    assert.deepEqual(catalog.tools.find(t => t.name === 'evidence_file').inputSchema.required,
      ['directory', 'path', 'expected_size_bytes', 'expected_sha256']);
    assert.ok(catalog.tools.find(t => t.name === 'evidence_manifest').inputSchema.properties.paths);
    const rows = [];
    let offset = 0, identity;
    while (true) {
      const page = result(await request('evidence_manifest', { directory: 'external', offset, limit: 2,
        ...selection, ...(identity ? { expected_manifest_id: identity } : {}) }));
      assert.equal(page.selection_mode, fixture.paths ? 'explicit_files' : 'recursive');
      if (fixture.paths) assert.deepEqual(page.paths, [...fixture.paths].sort());
      assert.equal(page.complete, true);
      assert.deepEqual(page.omissions, []);
      identity ??= page.manifest_id;
      assert.equal(page.manifest_id, identity);
      rows.push(...page.files);
      offset = page.next_offset;
      if (!page.has_more) break;
    }
    assert.deepEqual(rows.map(row => row.path).sort(), original.map(row => row.path).sort());
    // A second actual adapter process recovers files from the same profile,
    // with no registered task or shared state directory.
    await client.close();
    client = await connect();
    for (const row of rows) {
      const chunks = [];
      let offset = 0;
      while (true) {
        const page = result(await request('evidence_file', { directory: 'external', path: row.path,
          expected_size_bytes: row.size_bytes, expected_sha256: row.sha256, offset, limit: 32767 }));
        const chunk = Buffer.from(page.data, 'base64');
        assert.equal(page.offset, offset);
        assert.equal(page.chunk_size_bytes, chunk.length);
        assert.equal(page.chunk_sha256, sha(chunk));
        chunks.push(chunk);
        offset = page.next_offset;
        if (!page.has_more) break;
      }
      const bytes = Buffer.concat(chunks);
      assert.equal(bytes.length, row.size_bytes);
      assert.equal(sha(bytes), row.sha256);
      assert.deepEqual(bytes, original.find(item => item.path === row.path).data);
    }
    result(await request('evidence_manifest', { directory: 'external', ...selection, expected_manifest_id: identity }));
    const binding = { directory: 'external', path: rows[0].path,
      expected_size_bytes: rows[0].size_bytes, expected_sha256: rows[0].sha256 };
    for (const [name, args] of [
      ['evidence_manifest', { directory: '' }],
      ['evidence_manifest', { directory: '../outside' }],
      ['evidence_manifest', { directory: '/tmp' }],
      ['evidence_manifest', { directory: 'external', limit: 101 }],
      ['evidence_manifest', { directory: 'external', request_id: 'fake' }],
      ['evidence_manifest', { directory: 'external', offset: 1 }],
      ['evidence_manifest', { directory: 'external', paths: [] }],
      ['evidence_manifest', { directory: 'external', paths: null }],
      ['evidence_manifest', { directory: 'external', paths: 'report.md' }],
      ['evidence_manifest', { directory: 'external', paths: ['report.md', 'report.md'] }],
      ['evidence_manifest', { directory: 'external', paths: ['../outside'] }],
      ['evidence_file', { directory: 'external', path: 'report.md' }],
      ['evidence_file', { ...binding, path: '../outside' }],
      ['evidence_file', { ...binding, limit: 32769 }],
      ['evidence_file', { ...binding, offset: -1 }],
      ['evidence_file', { ...binding, expected_sha256: '0'.repeat(64) }],
    ]) {
      const response = await request(name, args);
      assert.equal(response.isError, true, JSON.stringify({ name, args, response }));
    }
    for (const item of original) assert.deepEqual(readFileSync(join(fixture.directory, item.path)), item.data);
    if (!fixture.paths) assert.deepEqual(inputs(fixture.directory), original);
    writeFileSync(join(fixture.directory, 'added'), 'concurrent membership');
    const changed = await request('evidence_manifest', { directory: 'external', ...selection,
      offset: 2, expected_manifest_id: identity });
    if (fixture.paths) {
      assert.equal(result(changed).manifest_id, identity);
      const conflict = await request('evidence_manifest', { directory: 'external', paths: [rows[0].path],
        expected_manifest_id: identity });
      assert.equal(conflict.isError, true);
      assert.match(conflict.content[0].text, /MANIFEST_CONFLICT/);
    } else {
      assert.equal(changed.isError, true);
      assert.match(changed.content[0].text, /MANIFEST_CONFLICT/);
    }
    unlinkSync(join(fixture.directory, 'added')); // Exact test-owned input only.
    assert.equal(existsSync(fixture.state), false);
    console.log(JSON.stringify({ transport: 'actual local MCP SDK server; two stdio clients',
      files: rows.map(({ path, size_bytes, sha256 }) => ({ path, size_bytes, sha256 })),
      state_directory_created: existsSync(fixture.state), executor: 'never invoked; nonexistent executable' }));
  } finally {
    // Preserve original responses even if an assertion fails.
    writeFileSync(fixture.observations, JSON.stringify({ catalog, calls }, null, 2));
  }
}

async function adapter_errors(catalog) {
  const calls = [];
  try {
    for (const [name, args] of [
      ['evidence_manifest', { directory: 'external', paths: ['report.md'] }],
      ['evidence_file', { directory: 'external', path: 'report.md', expected_size_bytes: 0, expected_sha256: sha(Buffer.alloc(0)) }],
      ...(fixture.project_reader ? [
        ['project_roots', {}],
        ['project_list', { directory: fixture.directory }],
        ['project_manifest', { directory: fixture.directory, paths: ['empty'] }],
        ['project_file', { path: join(fixture.directory, 'empty'), expected_file_id: '0'.repeat(64) }],
        ['project_git_tree', { repository_id: 'topeft', revision: fixture.first_commit }],
        ['project_git_blob', { repository_id: 'topeft', commit: fixture.first_commit, path: 'docs/empty',
          expected_binding_id: '0'.repeat(64), expected_object_id: '0'.repeat(40) }],
      ] : []),
      ['task_status', { request_id: 'existing_fixture_only' }],
    ]) {
      const response = await call(name, args);
      calls.push({ name, args, response });
      assert.equal(response.isError, true);
      const text = response.content[0].text;
      if (name.startsWith('project_')) {
        assert.match(text, /PROJECT_ACQUISITION_INCOMPLETE/);
        assert.match(text, /preserve verified bytes.*binding.*identities/);
        assert.doesNotMatch(text, /task_status|request_id|submission|registration|synthetic_key|Traceback/);
      } else if (name.startsWith('evidence_')) {
        assert.match(text, /EVIDENCE_ACQUISITION_INCOMPLETE/);
        assert.match(text, /preserve verified bytes.*selection, manifest and file identities/);
        assert.doesNotMatch(text, /task_status|request_id|submission|registration|synthetic_key|Traceback/);
      } else {
        assert.match(text, /task_status with the SAME request_id/);
      }
    }
    assert.equal(existsSync(fixture.state), false);
    console.log(JSON.stringify({ adapter_failure: fixture.adapter_errors, responses: calls.length,
      state_directory_created: existsSync(fixture.state) }));
  } finally {
    writeFileSync(fixture.observations, JSON.stringify({ catalog, calls }, null, 2));
  }
}

async function project_reads(catalog) {
  const calls = [], acquisitions = [];
  const preserve = () => {
    writeFileSync(fixture.observations + '.pending', JSON.stringify({ catalog, calls, acquisitions }, null, 2));
    renameSync(fixture.observations + '.pending', fixture.observations);
  };
  const request = async (name, args = {}) => {
    const response = await call(name, args);
    calls.push({ name, args, response });
    preserve();
    if (response.structuredContent) assert.deepEqual(JSON.parse(response.content[0].text), response.structuredContent);
    return response;
  };
  async function recover(name, args, original) {
    const pages = [], chunks = [];
    let offset = 0;
    while (true) {
      const page = result(await request(name, { ...args, offset, limit: 32767 }));
      const chunk = Buffer.from(page.data, 'base64');
      assert.equal(page.offset, offset);
      assert.equal(page.next_offset, offset + chunk.length);
      assert.equal(page.chunk_size_bytes, chunk.length);
      assert.equal(page.chunk_sha256, sha(chunk));
      chunks.push(chunk); pages.push(page);
      offset = page.next_offset;
      if (!page.has_more) break;
    }
    const data = Buffer.concat(chunks);
    assert.deepEqual(data, original);
    assert.equal(pages.at(-1).sha256, sha(data));
    assert.equal(pages.at(-1).size_bytes, data.length);
    assert.equal(pages.at(-1).eof, true);
    acquisitions.push({ method: name, args, original_base64: original.toString('base64'), pages });
    preserve();
  }
  try {
    for (const name of ['project_roots', 'project_list', 'project_manifest', 'project_file', 'project_git_tree', 'project_git_blob']) {
      const tool = catalog.tools.find(tool => tool.name === name);
      assert.ok(tool, name);
      assert.equal(tool.annotations.readOnlyHint, true);
      assert.equal(tool.inputSchema.additionalProperties, false);
    }
    const roots = result(await request('project_roots'));
    for (const root of roots.roots.filter(row => row.available)) {
      const { binding_id, ...binding } = root;
      assert.equal(identity(binding), binding_id, 'lossless root metadata identity');
    }
    assert.ok(roots.roots.some(row => row.repository_id === 'topeft' && row.available));
    let listing = result(await request('project_list', { directory: fixture.directory, limit: 100 }));
    const entries = [...listing.entries];
    while (listing.has_more) {
      listing = result(await request('project_list', { directory: fixture.directory, limit: 2,
        offset: listing.next_offset, expected_inventory_id: listing.inventory_id }));
      entries.push(...listing.entries);
    }
    assert.equal(entries.find(row => row.name === 'link').type, 'symlink');
    const paths = ['雪.md'];
    let meta = result(await request('project_manifest', { directory: fixture.directory, paths, limit: 1 }));
    const inventory = meta.inventory_id, files = [...meta.files];
    for (const row of files) {
      const { file_id, path, ...binding } = row;
      assert.equal(identity(binding), file_id, 'lossless file metadata identity');
      assert.ok(row.file_signature.every(value => typeof value === 'string'));
    }
    while (meta.has_more) {
      meta = result(await request('project_manifest', { directory: fixture.directory, paths: [...paths].reverse(),
        offset: meta.next_offset, limit: 1, expected_inventory_id: inventory }));
      files.push(...meta.files);
    }
    await client.close();
    client = await connect();
    for (const row of files) await recover('project_file', { path: row.requested_path, expected_file_id: row.file_id },
      readFileSync(row.requested_path));
    result(await request('project_manifest', { directory: fixture.directory, paths, expected_inventory_id: inventory }));
    let tree = result(await request('project_git_tree', { repository_id: 'topeft', revision: fixture.first_commit,
      subtree: 'docs', limit: 100 }));
    const rows = [...tree.entries], tree_id = tree.inventory_id;
    assert.equal(identity(tree.repository), tree.binding_id, 'lossless Git repository identity');
    while (tree.has_more) {
      tree = result(await request('project_git_tree', { repository_id: 'topeft', revision: tree.commit, subtree: 'docs',
        offset: tree.next_offset, limit: 2, expected_inventory_id: tree_id, expected_binding_id: tree.binding_id }));
      rows.push(...tree.entries);
    }
    for (const row of rows.filter(row => row.path === 'docs/雪.md')) {
      const canonical = spawnSync('git', ['--no-replace-objects', '-C', join(fixture.directory, '..'),
        'cat-file', 'blob', row.object_id], { env: { PATH: process.env.PATH, GIT_NO_LAZY_FETCH: '1',
          GIT_OPTIONAL_LOCKS: '0', GIT_ALLOW_PROTOCOL: '' } });
      assert.equal(canonical.status, 0);
      await recover('project_git_blob', { repository_id: 'topeft', commit: tree.commit, path: row.path,
        expected_binding_id: tree.binding_id, expected_object_id: row.object_id }, canonical.stdout);
    }
    for (const [name, args] of [
      ['project_roots', { extra: true }],
      ['project_list', { directory: '/' }],
      ['project_git_tree', { repository_id: 'unregistered', revision: 'HEAD' }],
    ]) assert.equal((await request(name, args)).isError, true, name);
    const evidence = result(await request('evidence_manifest', { directory: 'external', paths: ['report.md'] }));
    const row = evidence.files[0];
    const page = result(await request('evidence_file', { directory: 'external', path: row.path,
      expected_size_bytes: row.size_bytes, expected_sha256: row.sha256 }));
    const evidence_original = readFileSync(join(fixture.directory, '../../evidence/external/report.md'));
    assert.deepEqual(Buffer.from(page.data, 'base64'), evidence_original);
    acquisitions.push({ method: 'evidence_file', args: { directory: 'external', path: row.path },
      original_base64: evidence_original.toString('base64'), pages: [page] });
    assert.equal(existsSync(fixture.state), false);
    console.log(JSON.stringify({ project_reader: 'actual SDK; separate clients', files: files.length,
      git_entries: rows.length, acquisitions: acquisitions.length, state_created: false }));
  } finally {
    preserve();
  }
}
try {
  client = await connect();
  const catalog = await client.request('tools/list');
  if (fixture.transfer_error) {
    const observations = [];
    for (const name of ['prompt_upload', 'finalize_content', 'server_info']) {
      const args = name === 'prompt_upload' ? { request_id: 'lost', total_bytes: 3, sha256: sha(Buffer.from('abc')) } :
        name === 'finalize_content' ? { request_id: 'lost' } : {};
      const reply = await call(name, args);
      assert.equal(reply.isError, true);
      const text = reply.content[0].text;
      assert.ok(text.startsWith(name === 'server_info' ? 'INFO_UNAVAILABLE' : 'TRANSFER_REPLY_UNKNOWN'), text);
      assert.ok(!text.includes('inspect task_status'), text);
      observations.push({ name, reply });
    }
    console.log(JSON.stringify({ transfer_errors: observations }));
  } else if (fixture.capabilities) {
    await capabilities(catalog);
  } else if (fixture.adapter_errors) {
    await adapter_errors(catalog);
  } else if (fixture.project_reader) {
    await project_reads(catalog);
  } else if (fixture.external_evidence) {
    await external_evidence(catalog);
  } else {
  for (const name of ['submit_task', 'prompt_upload', 'prompt_chunk', 'finalize_prompt', 'submit_uploaded_task', 'task_artifacts', 'task_artifact']) {
    assert.ok(catalog.tools.some(tool => tool.name === name), name);
  }
  const info = result(await call('server_info'));
  assert.equal(info.backend_rpc_timeout_ms, 900000);
  assert.equal(info.max_prompt_bytes, 2097152);
  assert.equal(info.admission_mode, 'governed_contracts');
  const bytes = Buffer.from(fixture.prompt + '雪€🦊'.repeat(4000));
  assert.ok(bytes.length > 32768);
  const request_id = 'mcp_fixture';
  result(await call('prompt_upload', { request_id, total_bytes: bytes.length, sha256: sha(bytes) }));
  for (let offset = 0; offset < bytes.length; offset += 24575) {
    result(await call('prompt_chunk', { request_id, offset, data_base64: bytes.subarray(offset, offset + 24575).toString('base64') }));
  }
  const deposit = result(await call('finalize_prompt', { request_id }));
  assert.equal(deposit.state, 'DEPOSITED');
  assert.equal(deposit.execution_started, false);
  assert.equal(deposit.size_bytes, bytes.length);
  assert.equal(deposit.prompt_sha256, sha(bytes));
  assert.deepEqual(readFileSync(deposit.path), bytes);
  assert.equal((await call('task_status', { request_id })).isError, true);
  assert.equal(result(await call('finalize_prompt', { request_id })).duplicate_deposit, true);
  // Same installation bindings, but no tunnel credentials in this owner shell.
  const localEnv = Object.fromEntries(Object.entries(env).filter(([key]) =>
    ['HOME', 'PATH', 'TMPDIR'].includes(key) || key.startsWith('GLADOS_BRIDGE_')));
  const local = spawnSync(join(fixture.server, '..', 'manual.sh'), ['submit', request_id],
    { env: localEnv, encoding: 'utf8', timeout: 90000 });
  assert.equal(local.status, 0, local.stderr + local.stdout);
  assert.equal(JSON.parse(local.stdout).ok, true, local.stdout);
  let receipt;
  for (let i = 0; i < 180; i++) {
    receipt = result(await call('task_status', { request_id }));
    if (!['STARTING', 'RUNNING'].includes(receipt.state)) break;
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  assert.equal(receipt.state, 'COMPLETED', JSON.stringify(receipt));
  assert.deepEqual(readFileSync(join(fixture.state, request_id, 'received.bin')), bytes);
  await client.close();
  client = await connect(); // Separate client/server process and local state readback.
  writeFileSync(fixture.profile, 'broken profile after completion');
  assert.equal(result(await call('submit_task', { request_id, prompt: bytes.toString('utf8') })).duplicate_request, true);
  const conflict = await call('submit_task', { request_id, prompt: bytes.toString('utf8') + 'changed' });
  assert.equal(conflict.isError, true);
  assert.match(conflict.content[0].text, /ID_CONFLICT/);
  const listing = result(await call('task_artifacts', { request_id }));
  const row = listing.artifacts.find(item => item.name === 'bytes_雪.bin');
  const chunks = [];
  let offset = 0;
  while (true) {
    const page = result(await call('task_artifact', { request_id, artifact_id: row.artifact_id, offset, limit: 32767 }));
    const data = Buffer.from(page.data, 'base64');
    assert.equal(sha(data), page.chunk_sha256);
    chunks.push(data);
    offset = page.next_offset;
    if (!page.has_more) break;
  }
  const artifact = Buffer.concat(chunks);
  assert.equal(artifact.length, row.size_bytes);
  assert.equal(sha(artifact), row.sha256);
  assert.deepEqual(artifact, readFileSync(join(receipt.evidence_directory, 'bytes_雪.bin')));
  writeFileSync(join(receipt.evidence_directory, 'consumer_recovered.bin'), artifact);
  assert.equal((await call('task_artifact', { request_id, artifact_id: '../../auth.json' })).isError, true);
  console.log(JSON.stringify({ status: 'passed', transport: 'local MCP stdio through actual SDK server',
    codex: 'simulated', prompt_bytes: bytes.length, artifact_bytes: artifact.length,
    artifact_sha256: row.sha256, second_client: 'separate process, same service state',
    provider_catalog: 'unverified; only local tools/list observed' }));
  }
} finally {
  if (client) await client.close();
  if (fixture.lifecycle) writeFileSync(fixture.lifecycle, JSON.stringify(lifecycle));
}
