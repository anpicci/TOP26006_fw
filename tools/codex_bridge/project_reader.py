"""Identity-bound project filesystem and immutable local Git reads.

No task state, shell, checkout, execution, persistent cache or network. The
installation binding defines technical reach; each caller still needs authority.
"""
import base64
import contextlib
import functools
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess

from artifacts import PAGE_BYTES, stream_identity
from evidence_reader import (DirectoryChain, EvidenceReader, inode, pagination,
                             relative_parts, signature, verify_page)

PROJECT_METHODS = ('project_roots', 'project_list', 'project_manifest', 'project_file',
                   'project_git_tree', 'project_git_blob')
# Never expose service/account credentials or Git internals through parent roots.
PRIVATE_NAMES = {'.git', '.ssh', '.aws', '.codex', '.gnupg', '.netrc', '.git-credentials', '.env'}
OID = re.compile(r'(?:[0-9a-f]{40}|[0-9a-f]{64})\Z')
DIGEST = re.compile(r'[0-9a-f]{64}\Z')


def portable_numbers(values):
    """Filesystem identities exceed JSON/JavaScript's exact integer range."""
    return [str(value) for value in values]


def identity(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True,
                                     separators=(',', ':')).encode()).hexdigest()


def absolute_path(value):
    if not isinstance(value, str) or not value.startswith('/') or value == '/':
        raise ValueError('PROJECT_INVALID_ABSOLUTE_PATH')
    relative_parts(value[1:])
    return Path(value)


def private_path(path):
    return any(part in PRIVATE_NAMES or part.startswith('.env.') for part in Path(path).parts)


def git_environment():
    # Discard inherited repository/object/config/trace/credential steering.
    env = {k: v for k, v in os.environ.items() if k in ('PATH', 'LANG', 'LC_ALL', 'SYSTEMROOT')}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null',
               GIT_OPTIONAL_LOCKS='0', GIT_NO_LAZY_FETCH='1', GIT_NO_REPLACE_OBJECTS='1',
               GIT_TERMINAL_PROMPT='0', GIT_PROTOCOL_FROM_USER='0', GIT_ALLOW_PROTOCOL='')
    return env


def git_command(root, *args):
    return ['git', '--no-pager', '--no-optional-locks', '--no-replace-objects',
            '--literal-pathspecs', '-c', 'core.fsmonitor=false', '-c', 'core.hooksPath=/dev/null',
            '-c', 'gc.auto=0', '-c', 'protocol.allow=never', '-C', str(root), *args]


