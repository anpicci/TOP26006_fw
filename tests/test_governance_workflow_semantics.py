"""Challenge generated mechanics independently of planner recomputation."""
from copy import deepcopy

import pytest
import yaml

from tools import governance_workflow_compiler as compiler
from test_governance_workflow_compiler import (
    run, policy_repository, policy_source, LIFECYCLE, lifecycle_data, ordered_resource_fixture, prompt_yaml,
    SIMPLE, base_data, MULTI_REPO, multi_repo_data)


@pytest.mark.parametrize('damage',['force_remove','wrong_ref','wrong_lease','missing_preserve','readback'])
def test_independent_verifier_rejects_planner_shared_defect(monkeypatch, damage):
    original=compiler._plan_stages
    def damaged(*args):
        stages=original(*args)
        if damage=='force_remove': stages[1]['safety_critical_argv'].insert(-1,'--force')
        elif damage=='wrong_ref': stages[-1]['safety_critical_argv'][-2]='refs/heads/foreign'
        elif damage=='wrong_lease': stages[-1]['safety_critical_argv'][-1]='unobserved'
        elif damage=='missing_preserve': stages[0]['stage_goal']='inspect'
        else: stages[2]['required_readback']['registration_absent']='/foreign'
        return stages
    monkeypatch.setattr(compiler,'_plan_stages',damaged)
    result=run(LIFECYCLE,lifecycle_data())
    assert result.compiler_result=='COMPILER_INVARIANT_FAILURE'
    assert not result.prompt


def test_h4_four_exact_tuples_are_generated_not_hidden_in_empirical_test():
    feature,data=ordered_resource_fixture()
    result=run(feature,data)
    assert result.compiler_result=='COMPILED_CONFORMING_CANDIDATE', result.receipt
    relation=next(s for s in prompt_yaml(result)['workflow_stages'] if s['stage_id']=='static_validation_2')['validation_contract']
    assert [(r['provider'],r['consumer'],r['expected']) for r in relation['cases']] == [
        ('stage:edit:observed_commit_head','stage:edit_2:observed_commit_head','PASS'),
        ('stage:edit:observed_commit_head','stage:edit_3:observed_commit_head','PASS'),
        ('stage:inspect_2:observed_commit_head','stage:edit_2:observed_commit_head','FAIL_EXPECTED'),
        ('stage:inspect_2:observed_commit_head','stage:edit_3:observed_commit_head','PASS')]
    graph=next(s for s in result.receipt['result_graph'] if s['stage_id']=='static_validation_2')
    assert graph['validation']==relation


def test_mapping_and_binding_order_preserve_full_generated_prompt():
    from test_governance_workflow_compiler import compile_fixture
    data=multi_repo_data()
    first=compile_fixture(MULTI_REPO,yaml.safe_dump(data,sort_keys=False))
    data['bindings'].reverse()
    data['repositories']=dict(reversed(list(data['repositories'].items())))
    second=compile_fixture(MULTI_REPO,yaml.safe_dump(data,sort_keys=True))
    assert first.compiler_result==second.compiler_result=='COMPILED_CONFORMING_CANDIDATE'
    assert first.prompt==second.prompt
    assert first.receipt['result_graph']==second.receipt['result_graph']
    assert first.receipt['traceability']==second.receipt['traceability']


@pytest.mark.parametrize('damage',['source','tuple','review'])
def test_dependent_source_is_verified_against_accepted_state(monkeypatch, damage):
    from test_governance_workflow_compiler import dependent_data
    original=compiler._plan_stages
    def damaged(*args):
        stages=original(*args)
        stage=stages[-1]
        if damage=='source':
            stage['expected_source_head']='f'*40
            stage['must_pass_before_effects']['source_head']='f'*40
        elif damage=='tuple': stage['must_pass_before_effects']['candidate_tuple']={'topeft':'f'*40}
        else: stage['must_pass_before_effects']['review_evidence']='unreviewed'
        return stages
    monkeypatch.setattr(compiler,'_plan_stages',damaged)
    result=run(MULTI_REPO.replace('write candidates','write candidates and integrate'),dependent_data())
    assert result.compiler_result=='COMPILER_INVARIANT_FAILURE' and not result.prompt


