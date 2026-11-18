"""Isolated simulated provider launch through an explicit fixture wrapper."""
from pathlib import Path
import shlex
import sys
import json
import os
import zipfile

_owned_archives = set()


def write_fake(path, source):
    path = Path(path)
    implementation = path.with_suffix('.py')
    implementation.write_text(source, encoding='utf-8')
    wrapper = path.with_name(path.name + '_fixture_wrapper')
    wrapper.write_text('#!/bin/sh\nexec "$@"\n')
    wrapper.chmod(0o700)
    path.write_text('#!/bin/sh\nexec ' + shlex.join([str(wrapper), sys.executable, '-S', str(implementation)]) + ' "$@"\n')
    path.chmod(0o700)


def retain_fixture_evidence(backend, request_id, label):
    """Optional exact serialized local evidence, never production acceptance."""
    selected = os.environ.get('GLADOS_BRIDGE_TEST_EVIDENCE')
    if not selected:
        return
    target = Path(selected)
    mode = 'a' if str(target) in _owned_archives else 'x'
    with backend.db() as db:
        row = db.execute('SELECT * FROM tasks WHERE id=?', (request_id,)).fetchone()
    receipt = json.loads(row['receipt'])
    folder = backend.root / request_id
    with zipfile.ZipFile(target, mode, compression=zipfile.ZIP_DEFLATED) as archive:
        prefix = label + '/' + request_id + '/'
        archive.writestr(prefix + 'receipt.json', json.dumps({
            'state': row['state'], 'digest': row['digest'], 'receipt': receipt}, indent=2))
        for name in ('prompt.txt', 'result.txt', 'events.jsonl', 'stderr.log', 'artifacts.json'):
            path = folder / name
            if path.is_file():
                archive.write(path, prefix + 'transport/' + name)
        received = folder / 'received.bin'
        if received.exists():
            import hashlib
            archive.writestr(prefix + 'consumer_input.json', json.dumps({
                'size_bytes': received.stat().st_size,
                'sha256': hashlib.sha256(received.read_bytes()).hexdigest()}))
        evidence = Path(receipt.get('evidence_directory', folder))
        if evidence != folder:
            for path in evidence.rglob('*'):
                if path.is_file() and not path.is_symlink():
                    archive.write(path, prefix + 'canonical/' + path.relative_to(evidence).as_posix())
    _owned_archives.add(str(target))
