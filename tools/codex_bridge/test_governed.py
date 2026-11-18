"""Local functional qualification: real Git/files/RPC; simulated Codex only."""
import base64
import hashlib
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
import zipfile
from unittest import mock

import bridge
from artifacts import artifact_page, freeze_artifacts
from artifacts import begin_evidence, finish_evidence
from governed_task import DEPENDENCIES, GovernedInbox
from repository_task import git
from test_support import write_fake, retain_fixture_evidence


FAKE = r'''#!/usr/bin/env python3
import hashlib,json,os,pathlib,re,subprocess,sys
if '--version' in sys.argv:
 print('codex-cli 0.167.0');sys.exit(0)
if '--help' in sys.argv:
 print('--ignore-user-config --ephemeral --json --sandbox --output-last-message --skip-git-repo-check --approve-for-me --add-dir');sys.exit(0)
content=sys.stdin.buffer.read()
prompt=content.decode('utf-8')
assert all(k not in os.environ for k in ['CONTROL_PLANE_API_KEY','OPENAI_API_KEY','CODEX_API_KEY'])
result=pathlib.Path(sys.argv[sys.argv.index('--output-last-message')+1])
(result.parent/'received.bin').write_bytes(content)
assert sys.argv[-1]=='-'
context=next(json.loads(v.split('=',1)[1]) for v in sys.argv if v.startswith('developer_instructions='))
report=pathlib.Path(re.search(r'Canonical report path: (.*?)\. Canonical patch',context)[1])
patch=pathlib.Path(re.search(r'Canonical patch path: (.*?)\. Produce files',context)[1])
assert sys.argv[sys.argv.index('--cd')+1]==str(report.parent)
assert sys.argv[sys.argv.index('--sandbox')+1]=='workspace-write'
assert 'leave that exact path absent' not in context
root=pathlib.Path(re.search(r'^workspace_root: (.*)$',prompt,re.M)[1])
print(json.dumps({'type':'turn.started'}),flush=True)
if 'FAIL_BEFORE_RESULT' in prompt or 'FAIL_PARTIAL' in prompt:
 if 'FAIL_PARTIAL' in prompt:
  report.write_bytes(b'' if 'EMPTY_REPORT' in prompt else b'Executor partial report\x00\xff')
  patch.write_bytes(b'partial conflicting patch\x00\xff')
  nested=report.parent/'nested'
  nested.mkdir()
  (nested/'bytes.bin').write_bytes(bytes(range(256))*131)
  (report.parent/'bridge_bookkeeping.json').write_bytes(b'original bookkeeping collision')
 print('simulated primary bootstrap failure: EROFS',file=sys.stderr,flush=True)
 print(json.dumps({'type':'turn.failed'}),flush=True)
 sys.exit(7)
if 'SYNTHETIC_CODING' in prompt:
 os.chdir(root)
 before=subprocess.check_output(['git','rev-parse','HEAD']).decode().strip()
 assert '--approve-for-me' in sys.argv
 assert str(root) in [sys.argv[i+1] for i,v in enumerate(sys.argv) if v=='--add-dir']
 pathlib.Path('payload.txt').write_bytes('changed ünicode\n'.encode())
 subprocess.run(['git','add','--','payload.txt'],check=True)
 subprocess.run(['git','commit','-qm','test: change isolated payload'],check=True)
else:
 assert '--add-dir' not in sys.argv
 assert '--approve-for-me' not in sys.argv
if 'EXECUTOR_PATCH' in prompt:
 data=subprocess.check_output(['git','diff','--binary','-U0',before,'--']) if 'SYNTHETIC_CODING' in prompt else b''
 if 'MISMATCH_PATCH' in prompt:
  data=data.replace('changed ünicode'.encode(),'wrong ünicode'.encode())
 patch.write_bytes(data)
 (result.parent/'executor_patch.bin').write_bytes(data)
body=b'# Fixture task report\nSimulated Codex, real local files and Git.\n'
if 'FINAL_MESSAGE_ONLY' not in prompt:
 report.write_bytes(body)
(report.parent/'bytes_雪.bin').write_bytes(bytes(range(256))*131+'€雪'.encode())
result.write_bytes(body)
print(json.dumps({'type':'turn.completed'}),flush=True)
'''


class GovernedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.authority = Path(__file__).resolve().parents[2]
        # Historical execution compatibility is a fixture input, not authority
        # for this checkout. Current-master admission is tested separately and
        # must refuse unsupported new semantics without launching inference.
        cls.master = 'e308672369d600f933a5a9fefa6de33e58a3f20f'
        paths = (*DEPENDENCIES, 'governance/modules/topeft.md',
                 'governance/modules/topcoffea.md', 'governance/modules/andocs.md',
                 'governance/modules/eftfit.md')
        # Only historical setup data has a portable fallback. Readers and
        # admission still obtain their current binding from refs/heads/master.
        try:
            git(cls.authority, 'cat-file', '-e', cls.master + '^{commit}')
        except ValueError:
            # An invalid checkout must not be mistaken for an absent pin.
            git(cls.authority, 'rev-parse', '--verify', 'HEAD')
            fixture = Path(__file__).resolve().parent / 'fixtures/historical_governed'
            manifest = json.loads((fixture / 'manifest.json').read_text(encoding='utf-8'))
            if manifest['format_version'] != 1 or manifest['revision'] != cls.master:
                raise ValueError('HISTORICAL_FIXTURE_REVISION_MISMATCH')
            rows = manifest['files']
            if len(rows) != len(paths) or {row['path'] for row in rows} != set(paths):
                raise ValueError('HISTORICAL_FIXTURE_MEMBERSHIP_MISMATCH')
            cls.sources = {}
            for row in rows:
                content = (fixture / row['path']).read_bytes()
                blob = b'blob ' + str(len(content)).encode('ascii') + b'\0' + content
                if (len(content) != row['size_bytes'] or
                        hashlib.sha256(content).hexdigest() != row['sha256'] or
                        hashlib.sha1(blob).hexdigest() != row['object_id']):
                    raise ValueError('HISTORICAL_FIXTURE_CONTENT_MISMATCH: ' + row['path'])
                cls.sources[row['path']] = content
        else:
            cls.sources = {p: git(cls.authority, 'show', cls.master + ':' + p) for p in paths}

    def setUp(self):
        self.consumer_pages = {}
        retained = os.environ.get('GLADOS_BRIDGE_RETAIN_FIXTURES')
        self.tmp = None if retained else tempfile.TemporaryDirectory(prefix='bridge_qualification_')
        self.base = Path(tempfile.mkdtemp(prefix='bridge_qualification_', dir=retained)
                         if retained else self.tmp.name)
        self.repo = self.base / 'repo'
        self.repo.mkdir()
        self.run_git('init', '-q', '-b', 'master')
        self.run_git('config', 'user.name', 'Local fixture')
        self.run_git('config', 'user.email', 'fixture@example.invalid')
        for path, content in self.sources.items():
            target = self.repo / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        (self.repo / 'payload.txt').write_text('before\n')
        self.run_git('add', '--', *self.sources, 'payload.txt')
        self.run_git('commit', '-qm', 'test: initialize isolated fixture')
        self.run_git('switch', '-qc', 'fixture_work')
        self.evidence = self.base / 'evidence'
        self.evidence.mkdir()
        self.fake = self.base / 'codex'
        write_fake(self.fake, FAKE)
        self.wrapper = self.base / 'wrapper'
        self.wrapper.write_text('#!/bin/sh\nexec "$@"\n')
        self.wrapper.chmod(0o700)
        self.profile = self.base / 'profile.yml'
        self.profile.write_text(
            'profile_version: 1\nprofile_name: fixture\nworkspace_root: ' + str(self.repo) +
            '\nevidence_root: ' + str(self.evidence) + '\nprovider_procedure: openai_codex\ntooling:\n'
            '  command_wrapper: ' + str(self.wrapper) + '\n  python_interpreter: ' + sys.executable +
            '\nrepositories:\n  TOP26006_fw:\n    path: ' + str(self.repo) + '\n')
        self.b = bridge.Bridge(self.base / 'state', str(self.fake), wrapper=str(self.wrapper))
        self.b.inbox = GovernedInbox(self.profile, self.repo, self.b.root)

    def tearDown(self):
        selected = os.environ.get('GLADOS_BRIDGE_TEST_EVIDENCE')
        if selected and Path(selected).exists() and self.consumer_pages:
            with zipfile.ZipFile(selected, 'a', compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr(self._testMethodName + '/consumer_pages.json',
                                 json.dumps(self.consumer_pages))
        if self.tmp:
            self.tmp.cleanup()

    def run_git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args], check=True, capture_output=True).stdout

    def contract(self, ident='fixture', coding=False):
        return ('```yaml\nprompt_id: ' + ident + '\nshort_title: local_fixture\nprompt_mode: ' +
                ('coding' if coding else 'investigation_only') +
                '\npreferred_codex_model: gpt-6.1-sol\nreasoning_level: high\ndelegation_policy: forbidden\n'
                'model_selection_rationale: bounded local fixture\nworkspace_root: ' + str(self.repo) +
                '\nrepo_locations:\n  TOP26006_fw: ' + str(self.repo) + '\nallowed_to_modify: ' +
                ('\n  - TOP26006_fw:payload.txt' if coding else '[]') +
                '\nread_only:\n  - TOP26006_fw governance\nvalidation_ceiling: ' +
                ('targeted_unit_test' if coding else 'static_inspection_only') + '\n'
                'decision_question: can the fixture return exact task evidence\npatch_kind_expected: ' +
                ('prompt_local' if coding else 'empty_no_changes') +
                '\nfinal_chat_deliverable: actual report and patch\npatch_producer: codex_or_host\nbranch_policy: ' +
                ('continue_existing_branch\ntarget_branch: fixture_work' if coding else 'read_only_current_branch') +
                '\nheavy_command_permissions:\n  network_access: no\n  storage_writes: no\n```\n' +
                ('SYNTHETIC_CODING\n' if coding else 'Inspect only.\n'))

    def finish(self, ident):
        end = time.monotonic() + 90
        while time.monotonic() < end:
            receipt = self.b.status(ident)
            if receipt['state'] not in ('STARTING', 'RUNNING'):
                try:
                    fd = self.b.lock('busy.lock')
                except BlockingIOError:
                    pass
                else:
                    os.close(fd)
                    pid = receipt.get('supervisor_pid')
                    if not pid or not Path('/proc/%d' % pid).exists():
                        return receipt
            time.sleep(.05)
        self.fail('fixture worker did not terminate')

    def retrieve(self, ident, row, size=32768):
        other = bridge.Bridge(self.b.root, str(self.fake))
        content, offset = bytearray(), 0
        while True:
            page = other.task_artifact(ident, row['artifact_id'], offset, size)
            self.consumer_pages.setdefault(ident + '/' + row['artifact_id'], []).append(page)
            chunk = base64.b64decode(page['data'], validate=True)
            self.assertEqual(hashlib.sha256(chunk).hexdigest(), page['chunk_sha256'])
            content.extend(chunk)
            offset = page['next_offset']
            if not page['has_more']:
                break
        self.assertEqual(len(content), row['size_bytes'])
        self.assertEqual(hashlib.sha256(content).hexdigest(), row['sha256'])
        return bytes(content)

    def test_large_utf8_upload_readonly_canonical_collision_and_second_session(self):
        ident = 'large'
        (self.evidence / ident).mkdir()
        prompt = self.contract(ident) + '雪€🦊' * 9000
        content = prompt.encode('utf-8')
        digest = hashlib.sha256(content).hexdigest()
        self.assertGreater(len(content), 32768)
        self.b.prompt_upload(ident, len(content), digest)
        for offset in range(0, len(content), 24575):
            data = base64.b64encode(content[offset:offset + 24575]).decode()
            self.b.prompt_chunk(ident, offset, data)
            self.assertTrue(self.b.prompt_chunk(ident, offset, data)['duplicate_chunk'])
        self.b.submit_uploaded_task(ident)
        receipt = self.finish(ident)
        self.assertEqual(receipt['state'], 'COMPLETED', receipt)
        self.assertEqual(Path(receipt['evidence_directory']).name, ident + '_rerun_001')
        self.assertEqual((self.b.root / ident / 'received.bin').read_bytes(), content)
        self.assertEqual(Path(receipt['patch_path']).read_bytes(), b'')
        rows = self.b.task_artifacts(ident)['artifacts']
        row = next(r for r in rows if r['name'] == 'bytes_雪.bin')
        self.assertEqual(self.retrieve(ident, row, 32767), bytes(range(256)) * 131 + '€雪'.encode())
        prompt_row = next(r for r in rows if r['name'] == 'transport/prompt.txt')
        self.assertEqual(self.retrieve(ident, prompt_row), content)
        self.assertTrue(self.b.submit_uploaded_task(ident)['duplicate_request'])
        retain_fixture_evidence(self.b, ident, self._testMethodName)

    def test_coding_real_commit_actual_patch_and_foreign_untracked_preserved(self):
        (self.repo / 'foreign.txt').write_bytes(b'foreign work\x00')
        before = self.run_git('rev-parse', 'HEAD').decode().strip()
        prompt = self.contract('coding', coding=True)
        self.b.submit('coding', prompt)
        receipt = self.finish('coding')
        self.assertEqual(receipt['state'], 'COMPLETED', receipt)
        after = self.run_git('rev-parse', 'HEAD').decode().strip()
        self.assertNotEqual(before, after)
        self.assertEqual(self.run_git('rev-parse', 'HEAD^').decode().strip(), before)
        patch = Path(receipt['patch_path']).read_bytes()
        native = self.run_git('diff', '--binary', before, after, '--')
        self.assertEqual(patch, native)
        self.assertIn(b'payload.txt', patch)
        self.assertEqual((self.repo / 'foreign.txt').read_bytes(), b'foreign work\x00')
        self.assertEqual(self.run_git('status', '--porcelain', '--untracked-files=no'), b'')
        manifest = self.b.task_artifacts('coding')['artifacts']
        row = next(r for r in manifest if r['name'].endswith('_worktree_diff.patch'))
        self.assertEqual(self.retrieve('coding', row, 13), native)
        retain_fixture_evidence(self.b, 'coding', self._testMethodName)

    def test_executor_patch_preserved_semantically_and_retrieved(self):
        prompt = self.contract('provided', coding=True).replace('patch_producer: codex_or_host\n', '')
        self.b.submit('provided', prompt + 'EXECUTOR_PATCH\n')
        receipt = self.finish('provided')
        self.assertEqual(receipt['state'], 'COMPLETED', receipt)
        authored = (self.b.root / 'provided/executor_patch.bin').read_bytes()
        self.assertEqual(Path(receipt['patch_path']).read_bytes(), authored)
        self.assertEqual(receipt['patch_producer'], 'executor_file')
        self.assertEqual(receipt['patch_validation'], 'equivalent_trees_after_private_git_apply')
        row = next(r for r in self.b.task_artifacts('provided')['artifacts'] if r['name'].endswith('_worktree_diff.patch'))
        self.assertEqual(self.retrieve('provided', row, 17), authored)
        retain_fixture_evidence(self.b, 'provided', self._testMethodName)

    def test_executor_mismatch_is_failed_preserved_and_retrievable(self):
        self.b.submit('mismatch', self.contract('mismatch', coding=True) + 'EXECUTOR_PATCH\nMISMATCH_PATCH\n')
        receipt = self.finish('mismatch')
        self.assertEqual(receipt['state'], 'FAILED', receipt)
        self.assertTrue(any('PATCH_MISMATCH' in f for f in receipt['evidence_findings']))
        authored = (self.b.root / 'mismatch/executor_patch.bin').read_bytes()
        self.assertEqual(Path(receipt['patch_path']).read_bytes(), authored)
        row = next(r for r in self.b.task_artifacts('mismatch')['artifacts'] if r['name'].endswith('_worktree_diff.patch'))
        self.assertEqual(self.retrieve('mismatch', row), authored)
        self.assertEqual(receipt['patch_kind'], 'unvalidated')
        retain_fixture_evidence(self.b, 'mismatch', self._testMethodName)

    def test_missing_executor_patch_requires_authored_fallback(self):
        prompt = self.contract('missing').replace('patch_producer: codex_or_host\n', '')
        self.b.submit('missing', prompt)
        receipt = self.finish('missing')
        self.assertEqual(receipt['state'], 'FAILED', receipt)
        self.assertEqual(receipt['patch_producer'], 'absent')
        self.assertFalse(Path(receipt['patch_path']).exists())
        self.assertTrue(any('REQUIRED_EXECUTOR_PATCH_ABSENT' in f for f in receipt['evidence_findings']))
        retain_fixture_evidence(self.b, 'missing', self._testMethodName)

    def test_source_readonly_diagnostics_and_final_message_capture(self):
        before = self.run_git('rev-parse', 'HEAD')
        prompt = self.contract('diagnostics') + 'FINAL_MESSAGE_ONLY\n'
        self.b.submit('diagnostics', prompt)
        receipt = self.finish('diagnostics')
        self.assertEqual(receipt['state'], 'COMPLETED', receipt)
        self.assertEqual(receipt['report_producer'], 'exact_final_message_capture')
        self.assertEqual(Path(receipt['report_path']).read_bytes(), (self.b.root / 'diagnostics/result.txt').read_bytes())
        args = receipt['argv']
        self.assertEqual(args[args.index('--cd') + 1], receipt['evidence_directory'])
        self.assertNotIn('--add-dir', args)
        self.assertIn('sandbox_workspace_write.exclude_slash_tmp=true', args)
        self.assertIn('sandbox_workspace_write.exclude_tmpdir_env_var=true', args)
        self.assertEqual(self.run_git('rev-parse', 'HEAD'), before)
        self.assertTrue(receipt['tracked_state_unchanged'])
        self.assertEqual(receipt['evidence_contract']['native_enforcement'], 'not_observed; argv is a capability request')
        row = next(r for r in self.b.task_artifacts('diagnostics')['artifacts'] if r['name'] == 'bytes_雪.bin')
        self.assertEqual(self.retrieve('diagnostics', row), bytes(range(256))*131 + '€雪'.encode())
        retain_fixture_evidence(self.b, 'diagnostics', self._testMethodName)

    def direct_evidence(self, ident='direct', coding=True):
        prompt = self.contract(ident, coding)
        task = self.b.inbox.task(ident, prompt)
        folder = self.b.root / ident
        folder.mkdir()
        (folder / 'prompt.txt').write_text(prompt)
        for name in ('result.txt', 'events.jsonl', 'stderr.log'):
            (folder / name).write_bytes(b'fixture transport')
        return folder, begin_evidence(folder, task.admit(ident, prompt), ident)

    def test_failure_before_final_message_has_no_report_and_preserves_process_failure(self):
        ident = 'no_result'
        self.b.submit(ident, self.contract(ident) + 'FAIL_BEFORE_RESULT\n')
        receipt = self.finish(ident)
        self.assertEqual((receipt['state'], receipt['returncode']), ('FAILED', 7))
        self.assertFalse(receipt['process_success'])
        self.assertFalse(receipt['turn_completed_observed'])
        self.assertTrue(receipt['turn_failed_observed'])
        self.assertEqual(receipt['report_producer'], 'absent')
        self.assertIsNone(receipt['report_sha256'])
        self.assertFalse(Path(receipt['report_path']).exists())
        self.assertTrue(any('FINAL_MESSAGE_ABSENT' in f for f in receipt['evidence_findings']))
        self.assertNotIn('collection_error', receipt)
        rows = self.b.task_artifacts(ident)['artifacts']
        self.assertFalse(any(r['name'].endswith('_report.md') for r in rows))
        stderr = next(r for r in rows if r['name'] == 'transport/stderr.log')
        self.assertIn(b'primary bootstrap failure: EROFS', self.retrieve(ident, stderr))
        retain_fixture_evidence(self.b, ident, self._testMethodName)

    def test_partial_failure_evidence_listing_and_byte_pages_including_real_empty_report(self):
        for ident, empty in (('partial', False), ('empty_report', True)):
            with self.subTest(ident=ident):
                self.b.submit(ident, self.contract(ident) + 'FAIL_PARTIAL\n' + ('EMPTY_REPORT\n' if empty else ''))
                receipt = self.finish(ident)
                self.assertEqual((receipt['state'], receipt['returncode']), ('FAILED', 7))
                self.assertFalse(receipt['process_success'])
                self.assertTrue(receipt['turn_failed_observed'])
                self.assertEqual(receipt['collection_error'], 'ValueError')
                self.assertEqual(receipt['collection_failure_reason'], 'BRIDGE_BOOKKEEPING_COLLISION')
                manifest = self.b.task_artifacts(ident)
                self.assertFalse(manifest['manifest_frozen'])
                rows = manifest['artifacts']
                for name, expected in ((ident + '_report.md', b'' if empty else b'Executor partial report\x00\xff'),
                                       (ident + '_worktree_diff.patch', b'partial conflicting patch\x00\xff'),
                                       ('nested/bytes.bin', bytes(range(256))*131),
                                       ('bridge_bookkeeping.json', b'original bookkeeping collision')):
                    row = next(r for r in rows if r['name'] == name)
                    self.assertEqual(row['evidence_status'], 'partial_unvalidated')
                    self.assertEqual(self.retrieve(ident, row, 32767), expected)
                    self.assertEqual((Path(receipt['evidence_directory']) / name).read_bytes(), expected)
                log = next(r for r in rows if r['name'] == 'stderr.log')
                self.assertIn(b'primary bootstrap failure: EROFS', self.retrieve(ident, log))
                with self.assertRaisesRegex(ValueError, 'UNKNOWN_TASK_ARTIFACT'):
                    self.b.task_artifact(ident, str(Path(receipt['report_path'])))
                retain_fixture_evidence(self.b, ident, self._testMethodName + '_' + ident)

    def test_partial_evidence_rejects_links_special_files_and_changed_directory(self):
        ident = 'unsafe_partial'
        self.b.submit(ident, self.contract(ident) + 'FAIL_PARTIAL\n')
        receipt = self.finish(ident)
        evidence = Path(receipt['evidence_directory'])
        original = Path(receipt['report_path']).read_bytes()
        foreign = self.base / 'foreign_evidence'
        foreign.write_bytes(b'foreign bytes')
        target = evidence / 'unsafe'
        for kind in ('symlink', 'fifo', 'hardlink', 'directory_link'):
            with self.subTest(kind=kind):
                if kind == 'symlink':
                    target.symlink_to(foreign)
                elif kind == 'fifo':
                    os.mkfifo(target)
                elif kind == 'hardlink':
                    os.link(foreign, target)
                else:
                    target.symlink_to(self.base, target_is_directory=True)
                with self.assertRaises((ValueError, OSError)):
                    self.b.task_artifacts(ident)
                with self.assertRaises((ValueError, OSError)):
                    self.b.task_artifact(ident, 'partial_unsafe')
                target.unlink()  # Exact fixture-owned unsafe entry only.
        self.assertEqual(foreign.read_bytes(), b'foreign bytes')
        self.assertEqual(Path(receipt['report_path']).read_bytes(), original)
        for artifact_id in ('partial_../foreign_evidence', 'partial_/etc/passwd'):
            with self.assertRaisesRegex(ValueError, 'UNKNOWN_TASK_ARTIFACT'):
                self.b.task_artifact(ident, artifact_id)
        evidence.rename(evidence.with_name('preserved_evidence'))
        evidence.mkdir()
        with self.assertRaisesRegex(ValueError, 'EVIDENCE_DIRECTORY_IDENTITY_CHANGED'):
            self.b.task_artifacts(ident)

    def test_legacy_failed_artifact_recovery_without_governed_locator(self):
        ident = 'legacy_failed'
        folder = self.b.root / ident
        folder.mkdir()
        values = {'stderr.log': b'legacy failure\x00\xff', ident + '_report.md': b''}
        for name, content in values.items():
            (folder / name).write_bytes(content)
        with self.b.db() as db:
            db.execute('INSERT INTO tasks VALUES (?,?,?,?,?,?,?)',
                       (ident, 'legacy_digest', '', 'FAILED', 0, 0, '{}'))
        manifest = self.b.task_artifacts(ident)
        self.assertFalse(manifest['manifest_frozen'])
        for row in manifest['artifacts']:
            self.assertTrue(row['artifact_id'].startswith('legacy_'))
            self.assertEqual(self.retrieve(ident, row), values[row['name']])
        retain_fixture_evidence(self.b, ident, self._testMethodName)

    def test_partial_page_rechecks_directory_components_and_regular_file(self):
        ident = 'page_binding'
        self.b.submit(ident, self.contract(ident) + 'FAIL_PARTIAL\n')
        receipt = self.finish(ident)
        manifest = self.b.task_artifacts(ident)
        evidence = Path(receipt['evidence_directory'])
        nested = evidence / 'nested'
        nested.rename(evidence / 'preserved_nested')
        nested.symlink_to(self.base, target_is_directory=True)
        # A stale listing cannot authorize a page through a swapped parent.
        with mock.patch.object(self.b, 'task_artifacts', return_value=manifest):
            with self.assertRaises(OSError):
                self.b.task_artifact(ident, 'partial_nested/bytes.bin')
        nested.unlink()
        (evidence / 'preserved_nested').rename(nested)
        report = Path(receipt['report_path'])
        report.rename(evidence / 'preserved_report')
        os.mkfifo(report)
        with mock.patch.object(self.b, 'task_artifacts', return_value=manifest):
            with self.assertRaisesRegex(ValueError, 'REGULAR_FILE'):
                self.b.task_artifact(ident, 'partial_' + report.name)

    def test_existing_empty_report_without_result_remains_executor_file(self):
        folder, receipt = self.direct_evidence('real_empty', coding=False)
        (folder / 'result.txt').unlink()
        Path(receipt['report_path']).write_bytes(b'')
        result = finish_evidence(folder, receipt, 'real_empty')
        self.assertEqual(result['report_producer'], 'executor_file')
        self.assertEqual(result['report_sha256'], hashlib.sha256(b'').hexdigest())
        self.assertEqual(result['evidence_findings'], [])
        rows = json.loads((folder / 'artifacts.json').read_bytes())
        row = next(r for r in rows if r['name'] == 'real_empty_report.md')
        self.assertEqual(base64.b64decode(artifact_page(folder, row, 0, 1)['data']), b'')

    def test_present_patch_equivalent_encodings_and_dirty_strip_conventions(self):
        # Direct actual consumer: more context than the measured default, then
        # -p1 executor encoding over a frozen dirty baseline measured with -p2.
        (self.repo / 'payload.txt').write_text(''.join('line %d\n' % n for n in range(30)))
        self.run_git('add', '--', 'payload.txt')
        self.run_git('commit', '-qm', 'test: multiline isolated baseline')
        for ident, dirty in (('context', False), ('dirty_provided', True)):
            with self.subTest(ident=ident):
                if dirty:
                    (self.repo / 'CPC.md').write_bytes((self.repo / 'CPC.md').read_bytes() + b'\nforeign\n')
                prompt = self.contract(ident, True).replace('heavy_command_permissions:',
                    'dirty_worktree_policy: allow_declared_preexisting_changes\nheavy_command_permissions:')
                task = self.b.inbox.task(ident, prompt)
                folder = self.b.root / ident
                folder.mkdir()
                (folder / 'prompt.txt').write_text(prompt)
                for name in ('result.txt', 'events.jsonl', 'stderr.log'):
                    (folder / name).write_bytes(b'fixture transport')
                receipt = begin_evidence(folder, task.admit(ident, prompt), ident)
                (self.repo / 'payload.txt').write_text((self.repo / 'payload.txt').read_text().replace('line 15', ident))
                if dirty:
                    (self.repo / 'payload.txt').write_text((self.repo / 'payload.txt').read_text().replace('line 16', ident))
                initial = self.run_git('diff', '--binary', '-U10', '--', 'payload.txt')
                Path(receipt['patch_path']).write_bytes(initial)
                result = finish_evidence(folder, receipt, ident)
                self.assertEqual(result['evidence_findings'], [])
                self.assertEqual(Path(receipt['patch_path']).read_bytes(), initial)
                self.assertEqual(result['patch_strip_components']['TOP26006_fw'], 1)
                # Bring only this fixture's payload into its next committed base.
                self.run_git('add', '--', 'payload.txt')
                self.run_git('commit', '-qm', 'test: next isolated baseline')

    def test_foreign_evidence_collisions_and_special_paths_never_overwritten(self):
        existing = self.evidence / 'direct'
        existing.mkdir()
        foreign = existing / 'direct_worktree_diff.patch'
        foreign.write_bytes(b'foreign evidence')
        folder, receipt = self.direct_evidence()
        self.assertEqual(Path(receipt['evidence_directory']).name, 'direct_rerun_001')
        finish_evidence(folder, receipt, 'direct')
        self.assertEqual(foreign.read_bytes(), b'foreign evidence')
        for ident, kind in (('bookkeeping', 'bookkeeping'), ('symlink', 'symlink'), ('fifo', 'fifo')):
            with self.subTest(ident=ident):
                folder, receipt = self.direct_evidence(ident)
                path = Path(receipt['patch_path'])
                if kind == 'bookkeeping':
                    path = Path(receipt['evidence_directory']) / 'bridge_bookkeeping.json'
                    path.write_bytes(b'foreign bookkeeping')
                elif kind == 'symlink':
                    path.symlink_to(foreign)
                else:
                    os.mkfifo(path)
                with self.assertRaises((ValueError, OSError)):
                    finish_evidence(folder, receipt, ident)
                self.assertEqual(foreign.read_bytes(), b'foreign evidence')
                if kind == 'bookkeeping':
                    self.assertEqual(path.read_bytes(), b'foreign bookkeeping')

    def test_finish_binary_mode_deletion_and_independent_repo_sections(self):
        second = self.base / 'consumer'
        subprocess.run(['git', 'clone', '-q', '--no-hardlinks', str(self.repo), str(second)], check=True)
        prompt = self.contract('binary', True).replace(
            '  TOP26006_fw: ' + str(self.repo),
            '  TOP26006_fw: ' + str(self.repo) + '\n  topeft: ' + str(second))
        prompt = prompt.replace('- TOP26006_fw:payload.txt',
                                '- TOP26006_fw:payload.txt\n  - topeft:payload.txt')
        task = self.b.inbox.task('binary', prompt)
        folder = self.b.root / 'binary'
        folder.mkdir()
        (folder / 'prompt.txt').write_text(prompt)
        for name in ('result.txt', 'events.jsonl', 'stderr.log'):
            (folder / name).write_bytes(b'fixture transport')
        receipt = begin_evidence(folder, task.admit('binary', prompt), 'binary')
        (self.repo / 'payload.txt').write_bytes(bytes(range(256)) * 30)
        (self.repo / 'payload.txt').chmod(0o755)
        (second / 'payload.txt').unlink()
        patch = bytearray()
        for repo_id, root in task.repositories.items():
            patch.extend(('# repository_id: ' + repo_id + '\n').encode())
            patch.extend(git(root, 'diff', '--binary', '-U0', 'HEAD', '--'))
        Path(receipt['patch_path']).write_bytes(patch)
        result = finish_evidence(folder, receipt, 'binary')
        self.assertEqual(result['evidence_findings'], [])
        self.assertEqual(result['scope_findings'], [])
        self.assertEqual(result['patch_strip_components'], {'TOP26006_fw': 1, 'topeft': 1})
        self.assertEqual(Path(receipt['patch_path']).read_bytes(), patch)

    def test_finish_rejects_patch_path_escape_and_incompatible_kind(self):
        for ident, kind in (('escape', 'prompt_local'), ('kind', 'empty_no_changes')):
            with self.subTest(ident=ident):
                folder, receipt = self.direct_evidence(ident)
                receipt['contract']['patch_kind_expected'] = kind
                path = Path(receipt['patch_path'])
                data = b'diff --git a/../foreign b/../foreign\nnew file mode 100644\n--- /dev/null\n+++ b/../foreign\n@@ -0,0 +1 @@\n+wrong\n'
                path.write_bytes(data)
                result = finish_evidence(folder, receipt, ident)
                self.assertTrue(result['evidence_findings'])
                self.assertEqual(result['patch_kind'], 'unvalidated')
                self.assertEqual(path.read_bytes(), data)
                self.assertFalse((self.base / 'foreign').exists())

    def test_dirty_raw_baseline_avoids_attribute_conversion(self):
        # Git add would normalize this baseline because of .gitattributes.
        (self.repo / '.gitattributes').write_bytes(b'payload.txt text eol=lf\n')
        (self.repo / 'payload.txt').write_bytes(b'one\ntwo\nthree\n')
        self.run_git('add', '--', '.gitattributes', 'payload.txt')
        self.run_git('commit', '-qm', 'test: attribute fixture')
        (self.repo / 'payload.txt').write_bytes(b'one\r\ntwo\r\nthree\r\n')
        # Force a tracked dirty baseline even if Git treats CRLF as equivalent.
        (self.repo / 'CPC.md').write_bytes((self.repo / 'CPC.md').read_bytes() + b'\nforeign\n')
        prompt = self.contract('raw', True).replace('heavy_command_permissions:',
            'dirty_worktree_policy: allow_declared_preexisting_changes\nheavy_command_permissions:')
        task = self.b.inbox.task('raw', prompt)
        folder = self.b.root / 'raw'
        folder.mkdir()
        (folder / 'prompt.txt').write_text(prompt)
        for name in ('result.txt', 'events.jsonl', 'stderr.log'):
            (folder / name).write_bytes(b'fixture transport')
        receipt = begin_evidence(folder, task.admit('raw', prompt), 'raw')
        (self.repo / 'payload.txt').write_bytes(b'one\r\nchanged\r\nthree\r\n')
        result = finish_evidence(folder, receipt, 'raw')
        self.assertEqual(result['evidence_findings'], [])
        self.assertEqual(result['patch_producer'], 'host_measured_task_delta')
        self.assertIn(b'changed\r\n', Path(receipt['patch_path']).read_bytes())
        self.assertEqual(result['patch_strip_components']['TOP26006_fw'], 2)
        trees = result['patch_consumer_checks']['TOP26006_fw']
        self.assertEqual(trees['measured_result_tree'], trees['supplied_result_tree'])
        self.assertNotEqual(trees['baseline_tree'], trees['measured_result_tree'])

    def test_default_custom_evidence_roots_and_mode_mapping_boundaries(self):
        default = self.b.inbox.task('paths', self.contract('paths'))
        self.assertEqual(default.evidence_root, str(self.evidence))
        custom = self.repo / 'custom_diagnostics'
        custom.mkdir()
        for raw in (str(custom), 'custom_diagnostics'):
            prompt = self.contract('paths').replace('heavy_command_permissions:',
                'evidence_root: ' + raw + '\nheavy_command_permissions:')
            self.assertEqual(self.b.inbox.task('paths', prompt).evidence_root, str(custom))
        (self.repo / 'alias').symlink_to(custom, target_is_directory=True)
        for raw in ('../evidence', str(self.repo / 'alias'), str(self.repo / 'alias' / 'child')):
            prompt = self.contract('paths').replace('heavy_command_permissions:',
                'evidence_root: ' + raw + '\nheavy_command_permissions:')
            with self.assertRaises((ValueError, FileNotFoundError)):
                self.b.inbox.task('paths', prompt)
        prompt = self.contract('custom').replace('heavy_command_permissions:',
            'evidence_root: ' + str(custom) + '\nheavy_command_permissions:')
        (custom / 'custom').mkdir()
        self.b.submit('custom', prompt)
        receipt = self.finish('custom')
        self.assertEqual(receipt['state'], 'COMPLETED', receipt)
        self.assertEqual(receipt['evidence_directory'], str(custom / 'custom_rerun_001'))
        retain_fixture_evidence(self.b, 'custom', self._testMethodName)
        for value in ('ultra', 'invented'):
            prompt = self.contract('modes').replace('heavy_command_permissions:',
                'codex_cli_mode: ' + value + '\nheavy_command_permissions:')
            with self.assertRaisesRegex(ValueError, 'UNSUPPORTED_CODEX_CLI_MODE'):
                self.b.inbox.task('modes', prompt)

    def test_multiple_repositories_profiles_and_exact_stage_grants(self):
        second = self.base / 'consumer'
        subprocess.run(['git', 'clone', '-q', '--no-hardlinks', str(self.repo), str(second)], check=True)
        prompt = self.contract('profiles').replace(
            '  TOP26006_fw: ' + str(self.repo),
            '  TOP26006_fw: ' + str(self.repo) + '\n  topeft: ' + str(second))
        prompt = prompt.replace('gpt-6.1-sol', 'gpt-6-astra').replace('reasoning_level: high', 'reasoning_level: medium')
        task = self.b.inbox.task('profiles', prompt)
        self.assertEqual(set(task.repositories), {'TOP26006_fw', 'topeft'})
        self.assertEqual((task.model, task.reasoning), ('gpt-6-astra', 'medium'))
        self.assertIn('governance/modules/topeft.md', task.dependencies)
        workflow = self.contract('flow', coding=True).replace('prompt_mode: coding', 'prompt_mode: orchestrated_workflow')
        workflow = workflow.replace('branch_policy: continue_existing_branch\ntarget_branch: fixture_work\nheavy_command_permissions:\n  network_access: no\n  storage_writes: no', '''workflow_goal: local fixture
workflow_stop_policy: stop_on_failed_gate_or_new_decision_boundary
workflow_stage_ledger_path: task_owned_ledger.md
workflow_effect_envelope:
  network_access: yes
  allowed_to_modify:
    - TOP26006_fw:payload.txt
workflow_stages:
  - stage_id: inspect
    stage_mode: investigation_only
    stage_goal: inspect local source
    stage_branch_policy: read_only_current_branch
    stage_effect_permissions: {}
    stage_inputs: selected source
    stage_acceptance_gate: source observed
    stage_outputs: observed source
    stage_failure_behavior: stop
  - stage_id: edit
    stage_mode: coding
    stage_goal: edit selected payload
    stage_branch_policy: continue_existing_branch
    target_branch: fixture_work
    stage_effect_permissions:
      network_access: no
      allowed_to_modify:
        - TOP26006_fw:payload.txt
    stage_inputs: prior observations
    stage_acceptance_gate: exact change
    stage_outputs: patch
    stage_failure_behavior: stop''')
        task = self.b.inbox.task('flow', workflow)
        self.assertFalse(task.network)  # Envelope yes did not grant network.
        self.assertEqual(task.grants[0], {})
        self.assertEqual(task.fields['workflow_stages'][1]['stage_effect_permissions']['network_access'], 'no')
        self.assertEqual(task.content.encode(), workflow.encode())
        args = self.b.command(self.base / 'work', task)
        self.assertIn('sandbox_workspace_write.network_access=false', args)
        self.b.submit('flow', workflow)
        self.assertEqual(self.finish('flow')['state'], 'COMPLETED')
        with self.b.db() as db:
            receipt = json.loads(db.execute('SELECT receipt FROM tasks WHERE id=?', ('flow',)).fetchone()[0])
        self.assertEqual(receipt['contract'], task.fields)
        self.assertEqual((self.b.root / 'flow/received.bin').read_bytes(), workflow.encode())
        retain_fixture_evidence(self.b, 'flow', self._testMethodName)

    def test_fail_closed_shapes_and_upload_identity(self):
        prompt = self.contract('bad')
        variants = [prompt.replace('prompt_mode: investigation_only', 'prompt_mode: mystery'),
                    prompt.replace('prompt_mode: investigation_only', 'prompt_mode: tracked_write'),
                    prompt.replace('gpt-6.1-sol', 'unknown'),
                    prompt.replace('network_access: no', 'network_access: maybe'),
                    prompt.replace('network_access: no', 'network_access: no\n  network_access: yes'),
                    prompt.replace('read_only:\n  - TOP26006_fw governance', 'read_only: &a [x]'),
                    prompt.replace('TOP26006_fw: ' + str(self.repo), 'GridpackGeneration: ' + str(self.repo)),
                    prompt.replace('workspace_root: ' + str(self.repo), 'workspace_root: .'),
                    prompt.replace('reasoning_level: high', 'reasoning_level: high\nrequired_profile_agreement_evidence: exact runtime model'),
                    prompt.replace('reasoning_level: high', 'reasoning_level: high\nmodel_profile:\n  model: gpt-6-astra\n  reasoning_effort: high')]
        for value in variants:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.b.submit('bad', value)
        with self.b.db() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM tasks').fetchone()[0], 0)
        self.b.prompt_upload('up', 3, hashlib.sha256(b'abc').hexdigest())
        with self.assertRaisesRegex(ValueError, 'ID_CONFLICT'):
            self.b.prompt_upload('up', 3, hashlib.sha256(b'xyz').hexdigest())
        with self.assertRaisesRegex(ValueError, 'INCOMPLETE'):
            self.b.submit_uploaded_task('up')
        self.b.prompt_chunk('up', 0, base64.b64encode(b'abc').decode())
        with self.assertRaisesRegex(ValueError, 'CHUNK_CONFLICT'):
            self.b.prompt_chunk('up', 0, base64.b64encode(b'xyz').decode())
        invalid_utf8 = b'\xff\xfe'
        self.b.prompt_upload('utf8', 2, hashlib.sha256(invalid_utf8).hexdigest())
        self.b.prompt_chunk('utf8', 0, base64.b64encode(invalid_utf8).decode())
        with self.assertRaisesRegex(ValueError, 'STRICT_UTF8'):
            self.b.submit_uploaded_task('utf8')
        for size in (0, bridge.MAX_PROMPT + 1):
            with self.assertRaisesRegex(ValueError, 'INVALID_UPLOAD_SIZE'):
                self.b.prompt_upload('oversize', size, '0' * 64)

    def test_non_file_action_modes_retain_empty_local_write_scope(self):
        for mode in ('pr_publication', 'production_execution', 'branch_maintenance_only', 'integration_only'):
            prompt = self.contract('action').replace('prompt_mode: investigation_only', 'prompt_mode: ' + mode)
            if mode == 'production_execution':
                prompt = prompt.replace('heavy_command_permissions:', 'execution_owner: codex\nheavy_command_permissions:')
            task = self.b.inbox.task('action', prompt)
            self.assertEqual(task.fields['allowed_to_modify'], [])
            self.assertEqual(task.fields['prompt_mode'], mode)
            self.assertEqual(task.content, prompt)

    def test_dirty_baseline_patch_excludes_preserved_foreign_changes(self):
        # A declared dirty policy changes baseline comparison, never adopts dirt.
        (self.repo / 'CPC.md').write_bytes((self.repo / 'CPC.md').read_bytes() + b'\nforeign marker\n')
        foreign_before = (self.repo / 'CPC.md').read_bytes()
        prompt = self.contract('dirty', coding=True).replace(
            'heavy_command_permissions:', 'dirty_worktree_policy: allow_declared_preexisting_changes\nheavy_command_permissions:')
        self.b.submit('dirty', prompt)
        receipt = self.finish('dirty')
        self.assertEqual(receipt['state'], 'COMPLETED', receipt)
        patch = Path(receipt['patch_path']).read_bytes()
        self.assertIn(b'payload.txt', patch)
        self.assertNotIn(b'CPC.md', patch)
        self.assertEqual((self.repo / 'CPC.md').read_bytes(), foreign_before)
        self.assertEqual(receipt['patch_strip_components']['TOP26006_fw'], 2)
        self.run_git('apply', '--reverse', '--check', '-p2', receipt['patch_path'])
        retain_fixture_evidence(self.b, 'dirty', self._testMethodName)

    def test_streaming_binary_artifact_beyond_old_log_cap_and_special_file_refusal(self):
        folder = self.base / 'streaming'
        folder.mkdir()
        source = folder / 'large.bin'
        block = bytes(range(256)) * 4096
        with source.open('xb') as stream:
            for _ in range(17):
                stream.write(block)
            stream.write('雪'.encode())
        row = freeze_artifacts(folder, [('large.bin', source)])[0]
        self.assertEqual(row['size_bytes'], 17 * len(block) + 3)
        page = artifact_page(folder, row, row['size_bytes'] - 7, 32768)
        self.assertEqual(base64.b64decode(page['data']), block[-4:] + '雪'.encode())
        self.assertFalse(page['has_more'])
        fifo = folder / 'fifo'
        os.mkfifo(fifo)
        with self.assertRaisesRegex(ValueError, 'REGULAR_FILE'):
            freeze_artifacts(folder, [('fifo', fifo)])

    def test_artifact_tamper_and_traversal_rejected(self):
        self.b.submit('safe', self.contract('safe'))
        self.assertEqual(self.finish('safe')['state'], 'COMPLETED')
        with self.assertRaisesRegex(ValueError, 'UNKNOWN_TASK_ARTIFACT'):
            self.b.task_artifact('safe', '../../auth.json')
        with self.assertRaises(ValueError):
            self.b.task_artifact('../safe', '0000')
        row = self.b.task_artifacts('safe')['artifacts'][0]
        (self.b.root / 'safe/artifacts' / row['artifact_id']).write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError, 'ARTIFACT_CHANGED'):
            self.b.task_artifact('safe', row['artifact_id'])

    def test_master_binding_and_manual_production_refusal(self):
        prompt = self.contract('manual', coding=True).replace('prompt_mode: coding', 'prompt_mode: production_execution')
        prompt = prompt.replace('```\nSYNTHETIC', 'execution_owner: user\n```\nSYNTHETIC')
        with self.assertRaisesRegex(ValueError, 'OWNER_MANUAL_PRODUCTION_BOUNDARY'):
            self.b.submit('manual', prompt)
        (self.repo / 'AGENTS.md').write_text('candidate governance must not self-authorize')
        self.run_git('add', 'AGENTS.md')
        self.run_git('commit', '-qm', 'test: candidate-only policy')
        task = self.b.inbox.task('candidate', self.contract('candidate'))
        self.assertEqual(task.master, git(self.repo, 'rev-parse', 'master').decode().strip())

    @unittest.skipUnless(os.environ.get('GLADOS_BRIDGE_TEST_NODE_MODULES'),
                         'set GLADOS_BRIDGE_TEST_NODE_MODULES to an existing SDK installation; never install for tests')
    def test_real_mcp_stdio_catalog_upload_and_separate_client_retrieval(self):
        server_dir = self.base / 'adapter'
        server_dir.mkdir()
        source = Path(__file__).parent
        for path in source.iterdir():
            if path.suffix in ('.py', '.mjs', '.json', '.sh') and path.is_file():
                shutil.copyfile(path, server_dir / path.name)
                if path.suffix == '.sh':
                    (server_dir / path.name).chmod(0o700)
        shutil.copyfile(Path(__file__).resolve().parents[1] / 'resolve_local_profile.py', server_dir / 'resolve_local_profile.py')
        (server_dir / 'node_modules').symlink_to(Path(os.environ['GLADOS_BRIDGE_TEST_NODE_MODULES']).resolve(), target_is_directory=True)
        fixture = self.base / 'mcp_fixture.json'
        fixture.write_text(json.dumps({
            'repo': str(self.repo), 'profile': str(self.profile), 'state': str(self.b.root),
            'python': sys.executable, 'wrapper': str(self.wrapper), 'codex': str(self.fake),
            'server': str(server_dir / 'server.mjs'), 'prompt': self.contract('mcp_fixture'),
        }))
        result = subprocess.run(['node', str(server_dir / 'test_mcp_stdio.mjs'), str(fixture)],
                                capture_output=True, text=True, timeout=300)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        print(result.stdout.strip())
        retain_fixture_evidence(self.b, 'mcp_fixture', self._testMethodName)


if __name__ == '__main__':
    unittest.main(verbosity=2)
