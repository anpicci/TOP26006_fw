import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

import bridge
from repository_task import RepositoryTask, VALIDATOR, governance, git
from test_support import write_fake


FAKE_REPO_CODEX = '''#!/usr/bin/env python3
import json,os,pathlib,sys,time
if '--version' in sys.argv:
 print('codex-cli 0.167.0');sys.exit(0)
if '--help' in sys.argv:
 print('--ignore-user-config --ephemeral --json --sandbox --output-last-message --skip-git-repo-check');sys.exit(0)
prompt=sys.stdin.read()
output=pathlib.Path(sys.argv[sys.argv.index('--output-last-message')+1])
with (output.parent/'invocations.txt').open('a') as f:f.write('one\\n')
assert '--skip-git-repo-check' not in sys.argv
assert sys.argv[sys.argv.index('--sandbox')+1]=='read-only'
assert sys.argv[sys.argv.index('--model')+1]=='gpt-6.1-sol'
assert 'model_reasoning_effort="high"' in sys.argv
assert 'CONTROL_PLANE_API_KEY' not in os.environ
assert 'OPENAI_API_KEY' not in os.environ
assert 'CODEX_API_KEY' not in os.environ
print(json.dumps({'type':'turn.started'}),flush=True)
time.sleep(0.15)
if 'SYNTHETIC_MUTATION' in prompt:pathlib.Path('AGENTS.md').write_text('changed')
output.write_text('# Synthetic report\\nLocal metadata inspected by test double, not real Codex.\\n')
print(json.dumps({'type':'turn.completed'}),flush=True)
'''


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.repo = self.base/'repo'
        self.repo.mkdir()
        subprocess.run(['git','init','-q','-b','master',str(self.repo)],check=True)
        self.run_git('config','user.email','fixture@example.invalid')
        self.run_git('config','user.name','Fixture')
        self.run_git('remote','add','origin','https://github.com/anpicci/TOP26006_fw.git')
        fixture = Path(os.environ.get('GOVERNANCE_FIXTURE_ROOT', Path(__file__).resolve().parents[2]))
        target = self.repo/VALIDATOR
        target.parent.mkdir(parents=True)
        target.write_bytes((fixture/VALIDATOR).read_bytes())
        (self.repo/'AGENTS.md').write_text('Synthetic governance fixture.\n')
        self.run_git('add','AGENTS.md',VALIDATOR)
        self.run_git('commit','-qm','test: initialize synthetic fixture')
        self.prompt = self.base/'CODEX_PROMPT_TEST.md'
        self.prompt.write_text('```yaml\nprompt_id: repo_probe\nprompt_mode: investigation_only\n'
            'branch_policy: read_only_current_branch\nvalidation_ceiling: static_inspection_only\n'
            'delegation_policy: forbidden\npreferred_codex_model: gpt-6.1-sol\n'
            'reasoning_level: high\nworkspace_root: '+str(self.repo)+'\n```\n')
        self.bind()
        self.fake = self.base/'codex'
        write_fake(self.fake, FAKE_REPO_CODEX)
        self.wrapper = self.base/'wrapper'
        self.wrapper.write_text('#!/bin/sh\nprintf invoked >> "'+str(self.base/'wrapper_used')+'"\nexec "$@"\n')
        self.wrapper.chmod(0o700)

    def run_git(self,*args):
        return subprocess.run(['git','-C',str(self.repo),*args],check=True,capture_output=True).stdout

    def bind(self):
        self.deps={p:self.run_git('rev-parse','master:'+p).decode().strip() for p in (VALIDATOR,'AGENTS.md')}
        self.prompt.with_suffix('.binding.json').write_text(json.dumps({
            'prompt_sha256':hashlib.sha256(self.prompt.read_bytes()).hexdigest(),
            'governance_dependencies':self.deps}))

    def make_bridge(self):
        return bridge.Bridge(self.base/'state',str(self.fake),
            RepositoryTask(self.prompt,self.repo),str(self.wrapper))

    def finish(self,b):
        deadline=time.monotonic()+90
        while time.monotonic()<deadline:
            r=b.status('repo_probe')
            if r['state'] not in ('STARTING','RUNNING'):return r
            time.sleep(.03)
        self.fail('worker did not terminate')

    def tearDown(self): self.tmp.cleanup()

    def test_bound_task_profile_wrapper_and_evidence(self):
        b=self.make_bridge()
        before=b.task.admit('repo_probe',self.prompt.read_text())['repository_before']
        submitted=b.submit('repo_probe',self.prompt.read_text())
        argv=submitted['argv']
        self.assertIn('--enable',argv)
        self.assertIn('shell_snapshot',[argv[i+1] for i,x in enumerate(argv[:-1]) if x=='--disable'])
        self.assertIn('allow_login_shell=false',argv)
        self.assertNotIn('--ignore-rules',argv)
        self.assertNotIn('shell_tool',[argv[i+1] for i,x in enumerate(argv[:-1]) if x=='--disable'])
        r=self.finish(b)
        self.assertEqual(r['state'],'COMPLETED')
        self.assertTrue(r['repository_preserved'])
        self.assertEqual(r['repository_after'],before)
        self.assertEqual(r['model_profile'],{'model':'gpt-6.1-sol','reasoning_effort':'high'})
        self.assertEqual(Path(r['patch_path']).read_bytes(),b'')
        self.assertEqual(hashlib.sha256(Path(r['report_path']).read_bytes()).hexdigest(),r['report_sha256'])
        self.assertEqual((self.base/'wrapper_used').read_text(),'invoked')
        self.assertTrue(b.submit('repo_probe',self.prompt.read_text())['duplicate_request'])
        self.assertEqual((b.root/'repo_probe/invocations.txt').read_text(),'one\n')

    def test_modified_prompt_rejected_without_reservation(self):
        b=self.make_bridge()
        with self.assertRaisesRegex(ValueError,'TASK_NOT_BOUND'):
            b.submit('repo_probe',self.prompt.read_text()+'extra')
        with b.db() as db:self.assertEqual(db.execute('SELECT count(*) FROM tasks').fetchone()[0],0)

    def test_different_id_cannot_reexecute_contract(self):
        b=self.make_bridge()
        with self.assertRaisesRegex(ValueError,'TASK_NOT_BOUND'):b.submit('other',self.prompt.read_text())

    def test_local_prompt_tampering_rejected(self):
        self.prompt.write_text(self.prompt.read_text()+'changed')
        with self.assertRaisesRegex(ValueError,'PROMPT_CHANGED'):self.make_bridge()

    def test_unrelated_master_commit_keeps_dependencies_valid(self):
        old=self.run_git('rev-parse','master')
        self.run_git('commit','--allow-empty','-qm','test: unrelated change')
        task=RepositoryTask(self.prompt,self.repo)
        self.assertNotEqual(task.master,old.decode().strip())

    def test_governance_change_blocks_new_dispatch(self):
        b=self.make_bridge()
        (self.repo/'AGENTS.md').write_text('different governance')
        self.run_git('add','AGENTS.md');self.run_git('commit','-qm','test: governance changed')
        with self.assertRaisesRegex(ValueError,'GOVERNANCE_DELTA'):b.submit('repo_probe',self.prompt.read_text())

    def test_wrong_repository_rejected(self):
        self.run_git('remote','set-url','origin','https://github.com/example/other.git')
        with self.assertRaisesRegex(ValueError,'REPOSITORY_IDENTITY'):self.make_bridge()

    def test_dirty_state_preserved_without_adoption(self):
        (self.repo/'AGENTS.md').write_text('foreign uncommitted changes')
        b=self.make_bridge();b.submit('repo_probe',self.prompt.read_text());r=self.finish(b)
        self.assertEqual(r['state'],'COMPLETED')
        self.assertTrue(r['repository_before']['tracked_dirty'])
        self.assertEqual((self.repo/'AGENTS.md').read_text(),'foreign uncommitted changes')

    def test_mutation_or_concurrent_drift_not_reported_as_preserved(self):
        self.prompt.write_text(self.prompt.read_text()+'SYNTHETIC_MUTATION\n');self.bind()
        b=self.make_bridge();b.submit('repo_probe',self.prompt.read_text());r=self.finish(b)
        self.assertEqual(r['state'],'FAILED');self.assertFalse(r['repository_preserved'])
        self.assertNotIn('patch_path',r)

    def test_receipts_accessible_when_current_binding_is_broken(self):
        b=self.make_bridge();b.submit('repo_probe',self.prompt.read_text());self.finish(b)
        self.prompt.write_text('broken')
        command=[str(self.wrapper),sys.executable,'-S','-B',str(Path(bridge.__file__).resolve()),'--state',str(b.root),
            '--read-only-prompt',str(self.prompt),'--workspace',str(self.repo),
            '--command-wrapper',str(self.wrapper),'--rpc']
        for method in ('task_status','task_output'):
            r=subprocess.run(command,input=json.dumps({'method':method,'args':{'request_id':'repo_probe'}}),
                             text=True,capture_output=True,check=True)
            self.assertTrue(json.loads(r.stdout)['ok'])


if __name__=='__main__': unittest.main(verbosity=2)