def test_opaque_provenance_cannot_become_a_result_dependency():
    from test_governance_workflow_compiler import staged_given_data, given_observation
    feature,data,fact=staged_given_data()
    fact['source_identity']='stage:document:identity'
    check=run(feature,data).receipt['given_readiness'][0]['verification']
    fact.update(acquisition='acquired',observed_state=given_observation(check,fact))
    result=run(feature,data)
    assert result.compiler_result=='COMPILED_CONFORMING_CANDIDATE', result.receipt
    assert all('stage:document:identity' not in stage['inputs'] for stage in result.receipt['result_graph'])


def test_receipt_binds_all_implementation_modules():
    import hashlib
    from pathlib import Path
    result=run()
    for name,digest in result.receipt['compiler_identity']['modules'].items():
        assert digest==hashlib.sha256(Path(compiler.__file__).with_name(name).read_bytes()).hexdigest()
    assert len(result.receipt['compiler_identity']['modules'])==2


def test_missing_canonical_validator_returns_diagnostic_receipt(monkeypatch):
    import subprocess
    original=compiler.Policy_source_binding.read
    def missing(binding,path):
        if path.endswith('scripts/validate_prompt.py'):
            raise subprocess.CalledProcessError(128,['git','cat-file'])
        return original(binding,path)
    monkeypatch.setattr(compiler.Policy_source_binding,'read',missing)
    result=run()
    assert result.compiler_result=='NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE'
    assert not result.prompt and result.receipt['authorized_effects']==[]


