"""Read external evidence without task state, snapshots or execution.

Linux descriptor-relative traversal pins every component. Revalidate namespace
bindings and metadata before returning; callers still need a final manifest
check because this is optimistic acquisition, not a multi-file transaction.
"""
import base64
import contextlib
import hashlib
import json
import os
from pathlib import Path
import re
import stat

from artifacts import PAGE_BYTES, regular_reader, stream_identity

MANIFEST_ITEMS = 100
DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
_paths_absent = object()


def relative_parts(value):
    if (not isinstance(value, str) or not value or value.startswith('/') or
            '\x00' in value or any(p in ('', '.', '..') for p in value.split('/'))):
        raise ValueError('INVALID_EVIDENCE_RELATIVE_PATH')
    # JSON transports Unicode, never surrogateescaped filesystem names.
    try:
        value.encode('utf-8', errors='strict')
    except UnicodeError as exc:
        raise ValueError('EVIDENCE_PATH_NOT_UTF8') from exc
    return value.split('/')


def inode(info):
    return info.st_dev, info.st_ino


def signature(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink,
            info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def verify_page(stream, offset, chunk):
    # Recheck the returned page directly after hashing. Same-size writes can
    # share filesystem timestamp granularity; bypass Python's read buffer.
    if os.pread(stream.fileno(), len(chunk), offset) != chunk:
        raise ValueError('EVIDENCE_FILE_CHANGED')


def pagination(offset, limit, maximum):
    if type(offset) is not int or type(limit) is not int or offset < 0 or not 1 <= limit <= maximum:
        raise ValueError('INVALID_EVIDENCE_PAGINATION')


class DirectoryChain:
    """A live chain, rooted at /, with explicit no-follow namespace checks."""
    def __init__(self, stack, root):
        self.stack = stack
        self.bindings = []
        self.fd = os.open('/', DIRECTORY_FLAGS)
        stack.callback(os.close, self.fd)
        root = Path(root)
        if not root.is_absolute() or '..' in root.parts:
            raise ValueError('EVIDENCE_ROOT_MUST_BE_ABSOLUTE')
        for part in root.parts[1:]:
            self.descend(part)

    def descend(self, part):
        parent = self.fd
        child = os.open(part, DIRECTORY_FLAGS, dir_fd=parent)
        self.stack.callback(os.close, child)
        self.bindings.append((parent, part, child, inode(os.fstat(child))))
        self.fd = child
        self.check()
        return child

    def check(self):
        for parent, part, child, identity in self.bindings:
            current = os.stat(part, dir_fd=parent, follow_symlinks=False)
            if (not stat.S_ISDIR(current.st_mode) or inode(current) != identity or
                    inode(os.fstat(child)) != identity):
                raise ValueError('EVIDENCE_DIRECTORY_CHANGED')


class EvidenceReader:
    def __init__(self, root, *, require_private=True):
        self.root = Path(root)
        self.require_private = require_private

    @contextlib.contextmanager
    def directory(self, directory):
        parts = relative_parts(directory)
        try:
            with contextlib.ExitStack() as stack:
                chain = DirectoryChain(stack, self.root)
                for part in parts:
                    chain.descend(part)
                yield chain
                chain.check()
        except OSError as exc:
            # Do not return host paths or incidental internal exception content.
            raise ValueError('EVIDENCE_UNAVAILABLE_OR_UNSAFE: errno=' + str(exc.errno)) from exc

    @contextlib.contextmanager
    def file(self, chain, path, namespace=None):
        parts = relative_parts(path)
        # Separate descriptors for each branch, all closed at this file's end.
        with contextlib.ExitStack() as stack:
            parent = chain.fd
            bindings = []
            for part in parts[:-1]:
                child = os.open(part, DIRECTORY_FLAGS, dir_fd=parent)
                stack.callback(os.close, child)
                bindings.append((parent, part, child))
                parent = child

            def check():
                chain.check()
                for above, part, child in bindings:
                    info = os.stat(part, dir_fd=above, follow_symlinks=False)
                    if not stat.S_ISDIR(info.st_mode) or inode(info) != inode(os.fstat(child)):
                        raise ValueError('EVIDENCE_DIRECTORY_CHANGED')

            check()
            if namespace is not None:
                namespace.extend((part, inode(os.fstat(child))) for _, part, child in bindings)
            # Refuse special files before opening, then check the opened object
            # again with the shared private-regular reader (including link count).
            before = os.stat(parts[-1], dir_fd=parent, follow_symlinks=False)
            if not stat.S_ISREG(before.st_mode) or (self.require_private and before.st_nlink != 1):
                raise ValueError('EVIDENCE_MUST_BE_PRIVATE_REGULAR_FILE')
            with regular_reader(parts[-1], dir_fd=parent, require_private=self.require_private) as stream:
                opened = os.fstat(stream.fileno())
                if signature(opened) != signature(before):
                    raise ValueError('EVIDENCE_FILE_CHANGED')
                check()
                yield stream
                check()
                if (signature(os.fstat(stream.fileno())) != signature(opened) or
                        signature(os.stat(parts[-1], dir_fd=parent, follow_symlinks=False)) != signature(opened)):
                    raise ValueError('EVIDENCE_FILE_CHANGED')

    def manifest(self, directory, offset=0, limit=100, expected_manifest_id=None, paths=_paths_absent):
        pagination(offset, limit, MANIFEST_ITEMS)
        selected = paths is not _paths_absent
        if selected:
            if not isinstance(paths, list) or not paths:
                raise ValueError('INVALID_EVIDENCE_SELECTION')
            paths = ['/'.join(relative_parts(path)) for path in paths]
            if len(set(paths)) != len(paths):
                raise ValueError('DUPLICATE_EVIDENCE_SELECTION')
            paths.sort()
        selection_mode = 'explicit_files' if selected else 'recursive'
        if (expected_manifest_id is not None and
                (not isinstance(expected_manifest_id, str) or not re.fullmatch('[0-9a-f]{64}', expected_manifest_id))):
            raise ValueError('INVALID_EXPECTED_MANIFEST_ID')
        if offset and expected_manifest_id is None:
            raise ValueError('EXPECTED_MANIFEST_ID_REQUIRED_FOR_NEXT_PAGE')
        rows, directories, files = [], [], []
        with self.directory(directory) as chain:
            base = chain.fd

            def walk(fd, prefix):
                before = os.fstat(fd)
                names = sorted(os.listdir(fd))
                directories.append((prefix, signature(before)))
                for name in names:
                    relative_parts(name)
                    path = prefix + name
                    info = os.stat(name, dir_fd=fd, follow_symlinks=False)
                    if stat.S_ISDIR(info.st_mode):
                        child = os.open(name, DIRECTORY_FLAGS, dir_fd=fd)
                        try:
                            if signature(os.fstat(child)) != signature(info):
                                raise ValueError('EVIDENCE_DIRECTORY_CHANGED')
                            walk(child, path + '/')
                        finally:
                            os.close(child)
                    else:
                        # Reopen via the pinned dossier, never via a host path.
                        with self.file(chain, path) as stream:
                            size, digest = stream_identity(stream)
                            files.append((path, signature(os.fstat(stream.fileno()))))
                        rows.append({'path': path, 'size_bytes': size, 'sha256': digest})
                if signature(os.fstat(fd)) != signature(before) or sorted(os.listdir(fd)) != names:
                    raise ValueError('EVIDENCE_DIRECTORY_CHANGED')

            if selected:
                # Only necessary ancestors and named files: never enumerate
                # excluded membership or bind volatile directory metadata.
                for path in paths:
                    namespace = []
                    with self.file(chain, path, namespace) as stream:
                        size, digest = stream_identity(stream)
                        files.append((path, signature(os.fstat(stream.fileno())), namespace))
                    rows.append({'path': path, 'size_bytes': size, 'sha256': digest})
            else:
                walk(base, '')
            # Detect changes to earlier entries while later files were hashed.
            for entry in files:
                path, expected = entry[:2]
                namespace = [] if selected else None
                with self.file(chain, path, namespace) as stream:
                    if signature(os.fstat(stream.fileno())) != expected:
                        raise ValueError('EVIDENCE_FILE_CHANGED')
                    if selected and namespace != entry[2]:
                        raise ValueError('EVIDENCE_DIRECTORY_CHANGED')
            for prefix, expected in directories:
                with contextlib.ExitStack() as stack:
                    fd = base
                    for part in prefix.rstrip('/').split('/') if prefix else []:
                        fd = os.open(part, DIRECTORY_FLAGS, dir_fd=fd)
                        stack.callback(os.close, fd)
                    if signature(os.fstat(fd)) != expected:
                        raise ValueError('EVIDENCE_DIRECTORY_CHANGED')
            chain.check()
            rows.sort(key=lambda row: row['path'])
            # Include directory inodes (including empty directories) so an
            # equal-byte directory replacement is visible between pages.
            identity = {'directory': directory, 'selection_mode': selection_mode,
                        'directories': directories, 'files': rows}
            if selected:
                identity.update(paths=paths, file_bindings=files, root=str(self.root),
                                ancestor_bindings=[(part, identity) for _, part, _, identity in chain.bindings])
            manifest_id = hashlib.sha256(json.dumps(identity, ensure_ascii=True, sort_keys=True,
                                                    separators=(',', ':')).encode()).hexdigest()
            if expected_manifest_id is not None and expected_manifest_id != manifest_id:
                raise ValueError('EVIDENCE_MANIFEST_CONFLICT')
            if offset > len(rows):
                raise ValueError('EVIDENCE_OFFSET_BEYOND_EOF')
            page = rows[offset:offset + limit]
        result = {'directory': directory, 'manifest_id': manifest_id, 'files': page,
                'offset': offset, 'next_offset': offset + len(page), 'has_more': offset + len(page) < len(rows),
                'total': len(rows), 'complete': True, 'omissions': [], 'manifest_frozen': False,
                'selection_mode': selection_mode}
        if selected:
            result['paths'] = paths
        return result

    def file_page(self, directory, path, expected_size_bytes, expected_sha256, offset=0, limit=8192):
        pagination(offset, limit, PAGE_BYTES)
        if (type(expected_size_bytes) is not int or expected_size_bytes < 0 or
                not isinstance(expected_sha256, str) or not re.fullmatch('[0-9a-f]{64}', expected_sha256)):
            raise ValueError('INVALID_EXPECTED_EVIDENCE_IDENTITY')
        with self.directory(directory) as chain, self.file(chain, path) as stream:
            size, digest = stream_identity(stream)
            if (size, digest) != (expected_size_bytes, expected_sha256):
                raise ValueError('EVIDENCE_FILE_CONFLICT')
            if offset > size:
                raise ValueError('EVIDENCE_OFFSET_BEYOND_EOF')
            stream.seek(offset)
            chunk = stream.read(limit)
            # Rehash after the page read. Metadata guards also detect same-size
            # in-place writes or replacements, including changes during hashing.
            stream.seek(0)
            if stream_identity(stream) != (size, digest):
                raise ValueError('EVIDENCE_FILE_CHANGED')
            verify_page(stream, offset, chunk)
        return {'directory': directory, 'path': path, 'size_bytes': size, 'sha256': digest,
                'encoding': 'base64', 'data': base64.b64encode(chunk).decode('ascii'),
                'offset': offset, 'chunk_size_bytes': len(chunk),
                'chunk_sha256': hashlib.sha256(chunk).hexdigest(),
                'next_offset': offset + len(chunk), 'has_more': offset + len(chunk) < size}
