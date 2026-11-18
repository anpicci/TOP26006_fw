"""Exact-byte, nonexecuting prompt publication with atomic no-clobber linking.

Readiness derives from the upload and reopened file, never a second ready flag.
A deterministic private pending file makes the link/unlink crash gap recoverable.
"""
import contextlib
import hashlib
import os
from pathlib import Path
import stat

from artifacts import regular_reader


def filename(request_id):
    # Callers validate the bridge ID grammar before deriving any path.
    return 'CODEX_PROMPT_' + request_id + '.md'


@contextlib.contextmanager
def prompt_directory(workspace, create=False):
    root = Path(workspace)
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    with contextlib.ExitStack() as stack:
        fd = os.open(root, flags)
        stack.callback(os.close, fd)
        for component in ('reports', 'prompts'):
            if create:
                try:
                    os.mkdir(component, mode=0o700, dir_fd=fd)
                except FileExistsError:
                    pass
            fd = os.open(component, flags, dir_fd=fd)
            stack.callback(os.close, fd)
        yield fd, root / 'reports' / 'prompts'
        if create:
            with prompt_directory(root) as (current, _):
                if inode(os.fstat(fd)) != inode(os.fstat(current)):
                    raise ValueError('PROMPT_DIRECTORY_CHANGED')


def inode(info):
    return info.st_dev, info.st_ino


def read_bound(directory, name, content):
    with regular_reader(name, dir_fd=directory) as stream:
        info = os.fstat(stream.fileno())
        actual = stream.read(len(content) + 1)
        current = os.stat(name, dir_fd=directory, follow_symlinks=False)
        if inode(current) != inode(info) or actual != content:
            raise ValueError('DEPOSIT_CONFLICT_OR_CHANGED')
        return actual


def publish_absent(directory, source, target):
    # Atomic visibility and absence check, including concurrent symlink inserts.
    os.link(source, target, src_dir_fd=directory, dst_dir_fd=directory, follow_symlinks=False)


def reconcile_link(directory, pending, name, content):
    """Remove only the proven publication alias left by an interrupted link.

    Caller holds the existing state database transaction, independently of the
    worker lock. Any unrecognized link/content is preserved and refused.
    """
    try:
        source = os.stat(pending, dir_fd=directory, follow_symlinks=False)
        target = os.stat(name, dir_fd=directory, follow_symlinks=False)
    except FileNotFoundError:
        return
    if inode(source) != inode(target):
        return
    if not stat.S_ISREG(source.st_mode) or source.st_nlink != 2 or source.st_uid != os.getuid():
        raise ValueError('UNRECOGNIZED_DEPOSIT_LINK')
    fd = os.open(pending, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    with os.fdopen(fd, 'rb') as stream:
        if inode(os.fstat(stream.fileno())) != inode(source) or stream.read(len(content) + 1) != content:
            raise ValueError('DEPOSIT_CONFLICT_OR_CHANGED')
    if inode(os.stat(pending, dir_fd=directory, follow_symlinks=False)) != inode(source):
        raise ValueError('DEPOSIT_PENDING_CHANGED')
    os.unlink(pending, dir_fd=directory)
    os.fsync(directory)


def prepare_pending(directory, pending, content):
    fd = os.open(pending, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK,
                 0o600, dir_fd=directory)
    with os.fdopen(fd, 'r+b') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid():
            raise ValueError('UNSAFE_DEPOSIT_PENDING')
        prefix = stream.read(len(content) + 1)
        if not content.startswith(prefix):
            raise ValueError('DEPOSIT_PENDING_CONFLICT')
        # An interrupted write is recoverable by exact prefix extension only.
        # Never truncate, overwrite or discard existing bytes.
        stream.write(content[len(prefix):])
        stream.flush()
        os.fsync(stream.fileno())
        if inode(os.stat(pending, dir_fd=directory, follow_symlinks=False)) != inode(info):
            raise ValueError('DEPOSIT_PENDING_CHANGED')


def publish(workspace, request_id, content):
    name = filename(request_id)
    pending = '.' + name + '.pending'
    duplicate = False
    with prompt_directory(workspace, create=True) as (directory, root):
        reconcile_link(directory, pending, name, content)
        try:
            read_bound(directory, name, content)
            duplicate = True
        except FileNotFoundError:
            prepare_pending(directory, pending, content)
            try:
                publish_absent(directory, pending, name)
            except FileExistsError:
                duplicate = True
            reconcile_link(directory, pending, name, content)
        os.fsync(directory)
        read_bound(directory, name, content)
    return {'request_id': request_id, 'transfer_id': request_id, 'path': str(root / name),
            'size_bytes': len(content), 'prompt_sha256': hashlib.sha256(content).hexdigest(),
            'state': 'DEPOSITED', 'duplicate_deposit': duplicate, 'execution_started': False}


def consume(workspace, request_id, content):
    with prompt_directory(workspace) as (directory, _):
        return read_bound(directory, filename(request_id), content)
