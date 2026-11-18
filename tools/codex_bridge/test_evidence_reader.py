"""External producer fixtures: no bridge task, executor or live state required."""
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import evidence_reader as er


def sha(data):
    return hashlib.sha256(data).hexdigest()


class EvidenceReaderTests(unittest.TestCase):
    def setUp(self):
        retained = os.environ.get('GLADOS_BRIDGE_READER_FIXTURES')
        self.temporary = None if retained else tempfile.TemporaryDirectory(prefix=self._testMethodName + '_')
        self.base = Path(tempfile.mkdtemp(prefix=self._testMethodName + '_', dir=retained)
                         if retained else self.temporary.name)
        self.root = self.base / 'evidence'
        self.dossier = self.root / 'external'
        self.dossier.mkdir(parents=True)
        self.reader = er.EvidenceReader(self.root)
        self.records = []
        self.retained = retained

    def tearDown(self):
        (self.base / 'observations.json').write_text(json.dumps(self.records, indent=2))
        if not self.retained:
            self.temporary.cleanup()

    def call(self, method, **args):
        record_args = json.loads(json.dumps(args))
        try:
            result = getattr(self.reader, method)(**args)
        except (ValueError, OSError) as exc:
            self.records.append({'method': method, 'args': record_args, 'error': str(exc)})
            raise
        self.records.append({'method': method, 'args': record_args, 'result': result})
        return result

    def put(self, path, content):
        target = self.dossier / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return target

    def page(self, path='report.md', content=b'original', **args):
        return self.call('file_page', directory='external', path=path,
                         expected_size_bytes=len(content), expected_sha256=sha(content), **args)

    def test_lossless_external_dossier_and_serialized_pages(self):
        self.acquire_lossless_dossier()

    def test_selected_lossless_without_enumerating_excluded_entries(self):
        self.put('excluded/secret', b'not selected')
        (self.dossier / 'excluded/link').symlink_to(self.base)
        os.mkfifo(self.dossier / 'excluded/fifo')
        original_open, opened = er.os.open, []
        def open_selected(path, *args, **kwargs):
            self.assertNotIn('excluded', str(path).split('/'))
            opened.append(str(path))
            return original_open(path, *args, **kwargs)
        # Any enumeration, even of the dossier itself, is forbidden here.
        with mock.patch.object(er.os, 'listdir', side_effect=AssertionError('excluded traversal')), \
             mock.patch.object(er.os, 'open', side_effect=open_selected):
            self.acquire_lossless_dossier(selected=True)
        self.records.append({'descriptor_opens': opened, 'enumeration': 'forbidden by mock'})

    def acquire_lossless_dossier(self, selected=False):
        originals = {'report.md': b'# Report\r\n' + '雪€🦊'.encode() * 7000,
                     'change.patch': b'diff --git a/x b/x\n\x00\xff',
                     'nested/payload.bin': bytes(range(256)) * 270,
                     'empty': b''}
        for name, content in originals.items():
            self.put(name, content)
        selection = {'paths': list(reversed(originals))} if selected else {}
        pages, rows, offset, identity = [], [], 0, None
        while True:
            page = self.call('manifest', directory='external', offset=offset, limit=2,
                             expected_manifest_id=identity, **selection)
            self.assertEqual(page['selection_mode'], 'explicit_files' if selected else 'recursive')
            if selected:
                self.assertEqual(page['paths'], sorted(originals))
                selection['paths'].reverse()
                # Both dossier and selected-parent metadata can change without
                # changing the selected namespace or bytes.
                self.put('unselected', b'unrelated addition')
                self.put('nested/unselected', b'unrelated sibling')
            pages.append(page)
            identity = page['manifest_id']
            rows.extend(page['files'])
            offset = page['next_offset']
            if not page['has_more']:
                break
        recovered = {}
        for row in rows:
            chunks, offset = [], 0
            while True:
                page = self.call('file_page', directory='external', path=row['path'],
                                 expected_size_bytes=row['size_bytes'], expected_sha256=row['sha256'],
                                 offset=offset, limit=32767)
                chunks.append(page)
                offset = page['next_offset']
                if not page['has_more']:
                    break
            recovered[row['path']] = chunks
        final = self.call('manifest', directory='external', expected_manifest_id=identity, **selection)
        portable = self.base / 'acquisition.json'
        portable.write_text(json.dumps({'manifest_pages': pages, 'file_pages': recovered, 'final_manifest': final}))
        # The consumer validates reopened evidence, including full membership.
        saved = json.loads(portable.read_bytes())
        actual_rows = [row for page in saved['manifest_pages'] for row in page['files']]
        self.assertEqual({row['path'] for row in actual_rows}, set(originals))
        for row in actual_rows:
            chunks = saved['file_pages'][row['path']]
            data, offset = bytearray(), 0
            for chunk in chunks:
                raw = base64.b64decode(chunk['data'], validate=True)
                self.assertEqual((chunk['offset'], chunk['chunk_size_bytes'], chunk['chunk_sha256']),
                                 (offset, len(raw), sha(raw)))
                data.extend(raw)
                offset = chunk['next_offset']
                self.assertEqual(offset, len(data))
            self.assertEqual(bytes(data), originals[row['path']])
            self.assertEqual((len(data), sha(data)), (row['size_bytes'], row['sha256']))
        self.assertEqual(saved['final_manifest']['manifest_id'], identity)
        self.assertFalse((self.base / 'state').exists())

    def test_selected_invalid_or_unsafe_acquisition_fails_whole_set(self):
        self.put('good', b'good')
        foreign = self.base / 'foreign'
        foreign.write_bytes(b'forbidden')
        (self.dossier / 'link').symlink_to(foreign)
        (self.dossier / 'component').symlink_to(self.base, target_is_directory=True)
        os.link(foreign, self.dossier / 'hardlink')
        os.mkfifo(self.dossier / 'fifo')
        invalid = [None, [], 'good', {}, [1], ['good', 'good'], [''], ['.'], ['..'],
                   ['/tmp/x'], ['a//b'], ['a/../good'], ['a/'], ['\ud800'],
                   ['missing'], ['link'], ['component/foreign'], ['hardlink'], ['fifo'], ['component']]
        with mock.patch.object(er, 'stream_identity', side_effect=AssertionError('unsafe contents read')):
            for paths in invalid:
                with self.subTest(paths=repr(paths)), self.assertRaises(ValueError):
                    self.call('manifest', directory='external', paths=paths)
        with self.assertRaises(ValueError):
            self.call('manifest', directory='external', paths=['good', 'missing'])
        with self.assertRaises(ValueError):
            self.call('manifest', directory='external')
        self.assertEqual(foreign.read_bytes(), b'forbidden')

    def test_selected_identity_conflicts_and_parent_bindings(self):
        self.put('nested/a', b'a')
        self.put('b', b'b')
        paths = ['nested/a', 'b']
        def manifest(**args):
            return self.call('manifest', directory='external', paths=paths, **args)
        first = manifest(limit=1)
        with self.assertRaisesRegex(ValueError, 'CONFLICT'):
            self.call('manifest', directory='external', paths=['b'], expected_manifest_id=first['manifest_id'])
        for kind in ('modify', 'equal_byte_replace', 'parent', 'dossier'):
            current = manifest()
            if kind == 'modify':
                self.put('b', b'z')
            elif kind == 'equal_byte_replace':
                self.put('replacement', b'z')
                os.replace(self.dossier / 'replacement', self.dossier / 'b')
            elif kind == 'parent':
                (self.dossier / 'nested').rename(self.dossier / 'preserved')
                (self.dossier / 'nested').mkdir()
                # Keep file inode/content while changing its parent binding.
                (self.dossier / 'preserved/a').rename(self.dossier / 'nested/a')
            else:
                self.dossier.rename(self.root / 'preserved')
                self.dossier.mkdir()
                for name in ('b', 'nested'):
                    (self.root / 'preserved' / name).rename(self.dossier / name)
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, 'CONFLICT'):
                manifest(offset=1, expected_manifest_id=current['manifest_id'])

    def test_selected_parent_swap_while_hashing_later_file(self):
        self.put('a/first', b'first')
        self.put('z', b'last')
        original = er.stream_identity
        calls = []
        def swap(stream):
            result = original(stream)
            calls.append(True)
            if len(calls) == 2:
                (self.dossier / 'a').rename(self.dossier / 'preserved')
                (self.dossier / 'a').mkdir()
                (self.dossier / 'preserved/first').rename(self.dossier / 'a/first')
            return result
        with mock.patch.object(er, 'stream_identity', side_effect=swap):
            # Moving the earlier file can change its ctime as well as the
            # parent binding; either guard must refuse a complete manifest.
            with self.assertRaisesRegex(ValueError, 'CHANGED'):
                self.call('manifest', directory='external', paths=['a/first', 'z'])

    def test_paths_links_and_special_files_never_read_foreign_bytes(self):
        self.put('report.md', b'original')
        foreign = self.base / 'foreign'
        foreign.write_bytes(b'outside')
        for directory in ('', '.', '..', '../foreign', '/tmp', 'external/../external', 'external//x', 'external/'):
            with self.subTest(directory=directory), self.assertRaises(ValueError):
                self.call('manifest', directory=directory)
        for path in ('../foreign', '/tmp/x', 'x/../../foreign', '.', '', 'x//y'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.page(path=path)
        for directory in ('missing', 'external/report.md'):
            with self.assertRaises(ValueError):
                self.call('manifest', directory=directory)
        with self.assertRaises(ValueError):
            self.page('absent')
        # Checking the shared stream hasher proves rejection precedes contents.
        for kind in ('symlink', 'directory_symlink', 'hardlink', 'fifo'):
            target = self.dossier / kind
            if kind == 'symlink':
                target.symlink_to(foreign)
            elif kind == 'directory_symlink':
                target.symlink_to(self.base, target_is_directory=True)
            elif kind == 'hardlink':
                os.link(foreign, target)
            elif kind == 'fifo':
                os.mkfifo(target)
            try:
                with mock.patch.object(er, 'stream_identity', side_effect=AssertionError('foreign read')):
                    with self.assertRaises(ValueError):
                        self.page(kind + ('/foreign' if kind == 'directory_symlink' else ''))
                with self.assertRaises(ValueError):
                    self.call('manifest', directory='external')
            finally:
                target.unlink()  # Exact newly created fixture alias only.
        alias = self.root / 'alias'
        alias.symlink_to(self.dossier, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.call('manifest', directory='alias')
        root_alias = self.base / 'root_alias'
        root_alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError):
            er.EvidenceReader(root_alias).manifest('external')
        self.assertEqual(foreign.read_bytes(), b'outside')

    def test_invalid_offsets_limits_and_expected_identities(self):
        self.put('report.md', b'original')
        for offset, limit in ((-1, 1), (True, 1), (0, False), (0, 0), (0, 32769), (1.5, 1)):
            with self.assertRaises(ValueError):
                self.page(offset=offset, limit=limit)
        for args in ({'expected_size_bytes': 9, 'expected_sha256': sha(b'original')},
                     {'expected_size_bytes': 8, 'expected_sha256': '0' * 64},
                     {'expected_size_bytes': True, 'expected_sha256': sha(b'original')},
                     {'expected_size_bytes': 8, 'expected_sha256': 'invalid'}):
            with self.assertRaises(ValueError):
                self.call('file_page', directory='external', path='report.md', **args)
        with self.assertRaisesRegex(ValueError, 'BEYOND_EOF'):
            self.page(offset=9)
        self.assertEqual(base64.b64decode(self.page(offset=8)['data']), b'')
        self.put('empty', b'')
        self.assertFalse(self.page('empty', b'')['has_more'])
        for args in ({'offset': 1}, {'limit': 101}, {'expected_manifest_id': 5},
                     {'offset': 2, 'expected_manifest_id': '0' * 64}):
            with self.assertRaises(ValueError):
                self.call('manifest', directory='external', **args)
        self.assertEqual(self.call('manifest', directory='external', offset=0)['total'], 2)

    def test_manifest_membership_and_byte_changes_between_pages(self):
        self.put('a', b'a')
        self.put('b', b'b')
        first = self.call('manifest', directory='external', limit=1)
        self.put('c', b'c')
        with self.assertRaisesRegex(ValueError, 'CONFLICT'):
            self.call('manifest', directory='external', offset=1, expected_manifest_id=first['manifest_id'])
        current = self.call('manifest', directory='external')
        (self.dossier / 'b').unlink()
        with self.assertRaisesRegex(ValueError, 'CONFLICT'):
            self.call('manifest', directory='external', expected_manifest_id=current['manifest_id'])
        current = self.call('manifest', directory='external')
        self.put('a', b'z')
        with self.assertRaisesRegex(ValueError, 'CONFLICT'):
            self.call('manifest', directory='external', expected_manifest_id=current['manifest_id'])
        with self.assertRaisesRegex(ValueError, 'CONFLICT'):
            self.page('a', b'a')

    def test_file_modification_and_replacement_during_page(self):
        for replacement in (False, True):
            self.put('report.md', b'original')
            original = er.stream_identity
            calls = []
            def change(stream):
                result = original(stream)
                if not calls:
                    calls.append(True)
                    if replacement:
                        self.put('replacement', b'newbytes')
                        os.replace(self.dossier / 'replacement', self.dossier / 'report.md')
                    else:
                        self.put('report.md', b'newbytes')
                return result
            with mock.patch.object(er, 'stream_identity', side_effect=change):
                with self.assertRaisesRegex(ValueError, 'CHANGED'):
                    self.page()

    def test_directory_root_and_component_replacement_during_read(self):
        for selected in ('nested', 'external', 'evidence'):
            case = self.root / selected if selected == 'external' else self.dossier / selected
            if selected == 'evidence':
                case = self.root
            self.put('nested/report.md', b'original')
            original = er.stream_identity
            calls = []
            def swap(stream):
                result = original(stream)
                if not calls:
                    calls.append(True)
                    case.rename(case.with_name(case.name + '_preserved'))
                    case.mkdir()
                return result
            with mock.patch.object(er, 'stream_identity', side_effect=swap):
                with self.assertRaises(ValueError):
                    self.page('nested/report.md')
            case.rmdir()
            case.with_name(case.name + '_preserved').rename(case)

    def test_manifest_races_do_not_return_complete_mixed_inventory(self):
        for kind in ('add', 'remove', 'modify_earlier', 'directory'):
            a = self.put('a', b'a')
            self.put('b', b'b')
            original = er.stream_identity
            calls = []
            def change(stream):
                result = original(stream)
                calls.append(True)
                if len(calls) == 2:
                    if kind == 'add':
                        self.put('added', b'added')
                    elif kind == 'remove':
                        a.unlink()
                    elif kind == 'modify_earlier':
                        a.write_bytes(b'z')
                    else:
                        self.dossier.rename(self.root / 'preserved')
                        self.dossier.mkdir()
                return result
            with mock.patch.object(er, 'stream_identity', side_effect=change):
                with self.assertRaises(ValueError):
                    self.call('manifest', directory='external')
            if kind == 'directory':
                self.dossier.rmdir()
                (self.root / 'preserved').rename(self.dossier)
            if (self.dossier / 'added').exists():
                (self.dossier / 'added').unlink()

    def test_empty_dossier_and_equal_byte_directory_swap(self):
        first = self.call('manifest', directory='external')
        self.assertTrue(first['complete'])
        self.assertEqual(first['files'], [])
        self.dossier.rename(self.root / 'preserved')
        self.dossier.mkdir()
        with self.assertRaisesRegex(ValueError, 'CONFLICT'):
            self.call('manifest', directory='external', expected_manifest_id=first['manifest_id'])

    def test_symlink_swap_at_open_and_mutation_after_chunk_hash(self):
        self.put('nested/report.md', b'original')
        foreign = self.base / 'foreign'
        foreign.write_bytes(b'forbidden')
        original_open = os.open
        changed = []
        def swap(path, flags, *args, **kwargs):
            if path == 'report.md' and not changed:
                changed.append(True)
                (self.dossier / 'nested/report.md').rename(self.dossier / 'nested/preserved')
                (self.dossier / 'nested/report.md').symlink_to(foreign)
            return original_open(path, flags, *args, **kwargs)
        with mock.patch.object(er.os, 'open', side_effect=swap), \
             mock.patch.object(er, 'stream_identity', side_effect=AssertionError('outside read')):
            with self.assertRaises(ValueError):
                self.page('nested/report.md')
        self.put('report.md', b'original')
        original_hash = er.stream_identity
        calls = []
        def modify_after_hash(stream):
            result = original_hash(stream)
            calls.append(True)
            if len(calls) == 2:
                self.put('report.md', b'newbytes')
            return result
        frozen = er.signature((self.dossier / 'report.md').stat())
        with mock.patch.object(er, 'stream_identity', side_effect=modify_after_hash), \
             mock.patch.object(er, 'signature', return_value=frozen):
            with self.assertRaisesRegex(ValueError, 'CHANGED'):
                self.page()

    def installation(self):
        source = Path(__file__).parent
        repo = source.resolve().parents[1]
        profile = self.base / 'profile.yml'
        wrapper = repo / 'codex-run.sh'
        profile.write_text('profile_version: 1\nprofile_name: reader_fixture\nworkspace_root: ' + str(repo) +
                           '\nevidence_root: ' + str(self.root) + '\nprovider_procedure: openai_codex\ntooling:\n'
                           '  command_wrapper: ' + str(wrapper) + '\n  python_interpreter: ' + sys.executable +
                           '\nrepositories:\n  TOP26006_fw:\n    path: ' + str(repo) + '\n')
        return source, repo, profile, wrapper

    def test_rpc_preserves_existing_private_state_with_busy_worker_lock(self):
        import bridge
        self.put('report.md', b'original')
        source, repo, profile, wrapper = self.installation()
        backend = bridge.Bridge(self.base / 'state', codex=str(self.base / 'forbidden_executor'))
        lock = backend.lock('busy.lock')
        try:
            before = {p.name: p.read_bytes() for p in backend.root.iterdir()}
            command = [str(wrapper), sys.executable, '-s', '-B', str(source / 'bridge.py'),
                       '--state', str(backend.root), '--governed-profile', str(profile),
                       '--workspace', str(repo), '--command-wrapper', str(wrapper),
                       '--codex', str(self.base / 'forbidden_executor'), '--rpc']
            request = {'method': 'evidence_manifest', 'args': {'directory': 'external'}}
            process = subprocess.run(command, input=json.dumps(request), capture_output=True, text=True, timeout=30)
            self.records.append({'command': command, 'request': request, 'stdout': process.stdout,
                                 'stderr': process.stderr, 'returncode': process.returncode})
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertTrue(json.loads(process.stdout)['ok'], process.stdout)
            after = {p.name: p.read_bytes() for p in backend.root.iterdir()}
            self.assertEqual(before, after)
            with backend.db() as db:
                for table in ('tasks', 'uploads', 'chunks'):
                    self.assertEqual(db.execute('SELECT count(*) FROM ' + table).fetchone()[0], 0)
            self.records.append({'state_before_after': {name: sha(content) for name, content in after.items()},
                                 'state_byte_comparison': before == after})
        finally:
            os.close(lock)

    def test_real_mcp_external_reader_without_task_or_state_writes(self):
        self.run_mcp_fixture()

    def test_real_mcp_selected_reader_without_task_or_state_writes(self):
        self.run_mcp_fixture(selected=True)

    def test_real_mcp_adapter_spawn_and_invalid_json_recovery(self):
        for failure in ('spawn', 'invalid_json'):
            with self.subTest(failure=failure):
                self.run_mcp_fixture(failure=failure)

    def run_mcp_fixture(self, selected=False, failure=None):
        modules = os.environ.get('GLADOS_BRIDGE_TEST_NODE_MODULES')
        if not modules:
            self.skipTest('existing MCP SDK node_modules not supplied')
        source, repo, profile, wrapper = self.installation()
        adapter = self.base / ('adapter_' + (failure or 'reader'))
        adapter.mkdir()
        for path in source.iterdir():
            if path.suffix in ('.py', '.mjs', '.json') and path.is_file():
                shutil.copyfile(path, adapter / path.name)
        shutil.copyfile(Path(__file__).resolve().parents[1] / 'resolve_local_profile.py', adapter / 'resolve_local_profile.py')
        (adapter / 'node_modules').symlink_to(Path(modules).resolve(), target_is_directory=True)
        # Use the actual configured resolver/master in the maintained checkout;
        # no temporary Git repo, worktree, task or simulated inference needed.
        for name, content in {'report.md': '雪€🦊'.encode() * 7000, 'change.patch': b'patch\r\n',
                              'nested/payload.bin': bytes(range(256)) * 270, 'empty': b''}.items():
            self.put(name, content)
        options = {}
        if selected:
            self.put('excluded/private', b'not selected')
            (self.dossier / 'excluded/link').symlink_to(self.base)
            os.mkfifo(self.dossier / 'excluded/fifo')
            options['paths'] = ['report.md', 'empty', 'nested/payload.bin', 'change.patch']
        if failure:
            options['adapter_errors'] = failure
            if failure == 'spawn':
                wrapper = self.base / 'nonexistent_wrapper'
            else:
                # Test-only inert backend, reached through the real adapter's
                # execFile callback and resolved wrapper/interpreter.
                (adapter / 'bridge.py').write_text('print("not JSON: synthetic_key")\n')
        suffix = failure or 'reader'
        fixture = self.base / ('mcp_fixture_' + suffix + '.json')
        fixture.write_text(json.dumps({'external_evidence': True, 'repo': str(repo), 'profile': str(profile),
                                      'state': str(self.base / 'never_created_state'), 'python': sys.executable,
                                      'wrapper': str(wrapper), 'codex': str(self.base / 'forbidden_executor'),
                                      'server': str(adapter / 'server.mjs'), 'directory': str(self.dossier),
                                      'observations': str(self.base / ('mcp_observations_' + suffix + '.json')),
                                      **options}))
        result = subprocess.run(['node', str(adapter / 'test_mcp_stdio.mjs'), str(fixture)],
                                capture_output=True, text=True, timeout=300)
        (self.base / ('mcp_stdout_' + suffix + '.log')).write_text(result.stdout)
        (self.base / ('mcp_stderr_' + suffix + '.log')).write_text(result.stderr)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((self.base / 'never_created_state').exists())
        print(result.stdout.strip())


if __name__ == '__main__':
    unittest.main(verbosity=2)