def qualification_capability_cases():
    """Current complex capability inputs; no historical mission is executed here."""
    import test_governance_workflow_compiler as t
    cases={}
    feature,data=t.composed_resource_fixture()
    data['requested_effects']=[e for e in data['requested_effects'] if e['effect_id'] not in {'commit_writer_a','commit_writer_b'}]
    data['common_validation_contract']=deepcopy(t.parallel_data()['common_validation_contract'])
    feature=feature.replace('Then exact union is reviewed','Then exact union is reviewed and common validation passes')
    cases['H1']=(feature,data)
    data=t.q04_data()
    data['requested_effects']=[e for e in data['requested_effects'] if e['effect_id']!='commit_writer_a']
    accepted=data['continuation']['accepted_prior_evidence'][0]
    accepted.pop('observed_commit_head')
    accepted['frozen_postimages']={'docs/writer_b.md':{'sha256':'e'*64,'locator':'accepted/postimages/writer_b.md'}}
    t._binding(data,'q04.accepted_writer_result')['observed_state']['value']=deepcopy(accepted)
    cases['H2']=(t.Q04_FEATURE,data)
    cases['H4']=t.ordered_resource_fixture()

    def adoption(paths, handoff=False):
        data=t.lifecycle_data();life=data.pop('lifecycle_contract')
        data['lifecycle_resources']={'adoption':life};data['stages']=[]
        data['prompt'].update(patch_kind_expected='prompt_local',validation_ceiling='static_inspection_only',
                              delegation_policy='required' if handoff else 'forbidden',
                              repo_locations={'TOP26006_fw':life['repository_path']},
                              read_only={'TOP26006_fw':['refs/heads/master','accepted acquisition/review']})
        area=data['prompt']['allowed_to_modify']['TOP26006_fw']
        area.update(tracked_paths=paths,git_index_entries=paths)
        t.bind_relation(data,'lifecycle_resources.adoption.carrier',
                        {key:life.get(key,'refs/heads/'+life['controller_branch']) for key in
                         ('repository','repository_path','worktree','ref','reference_ref')})
        life['reference_ref']='refs/heads/'+life['controller_branch']
        data['ordered_action_bindings']={};data['requested_effects']=[]
        givens=['the accepted exact coordination candidate and acquisition/review are bound']
        if handoff:
            givens += ['accepted D6/D7 infrastructure semantics remain bounded to infrastructure',
                       'task-specific scientific and application acceptance remains external',
                       'D8 is inactive and non-normative; prepared handoff grants no CP effect or adoption']
        feature='Feature: accepted coordination canonicalization\nScenario: bounded local effect and retirement\n'
        feature+='\n'.join(('Given ' if i==0 else 'And ')+s for i,s in enumerate(givens))+'\n'
        rows=[]
        if handoff:rows.append(('create_worktree','I create the exact isolated controller worktree',{}))
        edit={'paths':paths,'branch':'probe','reviewed_postimages':{path:{'sha256':'a'*64,'locator':'accepted/postimages/'+path} for path in paths},
              'review_evidence':'accepted:exact_candidate_review'}
        if handoff:edit['deferred_commit_stage']='commit'
        rows.append(('edit','I edit the exact accepted coordination paths',edit))
        if handoff:
            rows += [('inspect','I review the exact staged candidate independently',{'independent_review':True}),
                     ('commit','I create one local canonicalization commit',{'review_evidence':'stage:inspect:readback'}),
                     ('prepare_handoff','I prepare the non-effective handoff',{'evidence_locator':'prepared:CP_handoff',
                         'status':'PREPARED_NOT_EFFECTIVE_PENDING_ACCEPTANCE'})]
        rows += [('preserve','I preserve portable result and evidence',{}),
                 ('remove_worktree','I remove the exact clean linked worktree',{}),
                 ('inspect_2' if handoff else 'inspect','I read back path and registration absence',{}),
                 ('delete_ref','I delete the exact temporary ref',{})]
        for index,(sid,text,context) in enumerate(rows):
            line=len(feature.splitlines())+1;source_id='s'+str(line)
            feature+=('When ' if index==0 else 'And ')+text+'\n'
            context={'resource':'adoption',**context};data['ordered_action_bindings'][source_id]=context
            effects=[]
            if sid=='create_worktree':effects=[('worktree_create',life['worktree']),('local_git_ref_write',life['ref'])]
            elif sid=='edit':
                effects=[('tracked_write',path) for path in paths]
                if not handoff:effects.append(('local_git_ref_write',life['ref']))
            elif sid=='commit':effects=[('local_git_ref_write',life['ref'])]
            elif sid=='remove_worktree':effects=[('worktree_remove',life['worktree'])]
            elif sid=='delete_ref':effects=[('delete_local_branch',life['ref'])]
            for n,(kind,target) in enumerate(effects):
                eid=sid+'_'+str(n)
                data['bindings'].append({**data['bindings'][0],'binding_id':eid,'authorizes_effect':True,'effect':kind,'target':target})
                data['requested_effects'].append({'effect_id':eid,'effect':kind,'target':target,
                    'requested_by_step':line,'positive_authority_binding':eid,'stage_id':sid})
            if sid=='edit' and not handoff:
                t.bind_relation(data,'ordered_action_bindings.'+source_id+'.reviewed_result',
                    {'paths':paths,'postimages':context['reviewed_postimages'],'review_evidence':context['review_evidence']},
                    source_kind='accepted_evidence')
                data['bindings'][-1]['source_identity']='accepted:adoption'
                context['reuse_review_binding']=data['bindings'][-1]['binding_id']
        if not handoff:
            data['continuation']={'prior_artifact_identity':'accepted:adoption','accepted_closure_layers':['acquisition','review'],
                'accepted_prior_evidence':['accepted exact paths/postimages/review'],
                'invalidation_boundary':['carrier_applicability'],'delta_scope':[r[0] for r in rows],
                'unresolved_checks_only':['carrier_applicability'],'checks_not_to_repeat':['acquisition','review']}
        return feature+'Then the report cites evidence\n',data
    cases['H3']=adoption(['AGENTS.md','CPC.md','CONTRIBUTING.md','governance/repositories.md',
                           'governance/contracts/git_lifecycle.md','governance/contracts/orchestration.md'])
    cases['H5']=adoption(['AGENTS.md','CPC.md'],True)
    return cases


