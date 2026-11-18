"""Discriminating project/Git reader fixtures, retained when requested."""
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import project_reader as pr
from artifacts import regular_reader


def sha(data):
    return hashlib.sha256(data).hexdigest()


class ProjectReaderTests(unittest.TestCase):
    def setUp(self):
        retained = os.environ.get('GLADOS_BRIDGE_PROJECT_FIXTURES')
        self.temporary = None if retained else tempfile.TemporaryDirectory()
        self.base = Path(tempfile.mkdtemp(prefix=self._testMethodName + '_', dir=retained)
                         if retained else self.temporary.name)
        self.repo = self.base / 'workspace'
        self.repo.mkdir()
        self.run_git(self.repo, 'init', '-b', 'master', '--separate-git-dir', str(self.base / 'top.git'))
        (self.repo / 'governance').mkdir()
        source = Path(__file__).resolve().parents[2]
        registry = subprocess.check_output(['git', '-C', str(source), 'show',
                                            'refs/heads/master:governance/repositories.md'])
        (self.repo / 'governance/repositories.md').write_bytes(registry)
        self.originals = {'docs/雪.md': '雪€🦊'.encode() * 3700, 'docs/binary': bytes(range(256)) * 270,
                          'docs/empty': b'', 'docs/:(glob)*': b'literal magic', 'README.md': b'first'}
        for path, content in self.originals.items():
            self.put(self.repo / path, content)
        (self.repo / 'docs/link').symlink_to('雪.md')
        self.run_git(self.repo, 'add', '--', 'governance', 'docs', 'README.md')
        self.run_git(self.repo, 'commit', '-m', 'fixture initial')
        self.first = self.run_git(self.repo, 'rev-parse', 'HEAD').decode().strip()
        # A gitlink is deliberately not an acquired regular blob.
        self.run_git(self.repo, 'update-index', '--add', '--cacheinfo', '160000,' + self.first + ',docs/submodule')
        self.run_git(self.repo, 'commit', '-m', 'fixture gitlink')
        self.first = self.run_git(self.repo, 'rev-parse', 'HEAD').decode().strip()
        self.put(self.repo / 'README.md', b'second')
        self.run_git(self.repo, 'add', '--', 'README.md')
        self.run_git(self.repo, 'commit', '-m', 'fixture second')
        self.second = self.run_git(self.repo, 'rev-parse', 'HEAD').decode().strip()
        self.put(self.repo / 'README.md', b'dirty worktree')
        evidence = self.base / 'evidence'
        evidence.mkdir()
        self.profile = {'workspace_root': str(self.repo), 'evidence_root': str(evidence),
                        'repositories': {'TOP26006_fw': {'path': str(self.repo)}}}
        self.master = self.second
        self.inbox = SimpleNamespace(root=self.repo, profile=self.profile, check=lambda: self.master)
        self.reader = pr.ProjectReader(self.inbox)
        self.records = []
        self.acquisitions = []
        self.put(self.base / 'fixture_identity.json', json.dumps({'first': self.first, 'second': self.second,
                    'profile': self.profile, 'source_fingerprints': {p.name: sha(p.read_bytes())
                    for p in Path(__file__).parent.iterdir() if p.suffix in ('.py', '.mjs', '.json') and p.is_file()}},
                    indent=2).encode())

    @staticmethod
    def run_git(root, *args):
        env = pr.git_environment()
        env.update(GIT_AUTHOR_NAME='Reader Fixture', GIT_AUTHOR_EMAIL='fixture@example.invalid',
                   GIT_COMMITTER_NAME='Reader Fixture', GIT_COMMITTER_EMAIL='fixture@example.invalid')
        result = subprocess.run(['git', '-C', str(root), *args], env=env, capture_output=True, timeout=30)
        if result.returncode:
            raise AssertionError(result.stderr.decode(errors='replace'))
        return result.stdout

    @staticmethod
    def put(path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def tearDown(self):
        (self.base / 'observations.json').write_text(json.dumps(self.records, indent=2))
        (self.base / 'acquisitions.json').write_text(json.dumps(self.acquisitions, indent=2))
        if self.temporary:
            self.temporary.cleanup()

    def call(self, method, **args):
        record = {'method': method, 'args': json.loads(json.dumps(args))}
        self.records.append(record)
        try:
            record['result'] = getattr(self.reader, method)(**args)
            return record['result']
        except (ValueError, OSError) as exc:
            record['error'] = str(exc)
            raise

    def binding_only_hash(self, stream):
        # A gitfile's bytes are necessary binding metadata. Reject every
        # attempted project-content hash before it can consume excluded bytes.
        from artifacts import stream_identity
        self.assertEqual(Path(os.readlink('/proc/self/fd/' + str(stream.fileno()))).name, '.git')
        return stream_identity(stream)

    def recover(self, method, args, original, locator):
        pages, chunks, offset = [], [], 0
        while True:
            page = self.call(method, **args, offset=offset, limit=32767)
            chunk = base64.b64decode(page['data'], validate=True)
            self.assertEqual(page['offset'], offset)
            self.assertEqual(page['chunk_sha256'], sha(chunk))
            self.assertEqual(page['chunk_size_bytes'], len(chunk))
            self.assertEqual(page['next_offset'], offset + len(chunk))
            pages.append(page)
            chunks.append(chunk)
            offset = page['next_offset']
            if not page['has_more']:
                break
        recovered = b''.join(chunks)
        self.assertEqual(recovered, original)
        self.assertEqual(page['sha256'], sha(original))
        self.assertEqual(page['size_bytes'], len(original))
        self.assertTrue(page['eof'])
        authoritative = self.base / 'originals' / locator
        self.put(authoritative, original)
        self.acquisitions.append({'method': method, 'args': args, 'original': str(authoritative.relative_to(self.base)),
                                  'pages': pages})

    def test_files_inventory_selection_hardlinks_and_lossless_bytes(self):
        directory = self.repo / 'docs'
        os.link(directory / 'binary', directory / 'hardlink')
        os.mkfifo(directory / 'fifo')
        first = self.call('project_list', directory=str(directory), limit=2)
        rows, offset = first['entries'], first['next_offset']
        while first['has_more']:
            first = self.call('project_list', directory=str(directory), offset=offset, limit=2,
                              expected_inventory_id=first['inventory_id'])
            rows.extend(first['entries'])
            offset = first['next_offset']
        self.assertEqual({row['name']: row['type'] for row in rows}['fifo'], 'special')
        self.assertEqual({row['name']: row['type'] for row in rows}['link'], 'symlink')
        paths = ['雪.md', 'binary', 'empty', ':(glob)*', 'hardlink']
        with mock.patch.object(pr.os, 'listdir', side_effect=AssertionError('selected enumeration')):
            meta = self.call('project_manifest', directory=str(directory), paths=paths, limit=2)
            inventory, files = meta['inventory_id'], meta['files']
            self.put(directory / 'irrelevant', b'unrelated')
            while meta['has_more']:
                meta = self.call('project_manifest', directory=str(directory), paths=list(reversed(paths)), limit=2,
                                 offset=meta['next_offset'], expected_inventory_id=inventory)
                files.extend(meta['files'])
        for row in files:
            self.assertTrue(all(isinstance(value, str) for value in row['file_signature']))
            self.assertEqual(int(row['file_signature'][1]), (directory / row['path']).stat().st_ino)
            original = (directory / row['path']).read_bytes()
            self.recover('project_file', {'path': row['requested_path'], 'expected_file_id': row['file_id']},
                         original, 'filesystem/' + row['path'])
        self.call('project_manifest', directory=str(directory), paths=paths, expected_inventory_id=inventory)
        # Private artifact default remains strict and nonblocking on specials.
        for name in ('hardlink', 'link', 'fifo'):
            with self.assertRaises((ValueError, OSError)):
                with regular_reader(directory / name):
                    self.fail('private unsafe object accepted')

    def test_external_repository_gitfile_and_registered_worktree_bindings(self):
        external = self.base / 'external'
        external.mkdir()
        self.run_git(external, 'init', '-b', 'master')
        self.put(external / 'outside.md', b'outside workspace, configured')
        self.run_git(external, 'add', '--', 'outside.md')
        self.run_git(external, 'commit', '-m', 'fixture external')
        linked = self.base / 'linked'
        self.run_git(external, 'worktree', 'add', '--detach', str(linked), 'HEAD')
        self.profile['repositories']['topeft'] = {'path': str(external)}
        self.reader = pr.ProjectReader(self.inbox)
        roots = self.call('project_roots')
        row = next(row for row in roots['roots'] if row['path'] == str(linked))
        self.assertTrue(row['available'])
        self.assertEqual(row['repository']['common_directory'], str(external / '.git'))
        for root in (external, linked):
            metadata = self.call('project_manifest', directory=str(root), paths=['outside.md'])['files'][0]
            self.recover('project_file', {'path': metadata['requested_path'], 'expected_file_id': metadata['file_id']},
                         b'outside workspace, configured', root.name + '/outside.md')
        original_git = pr.local_git
        def unavailable_worktrees(root, *args):
            if args[0] == 'worktree':
                raise ValueError('PROJECT_GIT_BACKEND_INTERRUPTED')
            return original_git(root, *args)
        with mock.patch.object(pr, 'local_git', side_effect=unavailable_worktrees):
            self.reader = pr.ProjectReader(self.inbox)
            limited = self.call('project_roots')
            self.assertTrue(limited['discovery_limits'])
            self.assertEqual(len([r for r in limited['roots'] if r['root_id'] == 'repo:topeft']), 1)
            self.assertTrue(next(r for r in limited['roots'] if r['root_id'] == 'repo:topeft')['available'])
        # This is a fixture-owned registration; retained for portable inspection.

    def test_scope_exclusions_aliases_specials_and_invalid_inputs(self):
        unknown = self.repo / 'unknown'
        unknown.mkdir()
        self.put(unknown / 'blocked', b'must never read')
        self.profile['repositories']['unknown'] = {'path': str(unknown)}
        self.profile['repositories']['GridpackGeneration'] = {'path': str(self.base / 'inactive')}
        self.reader = pr.ProjectReader(self.inbox)
        self.put(self.repo / 'ANDOCS/AN-24-239/no', b'excluded')
        (self.repo / 'alias').symlink_to(self.base)
        (self.repo / 'safe_alias').symlink_to(self.repo / 'docs')
        os.mkfifo(self.repo / 'docs/fifo')
        for directory, paths in [(self.repo, ['alias/foreign']), (self.repo, ['safe_alias/binary']),
                                  (self.repo, ['unknown/blocked']), (self.repo, ['ANDOCS/AN-24-239/no']),
                                  (self.repo, ['.git/config']), (self.repo / 'docs', ['fifo']),
                                  (self.repo / 'docs', ['link']), (self.repo, ['../foreign'])]:
            with mock.patch.object(pr, 'stream_identity', side_effect=self.binding_only_hash):
                with self.assertRaises((ValueError, OSError)):
                    self.call('project_manifest', directory=str(directory), paths=paths)
        for path in ('/', '/tmp', str(self.repo) + '/../workspace', str(self.repo) + '//docs'):
            with self.assertRaises(ValueError):
                self.call('project_list', directory=path)
        with self.assertRaises(ValueError):
            self.call('project_manifest', directory=str(self.repo), paths=[])
        with self.assertRaises(ValueError):
            self.call('project_manifest', directory=str(self.repo), paths=['README.md', 'README.md'])
        for repo_id in ('unknown', 'GridpackGeneration', 'ANDOCS/AN-24-239'):
            with self.assertRaises(ValueError):
                self.call('project_git_tree', repository_id=repo_id, revision='HEAD')

    def test_excluded_surfaces_in_external_roots_and_linked_worktrees(self):
        external = self.base / 'external_andocs'
        external.mkdir()
        self.run_git(external, 'init', '-b', 'master')
        self.put(external / 'AN-24-239/no', b'not authorized')
        self.put(external / 'permitted.md', b'active parent')
        self.run_git(external, 'add', '--', 'permitted.md')
        self.run_git(external, 'commit', '-m', 'fixture parent')
        linked = self.base / 'linked_top'
        self.run_git(self.repo, 'worktree', 'add', '--detach', str(linked), self.first)
        self.put(linked / 'ANDOCS/AN-24-239/no', b'linked excluded')
        unregistered = self.repo / 'unregistered'
        unregistered.mkdir()
        self.run_git(unregistered, 'init', '-b', 'master')
        self.put(unregistered / 'no', b'unknown repository')
        self.profile['repositories']['ANDOCS'] = {'path': str(external)}
        self.reader = pr.ProjectReader(self.inbox)
        with self.assertRaisesRegex(ValueError, 'SCOPE_DENIED'):
            self.call('project_git_tree', repository_id='ANDOCS', revision='HEAD', subtree='AN-24-239')
        for directory, paths in [(external, ['AN-24-239/no']),
                                  (linked, ['ANDOCS/AN-24-239/no']),
                                  (self.repo, ['unregistered/no'])]:
            with mock.patch.object(pr, 'stream_identity', side_effect=self.binding_only_hash):
                with self.assertRaisesRegex(ValueError, 'SCOPE_DENIED|UNREGISTERED_REPOSITORY'):
                    self.call('project_manifest', directory=str(directory), paths=paths)
        permitted = self.call('project_manifest', directory=str(external), paths=['permitted.md'])['files'][0]
        self.recover('project_file', {'path': permitted['requested_path'], 'expected_file_id': permitted['file_id']},
                     b'active parent', 'external/permitted.md')

    def test_mutated_file_parent_root_selection_and_inventory_conflict(self):
        directory = self.repo / 'docs'
        row = self.call('project_manifest', directory=str(directory), paths=['binary'])['files'][0]
        self.put(directory / 'binary', b'changed')
        with self.assertRaisesRegex(ValueError, 'CONFLICT'):
            self.call('project_file', path=row['requested_path'], expected_file_id=row['file_id'])
        metadata = self.call('project_manifest', directory=str(directory), paths=['empty', '雪.md'])
        with self.assertRaisesRegex(ValueError, 'CONFLICT'):
            self.call('project_manifest', directory=str(directory), paths=['empty'],
                      expected_inventory_id=metadata['inventory_id'])
        row = metadata['files'][0]
        directory.rename(self.repo / 'preserved_docs')
        directory.mkdir()
        self.put(directory / 'empty', b'')
        with self.assertRaisesRegex(ValueError, 'CONFLICT'):
            self.call('project_file', path=row['requested_path'], expected_file_id=row['file_id'])
        listing = self.call('project_list', directory=str(directory), limit=1)
        self.put(directory / 'new', b'new')
        with self.assertRaisesRegex(ValueError, 'CONFLICT'):
            self.call('project_list', directory=str(directory), expected_inventory_id=listing['inventory_id'])
        self.repo.rename(self.base / 'preserved_workspace')
        self.repo.mkdir()
        with self.assertRaisesRegex(ValueError, 'CHANGED'):
            self.call('project_list', directory=str(self.repo))

    def test_races_during_hashing_never_return_complete_mixed_files(self):
        for kind in ('file', 'parent', 'root', 'earlier', 'repository'):
            with self.subTest(kind=kind):
                directory = self.repo / ('case_' + kind)
                self.put(directory / 'a', b'original')
                self.put(directory / 'b', b'second')
                original_hash, calls = pr.stream_identity, []
                def change(stream):
                    result = original_hash(stream)
                    if Path(os.readlink('/proc/self/fd/' + str(stream.fileno()))).name == '.git':
                        return result
                    calls.append(True)
                    if len(calls) == (2 if kind == 'earlier' else 1):
                        if kind == 'repository':
                            (directory / '.git').mkdir()
                        elif kind in ('file', 'earlier'):
                            self.put(directory / 'a', b'changed!')
                        else:
                            target = self.repo if kind == 'root' else directory
                            target.rename(target.with_name(target.name + '_preserved'))
                            target.mkdir()
                    return result
                with mock.patch.object(pr, 'stream_identity', side_effect=change):
                    with self.assertRaises((ValueError, OSError)):
                        self.call('project_manifest', directory=str(directory), paths=['a', 'b'])
                if kind == 'root':
                    self.repo.rmdir()
                    self.repo.with_name(self.repo.name + '_preserved').rename(self.repo)

    def test_local_git_frozen_commit_tree_membership_and_lossless_blobs(self):
        self.put(self.base / 'canonical_docs_tree.raw',
                 self.run_git(self.repo, 'ls-tree', '-r', '-t', '-z', '-l', self.first + ':docs'))
        self.run_git(self.repo, 'update-ref', 'refs/heads/moving', self.first)
        tree = self.call('project_git_tree', repository_id='TOP26006_fw', revision='refs/heads/moving',
                         subtree='docs', limit=2)
        self.assertEqual(tree['commit'], self.first)
        rows, inventory = tree['entries'], tree['inventory_id']
        # A ref moves; callers continue with the frozen commit returned above.
        self.run_git(self.repo, 'update-ref', 'refs/heads/moving', self.second)
        while tree['has_more']:
            tree = self.call('project_git_tree', repository_id='TOP26006_fw', revision=tree['commit'], subtree='docs',
                             offset=tree['next_offset'], limit=2, expected_inventory_id=inventory,
                             expected_binding_id=tree['binding_id'])
            rows.extend(tree['entries'])
        self.assertEqual({row['path'] for row in rows}, set(p for p in self.originals if p.startswith('docs/')) |
                         {'docs/link', 'docs/submodule'})
        for row in rows:
            if row['type'] != 'blob':
                continue
            canonical = self.run_git(self.repo, 'cat-file', 'blob', row['object_id'])
            self.recover('project_git_blob', {'repository_id': 'TOP26006_fw', 'commit': self.first,
                        'path': row['path'], 'expected_binding_id': tree['binding_id'],
                        'expected_object_id': row['object_id']}, canonical, 'git/' + row['object_id'])
        old = self.call('project_git_tree', repository_id='TOP26006_fw', revision=self.first)
        readme = next(row for row in old['entries'] if row['path'] == 'README.md')
        self.recover('project_git_blob', {'repository_id': 'TOP26006_fw', 'commit': self.first,
                     'path': 'README.md', 'expected_binding_id': old['binding_id'],
                     'expected_object_id': readme['object_id']}, b'first', 'git/' + readme['object_id'])
        self.assertNotEqual((self.repo / 'README.md').read_bytes(), b'first')
        self.call('project_git_tree', repository_id='TOP26006_fw', revision=self.first, subtree='docs',
                  expected_inventory_id=inventory, expected_binding_id=tree['binding_id'])

    def test_git_negative_parameters_missing_objects_replace_and_environment(self):
        top = self.call('project_git_tree', repository_id='TOP26006_fw', revision=self.first)
        readme = next(row for row in top['entries'] if row['path'] == 'README.md')
        blob_args = {'repository_id': 'TOP26006_fw', 'commit': self.first, 'path': 'README.md',
                     'expected_binding_id': top['binding_id'], 'expected_object_id': readme['object_id']}
        for revision in ('--help', '-C/tmp', 'not_a_ref', '0' * 40, 'HEAD:README.md'):
            with self.assertRaises(ValueError):
                self.call('project_git_tree', repository_id='TOP26006_fw', revision=revision)
        for changes in ({'expected_object_id': '0' * 40}, {'path': 'absent'}, {'path': '../foreign'},
                        {'path': 'docs/submodule'}, {'commit': self.second}, {'expected_binding_id': '0' * 64}):
            with self.assertRaises(ValueError):
                self.call('project_git_blob', **dict(blob_args, **changes))
        with self.assertRaises(ValueError):
            self.call('project_git_tree', repository_id='TOP26006_fw', revision='HEAD', offset=1,
                      expected_inventory_id=top['inventory_id'])
        with self.assertRaises(ValueError):
            self.call('project_git_tree', repository_id='TOP26006_fw', revision=self.first, subtree=':(glob)*')
        self.run_git(self.repo, 'replace', self.first, self.second)
        with mock.patch.dict(os.environ, {'GIT_DIR': '/forbidden', 'GIT_WORK_TREE': '/forbidden',
                'GIT_OBJECT_DIRECTORY': '/forbidden', 'GIT_CONFIG_COUNT': '1', 'GIT_CONFIG_KEY_0': 'x.y',
                'GIT_CONFIG_VALUE_0': 'bad', 'GIT_TRACE': str(self.base / 'must_not_write')}):
            self.recover('project_git_blob', blob_args, b'first', 'git/replaced_original')
        self.assertFalse((self.base / 'must_not_write').exists())
        # Missing promisor object must not run a remote helper, even with local
        # protocol configuration allowing ext. A hook/credential command is inert.
        marker = self.base / 'network_or_hook_used'
        self.run_git(self.repo, 'config', 'remote.origin.promisor', 'true')
        self.run_git(self.repo, 'config', 'remote.origin.url', 'ext::touch ' + str(marker))
        self.run_git(self.repo, 'config', 'protocol.ext.allow', 'always')
        with self.assertRaises(ValueError):
            self.call('project_git_tree', repository_id='TOP26006_fw', revision='1' * 40)
        self.assertFalse(marker.exists())
        self.records.append({'git_environment': pr.git_environment(), 'network_marker_exists': marker.exists()})

    def test_git_binding_swap_and_changed_commit_inventory(self):
        first = self.call('project_git_tree', repository_id='TOP26006_fw', revision=self.first)
        with self.assertRaisesRegex(ValueError, 'CONFLICT'):
            self.call('project_git_tree', repository_id='TOP26006_fw', revision=self.second,
                      expected_inventory_id=first['inventory_id'])
        marker = self.repo / '.git'
        marker.rename(self.repo / 'old_gitfile')
        marker.write_text('gitdir: ' + str(self.base / 'absent.git') + '\n')
        with self.assertRaises(ValueError):
            self.call('project_git_tree', repository_id='TOP26006_fw', revision=self.first,
                      expected_binding_id=first['binding_id'])

    def test_private_artifact_and_deposit_shared_reader_regressions(self):
        from artifacts import freeze_artifacts, artifact_page
        from evidence_reader import EvidenceReader
        import deposits
        folder = self.base / 'private_artifacts'
        folder.mkdir()
        original = b'private\x00\xff' + '雪'.encode() * 20000
        self.put(folder / 'bytes', original)
        row = freeze_artifacts(folder, [('bytes', folder / 'bytes')])[0]
        offset, pages = 0, []
        while True:
            page = artifact_page(folder, row, offset, 32767)
            pages.append(page)
            offset = page['next_offset']
            if not page['has_more']:
                break
        self.assertEqual(b''.join(base64.b64decode(p['data']) for p in pages), original)
        self.put(self.base / 'originals/private', original)
        self.acquisitions.append({'method': 'artifact_page', 'args': {}, 'original': 'originals/private', 'pages': pages})
        os.link(folder / 'bytes', folder / 'hardlink')
        os.mkfifo(folder / 'fifo')
        (folder / 'link').symlink_to(folder / 'bytes')
        reader = EvidenceReader(self.base)
        for name in ('hardlink', 'fifo', 'link'):
            with self.assertRaises((ValueError, OSError)):
                with regular_reader(folder / name):
                    self.fail('unsafe private content')
            with self.assertRaises((ValueError, OSError)):
                reader.manifest('private_artifacts', paths=[name])
        # Exercise the actual deposit consumer of regular_reader, without task
        # admission or any application executor.
        content = b'```yaml\nprompt_id: private_fixture\n```\r\n' + '雪'.encode()
        receipt = deposits.publish(self.repo, 'private_fixture', content)
        self.assertEqual(deposits.consume(self.repo, 'private_fixture', content), content)
        self.assertTrue(deposits.publish(self.repo, 'private_fixture', content)['duplicate_deposit'])
        self.records.append({'deposit_receipt': receipt, 'consumed_base64': base64.b64encode(content).decode()})

    def test_page_race_and_git_descriptor_rebinding_refused(self):
        row = self.call('project_manifest', directory=str(self.repo / 'docs'), paths=['binary'])['files'][0]
        original, calls = pr.stream_identity, []
        def mutate(stream):
            value = original(stream)
            if Path(os.readlink('/proc/self/fd/' + str(stream.fileno()))).name == '.git':
                return value
            calls.append(True)
            if len(calls) == 2:
                self.put(self.repo / 'docs/binary', b'changed after chunk')
            return value
        with mock.patch.object(pr, 'stream_identity', side_effect=mutate):
            with self.assertRaisesRegex(ValueError, 'CHANGED'):
                self.call('project_file', path=row['requested_path'], expected_file_id=row['file_id'])
        tree = self.call('project_git_tree', repository_id='TOP26006_fw', revision=self.first)
        row = next(row for row in tree['entries'] if row['path'] == 'README.md')
        popen = pr.subprocess.Popen
        changed = []
        def replace_after_launch(argv, *args, **kwargs):
            process = popen(argv, *args, **kwargs)
            if 'cat-file' in argv and not changed:
                changed.append(True)
                (self.base / 'top.git').rename(self.base / 'preserved.git')
                (self.base / 'top.git').mkdir()
            return process
        with mock.patch.object(pr.subprocess, 'Popen', side_effect=replace_after_launch):
            with self.assertRaises((ValueError, OSError)):
                self.call('project_git_blob', repository_id='TOP26006_fw', commit=self.first, path='README.md',
                          expected_binding_id=tree['binding_id'], expected_object_id=row['object_id'])

    def run_mcp(self, failure=None):
        modules = os.environ.get('GLADOS_BRIDGE_TEST_NODE_MODULES')
        if not modules:
            self.skipTest('existing MCP SDK node_modules not supplied')
        source = Path(__file__).resolve().parent
        actual_repo = source.parents[1]
        wrapper = actual_repo / 'codex-run.sh'
        profile = self.base / 'profile.yml'
        profile.write_text('profile_version: 1\nprofile_name: project_fixture\nworkspace_root: ' + str(actual_repo) +
             '\nevidence_root: ' + str(self.base / 'evidence') + '\nprovider_procedure: openai_codex\ntooling:\n'
             '  command_wrapper: ' + str(wrapper) + '\n  python_interpreter: ' + sys.executable +
             '\nrepositories:\n  TOP26006_fw:\n    path: ' + str(actual_repo) + '\n  topeft:\n    path: ' + str(self.repo) + '\n')
        self.put(self.base / 'evidence/external/report.md', 'old evidence consumer 雪'.encode())
        adapter = self.base / ('adapter_' + (failure or 'reader'))
        adapter.mkdir()
        for path in source.iterdir():
            if path.suffix in ('.py', '.mjs', '.json') and path.is_file():
                shutil.copyfile(path, adapter / path.name)
        shutil.copyfile(Path(__file__).resolve().parents[1] / 'resolve_local_profile.py', adapter / 'resolve_local_profile.py')
        (adapter / 'node_modules').symlink_to(Path(modules).resolve(), target_is_directory=True)
        if failure == 'spawn':
            wrapper = self.base / 'nonexistent_wrapper'
        elif failure == 'invalid_json':
            # No Python executes in this fault: echo returns the backend argv
            # immediately as non-JSON through the actual execFile callback.
            wrapper = Path('/bin/echo')
        fixture = self.base / ('mcp_fixture_' + (failure or 'reader') + '.json')
        fixture.write_text(json.dumps({'project_reader': True, 'adapter_errors': failure,
                'repo': str(actual_repo), 'profile': str(profile), 'state': str(self.base / 'never_state'),
                'python': sys.executable, 'wrapper': str(wrapper), 'codex': str(self.base / 'forbidden_executor'),
                'server': str(adapter / 'server.mjs'), 'directory': str(self.repo / 'docs'),
                'first_commit': self.first, 'observations': str(self.base / ('mcp_' + (failure or 'reader') + '.json'))}))
        result = subprocess.run(['node', str(adapter / 'test_mcp_stdio.mjs'), str(fixture)],
                                capture_output=True, text=True, timeout=30 if failure else 3600)
        (self.base / ('mcp_' + (failure or 'reader') + '.log')).write_text(result.stdout + result.stderr)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((self.base / 'never_state').exists())

    def test_real_mcp_project_files_and_git_separate_clients_no_state(self):
        self.run_mcp()

    def test_real_mcp_adapter_errors_and_task_recovery(self):
        for failure in ('spawn', 'invalid_json'):
            self.run_mcp(failure)


if __name__ == '__main__':
    unittest.main(verbosity=2)