def local_git(root, *args):
    try:
        with git_invocation(root, *args) as (command, options):
            result = subprocess.run(command, **options, capture_output=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError('PROJECT_GIT_BACKEND_INTERRUPTED') from exc
    if result.returncode:
        raise ValueError('PROJECT_GIT_OBJECT_OR_BINDING_UNAVAILABLE')
    return result.stdout


@contextlib.contextmanager
def git_invocation(root, *args):
    if not isinstance(root, dict):
        yield git_command(root, *args), {'env': git_environment()}
        return
    # Pin checkout, private git dir and common dir, including a linked
    # worktree's gitfile/commondir. Git children inherit only these descriptors.
    with contextlib.ExitStack() as stack:
        chains = [DirectoryChain(stack, root[key]) for key in
                  ('worktree', 'git_directory', 'common_directory')]
        for chain, key in zip(chains, ('namespace', 'git_namespace', 'common_namespace')):
            if [(p, portable_numbers(v)) for _, p, _, v in chain.bindings] != root[key]:
                raise ValueError('PROJECT_REPOSITORY_BINDING_CHANGED')
        work, git_dir, common = [chain.fd for chain in chains]
        env = git_environment()
        env['GIT_COMMON_DIR'] = '/proc/self/fd/' + str(common)
        command = git_command('/', '--git-dir=/proc/self/fd/' + str(git_dir),
                              '--work-tree=/proc/self/fd/' + str(work), *args)
        yield command, {'env': env, 'pass_fds': (work, git_dir, common)}
        for chain in chains:
            chain.check()


def directory_identity(path):
    with contextlib.ExitStack() as stack:
        chain = DirectoryChain(stack, path)
        chain.check()
        return [(part, portable_numbers(value)) for _, part, _, value in chain.bindings]


def repository_binding(path):
    """Verify exact checkout/gitfile/common-dir, never an inherited parent repo."""
    namespace = directory_identity(path)
    marker = path / '.git'
    info = marker.lstat()
    if not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):
        raise ValueError('PROJECT_INVALID_GIT_BINDING')
    top = Path(os.fsdecode(local_git(path, 'rev-parse', '--show-toplevel')).strip())
    if top != path:
        raise ValueError('PROJECT_REPOSITORY_ROOT_MISMATCH')
    git_dir = Path(os.fsdecode(local_git(path, 'rev-parse', '--absolute-git-dir')).strip())
    common = Path(os.fsdecode(local_git(path, 'rev-parse', '--path-format=absolute', '--git-common-dir')).strip())
    if stat.S_ISREG(info.st_mode):
        # Gitfiles are small installation bindings, not arbitrary client files.
        if info.st_size > 8192:
            raise ValueError('PROJECT_INVALID_GITFILE')
        from artifacts import regular_reader
        with regular_reader(marker, require_private=False) as stream:
            marker_hash = stream_identity(stream)[1]
            if signature(os.fstat(stream.fileno())) != signature(info):
                raise ValueError('PROJECT_REPOSITORY_BINDING_CHANGED')
        if signature(marker.lstat()) != signature(info):
            raise ValueError('PROJECT_REPOSITORY_BINDING_CHANGED')
        marker_identity = [portable_numbers(signature(info)), marker_hash]
    elif stat.S_ISDIR(info.st_mode):
        marker_identity = portable_numbers(inode(info))
    else:
        raise ValueError('PROJECT_INVALID_GIT_BINDING')
    return {'worktree': str(path), 'namespace': namespace, 'git_directory': str(git_dir),
            'common_directory': str(common), 'git_namespace': directory_identity(git_dir),
            'common_namespace': directory_identity(common), 'git_marker': marker_identity}


def typed_registry(raw):
    result = {}
    for line in raw.splitlines():
        cells = [cell.strip() for cell in line.split('|')]
        if len(cells) > 3 and cells[1].startswith('`'):
            result[cells[1].strip('`')] = cells[2].strip('`')
    if result.get('TOP26006_fw') != 'COORDINATION_META_REPOSITORY':
        raise ValueError('PROJECT_REGISTRY_UNAVAILABLE')
    return result


def item_page(rows, offset, limit, key, token, expected):
    pagination(offset, limit, 100)
    if expected is not None and (not isinstance(expected, str) or not DIGEST.fullmatch(expected)):
        raise ValueError('PROJECT_INVALID_EXPECTED_IDENTITY')
    if offset and expected is None:
        raise ValueError('PROJECT_EXPECTED_IDENTITY_REQUIRED')
    if expected is not None and expected != token:
        raise ValueError('PROJECT_INVENTORY_CONFLICT')
    if offset > len(rows):
        raise ValueError('PROJECT_OFFSET_BEYOND_EOF')
    page = rows[offset:offset + limit]
    return {key: page, 'inventory_id': token, 'offset': offset,
            'next_offset': offset + len(page), 'has_more': offset + len(page) < len(rows),
            'total': len(rows), 'complete': True, 'completeness_unit': key}


def byte_page(chunk, size, digest, offset):
    return {'encoding': 'base64', 'data': base64.b64encode(chunk).decode('ascii'),
            'size_bytes': size, 'sha256': digest, 'offset': offset,
            'chunk_size_bytes': len(chunk), 'chunk_sha256': hashlib.sha256(chunk).hexdigest(),
            'next_offset': offset + len(chunk), 'has_more': offset + len(chunk) < size,
            'eof': offset + len(chunk) == size}