@pytest.mark.parametrize('case',['H1','H2','H3','H4','H5'])
def test_complex_functional_capability_contracts(case):
    feature,data=qualification_capability_cases()[case]
    result=run(feature,data)
    assert result.compiler_result=='COMPILED_CONFORMING_CANDIDATE', result.receipt
    plan=prompt_yaml(result);stages=plan.get('workflow_stages',[])
    if case=='H1':
        assert not any(s['stage_mode']=='integration_only' for s in stages)
        assert any(s['stage_id']=='common_validation' for s in stages)
        assert all(s['deferred_commit_stage']=='exact_union' for s in stages if s['stage_id'] in {'writer_a','writer_b'})
    elif case=='H2':
        assert 'writer_b' not in [s['stage_id'] for s in stages]
        assert next(s for s in stages if s['stage_id']=='writer_a')['deferred_commit_stage']=='exact_union'
    elif case=='H3':
        edit=next(s for s in stages if s['stage_id']=='edit')
        assert any(isinstance(v,dict) and 'accepted_review' in v for v in edit['stage_inputs'])
        assert 'without repetition' in edit['stage_acceptance_gate']
    elif case=='H5':
        assert [s['stage_id'] for s in stages][:5]==['create_worktree','edit','inspect','commit','prepare_handoff']


@pytest.mark.parametrize('damage', ['digest', 'source', 'path', 'review'])
def test_independent_artifact_projection_verifier(monkeypatch, damage):
    original=compiler._plan_stages
    def damaged(*args):
        stages=original(*args)
        stage=next(s for s in stages if s['stage_id']=='edit')
        record=next(v['exact_reviewed_postimages']['contract.json'] for v in stage['stage_inputs']
                    if isinstance(v,dict) and 'exact_reviewed_postimages' in v)
        if damage=='digest': record['sha256']='f'*64
        elif damage=='source': record['source']['content']='other'
        elif damage=='path': record['path']='foreign.json'
        else: record['review_evidence']='unreviewed'
        return stages
    monkeypatch.setattr(compiler,'_plan_stages',damaged)
    feature,data=ordered_resource_fixture()
    result=run(feature,data)
    assert not result.prompt


@pytest.mark.parametrize('damage', ['digest', 'missing_source', 'escape', 'path', 'review', 'alias'])
def test_artifact_input_counterexamples(damage):
    feature,data=ordered_resource_fixture()
    context=data['ordered_action_bindings']['s6']
    record=context['reviewed_postimages']['contract.json']
    if damage=='digest': record['sha256']='f'*64
    elif damage=='missing_source': record.pop('source')
    elif damage=='escape': record['source']={'kind':'acquired_locator','locator':'../foreign'}
    elif damage=='path': record['path']='other.json'
    elif damage=='review': record['review_evidence']='other review'
    else: record['source']['content']='distinct required content with same identity'
    assert not run(feature,data).prompt


def test_accepted_review_cannot_bind_another_artifact():
    feature,data=qualification_capability_cases()['H3']
    context=next(v for v in data['ordered_action_bindings'].values() if 'reviewed_postimages' in v)
    binding=next(b for b in data['bindings'] if b['binding_id']==context['reuse_review_binding'])
    accepted=deepcopy(binding['observed_state']['value'])
    context['reviewed_postimages']['AGENTS.md']['sha256']='f'*64
    assert binding['observed_state']['value']==accepted
    assert accepted['postimages']!=context['reviewed_postimages']
    result=run(feature,data)
    assert result.compiler_result=='NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE'
    assert not result.prompt


@pytest.mark.parametrize('relation_kind', ['frozen', 'reviewed'])
@pytest.mark.parametrize('current_rich,acquired_rich', [(False,False),(False,True),(True,False),(True,True)])
def test_artifact_canonicalization_is_symmetric(relation_kind, current_rich, acquired_rich):
    from tools.governance_workflow_ir import canonical_artifact_relation
    from test_governance_workflow_compiler import bind_relation
    compact={'doc.md':{'sha256':'a'*64,'locator':'accepted/doc.md'}}
    value=({'writer_id':'writer_b','base_oid':'b'*40,'reviewed_evidence':'accepted review',
            'frozen_postimages':compact} if relation_kind=='frozen' else
           {'paths':['doc.md'],'postimages':compact,'review_evidence':'accepted review'})
    expected=canonical_artifact_relation(value) if current_rich else deepcopy(value)
    observed=canonical_artifact_relation(value) if acquired_rich else deepcopy(value)
    before=deepcopy(observed)
    data=base_data()
    bind_relation(data,'generic.accepted_result',observed,source_kind='accepted_evidence')
    binding_id=compiler._exact_related_identity(compiler._bindings(data),'generic.accepted_result',
                                               expected,'TOP26006_fw','accepted_evidence')
    assert binding_id==data['bindings'][-1]['binding_id']
    assert observed==before
    assert canonical_artifact_relation(expected)==canonical_artifact_relation(observed)


