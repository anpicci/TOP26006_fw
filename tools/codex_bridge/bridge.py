#!/usr/bin/env python3
"""MCP -> bounded, asynchronous Codex exec pilot. Linux, Python >=3.9; standard library only."""
import argparse
import base64
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import sqlite3
import subprocess
import sys
import threading
import time
import traceback

from repository_task import RepositoryTask, ReadOnlyInbox, governance, snapshot
from artifacts import (begin_evidence, finish_evidence, artifact_page, regular_bytes,
                       regular_reader, file_identity, stream_identity,
                       evidence_sources, partial_evidence_reader)

VERSION = "4.3.0"
ACTIVE = ("STARTING", "RUNNING", "OUTCOME_UNKNOWN")
DISABLED = ("shell_tool", "apps", "browser_use", "computer_use", "multi_agent", "multi_agent_v2", "plugins", "hooks")
TIMEOUT = 600
MAX_PROMPT = 2 * 1024 * 1024  # Bounded in-memory reconstruction/SQLite transaction budget.
MAX_RPC = 6 * MAX_PROMPT + 8192  # Worst-case JSON escaping, not UTF-8 truncation.
ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z")


def child_environment():
    # Do not forward the tunnel key or an incidental API credential to Codex.
    keep = {"HOME", "PATH", "USER", "LOGNAME", "SHELL", "LANG", "LC_ALL", "TERM", "TMPDIR", "CODEX_HOME", "SSL_CERT_FILE", "SSL_CERT_DIR", "HTTPS_PROXY", "HTTP_PROXY", "NO_PROXY", "PYTHONDONTWRITEBYTECODE"}
    return {k: v for k, v in os.environ.items() if k in keep}


def check_id(value):
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        raise ValueError("request_id must be 1-64 ASCII letters, digits, underscore or hyphen; first character alphanumeric")