def verified_read(method):
    """Coalesce repeated binding probes within one read, recheck on exit.

    File descriptors still check every consumed namespace. No observation is
    reused across calls, and no acquisition data or persistent cache is kept.
    """
    @functools.wraps(method)
    def read(self, *args, **kwargs):
        self.check()
        self.checked_roots = {}
        try:
            result = method(self, *args, **kwargs)
            for row in list(self.checked_roots.values()):
                self.check_root(row, final=True)
            self.check()
            return result
        finally:
            self.checked_roots = None
    return read


class ProjectReader:
    def __init__(self, inbox):
        self.inbox = inbox
        self.checked_roots = None
        self.governance_inode = inode(os.stat(inbox.root, follow_symlinks=False))
        self.master = inbox.check()
        raw = local_git(inbox.root, 'show', self.master + ':governance/repositories.md')
        self.registry_id = hashlib.sha256(raw).hexdigest()
        self.registry = typed_registry(raw.decode('utf-8'))
        self.roots, self.repositories, self.blocked = [], {}, []
        self.discovery_limits = []
        workspace = Path(inbox.profile['workspace_root'])
        configured = inbox.profile['repositories']
        # Known exclusions have stable project-relative names even when absent
        # from the profile. Do not enumerate their contents.
        for repo_id, kind in self.registry.items():
            if kind in ('CONDITIONAL_INACTIVE', 'KNOWN_OUT_OF_SCOPE_SURFACE'):
                self.blocked.append(workspace / repo_id)
        for repo_id, config in configured.items():
            if repo_id not in self.registry or self.registry[repo_id] in (
                    'CONDITIONAL_INACTIVE', 'KNOWN_OUT_OF_SCOPE_SURFACE'):
                self.blocked.append(Path(config['path']))
            else:
                self.add_exclusions(repo_id, Path(config['path']))
        for label, path in [('workspace', workspace), ('evidence', Path(inbox.profile['evidence_root']))]:
            self.add_root(label, path)
        for repo_id, config in configured.items():
            path = Path(config['path'])
            if repo_id not in self.registry or self.denied(path):
                continue
            try:
                binding = repository_binding(path)
                self.repositories[repo_id] = binding
                self.add_root('repo:' + repo_id, path, repo_id, binding)
                try:
                    raw = local_git(path, 'worktree', 'list', '--porcelain', '-z')
                except ValueError:
                    # Discovery failure cannot revoke a verified main root.
                    self.discovery_limits.append({'repository_id': repo_id,
                                                  'reason': 'REGISTERED_WORKTREES_UNAVAILABLE'})
                    raw = b''
                for field in raw.split(b'\0'):
                    if field.startswith(b'worktree '):
                        linked = Path(field[9:].decode('utf-8'))
                        self.add_exclusions(repo_id, linked)
                        if linked == path or self.denied(linked):
                            continue
                        try:
                            other = repository_binding(linked)
                            if (other['common_directory'], other['common_namespace']) != (
                                    binding['common_directory'], binding['common_namespace']):
                                raise ValueError('PROJECT_WORKTREE_COMMON_DIRECTORY_MISMATCH')
                            self.add_root('worktree:' + repo_id + ':' + identity(str(linked))[:16],
                                          linked, repo_id, other)
                        except (ValueError, OSError):
                            self.add_unavailable('worktree:' + repo_id + ':' + identity(str(linked))[:16], linked)
            except (ValueError, OSError):
                # A parent workspace grant cannot bypass an unverified checkout.
                self.add_unavailable('repo:' + repo_id, path)
        self.roots.sort(key=lambda row: row['root_id'])

    def add_exclusions(self, repo_id, path):
        for excluded, kind in self.registry.items():
            if kind not in ('CONDITIONAL_INACTIVE', 'KNOWN_OUT_OF_SCOPE_SURFACE'):
                continue
            if repo_id == 'TOP26006_fw':
                self.blocked.append(path / excluded)
            elif excluded.startswith(repo_id + '/'):
                self.blocked.append(path / excluded[len(repo_id) + 1:])

    def denied(self, path):
        return private_path(path) or any(path == p or path.is_relative_to(p) for p in self.blocked)

    def add_unavailable(self, label, path):
        self.roots.append({'root_id': label, 'path': str(path), 'available': False,
                           'reason': 'ROOT_OR_REPOSITORY_UNVERIFIED'})

    def add_root(self, label, path, repo_id=None, repository=None):
        try:
            absolute_path(str(path))
            if self.denied(path):
                raise ValueError('PROJECT_SCOPE_DENIED')
            row = {'root_id': label, 'path': str(path), 'available': True,
                   'namespace': directory_identity(path)}
            if repo_id:
                row.update(repository_id=repo_id, repository=repository)
            row['binding_id'] = identity(row)
            self.roots.append(row)
        except (ValueError, OSError):
            self.add_unavailable(label, path)

    def check(self):
        try:
            info = os.stat(self.inbox.root, follow_symlinks=False)
        except OSError as exc:
            raise ValueError('PROJECT_GOVERNANCE_ROOT_BINDING_CHANGED') from exc
        if not stat.S_ISDIR(info.st_mode) or inode(info) != self.governance_inode:
            raise ValueError('PROJECT_GOVERNANCE_ROOT_BINDING_CHANGED')
        master = self.inbox.check()
        raw = local_git(self.inbox.root, 'show', master + ':governance/repositories.md')
        if hashlib.sha256(raw).hexdigest() != self.registry_id:
            raise ValueError('PROJECT_REGISTRY_BINDING_CHANGED')

    def check_root(self, row, final=False):
        if self.checked_roots is not None and row['root_id'] in self.checked_roots and not final:
            return
        if directory_identity(row['path']) != row['namespace']:
            raise ValueError('PROJECT_ROOT_BINDING_CHANGED')
        if 'repository' in row and repository_binding(Path(row['path'])) != row['repository']:
            raise ValueError('PROJECT_REPOSITORY_BINDING_CHANGED')
        if self.checked_roots is not None:
            self.checked_roots[row['root_id']] = row

    def root_for(self, path):
        path = absolute_path(path)
        if self.denied(path):
            raise ValueError('PROJECT_SCOPE_DENIED')
        matches = [row for row in self.roots if path.is_relative_to(row['path'])]
        if not matches:
            raise ValueError('PROJECT_PATH_NOT_COVERED')
        # Repository binding wins over the same workspace path.
        row = max(matches, key=lambda row: (len(Path(row['path']).parts),
                                          row['root_id'].startswith(('repo:', 'worktree:'))))
        if not row['available']:
            raise ValueError('PROJECT_ROOT_UNAVAILABLE')
        self.check_root(row)
        return path, row

    @verified_read
    def project_roots(self):
        return {'roots': self.roots, 'registry_sha256': self.registry_id,
                'master': self.master, 'catalog_id': identity([self.roots, self.discovery_limits]),
                'discovery_limits': self.discovery_limits,
                'excluded_project_surfaces': [key for key, kind in self.registry.items()
                    if kind in ('CONDITIONAL_INACTIVE', 'KNOWN_OUT_OF_SCOPE_SURFACE')],
                'private_components': sorted(PRIVATE_NAMES), 'symlinks_followed': False,
                'task_required': False, 'snapshot': False}

    @contextlib.contextmanager
    def directory(self, path):
        path, row = self.root_for(path)
        try:
            with contextlib.ExitStack() as stack:
                chain = DirectoryChain(stack, row['path'])
                current = Path(row['path'])
                boundaries = []
                for part in path.relative_to(row['path']).parts:
                    chain.descend(part)
                    current = current / part
                    self.check_repository_boundary(current, chain.fd)
                    boundaries.append((current, chain.fd))
                yield chain, row
                chain.check()
                for current, fd in boundaries:
                    self.check_repository_boundary(current, fd)
                self.check_root(row)
        except OSError as exc:
            raise ValueError('PROJECT_FILE_OR_DIRECTORY_UNAVAILABLE: errno=' + str(exc.errno)) from exc

    def check_repository_boundary(self, path, fd):
        # Only necessary ancestors, before and after consumption. A newly
        # inserted nested repository marker changes the authority boundary.
        try:
            os.stat('.git', dir_fd=fd, follow_symlinks=False)
        except FileNotFoundError:
            return
        if not any(r['path'] == str(path) and r['available'] and
                   'repository_id' in r for r in self.roots):
            raise ValueError('PROJECT_UNREGISTERED_REPOSITORY_BOUNDARY')

    @verified_read
    def project_list(self, directory, offset=0, limit=100, expected_inventory_id=None):
        pagination(offset, limit, 100)
        with self.directory(directory) as (chain, root):
            before = signature(os.fstat(chain.fd))
            names = sorted(os.listdir(chain.fd))
            rows = []
            for name in names:
                relative_parts(name)
                path = Path(directory) / name
                info = os.stat(name, dir_fd=chain.fd, follow_symlinks=False)
                kind = ('file' if stat.S_ISREG(info.st_mode) else 'directory' if stat.S_ISDIR(info.st_mode)
                        else 'symlink' if stat.S_ISLNK(info.st_mode) else 'special')
                rows.append({'name': name, 'path': str(path), 'type': kind,
                             'content_acquired': False, 'scope_allowed': not self.denied(path)})
            if signature(os.fstat(chain.fd)) != before or sorted(os.listdir(chain.fd)) != names:
                raise ValueError('PROJECT_DIRECTORY_CHANGED')
            token = identity([root['binding_id'], directory, before, rows])
        result = item_page(rows, offset, limit, 'entries', token, expected_inventory_id)
        result.update(directory=directory, root=root, symlinks_followed=False)
        return result

    def file_metadata(self, directory, path):
        relative_parts(path)
        absolute = str(Path(directory) / path)
        self.root_for(absolute)  # exclusions and the deepest repository boundary
        with self.directory(str(Path(absolute).parent)) as (chain, root):
            namespace = []
            reader = EvidenceReader(root['path'], require_private=False)
            with reader.file(chain, Path(absolute).name, namespace) as stream:
                size, digest = stream_identity(stream)
                sig = signature(os.fstat(stream.fileno()))
                binding = [(part, portable_numbers(value)) for _, part, _, value in chain.bindings]
            row = {'path': path, 'requested_path': absolute, 'canonical_path': absolute,
                   'root_id': root['root_id'], 'root_binding_id': root['binding_id'],
                   'size_bytes': size, 'sha256': digest, 'file_signature': portable_numbers(sig),
                   'ancestor_bindings': binding, 'type': 'file'}
            row['file_id'] = identity({k: v for k, v in row.items() if k != 'path'})
            return row

    @verified_read
    def project_manifest(self, directory, paths, offset=0, limit=100, expected_inventory_id=None):
        pagination(offset, limit, 100)
        if not isinstance(paths, list) or not paths or not all(isinstance(p, str) for p in paths):
            raise ValueError('PROJECT_INVALID_SELECTION')
        if len(set(paths)) != len(paths):
            raise ValueError('PROJECT_DUPLICATE_SELECTION')
        with self.directory(directory) as (_, root):
            rows = [self.file_metadata(directory, path) for path in sorted(paths)]
            # Reopen every selected identity after hashing later members.
            for row in rows:
                with self.directory(str(Path(row['requested_path']).parent)) as (chain, selected_root):
                    with EvidenceReader(selected_root['path'], require_private=False).file(
                            chain, Path(row['requested_path']).name) as stream:
                        if (portable_numbers(signature(os.fstat(stream.fileno()))) != row['file_signature'] or
                                [(p, portable_numbers(v)) for _, p, _, v in chain.bindings] != row['ancestor_bindings'] or
                                selected_root['binding_id'] != row['root_binding_id']):
                            raise ValueError('PROJECT_FILE_BINDING_CHANGED')
            token = identity([directory, root['binding_id'], rows])
        result = item_page(rows, offset, limit, 'files', token, expected_inventory_id)
        result.update(directory=directory, root=root, paths=sorted(paths),
                      selection_mode='explicit_files', snapshot=False)
        return result

    @verified_read
    def project_file(self, path, expected_file_id, offset=0, limit=8192):
        pagination(offset, limit, PAGE_BYTES)
        if not isinstance(expected_file_id, str) or not DIGEST.fullmatch(expected_file_id):
            raise ValueError('PROJECT_INVALID_EXPECTED_IDENTITY')
        absolute_path(path)
        row = self.file_metadata(str(Path(path).parent), Path(path).name)
        # file_id does not depend on the caller's relative spelling in manifest.
        # Compare the canonical metadata identity used by both APIs.
        if row['file_id'] != expected_file_id:
            raise ValueError('PROJECT_FILE_CONFLICT')
        with self.directory(str(Path(path).parent)) as (chain, root):
            with EvidenceReader(root['path'], require_private=False).file(chain, Path(path).name) as stream:
                if portable_numbers(signature(os.fstat(stream.fileno()))) != row['file_signature']:
                    raise ValueError('PROJECT_FILE_CHANGED')
                if offset > row['size_bytes']:
                    raise ValueError('PROJECT_OFFSET_BEYOND_EOF')
                stream.seek(offset)
                chunk = stream.read(limit)
                stream.seek(0)
                if stream_identity(stream) != (row['size_bytes'], row['sha256']):
                    raise ValueError('PROJECT_FILE_CHANGED')
                verify_page(stream, offset, chunk)
            if [(p, portable_numbers(v)) for _, p, _, v in chain.bindings] != row['ancestor_bindings']:
                raise ValueError('PROJECT_FILE_BINDING_CHANGED')
        return dict(byte_page(chunk, row['size_bytes'], row['sha256'], offset),
                    path=path, file_id=expected_file_id, root=root)

    def repo(self, repository_id, expected_binding_id=None):
        if not isinstance(repository_id, str) or repository_id not in self.repositories:
            raise ValueError('PROJECT_REPOSITORY_NOT_COVERED')
        binding = self.repositories[repository_id]
        if repository_binding(Path(binding['worktree'])) != binding:
            raise ValueError('PROJECT_REPOSITORY_BINDING_CHANGED')
        token = identity(binding)
        if expected_binding_id is not None and expected_binding_id != token:
            raise ValueError('PROJECT_REPOSITORY_BINDING_CONFLICT')
        return binding, token

    def commit(self, binding, revision):
        if (not isinstance(revision, str) or not revision or revision.startswith('-') or
                not re.fullmatch(r'[A-Za-z0-9_./~^{}@+\-]+', revision)):
            raise ValueError('PROJECT_INVALID_REVISION')
        value = local_git(binding, 'rev-parse', '--verify', '--end-of-options',
                          revision + '^{commit}').decode().strip()
        if not OID.fullmatch(value):
            raise ValueError('PROJECT_INVALID_COMMIT')
        return value

    def tree_rows(self, binding, commit, subtree):
        if subtree:
            relative_parts(subtree)
        if self.denied(Path(binding['worktree']) / subtree):
            raise ValueError('PROJECT_SCOPE_DENIED')
        root = binding
        tree = local_git(root, 'rev-parse', '--verify', commit + '^{tree}').decode().strip()
        # Exact path lookup using literal pathspecs, then enumerate that tree.
        selected = tree
        if subtree:
            rows = self.parse_tree(local_git(root, 'ls-tree', '-z', '-l', tree, '--', subtree))
            if len(rows) != 1 or rows[0]['path'] != subtree or rows[0]['type'] != 'tree':
                raise ValueError('PROJECT_GIT_SUBTREE_ABSENT')
            selected = rows[0]['object_id']
        rows = self.parse_tree(local_git(root, 'ls-tree', '-r', '-t', '-z', '-l', selected))
        for row in rows:
            row['path'] = (subtree + '/' if subtree else '') + row['path']
        return tree, selected, rows

    @staticmethod
    def parse_tree(raw):
        rows = []
        for line in raw.split(b'\0'):
            if not line:
                continue
            header, name = line.split(b'\t', 1)
            mode, kind, oid, size = header.split()
            path = name.decode('utf-8', errors='strict')
            relative_parts(path)
            rows.append({'path': path, 'mode': mode.decode(), 'type': kind.decode(),
                         'object_id': oid.decode(), 'size_bytes': None if size == b'-' else int(size),
                         'content_acquired': False})
        return rows

    @verified_read
    def project_git_tree(self, repository_id, revision, subtree='', offset=0, limit=100,
                         expected_inventory_id=None, expected_binding_id=None):
        pagination(offset, limit, 100)
        if offset and (not isinstance(revision, str) or not OID.fullmatch(revision)):
            raise ValueError('PROJECT_FROZEN_COMMIT_REQUIRED')
        binding, token = self.repo(repository_id, expected_binding_id)
        commit = self.commit(binding, revision)
        tree, selected, rows = self.tree_rows(binding, commit, subtree)
        inventory = identity([token, commit, tree, subtree, selected, rows])
        self.repo(repository_id, token)
        result = item_page(rows, offset, limit, 'entries', inventory, expected_inventory_id)
        result.update(repository_id=repository_id, repository=binding, binding_id=token,
                      requested_revision=revision, commit=commit, tree=tree, subtree=subtree,
                      selected_tree=selected, immutable_objects=True)
        return result

    @verified_read
    def project_git_blob(self, repository_id, commit, path, expected_binding_id,
                         expected_object_id, offset=0, limit=8192):
        pagination(offset, limit, PAGE_BYTES)
        if not isinstance(expected_binding_id, str) or not DIGEST.fullmatch(expected_binding_id):
            raise ValueError('PROJECT_INVALID_EXPECTED_BINDING')
        if not isinstance(commit, str) or not OID.fullmatch(commit):
            raise ValueError('PROJECT_FROZEN_COMMIT_REQUIRED')
        if not isinstance(expected_object_id, str) or not OID.fullmatch(expected_object_id):
            raise ValueError('PROJECT_INVALID_OBJECT_ID')
        relative_parts(path)
        if self.denied(Path(self.repositories.get(repository_id, {}).get('worktree', '/')) / path):
            raise ValueError('PROJECT_SCOPE_DENIED')
        binding, token = self.repo(repository_id, expected_binding_id)
        if self.commit(binding, commit) != commit:
            raise ValueError('PROJECT_COMMIT_CONFLICT')
        rows = self.parse_tree(local_git(binding, 'ls-tree', '-z', '-l', commit, '--', path))
        if len(rows) != 1 or rows[0]['path'] != path or rows[0]['type'] != 'blob':
            raise ValueError('PROJECT_GIT_BLOB_PATH_ABSENT_OR_NOT_BLOB')
        row = rows[0]
        if row['object_id'] != expected_object_id:
            raise ValueError('PROJECT_GIT_BLOB_MEMBERSHIP_CONFLICT')
        if offset > row['size_bytes']:
            raise ValueError('PROJECT_OFFSET_BEYOND_EOF')
        digest = hashlib.sha256()
        object_hash = hashlib.new('sha1' if len(expected_object_id) == 40 else 'sha256')
        object_hash.update(('blob %d\0' % row['size_bytes']).encode())
        size, chunks = 0, []
        try:
            with git_invocation(binding, 'cat-file', 'blob', expected_object_id) as (command, options), \
                    subprocess.Popen(command, **options, stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL) as process:
                try:
                    while True:
                        data = process.stdout.read(1024 * 1024)
                        if not data:
                            break
                        digest.update(data)
                        object_hash.update(data)
                        start, end = max(offset, size), min(offset + limit, size + len(data))
                        if start < end:
                            chunks.append(data[start - size:end - size])
                        size += len(data)
                    if process.wait(timeout=30):
                        raise ValueError('PROJECT_GIT_OBJECT_UNAVAILABLE')
                finally:
                    if process.poll() is None:
                        process.kill()
                        process.wait()
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ValueError('PROJECT_GIT_BACKEND_INTERRUPTED') from exc
        if size != row['size_bytes'] or object_hash.hexdigest() != expected_object_id:
            raise ValueError('PROJECT_GIT_BLOB_IDENTITY_CONFLICT')
        self.repo(repository_id, token)
        return dict(byte_page(b''.join(chunks), size, digest.hexdigest(), offset),
                    repository_id=repository_id, binding_id=token, repository=binding,
                    commit=commit, path=path, object_id=expected_object_id, mode=row['mode'],
                    type='symlink_blob' if row['mode'] == '120000' else 'blob')