@pytest.mark.parametrize('damage', ['sha256','path','locator','review','source','extra_field'])
@pytest.mark.parametrize('relation_kind', ['frozen','reviewed'])
def test_artifact_canonicalization_preserves_exact_mismatches(damage, relation_kind):
    from tools.governance_workflow_ir import canonical_artifact_relation
    from test_governance_workflow_compiler import bind_relation, synthetic_artifact
    from hashlib import sha256
    digest=sha256(b'content').hexdigest()
    compact={'doc.md':{'sha256':digest,'locator':'accepted/doc.md'}}
    current=({'writer_id':'writer_b','base_oid':'b'*40,'reviewed_evidence':'accepted review',
              'frozen_postimages':compact} if relation_kind=='frozen' else
             {'paths':['doc.md'],'postimages':compact,'review_evidence':'accepted review'})
    data=base_data();bind_relation(data,'generic.accepted_result',current,source_kind='accepted_evidence')
    accepted=deepcopy(data['bindings'][-1]['observed_state']['value'])
    current=canonical_artifact_relation(current)
    field='frozen_postimages' if relation_kind=='frozen' else 'postimages'
    review_field='reviewed_evidence' if relation_kind=='frozen' else 'review_evidence'
    record=current[field]['doc.md']
    if damage=='sha256': record['sha256']='f'*64
    elif damage=='path':
        current[field]['other.md']=current[field].pop('doc.md');record['path']='other.md'
        if relation_kind=='reviewed':current['paths']=['other.md']
    elif damage=='locator':record['source']['locator']='accepted/other.md'
    elif damage=='review':
        record['review_evidence']='different review';current[review_field]='different review'
    elif damage=='source':record['source']={'kind':'synthetic_literal','content':'content'}
    else:current['additional_identity']='must not disappear'
    assert data['bindings'][-1]['observed_state']['value']==accepted
    assert canonical_artifact_relation(accepted)!=canonical_artifact_relation(current)
    with pytest.raises(compiler.Compile_error):
        compiler._exact_related_identity(compiler._bindings(data),'generic.accepted_result',
                                         current,'TOP26006_fw','accepted_evidence')


def test_artifact_canonicalization_preserves_literal_content_and_digest():
    from tools.governance_workflow_ir import canonical_artifact_relation
    from test_governance_workflow_compiler import synthetic_artifact
    value={'paths':['doc.md'],'postimages':{'doc.md':synthetic_artifact('doc.md','Unicode: café\n')},
           'review_evidence':'exact reviewed synthetic replacement','other':{'identity':['retained']}}
    assert canonical_artifact_relation(value)==value
    broken=deepcopy(value);broken['postimages']['doc.md']['source']['content']='other'
    with pytest.raises(ValueError,match='digest mismatch'):canonical_artifact_relation(broken)


def test_bind_relation_snapshots_nested_acquired_evidence():
    from test_governance_workflow_compiler import bind_relation
    value={'paths':['doc.md'],'postimages':{'doc.md':{'sha256':'a'*64,'locator':'accepted/doc.md'}},
           'review_evidence':'accepted review'}
    frozen=deepcopy(value);data=base_data()
    bind_relation(data,'accepted.review',value,source_kind='accepted_evidence')
    value['paths'].append('other.md');value['postimages']['doc.md']['sha256']='b'*64
    assert data['bindings'][-1]['observed_state']['value']==frozen


