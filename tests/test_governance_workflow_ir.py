"""Adversarial tests for canonical acquisition and produced-result relations."""
from copy import deepcopy
import subprocess

import pytest

from tools.governance_workflow_ir import Policy_source_binding, Result_graph


def git(path, *args):
    return subprocess.check_output(['git', '-C', str(path), *args], stderr=subprocess.PIPE)


def test_canonical_policy_ignores_checkout_and_feature_bytes(tmp_path):
    git(tmp_path, 'init', '--initial-branch=master')
    (tmp_path/'AGENTS.md').write_text('canonical policy')
    git(tmp_path, 'add', '--', 'AGENTS.md')
    git(tmp_path, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
        'commit', '-m', 'Bind fixture policy')
    binding = Policy_source_binding(tmp_path)
    git(tmp_path, 'switch', '-c', 'candidate')
    (tmp_path/'AGENTS.md').write_text('candidate policy')
    assert binding.read('AGENTS.md') == b'canonical policy'
    binding.revalidate()
    assert binding.receipt()['ref'] == 'refs/heads/master'


def test_material_policy_change_is_detected_but_unrelated_master_change_is_allowed(tmp_path):
    git(tmp_path, 'init', '--initial-branch=master')
    (tmp_path/'policy').write_text('one')
    git(tmp_path, 'add', '--', 'policy')
    def commit():
        git(tmp_path, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
            'commit', '--allow-empty', '-m', 'Policy fixture state')
    commit()
    binding = Policy_source_binding(tmp_path)
    assert binding.read('policy') == b'one'
    commit()
    binding.revalidate()
    (tmp_path/'policy').write_text('two')
    git(tmp_path, 'add', '--', 'policy')
    commit()
    with pytest.raises(ValueError, match='decision-material'):
        binding.revalidate()


def test_exact_validation_relation_and_dependencies_share_result_facts():
    stages=[{'stage_id': 'a', 'stage_inputs': [], 'stage_outputs': ['head']},
            {'stage_id': 'b', 'stage_inputs': [], 'stage_outputs': ['head']},
            {'stage_id': 'validate', 'stage_inputs': ['stage:a:head','stage:b:head'],
             'stage_outputs': ['evidence'], 'validation_contract': {
                 'predicate': 'contract equality and protocol membership',
                 'cases': [{'provider':'stage:a:head','consumer':'stage:b:head','expected':'PASS'}],
                 'matrix':['PASS']}}]
    graph=Result_graph.from_stages(stages)
    assert graph.predecessors('validate') == {'a','b'}
    assert graph.stages[-1].validation.projection() == stages[-1]['validation_contract']
    for damage in ('missing_input','future','duplicate','matrix'):
        broken=deepcopy(stages)
        if damage=='missing_input': broken[-1]['stage_inputs'].pop()
        elif damage=='future': broken[0]['stage_inputs']=['stage:b:head']
        elif damage=='duplicate': broken[1]['stage_id']='a'
        else: broken[-1]['validation_contract']['matrix']=['FAIL_EXPECTED']
        with pytest.raises(ValueError): Result_graph.from_stages(broken)


@pytest.mark.parametrize('content', ['', 'bounded fixture\n', 'Unicode: café\n'])
def test_literal_artifact_roundtrip_and_readback(content):
    from tools.governance_workflow_ir import Artifact_spec
    from test_governance_workflow_compiler import synthetic_artifact
    record=synthetic_artifact('contract.json', content)
    spec=Artifact_spec.from_record('contract.json',record,record['review_evidence'])
    assert spec.projection()==record
    assert spec.literal_bytes()==content.encode('utf-8')
    spec.verify_bytes(spec.literal_bytes())
    with pytest.raises(ValueError,match='digest mismatch'): spec.verify_bytes(b'corrupt'+spec.literal_bytes())


def test_frozen_and_new_acquired_artifact_identity_compatibility():
    from tools.governance_workflow_ir import Artifact_spec
    legacy={'sha256':'a'*64,'locator':'accepted/postimages/doc.md'}
    old=Artifact_spec.from_record('doc.md',legacy,'accepted review')
    new=Artifact_spec.from_record('doc.md',old.projection(),'accepted review')
    assert old==new
    with pytest.raises(ValueError,match='separately authorized'): new.literal_bytes()


@pytest.mark.parametrize('path,locator', [('a/../b','accepted/file'),('/absolute','accepted/file'),
    ('a','../escape'),('a','a//b'),('a','https://user:secret@example/file'),('a','a/./b'),('a','a\\b')])
def test_unsafe_artifact_paths_and_locators(path,locator):
    from tools.governance_workflow_ir import Artifact_spec
    with pytest.raises(ValueError):
        Artifact_spec.from_record(path,{'sha256':'a'*64,'locator':locator},'review')


def test_artifact_scope_and_source_ambiguity():
    from tools.governance_workflow_ir import artifact_specs, Artifact_spec
    from test_governance_workflow_compiler import synthetic_artifact
    record=synthetic_artifact('a','content')
    with pytest.raises(ValueError): artifact_specs({'a':record},['b'],record['review_evidence'])
    with pytest.raises(ValueError): artifact_specs({'a':record},['a','a'],record['review_evidence'])
    record['source']['locator']='accepted/a'
    with pytest.raises(ValueError): Artifact_spec.from_record('a',record,record['review_evidence'])
