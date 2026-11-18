"""Transport adapter for author-authorized CPC contracts, never an authority engine.

The maintained master parser/linter and profile resolver are loaded by Git object
identity. The original prompt, including all stage grants, is sent unchanged.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import types

import yaml

from repository_task import VALIDATOR, git, governance, snapshot


DEPENDENCIES = (
    'AGENTS.md', 'CPC.md', 'CONTRIBUTING.md', 'governance/repositories.md',
    'governance/contracts/git_lifecycle.md', 'governance/contracts/orchestration.md',
    'governance/contracts/production.md', 'governance/contracts/review_and_evidence.md',
    'governance/contracts/autonomy_and_blocker_classification.md',
    'governance/model_policy.md', 'docs/how_to/providers/openai_reference_procedure.md',
    'docs/reference/provider_compatibility.md', 'tools/resolve_local_profile.py',
    'config/local_profile.schema.yml', VALIDATOR,
)


def master_module(root, master, path, name):
    module = types.ModuleType(name)
    module.__file__ = str(Path(root) / path)
    sys.modules[name] = module
    exec(compile(git(root, 'show', master + ':' + path), module.__file__, 'exec'), module.__dict__)
    return module


class ContractLoader(yaml.BaseLoader):
    """Scalars stay strings; duplicate keys, tags, anchors and aliases are refused."""
    def compose_node(self, parent, index):
        if self.check_event(yaml.AliasEvent) or getattr(self.peek_event(), 'anchor', None):
            raise ValueError('UNSUPPORTED_YAML_ALIAS_OR_ANCHOR')
        if getattr(self.peek_event(), 'tag', None):
            raise ValueError('UNSUPPORTED_YAML_TAG')
        return super().compose_node(parent, index)

    def construct_mapping(self, node, deep=False):
        result = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str) or key in result or key == '<<':
                raise ValueError('DUPLICATE_OR_UNSUPPORTED_CONTRACT_KEY')
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def yes(value):
    return value in ('yes', 'true')


def permissions(value):
    if not isinstance(value, dict):
        raise ValueError('PERMISSION_MAP_REQUIRED')
    # Preserve arbitrary action-specific keys. Do not interpret an unknown value
    # as positive, nor invent new permission names or fill omitted keys.
    for key, item in value.items():
        if key == 'allowed_to_modify':
            if not isinstance(item, list):
                raise ValueError('STAGE_PATH_GRANT_MUST_BE_LIST')
        elif item not in ('yes', 'no', 'true', 'false'):
            raise ValueError('UNSUPPORTED_PERMISSION_VALUE: ' + key)
    return value


class GovernedInbox:
    governed = True
    def __init__(self, profile_path, workspace, state):
        self.root = Path(workspace).resolve(strict=True)
        if Path(git(self.root, 'rev-parse', '--show-toplevel').decode().strip()).resolve() != self.root:
            raise ValueError('COORDINATION_GIT_ROOT_MISMATCH')
        self.master = git(self.root, 'rev-parse', 'refs/heads/master^{commit}').decode().strip()
        self.dependencies = {p: git(self.root, 'rev-parse', self.master + ':' + p).decode().strip()
                             for p in DEPENDENCIES}
        self.profile_path = str(Path(profile_path).resolve(strict=True))
        self.profile_digest = hashlib.sha256(Path(self.profile_path).read_bytes()).hexdigest()
        resolver = master_module(self.root, self.master, 'tools/resolve_local_profile.py', 'bridge_profile_resolver')
        schema = yaml.safe_load(git(self.root, 'show', self.master + ':config/local_profile.schema.yml'))
        self.profile = resolver.resolve(resolver.read_yaml(self.profile_path), schema, execution_ready=True)
        if (Path(self.profile['workspace_root']).resolve() != self.root or
                Path(self.profile['repositories']['TOP26006_fw']['path']).resolve() != self.root):
            raise ValueError('LOCAL_PROFILE_COORDINATION_IDENTITY_MISMATCH')
        for path in self.profile['tooling'].values():
            if not Path(path).is_file() or not os.access(path, os.X_OK):
                raise ValueError('LOCAL_TOOL_NOT_EXECUTABLE')
        self.state = Path(state)

    def check(self):
        if hashlib.sha256(Path(self.profile_path).read_bytes()).hexdigest() != self.profile_digest:
            raise ValueError('LOCAL_PROFILE_CHANGED')
        return governance(self.root, self.dependencies)

    def task(self, request_id, prompt):
        return GovernedTask(self, request_id, prompt)

    def check_prompt_id(self, request_id, prompt):
        """Deposit identity only; no execution admission or CLI startup."""
        master = self.check()
        validator = master_module(self.root, master, VALIDATOR, 'bridge_deposit_parser')
        blocks = validator.parse_prompt(prompt)[0]
        if len(blocks) != 1:
            raise ValueError('DEPOSIT_REQUIRES_ONE_CPC_MAPPING')
        block = blocks[0]
        try:
            fields = yaml.load('\n'.join(prompt.splitlines()[block.start_line:block.end_line - 1]),
                               Loader=ContractLoader)
        except yaml.YAMLError as exc:
            raise ValueError('UNSUPPORTED_CONTRACT_YAML') from exc
        if not isinstance(fields, dict) or fields.get('prompt_id') != request_id:
            raise ValueError('REQUEST_PROMPT_ID_MISMATCH')


class GovernedTask:
    def __init__(self, inbox, request_id, prompt):
        self.inbox = inbox
        self.governance_root = inbox.root
        self.dependencies = dict(inbox.dependencies)
        self.master = inbox.check()
        self.content = prompt
        content = prompt.encode('utf-8')
        self.digest = hashlib.sha256(content).hexdigest()
        self.request_id = request_id
        validator = master_module(inbox.root, self.master, VALIDATOR, 'bridge_prompt_validator')
        lint = validator.validate_content(content, inbox.state / request_id / 'prompt.txt')
        if lint['error_count'] or lint['mapping_block_count'] != 1:
            raise ValueError('PROMPT_LINT_FAILED_OR_MULTIPLE_CONTRACTS')
        block = validator.parse_prompt(prompt)[0][0]
        lines = prompt.splitlines()
        try:
            fields = yaml.load('\n'.join(lines[block.start_line:block.end_line - 1]), Loader=ContractLoader)
        except yaml.YAMLError as exc:
            raise ValueError('UNSUPPORTED_CONTRACT_YAML') from exc
        self.fields = fields
        required = ('prompt_id', 'short_title', 'prompt_mode', 'preferred_codex_model',
                    'reasoning_level', 'delegation_policy', 'model_selection_rationale',
                    'workspace_root', 'repo_locations', 'allowed_to_modify', 'read_only',
                    'validation_ceiling', 'decision_question', 'patch_kind_expected', 'final_chat_deliverable')
        if any(k not in fields for k in required):
            raise ValueError('INCOMPLETE_CPC_CONTRACT')
        if fields['prompt_id'] != request_id:
            raise ValueError('REQUEST_PROMPT_ID_MISMATCH')
        agents = git(inbox.root, 'show', self.master + ':AGENTS.md').decode()
        mode_table = re.search(r'\| Mode \| Activity boundary \|\n(.*?)(?:\n\n|\Z)', agents, re.S)
        if mode_table is None:
            raise ValueError('UNSUPPORTED_MASTER_MODE_TABLE')
        modes = re.findall(r'^\| `?([a-z_]+)`? \|', mode_table[1], re.M)
        if fields['prompt_mode'] not in modes:
            raise ValueError('UNSUPPORTED_PROMPT_MODE')
        policy = git(inbox.root, 'show', self.master + ':governance/model_policy.md').decode()
        self.model = fields['preferred_codex_model']
        self.reasoning = fields['reasoning_level']
        if self.model not in re.findall(r'^gpt-[\w.\-]+$', policy, re.M):
            raise ValueError('UNSUPPORTED_MODEL_PROFILE')
        reasoning = re.search(r'Reasoning levels:\s*```text\s*(.*?)```', policy, re.S)
        if not reasoning or self.reasoning not in reasoning[1].split():
            raise ValueError('UNSUPPORTED_REASONING_PROFILE')
        if fields.get('model_profile', {'model': self.model, 'reasoning_effort': self.reasoning}) != {
                'model': self.model, 'reasoning_effort': self.reasoning}:
            raise ValueError('CONTRADICTORY_MODEL_PROFILE')
        if fields.get('required_profile_agreement_evidence'):
            raise ValueError('UNSUPPORTED_REQUIRED_PROFILE_PROOF: exact runtime identity is not observable on this exec adapter')
        if fields['delegation_policy'] not in ('forbidden', 'allowed', 'required'):
            raise ValueError('UNSUPPORTED_DELEGATION_POLICY')
        if fields.get('codex_cli_mode'):
            if fields['codex_cli_mode'] == 'ultra':
                raise ValueError('UNSUPPORTED_CODEX_CLI_MODE: ultra is a policy-recognized orchestration control, but this exec adapter has no qualified mapping; a separate adapter qualification is required')
            raise ValueError('UNSUPPORTED_CODEX_CLI_MODE: value has no current-master provider mapping')
        if fields.get('patch_producer', 'codex') not in ('codex', 'codex_or_host'):
            raise ValueError('UNSUPPORTED_PATCH_PRODUCER')
        if fields['patch_kind_expected'] not in ('prompt_local', 'empty_no_changes'):
            raise ValueError('UNSUPPORTED_PATCH_BASE: this adapter validates prompt_local or empty_no_changes against admission state; cumulative patches need a separately bound base')
        self.stages = fields.get('workflow_stages', [])
        if fields['prompt_mode'] == 'orchestrated_workflow':
            if 'branch_policy' in fields or 'heavy_command_permissions' in fields:
                raise ValueError('OUTER_WORKFLOW_GRANTS_PROHIBITED')
            envelope = permissions(fields.get('workflow_effect_envelope'))
            if not isinstance(self.stages, list) or not self.stages:
                raise ValueError('WORKFLOW_STAGES_REQUIRED')
            grants = []
            for stage in self.stages:
                if not isinstance(stage, dict) or stage.get('stage_mode') not in modes or stage['stage_mode'] == 'orchestrated_workflow':
                    raise ValueError('UNSUPPORTED_STAGE_MODE')
                grant = permissions(stage.get('stage_effect_permissions'))
                if any(yes(v) and not yes(envelope.get(k)) for k, v in grant.items() if k != 'allowed_to_modify'):
                    raise ValueError('STAGE_EXCEEDS_EFFECT_ENVELOPE')
                if 'allowed_to_modify' in grant and not envelope.get('allowed_to_modify'):
                    raise ValueError('STAGE_PATHS_WITHOUT_ENVELOPE')
                grants.append(grant)
        else:
            grants = [permissions(fields.get('heavy_command_permissions'))]
            if fields.get('branch_policy') not in ('read_only_current_branch', 'continue_existing_branch', 'create_feature_branch_from_reference'):
                raise ValueError('BRANCH_POLICY_REQUIRED')
        for stage in self.stages if self.stages else [fields]:
            if stage.get('stage_mode', stage.get('prompt_mode')) == 'production_execution' and stage.get('execution_owner') != 'codex':
                raise ValueError('OWNER_MANUAL_PRODUCTION_BOUNDARY: prepare a non-executing handoff contract instead')
        self.grants = grants  # No flattening or stage inheritance: used only for invocation capability ceiling.
        self.network = any(yes(g.get('network_access')) for g in grants)
        locations = fields['repo_locations']
        if not isinstance(locations, dict) or not locations:
            raise ValueError('REPO_LOCATIONS_MAPPING_REQUIRED')
        registry = git(inbox.root, 'show', self.master + ':governance/repositories.md').decode()
        self.repositories = {}
        for repo_id, raw in locations.items():
            row = next((line for line in registry.splitlines() if line.startswith('| `' + repo_id + '` |')), '')
            if not row or any(role in row for role in ('CONDITIONAL_INACTIVE', 'KNOWN_OUT_OF_SCOPE_SURFACE')):
                raise ValueError('INACTIVE_OR_UNKNOWN_REPOSITORY: ' + repo_id)
            if not isinstance(raw, str) or not Path(raw).is_absolute():
                raise ValueError('ABSOLUTE_REPOSITORY_PATH_REQUIRED')
            path = Path(raw).resolve(strict=True)
            if Path(git(path, 'rev-parse', '--show-toplevel').decode().strip()).resolve() != path:
                raise ValueError('REPOSITORY_GIT_ROOT_MISMATCH: ' + repo_id)
            self.repositories[repo_id] = str(path)
            for module in re.findall(r'\]\((modules/[^)]+)\)', row):
                key = 'governance/' + module
                self.dependencies[key] = git(inbox.root, 'rev-parse', self.master + ':' + key).decode().strip()
        if not isinstance(fields['workspace_root'], str) or not Path(fields['workspace_root']).is_absolute():
            raise ValueError('ABSOLUTE_WORKSPACE_PATH_REQUIRED')
        self.root = Path(fields['workspace_root']).resolve(strict=True)
        if str(self.root) not in self.repositories.values():
            raise ValueError('WORKSPACE_NOT_A_SELECTED_REPOSITORY')
        # Validate scope syntax for routing writable roots; leave semantic/action
        # review to author and executor under exact master governance.
        scopes = fields['allowed_to_modify']
        if not isinstance(scopes, list) or not isinstance(fields['read_only'], list):
            raise ValueError('PATH_SCOPE_LISTS_REQUIRED')
        self.writable = []
        for scope in scopes:
            if isinstance(scope, dict) and len(scope) == 1:
                repo_id, surface = next(iter(scope.items()))
            elif isinstance(scope, str) and ':' in scope:
                repo_id, surface = scope.split(':', 1)
            else:
                raise ValueError('UNSUPPORTED_WRITE_SCOPE_SHAPE')
            if repo_id not in locations or not isinstance(surface, str) or not surface:
                raise ValueError('WRITE_SCOPE_REPOSITORY_MISMATCH')
            if self.repositories[repo_id] not in self.writable:
                self.writable.append(self.repositories[repo_id])
        immutable = ('investigation_only', 'validation_only', 'pr_preparation')
        self.mutating = (any(stage['stage_mode'] not in immutable for stage in self.stages)
                         if self.stages else fields['prompt_mode'] not in immutable)
        # Source immutability and diagnostic output are separate boundaries.
        # The actual evidence directory becomes --cd at reservation, not a
        # reason to make the source workspace writable or change prompt_mode.
        self.sandbox = 'workspace-write'
        raw_evidence = fields.get('evidence_root', inbox.profile['evidence_root'])
        if not isinstance(raw_evidence, str) or not raw_evidence:
            raise ValueError('EVIDENCE_ROOT_PATH_REQUIRED')
        path = Path(raw_evidence)
        if '..' in path.parts or raw_evidence.startswith('~'):
            raise ValueError('EVIDENCE_ROOT_ESCAPE_OR_AMBIGUITY')
        path = path if path.is_absolute() else self.root / path
        try:
            resolved_evidence = path.resolve(strict=True)
        except OSError as exc:
            raise ValueError('EVIDENCE_ROOT_UNAVAILABLE: explicitly declared root must already exist') from exc
        if resolved_evidence != path:
            raise ValueError('EVIDENCE_ROOT_SYMLINK_OR_ALIAS')
        if not path.is_dir():
            raise ValueError('EVIDENCE_ROOT_DIRECTORY_REQUIRED')
        self.evidence_root = str(path)
        # These exact-file overrides cannot be reconciled with the canonical
        # collision contract. Do not silently ignore a requested destination.
        if any(k in fields for k in ('evidence_directory', 'report_path', 'patch_path')):
            raise ValueError('CUSTOM_EVIDENCE_FILE_LAYOUT_UNSUPPORTED: declare evidence_root; canonical names and collision reservation apply')
        self.lint = lint['results']

    def admit(self, request_id, prompt):
        if request_id != self.request_id or prompt != self.content:
            raise ValueError('TASK_NOT_BOUND')
        master = governance(self.governance_root, self.dependencies)
        before = {key: snapshot(path) for key, path in self.repositories.items()}
        dirty_policy = self.fields.get('dirty_worktree_policy', 'require_clean_worktree')
        if dirty_policy not in ('require_clean_worktree', 'work_on_dirty_branch_as_is', 'allow_declared_preexisting_changes', 'commit_preparation_existing_changes'):
            raise ValueError('UNSUPPORTED_DIRTY_WORKTREE_POLICY')
        if dirty_policy == 'require_clean_worktree' and any(v['tracked_dirty'] for v in before.values()):
            raise ValueError('DIRTY_WORKTREE_REQUIRES_EXPLICIT_POLICY')
        return {
            'governed_contract': True, 'contract': self.fields,
            'governance_root': str(self.governance_root), 'governance_master_oid': master,
            'governance_dependencies': self.dependencies, 'repositories': self.repositories,
            'repositories_before': before, 'evidence_root': self.evidence_root,
            'profile_path': self.inbox.profile_path, 'profile_sha256': self.inbox.profile_digest,
            'model_profile': {'model': self.model, 'reasoning_effort': self.reasoning},
            'runtime_reported_model': 'not_observable', 'runtime_reported_reasoning_effort': 'not_observable',
            'prompt_lint': self.lint, 'governance_completeness': 'not_assessed',
            'authorization': 'caller_and_owner_responsibility_not_certified_by_bridge',
        }
