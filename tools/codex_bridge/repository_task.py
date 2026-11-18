"""Bind one locally installed CPC prompt to a read-only invocation.

This adapter owns transport identity, not Project authorization. Governance and
the maintained prompt parser are read from exact local master objects. No YAML
profile replacement, model router, shell command filter or approval service.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import types


VALIDATOR = '.agents/skills/correction-lib-prompt-contract/scripts/validate_prompt.py'


def git(root, *args):
    env = {k: v for k, v in os.environ.items()
           if k in ('HOME', 'PATH', 'USER', 'LOGNAME', 'LANG', 'LC_ALL')}
    env['GIT_OPTIONAL_LOCKS'] = '0'
    result = subprocess.run(['git', '--no-pager', '--no-optional-locks', '-c', 'core.fsmonitor=false', '-C', str(root), *args],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env=env, timeout=15)
    if result.returncode:
        raise ValueError('REPOSITORY_PREFLIGHT_FAILED: ' + args[0])
    return result.stdout


def governance(root, dependencies, *, reader=None):
    read = reader or git
    master = read(root, 'rev-parse', '--verify', 'refs/heads/master^{commit}').decode().strip()
    for path, expected in dependencies.items():
        observed = read(root, 'rev-parse', master + ':' + path).decode().strip()
        if observed != expected:
            raise ValueError('GOVERNANCE_DELTA: author revalidation required for ' + path)
    return master


def snapshot(root):
    # Content is hashed locally, never returned as arbitrary source/file output.
    head = git(root, 'rev-parse', '--verify', 'HEAD').decode().strip()
    branch = git(root, 'rev-parse', '--abbrev-ref', 'HEAD').decode().strip()
    status = git(root, 'status', '--porcelain=v1', '--untracked-files=no')
    index = git(root, 'diff', '--cached', '--binary', '--no-ext-diff', '--no-textconv')
    worktree = git(root, 'diff', '--binary', '--no-ext-diff', '--no-textconv')
    return {'head': head, 'branch': branch,
            'refs': git(root, 'for-each-ref', '--format=%(refname) %(objectname)').decode().splitlines(),
            'index_entries_sha256': hashlib.sha256(git(root, 'ls-files', '--stage', '-z')).hexdigest(),
            'tracked_status_sha256': hashlib.sha256(status).hexdigest(),
            'index_diff_sha256': hashlib.sha256(index).hexdigest(),
            'worktree_diff_sha256': hashlib.sha256(worktree).hexdigest(),
            'tracked_dirty': bool(status)}


class RepositoryTask:
    def __init__(self, prompt_path, workspace, *, content=None, binding=None):
        self.path = (Path(prompt_path).absolute() if content is not None
                     else Path(prompt_path).resolve(strict=True))
        self.root = Path(workspace).resolve(strict=True)
        # Release evidence, not an alternative authorization or local profile.
        manifest_path = self.path.with_suffix('.binding.json')
        if binding is None:
            binding = json.loads(manifest_path.read_text(encoding='utf-8'))
        self.dependencies = binding['governance_dependencies']
        if content is None:
            content = self.path.read_bytes()
        self.digest = hashlib.sha256(content).hexdigest()
        if self.digest != binding['prompt_sha256']:
            raise ValueError('PROMPT_CHANGED: repeat author validation before activation')
        top = Path(git(self.root, 'rev-parse', '--show-toplevel').decode().strip()).resolve()
        if top != self.root:
            raise ValueError('REPOSITORY_IDENTITY: workspace is not the Git root')
        origin = git(self.root, 'config', '--get', 'remote.origin.url').decode().strip()
        if origin not in ('git@github.com:anpicci/TOP26006_fw.git',
                          'https://github.com/anpicci/TOP26006_fw.git',
                          'https://github.com/anpicci/TOP26006_fw',
                          'ssh://git@github.com/anpicci/TOP26006_fw.git'):
            raise ValueError('REPOSITORY_IDENTITY: origin is not canonical TOP26006_fw')
        self.master = governance(self.root, self.dependencies)
        # Reuse the maintained parser/linter, with blob identity checked above.
        if VALIDATOR not in self.dependencies:
            raise ValueError('VALIDATOR_IDENTITY_MISSING')
        source = git(self.root, 'show', self.master + ':' + VALIDATOR)
        module = types.ModuleType('bound_prompt_validator')
        module.__file__ = str(self.root / VALIDATOR)
        sys.modules[module.__name__] = module
        exec(compile(source, module.__file__, 'exec'), module.__dict__)
        lint = module.validate_content(content, self.path)
        if lint['error_count'] or lint['mapping_block_count'] != 1:
            raise ValueError('PROMPT_LINT_FAILED_OR_MULTIPLE_CONTRACTS')
        fields = lint['mapping_blocks'][0]['normalized_fields']
        self.fields = fields
        self.raw_fields = module.parse_prompt(content.decode('utf-8'))[0][0].fields
        required = {'prompt_mode': 'investigation_only',
                    'branch_policy': 'read_only_current_branch',
                    'validation_ceiling': 'static_inspection_only',
                    'delegation_policy': 'forbidden'}
        if any(fields.get(k) != v for k, v in required.items()):
            raise ValueError('READ_ONLY_PROFILE_MISMATCH')
        if fields.get('workspace_root') != str(self.root):
            raise ValueError('WORKSPACE_CONTRACT_MISMATCH')
        self.request_id = fields['prompt_id']
        self.model = fields['preferred_codex_model']
        self.reasoning = fields['reasoning_level']
        self.content = content.decode('utf-8')
        self.lint = lint['results']

    def admit(self, request_id, prompt):
        if request_id != self.request_id or prompt != self.content:
            raise ValueError('TASK_NOT_BOUND: only the installed exact prompt and prompt_id may run')
        return {'governance_master_oid': governance(self.root, self.dependencies),
                'governance_dependencies': self.dependencies,
                'repository_before': snapshot(self.root),
                'model_profile': {'model': self.model, 'reasoning_effort': self.reasoning},
                'runtime_reported_model': 'not_observable',
                'runtime_reported_reasoning_effort': 'not_observable',
                'prompt_lint': self.lint,
                'governance_completeness': 'author_review_required_not_certified_by_lint'}


class ReadOnlyInbox:
    """Installation opt-in for distinct author-reviewed read-only contracts.

    This narrows the supported interface; it is not semantic authorization,
    a filesystem read allowlist, or an approval service.
    """
    def __init__(self, profile_path, workspace, state):
        self.profile = json.loads(Path(profile_path).read_text(encoding='utf-8'))
        if set(self.profile) != {'governance_dependencies', 'model', 'reasoning'}:
            raise ValueError('INBOX_PROFILE_SHAPE')
        self.root = Path(workspace).resolve(strict=True)
        self.state = Path(state).absolute()
        self.dependencies = self.profile['governance_dependencies']
        if VALIDATOR not in self.dependencies:
            raise ValueError('VALIDATOR_IDENTITY_MISSING')

    def check(self):
        return governance(self.root, self.dependencies)

    def task(self, request_id, prompt):
        content = prompt.encode('utf-8')
        task = RepositoryTask(self.state / request_id / 'prompt.txt', self.root,
                              content=content, binding={
                                  'prompt_sha256': hashlib.sha256(content).hexdigest(),
                                  'governance_dependencies': self.dependencies})
        fields = task.fields
        if task.request_id != request_id:
            raise ValueError('REQUEST_PROMPT_ID_MISMATCH')
        required = {
            'allowed_to_modify': '[]', 'patch_kind_expected': 'empty_no_changes',
            'preferred_codex_model': self.profile['model'],
            'reasoning_level': self.profile['reasoning'],
            'repo_locations': 'TOP26006_fw: ' + str(self.root),
        }
        if any(fields.get(k) != v for k, v in required.items()):
            raise ValueError('INBOX_READ_ONLY_PROFILE_MISMATCH')
        if not fields.get('read_only') or any(k in fields for k in (
                'workflow_stages', 'workflow_effect_envelope', 'stage_effect_permissions')):
            raise ValueError('INBOX_UNSUPPORTED_CONTRACT_SHAPE')
        for key in ('short_title', 'decision_question', 'model_selection_rationale',
                    'final_chat_deliverable', 'evidence_requirements',
                    'classification_rules', 'anti_self_certification_rules',
                    'evidence_validation_method'):
            if not fields.get(key):
                raise ValueError('INBOX_MISSING_FIELD: ' + key)
        # Reuse the maintained parser's raw field, accepting only the documented
        # block mapping of explicit denials. Do not infer permissions from prose.
        record = task.raw_fields.get('heavy_command_permissions')
        if record is None:
            raise ValueError('INBOX_MISSING_DENIAL_MAP')
        seen = set()
        for line in record.value.splitlines():
            if not line.strip():
                continue
            parts = line.strip().split(':')
            if (len(parts) != 2 or not parts[0] or
                    not all(c.islower() or c == '_' for c in parts[0]) or
                    parts[1].strip() != 'no' or parts[0] in seen):
                raise ValueError('INBOX_ONLY_EXPLICIT_DENIALS_SUPPORTED')
            seen.add(parts[0])
        if not seen:
            raise ValueError('INBOX_EMPTY_DENIAL_MAP')
        return task
