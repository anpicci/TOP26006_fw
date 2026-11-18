import concurrent.futures
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest import mock
from types import SimpleNamespace
import subprocess
import bridge
from test_support import write_fake

FAKE = '''#!/usr/bin/env python3
import json,os,pathlib,sys,time
if '--version' in sys.argv:
 print('codex-cli 0.167.0');sys.exit(0)
if '--help' in sys.argv:
 print('--ignore-user-config --ephemeral --json --sandbox --output-last-message --skip-git-repo-check');sys.exit(0)
prompt=sys.stdin.read()
root=pathlib.Path.cwd().parent
with (root/'invocations.txt').open('a') as f:f.write('one\\n')
assert 'CONTROL_PLANE_API_KEY' not in os.environ
assert 'CODEX_API_KEY' not in os.environ
assert '--ignore-user-config' in sys.argv
assert sys.argv[sys.argv.index('--sandbox')+1]=='read-only'
print(json.dumps({'type':'turn.started'}),flush=True)
time.sleep(0.3)
if prompt=='fail': sys.exit(4)
pathlib.Path(sys.argv[sys.argv.index('--output-last-message')+1]).write_text('received:'+prompt)
if prompt!='missing_completion':print(json.dumps({'type':'turn.completed'}),flush=True)
'''


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.b = object.__new__(bridge.Bridge)
        self.b.codex = '/fixture/codex'
        self.b.inbox = SimpleNamespace(governed=True)
        self.help = ('--ignore-user-config --ephemeral --json --sandbox '
                     '--output-last-message --skip-git-repo-check --approve-for-me --add-dir')
        self.version = subprocess.CompletedProcess([], 0, 'codex-cli 0.167.0\n', '')

    def test_metadata_success_and_budgets(self):
        with mock.patch.object(bridge.subprocess, 'run', side_effect=[
                self.version, subprocess.CompletedProcess([], 0, self.help, '')]) as run:
            self.assertEqual(self.b.preflight(), 'codex-cli 0.167.0')
        self.assertEqual([call.args[0] for call in run.call_args_list],
                         [['/fixture/codex', '--version'], ['/fixture/codex', 'exec', '--help']])
        for call in run.call_args_list:
            self.assertEqual(call.kwargs['timeout'], 300)
            self.assertTrue(call.kwargs['capture_output'])
            self.assertTrue(call.kwargs['text'])

    def test_metadata_timeout_each_phase(self):
        for phase, args in [('version', ['--version']), ('help', ['exec', '--help'])]:
            with self.subTest(phase=phase):
                error = subprocess.TimeoutExpired(['/fixture/codex', *args], 300,
                                                  stderr=b'startup diagnostic\xff' + b'x' * 3000)
                effects = ([self.version] if phase == 'help' else []) + [error]
                with mock.patch.object(bridge.subprocess, 'run', side_effect=effects) as run:
                    with self.assertRaises(ValueError) as caught:
                        self.b.preflight()
                self.assertIs(caught.exception.__cause__, error)
                message = str(caught.exception)
                self.assertIn('phase=' + phase, message)
                self.assertIn('argv=' + json.dumps(['/fixture/codex', *args]), message)
                self.assertIn('timeout_seconds=300', message)
                self.assertIn('startup diagnostic', message)
                self.assertIn('[truncated]', message)
                self.assertNotIn('x' * 2048, message)
                self.assertEqual(run.call_count, len(effects))
                self.assertTrue(all(c.kwargs['timeout'] == 300 for c in run.call_args_list))

    def test_metadata_os_error_each_phase(self):
        for phase in ('version', 'help'):
            with self.subTest(phase=phase):
                error = FileNotFoundError(2, 'missing', '/fixture/codex')
                effects = ([self.version] if phase == 'help' else []) + [error]
                with mock.patch.object(bridge.subprocess, 'run', side_effect=effects):
                    with self.assertRaises(ValueError) as caught:
                        self.b.preflight()
                self.assertIs(caught.exception.__cause__, error)
                for text in ('phase=' + phase, 'argv=', 'errno=2', 'filename="/fixture/codex"'):
                    self.assertIn(text, str(caught.exception))

    def test_metadata_nonzero_each_phase(self):
        for phase in ('version', 'help'):
            with self.subTest(phase=phase):
                effects = ([self.version] if phase == 'help' else []) + [
                    subprocess.CompletedProcess([], 7, '', 'metadata failure\n' + 'z' * 3000)]
                with mock.patch.object(bridge.subprocess, 'run', side_effect=effects):
                    with self.assertRaises(ValueError) as caught:
                        self.b.preflight()
                for text in ('phase=' + phase, 'argv=', 'returncode=7', 'metadata failure', '[truncated]'):
                    self.assertIn(text, str(caught.exception))
                self.assertNotIn('z' * 2048, str(caught.exception))

    def test_metadata_accepts_changed_versions_with_required_capabilities(self):
        for version in ('codex-cli 0.167.0', 'codex-cli 0.167.2',
                        'codex-cli 0.168.0', 'codex-cli 1.0.0'):
            with self.subTest(version=version):
                with mock.patch.object(bridge.subprocess, 'run', side_effect=[
                        subprocess.CompletedProcess([], 0, version + '\n', ''),
                        subprocess.CompletedProcess([], 0, self.help, '')]):
                    self.assertEqual(self.b.preflight(), version)

    def test_metadata_missing_required_flag(self):
        for flag in self.help.split():
            with self.subTest(flag=flag):
                with mock.patch.object(bridge.subprocess, 'run', side_effect=[
                        subprocess.CompletedProcess([], 0, 'codex-cli 0.167.2\n', ''),
                        subprocess.CompletedProcess([], 0, self.help.replace(flag, ''), '')]):
                    with self.assertRaises(ValueError) as caught:
                        self.b.preflight()
                self.assertIn('does not support', str(caught.exception))
                self.assertIn(flag, str(caught.exception))


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.fake = self.root / 'codex'
        write_fake(self.fake, FAKE)
        self.b = bridge.Bridge(self.root / 'state', codex=str(self.fake))

    def tearDown(self):
        self.tmp.cleanup()

    def finish(self, request_id):
        end = time.monotonic() + 90
        while time.monotonic() < end:
            r = self.b.status(request_id)
            if r['state'] not in ('STARTING', 'RUNNING'):
                return r
            time.sleep(0.03)
        self.fail('worker did not finish')

    def test_exact_duplicate_survives_restart(self):
        self.b.submit('demo', 'plain text; $(not a shell)')
        self.b = bridge.Bridge(self.root / 'state', codex=str(self.fake))
        self.assertTrue(self.b.submit('demo', 'plain text; $(not a shell)')['duplicate_request'])
        self.assertEqual(self.finish('demo')['state'], 'COMPLETED')
        self.assertTrue(self.b.submit('demo', 'plain text; $(not a shell)')['duplicate_request'])
        self.assertEqual((self.b.root/'demo/invocations.txt').read_text(), 'one\n')

    def test_same_id_changed_content_rejected(self):
        self.b.submit('demo', 'a')
        with self.assertRaisesRegex(ValueError, 'ID_CONFLICT'):
            self.b.submit('demo', 'b')
        self.finish('demo')

    def test_concurrent_duplicate_single_execution(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
            receipts = list(ex.map(lambda _: self.b.submit('concurrent', 'a'), range(6)))
        self.assertEqual(sum(not r['duplicate_request'] for r in receipts), 1)
        self.finish('concurrent')
        self.assertEqual((self.b.root/'concurrent/invocations.txt').read_text(), 'one\n')

    def test_second_task_rejected_while_busy(self):
        self.b.submit('first', 'a')
        with self.assertRaisesRegex(ValueError, 'BUSY_OR_UNKNOWN'):
            self.b.submit('second', 'a')
        self.finish('first')

    def test_orphan_reservation_never_retried(self):
        with self.b.db() as db:
            db.execute('INSERT INTO tasks VALUES (?,?,?,?,?,?,?)', ('lost', 'hash', 'a', 'STARTING', 0, 0, '{}'))
        self.assertEqual(self.b.status('lost')['state'], 'OUTCOME_UNKNOWN')
        with self.assertRaisesRegex(ValueError, 'BUSY_OR_UNKNOWN'):
            self.b.submit('replacement', 'a')

    def test_cli_nonzero_preserved(self):
        self.b.submit('bad', 'fail')
        r = self.finish('bad')
        self.assertEqual((r['state'], r['returncode']), ('FAILED', 4))

    def test_zero_exit_without_completion_not_success(self):
        self.b.submit('incomplete', 'missing_completion')
        r = self.finish('incomplete')
        self.assertEqual((r['state'], r['returncode']), ('FAILED', 0))

    def test_pagination_and_path_rejection(self):
        for value in ('../escape', '/tmp/a', '', 'x'*65):
            with self.assertRaises(ValueError): self.b.submit(value, 'a')
        self.b.submit('page', 'abcdef')
        self.finish('page')
        r = self.b.output('page', limit=3)
        self.assertEqual((r['text'], r['next_offset'], r['has_more']), ('rec', 3, True))
        with self.assertRaises(ValueError):self.b.output('page', stream='../../auth.json')

    def test_secret_environment_not_forwarded(self):
        old = dict(os.environ)
        try:
            os.environ['CONTROL_PLANE_API_KEY'] = 'synthetic-test-key'
            os.environ['CODEX_API_KEY'] = 'synthetic-model-key'
            self.b.submit('env', 'a')
            self.assertEqual(self.finish('env')['state'], 'COMPLETED')
        finally:
            os.environ.clear();os.environ.update(old)

    def test_timeout_kills_only_owned_process(self):
        folder = self.b.root/'timeout'
        folder.mkdir();(folder/'work').mkdir()
        with self.b.db() as db:
            db.execute('INSERT INTO tasks VALUES (?,?,?,?,?,?,?)', ('timeout', 'hash', 'a', 'STARTING', 0, 0,
                       json.dumps({'argv':self.b.command(folder/'work'), 'cwd':str(folder/'work')})))
        old = bridge.TIMEOUT
        bridge.TIMEOUT = 0.05
        try:self.b.worker('timeout', self.b.lock('busy.lock'))
        finally:bridge.TIMEOUT = old
        self.assertEqual(self.b.status('timeout')['state'], 'TIMED_OUT')


if __name__ == '__main__':
    unittest.main(verbosity=2)
