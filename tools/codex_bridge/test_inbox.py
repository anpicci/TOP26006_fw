import concurrent.futures
import hashlib
import json
import time
import unittest
from pathlib import Path
import subprocess
import sys
import test_repository_task as fixtures
from repository_task import ReadOnlyInbox
import bridge


class InboxTests(unittest.TestCase):
    run_git = fixtures.RepositoryTests.run_git
    bind = fixtures.RepositoryTests.bind

    def setUp(self):
        fixtures.RepositoryTests.setUp(self)
        self.profile = self.base / 'inbox.json'
        self.profile.write_text(json.dumps({'governance_dependencies': self.deps,
                                           'model': 'gpt-6.1-sol', 'reasoning': 'high'}))
        self.b = bridge.Bridge(self.base/'state', str(self.fake), wrapper=str(self.wrapper),
            inbox=ReadOnlyInbox(self.profile, self.repo, self.base/'state'))

    def tearDown(self):
        self.tmp.cleanup()

    def contract(self, request_id, question='inspect selected source'):
        head = self.prompt.read_text().replace('prompt_id: repo_probe', 'prompt_id: '+request_id)
        lines = ('short_title: selected_readback\n'
                 'decision_question: '+question+'\n'
                 'model_selection_rationale: fixed admitted profile\n'
                 'allowed_to_modify: []\n'
                 'repo_locations:\n  TOP26006_fw: '+str(self.repo)+'\n'
                 'read_only:\n  - TOP26006_fw selected source\n'
                 'patch_kind_expected: empty_no_changes\n'
                 'final_chat_deliverable: report captured by host\n'
                 'evidence_requirements: observed source and limits\n'
                 'classification_rules: native rules\n'
                 'anti_self_certification_rules: no acceptance from completion\n'
                 'evidence_validation_method: compare actual source\n'
                 'heavy_command_permissions:\n  network_access: no\n  storage_writes: no\n')
        return head[:-4] + lines + '```\n\nInspect only authorized source with explicit context.\n'

    def finish(self, request_id):
        end=time.monotonic()+90
        while time.monotonic()<end:
            r=self.b.status(request_id)
            if r['state'] not in ('STARTING','RUNNING'):
                return r
            time.sleep(.03)
        self.fail('worker did not terminate')

    def test_two_distinct_contracts_same_service_and_profile(self):
        for ident in ('first','second'):
            prompt=self.contract(ident, 'question '+ident)
            r=self.b.submit(ident,prompt)
            self.assertFalse(r['duplicate_request'])
            r=self.finish(ident)
            self.assertEqual(r['state'],'COMPLETED')
            self.assertEqual(r['model_profile'],{'model':'gpt-6.1-sol','reasoning_effort':'high'})
            self.assertEqual(r['prompt_sha256'],hashlib.sha256(prompt.encode()).hexdigest())
            self.assertEqual((self.b.root/ident/'prompt.txt').read_text(),prompt)
            self.assertTrue(r['repository_preserved'])
        self.assertNotEqual(self.b.status('first')['prompt_sha256'],self.b.status('second')['prompt_sha256'])

    def test_duplicate_after_restart_does_not_relaunch(self):
        p=self.contract('same')
        self.b.submit('same',p);self.finish('same')
        self.b=bridge.Bridge(self.b.root,str(self.fake),wrapper=str(self.wrapper),
            inbox=ReadOnlyInbox(self.profile,self.repo,self.b.root))
        self.assertTrue(self.b.submit('same',p)['duplicate_request'])
        self.assertEqual((self.b.root/'same/invocations.txt').read_text(),'one\n')
        with self.assertRaisesRegex(ValueError,'ID_CONFLICT'):
            self.b.submit('same',p+'changed')

    def test_concurrent_duplicate_one_execution(self):
        p=self.contract('race')
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as e:
            r=list(e.map(lambda _:self.b.submit('race',p),range(4)))
        self.assertEqual(sum(not x['duplicate_request'] for x in r),1)
        self.finish('race')
        self.assertEqual((self.b.root/'race/invocations.txt').read_text(),'one\n')

    def test_invalid_contracts_create_no_task(self):
        p=self.contract('invalid')
        variants=[
            (p.replace('investigation_only','coding'),'READ_ONLY'),
            (p.replace('allowed_to_modify: []','allowed_to_modify: [AGENTS.md]'),'READ_ONLY'),
            (p.replace('storage_writes: no','storage_writes: yes'),'DENIAL'),
            (p.replace('storage_writes: no','storage_writes: no\n  storage_writes: yes'),'DENIAL'),
            (p.replace('gpt-6.1-sol','gpt-6-astra'),'READ_ONLY'),
            (p.replace('reasoning_level: high','reasoning_level: max'),'READ_ONLY'),
            (p.replace('prompt_id: invalid','prompt_id: wrong'),'MISMATCH'),
            (p.replace('allowed_to_modify: []','allowed_to_modify: []\nallowed_to_modify: []'),'LINT'),
            (p.replace('repo_locations:\n  TOP26006_fw: '+str(self.repo),
                       'repo_locations:\n  OTHER: '+str(self.repo)),'READ_ONLY'),
        ]
        for q,message in variants:
            with self.subTest(message=message):
                with self.assertRaisesRegex(ValueError,message):self.b.submit('invalid',q)
                self.assertFalse((self.b.root/'invalid').exists())
        with self.b.db() as db:self.assertEqual(db.execute('SELECT count(*) FROM tasks').fetchone()[0],0)

    def test_material_policy_change_blocks_new_but_not_old_receipt(self):
        p=self.contract('prior')
        self.b.submit('prior',p);self.finish('prior')
        (self.repo/'AGENTS.md').write_text('material policy update')
        self.run_git('add','AGENTS.md');self.run_git('commit','-qm','test: policy drift')
        with self.assertRaisesRegex(ValueError,'GOVERNANCE_DELTA'):
            self.b.submit('next',self.contract('next'))
        self.assertTrue(self.b.submit('prior',p)['duplicate_request'])
        self.assertEqual(self.b.status('prior')['state'],'COMPLETED')

    def test_unrelated_master_commit_keeps_intake_usable(self):
        self.run_git('commit','--allow-empty','-qm','test: unrelated oid')
        self.b.submit('next',self.contract('next'))
        self.assertEqual(self.finish('next')['state'],'COMPLETED')

    def test_unknown_state_blocks_new_contract(self):
        with self.b.db() as db:
            db.execute('INSERT INTO tasks VALUES (?,?,?,?,?,?,?)',
                       ('lost','hash','p','OUTCOME_UNKNOWN',0,0,'{}'))
        with self.assertRaisesRegex(ValueError,'BUSY_OR_UNKNOWN'):
            self.b.submit('next',self.contract('next'))

    def test_cli_receipt_reads_survive_broken_profile(self):
        p=self.contract('prior');self.b.submit('prior',p);self.finish('prior')
        self.profile.write_text('broken')
        cmd=[str(self.wrapper),sys.executable,'-S','-B',str(Path(bridge.__file__).resolve()),'--state',str(self.b.root),
             '--read-only-inbox',str(self.profile),'--workspace',str(self.repo),
             '--command-wrapper',str(self.wrapper),'--rpc']
        for name in ('task_status','task_output'):
            r=subprocess.run(cmd,input=json.dumps({'method':name,'args':{'request_id':'prior'}}),
                             capture_output=True,text=True,check=True)
            self.assertTrue(json.loads(r.stdout)['ok'])


if __name__=='__main__':unittest.main(verbosity=2)