def test_accepted_review_artifact_projection_is_canonical():
    from tools.governance_workflow_ir import canonical_artifact_relation
    feature,data=qualification_capability_cases()['H3']
    result=run(feature,data)
    assert result.compiler_result=='COMPILED_CONFORMING_CANDIDATE',result.receipt
    edit=next(s for s in prompt_yaml(result)['workflow_stages'] if s['stage_id']=='edit')
    observation=next(v['accepted_review']['observed_state'] for v in edit['stage_inputs']
                     if isinstance(v,dict) and 'accepted_review' in v)
    assert observation['value']==canonical_artifact_relation(observation['value'])
    postimages=next(v['exact_reviewed_postimages'] for v in edit['stage_inputs']
                   if isinstance(v,dict) and 'exact_reviewed_postimages' in v)
    assert observation['value']['postimages']==postimages



@pytest.mark.parametrize('competitor', [False, True])
def test_final_hardening_ordered_review_consumption(competitor):
    feature, data = qualification_capability_cases()['H3']
    context = next(v for v in data['ordered_action_bindings'].values() if 'reuse_review_binding' in v)
    fact = next(b for b in data['bindings'] if b['binding_id'] == context['reuse_review_binding'])
    effect_ids = [e['effect_id'] for e in data['requested_effects'] if e['stage_id'] == 'edit']
    fact.update(dependent_effect_ids=effect_ids, material_reason='exact accepted edit result')
    if competitor:
        extra = deepcopy(fact)
        extra['binding_id'] = 'contradictory_review'
        extra['observed_state']['value']['review_evidence'] = 'different review'
        data['bindings'].append(extra)
    result = run(feature, data)
    assert result.compiler_result in {'COMPILED_CONFORMING_CANDIDATE', 'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE'}, result.receipt
    assert result.prompt
    assert set(result.receipt['excluded_effects']) == (set(effect_ids) if competitor else set())
    assert 'remove_worktree_0' in result.receipt['authorized_effects']
    selected = [r for r in result.receipt['identity_readiness'] if r['binding_id'] == fact['binding_id']]
    assert selected and all(r['state'] == 'already_acquired_material_fact' for r in selected)


@pytest.mark.parametrize('closed', [False, True])
def test_final_hardening_completed_dependent_effect(closed):
    from test_governance_workflow_compiler import dependent_data
    data = dependent_data()
    fact = next(b for b in data['bindings'] if b.get('observed_state', {}).get('identity_path') == 'continuation.accepted_effect_state')
    fact.update(dependent_effect_ids=['advance_topcoffea' if closed else 'advance_topeft'],
                material_reason='accepted effect state')
    result = run(MULTI_REPO.replace('write candidates', 'write candidates and integrate'), data)
    assert result.compiler_result == 'COMPILED_CONFORMING_CANDIDATE', result.receipt
    assert result.receipt['authorized_effects'] == ['advance_topeft']
    assert result.receipt['excluded_effects'] == []
    assert 'advance_topcoffea' in result.receipt['reused_accepted_effects']
    assert [s['stage_id'] for s in prompt_yaml(result)['workflow_stages']] == ['readback', 'integrate_topeft']


def test_final_hardening_reused_writer_dependency_is_closed():
    import test_governance_workflow_compiler as t
    data = t.q04_data()
    t.bind_state(data, 'closed.writer', 'accepted')
    data['bindings'][-1].update(dependent_effect_ids=['commit_writer_b'], material_reason='closed writer')
    result = run(t.Q04_FEATURE, data)
    assert result.compiler_result == 'COMPILED_CONFORMING_CANDIDATE', result.receipt
    assert 'commit_writer_b' in result.receipt['reused_accepted_effects']
    assert 'commit_writer_b' not in [e['effect_id'] for e in result.receipt['requested_effects']]
    assert 'writer_b' not in [s['stage_id'] for s in prompt_yaml(result)['workflow_stages']]


@pytest.mark.parametrize('dependencies,valid', [(['effect_1'], True), (['unknown'], False), (['effect_1', 'effect_1'], False)])
def test_final_hardening_documentary_dependencies(dependencies, valid):
    import test_governance_workflow_compiler as t
    feature, data = t.documentation_data()
    t.bind_state(data, 'documentary.context', 'context')
    data['bindings'][-1].update(materiality='DOCUMENTARY', dependent_effect_ids=dependencies)
    result = run(feature, data)
    assert result.compiler_result == ('COMPILED_CONFORMING_CANDIDATE' if valid else 'COMPILER_INVARIANT_FAILURE'), result.receipt
    if valid:
        assert 'effect_1' in result.receipt['authorized_effects']
        assert not result.receipt['identity_readiness']
    else:
        assert not result.prompt


