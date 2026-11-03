"""Independent constraints on a produced plan; never re-run its planner."""
from __future__ import annotations

from typing import Any

if __package__:
    from .governance_workflow_ir import artifact_specs
else:
    from governance_workflow_ir import artifact_specs


def verify_ordered_invariants(stages: list[dict[str, Any]], actions: tuple,
                              assignments: tuple, contracts: dict[str, Any],
                              action_bindings: dict[str, Any]) -> None:
    """Check safety obligations, not a second implementation of lowering."""
    by_id = {stage['stage_id']: stage for stage in stages}
    if not {a.stage_id for a in actions} <= by_id.keys():
        raise ValueError('ordered action missing from plan')
    positions = {stage['stage_id']: i for i, stage in enumerate(stages)}
    if [positions[a.stage_id] for a in actions] != sorted(positions[a.stage_id] for a in actions):
        raise ValueError('ordered action order changed')
    resources = {row.ordered_action.stage_id: row.resource for row in assignments if row.ordered_action}
    state = {name: {'preserved': False, 'removed': False, 'absent': False,
                    'deleted': False, 'unknown': False} for name in contracts}
    for action in actions:
        stage = by_id[action.stage_id]
        name = resources[action.stage_id]
        resource = contracts[name]
        local = state[name]
        kind = action.kind
        if local['deleted'] or stage['stage_goal'] != kind:
            raise ValueError('resource reused after terminal deletion or action kind changed')
        if any(s['unknown'] for s in state.values()) and not (local['unknown'] and kind == 'inspect'):
            raise ValueError('ambiguous effect not followed by authoritative readback')
        if kind == 'edit':
            context = action_bindings[action.source_id]
            expected = artifact_specs(context.get('reviewed_postimages'), context['paths'], context.get('review_evidence'))
            declarations = [row['exact_reviewed_postimages'] for row in stage['stage_inputs']
                            if isinstance(row, dict) and 'exact_reviewed_postimages' in row]
            if declarations != [{a.path: a.projection() for a in expected}]:
                raise ValueError('generated artifact declaration differs from source evidence')
            if stage['authorized_commit_scope'] != {resource['repository']: context['paths']}:
                raise ValueError('stage path scope differs from artifact paths')
        if kind == 'preserve':
            if not resource['preservation']:
                raise ValueError('portable preservation missing')
            local['preserved'] = True
        elif kind == 'inspect':
            if local['unknown']:
                check = stage.get('required_readback', {})
                if not check.get('unknown_blocks_downstream') or check.get('automatic_retry') is not False:
                    raise ValueError('ambiguous result lacks blocking no-retry readback')
                if not check.get('compare_to') or not check.get('argv'):
                    raise ValueError('ambiguous result lacks exact effect comparison')
                local['unknown'] = False
            if local['removed']:
                check = stage.get('required_readback', {})
                if check.get('path_absent') != resource['worktree'] or check.get('registration_absent') != resource['worktree']:
                    raise ValueError('absence readback does not bind removed resource')
                local['absent'] = True
        elif kind == 'worktree_create':
            argv = stage.get('safety_critical_argv', [])
            detached = resource.get('detached', False)
            expected = ['git', '-C', resource['repository_path'], 'worktree', 'add']
            expected += ['--detach'] if detached else ['-b', resource['ref'].removeprefix('refs/heads/')]
            expected += [resource['worktree'], resource.get('reference_ref', 'refs/heads/'+resource['controller_branch'])]
            if argv != expected or resource['worktree'] not in stage.get('must_be_absent', []):
                raise ValueError('creation command or absence contract differs from owned resource')
        elif kind == 'worktree_remove':
            if not local['preserved'] or local['removed']:
                raise ValueError('removal precedes preservation or repeats removal')
            expected = ['git', '-C', resource['repository_path'], 'worktree', 'remove', resource['worktree']]
            check = stage.get('required_readback_before_effect', {})
            if stage.get('safety_critical_argv') != expected or check.get('state_required') != resource['state_required']:
                raise ValueError('unsafe removal command or weakened clean-state requirement')
            local['removed'] = True
        elif kind == 'delete_ref':
            if not all(local[k] for k in ('preserved', 'removed', 'absent')):
                raise ValueError('deletion precedes preservation/removal/absence')
            observations = stage.get('runtime_observations', [])
            if len(observations) != 1:
                raise ValueError('deletion needs one fresh ref observation')
            readback = observations[0]
            expected = ['git', '-C', resource['repository_path'], 'update-ref', '-d', resource['ref'], readback['output']]
            if stage.get('safety_critical_argv') != expected or not readback.get('reject_movement_after_readback'):
                raise ValueError('deletion command lacks exact fresh compare-and-delete')
            if readback.get('argv') != ['git', '-C', resource['repository_path'], 'rev-parse', '--verify', resource['ref']]:
                raise ValueError('deletion observes another resource')
            local['deleted'] = True
        if stage.get('ambiguous_effect_contract'):
            if stage['ambiguous_effect_contract'].get('automatic_retry') is not False:
                raise ValueError('automatic retry after ambiguous effect')
            local['unknown'] = True
    if any(s['unknown'] for s in state.values()):
        raise ValueError('workflow ends with unresolved ambiguous result')
