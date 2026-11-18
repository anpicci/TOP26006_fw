"""Canonical task evidence and lossless, task-scoped artifact reads."""
import base64
import contextlib
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile

from repository_task import git, governance, snapshot

PAGE_BYTES = 32768


def reserve_evidence(root, request_id):
    root = Path(root).resolve(strict=True)
    for n in range(10000):
        path = root / (request_id if not n else request_id + '_rerun_%03d' % n)
        try:
            path.mkdir(mode=0o700)
            return path
        except FileExistsError:
            continue
    raise ValueError('EVIDENCE_COLLISION_LIMIT')


def tracked_tree(root, destination):
    """Freeze tracked worktree postimages, including mode/deletion and symlinks.

    Index and refs are recorded separately. These private trees are not exposed
    by the artifact API. No Git index/ref/object writes in the selected repo.
    """
    root, destination = Path(root), Path(destination)
    destination.mkdir(mode=0o700)
    for raw in git(root, 'ls-files', '-z').split(b'\0'):
        if not raw:
            continue
        relative = Path(os.fsdecode(raw))
        source = root / relative
        if not source.exists() and not source.is_symlink():
            continue
        if source.is_dir():
            # Gitlinks have independent ownership; the selected repository's
            # gitlink delta is captured by HEAD/index evidence, not traversed.
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_symlink():
            target.symlink_to(os.readlink(source))
        else:
            if not source.resolve().is_relative_to(root.resolve()):
                raise ValueError('TRACKED_PATH_ESCAPES_ROOT')
            shutil.copyfile(source, target, follow_symlinks=False)
            target.chmod(stat.S_IMODE(source.stat().st_mode))


def begin_evidence(folder, receipt, request_id):
    evidence = reserve_evidence(receipt['evidence_root'], request_id)
    receipt['evidence_directory'] = str(evidence)
    receipt['report_path'] = str(evidence / (request_id + '_report.md'))
    receipt['patch_path'] = str(evidence / (request_id + '_worktree_diff.patch'))
    info = evidence.stat()
    receipt['evidence_directory_identity'] = [info.st_dev, info.st_ino]
    for i, root in enumerate(receipt['repositories'].values()):
        key = list(receipt['repositories'])[i]
        if receipt['repositories_before'][key]['tracked_dirty']:
            tracked_tree(root, folder / ('before_%d' % i))
    return receipt


def regular_bytes(path):
    with regular_reader(path) as stream:
        return stream.read()


@contextlib.contextmanager
def regular_reader(path, dir_fd=None, *, require_private=True):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=dir_fd)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or (require_private and info.st_nlink != 1):
            raise ValueError('ARTIFACT_MUST_BE_PRIVATE_REGULAR_FILE')
        yield stream


def stream_identity(stream, destination=None):
    digest, size = hashlib.sha256(), 0
    while True:
        chunk = stream.read(1024 * 1024)
        if not chunk:
            break
        digest.update(chunk)
        size += len(chunk)
        if destination is not None:
            destination.write(chunk)
    return size, digest.hexdigest()


def file_identity(path):
    with regular_reader(path) as stream:
        return stream_identity(stream)


def evidence_directory(receipt, request_id):
    evidence = Path(receipt['evidence_directory'])
    info = evidence.lstat()
    if (not stat.S_ISDIR(info.st_mode) or
            evidence.resolve().parent != Path(receipt['evidence_root']).resolve() or
            [info.st_dev, info.st_ino] != receipt['evidence_directory_identity']):
        raise ValueError('EVIDENCE_DIRECTORY_IDENTITY_CHANGED')
    if (Path(receipt['report_path']) != evidence / (request_id + '_report.md') or
            Path(receipt['patch_path']) != evidence / (request_id + '_worktree_diff.patch')):
        raise ValueError('CANONICAL_EVIDENCE_PATH_MISMATCH')
    return evidence