@pytest.mark.parametrize('acquisition', ['pending', 'not_acquired'])
def test_final_hardening_unresolved_evidence_is_unique(acquisition):
    import test_governance_workflow_compiler as t
    feature, data = t.material_given_data('the selected commit branch is checked out')
    t.ab_dispatch_bindings(data)
    extra = deepcopy(next(b for b in data['bindings'] if b['binding_id'] == 'given_ref'))
    extra.update(binding_id='unconsumed_once', acquisition=acquisition)
    extra['observed_state'] = {'identity_path':'unsupported.branch', 'value':'other'}
    data['bindings'].append(extra)
    result = run(feature, data)
    assert result.receipt['unresolved_evidence'].count('unconsumed_once') == 1
    assert result.receipt['excluded_effects'] == ['commit_ref']
    assert not result.receipt['dispatchability']['dispatchable']


@pytest.mark.parametrize('path,valid', [('/workspace/protected/output', False), ('protected/output', False),
                                       ('other/output', True), ('../protected/output', False)])
def test_final_hardening_relative_storage_negative_scope(path, valid):
    data = base_data()
    data['prompt']['read_only'] = {'TOP26006_fw': ['/workspace/protected']}
    data['prompt']['allowed_to_modify']['TOP26006_fw']['storage_paths'] = [path]
    result = run(data=data)
    assert result.compiler_result == ('COMPILED_CONFORMING_CANDIDATE' if valid else 'COMPILER_INVARIANT_FAILURE'), result.receipt


@pytest.mark.parametrize('authorization', ['generic', 'exact', 'wrong_ref', 'wrong_source', 'wrong_effect', 'documentary', 'pending', 'fast_forward'])
def test_final_hardening_non_fast_forward_authority(authorization):
    import test_governance_workflow_compiler as t
    data = base_data()
    feature = 'Feature: local ref maintenance\nScenario: exact move\nGiven bound ref\nWhen I move the local ref\nThen the report cites evidence'
    target = 'refs/heads/local_target'
    data['prompt'].update(prompt_mode='branch_maintenance_only', branch_policy='continue_existing_branch',
        target_branch='local_target', allowed_to_modify={'TOP26006_fw': [target]},
        branch_maintenance_action='restore_exact_local_ref', affected_local_branches=['local_target'],
        expected_preserved_head='a'*40, preservation_ref='refs/heads/preserved',
        reference_restore_source='b'*40, non_fast_forward_ref_move_authorized=authorization != 'fast_forward')
    t.add_effect(data, 'local_git_ref_write', target, 4, 'allowed_to_modify')
    data['prompt']['heavy_command_permissions'] = {'allowed_to_modify':data['prompt']['allowed_to_modify']}
    if authorization not in {'generic', 'fast_forward'}:
        fact = data['bindings'][-1]
        value = {key:data['prompt'][key] for key in ('branch_maintenance_action', 'expected_preserved_head',
                 'preservation_ref', 'reference_restore_source')}
        value.update(effect_id='effect_1', repository_id='TOP26006_fw', target_ref=target,
                     non_fast_forward_ref_move_authorized=True)
        if authorization == 'wrong_ref': value['target_ref'] = 'refs/heads/foreign'
        if authorization == 'wrong_source': value['reference_restore_source'] = 'c'*40
        if authorization == 'wrong_effect': value['effect_id'] = 'other_effect'
        if authorization == 'documentary': fact['materiality'] = 'DOCUMENTARY'
        if authorization == 'pending': fact['acquisition'] = 'pending'
        fact['observed_state'] = {'identity_path':'branch_maintenance.non_fast_forward_ref_move', 'value':value}
    result = run(feature, data)
    accepted = authorization in {'exact', 'fast_forward'}
    assert result.compiler_result == ('COMPILED_CONFORMING_CANDIDATE' if accepted else 'NOT_READY_MISSING_AUTHORITY_BINDING'), result.receipt
    assert bool(result.prompt) == accepted