class Bridge:
    def __init__(self, state, codex=None, task=None, wrapper=None, inbox=None):
        self.root = Path(state).expanduser().absolute()
        if self.root.is_symlink():
            raise ValueError("state directory cannot be a symlink")
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        if self.root.stat().st_uid != os.getuid() or self.root.stat().st_mode & 0o077:
            raise ValueError("state directory must belong to this user and have permissions 0700")
        self.root = self.root.resolve()
        self.codex = str(Path(codex or shutil.which("codex") or "/nonexistent/codex").absolute())
        self.task = task
        self.inbox = inbox
        self.wrapper = wrapper
        self.model = task.model if task else os.environ.get("GLADOS_CODEX_MODEL", "")
        with self.db() as db:
            db.execute("CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, digest TEXT NOT NULL, prompt TEXT NOT NULL, state TEXT NOT NULL, created REAL NOT NULL, updated REAL NOT NULL, receipt TEXT NOT NULL)")
            db.execute('CREATE TABLE IF NOT EXISTS uploads (id TEXT PRIMARY KEY, digest TEXT NOT NULL, size INTEGER NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS chunks (id TEXT NOT NULL, offset INTEGER NOT NULL, data BLOB NOT NULL, PRIMARY KEY(id,offset))')

    @contextlib.contextmanager
    def db(self):
        db = sqlite3.connect(self.root / "tasks.sqlite3", timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA synchronous=FULL")
        try:
            yield db
            db.commit()
        finally:
            db.close()

    def lock(self, name):
        fd = os.open(self.root / name, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BaseException:
            os.close(fd)
            raise
        return fd

    def update(self, request_id, state, **fields):
        with self.db() as db:
            row = db.execute("SELECT receipt FROM tasks WHERE id=?", (request_id,)).fetchone()
            receipt = json.loads(row[0])
            receipt.update(fields)
            db.execute("UPDATE tasks SET state=?,updated=?,receipt=? WHERE id=?", (state, time.time(), json.dumps(receipt), request_id))

    def preflight(self):
        results = {}
        def bounded_stderr(value):
            if isinstance(value, bytes):
                value = value.decode('utf-8', errors='replace')
            value = value or ''
            return json.dumps(value[:2048] + (' [truncated]' if len(value) > 2048 else ''))

        for key, args in (("version", ["--version"]), ("help", ["exec", "--help"])):
            argv = [self.codex, *args]
            context = 'phase=' + key + ' argv=' + json.dumps(argv)
            try:
                r = subprocess.run(argv, capture_output=True, text=True, timeout=300, env=child_environment())
            except subprocess.TimeoutExpired as e:
                raise ValueError('Codex metadata timed out: ' + context +
                                 ' timeout_seconds=' + str(e.timeout) +
                                 ' stderr=' + bounded_stderr(e.stderr)) from e
            except OSError as e:
                raise ValueError('Codex metadata unavailable: ' + context +
                                 ' errno=' + str(e.errno) + ' filename=' + json.dumps(e.filename)) from e
            if r.returncode:
                raise ValueError('Codex metadata command failed: ' + context +
                                 ' returncode=' + str(r.returncode) + ' stderr=' + bounded_stderr(r.stderr))
            results[key] = r.stdout
        for flag in ("--ignore-user-config", "--ephemeral", "--json", "--sandbox", "--output-last-message", "--skip-git-repo-check"):
            if flag not in results["help"]:
                raise ValueError("Installed Codex does not support " + flag)
        if getattr(self.inbox, 'governed', False):
            for flag in ('--approve-for-me', '--add-dir'):
                if flag not in results['help']:
                    raise ValueError('Installed Codex does not support governed dispatch control ' + flag)
        # Keep the installed release as provenance. Admission depends on the
        # command surface checked above, not an exact release identifier.
        return results["version"].strip()

    def info(self, probe_execution=False):
        if probe_execution or not (getattr(self.inbox, 'access', False) or getattr(self.inbox, 'governed', False)):
            return self.execution_info()
        master = self.inbox.check()
        return {'name': 'glados-codex-bridge', 'version': VERSION,
                'host': os.uname().nodename, 'codex_path': self.codex,
                'scope': 'profile-bound reading and opaque publication; execution separately admitted',
                'governance_master_oid': master, 'governance_dependencies': self.inbox.dependencies,
                'requested_model': 'per_task_immutable_profile', 'reasoning_requested': 'per_task',
                'sandbox_requested': 'derived_per_task_no_bypass',
                'authorization_limit': 'caller and owner authority required; access configuration and transport checks never authorize execution',
                'max_concurrent_tasks': 1,
                'available_tools': ['server_info', 'submit_task', 'task_status', 'task_output',
                    'prompt_upload', 'prompt_chunk', 'finalize_prompt', 'finalize_content', 'submit_uploaded_task',
                    'task_artifacts', 'task_artifact', 'evidence_manifest', 'evidence_file',
                    'project_roots', 'project_list', 'project_manifest', 'project_file', 'project_git_tree', 'project_git_blob'],
                'reader_available': True, 'storage_available': True,
                'cli_compatible': None, 'codex_version': None, 'error': None,
                'execution_readiness': 'NOT_PROBED', 'auth_status': 'NOT_CHECKED',
                'admission_mode': 'governed_contracts',
                'local_profile': self.inbox.profile_path,
                'evidence_root': self.inbox.profile['evidence_root'],
                'prompt_directory': str(self.inbox.root / 'reports/prompts'),
                'state_directory': str(self.root), 'max_prompt_bytes': MAX_PROMPT,
                'max_content_bytes': MAX_PROMPT, 'max_rpc_bytes': MAX_RPC,
                'max_page_bytes': 32768, 'backend_rpc_timeout_ms': 900000,
                'prompt_chunk_encoding': 'base64', 'artifact_encoding': 'base64'}

    def execution_info(self):
        try:
            version, ready, error = self.preflight(), True, None
        except ValueError as e:
            version, ready, error = None, False, str(e)
        info = {"name": "glados-codex-bridge", "version": VERSION, "host": os.uname().nodename,
                "codex_version": version, "codex_path": self.codex, "cli_compatible": ready, "error": error,
                'execution_readiness': 'CLI_COMPATIBLE' if ready else 'CLI_UNAVAILABLE',
                "auth_status": "NOT_CHECKED", "state_directory": str(self.root),
                "requested_model": self.model or "native_default_without_user_config",
                "scope": "one locally bound repository read-only task" if self.task else "plain-text pilot in a dedicated cwd; no repository or session resume",
                "bound_request_id": self.task.request_id if self.task else None,
                "bound_prompt_sha256": self.task.digest if self.task else None,
                "bound_prompt": self.task.content if self.task else None,
                "reasoning_requested": self.task.reasoning if self.task else None,
                "shell_snapshot_requested": False if self.task else "native_default",
                "allow_login_shell_requested": False if self.task else "native_default",
                "sandbox_requested": "read-only", "disabled_features": [f for f in DISABLED if not (self.task and f == "shell_tool")],
                "timeout_seconds": TIMEOUT, "max_concurrent_tasks": 1,
                "available_tools": ["server_info", "submit_task", "task_status", "task_output"]}

        if self.inbox:
            if getattr(self.inbox, 'governed', False):
                info.update(scope='complete author-authorized CPC contracts; task and stage grants govern effects',
                            admission_mode='governed_contracts', requested_model='per_task_immutable_profile',
                            reasoning_requested='per_task', sandbox_requested='derived_per_task_no_bypass',
                            governance_master_oid=self.inbox.check(),
                            governance_dependencies=self.inbox.dependencies,
                            local_profile=self.inbox.profile_path,
                            evidence_root=self.inbox.profile['evidence_root'],
                            prompt_directory=str(self.inbox.root / 'reports' / 'prompts'),
                            timeout_seconds=None,
                            authorization_limit='caller and owner authority required; lint and transport checks never authorize')
                info.update(max_prompt_bytes=MAX_PROMPT, max_rpc_bytes=MAX_RPC,
                            max_page_bytes=32768, backend_rpc_timeout_ms=900000,
                            prompt_chunk_encoding='base64', artifact_encoding='base64',
                            available_tools=['server_info', 'submit_task', 'task_status', 'task_output',
                                             'prompt_upload', 'prompt_chunk', 'finalize_prompt', 'finalize_content', 'submit_uploaded_task',
                                             'task_artifacts', 'task_artifact',
                                             'evidence_manifest', 'evidence_file',
                                             'project_roots', 'project_list', 'project_manifest',
                                             'project_file', 'project_git_tree', 'project_git_blob'])
                return info
            info.update(scope="author-reviewed read-only contracts in configured TOP26006_fw",
                        admission_mode="read_only_contracts",
                        requested_model=self.inbox.profile["model"],
                        reasoning_requested=self.inbox.profile["reasoning"],
                        sandbox_requested="read-only", shell_snapshot_requested=False,
                        allow_login_shell_requested=False,
                        disabled_features=[f for f in DISABLED if f != "shell_tool"],
                        governance_dependencies=self.inbox.dependencies,
                        authorization_limit="parent author review and user mandate required; metadata admission is not semantic authorization")
        return info

    def status(self, request_id):
        check_id(request_id)
        # Same transaction serializes status with submission. The worker holds busy.lock
        # until its terminal receipt is committed, including across MCP restarts.
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM tasks WHERE id=?", (request_id,)).fetchone()
            if row is None:
                raise ValueError("Unknown request_id; no task was submitted by this query")
            if row["state"] in ("STARTING", "RUNNING"):
                try:
                    fd = self.lock("busy.lock")
                except BlockingIOError:
                    pass
                else:
                    os.close(fd)
                    db.execute("UPDATE tasks SET state='OUTCOME_UNKNOWN',updated=? WHERE id=?", (time.time(), request_id))
                    row = db.execute("SELECT * FROM tasks WHERE id=?", (request_id,)).fetchone()
            receipt = json.loads(row['receipt'])
            # Full contract stays durably bound locally; do not echo multi-MiB
            # task inputs in every status page or exceed MCP response limits.
            public = {k: v for k, v in receipt.items() if k not in ('contract', 'artifacts')}
            return {"request_id": row["id"], "prompt_sha256": row["digest"], "state": row["state"],
                    "created_unix": row["created"], "updated_unix": row["updated"], **public}

    def command(self, work, task=None):
        task = self.task if task is None else task
        model = task.model if task else self.model
        args = [self.codex, "exec", "--ignore-user-config", "--ephemeral", "--skip-git-repo-check",
                "--sandbox", "read-only", "--json", "--color", "never", "--cd", str(work),
                "-c", 'approval_policy="never"', "-c", 'web_search="disabled"']
        if task:
            args.remove("--skip-git-repo-check")
            args[args.index("--cd") + 1] = str(task.root)
            args.extend(["--disable", "shell_snapshot", "-c", "allow_login_shell=false"])
            args.extend(["--enable", "shell_tool", "-c", 'model_reasoning_effort="' + task.reasoning + '"'])
        if task and hasattr(task, 'sandbox'):
            args[args.index('--sandbox') + 1] = task.sandbox
            if task.network:
                args.extend(['-c', 'sandbox_workspace_write.network_access=true'])
            else:
                args.extend(['-c', 'sandbox_workspace_write.network_access=false'])
            # Governed --cd is rebound to the reserved evidence directory in
            # submit. Only mutating tasks add source write capabilities.
            if task.mutating:
                for path in task.writable:
                    args.extend(['--add-dir', path])
            args.extend(['-c', 'sandbox_workspace_write.exclude_tmpdir_env_var=true',
                         '-c', 'sandbox_workspace_write.exclude_slash_tmp=true'])
            if task.mutating:
                args[args.index('approval_policy="never"')] = 'approval_policy="on-request"'
                args.append('--approve-for-me')
        for feature in DISABLED:
            if task and feature == "shell_tool":
                continue
            if task and hasattr(task, 'fields') and hasattr(task, 'sandbox') and feature in ('multi_agent', 'multi_agent_v2') and task.fields['delegation_policy'] != 'forbidden':
                args.extend(['--enable', feature])
                continue
            args.extend(["--disable", feature])
        if model:
            args.extend(["--model", model])
        args.extend(["--output-last-message", str(work.parent / "result.txt"), "-"])
        return args

    def submit(self, request_id, prompt):
        check_id(request_id)
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt.encode()) > MAX_PROMPT:
            raise ValueError("prompt must be nonempty strict UTF-8 text, at most 2097152 bytes")
        digest = hashlib.sha256(prompt.encode()).hexdigest()
        busy = None
        try:
            with self.db() as db:
                db.execute("BEGIN IMMEDIATE")
                old = db.execute("SELECT digest FROM tasks WHERE id=?", (request_id,)).fetchone()
                if old:
                    if old[0] != digest:
                        raise ValueError("ID_CONFLICT: this request_id already binds a different prompt")
                    duplicate = True
                else:
                    duplicate = False
                    uploaded = db.execute('SELECT digest FROM uploads WHERE id=?', (request_id,)).fetchone()
                    if uploaded and uploaded[0] != digest:
                        raise ValueError('ID_CONFLICT: upload binds different prompt bytes')
                    if db.execute("SELECT id FROM tasks WHERE state IN (?,?,?)", ACTIVE).fetchone():
                        raise ValueError("BUSY_OR_UNKNOWN: inspect existing task; do not resubmit with another ID")
                    try:
                        busy = self.lock("busy.lock")
                    except BlockingIOError as e:
                        raise ValueError("BUSY: one worker is already active") from e
                    task = self.inbox.task(request_id, prompt) if self.inbox else self.task
                    admission = task.admit(request_id, prompt) if task else {}
                    version = self.preflight()
                    folder = self.root / request_id
                    folder.mkdir(mode=0o700)  # Existing orphan directory: fail, never overwrite.
                    (folder / "work").mkdir(mode=0o700)
                    (folder / "prompt.txt").write_text(prompt, encoding="utf-8")
                    command = self.command(folder / "work", task)
                    receipt = {"codex_version": version, "argv": command, "cwd": str(task.root) if task else str(folder / "work"),
                               **admission,
                               "returncode": None, "success_means": "CLI completed, not scientific acceptance"}
                    if receipt.get('governed_contract'):
                        receipt = begin_evidence(folder, receipt, request_id)
                        command[command.index('--cd') + 1] = receipt['evidence_directory']
                        command.insert(-1, '--skip-git-repo-check')
                        receipt['invocation_cwd'] = receipt['evidence_directory']
                        receipt['evidence_contract'] = {
                            'report': 'executor file, otherwise exact final-message capture',
                            'patch': task.fields.get('patch_producer', 'codex'),
                            'patch_base': 'admission tracked worktree',
                            'validation': 'Git apply in private indexes; compare resulting tree identities',
                            'native_enforcement': 'not_observed; argv is a capability request',
                        }
                        context = ('Bridge transport context, not authorization: exact prompt bytes arrive on stdin. '
                                   'Apply current master AGENTS/CPC and selected native policies. '
                                   'Stop on unsupported semantics or new owner decisions. '
                                   'Source workspace: ' + str(task.root) + '; invocation workspace is the independently reserved diagnostic directory. '
                                   'Canonical report path: ' + receipt['report_path'] + '. '
                                   'Canonical patch path: ' + receipt['patch_path'] + '. '
                                   'Produce files required by the authored prompt; an existing patch is preserved and validated against admission tracked state. '
                                   'Host task-delta fallback is permitted only by authored patch_producer: codex_or_host; default codex requires an executor patch. '
                                   'If the report file is absent, exact final-message bytes are captured as its transport fallback. '
                                   'These fallbacks never waive authored report or artifact requirements. '
                                   'Evidence contract: ' + json.dumps(receipt['evidence_contract']) + '. '
                                   'Put authorized diagnostic artifacts only inside ' + receipt['evidence_directory'] +
                                   '. Report FOLD and scp using this actual collision-resolved directory. '
                                   'Profile tooling: ' + json.dumps(task.inbox.profile['tooling']) +
                                   '. Project grants differ from sandbox capabilities; approvals are never bypassed.')
                        insert_at = command.index('--output-last-message')
                        command[insert_at:insert_at] = ['-c', 'developer_instructions=' + json.dumps(context, ensure_ascii=False)]
                        receipt['argv'] = command
                        receipt['worker_timeout_seconds'] = None
                    now = time.time()
                    db.execute("INSERT INTO tasks VALUES (?,?,?,?,?,?,?)", (request_id, digest, prompt, "STARTING", now, now, json.dumps(receipt)))
            if not duplicate:
                # Reservation is durably committed BEFORE spawning. Crash in this gap
                # leaves OUTCOME_UNKNOWN, never an automatic retry.
                try:
                    with open(self.root / request_id / "supervisor.log", "ab") as log:
                        supervisor = subprocess.Popen([*([self.wrapper] if self.wrapper else []), sys.executable, '-S', '-B', str(Path(__file__).resolve()), "--state", str(self.root),
                                          "--worker", request_id, "--lock-fd", str(busy)],
                                         stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                         env=child_environment(), start_new_session=True, pass_fds=(busy,))
                        threading.Thread(target=supervisor.wait, daemon=True).start()
                except OSError as e:
                    self.update(request_id, "START_FAILED", error=type(e).__name__)
        finally:
            if busy is not None:
                os.close(busy)
        return {**self.status(request_id), "duplicate_request": duplicate}

    def prompt_upload(self, request_id, total_bytes, sha256):
        check_id(request_id)
        if type(total_bytes) is not int or not 1 <= total_bytes <= MAX_PROMPT or not re.fullmatch('[0-9a-f]{64}', sha256):
            raise ValueError('INVALID_UPLOAD_SIZE_OR_DIGEST')
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            old = db.execute('SELECT digest,size FROM uploads WHERE id=?', (request_id,)).fetchone()
            if old and tuple(old) != (sha256, total_bytes):
                raise ValueError('ID_CONFLICT')
            if not old:
                db.execute('INSERT INTO uploads VALUES (?,?,?)', (request_id, sha256, total_bytes))
            received = db.execute('SELECT coalesce(sum(length(data)),0) FROM chunks WHERE id=?', (request_id,)).fetchone()[0]
        return {'request_id': request_id, 'prompt_sha256': sha256, 'size_bytes': total_bytes,
                'transfer_id': request_id, 'received_bytes': received,
                'state': 'UPLOADING', 'execution_started': False}

    def prompt_chunk(self, request_id, offset, data_base64):
        check_id(request_id)
        try:
            data = base64.b64decode(data_base64, validate=True)
        except (ValueError, TypeError) as exc:
            raise ValueError('INVALID_BASE64') from exc
        if type(offset) is not int or offset < 0 or not 1 <= len(data) <= 24576:
            raise ValueError('INVALID_CHUNK_SIZE_OR_OFFSET')
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            upload = db.execute('SELECT size FROM uploads WHERE id=?', (request_id,)).fetchone()
            if not upload:
                raise ValueError('UPLOAD_NOT_RESERVED')
            old = db.execute('SELECT data FROM chunks WHERE id=? AND offset=?', (request_id, offset)).fetchone()
            received = db.execute('SELECT coalesce(sum(length(data)),0) FROM chunks WHERE id=?', (request_id,)).fetchone()[0]
            if old:
                if old[0] != data:
                    raise ValueError('CHUNK_CONFLICT')
            elif offset != received or offset + len(data) > upload[0]:
                raise ValueError('NONCONTIGUOUS_OR_OVERSIZED_CHUNK')
            else:
                db.execute('INSERT INTO chunks VALUES (?,?,?)', (request_id, offset, data))
                received += len(data)
        return {'request_id': request_id, 'received_bytes': received, 'duplicate_chunk': bool(old)}

    def uploaded_bytes(self, request_id):
        check_id(request_id)
        with self.db() as db:
            upload = db.execute('SELECT digest,size FROM uploads WHERE id=?', (request_id,)).fetchone()
            if not upload:
                raise ValueError('UPLOAD_NOT_RESERVED')
            content = b''.join(row[0] for row in db.execute('SELECT data FROM chunks WHERE id=? ORDER BY offset', (request_id,)))
        if len(content) != upload[1] or hashlib.sha256(content).hexdigest() != upload[0]:
            raise ValueError('UPLOAD_INCOMPLETE_OR_DIGEST_MISMATCH')
        return content

    def uploaded_text(self, request_id):
        try:
            return self.uploaded_bytes(request_id).decode('utf-8', errors='strict')
        except UnicodeError as exc:
            raise ValueError('PROMPT_MUST_BE_STRICT_UTF8') from exc

    def submit_uploaded_task(self, request_id):
        return self.submit(request_id, self.uploaded_text(request_id))

    def finalize_prompt(self, request_id):
        self.uploaded_text(request_id)  # Legacy Markdown adapter only.
        return self.finalize_content(request_id)

    def finalize_content(self, request_id):
        if not (getattr(self.inbox, 'access', False) or getattr(self.inbox, 'governed', False)):
            raise ValueError('DEPOSIT_REQUIRES_ACCESS_PROFILE')
        self.inbox.check()
        content = self.uploaded_bytes(request_id)
        from deposits import publish
        with self.db() as db:
            # Serialize deposit recovery using existing bookkeeping, never the
            # worker lock and never a task/execution reservation.
            db.execute('BEGIN IMMEDIATE')
            result = publish(self.inbox.root, request_id, content)
            self.inbox.check()
            return result

    def deposited_prompt(self, request_id):
        if not getattr(self.inbox, 'governed', False):
            raise ValueError('DEPOSIT_REQUIRES_GOVERNED_PROFILE')
        from deposits import consume
        # One bounded file snapshot, checked against the durable upload. The
        # exact returned bytes become submit_task's prompt; no later path read.
        return consume(self.inbox.root, request_id, self.uploaded_bytes(request_id)).decode('utf-8')

    def task_artifacts(self, request_id, offset=0, limit=100):
        state = self.status(request_id)
        if type(offset) is not int or type(limit) is not int or offset < 0 or not 1 <= limit <= 100:
            raise ValueError('INVALID_MANIFEST_PAGINATION')
        folder = self.root / request_id
        manifest = folder / 'artifacts.json'
        if os.path.lexists(manifest):
            rows = json.loads(regular_bytes(manifest))
        else:
            # R6 history and active/failed tasks remain readable without loading
            # an admission configuration or migrating the old task row.
            names = ['prompt.txt', 'result.txt', 'events.jsonl', 'stderr.log', 'supervisor.log',
                     request_id + '_report.md', request_id + '_worktree_diff.patch']
            rows = []
            for name in names:
                path = folder / name
                if os.path.lexists(path):
                    size, digest = file_identity(path)
                    rows.append({'artifact_id': 'legacy_' + name, 'name': name,
                                 'size_bytes': size, 'sha256': digest})
            if state.get('governed_contract'):
                for name, _ in evidence_sources(state, request_id):
                    with partial_evidence_reader(state, request_id, name) as stream:
                        size, digest = stream_identity(stream)
                    rows.append({'artifact_id': 'partial_' + name, 'name': name,
                                 'size_bytes': size, 'sha256': digest,
                                 'evidence_status': 'partial_unvalidated'})
        return {'request_id': request_id, 'state': state['state'], 'artifacts': rows[offset:offset + limit],
                'total': len(rows), 'next_offset': offset + len(rows[offset:offset + limit]),
                'has_more': offset + limit < len(rows), 'manifest_frozen': manifest.exists()}

    def task_artifact(self, request_id, artifact_id, offset=0, limit=8192):
        if not isinstance(artifact_id, str):
            raise ValueError('INVALID_ARTIFACT_ID')
        rows = self.task_artifacts(request_id)['artifacts']
        # Fetch all manifest pages internally: identifiers are exact allowlist
        # members, never filesystem paths supplied by a caller.
        start = len(rows)
        while start and start % 100 == 0:
            page = self.task_artifacts(request_id, offset=start)
            rows.extend(page['artifacts'])
            start += len(page['artifacts'])
            if not page['has_more']:
                break
        row = next((r for r in rows if r['artifact_id'] == artifact_id), None)
        if row is None:
            raise ValueError('UNKNOWN_TASK_ARTIFACT')
        folder = self.root / request_id
        if artifact_id.startswith(('legacy_', 'partial_')):
            if type(offset) is not int or type(limit) is not int or offset < 0 or not 1 <= limit <= 32768:
                raise ValueError('INVALID_ARTIFACT_PAGINATION')
            reader = (partial_evidence_reader(self.status(request_id), request_id, row['name'])
                      if artifact_id.startswith('partial_') else regular_reader(folder / row['name']))
            with reader as stream:
                size, digest = stream_identity(stream)
                if size != row['size_bytes'] or digest != row['sha256']:
                    raise ValueError('ARTIFACT_CHANGED_DURING_READ')
                stream.seek(offset)
                chunk = stream.read(limit)
            return {**row, 'request_id': request_id, 'encoding': 'base64', 'data': base64.b64encode(chunk).decode(),
                    'offset': offset, 'next_offset': offset + len(chunk), 'has_more': offset + len(chunk) < size,
                    'chunk_sha256': hashlib.sha256(chunk).hexdigest()}
        return {'request_id': request_id, **artifact_page(folder, row, offset, limit)}

    def output(self, request_id, stream="result", offset=0, limit=8192):
        check_id(request_id)
        names = {"result": "result.txt", "events": "events.jsonl", "stderr": "stderr.log"}
        if stream not in names or not isinstance(offset, int) or not isinstance(limit, int) or offset < 0 or not 1 <= limit <= 32768:
            raise ValueError("invalid stream or pagination; offset is bytes, limit is 1..32768")
        state = self.status(request_id)
        file = self.root / request_id / names[stream]
        if not file.exists():
            return {"request_id": request_id, "state": state["state"], "available": False}
        fd = os.open(file, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as f:
            size = os.fstat(f.fileno()).st_size
            f.seek(offset)
            data = f.read(limit)
        return {"request_id": request_id, "state": state["state"], "stream": stream, "available": True,
                "offset": offset, "next_offset": offset + len(data), "size_bytes": size,
                "has_more": offset + len(data) < size, "text": data.decode("utf-8", errors="replace")}

    def worker(self, request_id, lock_fd):
        os.fstat(lock_fd)  # Must inherit the held exclusive lock from submit.
        with self.db() as db:
            row = db.execute("SELECT * FROM tasks WHERE id=?", (request_id,)).fetchone()
        if not row or row["state"] != "STARTING":
            raise ValueError("Worker can only consume one reserved STARTING task")
        receipt = json.loads(row["receipt"])
        folder = self.root / request_id
        proc = None
        try:
            governed = receipt.get('governed_contract', False)
            if "governance_dependencies" in receipt:
                content = row['prompt'].encode('utf-8')
                if hashlib.sha256(content).hexdigest() != row['digest'] or regular_bytes(folder / 'prompt.txt') != content:
                    raise ValueError('PROMPT_STORAGE_CHANGED_BEFORE_EXECUTION')
                master = governance(receipt.get('governance_root', receipt['cwd']), receipt["governance_dependencies"])
                before = ({key: snapshot(path) for key, path in receipt['repositories'].items()}
                          if governed else snapshot(receipt['cwd']))
                if before != receipt['repositories_before' if governed else 'repository_before']:
                    raise ValueError("REPOSITORY_CHANGED_BEFORE_EXECUTION")
                if governed and hashlib.sha256(Path(receipt['profile_path']).read_bytes()).hexdigest() != receipt['profile_sha256']:
                    raise ValueError('LOCAL_PROFILE_CHANGED_BEFORE_EXECUTION')
                self.update(request_id, "STARTING", pre_spawn_master_oid=master)
            self.update(request_id, "RUNNING", supervisor_pid=os.getpid(), started_unix=time.time())
            with open(folder / "events.jsonl", "xb") as events, open(folder / "stderr.log", "xb") as errors:
                proc = subprocess.Popen(receipt["argv"], stdin=subprocess.PIPE, stdout=events, stderr=errors,
                                        cwd=receipt.get('invocation_cwd', receipt['cwd']), env=child_environment(), start_new_session=True,
                                        )
                self.update(request_id, "RUNNING", codex_pid=proc.pid)
                try:
                    proc.communicate(row["prompt"].encode(), timeout=receipt.get('worker_timeout_seconds', TIMEOUT))
                    # Exit zero is necessary but not sufficient; require completion event
                    # and the final-message file, never infer success from launch alone.
                    completed, failed = False, False
                    with (folder / 'events.jsonl').open(encoding='utf-8', errors='replace') as event_stream:
                        for line in event_stream:
                            try:
                                kind = json.loads(line).get("type")
                                completed |= kind == "turn.completed"
                                failed |= kind == "turn.failed"
                            except (ValueError, AttributeError):
                                pass
                    ok = proc.returncode == 0 and completed and not failed and (folder / "result.txt").exists()
                    # Persist the producer outcome before any secondary collector
                    # work. Collection failure cannot replace these process facts.
                    self.update(request_id, 'RUNNING', returncode=proc.returncode,
                                turn_completed_observed=completed, turn_failed_observed=failed,
                                process_success=ok)
                    if governed:
                        try:
                            evidence = finish_evidence(folder, receipt, request_id)
                        except Exception as exc:
                            traceback.print_exc()
                            self.update(request_id, 'RUNNING', collection_error=type(exc).__name__,
                                        collection_failure_reason=(str(exc) if isinstance(exc, ValueError)
                                                                   else 'inspect local supervisor log'))
                            ok = False
                        else:
                            self.update(request_id, 'RUNNING', **evidence)
                            ok = ok and not evidence['scope_findings'] and not evidence['evidence_findings']
                            if not self._mutation_permitted(receipt):
                                ok = ok and evidence['tracked_state_unchanged']
                    elif "governance_dependencies" in receipt:
                        after = snapshot(receipt["cwd"])
                        end_master = governance(receipt["cwd"], receipt["governance_dependencies"])
                        unchanged = after == receipt["repository_before"]
                        self.update(request_id, "RUNNING", repository_after=after,
                                    repository_preserved=unchanged, post_run_master_oid=end_master)
                        ok = ok and unchanged
                        if ok:
                            report = folder / (request_id + "_report.md")
                            report.write_bytes((folder / "result.txt").read_bytes())
                            patch = folder / (request_id + "_worktree_diff.patch")
                            with patch.open("xb"):
                                pass
                            self.update(request_id, "RUNNING", report_path=str(report),
                                        report_sha256=hashlib.sha256(report.read_bytes()).hexdigest(),
                                        patch_path=str(patch), patch_kind="empty_no_changes",
                                        patch_sha256=hashlib.sha256(b"").hexdigest())
                    self.update(request_id, "COMPLETED" if ok else "FAILED", returncode=proc.returncode,
                                turn_completed_observed=completed, ended_unix=time.time())
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait()
                    self.update(request_id, 'OUTCOME_UNKNOWN' if governed else "TIMED_OUT", returncode=proc.returncode, ended_unix=time.time())
        except BaseException as e:
            if proc is not None and proc.poll() is None:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
            self.update(request_id, "FAILED", error=type(e).__name__,
                        returncode=proc.returncode if proc is not None else None,
                        failure_reason=str(e) if isinstance(e, ValueError) else "inspect local supervisor log",
                        ended_unix=time.time())
            raise
        finally:
            if receipt.get('governed_contract'):
                try:
                    after = {key: snapshot(path) for key, path in receipt['repositories'].items()}
                    with self.db() as db:
                        current_state = db.execute('SELECT state FROM tasks WHERE id=?', (request_id,)).fetchone()[0]
                    self.update(request_id, current_state, repositories_after=after)
                except Exception:
                    # Preserve the original outcome. Missing readback is explicit,
                    # never authorization to retry or roll back.
                    with self.db() as db:
                        current_state = db.execute('SELECT state FROM tasks WHERE id=?', (request_id,)).fetchone()[0]
                    self.update(request_id, current_state, post_run_readback='unavailable; inspect owned state before recovery')
            os.close(lock_fd)

    @staticmethod
    def _mutation_permitted(receipt):
        return receipt['contract']['prompt_mode'] not in ('investigation_only', 'validation_only', 'pr_preparation')


def main():
    os.umask(0o077)
    os.environ.pop("CONTROL_PLANE_API_KEY", None)
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", default=str(Path.home() / ".local/state/glados-codex-bridge-r1"))
    parser.add_argument("--worker")
    parser.add_argument("--lock-fd", type=int)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--rpc", action="store_true")
    entry = parser.add_mutually_exclusive_group()
    entry.add_argument('--prompt-file', metavar='REQUEST_ID', help='submit the bound deposited Markdown through submit_task')
    entry.add_argument('--task-status', metavar='REQUEST_ID', help='observe an existing task without submission')
    parser.add_argument("--read-only-prompt")
    parser.add_argument("--read-only-inbox")
    parser.add_argument('--governed-profile')
    parser.add_argument("--workspace")
    parser.add_argument("--command-wrapper")
    parser.add_argument('--codex', help='explicit installation CLI executable; never supplied by task RPC')
    args = parser.parse_args()
    if sum(bool(v) for v in (args.read_only_prompt, args.read_only_inbox, args.governed_profile)) > 1:
        parser.error("choose bound prompt, read-only inbox, or governed profile")
    if bool(args.read_only_prompt or args.read_only_inbox or args.governed_profile) != bool(args.workspace):
        parser.error("--read-only-prompt and --workspace must be supplied together")
    if (args.read_only_prompt or args.read_only_inbox or args.governed_profile) and not args.command_wrapper:
        parser.error("repository mode requires --command-wrapper")
    request = None
    if args.rpc and not (args.prompt_file or args.task_status or args.worker or args.check):
        raw = sys.stdin.buffer.read(MAX_RPC + 1)
        if len(raw) > MAX_RPC:
            print(json.dumps({'ok': False, 'error': 'RPC payload too large'}))
            return
        try:
            request = json.loads(raw)
            if not isinstance(request, dict):
                raise ValueError('Invalid bridge request')
        except ValueError:
            print(json.dumps({'ok': False, 'error': 'Invalid bridge request'}))
            return
        from project_reader import PROJECT_METHODS
        if request.get('method') in ('evidence_manifest', 'evidence_file', *PROJECT_METHODS):
            # These operations do not even construct Bridge: no state mkdir,
            # SQLite connection, worker lock, CLI probe or task reconciliation.
            try:
                if not args.governed_profile:
                    raise ValueError('EVIDENCE_REQUIRES_GOVERNED_PROFILE')
                from access_profile import AccessInbox
                from evidence_reader import EvidenceReader
                inbox = AccessInbox(args.governed_profile, args.workspace)
                if request['method'] in PROJECT_METHODS:
                    from project_reader import ProjectReader
                    reader = ProjectReader(inbox)
                    operation = getattr(reader, request['method'])
                else:
                    inbox.check()
                    reader = EvidenceReader(inbox.profile['evidence_root'])
                    operation = reader.manifest if request['method'] == 'evidence_manifest' else reader.file_page
                if not isinstance(request.get('args', {}), dict):
                    raise ValueError('Invalid bridge arguments')
                result = operation(**request.get('args', {}))
                if request['method'] not in PROJECT_METHODS:
                    inbox.check()
                print(json.dumps({'ok': True, 'result': result}))
            except (ValueError, TypeError, OSError) as exc:
                error = ('EVIDENCE_UNAVAILABLE_OR_UNSAFE: errno=' + str(exc.errno)
                         if isinstance(exc, OSError) else str(exc))
                if request['method'] in PROJECT_METHODS:
                    code = error.split(':', 1)[0]
                    error = (code.replace('EVIDENCE_', 'PROJECT_')
                             if re.fullmatch('[A-Z][A-Z0-9_]*', code)
                             else 'PROJECT_INVALID_ARGUMENTS_OR_UNAVAILABLE')
                print(json.dumps({'ok': False, 'error': error}))
            return
    bridge = Bridge(args.state, codex=args.codex, wrapper=args.command_wrapper)
    def bind_access():
        if args.governed_profile:
            from access_profile import AccessInbox
            bridge.inbox = AccessInbox(args.governed_profile, args.workspace)
        elif args.read_only_inbox or args.read_only_prompt:
            bind_task()
    def bind_task():
        if args.governed_profile:
            from governed_task import GovernedInbox
            bridge.inbox = GovernedInbox(args.governed_profile, args.workspace, bridge.root)
            if bridge.inbox.profile['tooling']['command_wrapper'] != str(Path(args.command_wrapper).resolve()):
                raise ValueError('WRAPPER_PROFILE_MISMATCH')
            if Path(bridge.inbox.profile['tooling']['python_interpreter']).resolve() != Path(sys.executable).resolve():
                raise ValueError('PYTHON_PROFILE_MISMATCH')
        if args.read_only_inbox:
            bridge.inbox = ReadOnlyInbox(args.read_only_inbox, args.workspace, bridge.root)
        if args.read_only_prompt:
            bridge.task = RepositoryTask(args.read_only_prompt, args.workspace)
            bridge.model = bridge.task.model
    if args.worker:
        bridge.worker(args.worker, args.lock_fd)
        return
    if args.check:
        bind_task()
        if bridge.inbox:
            bridge.inbox.check()
        info = bridge.info(probe_execution=True)
        info["python_version"] = sys.version.split()[0]
        print(json.dumps(info, indent=2))
        sys.exit(0 if info["cli_compatible"] else 1)
    if not args.rpc:
        parser.error("Use server.mjs for MCP, or --check for local preflight")
    local_id = args.prompt_file or args.task_status
    local_hint = ({'request_id': local_id,
                   'observe_command': str(Path(__file__).resolve().with_name('manual.sh')) + ' status ' + local_id,
                   'recovery': 'Observe this same ID after interruption; never choose another ID to retry.'}
                  if local_id and ID_RE.fullmatch(local_id) else {})
    try:
        if args.prompt_file:
            if not args.governed_profile:
                raise ValueError('DEPOSIT_REQUIRES_GOVERNED_PROFILE')
            bind_task()
            request = {'method': 'submit_task', 'args': {
                'request_id': args.prompt_file, 'prompt': bridge.deposited_prompt(args.prompt_file)}}
        elif args.task_status:
            request = {'method': 'task_status', 'args': {'request_id': args.task_status}}
        # Ordinary stdio RPC was parsed before constructing the stateful bridge.
        operations = {"server_info": bridge.info, "submit_task": bridge.submit,
                      "task_status": bridge.status, "task_output": bridge.output,
                      'prompt_upload': bridge.prompt_upload, 'prompt_chunk': bridge.prompt_chunk,
                      'finalize_prompt': bridge.finalize_prompt, 'finalize_content': bridge.finalize_content,
                      'submit_uploaded_task': bridge.submit_uploaded_task,
                      'task_artifacts': bridge.task_artifacts, 'task_artifact': bridge.task_artifact}
        if request.get("method") not in operations or not isinstance(request.get("args", {}), dict):
            raise ValueError("Invalid bridge method or arguments")
        if request['method'] in ('finalize_prompt', 'finalize_content', 'server_info'):
            if request['method'] == 'server_info' and request.get('args', {}).get('probe_execution'):
                bind_task()
            else:
                bind_access()
        if request["method"] in ("submit_task", 'submit_uploaded_task'):
            # Existing exact requests remain lookup-only even if installation
            # configuration/governance changed after their execution.
            with bridge.db() as db:
                exists = db.execute('SELECT 1 FROM tasks WHERE id=?', (request.get('args', {}).get('request_id'),)).fetchone()
            if not exists and not args.prompt_file:
                bind_task()
        result = operations[request["method"]](**request.get("args", {}))
        if request["method"] == "server_info":
            result["python_version"] = sys.version.split()[0]
        print(json.dumps({"ok": True, "result": result, **local_hint}))
    except (ValueError, TypeError) as e:
        print(json.dumps({"ok": False, "error": str(e), **local_hint}))
    except Exception as e:
        # Preserve details locally; no arbitrary internal exception text to MCP.
        method = request.get('method') if isinstance(request, dict) else None
        recovery = ('reconcile the same transfer and bytes with prompt_upload/finalize_content; no task was initiated'
                    if method in ('prompt_upload', 'prompt_chunk', 'finalize_prompt', 'finalize_content') else
                    'retry information query; no execution initiated' if method == 'server_info' else
                    'inspect task_status with the same request_id before any new submission')
        print(json.dumps({"ok": False, "error": "BACKEND_ERROR: " + type(e).__name__ + "; " + recovery}))
        raise


if __name__ == "__main__":
    main()
