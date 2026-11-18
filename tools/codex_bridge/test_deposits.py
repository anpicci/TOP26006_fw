"""Changed consumers with real local RPC/Git/files; simulated executor only."""
import base64
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import subprocess
import shutil
import unittest
import zipfile
from unittest import mock

import bridge
import deposits
import test_governed
from test_support import retain_fixture_evidence


class DepositTests(unittest.TestCase):
    # Reuse the maintained governed fixture without inheriting unrelated tests.
    setUpClass = classmethod(test_governed.GovernedTests.setUpClass.__func__)
    setUp = test_governed.GovernedTests.setUp
    tearDown = test_governed.GovernedTests.tearDown
    run_git = test_governed.GovernedTests.run_git
    contract = test_governed.GovernedTests.contract
    finish = test_governed.GovernedTests.finish
    retrieve = test_governed.GovernedTests.retrieve

    def upload(self, ident, content=None):
        content = self.contract(ident).encode() if content is None else content
        self.b.prompt_upload(ident, len(content), hashlib.sha256(content).hexdigest())
        for offset in range(0, len(content), 24575):
            self.b.prompt_chunk(ident, offset, base64.b64encode(content[offset:offset + 24575]).decode())
        return content

    def test_opaque_transfers_and_legacy_task_identity(self):
        for ident, content in [('document', b'ordinary document'),
                               ('mappings', b'```yaml\na: b\n```\n```yaml\nc: d\n```'),
                               ('first_transfer', self.contract('reusable_task').encode()),
                               ('second_transfer', self.contract('reusable_task').encode()),
                               ('binary', bytes(range(256)))]:
            self.upload(ident, content)
            receipt = self.b.finalize_content(ident)
            self.assertEqual(Path(receipt['path']).read_bytes(), content)
            self.assertEqual(receipt['transfer_id'], ident)
            self.assertNotIn('prompt_id', receipt)
            self.assertFalse(receipt['execution_started'])
            self.assertTrue(self.b.finalize_content(ident)['duplicate_deposit'])
        with self.assertRaisesRegex(ValueError, 'STRICT_UTF8'):
            self.b.submit_uploaded_task('binary')
        with self.b.db() as db:
            db.execute('INSERT INTO tasks VALUES (?,?,?,?,?,?,?)',
                       ('legacy', '0' * 64, 'old task', 'COMPLETED', 1, 2, '{}'))
        self.upload('legacy', b'new opaque operation')
        self.assertFalse(self.b.prompt_upload('legacy', 20, hashlib.sha256(b'new opaque operation').hexdigest())['execution_started'])
        self.assertFalse(self.b.finalize_content('legacy')['execution_started'])
        with self.b.db() as db:
            self.assertEqual(db.execute('SELECT prompt FROM tasks WHERE id=?', ('legacy',)).fetchone()[0], 'old task')
        with self.assertRaisesRegex(ValueError, 'ID_CONFLICT'):
            self.b.prompt_upload('legacy', 3, hashlib.sha256(b'new').hexdigest())

    def test_access_does_not_load_execution_dependencies(self):
        import sys
        from access_profile import AccessInbox
        # A profile with no execution tooling still supplies all access facts.
        import yaml
        profile = yaml.safe_load(self.profile.read_text())
        profile.pop('tooling')
        self.profile.write_text(yaml.safe_dump(profile))
        # Remove nonconsumed policy/parser objects from the actual fixture
        # master: access must not even resolve their object identities.
        self.run_git('rm', '--', 'governance/model_policy.md',
                     '.agents/skills/correction-lib-prompt-contract/scripts/validate_prompt.py')
        self.run_git('commit', '-qm', 'test: remove execution-only fixture dependencies')
        self.run_git('update-ref', 'refs/heads/master', self.run_git('rev-parse', 'HEAD').decode().strip())
        with mock.patch.dict(sys.modules, {'governed_task': None}), \
             mock.patch.object(self.b, 'preflight', side_effect=AssertionError('CLI probe')):
            self.b.inbox = AccessInbox(self.profile, self.repo)
            self.upload('plain', b'ordinary bytes')
            self.assertEqual(self.b.finalize_content('plain')['state'], 'DEPOSITED')
            info = self.b.info()
            self.assertIsNone(info['cli_compatible'])
            self.assertEqual(info['execution_readiness'], 'NOT_PROBED')
            from project_reader import ProjectReader
            self.assertTrue(ProjectReader(self.b.inbox).project_roots()['roots'])
        self.profile.write_text(self.profile.read_text() + '\n# changed\n')
        with self.assertRaisesRegex(ValueError, 'LOCAL_PROFILE_CHANGED'):
            self.b.finalize_content('plain')

    @unittest.skipUnless(os.environ.get('GLADOS_BRIDGE_TEST_NODE_MODULES'), 'existing SDK required')
    def test_capabilities_actual_mcp_without_execution_tooling(self):
        import yaml
        profile = yaml.safe_load(self.profile.read_text())
        profile.pop('tooling')
        self.profile.write_text(yaml.safe_dump(profile))
        source = Path(__file__).resolve().parent
        selected = os.environ.get('GLADOS_BRIDGE_TEST_RELEASE')
        adapter = Path(selected) if selected else self.base / 'capability_adapter'
        if not selected:
            adapter.mkdir()
            for path in source.iterdir():
                if path.is_file() and path.suffix in ('.py', '.mjs', '.json', '.sh'):
                    shutil.copyfile(path, adapter / path.name)
            shutil.copyfile(source.parent / 'resolve_local_profile.py', adapter / 'resolve_local_profile.py')
            (adapter / 'node_modules').symlink_to(os.environ['GLADOS_BRIDGE_TEST_NODE_MODULES'])
        fixture = self.base / 'capability_fixture.json'
        fixture.write_text(json.dumps({'capabilities': True, 'repo': str(self.repo),
            'profile': str(self.profile), 'state': str(self.b.root),
            'python': os.sys.executable, 'wrapper': str(self.wrapper),
            'codex': '/nonexistent/codex', 'server': str(adapter / 'server.mjs'),
            **({'entrypoint': str(adapter / 'start.sh')} if selected else {}),
            'observations': str(self.base / 'protocol.json'),
            'lifecycle': str(self.base / 'lifecycle.json')}))
        reply = subprocess.run(['node', str(source / 'test_mcp_stdio.mjs'), str(fixture)],
                               capture_output=True, text=True, timeout=300)
        print(reply.stdout)
        self.assertEqual(reply.returncode, 0, reply.stderr + reply.stdout)
        # Actual adapter fallback with non-JSON output; no execution.
        broken = json.loads(fixture.read_text())
        broken.update(capabilities=False, transfer_error=True, wrapper='/bin/echo',
                      lifecycle=str(self.base / 'fallback_lifecycle.json'))
        fallback_fixture = self.base / 'fallback_fixture.json'
        fallback_fixture.write_text(json.dumps(broken))
        reply = subprocess.run(['node', str(source / 'test_mcp_stdio.mjs'), str(fallback_fixture)],
                               capture_output=True, text=True, timeout=300)
        print(reply.stdout)
        self.assertEqual(reply.returncode, 0, reply.stderr + reply.stdout)

    def test_access_policy_change_and_alias_refused(self):
        from access_profile import AccessInbox
        self.b.inbox = AccessInbox(self.profile, self.repo)
        self.upload('policy', b'opaque')
        registry = self.repo / 'governance/repositories.md'
        registry.write_text(registry.read_text() + '\n# changed access policy\n')
        self.run_git('add', '--', 'governance/repositories.md')
        self.run_git('commit', '-qm', 'test: change access fixture policy')
        self.run_git('update-ref', 'refs/heads/master', self.run_git('rev-parse', 'HEAD').decode().strip())
        with self.assertRaisesRegex(ValueError, 'GOVERNANCE_DELTA'):
            self.b.finalize_content('policy')
        alias = self.base / 'profile_alias.yml'
        alias.symlink_to(self.profile)
        with self.assertRaisesRegex(ValueError, 'UNSAFE_PROFILE_ALIAS'):
            AccessInbox(alias, self.repo)

    def manual(self, action, ident, **extra):
        # Shell has its own explicit installation bindings, no tunnel context.
        env = {key: os.environ[key] for key in ('HOME', 'PATH', 'TMPDIR') if key in os.environ}
        env.update(GLADOS_BRIDGE_WORKSPACE=str(self.repo), GLADOS_BRIDGE_PROFILE=str(self.profile),
                   GLADOS_BRIDGE_WRAPPER=str(self.wrapper), GLADOS_BRIDGE_PYTHON=os.sys.executable,
                   GLADOS_BRIDGE_STATE=str(self.b.root), GLADOS_BRIDGE_CODEX=str(self.fake))
        env.update(extra)
        result = subprocess.run([str(Path(__file__).with_name('manual.sh')), action, ident],
                                env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=90)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return json.loads(result.stdout)

    def test_deposit_no_execution_busy_and_missing_cli(self):
        content = self.upload('deposit', self.contract('deposit').encode() + b'\r\n' + '雪€'.encode() * 6000)
        self.b.codex = '/nonexistent/codex'
        busy = self.b.lock('busy.lock')
        try:
            original_popen = subprocess.Popen
            def no_executor(argv, *args, **kwargs):
                self.assertEqual(argv[0], 'git', argv)
                return original_popen(argv, *args, **kwargs)
            with mock.patch('bridge.subprocess.Popen', side_effect=no_executor), \
                 mock.patch.object(self.b, 'preflight', side_effect=AssertionError('CLI')):
                receipt = self.b.finalize_prompt('deposit')
                self.assertEqual(receipt['state'], 'DEPOSITED')
                self.assertFalse(receipt['execution_started'])
                self.assertEqual(receipt['size_bytes'], len(content))
                self.assertEqual(receipt['prompt_sha256'], hashlib.sha256(content).hexdigest())
                self.assertEqual(Path(receipt['path']).read_bytes(), content)
                self.assertTrue(self.b.finalize_prompt('deposit')['duplicate_deposit'])
        finally:
            os.close(busy)
        with self.b.db() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM tasks').fetchone()[0], 0)
        # The real local entry retains CLI admission; deposit did not test it.
        failed = self.manual('submit', 'deposit', GLADOS_BRIDGE_CODEX='/nonexistent/codex')
        self.assertFalse(failed['ok'])
        self.assertIn('metadata unavailable', failed['error'])
        self.assertEqual(Path(receipt['path']).read_bytes(), content)

    def test_deposit_refuses_incomplete_digest_utf8_and_id(self):
        self.b.prompt_upload('incomplete', 3, hashlib.sha256(b'abc').hexdigest())
        with self.assertRaisesRegex(ValueError, 'INCOMPLETE'):
            self.b.finalize_prompt('incomplete')
        self.b.prompt_upload('digest', 3, '0' * 64)
        self.b.prompt_chunk('digest', 0, base64.b64encode(b'abc').decode())
        self.upload('utf8', b'\xff\xfe')
        self.upload('mismatch', self.contract('different').encode())
        for ident, error in (('digest', 'DIGEST_MISMATCH'), ('utf8', 'STRICT_UTF8')):
            with self.subTest(ident=ident), self.assertRaisesRegex(ValueError, error):
                self.b.finalize_prompt(ident)
        receipt = self.b.finalize_prompt('mismatch')
        self.assertEqual(Path(receipt['path']).read_bytes(), self.contract('different').encode())
        with self.b.db() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM tasks').fetchone()[0], 0)

    def test_deposit_concurrent_and_interrupted_publication(self):
        content = self.upload('parallel')
        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            results = list(pool.map(lambda _: self.b.finalize_prompt('parallel'), range(2)))
        self.assertEqual({row['path'] for row in results}, {str(self.repo / 'reports/prompts/CODEX_PROMPT_parallel.md')})
        self.assertEqual(Path(results[0]['path']).read_bytes(), content)
        self.upload('before')
        with mock.patch('deposits.publish_absent', side_effect=InterruptedError('before publication')):
            with self.assertRaises(InterruptedError):
                self.b.finalize_prompt('before')
        self.assertFalse((self.repo / 'reports/prompts/CODEX_PROMPT_before.md').exists())
        partials = {p: p.read_bytes() for p in (self.repo / 'reports/prompts').glob('.*.pending')}
        self.assertTrue(partials)
        self.assertEqual(Path(self.b.finalize_prompt('before')['path']).read_bytes(), self.contract('before').encode())
        self.assertEqual(next(iter(partials.values())), self.contract('before').encode())
        for path in partials:
            self.assertFalse(path.exists())  # Proven alias retired after publication.
        self.upload('after')
        original_publish = deposits.publish_absent
        def interrupt_after(*args):
            original_publish(*args)
            raise InterruptedError('reply lost after atomic publication')
        with mock.patch('deposits.publish_absent', side_effect=interrupt_after):
            with self.assertRaises(InterruptedError):
                self.b.finalize_prompt('after')
        target = self.repo / 'reports/prompts/CODEX_PROMPT_after.md'
        identity = target.stat().st_ino
        self.assertTrue(self.b.finalize_prompt('after')['duplicate_deposit'])
        self.assertEqual(target.stat().st_ino, identity)
        self.assertEqual(target.stat().st_nlink, 1)
        partial = self.upload('prefix')
        pending = target.parent / ('.' + deposits.filename('prefix') + '.pending')
        pending.write_bytes(partial[:17])
        self.assertEqual(Path(self.b.finalize_prompt('prefix')['path']).read_bytes(), partial)
        self.assertFalse(pending.exists())

    def test_deposit_collision_link_and_directory_replacement(self):
        for ident, kind in (('conflict', 'bytes'), ('symlink', 'symlink'), ('hardlink', 'hardlink'), ('fifo', 'fifo')):
            content = self.upload(ident)
            with deposits.prompt_directory(self.repo, create=True) as (_, root):
                target = root / deposits.filename(ident)
                foreign = self.base / (ident + '_foreign')
                foreign.write_bytes(content if kind == 'hardlink' else b'foreign')
                if kind == 'bytes':
                    target.write_bytes(b'foreign')
                elif kind == 'symlink':
                    target.symlink_to(foreign)
                elif kind == 'hardlink':
                    os.link(foreign, target)
                else:
                    os.mkfifo(target)
                before = target.lstat()
                with self.assertRaises((OSError, ValueError)):
                    self.b.finalize_prompt(ident)
                self.assertEqual(target.lstat().st_ino, before.st_ino)
                self.assertEqual(foreign.read_bytes(), content if kind == 'hardlink' else b'foreign')
        self.upload('root')
        root = self.repo / 'reports/prompts'
        preserved = root.with_name('preserved_prompts')
        root.rename(preserved)
        root.symlink_to(preserved, target_is_directory=True)
        with self.assertRaises(OSError):
            self.b.finalize_prompt('root')
        self.assertFalse((preserved / deposits.filename('root')).exists())

    def test_manual_exact_bytes_dedup_status_and_collector(self):
        content = self.upload('local', self.contract('local').encode() + b'\r\n' + '雪€🦊'.encode() * 4000)
        deposited = self.b.finalize_prompt('local')
        first = self.manual('submit', 'local')
        self.assertTrue(first['ok'], first)
        second = self.manual('submit', 'local')
        self.assertTrue(second['result']['duplicate_request'], second)
        receipt = self.finish('local')
        self.assertEqual(receipt['state'], 'COMPLETED', receipt)
        self.assertTrue(receipt['governed_contract'])
        self.assertEqual((self.b.root / 'local/received.bin').read_bytes(), content)
        self.assertEqual(Path(deposited['path']).read_bytes(), content)
        rows = self.b.task_artifacts('local')['artifacts']
        self.assertEqual(self.retrieve('local', next(r for r in rows if r['name'] == 'transport/prompt.txt')), content)
        self.assertTrue(any(r['name'].endswith('_report.md') for r in rows))
        self.assertTrue(any(r['name'].endswith('_worktree_diff.patch') for r in rows))
        self.assertEqual(self.manual('status', 'local')['result']['state'], 'COMPLETED')
        with self.b.db() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM tasks').fetchone()[0], 1)
        # Status remains usable even if the admission profile later breaks.
        self.profile.write_text('broken profile')
        self.assertEqual(self.manual('status', 'local')['result']['state'], 'COMPLETED')
        retain_fixture_evidence(self.b, 'local', self._testMethodName)
        selected = os.environ.get('GLADOS_BRIDGE_TEST_EVIDENCE')
        if selected:
            with zipfile.ZipFile(selected, 'a', compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr(self._testMethodName + '/publication.json', json.dumps(deposited))
                archive.write(deposited['path'], self._testMethodName + '/published.md')

    def test_manual_tamper_link_scope_and_snapshot_binding(self):
        content = self.upload('snapshot')
        path = Path(self.b.finalize_prompt('snapshot')['path'])
        path.write_bytes(content + b'changed')
        self.assertIn('DEPOSIT_CONFLICT_OR_CHANGED', self.manual('submit', 'snapshot')['error'])
        path.unlink()  # Fixture-owned altered entry only.
        path.symlink_to(self.profile)
        with self.assertRaises(OSError):
            self.b.deposited_prompt('snapshot')
        path.unlink()
        self.b.finalize_prompt('snapshot')
        self.assertIn('request_id must', self.manual('submit', '../profile')['error'])
        snapshot = self.b.deposited_prompt('snapshot')
        path.rename(path.with_suffix('.preserved'))
        path.write_bytes(b'foreign replacement after snapshot')
        self.b.submit('snapshot', snapshot)
        receipt = self.finish('snapshot')
        self.assertEqual(receipt['state'], 'COMPLETED', receipt)
        self.assertEqual((self.b.root / 'snapshot/received.bin').read_bytes(), content)
        self.assertEqual(path.read_bytes(), b'foreign replacement after snapshot')
        retain_fixture_evidence(self.b, 'snapshot', self._testMethodName)

    def test_manual_busy_and_partial_failure_retrieval(self):
        self.upload('partial', self.contract('partial').encode() + b'FAIL_PARTIAL\n')
        self.b.finalize_prompt('partial')
        lock = self.b.lock('busy.lock')
        try:
            response = self.manual('submit', 'partial')
            self.assertFalse(response['ok'])
            self.assertIn('BUSY', response['error'])
            with self.b.db() as db:
                self.assertEqual(db.execute('SELECT count(*) FROM tasks').fetchone()[0], 0)
        finally:
            os.close(lock)
        self.assertTrue(self.manual('submit', 'partial')['ok'])
        receipt = self.finish('partial')
        self.assertEqual(receipt['state'], 'FAILED', receipt)
        self.assertEqual(receipt['returncode'], 7)
        self.assertFalse(receipt['process_success'])
        self.assertEqual(receipt['collection_error'], 'ValueError')
        self.assertEqual(receipt['collection_failure_reason'], 'BRIDGE_BOOKKEEPING_COLLISION')
        rows = self.b.task_artifacts('partial')['artifacts']
        report = next(r for r in rows if r['name'].endswith('_report.md'))
        self.assertEqual(self.retrieve('partial', report), b'Executor partial report\x00\xff')
        self.assertTrue(self.manual('submit', 'partial')['result']['duplicate_request'])
        retain_fixture_evidence(self.b, 'partial', self._testMethodName)

    def test_manual_replacement_during_real_cli_preflight(self):
        content = self.upload('replacement')
        path = Path(self.b.finalize_prompt('replacement')['path'])
        implementation = self.fake.with_suffix('.py')
        source = implementation.read_text()
        source = source.replace("if '--version' in sys.argv:\n",
            "if '--version' in sys.argv:\n pathlib.Path(" + repr(str(path)) +
            ").write_bytes(b'replacement after file snapshot')\n", 1)
        implementation.write_text(source)
        response = self.manual('submit', 'replacement')
        self.assertTrue(response['ok'], response)
        self.assertIn(' status replacement', response['observe_command'])
        self.assertEqual(self.finish('replacement')['state'], 'COMPLETED')
        self.assertEqual(path.read_bytes(), b'replacement after file snapshot')
        self.assertEqual((self.b.root / 'replacement/received.bin').read_bytes(), content)
        retain_fixture_evidence(self.b, 'replacement', self._testMethodName)

    def test_pending_conflict_and_replacement_preserved(self):
        self.upload('pending')
        with deposits.prompt_directory(self.repo, create=True) as (_, root):
            pending = root / ('.' + deposits.filename('pending') + '.pending')
            pending.write_bytes(b'foreign conflicting bytes')
            with self.assertRaisesRegex(ValueError, 'PENDING_CONFLICT'):
                self.b.finalize_prompt('pending')
            self.assertEqual(pending.read_bytes(), b'foreign conflicting bytes')
            self.assertFalse((root / deposits.filename('pending')).exists())
            pending.rename(pending.with_suffix('.preserved'))
            pending.symlink_to(self.profile)
            original = self.profile.read_bytes()
            with self.assertRaises(OSError):
                self.b.finalize_prompt('pending')
            self.assertEqual(self.profile.read_bytes(), original)


if __name__ == '__main__':
    unittest.main(verbosity=2)