def evidence_sources(receipt, request_id):
    evidence = evidence_directory(receipt, request_id)
    sources = []
    for current, dirs, files in os.walk(evidence, followlinks=False):
        if any((Path(current) / name).is_symlink() for name in dirs):
            raise ValueError('ARTIFACT_SYMLINK_DIRECTORY')
        for name in sorted(files):
            path = Path(current) / name
            sources.append((path.relative_to(evidence).as_posix(), path))
    return sources


@contextlib.contextmanager
def partial_evidence_reader(receipt, request_id, name):
    evidence = evidence_directory(receipt, request_id)
    relative = Path(name)
    if relative.is_absolute() or not relative.parts or any(p in ('.', '..') for p in relative.parts):
        raise ValueError('ARTIFACT_PATH_ESCAPES_EVIDENCE')
    # Pin the reserved directory, then open each component without following
    # links. A swapped parent cannot redirect byte-page reads outside it.
    fd = os.open(evidence, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if [info.st_dev, info.st_ino] != receipt['evidence_directory_identity']:
            raise ValueError('EVIDENCE_DIRECTORY_IDENTITY_CHANGED')
        for part in relative.parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        with regular_reader(relative.name, dir_fd=fd) as stream:
            yield stream
    finally:
        os.close(fd)


def freeze_artifacts(folder, sources):
    """Allowlist files into an immutable-by-identity retrieval namespace."""
    destination = folder / 'artifacts'
    destination.mkdir(mode=0o700, exist_ok=True)
    rows = []
    for name, path in sources:
        artifact_id = '%04d' % len(rows)
        target = destination / artifact_id
        with regular_reader(path) as source, target.open('xb') as destination_stream:
            size, digest = stream_identity(source, destination_stream)
        rows.append({'artifact_id': artifact_id, 'name': name, 'size_bytes': size,
                     'sha256': digest, 'source_path': str(path)})
    with (folder / 'artifacts.json').open('x', encoding='utf-8') as stream:
        json.dump(rows, stream, ensure_ascii=False)
    # Reopen and validate the serialized consumer manifest, not builder memory.
    for row in json.loads((folder / 'artifacts.json').read_bytes()):
        with regular_reader(destination / row['artifact_id']) as stream:
            size, digest = stream_identity(stream)
        if size != row['size_bytes'] or digest != row['sha256']:
            raise ValueError('ARTIFACT_FREEZE_INTEGRITY')
    return rows


def patch_sections(content, repositories):
    """Independent repository patches use the existing explicit section labels."""
    if len(repositories) == 1:
        return {next(iter(repositories)): content}
    sections, selected = {}, None
    for line in content.splitlines(keepends=True):
        if line.startswith(b'# repository_id: '):
            selected = line[len(b'# repository_id: '):].strip().decode('utf-8')
            if selected not in repositories or selected in sections:
                raise ValueError('PATCH_REPOSITORY_SECTION_MISMATCH')
            sections[selected] = bytearray()
        elif selected is not None:
            sections[selected].extend(line)
        elif line.strip():
            raise ValueError('PATCH_REPOSITORY_SECTION_REQUIRED')
    return {key: bytes(sections.get(key, b'')) for key in repositories}


def validate_patch(folder, receipt, expected, candidate, strips):
    """Apply both encodings to private indexes, compare full resulting trees.

    No source index, ref or object writes. Source objects are read through an
    invocation-local alternate. Context, hunk ordering, binary encoding and
    native dirty-baseline prefixes need not be byte-identical.
    """
    sections = patch_sections(candidate, receipt['repositories'])
    validated_strips = {}
    validation_trees = {}
    for i, (repo_id, root) in enumerate(receipt['repositories'].items()):
        with tempfile.TemporaryDirectory(prefix='patch_check_', dir=folder) as temporary:
            private = Path(temporary)
            env = {k: v for k, v in os.environ.items()
                   if k in ('HOME', 'PATH', 'USER', 'LOGNAME', 'LANG', 'LC_ALL')}
            env['GIT_ALTERNATE_OBJECT_DIRECTORIES'] = str(
                (Path(root) / os.fsdecode(git(root, 'rev-parse', '--git-path', 'objects')).strip()).resolve())
            env['GIT_INDEX_FILE'] = str(private / 'index')

            def run(*args, data=None, work=None):
                return subprocess.run(['git', '--git-dir=' + str(private / 'objects.git'),
                                       *args], cwd=work or private, env=env, input=data,
                                      capture_output=True, timeout=60)

            def required(*args, work=None):
                result = run(*args, work=work)
                if result.returncode:
                    raise ValueError('PATCH_BASE_EXTRACTION_FAILED')
                return result.stdout

            required('init', '--bare', '-q')
            if receipt['repositories_before'][repo_id]['tracked_dirty']:
                # Import raw frozen bytes, not git-add's clean filters or EOL
                # normalization. The no-index task delta also uses raw bytes.
                frozen = folder / ('before_%d' % i)
                entries = bytearray()
                for current, dirs, files in os.walk(frozen, followlinks=False):
                    links = [name for name in dirs if (Path(current) / name).is_symlink()]
                    dirs[:] = [name for name in dirs if name not in links]
                    for name in files + links:
                        path = Path(current) / name
                        mode = ('120000' if path.is_symlink() else
                                '100755' if path.stat().st_mode & stat.S_IXUSR else '100644')
                        content = os.fsencode(os.readlink(path)) if path.is_symlink() else regular_bytes(path)
                        result = run('hash-object', '-w', '--no-filters', '--stdin', data=content)
                        if result.returncode:
                            raise ValueError('PATCH_BASE_EXTRACTION_FAILED')
                        entries.extend(mode.encode() + b' ' + result.stdout.strip() + b'\t' +
                                       os.fsencode(path.relative_to(frozen)) + b'\0')
                if run('update-index', '-z', '--index-info', data=bytes(entries)).returncode:
                    raise ValueError('PATCH_BASE_EXTRACTION_FAILED')
            else:
                required('read-tree', receipt['repositories_before'][repo_id]['head'])
            baseline = required('write-tree').strip().decode('ascii')

            def applied_tree(content, strip):
                required('read-tree', baseline)
                if content:
                    result = run('apply', '--cached', '--binary', '--unidiff-zero', '--whitespace=nowarn',
                                 '-p%d' % strip, '-', data=content)
                    if result.returncode:
                        return None
                return required('write-tree')

            target = applied_tree(expected[repo_id], strips[repo_id])
            if target is None:
                raise ValueError('MEASURED_PATCH_CONSUMER_FAILED')
            for strip in dict.fromkeys((strips[repo_id], 1, 2)):
                candidate_tree = applied_tree(sections[repo_id], strip)
                if candidate_tree == target:
                    validated_strips[repo_id] = strip
                    validation_trees[repo_id] = {
                        'baseline_tree': baseline,
                        'measured_result_tree': target.strip().decode('ascii'),
                        'supplied_result_tree': candidate_tree.strip().decode('ascii'),
                        'baseline_head': receipt['repositories_before'][repo_id]['head'],
                    }
                    break
            else:
                raise ValueError('PATCH_MISMATCH: ' + repo_id + '; no compatible -p1/-p2 encoding of admission task delta')
    return validated_strips, validation_trees


def finish_evidence(folder, receipt, request_id):
    repositories = receipt['repositories']
    after = {key: snapshot(path) for key, path in repositories.items()}
    patch = bytearray()
    scope_findings = []
    patch_strip_components = {}
    expected = {}
    for i, (repo_id, root) in enumerate(repositories.items()):
        # Compare exact before/after tracked bytes rather than equating the whole
        # tree or manufacturing an empty coding patch. --binary is lossless.
        if receipt['repositories_before'][repo_id]['tracked_dirty']:
            tracked_tree(root, folder / ('after_%d' % i))
            result = subprocess.run(['git', '-c', 'core.quotePath=true', 'diff', '--no-index',
                                 '--binary', '--no-ext-diff', '--no-textconv',
                                 '--src-prefix=a/', '--dst-prefix=b/',
                                 'before_%d' % i, 'after_%d' % i], cwd=folder,
                                capture_output=True, timeout=60)
            if result.returncode not in (0, 1):
                raise ValueError('TASK_DELTA_EXTRACTION_FAILED')
            delta = result.stdout
            # Keep native bytes, including arbitrary quoted paths and binary
            # hunks. A textual prefix replacement could corrupt file content.
            # git apply -p2 strips a/b and the private before_N/after_N label.
            patch_strip_components[repo_id] = 2
            names = subprocess.run(['git', 'diff', '--no-index', '--name-only', '-z',
                                    'before_%d' % i, 'after_%d' % i], cwd=folder,
                                   capture_output=True, timeout=60)
            if names.returncode not in (0, 1):
                raise ValueError('TASK_DELTA_NAMES_FAILED')
            changed = [os.fsdecode(p).split('/', 1)[1] for p in names.stdout.split(b'\0') if p]
        else:
            patch_strip_components[repo_id] = 1
            # Native diff handles gitlinks, renames and all Git path quoting.
            delta = git(root, 'diff', '--binary', '--no-ext-diff', '--no-textconv',
                        receipt['repositories_before'][repo_id]['head'], '--')
            changed = [os.fsdecode(p) for p in git(root, 'diff', '--name-only', '-z',
                       receipt['repositories_before'][repo_id]['head'], '--').split(b'\0') if p]
        patterns = []
        for scope in receipt['contract']['allowed_to_modify']:
            if isinstance(scope, dict):
                key, value = next(iter(scope.items()))
            else:
                key, value = scope.split(':', 1)
            if key == repo_id and isinstance(value, str):
                patterns.append(value)
        for path in changed:
            if not any(fnmatch.fnmatchcase(path, p) or path.startswith(p.rstrip('/') + '/') for p in patterns):
                scope_findings.append({'repository_id': repo_id, 'path': path, 'finding': 'outside_outer_write_scope'})
        if len(repositories) > 1 and delta:
            # Deliberately separate Git patches: apply each section in the named
            # independent repository, never stage a nested repository in TOP.
            patch.extend(('# repository_id: ' + repo_id + '\n').encode())
        patch.extend(delta)
        expected[repo_id] = delta
    evidence = evidence_directory(receipt, request_id)
    report, patch_path = Path(receipt['report_path']), Path(receipt['patch_path'])
    bookkeeping_path = evidence / 'bridge_bookkeeping.json'
    if os.path.lexists(bookkeeping_path):
        raise ValueError('BRIDGE_BOOKKEEPING_COLLISION')
    report_producer = 'executor_file'
    evidence_findings = []
    if not os.path.lexists(report):
        # Final message is authored by Codex; publishing its bytes is transport,
        # not inventing a report or certifying its semantic completeness.
        try:
            final_message = regular_bytes(folder / 'result.txt')
        except FileNotFoundError:
            report_producer = 'absent'
            evidence_findings.append('FINAL_MESSAGE_ABSENT: no executor report or final-message file')
        else:
            with report.open('xb') as stream:
                stream.write(final_message)
            report_producer = 'exact_final_message_capture'
    patch_producer = 'executor_file'
    patch_validation = 'not_validated'
    patch_consumer_checks = {}
    if not os.path.lexists(patch_path):
        if receipt['contract'].get('patch_producer', 'codex') == 'codex_or_host':
            with patch_path.open('xb') as stream:
                stream.write(patch)
            patch_producer = 'host_measured_task_delta'
        else:
            patch_producer = 'absent'
            evidence_findings.append('REQUIRED_EXECUTOR_PATCH_ABSENT: host fallback was not selected in the authored prompt')
    if patch_producer != 'absent':
        supplied = regular_bytes(patch_path)
        try:
            if receipt['contract']['patch_kind_expected'] == 'empty_no_changes' and (patch or supplied):
                raise ValueError('PATCH_KIND_MISMATCH: empty_no_changes requires empty measured and supplied patches')
            patch_strip_components, patch_consumer_checks = validate_patch(folder, receipt, expected, supplied, patch_strip_components)
            patch_validation = 'equivalent_trees_after_private_git_apply'
        except ValueError as exc:
            # Preserve conflicting evidence and publish its exact bytes as
            # failed evidence, never overwrite it or report task completion.
            evidence_findings.append(str(exc))
            patch_strip_components = {}
    master = governance(receipt['governance_root'], receipt['governance_dependencies'])
    bookkeeping = {
        'request_id': request_id, 'prompt_sha256': hashlib.sha256((folder / 'prompt.txt').read_bytes()).hexdigest(),
        'repositories_before': receipt['repositories_before'], 'repositories_after': after,
        'governance_master_after': master, 'cli_success_is_not_review_or_acceptance': True,
        'report_producer': report_producer,
        'patch_producer': patch_producer,
        'patch_baseline': 'admission tracked worktree; initial HEAD for clean state, frozen postimages for dirty state',
        'patch_validation': patch_validation,
        'patch_consumer_checks': patch_consumer_checks,
        'evidence_findings': evidence_findings,
        'scope_findings': scope_findings,
        'patch_strip_components': patch_strip_components,
        'FOLD': str(evidence), 'scp': 'scp -r apiccine@glados.crc.nd.edu:${FOLD} .',
    }
    with bookkeeping_path.open('x', encoding='utf-8') as stream:
        json.dump(bookkeeping, stream, indent=2)
    sources = evidence_sources(receipt, request_id)
    sources.extend(('transport/' + name, folder / name) for name in ('prompt.txt', 'result.txt', 'events.jsonl', 'stderr.log')
                   if name != 'result.txt' or os.path.lexists(folder / name))
    rows = freeze_artifacts(folder, sources)
    return {'repositories_after': after, 'post_run_master_oid': master,
            'report_sha256': (hashlib.sha256(regular_bytes(report)).hexdigest() if report_producer != 'absent' else None),
            'patch_sha256': (hashlib.sha256(regular_bytes(patch_path)).hexdigest() if patch_producer != 'absent' else None),
            'patch_kind': ('prompt_local' if patch else 'empty_no_changes') if not evidence_findings else 'unvalidated',
            'report_producer': report_producer, 'patch_producer': patch_producer,
            'patch_validation': patch_validation, 'evidence_findings': evidence_findings,
            'patch_consumer_checks': patch_consumer_checks,
            'artifacts': rows, 'FOLD': str(evidence), 'scp': bookkeeping['scp'],
            'report_semantic_completeness': 'review_required',
            'scope_findings': scope_findings,
            'patch_strip_components': patch_strip_components,
            'tracked_state_unchanged': after == receipt['repositories_before']}


def artifact_page(folder, row, offset, limit):
    if type(offset) is not int or type(limit) is not int or offset < 0 or not 1 <= limit <= PAGE_BYTES:
        raise ValueError('INVALID_ARTIFACT_PAGINATION')
    with regular_reader(folder / 'artifacts' / row['artifact_id']) as stream:
        size, digest = stream_identity(stream)
        if size != row['size_bytes'] or digest != row['sha256']:
            raise ValueError('ARTIFACT_CHANGED')
        stream.seek(offset)
        chunk = stream.read(limit)
    return {**row, 'encoding': 'base64', 'data': base64.b64encode(chunk).decode('ascii'),
            'offset': offset, 'next_offset': offset + len(chunk), 'has_more': offset + len(chunk) < size,
            'chunk_sha256': hashlib.sha256(chunk).hexdigest()}
