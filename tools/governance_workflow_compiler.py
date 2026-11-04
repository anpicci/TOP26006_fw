"""Compile bounded Gherkin intent with separately acquired governance bindings.

This non-normative D8 tool prepares a CPC candidate. It never dispatches it.
The binding YAML is a task instance, not a policy registry or an authority source.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field, replace
import hashlib
import importlib.util
from pathlib import Path
import posixpath
import re
import sys
import subprocess
import types
from typing import Any, Optional

import yaml

if __package__:
    from .governance_workflow_ir import Policy_source_binding, Result_graph, canonical_mapping, artifact_specs, canonical_artifact_relation
    from .governance_workflow_semantics import verify_ordered_invariants
else:
    from governance_workflow_ir import Policy_source_binding, Result_graph, canonical_mapping, artifact_specs, canonical_artifact_relation
    from governance_workflow_semantics import verify_ordered_invariants


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / ".agents/skills/correction-lib-prompt-contract/scripts/validate_prompt.py"
GOVERNANCE = {
    "AGENTS.md": ROOT / "AGENTS.md",
    "CPC.md": ROOT / "CPC.md",
    "governance/repositories.md": ROOT / "governance/repositories.md",
    "governance/contracts/orchestration.md": ROOT / "governance/contracts/orchestration.md",
    "governance/contracts/git_lifecycle.md": ROOT / "governance/contracts/git_lifecycle.md",
    "governance/contracts/production.md": ROOT / "governance/contracts/production.md",
    "governance/contracts/review_and_evidence.md": ROOT / "governance/contracts/review_and_evidence.md",
    "governance/contracts/autonomy_and_blocker_classification.md": ROOT / "governance/contracts/autonomy_and_blocker_classification.md",
    "governance/model_policy.md": ROOT / "governance/model_policy.md",
    "CONTRIBUTING.md": ROOT / "CONTRIBUTING.md",
}
ENCODED_RULE_OWNERS = {
    "continuation_evidence_reuse": "governance/contracts/review_and_evidence.md",
    "ambiguous_outcome_readback": "governance/contracts/autonomy_and_blocker_classification.md",
}
DERIVATION = "DETERMINISTIC_GOVERNANCE_DERIVATION"
READBACK = "RUNTIME_OR_SOURCE_READBACK_REQUIRED"
NEW_DECISION = "NEW_OWNER_OR_SCIENTIFIC_DECISION_REQUIRED"
UNSUPPORTED = "UNSUPPORTED_BY_CURRENT_CANONICAL_CONTRACT"
RESULTS = {
    "COMPILED_CONFORMING_CANDIDATE",
    "NOT_READY_MISSING_AUTHORITY_BINDING",
    "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
    "NOT_READY_NEW_DECISION_BOUNDARY",
    "UNSUPPORTED_CANONICAL_CONSTRUCT",
    "COMPILER_INVARIANT_FAILURE",
    "COMPILER_DEFECT",
    "IMPLEMENTATION_GAP",
    "ARCHITECTURE_BOUNDARY_UNRESOLVED",
    "WORKFLOW_GRAPH_INCONSISTENT",
}
STAGE_CORE = {
    "stage_id", "stage_mode", "stage_goal", "stage_effect_permissions",
    "stage_inputs", "stage_acceptance_gate", "stage_outputs", "stage_failure_behavior",
}
PROMPT_CORE = {"prompt_id", "short_title", "prompt_mode", "preferred_codex_model",
               "reasoning_level", "delegation_policy", "model_selection_rationale",
               "workspace_root", "repo_locations", "allowed_to_modify", "read_only",
               "validation_ceiling", "decision_question", "patch_kind_expected",
               "final_chat_deliverable"}
ACQUISITION = {"acquired", "not_acquired", "pending", "superseded", "last_observed"}
EFFECT_KEYS = {
    "tracked_write": "allowed_to_modify", "local_git_ref_write": "allowed_to_modify",
    "worktree_create": "allowed_to_modify", "worktree_remove": "allowed_to_modify",
    "remote_git_write": "remote_git_write", "network_read": "network_access",
    "scheduler_query": "scheduler_query", "scheduler_submit_condor": "condor_submission",
    "scheduler_submit_work_queue": "work_queue_or_lobster_submission",
    "production_storage_write": "storage_writes", "publication": "pr_or_mr_write",
    "merge": "pr_or_mr_merge", "delete_local_branch": "local_branch_deletion",
    "delete_remote_branch": "remote_branch_deletion", "unblind": "unblind",
}
EFFECT_ACTION_WORDS = {
    "worktree_create": r"\b(create|add)\b",
    "worktree_remove": r"\b(remove|retire)\b",
    "tracked_write": r"\b(edit|write|modify|change|prepare|compose)\b",
    "local_git_ref_write": r"\b(commit|integrate|advance|create|move|update|rename)\b",
    "remote_git_write": r"\b(push|publish|remote)\b",
    "network_read": r"\b(query|read|fetch|inspect)\b",
    "scheduler_query": r"\b(query|inspect)\b",
    "scheduler_submit_condor": r"\b(submit|run|launch)\b",
    "scheduler_submit_work_queue": r"\b(submit|run|launch)\b",
    "production_storage_write": r"\b(produce|production|run|write)\b",
    "publication": r"\b(publish|publication|open)\b",
    "merge": r"\b(merge|integrat)\w*\b",
    "delete_local_branch": r"\b(delete|retire|remove)\b",
    "delete_remote_branch": r"\b(delete|retire|remove)\b",
    "unblind": r"\b(unblind)\b",
}
HISTORICAL_CASES = {
    "H1": "009 initial parallel-worktree accepted prompt and manual oracle",
    "H2": "009 bounded continuation accepted prompt and invalidation oracle",
    "H3": "014 governance adoption and terminal retirement accepted oracle",
    "H4": "016 two-repository candidate and integration accepted oracle",
    "H5": "017 pre-D8 canonicalization accepted workflow oracle",
}


@dataclass(frozen=True)
class Source_line:
    line: int
    keyword: str
    source_keyword: str
    text: str
    tags: tuple[str, ...] = ()
    scenario_index: int = 0
    semantic_id: str = ""


@dataclass(frozen=True)
class Semantic_intent:
    source_id: str
    feature: str
    scenarios: tuple[str, ...]
    steps: tuple[Source_line, ...]
    actions: tuple[str, ...]
    assertions: tuple[str, ...]
    negative_assertions: tuple[str, ...]
    feature_tags: tuple[str, ...] = ()
    scenario_tags: tuple[tuple[str, ...], ...] = ()
    workflow_diagram: str = ""
    partition: Optional[Semantic_partition] = None


@dataclass(frozen=True)
class Binding:
    binding_id: str
    claim: str
    materiality: str
    source_kind: str
    source_identity: str
    acquisition: str
    validity_scope: str
    observed_state: Any = None
    authorizes_effect: bool = False
    effect: str = ""
    target: str = ""
    dependent_effect_ids: tuple[str, ...] = ()
    runtime_preflight: str = ""
    material_reason: str = ""


@dataclass(frozen=True)
class Effect_intent:
    effect_id: str
    effect: str
    target: str
    requested_by_step: int
    positive_authority_binding: str
    stage_id: str = ""


@dataclass(frozen=True)
class Action_intent:
    """A closed semantic operation, independent of supplied grants/stage prose."""
    kind: str
    source_line: int
    source_id: str
    stage_id: str


@dataclass(frozen=True)
class Semantic_assignment:
    source_line: int
    semantic_id: str
    domain: str
    owners: tuple[str, ...]
    effects: tuple[Effect_intent, ...]
    resource: str
    ordered_action: Optional[Action_intent]
    provenance: tuple[str, ...]
    predecessors: tuple[int, ...] = ()
    successors: tuple[int, ...] = ()


@dataclass(frozen=True)
class Semantic_partition:
    assignments: tuple[Semantic_assignment, ...]
    parallel_roles: tuple[str, ...]
    separate_parallel: bool


@dataclass(frozen=True)
class Git_resource:
    """Stable task-owned lifecycle resource; Git observations are not inputs."""
    repository: str
    repository_path: str
    worktree: str
    ref: str
    controller_branch: str
    reference_ref: str
    state_required: dict[str, bool]
    state_source: str
    preservation: list[str]
    detached: bool = False

    def creation(self) -> tuple[dict[str, str], list[str]]:
        if self.detached:
            policy = {"stage_branch_policy": "read_only_current_branch"}
            options = ["--detach"]
        else:
            policy = {"stage_branch_policy": "create_feature_branch_from_reference",
                      "reference_branch": self.reference_ref.removeprefix("refs/heads/"),
                      "feature_branch": self.ref.removeprefix("refs/heads/")}
            options = ["-b", policy["feature_branch"]]
        return policy, ["git", "-C", self.repository_path, "worktree", "add",
                        *options, self.worktree, self.reference_ref]


def _fresh_ref_check(repository_path: str, ref: str, stage_id: str) -> dict[str, Any]:
    """Describe one effect-local readback, not an acquired observation."""
    return {"output": f"stage:{stage_id}:pre_delete_ref_oid",
            "argv": ["git", "-C", repository_path, "rev-parse", "--verify", ref],
            "before_effect": True, "require_exit_zero": True,
            "require_full_oid": True, "require_no_attached_worktree": ref,
            "reject_movement_after_readback": True,
            "on_mismatch": "stop; no refreshed lease, alternate OID or retry"}


def _resource_values(path: str, values: Any) -> Any:
    """Project only carrier relations; exact reviewed result relations stay exact."""
    resource = (path.endswith((".carrier", ".composition_carrier", ".candidate_carrier",
                               ".permanent_target", ".integration_target_carrier")) or
                path in {"retirement.owned_ref", "retirement.preserved_ref"})
    if resource and isinstance(values, dict):
        observations = {"head", "base_oid", "permanent_live_head", "candidate_head",
                        "candidate_base_oid", "exact_old_oid", "expected_preserved_head"}
        return {key: value for key, value in values.items() if key not in observations}
    return values


@dataclass(frozen=True)
class Continuation:
    prior_artifact_identity: str
    accepted_closure_layers: tuple[str, ...]
    accepted_prior_evidence: tuple[Any, ...]
    invalidation_boundary: tuple[Any, ...]
    delta_scope: tuple[Any, ...]
    unresolved_checks_only: tuple[Any, ...]
    checks_not_to_repeat: tuple[Any, ...]


@dataclass(frozen=True)
class Trace_edge:
    source: str
    output: str
    relation: str


@dataclass
class Compile_result:
    compiler_result: str
    prompt: str = ""
    receipt: dict[str, Any] = field(default_factory=dict)


class Compile_error(Exception):
    def __init__(self, result: str, message: str, line: Optional[int] = None, contract: str = ""):
        super().__init__(message)
        self.result = result
        self.line = line
        self.contract = contract


def _error(result: str, message: str, line: Optional[int] = None, contract: str = "") -> None:
    raise Compile_error(result, message, line, contract)


def _require(condition: bool, result: str, message: str, line: Optional[int] = None, contract: str = "") -> None:
    if not condition:
        _error(result, message, line, contract)


def _architecture_boundary(error: Compile_error, intent: Optional[Semantic_intent],
                           effects: tuple[Effect_intent, ...], shape: Optional[str]) -> dict[str, Any]:
    """Explain a capability result without promoting it to task authority.

    Detection sites select the classification. No caller-provided boundary,
    effect inventory or error-message heuristic can select the classification.
    D8 sources are the accepted architecture supplied at implementation time;
    these references do not introduce a second governance vocabulary.
    """
    classification, sources, section, next_boundary = {
        "UNSUPPORTED_CANONICAL_CONSTRUCT": (
            "normative", ["CPC.md", "AGENTS.md", "governance/model_policy.md"],
            "CPC Construction / AGENTS Modes and validation ceilings / Model and reasoning policy",
            "Does the owner request a canonical vocabulary revision for the rejected value?"),
        "IMPLEMENTATION_GAP": (
            "implementation_gap", ["D8-B §§3,5–8,15,17", "D8-C §3 Q03–Q06,Q20; §6"],
            "Minimum-sufficient execution, continuation and repository-local coordination",
            "Repair the compiler representation of this supported behavior without changing its semantics."),
        "ARCHITECTURE_BOUNDARY_UNRESOLVED": (
            "unresolved", ["D8-B §§3,5,15", "D8-C §3 Q17,Q20"],
            "Semantic input and canonical execution-shape boundary",
            "Bind the semantic construct to an exact architectural execution contract before selecting a shape."),
    }[error.result]
    if error.contract:
        source, section = error.contract.split("#", 1)
        sources = [source]
    steps = [step for step in intent.steps if error.line is None or step.line == error.line] if intent else []
    return {
        "semantic_pattern": [step.text for step in steps] or str(error),
        "affected_behavior_steps": [step.line for step in steps] or ([error.line] if error.line else []),
        "affected_effects": [effect.effect_id for effect in effects
                             if error.line is None or effect.requested_by_step == error.line],
        "attempted_execution_shape": shape,
        "current_architecture_boundary": {
            "classification": classification, "source_documents": sources,
            "exact_contract_or_section": section, "statement": str(error)},
        "missing_capability": str(error),
        "decision_options": ["compiler_implementation", "new_execution_shape", "gherkin_contract_change",
                             "governance_change", "owner_architecture_decision"],
        "recommended_next_boundary": next_boundary,
    }


def _source_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_local_branch_ref(value: Any) -> bool:
    """Bound the ref grammar before inserting a ref in a generated command."""
    if not isinstance(value, str) or not value.startswith("refs/heads/"):
        return False
    name = value[len("refs/heads/"):]
    if not name or len(name) > 240 or not re.fullmatch(r"[A-Za-z0-9_./-]+", name):
        return False
    return all(part and part not in {".", ".."} and not part.startswith(".") and
               not part.endswith(".") and not part.endswith(".lock")
               for part in name.split("/")) and ".." not in name


def _canonical_sources(policy: Optional[Policy_source_binding] = None) -> tuple[dict[str, str], dict[str, str]]:
    _require(set(ENCODED_RULE_OWNERS.values()) <= GOVERNANCE.keys(), "COMPILER_DEFECT",
             "encoded rule family lacks its live canonical owner")
    try:
        policy = policy or Policy_source_binding(ROOT)
        bodies = {name: policy.read(name) for name in GOVERNANCE}
        contents = {name: body.decode('utf-8') for name, body in bodies.items()}
        identities = {name: hashlib.sha256(body).hexdigest() for name, body in bodies.items()}
    except (OSError, UnicodeError, ValueError, subprocess.CalledProcessError) as exc:
        _error('NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE', f"live governance source unreadable: {exc}")
    return contents, identities


def _canonical_repository(repo_id: str, contents: dict[str, str]) -> str:
    for line in contents["governance/repositories.md"].splitlines():
        columns = [column.strip() for column in line.split("|")]
        if len(columns) < 9 or columns[1] != f"`{repo_id}`":
            continue
        _require(columns[2] not in {"`CONDITIONAL_INACTIVE`", "`KNOWN_OUT_OF_SCOPE_SURFACE`"},
                 "UNSUPPORTED_CANONICAL_CONSTRUCT", f"{repo_id!r} is inactive",
                 contract="governance/repositories.md#Typed registry")
        module = columns[7]
        if module in {"root", "inherited"}:
            return ""
        matches = set(re.findall(r"modules/([a-z0-9_]+\.md)", module))
        _require(len(matches) == 1, 'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE',
                 f"{repo_id!r} has no uniquely selected module")
        return "governance/modules/" + next(iter(matches))
    _error('NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE', f"{repo_id!r} is not an active typed repository")


def _repository_modules(data: dict[str, Any], contents: dict[str, str],
                        identities: dict[str, str]) -> dict[str, dict[str, str]]:
    roles: dict[str, dict[str, str]] = {}
    for repo_id in data.get("repositories", {}):
        module = _canonical_repository(repo_id, contents)
        if not module:
            continue
        try:
            raw = data['_policy_source'].read(module)
            body = raw.decode('utf-8')
        except (OSError, UnicodeError, ValueError, subprocess.CalledProcessError) as exc:
            _error('NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE', f"selected module unreadable: {exc}")
        contents[module] = body
        identities[module] = hashlib.sha256(raw).hexdigest()
        fields = ("permanent_live_development_branch", "permanent_personal_reference_branch",
                  "permanent_integration_branch", "feature_development_namespace")
        parsed = {}
        for field_name in fields:
            found = re.findall(r"^" + field_name + r": ([A-Za-z0-9_/*.-]+)$", body, re.M)
            _require(len(found) == 1, 'IMPLEMENTATION_GAP',
                     f"cannot uniquely parse {field_name} in {module}")
            parsed[field_name] = found[0]
        _require("native" in body.lower(), 'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE',
                 f"{module} lacks native-policy requirement")
        roles[repo_id] = parsed
    return roles


def _scope_names_repo(scope: str, repo_id: str) -> bool:
    return bool(re.search(r"(?<![A-Za-z0-9_/])" + re.escape(repo_id) +
                          r"(?![A-Za-z0-9_/])", scope))


def _canonical_mode(value: str, contents: dict[str, str]) -> None:
    section = contents["AGENTS.md"].split("## Modes and validation ceilings", 1)[1].split(
        "Declare validation_ceiling", 1)[0]
    modes = set(re.findall(r"^\| ([a-z_]+) \|", section, re.M))
    _require(bool(modes), "IMPLEMENTATION_GAP", "cannot extract canonical prompt modes")
    _require(value in modes, "UNSUPPORTED_CANONICAL_CONSTRUCT", f"{value!r} is not a live prompt mode",
             contract="AGENTS.md#Modes and validation ceilings")


def _canonical_branch(value: str, contents: dict[str, str]) -> None:
    paragraph = contents["CPC.md"].split("Branch policies remain ", 1)[1].split("\n\n", 1)[0]
    _require(bool(re.search(r"(?<![A-Za-z0-9_])" + re.escape(value) + r"(?![A-Za-z0-9_])", paragraph)),
             "UNSUPPORTED_CANONICAL_CONSTRUCT", f"{value!r} is not a live branch policy",
             contract="CPC.md#Construction: Branch policies remain")


def _canonical_ceiling(value: str, contents: dict[str, str]) -> None:
    section = contents["AGENTS.md"].split("Declare validation_ceiling:", 1)[1].split("## Reuse", 1)[0]
    values = set(re.findall(r"\b([a-z]+(?:_[a-z0-9]+)+) (?:permits|additionally permits|adds)\b", section))
    _require(bool(values), "IMPLEMENTATION_GAP", "cannot extract canonical validation ceilings")
    _require(value in values, "UNSUPPORTED_CANONICAL_CONSTRUCT",
             f"{value!r} is not a live validation ceiling", contract="AGENTS.md#Modes and validation ceilings")


def _canonical_model_field(key: str, value: str, contents: dict[str, str]) -> None:
    text = contents["governance/model_policy.md"]
    heading = {"preferred_codex_model": "Concrete Codex model labels:",
               "reasoning_level": "Reasoning levels:", "delegation_policy": "Delegation:"}[key]
    block = text.split(heading, 1)[1].split("```text", 1)[1].split("```", 1)[0]
    _require(bool(block.split()), "IMPLEMENTATION_GAP", "cannot extract canonical model-policy vocabulary")
    _require(value in block.split(), "UNSUPPORTED_CANONICAL_CONSTRUCT",
             f"{value!r} is not a live {key} value", contract="governance/model_policy.md#" + heading)


def _closed_values(field_name: str, contents: dict[str, str]) -> set[str]:
    """Extract only the current serialized fields with bounded canonical wording."""
    agents = contents["AGENTS.md"]
    git = contents["governance/contracts/git_lifecycle.md"]
    orchestration = contents["governance/contracts/orchestration.md"]
    production = contents["governance/contracts/production.md"]
    if field_name == "dirty_worktree_policy":
        if "Default preflight_profile" not in agents:
            return set()
        paragraph = agents.split("Default preflight_profile", 1)[-1].split("Inspect exact task paths", 1)[0]
        default = re.search(r"default dirty_worktree_policy\s+is ([a-z_]+)", paragraph)
        alternatives = re.search(r"Alternatives are ([a-z_,\s]+?); declare", paragraph)
        return ({default.group(1)} if default else set()) | (
            set(re.findall(r"[a-z]+(?:_[a-z0-9]+)+", alternatives.group(1))) if alternatives else set())
    if field_name == "preflight_profile":
        if "Default preflight_profile" not in agents:
            return set()
        paragraph = agents.split("Default preflight_profile", 1)[-1].split("Inspect exact task paths", 1)[0]
        default = re.search(r"is ([a-z_]+);", paragraph)
        expanded = re.search(r"([a-z_]+) requires a reason", paragraph)
        return ({default.group(1)} if default else set()) | ({expanded.group(1)} if expanded else set())
    if field_name == "patch_kind_expected":
        if "Patch kinds are " not in agents or "; name creation method" not in agents:
            return set()
        paragraph = agents.split("Patch kinds are ", 1)[-1].split("; name creation method", 1)[0]
        return {value.strip() for value in paragraph.replace(" and ", ",").split(",")
                if re.fullmatch(r"[a-z_]+", value.strip())}
    if field_name == "foreign_dirty_change_policy":
        return set(re.findall(r"foreign_dirty_change_policy: ([a-z_]+)", git))
    if field_name == "staging_policy":
        return set(re.findall(r"staging_policy: ([a-z_]+)", git))
    if field_name == "workflow_stop_policy":
        match = re.search(r"The default stop policy is\s+([a-z_]+)\.", orchestration)
        return {match.group(1)} if match else set()
    if field_name == "integration_method":
        match = re.search(r"default `integration_method` is `([a-z_]+)`", git)
        return {match.group(1)} if match else set()
    if field_name == "publication_action":
        match = re.search(r"Supported actions are:\s*```text\s*([a-z_\s]+?)```", git)
        return set(match.group(1).split()) if match else set()
    if field_name == "duplicate_pr_or_mr_policy":
        return set(re.findall(r"duplicate_pr_or_mr_policy: ([a-z_]+)", git))
    if field_name == "execution_owner":
        match = re.search(r"execution_owner \(([a-z]+) or ([a-z]+)\)", production)
        return set(match.groups()) if match else set()
    return set()


def _check_closed_fields(prompt: dict[str, Any], stages: list[dict[str, Any]],
                         contents: dict[str, str]) -> None:
    fields = {"dirty_worktree_policy", "preflight_profile", "patch_kind_expected",
              "foreign_dirty_change_policy", "staging_policy", "workflow_stop_policy",
              "integration_method", "publication_action", "duplicate_pr_or_mr_policy",
              "execution_owner"}
    for owner in (prompt, *stages):
        for key in fields & owner.keys():
            allowed = _closed_values(key, contents)
            _require(bool(allowed), "IMPLEMENTATION_GAP", f"cannot extract canonical {key} values")
            source = ("AGENTS.md" if key in {"dirty_worktree_policy", "preflight_profile", "patch_kind_expected"}
                      else "governance/contracts/orchestration.md" if key == "workflow_stop_policy"
                      else "governance/contracts/production.md" if key == "execution_owner"
                      else "governance/contracts/git_lifecycle.md")
            _require(owner[key] in allowed, "UNSUPPORTED_CANONICAL_CONSTRUCT",
                     f"{owner[key]!r} is not a source-derived live {key} value", contract=source + "#" + key)


def _branch_fields(owner: dict[str, Any], policy_key: str) -> None:
    policy = owner.get(policy_key)
    if policy == "create_feature_branch_from_reference":
        _require(bool(owner.get("reference_branch") and owner.get("feature_branch")),
                 "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "create branch needs exact reference and feature branch")
    if policy == "continue_existing_branch":
        _require(bool(owner.get("target_branch")), "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
                 "continuation needs exact target branch")


def parse_gherkin(text: str, source_id: str) -> Semantic_intent:
    """Parse only Feature/Scenario/Given/When/Then/And/But, tags and comments."""
    feature = ""
    scenarios: list[str] = []
    steps: list[Source_line] = []
    pending_tags: list[str] = []
    feature_tags: tuple[str, ...] = ()
    scenario_tags: list[tuple[str, ...]] = []
    phase = ""
    current_tags: tuple[str, ...] = ()
    prior_scenario_step_count = 0
    description_open = False
    in_diagram = False
    diagram: list[str] = []
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if in_diagram:
            if line == "```":
                in_diagram = False
            else:
                diagram.append(raw)
            continue
        if line == "```text":
            _require(description_open and not diagram, "WORKFLOW_GRAPH_INCONSISTENT",
                     "one workflow fence belongs in Feature/Rule/Scenario description", number)
            in_diagram = True
            continue
        if not line or line.startswith("#"):
            continue
        if line.startswith("@"):
            _require(bool(re.fullmatch(r"@[A-Za-z0-9_]+(?:\s+@[A-Za-z0-9_]+)*", line)),
                     'COMPILER_INVARIANT_FAILURE', "invalid tag line", number)
            pending_tags.extend(line.split())
            continue
        if line.startswith("Feature:"):
            _require(not feature and not scenarios and bool(line[8:].strip()),
                     'COMPILER_INVARIANT_FAILURE', "invalid or repeated Feature", number)
            feature = line[8:].strip()
            feature_tags = tuple(pending_tags)
            pending_tags.clear()
            description_open = True
            continue
        if line.startswith("Rule:"):
            _require(bool(feature and line[5:].strip()), "COMPILER_INVARIANT_FAILURE", "Rule needs Feature", number)
            description_open = True
            continue
        if line.startswith("Scenario:"):
            _require(bool(feature) and bool(line[9:].strip()),
                     'COMPILER_INVARIANT_FAILURE', "Scenario needs Feature and title", number)
            _require(not scenarios or len(steps) > prior_scenario_step_count,
                     'COMPILER_INVARIANT_FAILURE', "previous Scenario has no steps", number)
            if scenarios:
                previous = steps[prior_scenario_step_count:]
                _require(any(step.keyword == "When" for step in previous) and
                         any(step.keyword == "Then" for step in previous),
                         'COMPILER_INVARIANT_FAILURE', "previous Scenario lacks When or Then", number)
            scenarios.append(line[9:].strip())
            prior_scenario_step_count = len(steps)
            current_tags = tuple(pending_tags)
            scenario_tags.append(current_tags)
            pending_tags.clear()
            phase = ""
            description_open = True
            continue
        match = re.fullmatch(r"(Given|When|Then|And|But)\s+(.+)", line)
        # Standard syntax is within the semantic input contract even where
        # this parser has no lowering implementation. Malformed placement is
        # an input error, not uncertainty about the authoritative architecture.
        header = line.partition(":")[0]
        if match is None and (header in {"Background", "Scenario Outline", "Examples"} or
                              line.startswith(("|", '"""'))):
            _error("IMPLEMENTATION_GAP", f"standard Gherkin construct is not implemented: {line}",
                   number, "D8-C#Q20 semantic input versus compiler capability")
        if not match and description_open and not re.match(
                r"(?:Background|Scenario Outline|Examples|Given|When|Then|And|But)\b|[`|]", line):
            continue
        _require(match is not None and bool(scenarios), 'COMPILER_INVARIANT_FAILURE',
                 f"malformed or misplaced Gherkin construct: {line}", number)
        keyword, body = match.groups()
        description_open = False
        identifier = re.match(r"\[([A-Za-z][A-Za-z0-9_.-]*)\]\s+(.+)", body)
        semantic_id = identifier.group(1) if identifier else ""
        body = identifier.group(2) if identifier else body
        if keyword in {"And", "But"}:
            _require(bool(phase), 'COMPILER_INVARIANT_FAILURE', "And/But has no preceding step", number)
            effective = phase
        else:
            effective = keyword
            phase = keyword
        steps.append(Source_line(number, effective, keyword, body, feature_tags + current_tags,
                                 len(scenarios) - 1, semantic_id))
    _require(not in_diagram, "WORKFLOW_GRAPH_INCONSISTENT", "unclosed workflow diagram fence")
    _require(bool(feature and scenarios and steps) and len(steps) > prior_scenario_step_count and not pending_tags,
             'COMPILER_INVARIANT_FAILURE', "Feature, Scenario, steps or tag target missing")
    latest = steps[prior_scenario_step_count:]
    _require(any(step.keyword == "When" for step in latest) and any(step.keyword == "Then" for step in latest),
             'COMPILER_INVARIANT_FAILURE', "bounded Scenario needs When and observable Then")
    actions = tuple(step.text for step in steps if step.keyword == "When")
    assertions = tuple(step.text for step in steps if step.keyword == "Then")
    negative = tuple(step.text for step in steps if step.keyword == "Then" and
                     (step.source_keyword == "But" or re.search(r"\b(no|never|not|without)\b", step.text, re.I)))
    return Semantic_intent(source_id, feature, tuple(scenarios), tuple(steps), actions, assertions,
                           negative, feature_tags, tuple(scenario_tags), "\n".join(diagram))


def _ascii_graph(diagram: str) -> dict[str, Any]:
    """Parse a bounded ASCII drawing, with arrows terminating at node boxes.

    Captions after [id] are inert. Junctions use '+', crossings without a
    junction are not supported. Repeated IDs reference the same semantic node,
    which permits a separate failure-flow panel without a renderer or DSL.
    """
    _require(bool(diagram.strip()) and len(diagram) <= 100_000 and "\t" not in diagram,
             "WORKFLOW_GRAPH_INCONSISTENT", "missing, oversized or tab-aligned workflow diagram")
    rows = diagram.splitlines()
    _require(len(rows) <= 2000 and max(map(len, rows), default=0) <= 2000,
             "WORKFLOW_GRAPH_INCONSISTENT", "workflow diagram exceeds bounded grid")
    boxes: dict[tuple[int, int], str] = {}
    nodes: set[str] = set()
    cells: dict[tuple[int, int], str] = {}
    directions = {
        "-": ((0, -1), (0, 1)), "|": ((-1, 0), (1, 0)),
        "+": ((0, -1), (0, 1), (-1, 0), (1, 0)),
        ">": ((0, -1), (0, 1)), "v": ((-1, 0), (1, 0)),
        "/": ((-1, 1), (1, -1)), "\\": ((-1, -1), (1, 1)),
    }
    for y, row in enumerate(rows):
        matches = list(re.finditer(r"\[([A-Za-z][A-Za-z0-9_.-]*)\]", row))
        for i, match in enumerate(matches):
            node = match.group(1)
            nodes.add(node)
            end = matches[i + 1].start() if i + 1 < len(matches) else len(row)
            tail = row[match.end():end]
            connector = re.search(r"--|[+|>/\\]", tail)
            end = match.end() + (connector.start() if connector else len(tail.rstrip()))
            for x in range(match.start(), max(match.end(), end)):
                boxes[(y, x)] = node
        for x, char in enumerate(row):
            if (y, x) in boxes or char.isspace():
                continue
            _require(char in directions, "WORKFLOW_GRAPH_INCONSISTENT",
                     f"unsupported graph character at row {y + 1}, column {x + 1}")
            cells[(y, x)] = char
    _require(bool(nodes), "WORKFLOW_GRAPH_INCONSISTENT", "workflow diagram has no semantic nodes")
    adjacent: dict[tuple[int, int], set[tuple[int, int]]] = {p: set() for p in cells}
    endpoints: dict[tuple[int, int], list[tuple[str, bool]]] = {p: [] for p in cells}
    for (y, x), char in cells.items():
        for dy, dx in directions[char]:
            neighbor = (y + dy, x + dx)
            if neighbor in cells and (-dy, -dx) in directions[cells[neighbor]]:
                adjacent[(y, x)].add(neighbor)
            else:
                # Only arrow-to-box padding is skipped. A gap between wires
                # is never repaired or inferred from the semantic plan.
                ny, nx = neighbor
                while (0 <= ny < len(rows) and 0 <= nx < len(rows[ny]) and
                       rows[ny][nx].isspace() and (ny, nx) not in boxes):
                    ny, nx = ny + dy, nx + dx
                if (ny, nx) in boxes:
                    target = (char == ">" and (dy, dx) == (0, 1)) or \
                             (char == "v" and (dy, dx) == (1, 0))
                    endpoints[(y, x)].append((boxes[(ny, nx)], target))
        degree = len(adjacent[(y, x)]) + len(endpoints[(y, x)])
        _require(degree >= 2 and (char == "+" or degree == 2),
                 "WORKFLOW_GRAPH_INCONSISTENT", "dangling or ambiguous graph connector")
        if char in {">", "v"}:
            _require(any(target for _, target in endpoints[(y, x)]),
                     "WORKFLOW_GRAPH_INCONSISTENT", "arrow must terminate at a semantic node")
    pending = set(cells)
    edges: set[tuple[str, str]] = set()
    while pending:
        seed = min(pending)
        stack = [seed]
        component = set()
        while stack:
            point = stack.pop()
            if point not in component:
                component.add(point)
                stack.extend(adjacent[point] - component)
        pending -= component
        sources = {node for point in component for node, target in endpoints[point] if not target}
        targets = {node for point in component for node, target in endpoints[point] if target}
        _require(bool(sources and targets) and not sources & targets,
                 "WORKFLOW_GRAPH_INCONSISTENT", "connector lacks unambiguous directed source/target")
        edges.update((source, target) for source in sources for target in targets)
    return {"format": "plain_markdown_ascii_flow", "nodes": sorted(nodes),
            "connectors": [{"source": a, "target": b} for a, b in sorted(edges)]}


def _semantic_graph(intent: Semantic_intent) -> tuple[set[str], set[tuple[str, str]]]:
    """The supported scenario order; parallel assertions are not serial gates."""
    ids = [s.semantic_id for s in intent.steps]
    _require(all(ids) and len(set(ids)) == len(ids) and not any(i.startswith("derived_") for i in ids),
             "WORKFLOW_GRAPH_INCONSISTENT", "steps need unique explicit IDs; derived_ is compiler-owned")
    by_line = {s.line: s.semantic_id for s in intent.steps}
    return set(ids), {(by_line[row.source_line], by_line[target])
                     for row in _partition_rows(intent) for target in row.successors if target in by_line}


def _draw_ascii(nodes: set[str], edges: set[tuple[str, str]]) -> str:
    """Draw connected layered flows, with a compact fan/join fallback.

    All layout choices are documentary. The serialized drawing is parsed again
    and compared with the graph, so layout cannot silently introduce a gate.
    """
    remaining = set(nodes)
    layers: list[list[str]] = []
    while remaining:
        layer = sorted(n for n in remaining if not any(b == n and a in remaining for a, b in edges))
        _require(bool(layer), "WORKFLOW_GRAPH_INCONSISTENT", "cyclic dependency graph")
        layers.append(layer)
        remaining -= set(layer)
    layered_edges = {(a, b) for left, right in zip(layers, layers[1:]) for a in left for b in right}
    if edges == layered_edges and max(map(len, layers)) <= 3:
        width = max(len(n) + 2 for n in nodes) + 6
        lines = []
        for index, layer in enumerate(layers):
            if index:
                before = layers[index - 1]
                size = max(len(before), len(layer)) * width
                for phase in range(4):
                    row = [" "] * size
                    if phase == 1 and max(len(before), len(layer)) > 1:
                        for x in range(2, (max(len(before), len(layer)) - 1) * width + 3):
                            row[x] = "-"
                    for j in range(len(before) if phase == 0 else len(layer) if phase >= 2 else
                                   max(len(before), len(layer))):
                        row[j * width + 2] = "v" if phase == 3 else "+" if phase == 1 else "|"
                    lines.append("".join(row).rstrip())
            lines.append("".join(("[" + n + "]").ljust(width) for n in layer).rstrip())
        return "\n".join(lines)
    # Group equal outgoing sets. This keeps branches and joins geometric,
    # without requiring a separate textual edge list or an external layout tool.
    groups: dict[tuple[str, ...], list[str]] = {}
    for node in sorted(nodes):
        targets = tuple(sorted(b for a, b in edges if a == node))
        if targets:
            groups.setdefault(targets, []).append(node)
    panels = []
    incident = {n for edge in edges for n in edge}
    panels.extend("[" + n + "]" for n in sorted(nodes - incident))
    for targets, sources in groups.items():
        left_width = max(len(n) + 2 for n in sources) + 3
        count = max(len(sources), len(targets))
        panel = []
        for i in range(count):
            left = ("[" + sources[i] + "]").ljust(left_width, "-") if i < len(sources) else " " * left_width
            right = "--> [" + targets[i] + "]" if i < len(targets) else ""
            panel.append(left + "+" + right)
            if i < count - 1:
                panel.append(" " * left_width + "|")
        panels.append("\n".join(panel))
    return "\n\n".join(panels)


def _workflow_visualization(intent: Semantic_intent, data: dict[str, Any], shape: str,
                            effects: tuple[Effect_intent, ...]) -> tuple[dict[str, Any], str]:
    nodes, edges = _semantic_graph(intent)
    source = _ascii_graph(intent.workflow_diagram)
    normalized = lambda ns, es: {"format": "plain_markdown_ascii_flow", "nodes": sorted(ns),
                                "connectors": [{"source": a, "target": b} for a, b in sorted(es)]}
    _require(source == normalized(nodes, edges), "WORKFLOW_GRAPH_INCONSISTENT",
             "source graph adds or omits semantic nodes/dependencies")
    semantic_mapping = [{"node": s.semantic_id, "line": s.line, "role": s.keyword} for s in intent.steps]
    execution_mapping = [{"node": s.semantic_id, "semantic_steps": [s.semantic_id],
                          "role": "semantic_intent" if s.keyword == "When" else s.keyword}
                         for s in intent.steps]
    stages = data.get("stages", [])
    execution_nodes, execution_edges = set(nodes), set(edges)
    failure_edges: set[tuple[str, str]] = set()
    if stages and shape in {"orchestrated_workflow", "controller_local_workflow"}:
        # Stage dependencies are already lowered from the normalized ownership
        # partition. Geometry projects that plan; it never assigns ownership.
        action_rows = {row.source_line: row for row in _partition_rows(intent)
                       if row.domain != "non_action"}
        explicit_nodes = {owner: row.semantic_id for row in action_rows.values()
                          if row.domain in {"ordered_lifecycle", "structured_action"} or intent.partition.separate_parallel
                          for owner in row.owners}
        stage_nodes = {stage["stage_id"]: explicit_nodes.get(stage["stage_id"], "derived_" + stage["stage_id"])
                       for stage in stages}
        protected = data.get("continuation", {}).get("checks_not_to_repeat", [])
        for owner in protected:
            node = explicit_nodes.get(owner, "derived_" + owner)
            execution_nodes.add(node)
            execution_mapping = [m for m in execution_mapping if m["node"] != node]
            execution_mapping.append({"node": node, "semantic_steps": [row.semantic_id
                                      for row in action_rows.values() if owner in row.owners],
                                      "role": "reused_portable_result", "effect": False})
        action_ids = {row.semantic_id for row in action_rows.values()}
        aggregate_ids = {row.semantic_id for row in action_rows.values()
                         if row.domain == "parallel_worker_or_join" and not intent.partition.separate_parallel}
        execution_edges = {(a, b) for a, b in edges if a not in action_ids or b in aggregate_ids}
        execution_nodes.update(stage_nodes.values())
        consumed = set()
        for stage in stages:
            node = stage_nodes[stage["stage_id"]]
            provenance = stage["generation_provenance"]
            predecessors = data['_result_graph'].predecessors(stage['stage_id'])
            _require(predecessors <= stage_nodes.keys(), "WORKFLOW_GRAPH_INCONSISTENT",
                     "execution graph consumes an unavailable stage")
            execution_edges.update((stage_nodes[parent], node) for parent in predecessors)
            consumed.update(predecessors)
            row = action_rows.get(provenance["semantic_line"])
            if row and row.semantic_id in aggregate_ids:
                execution_edges.add((row.semantic_id, node))
            for owner in protected:
                if any(isinstance(value, str) and value.startswith("prior:") and
                       ":" + owner + "@" in value for value in stage["stage_inputs"]):
                    execution_edges.add((explicit_nodes.get(owner, "derived_" + owner), node))
            execution_mapping = [m for m in execution_mapping if m["node"] != node]
            execution_mapping.append({"node": node, "stage_id": stage["stage_id"],
                                      "semantic_steps": [s.semantic_id for s in intent.steps
                                                         if s.line == provenance["semantic_line"]],
                                      "role": provenance["provenance_class"],
                                      "rule_source": provenance["rule_source"]})
            failure_edges.add((node, "derived_stop"))
        execution_edges.update((stage_nodes[sid], step.semantic_id) for sid in stage_nodes.keys() - consumed
                               for step in intent.steps if step.keyword == "Then")
    elif stages:
        actions = [s for s in intent.steps if s.keyword == "When"]
        _require(len(actions) == 1 or shape == "ordered_workflow", "IMPLEMENTATION_GAP",
                 "staged visualization needs action-to-stage expansion")
        action = actions[0].semantic_id
        stage_nodes = {s["stage_id"]: "derived_" + s["stage_id"] for s in stages}
        if shape == "ordered_workflow":
            stage_nodes = {a.stage_id: a.source_id for a in _ordered_actions(intent)}
        then_ids = {s.semantic_id for s in intent.steps if s.keyword == "Then"}
        action_ids = {s.semantic_id for s in actions}
        execution_edges -= {(a, b) for a, b in execution_edges if a in action_ids}
        if shape == "ordered_workflow":
            first, rest = [stage_nodes[stages[0]["stage_id"]]], [stage_nodes[s["stage_id"]] for s in stages[1:]]
        else:
            first, rest = ["derived_" + stages[0]["stage_id"]], ["derived_" + s["stage_id"] for s in stages[1:]]
        execution_nodes.update(first + rest)
        if shape != "ordered_workflow":
            execution_edges.update((action, n) for n in first)
        if rest:
            execution_edges.update((n, rest[0]) for n in first)
        execution_edges.update(zip(rest, rest[1:]))
        execution_edges.update(((rest[-1] if rest else first[-1]), t) for t in then_ids)
        for stage in stages:
            node = stage_nodes[stage["stage_id"]]
            provenance = stage["generation_provenance"]
            execution_mapping = [m for m in execution_mapping if m["node"] != node]
            execution_mapping.append({"node": node, "stage_id": stage["stage_id"],
                                      "semantic_steps": [s.semantic_id for s in intent.steps
                                                         if s.line == provenance["semantic_line"]],
                                      "role": provenance["provenance_class"],
                                      "rule_source": provenance["rule_source"]})
            failure_edges.add((node, "derived_stop"))
    for given in data.get("_given_readiness", []):
        if given["state"] not in {"runtime_preflight_requirement", "unsupported_material_premise"}:
            continue
        step_id = next(s.semantic_id for s in intent.steps if s.line == given["line"])
        node = "derived_preflight_" + step_id
        execution_nodes.add(node)
        execution_edges.add((step_id, node))
        for effect in effects:
            if effect.effect_id not in given["dependent_effect_ids"]:
                continue
            target = stage_nodes[effect.stage_id] if stages else next(
                s.semantic_id for s in intent.steps if s.line == effect.requested_by_step)
            execution_edges.add((node, target))
        failure_edges.add((node, "derived_stop"))
        execution_mapping.append({"node": node, "semantic_steps": [step_id],
                                  "role": given["state"], "dependent_effects": given["dependent_effect_ids"]})
    acceptance = "derived_external_acceptance"
    execution_nodes.add(acceptance)
    execution_edges.update((s.semantic_id, acceptance) for s in intent.steps if s.keyword == "Then")
    execution_mapping.append({"node": acceptance, "role": "external_evidence_and_owner_boundary",
                              "rule_source": "D8-B §§13–14,17", "effect": False})
    drawing = _draw_ascii(execution_nodes, execution_edges)
    if failure_edges:
        drawing += "\n\n" + _draw_ascii({n for e in failure_edges for n in e}, failure_edges)
        execution_nodes.add("derived_stop")
        execution_edges |= failure_edges
        execution_mapping.append({"node": "derived_stop", "role": "stop_and_preserve_completed_effects",
                                  "rule_source": "governance/contracts/orchestration.md", "effect": False})
    generated = _ascii_graph(drawing)
    _require(generated == normalized(execution_nodes, execution_edges), "WORKFLOW_GRAPH_INCONSISTENT",
             "generated graph differs from semantic execution plan")
    return {"source_graph": source, "generated_graph": generated,
            "semantic_mapping": semantic_mapping, "execution_mapping": execution_mapping,
            "consistency": True}, drawing


def _bindings(data: dict[str, Any]) -> tuple[Binding, ...]:
    result: list[Binding] = []
    for item in data.get("bindings", []):
        _require(isinstance(item, dict), "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "binding must be mapping")
        try:
            binding = Binding(**item)
        except TypeError as exc:
            _error("NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", f"incomplete binding: {exc}")
        _require(all(isinstance(getattr(binding, name), str) for name in
                     ("binding_id", "claim", "materiality", "source_kind", "source_identity",
                      "acquisition", "validity_scope", "effect", "target",
                      "runtime_preflight", "material_reason")),
                 "COMPILER_INVARIANT_FAILURE", "binding fields must be strings")
        _require(isinstance(binding.dependent_effect_ids, (tuple, list)) and
                 all(isinstance(item, str) for item in binding.dependent_effect_ids),
                 "COMPILER_INVARIANT_FAILURE", "dependent effect IDs must be strings")
        _require(type(binding.authorizes_effect) is bool and binding.materiality in
                 {"IDENTITY_CRITICAL", "DECISION_MATERIAL", "DOCUMENTARY"} and
                 binding.source_kind in {"owner_decision", "governance", "repository_readback",
                                         "accepted_evidence", "other"},
                 "COMPILER_INVARIANT_FAILURE", f"invalid authority/materiality type for {binding.binding_id}")
        _require(binding.acquisition in ACQUISITION and bool(binding.source_identity and binding.validity_scope),
                 "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", f"invalid provenance for {binding.binding_id}")
        result.append(binding)
    _require(len({b.binding_id for b in result}) == len(result), "COMPILER_INVARIANT_FAILURE", "duplicate binding id")
    return tuple(result)


def _exact_identity(bindings: tuple[Binding, ...], identity_path: str, value: str,
                    repo_id: str, oid: bool = False) -> str:
    """Bind one consumed literal to a typed, acquired, value-bearing readback."""
    _require(isinstance(value, str) and bool(value) and
             (not oid or bool(re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", value))),
             "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
             f"{identity_path} is not an exact {'OID' if oid else 'identity'}")
    matches = [binding for binding in bindings
               if binding.acquisition == "acquired" and
               binding.materiality in {"IDENTITY_CRITICAL", "DECISION_MATERIAL"} and
               binding.source_kind in {"repository_readback", "accepted_evidence"} and
               _scope_names_repo(binding.validity_scope, repo_id) and
               isinstance(binding.observed_state, dict) and
               binding.observed_state == {"identity_path": identity_path, "value": value}]
    _require(len(matches) == 1, "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
             f"{identity_path} lacks one exact acquired value-bearing readback")
    return matches[0].binding_id


def _related_values(identity_path: str, values: Any) -> Any:
    """One symmetric canonical boundary for exact acquired related values."""
    try:
        return canonical_artifact_relation(_resource_values(identity_path, values))
    except ValueError as exc:
        _error('NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE', str(exc))


def _exact_related_identity(bindings: tuple[Binding, ...], identity_path: str,
                            values: dict[str, Any], repo_id: str,
                            source_kind: str) -> str:
    values = _related_values(identity_path, values)
    _require(all(value not in (None, "", []) for value in values.values()),
             "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
             f"{identity_path} has an incomplete exact relation")
    matches = [binding for binding in bindings
               if binding.acquisition == "acquired" and
               binding.materiality in {"IDENTITY_CRITICAL", "DECISION_MATERIAL"} and
               binding.source_kind == source_kind and
               _scope_names_repo(binding.validity_scope, repo_id) and
               isinstance(binding.observed_state, dict) and
               binding.observed_state.get("identity_path") == identity_path and
               _related_values(identity_path, binding.observed_state.get("value")) == values]
    _require(len(matches) == 1, "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
             f"{identity_path} lacks one exact acquired related readback")
    return matches[0].binding_id


def _relation_edge(bindings: tuple[Binding, ...], edges: list[Trace_edge],
                   identity_path: str, values: dict[str, Any], repo_id: str,
                   stage_id: str, source_kind: str = "repository_readback") -> None:
    binding_id = _exact_related_identity(bindings, identity_path, values, repo_id, source_kind)
    values = _related_values(identity_path, values)
    identity = f"identity:{identity_path}={values}"
    edges.append(Trace_edge(f"binding:{binding_id}", identity, "observes_exact_relation"))
    edges.append(Trace_edge(identity, f"stage:{stage_id}", "consumed_by"))


def _tracked_target_identity(target: str, failure_result: str) -> tuple[str, ...]:
    """Lexical repository-relative identity; source spelling remains provenance."""
    _require(isinstance(target, str) and bool(target) and not target.startswith("/") and
             ".." not in target.split("/"), failure_result,
             "tracked target is not repository relative")
    components = tuple(part for part in target.split("/") if part not in {"", "."})
    _require(bool(components), failure_result, "tracked target has no repository-relative identity")
    return components


def _tracked_targets_disjoint(identities: list[tuple[str, ...]]) -> bool:
    """Reject equality or ancestor overlap, using canonical components only."""
    return all(a[:len(b)] != b and b[:len(a)] != a
               for i, a in enumerate(identities) for b in identities[i + 1:])


def _verify_carrier_isolation(data: dict[str, Any], shape: str,
                              edges: list[Trace_edge], audit: dict[str, Any]) -> None:
    """Check all material mutable carriers after their local relations are bound."""
    if shape == "controller_local_workflow":
        carrier = data["_controller_local_carrier"]
        _require(all(stage.get("working_directory") == carrier["worktree"] and
                     (stage["stage_mode"] == "validation_only" or
                      "refs/heads/" + stage["target_branch"] == carrier["ref"])
                     for stage in data["stages"]), "COMPILER_INVARIANT_FAILURE",
                     "controller-local plan changed the bound carrier")
        targets = [target for stage in data["stages"] if stage["stage_mode"] == "coding"
                   for area in stage["stage_effect_permissions"].get("allowed_to_modify", {}).values()
                   for target in area.get("tracked_paths", [])]
        failure = "COMPILER_INVARIANT_FAILURE"
        identities = [_tracked_target_identity(target, failure) for target in targets]
        _require(_tracked_targets_disjoint(identities), failure,
                 "controller-local emitted write scopes overlap")
        repo = carrier["repository"]
        for stage in data["stages"]:
            if stage["stage_mode"] == "validation_only":
                continue
            scope = stage["stage_effect_permissions"].get("allowed_to_modify", {})
            commit_scope = stage.get("authorized_commit_scope", {})
            _require(set(scope) == set(commit_scope) == {repo}, failure,
                     "controller-local scope changed the bound repository")
            category = "tracked_paths" if stage["stage_mode"] == "coding" else "git_index_entries"
            local = [_tracked_target_identity(target, failure) for target in scope[repo].get(category, [])]
            committed = [_tracked_target_identity(target, failure) for target in commit_scope[repo]]
            _require(_tracked_targets_disjoint(local) and _tracked_targets_disjoint(committed) and
                     sorted(local) == sorted(committed), failure,
                     "controller-local commit scope differs from target identities")
            if stage["stage_mode"] == "commit_preparation":
                _require(sorted(local) == sorted(identities), failure,
                         "controller-local commit targets differ from writer union")
        audit.update(carrier_mode="controller_local", bound_carrier=carrier,
                     cross_role_isolation="not_applicable", cross_repository_isolation="not_applicable")
        return
    if shape not in {"orchestrated_workflow", "multi_repository_coordination"}:
        audit.update(cross_role_isolation="not_applicable",
                     cross_repository_isolation="not_applicable")
        return
    if shape == "multi_repository_coordination":
        audit["cross_repository_isolation"] = False
    carriers: list[tuple[str, str, str, str]] = []

    def add(role: str, repo_id: str, path: str, branch: str = "") -> None:
        _require(isinstance(path, str) and path.startswith("/") and bool(path.strip()),
                 "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", f"{role} lacks an absolute carrier path")
        carriers.append((role, repo_id, "/" + posixpath.normpath(path).lstrip("/"), branch))

    if shape == "orchestrated_workflow":
        repo_id = next(iter(data["repositories"]))
        protected = set(data.get("continuation", {}).get("checks_not_to_repeat", []))
        for worker in data["worker_contract"]["writers"]:
            if worker["stage_id"] not in protected:
                add(worker["stage_id"], repo_id, worker["worktree_path"], worker["branch"])
        work = data["worker_contract"]
        if any(stage["stage_id"] == "exact_union" for stage in data.get("stages", [])):
            add("exact_union", repo_id, work["composition_worktree_path"], work["composition_branch"])
        # The permanent target is a mutable ref even when it has no dedicated
        # worktree in the input. A controller on that ref would integrate before
        # review and common validation. Preservation may refer to the target;
        # retirement may not delete it or any active carrier.
        target = work.get("integration_target_branch")
        active_refs = {branch for _, _, _, branch in carriers}
        _require(target not in active_refs, "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
                 "material mutable ref aliases candidate and permanent integration target")
        life = data.get("retirement", {})
        retired = life.get("exact_owned_surface")
        if retired:
            protected_refs = {"refs/heads/" + branch for branch in active_refs | ({target} if target else set())}
            protected_refs.add(life.get("preservation_ref"))
            _require(retired not in protected_refs,
                     "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
                     "retirement ref aliases active, permanent, or preservation role")
    else:
        for repo_id in data["candidate_pair_order"]:
            repo = data["repositories"][repo_id]
            add(f"{repo_id}:primary", repo_id, data["prompt"]["repo_locations"][repo_id])
            add(f"{repo_id}:candidate", repo_id, repo["candidate_worktree"], repo["candidate_branch"])
    audit["carrier_roles"] = [role for role, _, _, _ in carriers]
    for index, (role, repo_id, path, branch) in enumerate(carriers):
        for other_role, other_repo, other_path, other_branch in carriers[index + 1:]:
            if role.endswith(":primary") and other_role.endswith(":primary"):
                # Repository roots can share a checkout location. Candidate
                # worktrees are the mutable surfaces that require isolation.
                continue
            if path == other_path:
                audit["cross_role_isolation"] = False
                if shape == "multi_repository_coordination":
                    audit["cross_repository_isolation"] = False
                _error("NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
                       f"material carrier path aliases {role} and {other_role}: {path}")
            if repo_id == other_repo and branch and branch == other_branch:
                audit["cross_role_isolation"] = False
                _error("NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
                       f"material mutable ref aliases {role} and {other_role}: {branch}")
    audit["cross_role_isolation"] = True
    audit["cross_repository_isolation"] = (True if shape == "multi_repository_coordination"
                                            else "not_applicable")
    edges.append(Trace_edge("governance:governance/contracts/orchestration.md",
                            "verification:cross_role_isolation", "requires_global_carrier_isolation"))
    for role, _, _, _ in carriers:
        edges.append(Trace_edge(f"carrier:{role}", "verification:cross_role_isolation",
                                "checked_for_alias"))
    if shape == "multi_repository_coordination":
        edges.append(Trace_edge("verification:cross_role_isolation",
                                "verification:cross_repository_isolation", "checks_repository_aware_paths"))


def _effects(data: dict[str, Any], intent: Semantic_intent) -> tuple[Effect_intent, ...]:
    result: list[Effect_intent] = []
    lines = {step.line for step in intent.steps}
    for item in data.get("requested_effects", []):
        try:
            effect = Effect_intent(**item)
        except TypeError as exc:
            _error("NOT_READY_MISSING_AUTHORITY_BINDING", f"incomplete requested effect: {exc}")
        _require(all(isinstance(getattr(effect, name), str) for name in
                     ("effect_id", "effect", "target", "positive_authority_binding", "stage_id")),
                 "COMPILER_INVARIANT_FAILURE", "effect fields must be strings")
        _require(effect.effect in EFFECT_KEYS, 'COMPILER_INVARIANT_FAILURE',
                 f"unknown effect inventory key {effect.effect}; an inventory is not semantic intent")
        _require(type(effect.requested_by_step) is int and effect.requested_by_step in lines and
                 bool(effect.effect_id and effect.target and effect.positive_authority_binding),
                 "COMPILER_INVARIANT_FAILURE", "effect has no exact source, target or binding")
        result.append(effect)
    _require(len({e.effect_id for e in result}) == len(result), "COMPILER_INVARIANT_FAILURE", "duplicate effect id")
    return tuple(result)


def _continuation(data: dict[str, Any]) -> Optional[Continuation]:
    raw = data.get("continuation")
    if raw is None:
        return None
    try:
        return Continuation(**{name: tuple(value) if name != "prior_artifact_identity" else value
                               for name, value in raw.items()})
    except (TypeError, AttributeError) as exc:
        _error("NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", f"incomplete continuation: {exc}")


def _historical_protected_carrier(binding: Binding,
                                  continuation: Optional[Continuation]) -> bool:
    if not continuation or not isinstance(binding.observed_state, dict):
        return False
    path = binding.observed_state.get("identity_path")
    return any(path in {f"worker_contract.writers.{writer_id}.{field}"
                        for field in ("branch", "base_oid", "observed_head", "worktree_path", "carrier")}
               for writer_id in continuation.checks_not_to_repeat)


def _action_kind(text: str) -> str:
    words = text.lower().strip()
    if re.search(r"\b(do not|never|unless|except)\b", words):
        return ""
    if re.match(r"(?:i )?(?:remove|retire)\b", words) and re.search(r"\b(worktree|controller)\b", words):
        return "worktree_remove"
    if re.match(r"(?:i )?(?:create|add)\b", words) and re.search(r"\b(worktrees?|controller)\b", words):
        return "worktree_create"
    if re.match(r"(?:i )?delete\b", words) and re.search(r"\bref\b", words):
        return "delete_ref"
    if re.match(r"(?:i )?preserve\b", words) and "evidence" in words:
        return "preserve"
    if re.match(r"(?:i )?prepare\b", words) and "handoff" in words:
        return "prepare_handoff"
    if re.match(r"(?:i )?(?:inspect|read|review|check|compare)\b", words):
        return "inspect"
    if re.match(r"(?:i )?(?:run|perform)\b", words) and "static validation" in words:
        return "static_validation"
    if re.match(r"(?:i )?(?:edit|write|modify|change)\b", words):
        return "edit"
    if re.match(r"(?:i )?(?:create|make|record)\b", words) and "commit" in words:
        return "commit"
    if "commit command" in words and "ambiguous terminal outcome" in words:
        return "outcome_unknown"
    return ""


def _ordered_actions(intent: Semantic_intent) -> tuple[Action_intent, ...]:
    rows = _partition_rows(intent)
    actions = tuple(row.ordered_action for row in rows if row.ordered_action is not None)
    _require(len(intent.scenarios) == 1 and 1 <= len(actions) <= 64 and
             len(actions) == len(intent.actions),
             "IMPLEMENTATION_GAP", "ordered plan needs a bounded single-scenario action sequence")
    return actions


def _lifecycle_identity(data: dict[str, Any]) -> Git_resource:
    """Bind the stable resource; observe Git values at the consuming stage."""
    life = data.get("lifecycle_contract", {})
    required = {"repository", "repository_path", "worktree", "ref",
                "ownership", "state_required", "state_source", "preservation", "controller_branch",
                "automatic_retry"}
    _require(isinstance(life, dict) and required <= life.keys(),
             "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "exact lifecycle identity/requirements missing")
    _require(life["repository"] in data["repositories"] and life["ownership"] == "task_owned" and
             life["automatic_retry"] is False and _safe_local_branch_ref(life["ref"]) and
             _safe_local_branch_ref("refs/heads/" + str(life["controller_branch"])) and
             life["ref"] != "refs/heads/" + life["controller_branch"],
             "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "unsafe or aliased lifecycle ownership/ref")
    for key in ("repository_path", "worktree"):
        value = life[key]
        _require(isinstance(value, str) and value.startswith("/") and
                 posixpath.normpath(value) == value and
                 bool(re.fullmatch(r"/[A-Za-z0-9_./-]+", value)),
                 "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "unsafe lifecycle path")
    _require(life["worktree"] != life["repository_path"] and
             not life["repository_path"].startswith(life["worktree"] + "/"),
             "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "lifecycle carrier aliases repository")
    clean = {"tracked_clean": True, "index_clean": True, "conflict_free": True,
             "untracked_empty": True, "ignored_empty": True, "unlocked": True}
    _require(life["state_required"] == clean and isinstance(life["preservation"], list) and
             bool(life["preservation"]) and all(isinstance(x, str) and x for x in life["preservation"]) and
             isinstance(life["state_source"], str) and bool(life["state_source"]),
             "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "lifecycle needs clean/unlocked state and portable preservation")
    reference_ref = life.get("reference_ref", "refs/heads/" + life["controller_branch"])
    _require(_safe_local_branch_ref(reference_ref) and reference_ref != life["ref"],
             "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "lifecycle reference role is unsafe")
    return Git_resource(life["repository"], life["repository_path"], life["worktree"],
                        life["ref"], life["controller_branch"], reference_ref,
                        life["state_required"], life["state_source"], life["preservation"],
                        bool(life.get("detached")))


def _accepted_result_identity(accepted: dict[str, Any]) -> dict[str, Any]:
    common = {key: accepted.get(key) for key in ("writer_id", "reviewed_evidence", "base_oid")}
    _require(all(common.values()), "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
             "accepted result lacks base or review provenance")
    if "observed_commit_head" in accepted:
        _require(bool(re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", str(accepted["observed_commit_head"]))),
                 "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "invalid accepted commit")
        return {**common, "observed_commit_head": accepted["observed_commit_head"]}
    return _related_values('', {**common, "frozen_postimages": accepted.get("frozen_postimages")})



def _shape(data: dict[str, Any], intent: Semantic_intent, effects: tuple[Effect_intent, ...],
           bindings: tuple[Binding, ...], continuation: Optional[Continuation]) -> str:
    if data.get("lifecycle_resources") and not data.get("worker_contract"):
        _ordered_actions(intent)
        return "ordered_workflow"
    if continuation:
        if data.get("multi_repository_state") and data.get("accepted_effect_state"):
            return "dependent_continuation"
        _require(not data.get("multi_repository_state"),
                 'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE',
                 "dependent continuation needs exact accepted effect-state/tuple bindings; protected work cannot be replayed")
        if not data.get("worker_contract"):
            return "continuation"
        invalidated = list(continuation.invalidation_boundary)
        protected = list(continuation.checks_not_to_repeat)
        writers = data["worker_contract"].get("writers", [])
        _require(len(writers) == 2 and len(invalidated) == len(protected) == 1 and
                 set(invalidated + protected) == {"writer_a", "writer_b"} and
                 not (set(invalidated) & set(protected)) and
                 set(continuation.delta_scope) >= {invalidated[0], "exact_union", "independent_review",
                                                    "reconciled_review", "common_validation"} and
                 set(continuation.delta_scope) <= {invalidated[0], "exact_union", "independent_review",
                                                    "reconciled_review", "common_validation", "integration",
                                                    "retirement"} and
                 {effect.stage_id for effect in effects if effect.stage_id in
                  {"integration", "retirement"}} <= set(continuation.delta_scope) and
                 not (set(continuation.delta_scope) & set(protected)) and
                 set(continuation.unresolved_checks_only) <= set(continuation.delta_scope),
                 'NOT_READY_NEW_DECISION_BOUNDARY',
                 "Q04 invalidation/protection boundary is ambiguous or contradictory")
        accepted = continuation.accepted_prior_evidence
        _require(len(accepted) == 1 and isinstance(accepted[0], dict) and
                 accepted[0].get("writer_id") == protected[0] and
                 bool(_accepted_result_identity(accepted[0])) and
                 accepted[0].get("reviewed_evidence") and
                 bool(accepted[0].get("base_oid")) and
                 protected[0] in continuation.accepted_closure_layers,
                 'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE', "Q04 accepted writer identity or common base missing")
        return "orchestrated_workflow"
    if any(row.domain == "structured_action" for row in _partition_rows(intent)):
        return "controller_local_workflow"
    action_text = " ".join(intent.actions).lower()
    repositories = data.get("repositories", {})
    by_binding_id = {binding.binding_id: binding for binding in bindings}
    changed_repositories = set()
    for effect in effects:
        if effect.effect != "tracked_write":
            continue
        authority = by_binding_id.get(effect.positive_authority_binding)
        for repo_id in repositories:
            if effect.target.startswith(repo_id + "/") or (authority and
                                                            _scope_names_repo(authority.validity_scope, repo_id)):
                changed_repositories.add(repo_id)
    if "provider" in action_text and "consumer" in action_text:
        _require(len(repositories) > 1, "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
                 "provider/consumer behavior needs repository-local bindings")
        return "multi_repository_coordination"
    if len(repositories) > 1 and len(changed_repositories) > 1:
        _require("provider" in action_text and "consumer" in action_text,
                 'IMPLEMENTATION_GAP', "multi-repository dependency is outside bounded planner")
        return "multi_repository_coordination"
    if intent.partition.parallel_roles:
        _require(bool(data.get("worker_contract")), "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
                 "parallel writers need bound isolation and review constraints")
        return "orchestrated_workflow"
    kinds = [_action_kind(action) for action in intent.actions]
    if data.get("lifecycle_contract") or (len(kinds) > 1 and
            any(kind in {"worktree_create", "worktree_remove", "prepare_handoff"} for kind in kinds)):
        _ordered_actions(intent)
        return "ordered_workflow"
    if kinds and all(kind in {"edit", "static_validation"} for kind in kinds) and kinds.count("edit") == 1:
        return "simple_non_orchestrated"
    if kinds == ["commit", "outcome_unknown"]:
        return "simple_non_orchestrated"
    if len(intent.actions) > 1:
        _require(all(re.search(r"\b(inspect|read|compare|review|check|validate|report)\b", action, re.I)
                     for action in intent.actions), 'IMPLEMENTATION_GAP',
                 "multi-action serial pattern is outside bounded planner")
        return "serial_single_repository"
    return "simple_non_orchestrated"


def _planned_mode(shape: str, intent: Semantic_intent,
                  effects: tuple[Effect_intent, ...]) -> str:
    if shape in {"orchestrated_workflow", "multi_repository_coordination", "ordered_workflow", "dependent_continuation", "controller_local_workflow"}:
        return "orchestrated_workflow"
    kinds = {effect.effect for effect in effects}
    if kinds & {"scheduler_submit_condor", "scheduler_submit_work_queue", "production_storage_write"}:
        return "production_execution"
    if kinds & {"remote_git_write", "publication", "merge", "delete_remote_branch"}:
        return "pr_publication"
    if "delete_local_branch" in kinds:
        return "branch_maintenance_only"
    if "local_git_ref_write" in kinds and "tracked_write" not in kinds:
        if any(_action_kind(action) == "commit" for action in intent.actions):
            return "commit_preparation"
        return "integration_only" if "integrat" in " ".join(intent.actions).lower() else "branch_maintenance_only"
    if "tracked_write" in kinds:
        if all(effect.target.startswith("docs/") for effect in effects if effect.effect == "tracked_write") and \
                "document" in intent.feature.lower():
            return "documentation_only"
        return "coding"
    return "investigation_only"


def _normalize_semantics(intent: Semantic_intent, data: dict[str, Any],
                         effects: tuple[Effect_intent, ...]) -> Semantic_intent:
    """Bind ownership once. Grammar requests behavior; typed bindings never grant it.

    Explicit ordered ownership supersedes a lexical resemblance, but cannot
    coexist with a worker/join effect assignment on the same source line.
    Operation kinds are interpreted only after ordered ownership is established.
    """
    if intent.partition is not None:
        return intent
    patterns = {
        "writer_a": r"I (?:edit|write) writer_a disjoint files",
        "writer_b": r"I (?:edit|write) writer_b disjoint files",
        "exact_union": r"I compose the exact union",
        "integration": r"I integrate the composed candidate",
        "retirement": r"I retire temporary branches",
    }
    aggregate_pattern = (
        r"(?:two )?writers (?:edit|write)(?: disjoint files)?"
        r"(?P<integrate>[, ]+(?:and )?(?:integrate|advance (?:the )?(?:integration )?(?:branch|ref|target)))?"
        r"(?P<retire>[, ]+(?:and )?(?:retire|remove) (?:temporary )?branches)?")
    composition = any(re.fullmatch(
        r"(?:the )?(?:exact union|composed candidate|combined worker results) (?:is|are) reviewed",
        clause.strip(), re.I)
        for assertion in intent.assertions for clause in re.split(r"\s+and\s+", assertion, flags=re.I))
    ordered_bindings = data.get("ordered_action_bindings", {})
    _require(isinstance(ordered_bindings, dict), "COMPILER_INVARIANT_FAILURE",
             "ordered action bindings must be a mapping")
    worker_roles = {w.get("stage_id") for w in data.get("worker_contract", {}).get("writers", [])}
    parallel_owners = worker_roles | {"exact_union", "integration", "retirement"}
    lifecycle = bool(data.get("lifecycle_contract") or data.get("lifecycle_resources"))
    rows = []
    counts: dict[str, int] = {}
    separate: dict[str, int] = {}
    aggregate = []
    for step in intent.steps:
        local = tuple(e for e in effects if e.requested_by_step == step.line)
        context = ordered_bindings.get(step.semantic_id)
        bound_parallel = {e.stage_id for e in local if e.stage_id in parallel_owners}
        lexical = tuple(role for role, pattern in patterns.items() if re.fullmatch(pattern, step.text, re.I))
        compound = re.fullmatch(aggregate_pattern, step.text, re.I) if step.keyword == "When" else None
        if step.keyword != "When":
            _require(not local and context is None, "NOT_READY_MISSING_AUTHORITY_BINDING",
                     "effect or ordered action bound to a non-action", step.line)
            rows.append(Semantic_assignment(step.line, step.semantic_id, "non_action", (), (), "", None,
                                            ("source:" + step.keyword,)))
            continue
        _require(not (context is not None and bound_parallel), "NOT_READY_MISSING_AUTHORITY_BINDING",
                 "contradictory typed ownership: ordered action and parallel stage", step.line)
        if context is not None or (lifecycle and not lexical and not compound and not bound_parallel):
            _require(context is None or isinstance(context, dict), "COMPILER_INVARIANT_FAILURE",
                     "ordered action context must be a mapping", step.line)
            resource = (context or {}).get("resource", "default")
            kind = _action_kind(step.text)
            _require(bool(kind), "IMPLEMENTATION_GAP", "unclassified ordered action", step.line)
            counts[kind] = counts.get(kind, 0) + 1
            name = {"worktree_remove": "remove_worktree", "worktree_create": "create_worktree"}.get(kind, kind)
            owner = name + ("_" + str(counts[kind]) if counts[kind] > 1 else "")
            action = Action_intent(kind, step.line, step.semantic_id, owner)
            rows.append(Semantic_assignment(step.line, step.semantic_id, "ordered_lifecycle", (owner,),
                local, resource, action, ("ordered_action_bindings:" + step.semantic_id if context is not None
                                         else "lifecycle_contract:default",)))
        elif lexical or compound:
            owners = lexical or tuple(["writer_a", "writer_b"] + (["exact_union"] if composition else []) +
                                      (["integration"] if compound.group("integrate") else []) +
                                      (["retirement"] if compound.group("retire") else []))
            if lexical:
                _require(not local or {e.stage_id for e in local} <= set(owners),
                         "NOT_READY_MISSING_AUTHORITY_BINDING",
                         "parallel source and typed effect owner disagree", step.line)
                _require(lexical[0] not in separate, "NOT_READY_MISSING_AUTHORITY_BINDING",
                         "duplicate parallel semantic owner", step.line)
                separate[lexical[0]] = step.line
            else:
                # Aggregate effects remain inventory, never semantic owners.
                # Let task contracts classify absent composition dependencies
                # before downstream validation rejects unsupported stage effects.
                aggregate.append(step.line)
            rows.append(Semantic_assignment(step.line, step.semantic_id, "parallel_worker_or_join", owners,
                local, "", None, ("separate_parallel_grammar" if lexical else "aggregate_parallel_grammar",
                                   "worker_contract", "source_local_effect_owners")))
        else:
            _require(not bound_parallel and not lifecycle and not data.get("worker_contract"),
                     "IMPLEMENTATION_GAP", "unclassified action in typed workflow", step.line)
            rows.append(Semantic_assignment(step.line, step.semantic_id, "other_action", (), local,
                                            "", None, ("other_execution_shape",)))
    roles = []
    parallel_rows = [r for r in rows if r.domain == "parallel_worker_or_join"]
    if parallel_rows:
        _require(not (aggregate and separate) and len(aggregate) <= 1 and
                 (bool(aggregate) or {"writer_a", "writer_b"} <= separate.keys()),
                 "IMPLEMENTATION_GAP", "parallel body needs one aggregate or distinct writer actions")
        requested = {owner for row in parallel_rows for owner in row.owners}
        _require("integration" not in requested or composition, "NOT_READY_NEW_DECISION_BOUNDARY",
                 "integration needs an identified composed result")
        _require(not separate or composition == ("exact_union" in separate),
                 "NOT_READY_NEW_DECISION_BOUNDARY", "composition action and observable assertion disagree")
        roles = ["writer_a", "writer_b", "independent_review"]
        if composition:
            roles += ["exact_union", "reconciled_review"]
        common_requested = any(re.search(r'\bcommon validation passes\b', text, re.I)
                               for text in intent.assertions)
        if "integration" in requested or (composition and common_requested):
            roles += ["common_validation"]
        if "integration" in requested:
            roles += ["integration"]
        if "retirement" in requested:
            roles += ["retirement"]
        first, last = min(r.source_line for r in parallel_rows), max(r.source_line for r in parallel_rows)
        _require(len(intent.scenarios) == 1 and all(
            row.domain != "other_action" and (row.domain != "ordered_lifecycle" or
            row.source_line < first or row.source_line > last) for row in rows),
            "IMPLEMENTATION_GAP", "unclassified or interleaved action in parallel body")
        if separate:
            tail = [separate[r] for r in ("exact_union", "integration", "retirement") if r in separate]
            _require(not tail or max(separate[w] for w in ("writer_a", "writer_b")) < min(tail),
                     "NOT_READY_NEW_DECISION_BOUNDARY", "join must follow both writer actions")
            _require(tail == sorted(tail), "NOT_READY_NEW_DECISION_BOUNDARY", "parallel tail dependencies reversed")
    # Graph geometry contributes topology only. Typed legacy ownership retains
    # its independent consistency constraint; unclassified structured actions
    # must not acquire source-order dependencies.
    structured = (not lifecycle and not ordered_bindings and not worker_roles and not parallel_rows and
                  len(data.get("repositories", {})) == 1 and
                  len({e.requested_by_step for e in effects if e.effect == "tracked_write"}) > 1)
    if structured:
        graph = _ascii_graph(intent.workflow_diagram)
        by_id = {step.semantic_id: step for step in intent.steps}
        _require(len(by_id) == len(intent.steps) and set(graph["nodes"]) == set(by_id),
                 "WORKFLOW_GRAPH_INCONSISTENT", "graph nodes differ from semantic source")
        dependencies = {(by_id[e["source"]].line, by_id[e["target"]].line)
                        for e in graph["connectors"]}
        # Reuse the graph cycle checker without changing or repairing geometry.
        _draw_ascii(set(by_id), {(e["source"], e["target"]) for e in graph["connectors"]})
        steps = {step.line: step for step in intent.steps}
        normalized = []
        for row in rows:
            predecessors = tuple(sorted(a for a, b in dependencies if b == row.source_line))
            successors = tuple(sorted(b for a, b in dependencies if a == row.source_line))
            if steps[row.source_line].keyword != "When":
                normalized.append(replace(row, predecessors=predecessors, successors=successors))
                continue
            kinds = {effect.effect for effect in row.effects}
            kind = ("write" if kinds == {"tracked_write"} else
                    "commit" if kinds == {"local_git_ref_write"} and re.match(
                        r"(?:[A-Za-z][A-Za-z0-9_]*\s+)?commits?\s+", steps[row.source_line].text, re.I) else
                    "review_join" if not kinds and len(predecessors) > 1 else "unclassified")
            owners = {effect.stage_id for effect in row.effects if effect.stage_id}
            _require(len(owners) <= 1, "NOT_READY_MISSING_AUTHORITY_BINDING",
                     "source action has conflicting effect owners", row.source_line)
            owner = next(iter(owners), "action_" + str(row.source_line))
            local = tuple(replace(effect, stage_id=owner) for effect in row.effects)
            normalized.append(replace(row, domain="structured_action", owners=(owner,),
                effects=local, ordered_action=Action_intent(kind, row.source_line, row.semantic_id, owner),
                predecessors=predecessors, successors=successors,
                provenance=("validated_source_graph:topology_only", "source_local_typed_effects", "source_keyword")))
        return replace(intent, partition=Semantic_partition(tuple(normalized), (), False))
    # Legacy typed contracts remain a separate consistency constraint.
    dependencies: set[tuple[int, int]] = set()
    for index in range(len(intent.scenarios)):
        steps = [s for s in intent.steps if s.scenario_index == index]
        actions = [s.line for s in steps if s.keyword == "When"]
        groups = [[line] for line in actions]
        if separate:
            writers = {separate[w] for w in ("writer_a", "writer_b")}
            groups = []
            for line in actions:
                if line in writers:
                    if line == min(writers):
                        groups.append(sorted(writers))
                else:
                    groups.append([line])
        dependencies.update((s.line, a) for s in steps if s.keyword == "Given" for a in groups[0])
        dependencies.update((a, b) for left, right in zip(groups, groups[1:]) for a in left for b in right)
        dependencies.update((a, s.line) for a in groups[-1] for s in steps if s.keyword == "Then")
    rows = [replace(row, predecessors=tuple(sorted(a for a, b in dependencies if b == row.source_line)),
                    successors=tuple(sorted(b for a, b in dependencies if a == row.source_line))) for row in rows]
    return replace(intent, partition=Semantic_partition(tuple(rows), tuple(roles), bool(separate)))


def _partition_rows(intent: Semantic_intent) -> tuple[Semantic_assignment, ...]:
    _require(intent.partition is not None, "COMPILER_DEFECT", "semantic partition was not normalized")
    lines = {s.line for s in intent.steps}
    return tuple(row for row in intent.partition.assignments if row.source_line in lines)


def _parallel_action_steps(intent: Semantic_intent) -> dict[str, Source_line]:
    if not intent.partition.separate_parallel:
        return {}
    steps = {step.line: step for step in intent.steps}
    return {owner: steps[row.source_line] for row in _partition_rows(intent)
            if row.domain == "parallel_worker_or_join" for owner in row.owners}


def _parallel_body(intent: Semantic_intent) -> Semantic_intent:
    return _partition_projection(intent, "parallel_worker_or_join")


def _ordered_part(intent: Semantic_intent) -> Semantic_intent:
    return _partition_projection(intent, "ordered_lifecycle")


def _partition_projection(intent: Semantic_intent, domain: str) -> Semantic_intent:
    lines = {row.source_line for row in _partition_rows(intent) if row.domain == domain}
    return replace(intent, steps=tuple(step for step in intent.steps
                   if step.keyword != "When" or step.line in lines),
                   actions=tuple(step.text for step in intent.steps
                                 if step.keyword == "When" and step.line in lines))


def _parallel_roles(intent: Semantic_intent) -> tuple[str, ...]:
    return intent.partition.parallel_roles


def _composition_dependencies(intent: Semantic_intent) -> tuple[Trace_edge, ...]:
    """Interpret the bounded composition behavior, independently of grants/mode.

    Whole action clauses are recognized, not the occurrence of an integration
    word inside an arbitrary sentence. Unfamiliar behavior stays unsupported.
    """
    if "common_validation" not in _parallel_roles(intent):
        return ()
    when = _parallel_action_steps(intent).get("integration") or next(
        step for step in _parallel_body(intent).steps if step.keyword == "When")
    then = next(step for step in intent.steps if step.keyword == "Then" and
                re.search(r"exact union|composed candidate|combined worker results", step.text, re.I))
    edges = [Trace_edge(f"line:{then.line}", "semantic:exact_union", "requires"),
             Trace_edge("semantic:exact_union", "gate:common_validation", "requires_candidate_validation")]
    if 'integration' in _parallel_roles(intent):
        edges += [Trace_edge(f"line:{when.line}", "semantic:integration", "requests"),
                  Trace_edge("gate:common_validation", "stage:integration", "required_predecessor")]
    return tuple(edges)


def _multi_repository_roles(intent: Semantic_intent) -> tuple[str, ...]:
    """Separate candidate preparation from requested permanent advancement.

    The bounded provider/consumer clause defines behavior before any supplied
    stage, effect inventory or authority is inspected.
    """
    action = " ".join(intent.actions).strip().lower()
    match = re.fullmatch(r"provider and consumer write candidates(?P<advance> and integrate)?", action)
    _require(match is not None, "IMPLEMENTATION_GAP",
             "provider/consumer behavior needs a bounded candidate/advancement representation")
    return ("integrate_topcoffea", "integrate_topeft") if match.group("advance") else ()


def _assertion_paths(intent: Semantic_intent, shape: str,
                     data: dict[str, Any]) -> list[tuple[int, int, str]]:
    """Recognize bounded material clauses and name their concrete gate."""
    paths: list[tuple[int, int, str]] = []
    # The composition/integration dependency owns common validation. Assertion
    # wording can refer to that gate, but cannot enable or disable the mechanic.
    if shape == "controller_local_workflow":
        return [(step.line, 1, "gate:" + row.owners[0])
                for step in intent.steps if step.keyword == "Then"
                for row in _partition_rows(intent) if step.line in row.successors and row.owners]
    common_required = bool(_composition_dependencies(intent))
    if common_required:
        _require(bool(data.get("common_validation_contract")),
                 'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE',
                 "composition before integration needs an exact common validation contract")
        _require(data.get("prompt", {}).get("validation_ceiling") == "targeted_unit_test",
                 'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE',
                 "composition validation needs targeted_unit_test ceiling")
    for step in intent.steps:
        if step.keyword != "Then":
            continue
        clauses = ([step.text] if data.get("lifecycle_contract") or data.get("commit_contract") or
                   data.get("deterministic_edit") else re.split(r"\s+and\s+", step.text, flags=re.I))
        for index, raw in enumerate(clauses, 1):
            clause = raw.strip().lower()
            if shape == "ordered_workflow" and data.get("lifecycle_contract"):
                _require(bool(re.fullmatch(r"(?:the )?worktree and ref are absent and canonical master is unchanged", clause)),
                         "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "unbound lifecycle assertion", step.line)
                gate = "gate:" + _ordered_actions(intent)[-1].stage_id
            elif data.get("commit_contract") and data.get("outcome_unknown"):
                _require(bool(re.search(r"read back|branch ref|head|index|retry|no new effect|idempotence|recovery authority", clause)),
                         "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "unbound commit outcome assertion", step.line)
                gate = "prompt:validation_ceiling"
            elif data.get("deterministic_edit"):
                _require(bool(re.search(r"minimum-sufficient|non-orchestrated|no worker|workflow is invented", clause)),
                         "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "unbound deterministic-edit assertion", step.line)
                gate = "prompt:validation_ceiling"
            elif shape == "orchestrated_workflow":
                if re.fullmatch(r"(?:the )?writer results are reviewed", clause):
                    gate = "gate:independent_review"
                elif re.fullmatch(r"(?:the )?(?:exact union|composed candidate|combined worker results) "
                                r"(?:is|are) reviewed", clause):
                    gate = "gate:exact_union"
                elif re.fullmatch(r"common validation passes", clause):
                    _require(bool(data.get("common_validation_contract")),
                             'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE',
                             "common validation needs an exact supplied validation contract", step.line)
                    _require(data.get("prompt", {}).get("validation_ceiling") == "targeted_unit_test",
                             'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE',
                             "common validation exceeds the frozen validation ceiling", step.line)
                    gate = "gate:common_validation"
                else:
                    _error('NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE',
                           f"material Then clause has no bound evaluable evidence contract: {raw}", step.line)
            elif shape in {"multi_repository_coordination", "dependent_continuation"}:
                _require(bool(re.fullmatch(r"(?:the )?pair is validated", clause)),
                         'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE',
                         f"material Then clause has no bound evaluable evidence contract: {raw}", step.line)
                gate = "gate:readback" if shape == "dependent_continuation" else "gate:pair_validation"
            else:
                simple = (r"(?:the )?report cites evidence|docs/[\w.-]+ is validated|"
                          r"(?:the )?branch appears|"
                          r"(?:the )?result(?: [\w.-]+)? is reported|"
                          r"[\w.-]+ is reported|no remote repository is modified")
                _require(bool(re.fullmatch(simple, clause)), 'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE',
                         f"material Then clause has no bound evaluable evidence contract: {raw}", step.line)
                gate = "prompt:validation_ceiling"
            paths.append((step.line, index, gate))
    _require(not data.get("common_validation_contract") or common_required,
             'NOT_READY_NEW_DECISION_BOUNDARY',
             "common validation contract has no composition dependency")
    return paths


def _plan_ordered(data: dict[str, Any], intent: Semantic_intent,
                  effects: tuple[Effect_intent, ...]) -> list[dict[str, Any]]:
    intent = _normalize_semantics(intent, data, effects)
    actions = _ordered_actions(intent)
    _require(not data.get("automatic_rollback") and not data.get("global_git_transaction") and
             not data.get("automatic_retry"), "COMPILER_INVARIANT_FAILURE", "ordered workflow cannot invent retry or atomic rollback")
    contracts = data.get("lifecycle_resources") or {"default": data.get("lifecycle_contract", {})}
    _require(isinstance(contracts, dict) and contracts,
             "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "ordered resources missing")
    resources = {name: _lifecycle_identity({**data, "lifecycle_contract": value})
                 for name, value in contracts.items()}
    seen_paths, seen_refs = set(), set()
    for resource in resources.values():
        _require(resource.worktree not in seen_paths and
                 (resource.repository, resource.ref) not in seen_refs,
                 "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "duplicate lifecycle carrier")
        _require(not any(resource.worktree.startswith(path + "/") or path.startswith(resource.worktree + "/")
                         for path in seen_paths), "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
                 "nested mutable lifecycle carriers are not isolated")
        if data.get("lifecycle_resources"):
            _require(resource.repository_path == data["prompt"]["repo_locations"].get(resource.repository) and
                     resource.worktree not in data["prompt"]["repo_locations"].values(),
                     "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "resource repository/carrier identity mismatch")
        seen_paths.add(resource.worktree); seen_refs.add((resource.repository, resource.ref))
    states = {name: {"preserved": False, "removed": False, "absence": False,
                     "result_head": None, "unknown": None} for name in resources}
    stages = []
    for action in actions:
        context = data.get("ordered_action_bindings", {}).get(action.source_id, {})
        name = context.get("resource", "default")
        _require(name in resources, "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
                 "ordered action needs an exact resource binding", action.source_line)
        life = resources[name]
        repo = life.repository
        state = states[name]
        preserved, removed, absence, result_head = (state[k] for k in
            ("preserved", "removed", "absence", "result_head"))
        kind = action.kind
        _require(not removed or kind in {"inspect", "delete_ref"},
                 "COMPILER_INVARIANT_FAILURE", "removed resource cannot be reused")
        _require(not any(v["unknown"] for v in states.values()) or (state["unknown"] and kind == "inspect"),
                 "COMPILER_INVARIANT_FAILURE", "ambiguous resource requires readback before dependent effects")
        local = [effect for effect in effects if effect.requested_by_step == action.source_line]
        _require(all(effect.stage_id == action.stage_id for effect in local),
                 "COMPILER_INVARIANT_FAILURE", "effect stage differs from its semantic action")
        item = {"stage_id": action.stage_id, "stage_mode": "validation_only",
                "stage_goal": kind, "stage_effect_permissions": {},
                "stage_inputs": ([f"stage:{stages[-1]['stage_id']}:{stages[-1]['stage_outputs'][0]}"] if stages else []),
                "stage_acceptance_gate": "reopen and validate exact evidence before dependent action",
                "stage_outputs": ["readback"],
                "stage_failure_behavior": "stop and preserve completed effects; OUTCOME_UNKNOWN requires exact readback before any retry",
                "generation_provenance": {"role": action.stage_id, "semantic_line": action.source_line,
                    "rule_source": "governance/contracts/git_lifecycle.md",
                    "evidence_gate": "gate:" + action.stage_id, "provenance_class": "requested_behavior"}}
        item["repository_id"] = repo
        item["working_directory"] = life.worktree
        if context.get("independent_review"):
            _require(kind == "inspect" and data["prompt"].get("delegation_policy") in {"allowed", "required"},
                     "NOT_READY_MISSING_AUTHORITY_BINDING", "independent review requires a read-only review lane")
            item["review_requirement"] = "reviewer authored/executed none of the reviewed work; dispose material findings before dependent effects"
            item["stage_acceptance_gate"] = "independent exact-result review has no unresolved blocking finding"
        if kind == "preserve":
            _require(not local, "COMPILER_INVARIANT_FAILURE", "preservation review cannot acquire an unrelated effect")
            item["stage_inputs"].append({"portable_preservation": life.preservation})
            item["stage_acceptance_gate"] = "reopen all portable result, compiler, semantic review and carrier identity evidence"
            preserved = True
        elif kind == "inspect":
            _require(not local, "COMPILER_INVARIANT_FAILURE", "readback cannot acquire an effect")
            if state["unknown"]:
                item["stage_inputs"].append("stage:" + state["unknown"] + ":effect_state")
                item["required_readback"] = {
                    "argv": [["git", "-C", life.worktree, *args] for args in
                             (["rev-parse", "HEAD"], ["rev-parse", "HEAD^"],
                              ["rev-parse", "HEAD^{tree}"], ["diff", "--cached", "--raw"],
                              ["status", "--porcelain"], ["rev-parse", "--verify", life.ref])],
                    "compare_to": "stage:" + state["unknown"] + ":staged_effect_identity",
                    "classifications": ["effect_happened", "proven_not_occurred", "OUTCOME_UNKNOWN"],
                    "unknown_blocks_downstream": True, "automatic_retry": False,
                    "retry_requires": "exact bounded recovery grant and proof effect did not occur"}
                item["stage_outputs"] += ["observed_commit_head", "effect_state"]
                item["stage_acceptance_gate"] = "require effect_happened and exact parent/tree/blob/ref/index agreement with staged effect before downstream success; proven_not_occurred or OUTCOME_UNKNOWN stops for separately authorized recovery; no blind retry"
                result_head = "stage:" + action.stage_id + ":observed_commit_head"
                state["unknown"] = None
            if removed:
                item["required_readback"] = {"path_absent": life.worktree,
                    "registration_absent": life.worktree, "no_worktree_attached_to": life.ref}
                absence = True
        elif kind in {"edit", "static_validation", "prepare_handoff"}:
            _require(isinstance(context, dict) and context, "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
                     "ordered action lacks exact bound inputs", action.source_line)
            if kind == "edit":
                paths = context.get("paths", [])
                branch = context.get("branch", "")
                _require(paths and len(set(paths)) == len(paths) and
                         "refs/heads/" + branch == life.ref and
                         _safe_local_branch_ref("refs/heads/" + branch) and
                         {e.target for e in local if e.effect == "tracked_write"} == set(paths) and
                         len([e for e in local if e.effect == "local_git_ref_write" and
                              e.target == "refs/heads/" + branch]) == (0 if context.get("deferred_commit_stage") else 1) and
                         all(e.effect in {"tracked_write", "local_git_ref_write"} for e in local),
                         "NOT_READY_MISSING_AUTHORITY_BINDING", "ordered edit needs exact paths and commit effect")
                item.update(stage_mode="coding", stage_branch_policy="continue_existing_branch",
                            target_branch=branch, authorized_commit_scope={repo: paths},
                            explicitly_adopted_inherited_changes="none", foreign_dirty_change_policy="preserve_and_exclude",
                            staging_policy="exact_path_only")
                item["stage_effect_permissions"] = {"allowed_to_modify": {repo: {
                    "tracked_paths": paths, "git_index_entries": paths,
                    "local_refs": ["refs/heads/" + branch], "git_effects": ["create_one_prompt_local_commit"]}}}
                try:
                    artifacts = artifact_specs(context.get('reviewed_postimages'), paths, context.get('review_evidence'))
                except ValueError as exc:
                    _error('NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE', str(exc))
                item["stage_inputs"].append({"exact_reviewed_postimages": {a.path: a.projection() for a in artifacts}})
                _require(context.get("reviewed_postimages") and context.get("review_evidence"),
                         "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "ordered edit lacks reviewed exact result")
                item['stage_inputs'].append({'reviewed_result_evidence': context['review_evidence']})
                if context.get('reuse_review_binding'):
                    bindings = _bindings(data)
                    binding_id = _exact_related_identity(bindings,
                        'ordered_action_bindings.' + action.source_id + '.reviewed_result',
                        {'paths': paths, 'postimages': context['reviewed_postimages'],
                         'review_evidence': context['review_evidence']}, repo, 'accepted_evidence')
                    _require(binding_id == context['reuse_review_binding'],
                             'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE', 'accepted review relation differs')
                    accepted_review = asdict(next(b for b in bindings if b.binding_id == binding_id))
                    observation = accepted_review['observed_state']
                    observation['value'] = _related_values(observation['identity_path'], observation['value'])
                    item['stage_inputs'].append({'accepted_review': accepted_review,
                                                'require_exact_postimage_equality': True})
                item["stage_acceptance_gate"] = "independent staged candidate review, exact-path diff and static validation before one local commit; read back parent/tree/paths"
                if context.get('reuse_review_binding'):
                    item['stage_acceptance_gate'] = 'reopen accepted review; compare exact staged postimages and scope; reuse valid acquisition/review without repetition; changed result stops for invalidation and review; read back commit parent/tree/paths'
                item["stage_outputs"] = ["readback", "observed_commit_head", "frozen_postimages"]
                if context.get("deferred_commit_stage"):
                    target = context["deferred_commit_stage"]
                    _require(any(a.stage_id == target and a.kind == "commit" and
                                 a.source_line > action.source_line for a in actions),
                             "NOT_READY_MISSING_AUTHORITY_BINDING", "staged edit needs a later exact commit action")
                    item["stage_effect_permissions"] = {"allowed_to_modify": {repo: {"tracked_paths": paths, "git_index_entries": paths}}}
                    item["deferred_commit_stage"] = target
                    item["stage_outputs"] = ["frozen_postimages"]
                    item["stage_acceptance_gate"] = "freeze base and exact postimages; preserve staged effect for independent precommit review"
                    state["prepared"] = {"stage_id": action.stage_id, "paths": paths, "commit_stage": target}
                if context.get("ambiguous_outcome"):
                    _require(context.get("readback_before_retry") is True and
                             context.get("automatic_retry") is False,
                             "COMPILER_INVARIANT_FAILURE", "ambiguous effect needs explicit readback and no automatic retry")
                    item["ambiguous_effect_contract"] = {
                        "initial_result": "OUTCOME_UNKNOWN", "maximum_attempts_before_readback": 1,
                        "capture_before_attempt": ["base", "parent", "staged_tree", "exact_path_blobs", "index"],
                        "automatic_retry": False, "no_global_rollback": True,
                        "on_unknown": "preserve partial state; next resource action must be exact readback"}
                    item["stage_outputs"] += ["staged_effect_identity", "effect_state"]
                    state["unknown"] = action.stage_id
                if "refs/heads/" + branch == life.ref and not context.get("deferred_commit_stage"):
                    result_head = f"stage:{action.stage_id}:observed_commit_head"
                    item["working_directory"] = life.worktree
            else:
                _require(not local and context.get("evidence_locator"),
                         "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "read-only action needs existing evidence")
                item["stage_inputs"].append(context["evidence_locator"])
                if context.get("result_inputs"):
                    available = {f"stage:{s['stage_id']}:{out}" for s in stages for out in s["stage_outputs"]}
                    _require(set(context["result_inputs"]) <= available,
                             "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "validation consumes an unavailable stage result")
                    item["stage_inputs"] += context["result_inputs"]
                if context.get("validation_contract"):
                    item["validation_contract"] = context["validation_contract"]
                    item["stage_outputs"].append("validation_evidence")
                if kind == "prepare_handoff":
                    _require(context.get("status") == "PREPARED_NOT_EFFECTIVE_PENDING_ACCEPTANCE",
                             "COMPILER_INVARIANT_FAILURE", "handoff must remain non-effective")
                    item["stage_acceptance_gate"] = "inspect prepared-only handoff evidence; no dispatch, publication or acceptance effect"
        elif kind == "commit":
            prepared = state.get("prepared", {})
            _require(prepared.get("commit_stage") == action.stage_id and
                     len(local) == 1 and local[0].effect == "local_git_ref_write" and
                     local[0].target == life.ref and context.get("review_evidence"),
                     "NOT_READY_MISSING_AUTHORITY_BINDING", "commit needs exact prepared result, review and local ref effect")
            item.update(stage_mode="commit_preparation", stage_branch_policy="continue_existing_branch",
                        target_branch=life.ref.removeprefix("refs/heads/"),
                        authorized_commit_scope={repo: prepared["paths"]},
                        explicitly_adopted_inherited_changes="none", foreign_dirty_change_policy="preserve_and_exclude",
                        staging_policy="exact_path_only")
            item["stage_inputs"] += ["stage:" + prepared["stage_id"] + ":frozen_postimages", context["review_evidence"]]
            item["stage_effect_permissions"] = {"allowed_to_modify": {repo: {"local_refs": [life.ref]}}}
            item["stage_outputs"] += ["observed_commit_head", "staged_effect_identity", "effect_state"]
            item["stage_acceptance_gate"] = "reopen exact staged path list and full diff against reviewed postimages before one commit; read back parent/tree/blobs/index"
            result_head = "stage:" + action.stage_id + ":observed_commit_head"
            if context.get("ambiguous_outcome"):
                _require(context.get("readback_before_retry") is True and context.get("automatic_retry") is False,
                         "COMPILER_INVARIANT_FAILURE", "ambiguous commit needs readback and no automatic retry")
                item["ambiguous_effect_contract"] = {
                    "initial_result": "OUTCOME_UNKNOWN", "maximum_attempts_before_readback": 1,
                    "capture_before_attempt": ["base", "parent", "staged_tree", "exact_path_blobs", "index"],
                    "automatic_retry": False, "no_global_rollback": True}
                state["unknown"] = action.stage_id
            state.pop("prepared", None)
        elif kind in {"worktree_create", "worktree_remove", "delete_ref"}:
            expected = {"worktree_create": "worktree_create", "worktree_remove": "worktree_remove",
                        "delete_ref": "delete_local_branch"}[kind]
            target = life.ref if kind == "delete_ref" else life.worktree
            path_effects = [e for e in local if e.effect == expected and e.target == target]
            branch_effects = [e for e in local if e.effect == "local_git_ref_write" and e.target == life.ref]
            _require(len(path_effects) == 1 and len(local) == (2 if kind == "worktree_create" and
                     not life.detached else 1) and
                     (kind != "worktree_create" or life.detached or len(branch_effects) == 1),
                     "NOT_READY_MISSING_AUTHORITY_BINDING", "lifecycle action lacks exact independent path/ref effects")
            scope = {repo: {"local_refs" if kind == "delete_ref" else "worktree_paths": [target]}}
            item.update(stage_mode="branch_maintenance_only", stage_branch_policy="continue_existing_branch",
                        target_branch=life.controller_branch)
            item["stage_effect_permissions"] = {"allowed_to_modify": scope}
            item["stage_inputs"].append({"must_pass_before_effects": {
                "repository": repo, "repository_path": life.repository_path,
                "worktree": life.worktree, "ref": life.ref,
                "ownership": "task_owned", "state": life.state_required,
                "source": life.state_source, "on_mismatch": "stop_before_effect"}})
            if result_head:
                item["stage_inputs"].append(result_head)
            if kind == "worktree_create":
                _require(not state.get("creation_stage"), "COMPILER_INVARIANT_FAILURE", "duplicate resource creation")
                state["creation_stage"] = action.stage_id
                # Creation cannot require a clean existing worktree at an absent path.
                item["stage_inputs"] = [value for value in item["stage_inputs"]
                                        if not isinstance(value, dict) or "must_pass_before_effects" not in value]
                item["stage_inputs"].append({"must_pass_before_effects": {
                    "repository": repo, "reference_ref": life.reference_ref,
                    "fresh_reference_readback": ["git", "-C", life.repository_path,
                                                 "rev-parse", "--verify", life.reference_ref],
                    "task_owned_destination": life.worktree, "reject_collisions": True}})
                policy, argv = life.creation()
                item.pop("target_branch", None)
                item.update(policy)
                item["stage_outputs"] += ["created_ref_oid", "base_oid"]
                item["must_be_absent"] = [life.worktree, "registration:" + life.worktree]
                if not life.detached:
                    scope[repo]["local_refs"] = [life.ref]
                    item["must_be_absent"].append(life.ref)
                # Policy and argv both come from the same typed resource action.
            elif kind == "worktree_remove":
                _require(preserved and not removed, "COMPILER_INVARIANT_FAILURE", "retirement needs prior portable preservation")
                argv = ["git", "-C", life.repository_path, "worktree", "remove", life.worktree]
                item["required_readback_before_effect"] = {
                    "worktree_list_argv": ["git", "-C", life.repository_path, "worktree", "list", "--porcelain"],
                    "head_argv": ["git", "-C", life.worktree, "rev-parse", "HEAD"],
                    "status_argv": ["git", "-C", life.worktree, "status", "--porcelain", "--untracked-files=all", "--ignored"],
                    "attached_ref": None if life.detached else life.ref,
                    "exact_path": life.worktree, "state_required": life.state_required,
                    "preserved_result": result_head, "require_head_equals_preserved_result": bool(result_head),
                    "reject_foreign_content": True}
                item["stage_acceptance_gate"] = "read back path and registration absence; preserved semantic result survives cleanup failure"
                removed = True
            else:
                _require(preserved and removed and absence and
                         not any(data.get("ordered_action_bindings", {}).get(a.source_id, {}).get("resource", "default") == name
                                 for a in actions[actions.index(action) + 1:]),
                         "COMPILER_INVARIANT_FAILURE", "ref deletion requires preservation then worktree removal then absence readback; terminal only")
                item["stage_effect_permissions"]["local_branch_deletion"] = True
                item.update(branch_maintenance_action="delete_exact_temporary_ref",
                            affected_local_branches=[life.ref], expected_preserved_head=result_head or "none: portable result preservation",
                            preservation_ref="none: exact portable result is preserved",
                            reference_restore_source="none: deletion only", non_fast_forward_ref_move_authorized="no",
                            local_branch_deletion="yes", expected_old_oid=result_head or f"stage:{action.stage_id}:pre_delete_ref_oid")
                fresh = _fresh_ref_check(life.repository_path, life.ref, action.stage_id)
                item["runtime_observations"] = [fresh]
                item["stage_outputs"].append("pre_delete_ref_oid")
                item["result_cross_check"] = {"expected": result_head,
                    "observed": fresh["output"], "required": bool(result_head),
                    "on_mismatch": "stop_before_effect; preserve evidence"}
                argv = ["git", "-C", life.repository_path, "update-ref", "-d", life.ref, fresh["output"]]
                item["stage_acceptance_gate"] = "read back exact ref absence and preserved canonical/controller identities"
                if state.get("creation_stage"):
                    item["anchor_noninterference"] = {
                        "ref": life.reference_ref,
                        "readback_argv": ["git", "-C", life.repository_path, "rev-parse", "--verify", life.reference_ref],
                        "compare_to": "stage:" + state["creation_stage"] + ":base_oid",
                        "mismatch": "report noninterference failure; do not roll back"}
            item["safety_critical_argv"] = argv
            item["automatic_retry"] = False
        else:
            _error("IMPLEMENTATION_GAP", "ordered action lacks a bound maintained lowering: " + kind, action.source_line)
        state.update(preserved=preserved, removed=removed, absence=absence, result_head=result_head)
        stages.append(item)
    _require(not any(state["unknown"] for state in states.values()),
             "COMPILER_INVARIANT_FAILURE", "ambiguous workflow ends without readback")
    return stages


def _plan_dependent(data: dict[str, Any], intent: Semantic_intent,
                    effects: tuple[Effect_intent, ...]) -> list[dict[str, Any]]:
    """Consume a preserved tuple; never regenerate a candidate or replay an effect."""
    _require(_multi_repository_roles(intent) and data.get("candidate_pair_order") == ["topcoffea", "topeft"],
             "IMPLEMENTATION_GAP", "continuation needs the bounded provider/consumer behavior")
    state = data.get("accepted_effect_state", {})
    required = {"candidate_heads", "target_heads", "completed_stages", "review_evidence",
                "validation_evidence", "consumer_outcome", "readback_authority_binding"}
    _require(isinstance(state, dict) and set(state) == required and
             set(state["candidate_heads"]) == set(state["target_heads"]) == set(data["repositories"]) and
             all(re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", str(oid)) for mapping in
                 (state["candidate_heads"], state["target_heads"]) for oid in mapping.values()) and
             set(state["completed_stages"]) == {"provider_candidate", "consumer_candidate",
                                                "independent_review", "pair_validation", "integrate_topcoffea"} and
             state["target_heads"]["topcoffea"] == state["candidate_heads"]["topcoffea"] and
             state["review_evidence"] and state["validation_evidence"] and
             state["consumer_outcome"] in {"failed_before_effect", "OUTCOME_UNKNOWN"},
             "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "accepted partial tuple/state is incomplete")
    bindings = _bindings(data)
    binding_id = _exact_related_identity(bindings, "continuation.accepted_effect_state", state,
                                         "topcoffea", "accepted_evidence")
    prior = data["continuation"]["prior_artifact_identity"]
    _require(next(b for b in bindings if b.binding_id == binding_id).source_identity == prior and
             not data.get("automatic_rollback") and not data.get("global_git_transaction") and
             not data.get("automatic_retry"), "COMPILER_INVARIANT_FAILURE", "continuation provenance or no-retry invariant violated")
    c = data["continuation"]
    _require(set(c["checks_not_to_repeat"]) == set(state["completed_stages"]) and
             set(c["delta_scope"]) <= {"readback", "integrate_topeft"} and
             not (set(c["delta_scope"]) & set(c["checks_not_to_repeat"])),
             "NOT_READY_NEW_DECISION_BOUNDARY", "partial continuation protection/delta mismatch")
    readback = next((b for b in bindings if b.binding_id == state["readback_authority_binding"]), None)
    _require(readback is not None and readback.acquisition == "acquired" and
             readback.source_kind == "owner_decision" and _scope_names_repo(readback.validity_scope, "topeft"),
             "NOT_READY_MISSING_AUTHORITY_BINDING", "consumer readback authority missing")
    repo = data["repositories"]["topeft"]
    target = "refs/heads/" + str(repo.get("permanent_target_branch"))
    _require(_safe_local_branch_ref(target), "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "consumer target missing")
    when = next(step for step in intent.steps if step.keyword == "When")
    stage = {"stage_id": "readback", "stage_mode": "validation_only", "repository_id": "topeft",
             "stage_goal": "Read back preserved consumer effect before any remaining action",
             "stage_effect_permissions": {}, "stage_inputs": ["accepted:" + prior, state],
             "stage_acceptance_gate": "exact ref/HEAD/index readback; preserve provider and accepted tuple; unknown remains stopped",
             "stage_outputs": ["readback", "observed_target_head"], "stage_failure_behavior": "stop and preserve; no replay, rollback or blind retry",
             "working_directory": data["prompt"]["repo_locations"]["topeft"],
             "readback_argv": [["git", "rev-parse", "--verify", target], ["git", "rev-parse", "HEAD"],
                               ["git", "diff", "--cached", "--raw"], ["git", "status", "--porcelain"]],
             "generation_provenance": {"role": "readback", "semantic_line": when.line,
                 "rule_source": "governance/contracts/orchestration.md", "evidence_gate": "gate:readback",
                 "provenance_class": "necessary_governance_mechanic"}}
    stages = [stage]
    if state["consumer_outcome"] == "OUTCOME_UNKNOWN":
        _require(not effects, "NOT_READY_MISSING_AUTHORITY_BINDING", "unknown outcome permits readback only, no retry effects")
        return stages
    _require(len(effects) == 1 and effects[0].stage_id == "integrate_topeft" and
             effects[0].effect == "local_git_ref_write" and effects[0].target == target and
             "integrate_topeft" in c["delta_scope"] and
             state["target_heads"]["topeft"] != state["candidate_heads"]["topeft"],
             "NOT_READY_MISSING_AUTHORITY_BINDING", "remaining consumer action needs exact non-replayed local effect")
    stages.append({"stage_id": "integrate_topeft", "stage_mode": "integration_only", "repository_id": "topeft",
        "stage_goal": "Advance only the remaining consumer to its accepted exact candidate",
        "stage_effect_permissions": {"allowed_to_modify": {"topeft": {"local_refs": [target]}}},
        "stage_inputs": ["stage:readback:readback", "accepted:" + prior, state],
        "stage_acceptance_gate": "read back exact consumer candidate head; provider/accepted tuple remain unchanged",
        "stage_outputs": ["observed_target_head"], "stage_failure_behavior": "preserve valid partial state; no rollback or retry",
        "stage_branch_policy": "continue_existing_branch", "target_branch": repo["permanent_target_branch"],
        "integration_source_branch": repo["candidate_branch"], "integration_target_branch": repo["permanent_target_branch"],
        "integration_method": "ff_only", "expected_source_head": state["candidate_heads"]["topeft"],
        "expected_target_head": "stage:readback:observed_target_head",
        "must_pass_before_effects": {"source_head": state["candidate_heads"]["topeft"],
            "target_head": "stage:readback:observed_target_head", "require_fast_forward_ancestry": True,
            "reject_movement_after_readback": True,
            "require_clean_index_and_worktree": True, "candidate_tuple": state["candidate_heads"],
            "validation_evidence": state["validation_evidence"], "review_evidence": state["review_evidence"]},
        "generation_provenance": {"role": "integrate_topeft", "semantic_line": when.line,
            "rule_source": "governance/contracts/git_lifecycle.md", "evidence_gate": "gate:integrate_topeft",
            "provenance_class": "requested_behavior"}})
    return stages


def _plan_controller_local(data: dict[str, Any], intent: Semantic_intent,
                           effects: tuple[Effect_intent, ...]) -> list[dict[str, Any]]:
    """Project a bounded fork/review/commit onto one existing controller carrier."""
    prompt = data["prompt"]
    _require(prompt.get("delegation_policy") == "forbidden" and not data.get("worker_contract") and
             len(data["repositories"]) == 1, "IMPLEMENTATION_GAP",
             "controller-local projection requires one repository and forbidden delegation")
    rows = [row for row in _partition_rows(intent) if row.domain == "structured_action"]
    writers = [row for row in rows if row.ordered_action.kind == "write"]
    joins = [row for row in rows if row.ordered_action.kind == "review_join"]
    commits = [row for row in rows if row.ordered_action.kind == "commit"]
    _require(len(writers) >= 2 and len(joins) == len(commits) == 1 and
             len(rows) == len(writers) + 2, "IMPLEMENTATION_GAP",
             "structured projection requires disjoint writes, one review join and separate commit")
    join, commit = joins[0], commits[0]
    writer_lines = {row.source_line for row in writers}
    _require(set(join.predecessors) == writer_lines and commit.predecessors == (join.source_line,) and
             all(row.successors == (join.source_line,) for row in writers) and
             all(not (set(row.predecessors) & writer_lines) for row in writers),
             "IMPLEMENTATION_GAP", "unsupported structured action dependencies")
    targets = [effect.target for row in writers for effect in row.effects]
    identities = [_tracked_target_identity(target, "NOT_READY_MISSING_AUTHORITY_BINDING")
                  for target in targets]
    _require(_tracked_targets_disjoint(identities),
             "NOT_READY_MISSING_AUTHORITY_BINDING", "independent controller writes overlap")
    repo = next(iter(data["repositories"]))
    location = prompt["repo_locations"][repo]
    refs = {effect.target for effect in commit.effects}
    _require(len(refs) == 1 and _safe_local_branch_ref(next(iter(refs))),
             "NOT_READY_MISSING_AUTHORITY_BINDING", "commit needs exactly one safe bound ref")
    ref = next(iter(refs)); branch = ref.removeprefix("refs/heads/")
    _require(isinstance(location, str) and location.startswith("/") and
             data["repositories"][repo].get("path", location) == location and
             prompt.get("target_branch", branch) == branch,
             "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "controller carrier differs from bound repository/ref")
    steps = {step.line: step for step in intent.steps}
    _require(all(row.predecessors and all(steps[line].keyword == "Given" for line in row.predecessors)
                 for row in writers) and commit.successors and
             all(steps[line].keyword == "Then" for line in commit.successors) and len(commit.effects) == 1,
             "IMPLEMENTATION_GAP", "structured fork needs premise inputs and a terminal commit result")
    by_line = {row.source_line: row for row in rows}
    outputs = {row.source_line: ("frozen_postimages" if row in writers else
               "reviewed_union" if row is join else "observed_commit_head") for row in rows}
    schedule = sorted(writers, key=lambda row: row.source_line) + [join, commit]
    stages = []
    for row in schedule:
        sid = row.owners[0]; kind = row.ordered_action.kind
        inputs = ["stage:" + by_line[line].owners[0] + ":" + outputs[line]
                  for line in row.predecessors if line in by_line]
        paths = sorted(effect.target for effect in row.effects) if kind == "write" else sorted(targets)
        scope = {repo: {"tracked_paths": paths}} if kind == "write" else {
            repo: {"git_index_entries": paths, "local_refs": [ref],
                   "git_effects": ["create_one_prompt_local_commit"]}}
        item = {"stage_id": sid, "stage_mode": "coding" if kind == "write" else
                "validation_only" if kind == "review_join" else "commit_preparation",
                "stage_goal": steps[row.source_line].text,
                "stage_effect_permissions": {} if kind == "review_join" else {"allowed_to_modify": scope},
                "stage_inputs": inputs, "stage_outputs": [outputs[row.source_line]],
                "stage_acceptance_gate": ("Freeze exact owned postimages and review this requested outcome independently."
                    if kind == "write" else "Review every predecessor independently; accept only the exact union; preserve failures."
                    if kind == "review_join" else "Reopen the accepted union and exact staged diff; commit only those paths; read back commit and master noninterference."),
                "stage_failure_behavior": "stop and preserve state; no retry of an ambiguous effect",
                "stage_branch_policy": "read_only_current_branch" if kind == "review_join" else "continue_existing_branch",
                "repository_id": repo, "working_directory": location,
                "generation_provenance": {"role": sid, "semantic_line": row.source_line,
                    "rule_source": "governance/contracts/review_and_evidence.md" if kind == "review_join" else
                    "governance/contracts/git_lifecycle.md", "evidence_gate": "gate:" + sid,
                    "provenance_class": "requested_behavior"}}
        item["runtime_carrier_readback"] = {
            "working_directory": location, "attached_ref": ref,
            "branch_argv": ["git", "-C", location, "symbolic-ref", "--quiet", "HEAD"],
            "head_argv": ["git", "-C", location, "rev-parse", "HEAD"],
            "require_task_ownership": True, "preserve_foreign_work": True,
            "before_effects": True, "on_mismatch": "stop_before_effect_and_preserve_state"}
        if kind != "review_join":
            item.update(target_branch=branch, authorized_commit_scope={repo: paths},
                explicitly_adopted_inherited_changes="none", foreign_dirty_change_policy="preserve_and_exclude",
                staging_policy="exact_path_only")
        if kind == "write": item["deferred_commit_stage"] = commit.owners[0]
        stages.append(item)
    data["_controller_local_carrier"] = {"repository": repo, "worktree": location, "ref": ref}
    return stages


def _plan_stages(data: dict[str, Any], intent: Semantic_intent, shape: str, effects: tuple[Effect_intent, ...],
                 roles: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    """Build the two bounded dependent patterns; supplied stage prose is inert.

    Historical stage input binds no executable value. Exact identities arrive
    through the typed worker and repository bindings.
    """
    if shape == "orchestrated_workflow" and _parallel_body(intent) != intent:
        body = _parallel_body(intent)
        ordered = _ordered_part(intent)
        body_lines = {s.line for s in body.steps if s.keyword == "When"}
        ordered_stages = _plan_ordered(data, ordered, tuple(e for e in effects if e.requested_by_step not in body_lines))
        body_stages = _plan_stages(data, body, shape, tuple(e for e in effects if e.requested_by_step in body_lines), roles)
        first_line, last_line = min(body_lines), max(body_lines)
        _require(all(s["generation_provenance"]["semantic_line"] < first_line or
                     s["generation_provenance"]["semantic_line"] > last_line for s in ordered_stages),
                 "IMPLEMENTATION_GAP", "lifecycle actions cannot interleave a parallel body")
        prelude = [s for s in ordered_stages if s["generation_provenance"]["semantic_line"] < first_line]
        epilogue = [s for s in ordered_stages if s not in prelude]
        workers = data["worker_contract"]["writers"]
        carriers = {(w["worktree_path"], "refs/heads/" + w["branch"]) for w in workers}
        carriers.add((data["worker_contract"]["composition_worktree_path"],
                      "refs/heads/" + data["worker_contract"]["composition_branch"]))
        for stage in prelude:
            if stage["stage_goal"] == "worktree_create":
                argv = stage["safety_critical_argv"]
                _require((argv[-2], "refs/heads/" + stage.get("feature_branch", "")) in carriers,
                         "NOT_READY_MISSING_AUTHORITY_BINDING", "created carrier is foreign to the parallel body")
        if prelude:
            for stage in body_stages:
                if stage["stage_id"] in {w["stage_id"] for w in workers}:
                    stage["stage_inputs"].append("stage:" + prelude[-1]["stage_id"] + ":readback")
        if epilogue:
            epilogue[0]["stage_inputs"].append("stage:" + body_stages[-1]["stage_id"] + ":" + body_stages[-1]["stage_outputs"][0])
        return prelude + body_stages + epilogue
    if shape == "controller_local_workflow":
        return _plan_controller_local(data, intent, effects)
    if shape == "ordered_workflow":
        return _plan_ordered(data, intent, effects)
    if shape == "dependent_continuation":
        return _plan_dependent(data, intent, effects)
    if shape not in {"orchestrated_workflow", "multi_repository_coordination"}:
        return []
    # Historical stage graphs are accepted only as inert diagnostic references.
    _require("governance/contracts/git_lifecycle.md" in GOVERNANCE and
             "governance/contracts/orchestration.md" in GOVERNANCE,
             "COMPILER_DEFECT", "planner rule owner unavailable")
    prompt = data["prompt"]
    _require(prompt.get("delegation_policy") != "forbidden", "COMPILER_INVARIANT_FAILURE",
             "independent review requires allowed or required delegation")
    prompt["delegation_policy"] = "required"

    def make(stage_id: str, mode: str, goal: str, inputs: list[str], gate: str,
             outputs: list[str], failure: str = "stop and preserve completed effects") -> dict[str, Any]:
        return {"stage_id": stage_id, "stage_mode": mode, "stage_goal": goal,
                "stage_effect_permissions": {}, "stage_inputs": inputs,
                "stage_acceptance_gate": gate, "stage_outputs": outputs,
                "stage_failure_behavior": failure}

    def stage_effects(stage_id: str) -> list[Effect_intent]:
        return [effect for effect in effects if effect.stage_id == stage_id]

    def local_scope(repo_id: str, paths: list[str], branch: str) -> dict[str, Any]:
        return {repo_id: {"tracked_paths": paths, "git_index_entries": paths,
                          "local_refs": ["refs/heads/" + branch],
                          "git_effects": ["create_one_prompt_local_commit"]}}

    stages: list[dict[str, Any]] = []
    if shape == "orchestrated_workflow":
        semantic_roles = _parallel_roles(intent)
        workers = data.get("worker_contract", {})
        writers = workers.get("writers", [])
        _require(len(writers) == 2 and [w.get("stage_id") for w in writers] == ["writer_a", "writer_b"],
                 'IMPLEMENTATION_GAP', "bounded planner supports two named disjoint writers")
        _require(len(data["repositories"]) == 1, 'IMPLEMENTATION_GAP',
                 "parallel writer pattern needs one repository")
        repo_id = next(iter(data["repositories"]))
        accepted_writer = data.get("continuation", {}).get("checks_not_to_repeat", [None])[0]
        accepted_head = (f"prior:{data['continuation']['prior_artifact_identity']}:"
                         f"{accepted_writer}@"
                         f"{data['continuation']['accepted_prior_evidence'][0].get('observed_commit_head', 'frozen_postimages')}") \
            if accepted_writer else ""
        for worker in writers:
            stage_id = worker["stage_id"]
            if stage_id == accepted_writer:
                continue
            branch = worker.get("branch")
            _require(bool(branch and worker.get("worktree_path")), "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
                     f"{stage_id} needs exact existing worker branch/worktree/base identities")
            paths = worker.get("write_paths", [])
            _require(sorted(paths) == sorted(e.target for e in stage_effects(stage_id)
                                                if e.effect == "tracked_write"),
                     "NOT_READY_MISSING_AUTHORITY_BINDING", f"{stage_id} paths lack exact effects")
            commit_requested = any(e.effect == "local_git_ref_write" for e in stage_effects(stage_id))
            _require(commit_requested or ("exact_union" in semantic_roles and
                     any(e.effect == "local_git_ref_write" for e in stage_effects("exact_union"))),
                     "NOT_READY_MISSING_AUTHORITY_BINDING", "uncommitted writer lacks controller commit closure")
            item = make(stage_id, "coding", f"Write {'and commit ' if commit_requested else ''}{stage_id} owned paths",
                        [f"worktree:{worker['worktree_path']}",
                         "fresh branch/HEAD/index readback; record base in frozen result provenance"],
                        "reopen exact diff, commit and frozen postimages", ["observed_commit_head", "frozen_postimages"])
            item.update(stage_branch_policy="continue_existing_branch", target_branch=branch,
                        authorized_commit_scope={repo_id: paths}, explicitly_adopted_inherited_changes="none",
                        foreign_dirty_change_policy="preserve_and_exclude", staging_policy="exact_path_only")
            item["stage_effect_permissions"] = {"allowed_to_modify": local_scope(repo_id, paths, branch)}
            if not commit_requested:
                item["stage_effect_permissions"] = {"allowed_to_modify": {repo_id: {"tracked_paths": paths}}}
                item["stage_outputs"] = ["frozen_postimages"]
                item["stage_acceptance_gate"] = "freeze exact base, full postimages and content hashes; preserve uncommitted result for controller closure"
                item["deferred_commit_stage"] = "exact_union"
            item["runtime_carrier_readback"] = {
                "working_directory": worker["worktree_path"], "attached_ref": "refs/heads/" + branch,
                "branch_argv": ["git", "-C", worker["worktree_path"], "symbolic-ref", "--quiet", "HEAD"],
                "head_argv": ["git", "-C", worker["worktree_path"], "rev-parse", "HEAD"],
                "require_task_ownership": True, "preserve_foreign_work": True,
                "record_result_base_provenance": True}
            stages.append(item)
        writer_inputs = [accepted_head if worker["stage_id"] == accepted_writer else
                         f"stage:{worker['stage_id']}:" + (
                             "observed_commit_head" if any(e.effect == "local_git_ref_write" and
                             e.stage_id == worker["stage_id"] for e in effects) else "frozen_postimages")
                         for worker in writers]
        stages.append(make("independent_review", "validation_only", "Independently review frozen writer results",
                           writer_inputs,
                           "independent reviewer findings disposed", ["review_evidence"]))
        if "exact_union" in semantic_roles:
            union_paths = sorted(workers.get("union_paths", []))
            composition_branch = workers.get("composition_branch")
            _require(bool(workers.get("composition_worktree_path")),
                     "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "composition carrier identity missing")
            _require(bool(composition_branch) and sorted(union_paths) ==
                     sorted(e.target for e in stage_effects("exact_union") if e.effect == "tracked_write"),
                     "NOT_READY_MISSING_AUTHORITY_BINDING", "exact union needs bound composition branch and write effects")
            item = make("exact_union", "coding", "Compose exact frozen byte union and commit controller candidate",
                        [*writer_inputs,
                         "stage:independent_review:review_evidence",
                         "exact union consumes frozen result bases/postimages; fresh controller readback",
                         f"worktree:{workers['composition_worktree_path']}"],
                        "exact byte union, independent combined semantic review and committed candidate readback",
                        ["observed_commit_head", "union_postimages", "combined_review_evidence"])
            item.update(stage_branch_policy="continue_existing_branch", target_branch=composition_branch,
                        authorized_commit_scope={repo_id: union_paths}, explicitly_adopted_inherited_changes="none",
                        foreign_dirty_change_policy="preserve_and_exclude", staging_policy="exact_path_only")
            item["stage_effect_permissions"] = {"allowed_to_modify": local_scope(repo_id, union_paths, composition_branch)}
            item["runtime_carrier_readback"] = {
                "working_directory": workers["composition_worktree_path"],
                "attached_ref": "refs/heads/" + composition_branch,
                "require_task_ownership": True, "preserve_foreign_work": True,
                "consume_exact_frozen_result_bases_and_postimages": True}
            stages.append(item)
            stages.append(make("reconciled_review", "validation_only",
                               "Review any controller rewrite of worker postimages",
                               ["stage:exact_union:union_postimages"],
                               "if a worker postimage changed, independent review and validation of that surface pass",
                               ["reconciled_review_evidence"]))
        if _composition_dependencies(intent):
            contract = data["common_validation_contract"]
            _require(isinstance(contract, dict) and set(contract) ==
                     {"test_target", "target"} and
                     all(isinstance(value, str) and value.strip() for value in contract.values()),
                     'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE', "common validation contract is not exact")
            _require(bool(re.fullmatch(r"tests/(?!.*\.\.)[A-Za-z0-9_./-]+\.py(?:::test_[A-Za-z0-9_]+)?",
                                       contract["test_target"])),
                     'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE', "common validation needs a bounded named test target")
            _require(contract["target"] == workers.get("composition_branch"),
                     'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE', "common validation target is not composed candidate")
            stages.append(make("common_validation", "validation_only",
                               "Run bound targeted unit test through resolved wrapper and interpreter",
                               ["stage:exact_union:observed_commit_head", "stage:reconciled_review:reconciled_review_evidence",
                                f"target:{contract['target']}"],
                               "must_pass: exact test target succeeds on the observed controller candidate head; "
                               "missing, unreadable, failed, or mismatched result stops dependent stages",
                               ["common_validation_evidence"]))
            stages[-1].update(validation_test_target=contract["test_target"],
                              stage_branch_policy="continue_existing_branch",
                              target_branch=composition_branch,
                              validation_worktree=workers["composition_worktree_path"],
                              expected_candidate_head="stage:exact_union:observed_commit_head")
        if "integration" in semantic_roles:
            integration_effect = stage_effects("integration")
            target = workers.get("integration_target_branch")
            _require(len(integration_effect) == 1 and integration_effect[0].effect == "local_git_ref_write" and
                     integration_effect[0].target == "refs/heads/" + str(target),
                     "NOT_READY_MISSING_AUTHORITY_BINDING", "integration needs exact target ref effect")
            integration_inputs = ["stage:exact_union:observed_commit_head",
                                  "stage:reconciled_review:reconciled_review_evidence"]
            if _composition_dependencies(intent):
                integration_inputs.append("stage:common_validation:common_validation_evidence")
            item = make("integration", "integration_only", "Integrate committed controller candidate",
                        integration_inputs,
                        "source and target readback match the authorized fast-forward", ["observed_target_head"])
            item.update(stage_branch_policy="continue_existing_branch", target_branch=target,
                        integration_source_branch=composition_branch, integration_target_branch=target,
                        integration_method="ff_only", expected_source_head="stage:exact_union:observed_commit_head")
            item["stage_effect_permissions"] = {"allowed_to_modify": {repo_id: {
                "git_index_entries": union_paths, "local_refs": [integration_effect[0].target],
                "git_effects": ["integrate_exact_source"]}}}
            stages.append(item)
        if "retirement" in semantic_roles:
            life = data.get("retirement", {})
            _require(life.get("exact_owned_surface") and life.get("preservation_ref"),
                     "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "retirement identity/preservation inputs missing")
            _require(_safe_local_branch_ref(life["exact_owned_surface"]) and
                     _safe_local_branch_ref(life["preservation_ref"]),
                     'COMPILER_INVARIANT_FAILURE', "unsafe retirement or preservation ref grammar")
            item = make("retirement", "branch_maintenance_only", "Retire exact owned temporary ref",
                        [f"stage:{stages[-1]['stage_id']}:{stages[-1]['stage_outputs'][0]}", "portable preservation evidence",
                         "reopened semantic and review gates"],
                        "exact old-OID compare-and-delete and ref/worktree readback",
                        ["retirement_readback", "pre_delete_ref_oid"])
            item.update(stage_branch_policy="continue_existing_branch", target_branch=workers["integration_target_branch"],
                        branch_maintenance_action="delete_exact_temporary_ref",
                        affected_local_branches=[life["exact_owned_surface"]],
                        expected_preserved_head="none: portable result preservation; record observed ref as evidence",
                        preservation_ref=life["preservation_ref"], reference_restore_source="none: deletion only",
                        non_fast_forward_ref_move_authorized="no", local_branch_deletion="yes",
                        remote_branch_deletion="no", expected_old_oid="stage:retirement:pre_delete_ref_oid",
                        runtime_observations=[_fresh_ref_check(
                            prompt["repo_locations"][repo_id], life["exact_owned_surface"], "retirement")],
                        safety_critical_argv=["git", "update-ref", "-d", life["exact_owned_surface"],
                                              "stage:retirement:pre_delete_ref_oid"],
                        safety_critical_ref_command=("git update-ref -d " + life["exact_owned_surface"] +
                                                     " stage:retirement:pre_delete_ref_oid"))
            item["stage_effect_permissions"] = {"allowed_to_modify": {repo_id: {
                "local_refs": [life["exact_owned_surface"]], "git_effects": ["delete_exact_temporary_ref"]}},
                                                "local_branch_deletion": "yes"}
            stages.append(item)
    else:
        integration_roles = _multi_repository_roles(intent)
        _require(not data.get("integration_stages") or
                 data["integration_stages"] == list(integration_roles),
                 "NOT_READY_NEW_DECISION_BOUNDARY",
                 "supplied integration roles disagree with requested provider/consumer behavior")
        data["integration_stages"] = list(integration_roles)
        _require(data.get("multi_repository_state") == "NOT_STARTED",
                 'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE',
                 "partial or completed multi-repository state needs a separately bound recovery/continuation plan")
        _require(prompt.get("validation_ceiling") == "targeted_unit_test",
                 'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE', "candidate-pair validation needs targeted_unit_test ceiling")
        repo_ids = data.get("candidate_pair_order")
        _require(repo_ids == ["topcoffea", "topeft"] and set(repo_ids) == set(data["repositories"]),
                 'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE', "bounded provider/consumer plan needs exact ordered pair")
        for position, repo_id in enumerate(repo_ids):
            stage_id = ("provider_candidate", "consumer_candidate")[position]
            role = roles.get(repo_id)
            _require(role is not None, 'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE', "candidate repository needs native module")
            repo = data["repositories"][repo_id]
            live_branch = role["permanent_live_development_branch"]
            branch = repo.get("candidate_branch", "")
            namespace = role["feature_development_namespace"].removesuffix("*")
            _require(repo.get("development_branch") == live_branch and repo.get("stage_id") == stage_id,
                     "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", f"{repo_id} live branch identity mismatch")
            _require(repo.get("candidate") == f"stage:{stage_id}:observed_commit_head",
                     "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
                     f"{repo_id} needs exact base and derived observed candidate binding")
            _require(branch.startswith(namespace) and branch != live_branch and
                     bool(branch[len(namespace):]) and repo.get("candidate_worktree") and
                     repo.get("candidate_carrier_authority_binding"),
                     'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE',
                     f"{repo_id} lacks an authorized native candidate carrier")
            paths = [e.target for e in stage_effects(stage_id) if e.effect == "tracked_write"]
            _require(bool(paths), "NOT_READY_MISSING_AUTHORITY_BINDING", f"{repo_id} candidate lacks tracked effect")
            item = make(stage_id, "coding", f"Write and commit {repo_id} candidate",
                        [f"{repo_id} observed live base {repo.get('base')}",
                         f"candidate worktree:{repo['candidate_worktree']}",
                         "fresh candidate branch/HEAD/index readback", "native policy"],
                        "reopen local commit, task diff and native-policy evidence", ["observed_commit_head"])
            item.update(repository_id=repo_id, stage_branch_policy="continue_existing_branch", target_branch=branch,
                        candidate_worktree=repo["candidate_worktree"],
                        runtime_carrier_readback={"worktree": repo["candidate_worktree"], "attached_branch": branch,
                            "record": ["head", "base_oid"], "require_task_owned_clean_carrier": True},
                        authorized_commit_scope={repo_id: paths}, explicitly_adopted_inherited_changes="none",
                        foreign_dirty_change_policy="preserve_and_exclude", staging_policy="exact_path_only")
            item["stage_effect_permissions"] = {"allowed_to_modify": local_scope(repo_id, paths, branch)}
            stages.append(item)
        stages.append(make("independent_review", "validation_only", "Independently review both committed candidates",
                           ["stage:provider_candidate:observed_commit_head",
                            "stage:consumer_candidate:observed_commit_head"],
                           "repo-local and cross-repository findings disposed", ["review_evidence"]))
        stages.append(make("pair_validation", "validation_only", "Validate exact observed candidate tuple",
                           ["stage:provider_candidate:observed_commit_head",
                            "stage:consumer_candidate:observed_commit_head",
                            "stage:independent_review:review_evidence"],
                           "must_pass: exact provider, consumer and common contract succeeds on both observed candidate heads; "
                           "missing, failed, unreadable or irrelevant evidence stops candidate-pair readiness",
                           ["candidate_pair_evidence"]))
        stages[-1]["validation_locator"] = data.get("pair_validation_contract", {}).get("test_target")
        stages[-1]["candidate_posture"] = {repo_id: {
            "worktree": data["repositories"][repo_id]["candidate_worktree"],
            "branch": data["repositories"][repo_id]["candidate_branch"],
            "head": f"stage:{('provider_candidate', 'consumer_candidate')[position]}:observed_commit_head"}
            for position, repo_id in enumerate(repo_ids)}
        prompt["candidate_pair"] = {repo_id: data["repositories"][repo_id]["candidate"]
                                    for repo_id in repo_ids}
        for repo_id, stage_id in zip(repo_ids, integration_roles):
            repo = data["repositories"][repo_id]
            target = repo.get("permanent_target_branch")
            _require(target == repo["development_branch"] and
                     target != repo["candidate_branch"],
                     "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
                     f"{repo_id} permanent target must be the distinct native live branch")
            local_effects = stage_effects(stage_id)
            _require(len(local_effects) == 1 and local_effects[0].effect == "local_git_ref_write" and
                     local_effects[0].target == "refs/heads/" + target,
                     "NOT_READY_MISSING_AUTHORITY_BINDING",
                     f"{repo_id} permanent advancement needs its own exact ref effect")
            paths = [e.target for e in stage_effects(repo["stage_id"]) if e.effect == "tracked_write"]
            inputs = [repo["candidate"], "stage:pair_validation:candidate_pair_evidence",
                      "stage:independent_review:review_evidence"]
            if repo_id != repo_ids[0]:
                inputs.append(f"stage:{integration_roles[0]}:observed_target_head")
            item = make(stage_id, "integration_only", f"Permanently advance {repo_id} native live target",
                        inputs, "reopen exact source/target and observed fast-forward result; preserve evidence",
                        ["observed_target_head", "preserved_candidate_and_effect_evidence"],
                        "stop downstream effects; preserve observed advancements and all candidate/evidence states; "
                        "no automatic rollback or retry; an ambiguous effect requires authoritative readback "
                        "before a separately authorized retry decision")
            item.update(repository_id=repo_id, stage_branch_policy="continue_existing_branch",
                        target_branch=target, integration_source_branch=repo["candidate_branch"],
                        integration_target_branch=target, integration_method="ff_only",
                        expected_source_head=repo["candidate"], expected_target_head=f"stage:{stage_id}:pre_effect_target_oid",
                        integration_worktree=prompt["repo_locations"][repo_id],
                        must_pass_before_effects={
                            "candidate_tuple": dict(prompt["candidate_pair"]),
                            "pair_validation_evidence": "stage:pair_validation:candidate_pair_evidence",
                            "review_evidence": "stage:independent_review:review_evidence",
                            "source_ref": "refs/heads/" + repo["candidate_branch"],
                            "source_head": repo["candidate"], "target_ref": "refs/heads/" + target,
                            "target_head": f"stage:{stage_id}:pre_effect_target_oid", "require_clean_index_and_worktree": True,
                            "fresh_target_readback": ["git", "rev-parse", "--verify", "refs/heads/" + target],
                            "reject_movement_after_readback": True,
                            "require_fast_forward_ancestry": True,
                            "on_mismatch": "stop_before_effect_and_preserve_state"},
                        failure_outcomes={
                            "failed_before_effect": "preserve prior effects and candidate evidence; stop downstream",
                            "observed_effect": "preserve exact repo-local advancement and candidate evidence",
                            "OUTCOME_UNKNOWN": "stop; authoritative repo-local ref/index/worktree readback "
                            "before any separately authorized recovery; never infer no effect"})
            item["runtime_observations"] = [{
                "output": f"stage:{stage_id}:pre_effect_target_oid",
                "argv": item["must_pass_before_effects"]["fresh_target_readback"],
                "before_effect": True, "require_exit_zero": True, "require_full_oid": True}]
            item["stage_outputs"].append("pre_effect_target_oid")
            item["stage_effect_permissions"] = {"allowed_to_modify": {repo_id: {
                "git_index_entries": paths, "local_refs": [local_effects[0].target],
                "git_effects": ["integrate_exact_source"]}}}
            stages.append(item)
    _require({e.stage_id for e in effects} <= {s["stage_id"] for s in stages},
             'COMPILER_INVARIANT_FAILURE', "effect targets an unsupported stage role")
    when = next(step for step in intent.steps if step.keyword == "When")
    then = next(step for step in intent.steps if step.keyword == "Then")
    for item in stages:
        role = item["stage_id"]
        semantic_action = _parallel_action_steps(intent).get(role, when)
        rule = ("governance/contracts/git_lifecycle.md" if item["stage_mode"] in
                {"coding", "integration_only", "branch_maintenance_only"} else
                "governance/contracts/review_and_evidence.md")
        item["generation_provenance"] = {
            "role": role, "semantic_line": semantic_action.line if item["stage_mode"] in
            {"coding", "integration_only", "branch_maintenance_only"} else then.line,
            "rule_source": rule, "evidence_gate": "gate:" + role,
            "provenance_class": ("necessary_governance_mechanic" if role in
                                 {"independent_review", "reconciled_review", "common_validation"}
                                 else "requested_behavior")}
    return stages


def _stage_trace(data: dict[str, Any], intent: Semantic_intent,
                 effects: tuple[Effect_intent, ...], shape: str) -> list[Trace_edge]:
    stages = data.get("stages", [])
    if shape not in {"orchestrated_workflow", "multi_repository_coordination", "ordered_workflow", "dependent_continuation", "controller_local_workflow"}:
        _require(not stages and not data.get("worker_contract"), "COMPILER_INVARIANT_FAILURE",
                 "caller stages are not a compiler-selected minimum-sufficient workflow")
        return []
    _require(bool(stages), "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
             "semantic workflow needs bound stage details")
    when = next((step for step in intent.steps if step.keyword == "When"), None)
    then = next((step for step in intent.steps if step.keyword == "Then"), None)
    _require(when is not None and then is not None, "COMPILER_INVARIANT_FAILURE",
             "workflow needs action and observable result")
    if shape == "controller_local_workflow":
        rows = [row for row in _partition_rows(intent) if row.domain == "structured_action"]
        expected = [row.owners[0] for row in sorted(rows, key=lambda row: (
            {"write": 0, "review_join": 1, "commit": 2}[row.ordered_action.kind], row.source_line))]
        by_line = {row.source_line: row for row in rows}
        graph = data["_result_graph"]
        for row in rows:
            _require(graph.predecessors(row.owners[0]) == {
                by_line[line].owners[0] for line in row.predecessors if line in by_line},
                "COMPILER_INVARIANT_FAILURE", "physical schedule changed semantic dependencies")
    elif shape == "dependent_continuation":
        expected = ['readback'] + ([] if data['accepted_effect_state']['consumer_outcome'] == 'OUTCOME_UNKNOWN'
                                   else ['integrate_topeft'])
        _require(not data.get('automatic_retry') and not data.get('automatic_rollback'),
                 'COMPILER_INVARIANT_FAILURE', 'dependent continuation invents retry or rollback')
        if data['accepted_effect_state']['consumer_outcome'] == 'OUTCOME_UNKNOWN':
            _require(not effects, 'COMPILER_INVARIANT_FAILURE', 'unknown outcome is readback only')
        else:
            accepted = data['accepted_effect_state']
            remaining = stages[-1]
            guard = remaining.get('must_pass_before_effects', {})
            source = accepted['candidate_heads']['topeft']
            _require(remaining.get('expected_source_head') == source and
                     guard.get('source_head') == source and
                     remaining.get('integration_source_branch') == data['repositories']['topeft']['candidate_branch'] and
                     remaining.get('integration_target_branch') == data['repositories']['topeft']['permanent_target_branch'] and
                     guard.get('candidate_tuple') == accepted['candidate_heads'] and
                     guard.get('validation_evidence') == accepted['validation_evidence'] and
                     guard.get('review_evidence') == accepted['review_evidence'] and
                     guard.get('require_fast_forward_ancestry') is True and
                     guard.get('require_clean_index_and_worktree') is True and
                     guard.get('reject_movement_after_readback') is True,
                     'COMPILER_INVARIANT_FAILURE', 'remaining integration differs from accepted exact source/tuple/gates')
    elif shape == "ordered_workflow":
        expected = [action.stage_id for action in _ordered_actions(intent)]
    elif shape == "orchestrated_workflow":
        _require(bool(re.search(r"\b(review|validat|union)\w*\b", then.text, re.I)),
                 "COMPILER_INVARIANT_FAILURE", "review stages lack observable Then behavior")
        workers = data["worker_contract"]
        protected = data.get("continuation", {}).get("checks_not_to_repeat", [])
        expected = [role for role in _parallel_roles(intent) if role not in protected]
        if _parallel_body(intent) != intent:
            ordered = _ordered_actions(_ordered_part(intent))
            first = min(row.source_line for row in _partition_rows(intent)
                        if row.domain == 'parallel_worker_or_join')
            expected = ([a.stage_id for a in ordered if a.source_line < first] + expected +
                        [a.stage_id for a in ordered if a.source_line > first])
    else:
        _require("pair" in then.text.lower() and "validat" in then.text.lower(),
                 "COMPILER_INVARIANT_FAILURE", "candidate-pair stage lacks observable Then behavior")
        expected = [data["repositories"][repo_id].get("stage_id")
                    for repo_id in data["candidate_pair_order"]]
        expected += ["independent_review", data.get("candidate_pair_validation_stage")]
        expected += list(_multi_repository_roles(intent))
    actual = [stage.get("stage_id") for stage in stages]
    _require(actual == expected and all(expected) and len(set(expected)) == len(expected),
             "COMPILER_INVARIANT_FAILURE", "supplied stages differ from semantic minimum-sufficient plan")
    if shape == 'ordered_workflow' or (shape == 'orchestrated_workflow' and _parallel_body(intent) != intent):
        ordered_intent = intent if shape == 'ordered_workflow' else _ordered_part(intent)
        try:
            verify_ordered_invariants(stages, _ordered_actions(ordered_intent),
                                      _partition_rows(ordered_intent),
                                      data.get('lifecycle_resources') or {'default': data['lifecycle_contract']},
                                      data.get('ordered_action_bindings', {}))
        except ValueError as exc:
            _error('COMPILER_INVARIANT_FAILURE', str(exc))
    if shape == "multi_repository_coordination":
        for position, stage_id in enumerate(_multi_repository_roles(intent)):
            stage = next(s for s in stages if s["stage_id"] == stage_id)
            repo_id = data["candidate_pair_order"][position]
            repo = data["repositories"][repo_id]
            required = {repo["candidate"], "stage:pair_validation:candidate_pair_evidence",
                        "stage:independent_review:review_evidence"}
            if position:
                required.add(f"stage:{_multi_repository_roles(intent)[position - 1]}:observed_target_head")
            _require(required <= set(stage["stage_inputs"]) and
                     actual.index("pair_validation") < actual.index(stage_id) and
                     stage["expected_source_head"] == repo["candidate"] and
                     stage["must_pass_before_effects"]["candidate_tuple"] == data["prompt"]["candidate_pair"],
                     "COMPILER_INVARIANT_FAILURE", "permanent advancement lacks exact tuple/review dependencies")
    if _composition_dependencies(intent):
        validation = next(stage for stage in stages if stage["stage_id"] == "common_validation")
        _require(actual.index('exact_union') < actual.index('common_validation') and
                 'stage:exact_union:observed_commit_head' in validation['stage_inputs'],
                 'COMPILER_INVARIANT_FAILURE', 'common validation lacks exact composed result')
        if 'integration' in _parallel_roles(intent):
            integration = next(stage for stage in stages if stage["stage_id"] == "integration")
            _require(actual.index('common_validation') < actual.index('integration') and
                     'stage:common_validation:common_validation_evidence' in integration['stage_inputs'],
                     'COMPILER_INVARIANT_FAILURE', 'integration lacks the candidate validation dependency')
    edges = list(_composition_dependencies(intent))
    for stage in stages:
        stage_id = stage["stage_id"]
        provenance = stage.get("generation_provenance", {})
        _require(provenance.get("role") == stage_id and
                 provenance.get("semantic_line") in {s.line for s in intent.steps if s.keyword in {"When", "Then"}} and
                 provenance.get("rule_source") in GOVERNANCE and
                 provenance.get("evidence_gate") == "gate:" + stage_id and
                 provenance.get("provenance_class") in
                 {"requested_behavior", "necessary_governance_mechanic"},
                 "COMPILER_INVARIANT_FAILURE", f"stage {stage_id} lacks valid generation provenance")
        source = f"line:{provenance['semantic_line']}"
        edges.append(Trace_edge(source, f"stage:{stage_id}", "generated_from"))
        edges.append(Trace_edge("governance:" + provenance["rule_source"],
                                f"stage:{stage_id}", "governed_by"))
        related_effects = [effect for effect in effects if effect.stage_id == stage_id]
        if not related_effects:
            _require(stage.get("stage_mode") in {"investigation_only", "validation_only"} and
                     stage.get("stage_effect_permissions") == {}, "COMPILER_INVARIANT_FAILURE",
                     f"stage {stage_id} has unrequested executable mechanics")
        if related_effects:
            edges.extend(Trace_edge(f"effect:{effect.effect_id}", f"stage:{stage_id}", "implemented_by")
                         for effect in related_effects)
        elif shape in {"ordered_workflow", "dependent_continuation", "controller_local_workflow"} or (shape == "orchestrated_workflow" and stage_id not in _parallel_roles(intent)):
            edges.append(Trace_edge(source, f"stage:{stage_id}", "requires_validation_stage"))
        elif stage_id in {"independent_review", "common_validation", data.get("candidate_pair_validation_stage"),
                          data.get("worker_contract", {}).get("independent_review_stage"),
                          data.get("worker_contract", {}).get("exact_union_stage")}:
            edges.append(Trace_edge(f"line:{then.line}", f"stage:{stage_id}", "requires_validation_stage"))
        elif stage_id == data.get("worker_contract", {}).get("conditional_reconciled_review_stage"):
            edges.append(Trace_edge("governance:orchestration_reconciled_review", f"stage:{stage_id}",
                                    "required_safety_gate"))
        elif stage_id in data.get("integration_stages", []):
            _error("NOT_READY_MISSING_AUTHORITY_BINDING",
                   f"integration stage {stage_id} lacks a requested local ref effect")
        else:
            _error("COMPILER_INVARIANT_FAILURE", f"stage {stage_id} has no semantic or governance reason")
        edges.append(Trace_edge(f"stage:{stage_id}", f"prompt:workflow_stages:{stage_id}", "serialized_as"))
        edges.append(Trace_edge(f"stage:{stage_id}", f"gate:{stage_id}", "requires_objective_gate"))
        edges.append(Trace_edge(f"gate:{stage_id}", f"evidence:stage:{stage_id}", "requires_readback"))
        for field_name in ("stage_mode", "stage_branch_policy", "integration_method",
                           "branch_maintenance_action"):
            if field_name in stage:
                edges.append(Trace_edge(f"stage:{stage_id}",
                                        f"prompt:workflow_stages:{stage_id}.{field_name}", "constrains_stage"))
        for field_name in stage.keys() - STAGE_CORE - {"generation_provenance"}:
            edges.append(Trace_edge("governance:" + provenance["rule_source"],
                                    f"prompt:workflow_stages:{stage_id}.{field_name}", "requires_field"))
        for effect in related_effects:
            edges.append(Trace_edge(f"effect:{effect.effect_id}",
                                    f"prompt:workflow_stages:{stage_id}.stage_effect_permissions",
                                    "granted_at_stage"))
        for key in stage["stage_effect_permissions"]:
            edges.append(Trace_edge(f"stage:{stage_id}", f"grant:{stage_id}:{key}", "generated_grant"))
            edges.append(Trace_edge(f"grant:{stage_id}:{key}",
                                    f"prompt:workflow_stages:{stage_id}.stage_effect_permissions.{key}",
                                    "serialized_as"))
    return edges


def _trace_complete(intent: Semantic_intent, effects: tuple[Effect_intent, ...],
                    stages: list[dict[str, Any]], edges: list[Trace_edge],
                    assertion_paths: list[tuple[int, int, str]],
                    required_relations: list[tuple[str, str]],
                    isolation_roles: list[str]) -> bool:
    pairs = {(edge.source, edge.output) for edge in edges}
    provenance = {(edge.source, edge.output) for edge in edges if edge.relation == "generated_from"}
    relation_nodes = {edge.output for edge in edges if edge.relation == "observes_exact_relation"}
    relation_complete = all(
        any(node.startswith(f"identity:{path}=") and (node, f"stage:{stage_id}") in pairs
            for node in relation_nodes)
        for path, stage_id in required_relations)
    validation_relation = next((node for node in relation_nodes if node.startswith(
        "identity:common_validation.target_relation=")), None)
    if any(path == "common_validation.target_relation" for path, _ in required_relations):
        then_line = next(step.line for step in intent.steps if step.keyword == "Then")
        relation_complete = relation_complete and validation_relation is not None and \
            (f"line:{then_line}", validation_relation) in pairs and \
            (validation_relation, "gate:common_validation") in pairs
    isolation_complete = not isolation_roles or (
        ("governance:governance/contracts/orchestration.md",
         "verification:cross_role_isolation") in pairs and
        all((f"carrier:{role}", "verification:cross_role_isolation") in pairs
            for role in isolation_roles))
    return (relation_complete and isolation_complete and
            all((f"line:{step.line}", "semantic_intent") in pairs for step in intent.steps) and
            all((f"line:{step.line}", f"precondition_evidence:line:{step.line}") in pairs
                and (any(source == f"precondition_evidence:line:{step.line}" and
                         (target.startswith("binding:") or target.startswith("documentary_given:") or
                          target.startswith("plan_bound_given:") or
                          target.startswith("gate:given:"))
                         for source, target in pairs))
                for step in intent.steps if step.keyword == "Given") and
            all((f"line:{step.line}", f"evidence_requirement:line:{step.line}") in pairs
                and (f"evidence_requirement:line:{step.line}", f"acceptance_assertion:line:{step.line}") in pairs
                and (f"evidence_requirement:line:{step.line}", "evaluation_path:external_evidence_review") in pairs
                and any(source == f"acceptance_assertion:line:{step.line}" and
                        (target.startswith("gate:") or target == "prompt:validation_ceiling")
                        for source, target in pairs)
                for step in intent.steps if step.keyword == "Then") and
            all((f"line:{line}", f"assertion:{line}:{index}") in pairs and
                (f"assertion:{line}:{index}", gate) in pairs and
                (gate, f"evidence:assertion:{line}:{index}") in pairs
                for line, index, gate in assertion_paths) and
            all((f"line:{step.line}", f"constraint:line:{step.line}") in pairs and
                ("governance:AGENTS.md", f"constraint:line:{step.line}") in pairs
                for step in intent.steps if step.keyword == "Then" and
                step.text in intent.negative_assertions) and
            all((f"line:{step.line}", "prompt:prompt_mode") in pairs
                for step in intent.steps if step.keyword == "When") and
            all((f"line:{effect.requested_by_step}", f"effect:{effect.effect_id}") in pairs and
                (f"binding:{effect.positive_authority_binding}", f"effect:{effect.effect_id}") in pairs and
                (f"effect:{effect.effect_id}", "prompt:allowed_to_modify") in pairs and
                (not stages or (f"effect:{effect.effect_id}", f"stage:{effect.stage_id}") in pairs)
                for effect in effects) and
            all(any(edge.output == f"stage:{stage['stage_id']}" for edge in edges) and
                any(output == f"stage:{stage['stage_id']}" and
                    (source.startswith("line:") or source.startswith("governance:"))
                    for source, output in provenance) and
                any(edge.source.startswith("governance:") and edge.output == f"stage:{stage['stage_id']}"
                    and edge.relation == "governed_by" for edge in edges) and
                (f"stage:{stage['stage_id']}", f"prompt:workflow_stages:{stage['stage_id']}") in pairs and
                (f"stage:{stage['stage_id']}", f"prompt:workflow_stages:{stage['stage_id']}.stage_mode") in pairs
                and (f"stage:{stage['stage_id']}", f"gate:{stage['stage_id']}") in pairs
                and all((f"stage:{stage['stage_id']}", f"grant:{stage['stage_id']}:{key}") in pairs
                        for key in stage["stage_effect_permissions"])
                for stage in stages) and
            ("semantic_intent", "prompt:prompt_mode") in pairs)


def _declared_grant(effect: Effect_intent, prompt: dict[str, Any], stages: list[dict[str, Any]]) -> bool:
    key = EFFECT_KEYS[effect.effect]
    if stages:
        stage = next((stage for stage in stages if stage.get("stage_id") == effect.stage_id), None)
        if stage is None:
            return False
        grants = stage.get("stage_effect_permissions", {})
    else:
        grants = prompt.get("heavy_command_permissions", {})
    if key == "allowed_to_modify":
        return _scope_contains(grants.get(key, {}), effect.target)
    if effect.effect in {"delete_local_branch", "delete_remote_branch"}:
        return (grants.get(key) is True or grants.get(key) == "yes") and _scope_contains(
            grants.get("allowed_to_modify", {}), effect.target)
    return grants.get(key) is True or grants.get(key) == "yes"


def _scope_contains(scope: Any, target: str) -> bool:
    if isinstance(scope, dict):
        return any(_scope_contains(item, target) for item in scope.values())
    if isinstance(scope, list):
        return any(_scope_contains(item, target) for item in scope)
    return scope == target


def _positive_keys(grants: dict[str, Any]) -> set[str]:
    return {key for key, value in grants.items() if value in (True, "yes") or
            (key == "allowed_to_modify" and isinstance(value, dict) and bool(value))}


def _grant_key_matches_effect(key: str, effect: Effect_intent) -> bool:
    return (EFFECT_KEYS[effect.effect] == key or
            (key == "allowed_to_modify" and effect.effect in {"delete_local_branch", "delete_remote_branch"}) or
            (key == "network_access" and effect.effect in {"remote_git_write", "publication", "merge",
                                                         "delete_remote_branch", "scheduler_query",
                                                         "scheduler_submit_condor", "scheduler_submit_work_queue"}) or
            (key == "merge_allowed" and effect.effect == "merge"))


def _verify_simple_scope(prompt: dict[str, Any], effects: tuple[Effect_intent, ...],
                         bindings: tuple[Binding, ...],
                         repositories: dict[str, Any]) -> None:
    """Reverse-check every executable simple scope against a consuming effect."""
    grants = prompt["heavy_command_permissions"]
    allowed = prompt["allowed_to_modify"]
    by_id = {binding.binding_id: binding for binding in bindings}

    def local_effect(repo_id: str, target: str, kinds: set[str]) -> bool:
        return any(effect.effect in kinds and effect.target == target and
                   effect.positive_authority_binding in by_id and
                   _scope_names_repo(by_id[effect.positive_authority_binding].validity_scope, repo_id)
                   for effect in effects)

    for surface_name, surface in (("allowed_to_modify", allowed),
                                  ("heavy_command_permissions.allowed_to_modify",
                                   grants.get("allowed_to_modify", {}))):
        _require(isinstance(surface, dict), "COMPILER_INVARIANT_FAILURE",
                 f"{surface_name} is not a repository scope")
        for repo_id, area in surface.items():
            _require(repo_id in repositories and isinstance(area, (dict, list)),
                     "COMPILER_INVARIANT_FAILURE", f"{surface_name} has unbound repository/category")
            if isinstance(area, list):
                _require(all(isinstance(target, str) and
                             local_effect(repo_id, target, set(EFFECT_KEYS)) for target in area),
                         "COMPILER_INVARIANT_FAILURE", f"unrequested {surface_name} target")
                continue
            for category, targets in area.items():
                _require(category in {"tracked_paths", "git_index_entries", "local_refs",
                                      "storage_paths", "git_effects"} and isinstance(targets, list),
                         "COMPILER_INVARIANT_FAILURE", f"unsupported executable scope category {category}")
                for target in targets:
                    _require(isinstance(target, str) and bool(target),
                             "COMPILER_INVARIANT_FAILURE", f"invalid {category} target")
                    if category == "git_effects":
                        justified = ((target == "create_one_prompt_local_commit" and
                                      (any(local_effect(repo_id, e.target, {"tracked_write"}) for e in effects) or
                                       prompt.get("prompt_mode") == "commit_preparation" and
                                       any(local_effect(repo_id, e.target, {"local_git_ref_write"}) for e in effects))) or
                                     (target == "create_feature_branch_from_reference" and
                                      prompt.get("branch_policy") == "create_feature_branch_from_reference" and
                                      any(local_effect(repo_id, e.target, {"local_git_ref_write"})
                                          for e in effects)))
                    elif category == "storage_paths":
                        # A diagnostic storage declaration is inert without
                        # its positive storage grant.
                        justified = grants.get("storage_writes") not in (True, "yes") or local_effect(
                            repo_id, target, {"production_storage_write"})
                    else:
                        kind = "tracked_write" if category in {"tracked_paths", "git_index_entries"} else \
                            "local_git_ref_write"
                        justified = local_effect(repo_id, target, {kind})
                        if category == "git_index_entries" and prompt.get("prompt_mode") == "commit_preparation":
                            justified = (_scope_contains(prompt.get("authorized_commit_scope", {}).get(repo_id, {}), target) and
                                         any(local_effect(repo_id, e.target, {"local_git_ref_write"}) for e in effects))
                        if category == "local_refs":
                            justified = justified or local_effect(repo_id, target,
                                                                   {"delete_local_branch", "delete_remote_branch"})
                    _require(justified, "COMPILER_INVARIANT_FAILURE",
                             f"unrequested {surface_name}.{category} target {target}")


def _effect_carrier(effect: Effect_intent, repo: str, data: dict[str, Any],
                    bindings: dict[str, Binding]) -> Optional[str]:
    """Resolve the carrier from its compiler-owned role, never a root fallback."""
    if not data.get("stages"):
        # A simple repository-local effect executes in its declared repository.
        location = data["prompt"]["repo_locations"].get(repo)
        return location.get("path") if isinstance(location, dict) else location
    if data.get("_controller_local_carrier"):
        carrier = data["_controller_local_carrier"]
        return carrier["worktree"] if carrier["repository"] == repo else None
    workers = data.get("worker_contract", {})
    for worker in workers.get("writers", []):
        if worker["stage_id"] == effect.stage_id:
            return worker.get("worktree_path")
    if effect.stage_id == "exact_union":
        return workers.get("composition_worktree_path")
    candidate = data["repositories"].get(repo, {})
    if candidate.get("stage_id") == effect.stage_id:
        return candidate.get("candidate_worktree")
    if effect.stage_id == "integration":
        # Permanent targets need their own acquired carrier relation. Repository
        # location alone says nothing about the worktree attached to this ref.
        matches = [b.observed_state.get("value") for b in bindings.values()
                   if b.acquisition == "acquired" and b.source_kind == "repository_readback" and
                   b.materiality != "DOCUMENTARY" and _scope_names_repo(b.validity_scope, repo) and
                   isinstance(b.observed_state, dict) and
                   b.observed_state.get("identity_path") == "worker_contract.integration_target_carrier"]
        if len(matches) == 1 and isinstance(matches[0], dict):
            carrier = matches[0]
            if (carrier.get("repository") == repo and
                    "refs/heads/" + str(carrier.get("attached_branch")) == effect.target):
                return carrier.get("worktree")
    return None


def _given_observation(check: dict[str, Any], fact: Binding) -> dict[str, Any]:
    """The acquired fact includes value, carrier, mechanism and evidence scope."""
    return {**{key: check[key] for key in
               ("property", "repository_id", "working_directory", "target", "argv", "comparison")},
            "observed_value": check["expected"], "source_identity": fact.source_identity,
            "validity_scope": fact.validity_scope,
            "dependent_effect_ids": sorted(fact.dependent_effect_ids)}


def _given_validity(check: Optional[dict[str, Any]], fact: Binding,
                    effects: tuple[Effect_intent, ...], data: dict[str, Any],
                    bindings: dict[str, Binding]) -> dict[str, Any]:
    """Compare the consumed property, not a global HEAD or evidence timestamp.

    Current carrier relations have already passed exact identity verification.
    A portable-result premise takes a different path and never enters this
    comparison. Unrelated relations and unconsumed carrier properties are inert.
    Absence of a newer observation is not an invented observation of drift.
    """
    relation: dict[str, Any] = {
        "claim": fact.claim, "evidence_identity": fact.source_identity,
        "validity_scope": fact.validity_scope, "observed_property": check["property"] if check else None,
        "dependent_effects": list(fact.dependent_effect_ids), "carrier_comparisons": [],
        "state": "no_comparable_current_observation"}
    if not check:
        return relation
    repo = check["repository_id"]
    dependent = [e for e in effects if e.effect_id in fact.dependent_effect_ids]
    for effect in dependent:
        # The compiler-owned role selects the exact relation; generic live
        # applicability and coincidentally equal literals cannot authenticate it.
        role = effect.stage_id
        workers = data.get("worker_contract", {}).get("writers", [])
        if any(w["stage_id"] == role for w in workers):
            path = f"worker_contract.writers.{role}.carrier"
        elif role == "exact_union":
            path = "worker_contract.composition_carrier"
        elif role == "integration":
            path = "worker_contract.integration_target_carrier"
        elif role and data["repositories"][repo].get("stage_id") == role:
            path = f"repositories.{repo}.candidate_carrier"
        else:
            path = f"repositories.{repo}.current_carrier"
        for binding in bindings.values():
            observation = binding.observed_state
            if not (binding.acquisition == "acquired" and binding.materiality != "DOCUMENTARY" and
                    binding.source_kind in {"repository_readback", "accepted_evidence"} and
                    _scope_names_repo(binding.validity_scope, repo) and isinstance(observation, dict) and
                    observation.get("identity_path") == path and isinstance(observation.get("value"), dict)):
                continue
            value = observation["value"]
            carrier = {"repository_id": value.get("repository"),
                       "working_directory": value.get("worktree", value.get("candidate_worktree")),
                       "attached_branch": value.get("attached_branch", value.get("candidate_branch"))}
            if carrier["repository_id"] != repo or carrier["working_directory"] != check["working_directory"]:
                continue
            properties = {
                "current_branch": "refs/heads/" + str(carrier["attached_branch"]),
                # HEAD describes this ref only when the relation binds its
                # attachment. A different branch's HEAD proves nothing about it.
                "local_ref_oid": value.get("head", value.get("candidate_head"))
                if "refs/heads/" + str(carrier["attached_branch"]) == check["target"] else None,
            }
            observed = properties.get(check["property"])
            if observed is None:
                continue
            relation["carrier_comparisons"].append({
                "effect_id": effect.effect_id, "carrier_identity": carrier,
                "relation_identity": path, "binding_id": binding.binding_id,
                "source_identity": binding.source_identity,
                "material_property": check["property"], "required_value": check["expected"],
                "current_observed_value": observed, "consistent": observed == check["expected"]})
    compared = relation["carrier_comparisons"]
    if compared:
        relation["state"] = "unchanged_consumed_property" if all(c["consistent"] for c in compared) else \
            "stale_consumed_property"
    return relation


def _given_invalidated(fact: Binding, effects: tuple[Effect_intent, ...],
                       continuation: Optional[Continuation]) -> bool:
    if not continuation:
        return False
    dependencies = {fact.binding_id, fact.source_identity, *fact.dependent_effect_ids}
    dependencies.update(effect.stage_id for effect in effects if effect.effect_id in fact.dependent_effect_ids)
    return any(item == "*" or (isinstance(item, str) and item in dependencies)
               for item in continuation.invalidation_boundary)


def _accepted_writer_given(step: Source_line, fact: Binding,
                           effects: tuple[Effect_intent, ...],
                           continuation: Optional[Continuation], repo_ids: set[str]) -> bool:
    """Consume the Q04 portable result; its retired carrier is not a premise."""
    match = re.fullmatch(r"accepted writer (writer_[ab]) result names commit ([0-9a-f]{40}|[0-9a-f]{64})",
                         step.text)
    if not match or not continuation or fact.source_kind != "accepted_evidence":
        return False
    accepted = next((item for item in continuation.accepted_prior_evidence
                     if isinstance(item, dict) and item.get("writer_id") == match.group(1)), None)
    return bool(accepted and accepted.get("observed_commit_head") == match.group(2) and
                fact.acquisition == "acquired" and
                fact.source_identity == continuation.prior_artifact_identity and
                any(_scope_names_repo(fact.validity_scope, repo) for repo in repo_ids) and
                not _given_invalidated(fact, effects, continuation) and
                match.group(1) not in continuation.invalidation_boundary and
                fact.observed_state == {"identity_path": "q04.accepted_writer_result", "value": {
                    key: accepted[key] for key in
                    ("writer_id", "observed_commit_head", "reviewed_evidence", "base_oid")}} and
                all(effect.stage_id == "exact_union" for effect in effects
                    if effect.effect_id in fact.dependent_effect_ids))


def _given_verification(step: Source_line, fact: Binding, effects: tuple[Effect_intent, ...],
                        data: dict[str, Any], by_id: dict[str, Binding]) -> Optional[dict[str, Any]]:
    """Derive a bounded local Git check from the property and consumed effect.

    Caller preflight prose is inert. These are AGENTS/Git lifecycle readbacks,
    not a general command template or an authorization to execute the check.
    """
    text = step.text.strip()
    current_branch = text.lower() in {
        "the selected commit branch is checked out",
        "the current branch is the selected commit target",
    }
    exact = re.fullmatch(r"(?:ref )?(refs/heads/[A-Za-z0-9_./-]+) "
                         r"(?:names commit|resolves to) ([0-9a-f]{40}|[0-9a-f]{64})", text)
    if not current_branch and not exact:
        return None
    dependent = [effect for effect in effects if effect.effect_id in fact.dependent_effect_ids]
    if not dependent:
        return None
    targets = {effect.target for effect in dependent}
    if len(targets) != 1 or any(effect.effect != "local_git_ref_write" for effect in dependent):
        return None
    target = next(iter(targets))
    if not _safe_local_branch_ref(target) or (exact and exact.group(1) != target):
        return None
    repositories = {repo for repo in data["repositories"]
                    if _scope_names_repo(fact.validity_scope, repo) and
                    all(effect.positive_authority_binding in by_id and
                        _scope_names_repo(by_id[effect.positive_authority_binding].validity_scope, repo)
                        for effect in dependent)}
    if len(repositories) != 1:
        return None
    repo = next(iter(repositories))
    locations = {_effect_carrier(effect, repo, data, by_id) for effect in dependent}
    if len(locations) != 1:
        return None
    location = next(iter(locations))
    if not isinstance(location, str) or not location.startswith("/"):
        return None
    if current_branch:
        for effect in dependent:
            contract = next((stage for stage in data.get("stages", [])
                             if stage["stage_id"] == effect.stage_id), data["prompt"])
            branch = contract.get("target_branch", contract.get("feature_branch"))
            if branch != target[len("refs/heads/"):] or contract.get(
                    "stage_mode", contract.get("prompt_mode")) not in {
                        "coding", "documentation_only", "integration_only"}:
                return None
    return {"property": "current_branch" if current_branch else "local_ref_oid",
            "repository_id": repo, "working_directory": location,
            "target": target, "expected": target if current_branch else exact.group(2),
            "argv": ["git", "symbolic-ref", "--quiet", "HEAD"] if current_branch else
                    ["git", "rev-parse", "--verify", target],
            "comparison": "exit_zero_and_stdout_equals_expected",
            "before_effects": list(fact.dependent_effect_ids),
            "failure_behavior": "block_only_dependent_effects",
            "rule_source": "governance/contracts/git_lifecycle.md"}


def _verify(data: dict[str, Any], intent: Semantic_intent, bindings: tuple[Binding, ...],
            effects: tuple[Effect_intent, ...], continuation: Optional[Continuation],
            shape: str, contents: dict[str, str],
            roles: dict[str, dict[str, str]],
            isolation_audit: dict[str, Any]) -> tuple[list[Trace_edge], list[str], list[str]]:
    prompt = data.get("prompt", {})
    _require(isinstance(prompt, dict), "COMPILER_INVARIANT_FAILURE", "prompt must be mapping")
    _require(PROMPT_CORE <= prompt.keys(), "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
             "required current CPC prompt field missing")
    _require(not ({"executed", "accepted", "execution_complete", "result_accepted"} & prompt.keys()),
             "COMPILER_INVARIANT_FAILURE", "compile candidate cannot assert execution or acceptance")
    _require("workflow_stages" not in prompt, "COMPILER_INVARIANT_FAILURE",
             "caller cannot serialize workflow_stages outside the compiler plan")
    _require(any(b.source_kind == "owner_decision" and b.acquisition == "acquired" for b in bindings),
             "NOT_READY_MISSING_AUTHORITY_BINDING", "acquired owner decision binding is missing")
    # An unacquired binding is not a global veto. Exact identities consumed
    # below still require acquisition; Givens use their declared effect-local
    # dependency and may instead carry a must-pass runtime preflight.
    _require(bool(prompt.get("decision_question") and prompt.get("prompt_id")),
             "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "prompt_id or decision_question missing")
    mode = str(prompt.get("prompt_mode", ""))
    _canonical_mode(mode, contents)
    _require(mode == _planned_mode(shape, intent, effects), "COMPILER_INVARIANT_FAILURE",
             "caller prompt_mode differs from compiler-selected behavior and effects")
    stage_edges = _stage_trace(data, intent, effects, shape)
    branch = prompt.get("branch_policy")
    if branch:
        _canonical_branch(str(branch), contents)
        _branch_fields(prompt, "branch_policy")
    if shape in {"orchestrated_workflow", "multi_repository_coordination", "ordered_workflow", "dependent_continuation", "controller_local_workflow"}:
        _require(mode == "orchestrated_workflow" and not branch and "heavy_command_permissions" not in prompt,
                 "COMPILER_INVARIANT_FAILURE", "orchestrated output has invalid outer mode/permissions")
        _require({"workflow_goal", "workflow_stop_policy", "workflow_stage_ledger_path",
                  "workflow_effect_envelope"} <= prompt.keys(), "COMPILER_INVARIANT_FAILURE",
                 "orchestrated outer contract incomplete")
    else:
        _require(mode != "orchestrated_workflow" and bool(branch),
                 "COMPILER_INVARIANT_FAILURE", "simple output needs non-orchestrated mode and branch policy")
        _require(not ({"workflow_goal", "workflow_stop_policy", "workflow_stage_ledger_path",
                       "workflow_effect_envelope"} & prompt.keys()),
                 "COMPILER_INVARIANT_FAILURE", "non-orchestrated shape cannot carry workflow mechanics")
        _require("heavy_command_permissions" in prompt, "COMPILER_INVARIANT_FAILURE",
                 "non-orchestrated positive grant map missing")
    for key in ("preferred_codex_model", "reasoning_level", "delegation_policy"):
        _require(bool(prompt.get(key)), "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", f"{key} missing")
        _canonical_model_field(key, str(prompt[key]), contents)
    _canonical_ceiling(str(prompt.get("validation_ceiling", "")), contents)
    _check_closed_fields(prompt, data.get("stages", []), contents)
    stage_ids = [stage.get("stage_id") for stage in data.get("stages", [])]
    _require(len(stage_ids) == len(set(stage_ids)), "COMPILER_INVARIANT_FAILURE", "duplicate stage id")
    for stage in data.get("stages", []):
        _require(STAGE_CORE <= stage.keys(), "COMPILER_INVARIANT_FAILURE", "stage core incomplete")
        _canonical_mode(str(stage["stage_mode"]), contents)
        _require(stage["stage_mode"] != "orchestrated_workflow", "COMPILER_INVARIANT_FAILURE", "nested workflow forbidden")
        if "stage_branch_policy" in stage:
            _canonical_branch(str(stage["stage_branch_policy"]), contents)
            _branch_fields(stage, "stage_branch_policy")
        if stage["stage_mode"] in {"coding", "documentation_only", "commit_preparation", "integration_only",
                                   "branch_maintenance_only", "pr_publication"}:
            _require("stage_branch_policy" in stage, "COMPILER_INVARIANT_FAILURE",
                     f"branch-relevant stage {stage['stage_id']} lacks stage_branch_policy")
        if stage["stage_mode"] == "integration_only":
            _require({"integration_source_branch", "integration_target_branch", "integration_method",
                      "expected_source_head"} <= stage.keys(),
                     "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "integration stage lacks exact source/target/method/head")
    if continuation:
        _require(bool(continuation.prior_artifact_identity and continuation.invalidation_boundary and
                      continuation.delta_scope), "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
                 "continuation closure or invalidation missing")
        _require(any(b.source_kind == "accepted_evidence" and b.acquisition == "acquired" and
                     b.source_identity == continuation.prior_artifact_identity for b in bindings),
                 "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "accepted continuation artifact is not bound")
        if data.get("worker_contract"):
            repo_id = next(iter(data["repositories"]))
            accepted = continuation.accepted_prior_evidence[0]
            accepted_binding_id = _exact_related_identity(
                bindings, "q04.accepted_writer_result",
                _accepted_result_identity(accepted), repo_id, "accepted_evidence")
            _require(next(b for b in bindings if b.binding_id == accepted_binding_id).source_identity ==
                     continuation.prior_artifact_identity,
                     "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
                     "Q04 accepted writer result does not belong to prior artifact")
            _relation_edge(bindings, stage_edges, "q04.accepted_writer_result",
                           _accepted_result_identity(accepted),
                           repo_id, "exact_union", "accepted_evidence")
    # Tags are retained in the intent and receipt, but never select a shape or grant an effect.
    by_id = {b.binding_id: b for b in bindings}
    if any(re.search(r"\b(scientific choice|choose (a|the) mapping|choose (a|the) fallback)\b", s.text, re.I)
           for s in intent.steps):
        selected = by_id.get(data.get("scientific_selection_binding"))
        _require(selected is not None and selected.acquisition == "acquired" and
                 selected.materiality == "DECISION_MATERIAL" and
                 selected.source_kind in {"owner_decision", "other"} and
                 selected.source_identity.startswith("scientific_owner:"),
                 "NOT_READY_NEW_DECISION_BOUNDARY", "scientific selection is not bound")
    unchanged = {m.group(1) for s in intent.steps for m in
                 [re.search(r"(?:reference branch|ref) ([\w/.-]+) remains unchanged", s.text, re.I)] if m}
    moved = {m.group(1) for s in intent.steps for m in
             [re.search(r"(?:move|advance) (?:reference branch|ref) ([\w/.-]+)", s.text, re.I)] if m}
    _require(not (unchanged & moved), "NOT_READY_NEW_DECISION_BOUNDARY", "same reference must move and remain unchanged")
    for assertion in intent.negative_assertions:
        if re.fullmatch(r"no remote repository is modified", assertion.strip(), re.I):
            _require(not any(effect.effect in {"remote_git_write", "publication", "merge",
                                               "delete_remote_branch"} for effect in effects),
                     "NOT_READY_NEW_DECISION_BOUNDARY",
                     "negative remote assertion contradicts requested remote effect")
        elif data.get("commit_contract") and re.search(r"no new effect.*recovery authority", assertion, re.I):
            _require(data.get("automatic_retry") is False, "COMPILER_INVARIANT_FAILURE", "no-new-effect constraint requires no automatic retry")
        elif data.get("deterministic_edit") and re.search(r"no worker.*workflow is invented", assertion, re.I):
            _require(not data.get("stages") and shape == "simple_non_orchestrated", "COMPILER_INVARIANT_FAILURE", "small-edit constraint forbids generated workflow")
        elif shape not in {"orchestrated_workflow", "multi_repository_coordination", "ordered_workflow", "controller_local_workflow"}:
            _error('IMPLEMENTATION_GAP',
                   f"negative assertion has no bounded constraint checker: {assertion}")
    if not effects:
        supported_words = (r"\b(inspect|read|compare|review|check|validate|report|production|publish|"
                           r"submit|edit|write|modify|change|move|advance|delete|retire|remove|"
                           r"merge|integrate|unblind|choose)\b")
        _require(all(re.search(supported_words, step.text, re.I) for step in intent.steps
                     if step.keyword == "When"), 'ARCHITECTURE_BOUNDARY_UNRESOLVED',
                 "action has no established canonical behavior or execution contract",
                 contract="D8-C#Q20 undefined semantic execution boundary")
    for repo_id, repo in data.get("repositories", {}).items():
        _canonical_repository(repo_id, contents)
        if repo_id in roles:
            expected = roles[repo_id]["permanent_live_development_branch"]
            if repo.get("development_branch") and repo["development_branch"] != expected:
                _error("NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
                       f"{repo_id} development branch contradicts registry-selected module")
            if repo.get("feature_branch"):
                namespace = roles[repo_id]["feature_development_namespace"].removesuffix("*")
                _require(repo["feature_branch"].startswith(namespace) and
                         bool(repo["feature_branch"][len(namespace):]),
                         "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
                         f"{repo_id} feature branch is outside native namespace")
                _require(bool(repo.get("feature_branch_exception_binding") and
                              repo.get("feature_branch_isolation_need") and
                              repo.get("feature_branch_retirement_condition")),
                         "NOT_READY_MISSING_AUTHORITY_BINDING",
                         f"{repo_id} feature namespace does not authorize an exception branch")
                exception = by_id.get(repo["feature_branch_exception_binding"])
                _require(exception is not None and exception.source_kind == "owner_decision" and
                         exception.acquisition == "acquired" and _scope_names_repo(exception.validity_scope, repo_id),
                         "NOT_READY_MISSING_AUTHORITY_BINDING", f"{repo_id} exception binding missing")
        if repo.get("authority_binding"):
            bound = by_id.get(repo["authority_binding"])
            _require(bound is not None and bound.acquisition == "acquired" and
                     _scope_names_repo(bound.validity_scope, repo_id),
                     "NOT_READY_MISSING_AUTHORITY_BINDING", f"repo-local authority missing for {repo_id}")
    _require(isinstance(prompt.get("repo_locations"), dict) and
             set(prompt["repo_locations"]) == set(data.get("repositories", {})) and
             all(bool(path) for path in prompt["repo_locations"].values()),
             "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
             "repo_locations do not match bound typed repository identities")
    _require(all(isinstance(prompt.get(key), dict) and
                 set(prompt[key]) <= set(data.get("repositories", {}))
                 for key in ("allowed_to_modify", "read_only")),
             "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
             "prompt scope names a repository outside bound typed identities")
    _require(prompt.get("repository_branch_roles") == roles,
             "COMPILER_INVARIANT_FAILURE", "repository-native branch roles not serialized")
    for stage in data.get("stages", []):
        repo_id = stage.get("repository_id")
        if repo_id in roles and stage.get("stage_mode") == "coding" and not data.get("lifecycle_resources"):
            _require(stage.get("target_branch") == data["repositories"][repo_id].get("candidate_branch"),
                     "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", f"{repo_id} writer branch is not bound candidate")
    authorized: list[str] = []
    excluded: list[str] = []
    edges = [Trace_edge(f"line:{s.line}", "semantic_intent", "intent_or_assertion") for s in intent.steps]
    edges.append(Trace_edge("semantic_intent", "prompt:prompt_mode", "selects_minimum_shape"))
    edges.extend(Trace_edge(f"line:{s.line}", "prompt:prompt_mode", "requests_action")
                 for s in intent.steps if s.keyword == "When")
    edges.extend(stage_edges)
    def bind_identity(path: str, value: str, repo_id: str, stage_id: str, oid: bool = False) -> None:
        if oid:
            edges.append(Trace_edge(f"tracking:{path}={value}", f"stage:{stage_id}", "records_observation_only"))
            return
        binding_id = _exact_identity(bindings, path, value, repo_id)
        identity = f"identity:{path}={value}"
        edges.append(Trace_edge(f"binding:{binding_id}", identity, "observes_exact_value"))
        edges.append(Trace_edge(identity, f"stage:{stage_id}", "consumed_by"))

    if data.get("lifecycle_resources"):
        for resource_id, resource in data["lifecycle_resources"].items():
            _relation_edge(bindings, edges, "lifecycle_resources." + resource_id + ".carrier",
                           {key: resource[key] for key in ("repository", "repository_path", "worktree", "ref", "reference_ref")},
                           resource["repository"], next(s["stage_id"] for s in data["stages"]
                           if s.get("working_directory") == resource["worktree"]))
    if shape == "orchestrated_workflow":
        repo_id = next(iter(data["repositories"]))
        workers = data["worker_contract"]
        protected = set(continuation.checks_not_to_repeat) if continuation else set()
        for worker in workers["writers"]:
            stage_id = worker["stage_id"]
            if stage_id in protected:
                continue
            for key in ("branch", "base_oid", "observed_head", "worktree_path"):
                bind_identity(f"worker_contract.writers.{stage_id}.{key}", worker.get(key),
                              repo_id, stage_id, key.endswith("oid") or key == "observed_head")
            _relation_edge(bindings, edges, f"worker_contract.writers.{stage_id}.carrier",
                           {"repository": repo_id, "worktree": worker["worktree_path"],
                            "attached_branch": worker["branch"], "head": worker.get("observed_head"),
                            "base_oid": worker.get("base_oid")}, repo_id, stage_id)
        semantic_roles = _parallel_roles(intent)
        if "exact_union" in semantic_roles:
            for key in ("composition_branch", "composition_base_oid", "composition_worktree_path"):
                bind_identity(f"worker_contract.{key}", workers.get(key), repo_id, "exact_union",
                              key.endswith("oid"))
            _relation_edge(bindings, edges, "worker_contract.composition_carrier",
                           {"repository": repo_id, "worktree": workers["composition_worktree_path"],
                            "attached_branch": workers["composition_branch"],
                            "head": workers.get("composition_base_oid"),
                            "base_oid": workers.get("composition_base_oid")}, repo_id, "exact_union")
        if "integration" in semantic_roles:
            bind_identity("worker_contract.integration_target_branch", workers.get("integration_target_branch"),
                          repo_id, "integration")
        if data.get("common_validation_contract"):
            contract = data["common_validation_contract"]
            relation = {"validation_locator": contract["test_target"], "repository": repo_id,
                        "worktree": workers["composition_worktree_path"],
                        "attached_branch": workers["composition_branch"],
                        "head": "stage:exact_union:observed_commit_head",
                        "covers": ["exact_union", "common_validation"]}
            _relation_edge(bindings, edges, "common_validation.target_relation", relation,
                           repo_id, "common_validation", "accepted_evidence")
            then = next(step for step in intent.steps if step.keyword == "Then")
            relation_node = f"identity:common_validation.target_relation={relation}"
            edges.extend((Trace_edge(f"line:{then.line}", relation_node, "requires_validation_relation"),
                          Trace_edge(relation_node, "gate:common_validation", "requires_must_pass")))
    if shape == "multi_repository_coordination":
        for repo_id in data["candidate_pair_order"]:
            repo = data["repositories"][repo_id]
            for key in ("base", "development_branch"):
                bind_identity(f"repositories.{repo_id}.{key}", repo.get(key), repo_id,
                              repo["stage_id"], key == "base")
            relation = {"repository": repo_id,
                        "permanent_live_development_branch": repo["development_branch"],
                        "permanent_live_head": repo.get("base"),
                        "candidate_branch": repo["candidate_branch"],
                        "candidate_worktree": repo["candidate_worktree"],
                        "candidate_head": repo.get("candidate_head"),
                        "candidate_base_oid": repo.get("candidate_base_oid")}
            _relation_edge(bindings, edges, f"repositories.{repo_id}.candidate_carrier",
                           relation, repo_id, repo["stage_id"])
            carrier = by_id.get(repo["candidate_carrier_authority_binding"])
            _require(carrier is not None and carrier.acquisition == "acquired" and
                     carrier.source_kind == "owner_decision" and
                     _scope_names_repo(carrier.validity_scope, repo_id) and
                     carrier.authorizes_effect and carrier.effect == "local_git_ref_write" and
                     carrier.target == "refs/heads/" + repo["candidate_branch"],
                     "NOT_READY_MISSING_AUTHORITY_BINDING", f"{repo_id} candidate carrier authorization missing")
            edges.append(Trace_edge(f"binding:{carrier.binding_id}", f"stage:{repo['stage_id']}",
                                    "authorizes_candidate_carrier"))
            if data["integration_stages"]:
                _relation_edge(bindings, edges, f"repositories.{repo_id}.permanent_target",
                               {"repository": repo_id, "worktree": prompt["repo_locations"][repo_id],
                                "attached_branch": repo["permanent_target_branch"], "head": repo.get("base")},
                               repo_id, "integrate_" + repo_id)
        pair_contract = data.get("pair_validation_contract")
        _require(isinstance(pair_contract, dict) and set(pair_contract) == {"test_target", "covers"} and
                 isinstance(pair_contract.get("test_target"), str) and
                 bool(re.fullmatch(r"tests/(?!.*\.\.)[A-Za-z0-9_./-]+\.py(?:::test_[A-Za-z0-9_]+)?",
                                   pair_contract["test_target"])) and
                 pair_contract.get("covers") == ["provider", "consumer", "common"],
                 'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE', "candidate-pair validation contract missing or irrelevant")
        _relation_edge(bindings, edges, "pair_validation.candidate_tuple",
                       {"validation_locator": pair_contract["test_target"],
                        "covers": pair_contract["covers"],
                        "provider_repository": data["candidate_pair_order"][0],
                        "consumer_repository": data["candidate_pair_order"][1],
                        "provider_head": "stage:provider_candidate:observed_commit_head",
                        "consumer_head": "stage:consumer_candidate:observed_commit_head"},
                       data["candidate_pair_order"][0], "pair_validation", "accepted_evidence")
    if shape == "dependent_continuation":
        relation = data["accepted_effect_state"]
        _relation_edge(bindings, edges, "continuation.accepted_effect_state", relation,
                       "topcoffea", "readback", "accepted_evidence")
    if shape in {"orchestrated_workflow", "multi_repository_coordination", "ordered_workflow", "dependent_continuation", "controller_local_workflow"}:
        isolation_audit["relation_local_consistency"] = True
        _verify_carrier_isolation(data, shape, edges, isolation_audit)
    if data.get("retirement") and shape == "orchestrated_workflow":
        life = data["retirement"]
        repo_id = next(iter(data["repositories"]))
        for identity_path, fields, kind, configured_binding in (
                ("retirement.owned_ref", ("exact_owned_surface", "exact_old_oid"),
                 "repository_readback", "ownership_readback_binding"),
                ("retirement.preserved_ref", ("preservation_ref", "expected_preserved_head"),
                 "accepted_evidence", "preservation_binding")):
            value = {key: life.get(key) for key in fields}
            binding_id = _exact_related_identity(bindings, identity_path, value, repo_id, kind)
            _require(binding_id == life.get(configured_binding),
                     "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
                     f"{identity_path} differs from configured evidence binding")
            identity = f"identity:{identity_path}={value}"
            edges.append(Trace_edge(f"binding:{binding_id}", identity, "observes_exact_relation"))
            edges.append(Trace_edge(identity, "stage:retirement", "consumed_by"))
    given_readiness: list[dict[str, Any]] = []
    blocked_given_effects: set[str] = set()
    for step in intent.steps:
        if step.keyword == "Given":
            edges.append(Trace_edge(f"line:{step.line}", f"precondition_evidence:line:{step.line}",
                                    "requires_acquisition_or_readback"))
            linked = data.get("given_bindings", {}).get(str(step.line))
            if linked:
                _require(linked in by_id, "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
                         "Given names an unknown binding", step.line)
                fact = by_id[linked]
                dependencies = tuple(fact.dependent_effect_ids)
                _require(len(dependencies) == len(set(dependencies)) and
                         all(any(effect.effect_id == effect_id for effect in effects)
                             for effect_id in dependencies),
                         "COMPILER_INVARIANT_FAILURE", "Given has unknown dependent effect", step.line)
                _require(fact.materiality == "DOCUMENTARY" or bool(dependencies),
                         'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE',
                         "material Given has no declared dependent effect", step.line)
                check = None
                validity = None
                if fact.materiality == "DOCUMENTARY":
                    edges.append(Trace_edge(f"precondition_evidence:line:{step.line}",
                                            f"binding:{linked}", "documentary_only"))
                    state = "non_material_documentary_premise"
                    dependencies = ()
                else:
                    check = _given_verification(step, fact, effects, data, by_id)
                    tracking_ref = bool(check and check["property"] == "local_ref_oid")
                    if tracking_ref:
                        # Exact reviewed source/result obligations are checked independently by integration.
                        check = {**check, "tracking_only": True}
                    portable = _accepted_writer_given(step, fact, effects, continuation, set(data["repositories"]))
                    invalidated = _given_invalidated(fact, effects, continuation)
                    validity = _given_validity(check, fact, effects, data, by_id)
                    if portable:
                        validity.update(state="portable_result_within_validity_scope",
                                        observed_property="accepted_writer_result")
                    elif invalidated:
                        validity["state"] = "explicitly_invalidated"
                    stale = validity["state"] == "stale_consumed_property"
                    acquired = bool(check and fact.acquisition == "acquired" and not invalidated and
                                    not stale and
                                    fact.source_kind in {"repository_readback", "accepted_evidence"} and
                                    fact.observed_state == _given_observation(check, fact))
                    contradictory = stale or bool(check and fact.acquisition == "acquired" and not invalidated and
                                                  fact.observed_state is not None and not acquired)
                    if tracking_ref:
                        state = "non_material_documentary_premise"
                        dependencies = ()
                        edges.append(Trace_edge(f"precondition_evidence:line:{step.line}",
                                                f"binding:{linked}", "records_observation_only"))
                        prompt.setdefault("evidence_requirements", []).append({
                            "tracking_only_ref_observation": {"binding_id": linked,
                                "observed_state": fact.observed_state,
                                "refresh_before_effect": check["argv"]}})
                    elif portable or acquired:
                        state = "already_acquired_material_fact"
                        evidence = {"binding_id": linked, "source_identity": fact.source_identity,
                                    "validity_scope": fact.validity_scope, "observed_state": fact.observed_state,
                                    "before_effects": list(dependencies)}
                        if data.get("stages"):
                            for stage in data["stages"]:
                                local = [e.effect_id for e in effects if e.effect_id in dependencies and
                                         e.stage_id == stage["stage_id"]]
                                if local:
                                    stage["stage_inputs"].append({"accepted_given_evidence": {
                                        **evidence, "before_effects": local}})
                        else:
                            prompt.setdefault("evidence_requirements", []).append({"accepted_given_evidence": evidence})
                        edges.append(Trace_edge(f"precondition_evidence:line:{step.line}",
                                                f"binding:{linked}", "resolved_by"))
                    elif check is None or contradictory:
                        state = "unsupported_material_premise"
                        blocked_given_effects.update(dependencies)
                        prompt.setdefault("evidence_requirements", []).append(
                            f"unsupported material Given {linked}; block only effects {', '.join(dependencies)}")
                        # An excluded effect must also be fenced in the emitted
                        # executable contract. Stage inputs precede every effect
                        # in that stage; absent outputs fence its descendants.
                        prerequisite = {"binding_id": linked, "source_identity": fact.source_identity,
                                        "validity_scope": fact.validity_scope, "state": state,
                                        "failure_behavior": "block_only_dependent_effects"}
                        if data.get("stages"):
                            for stage in data["stages"]:
                                local = [e.effect_id for e in effects if e.effect_id in dependencies and
                                         e.stage_id == stage["stage_id"]]
                                if local:
                                    stage["stage_inputs"].append({"must_pass_before_effects": {
                                        **prerequisite, "before_effects": local}})
                        else:
                            prompt.setdefault("evidence_requirements", []).append({
                                "must_pass_before_effects": {**prerequisite, "before_effects": list(dependencies)}})
                    else:
                        state = "runtime_preflight_requirement"
                        # stage_inputs are preconditions. Acceptance gates are
                        # post-effect evidence and cannot safely carry this check.
                        if data.get("stages"):
                            for stage in data["stages"]:
                                local = [effect.effect_id for effect in effects
                                         if effect.effect_id in dependencies and
                                         effect.stage_id == stage["stage_id"]]
                                if local:
                                    stage["stage_inputs"].append({"must_pass_before_effects": {
                                        **check, "before_effects": local}})
                        else:
                            prompt.setdefault("evidence_requirements", []).append(
                                {"must_pass_before_effects": check})
                    edges.append(Trace_edge(f"precondition_evidence:line:{step.line}",
                                            f"gate:given:{step.line}", "requires_effect_local_preflight"))
                    for effect_id in dependencies:
                        edges.append(Trace_edge(f"gate:given:{step.line}", f"effect:{effect_id}",
                                                "must_pass_before"))
                given_readiness.append({"line": step.line, "binding_id": linked,
                                        "materiality": fact.materiality,
                                        "dependent_effect_ids": list(dependencies),
                                        "state": state,
                                        "verification": check,
                                        "validity_relation": validity,
                                        "why_material": fact.material_reason if dependencies else "documentary only",
                                        "runtime_preflight_sufficient": state == "runtime_preflight_requirement"})
            else:
                plan_bound = ((shape == "orchestrated_workflow" and
                               re.fullmatch(r"isolated worktrees", step.text, re.I)) or
                              (shape == "multi_repository_coordination" and
                               re.fullmatch(r"exact bases", step.text, re.I)))
                _require(plan_bound or not (
                    step.text.lower() in {"the selected commit branch is checked out",
                                         "the current branch is the selected commit target"} or
                    re.fullmatch(r"(?:ref )?refs/heads/\S+ (?:names commit|resolves to) \S+", step.text) or
                    step.text.startswith("accepted writer ")),
                    'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE',
                    "identity Given needs an explicit materiality/dependency binding", step.line)
                state = "already_acquired_material_fact" if plan_bound else "non_material_documentary_premise"
                edges.append(Trace_edge(f"precondition_evidence:line:{step.line}",
                                        f"{'plan_bound_given' if plan_bound else 'documentary_given'}:line:{step.line}",
                                        state))
                given_readiness.append({"line": step.line, "binding_id": None,
                                        "materiality": "DECISION_MATERIAL" if plan_bound else "DOCUMENTARY",
                                        "dependent_effect_ids": [effect.effect_id for effect in effects]
                                        if plan_bound else [],
                                        "state": state,
                                        "why_material": "exact carrier/base relations consumed by planner"
                                        if plan_bound else "documentary only",
                                        "runtime_preflight_sufficient": False})
    data["_given_readiness"] = given_readiness
    data["_blocked_given_effects"] = sorted(blocked_given_effects)
    for step in intent.steps:
        if re.search(r"\bauthori[sz]ed\b", step.text, re.I) and step.keyword == "Given":
            _require(any(b.acquisition == "acquired" and b.source_kind == "owner_decision" and
                         b.authorizes_effect and b.claim.lower() in step.text.lower() for b in bindings),
                     "NOT_READY_MISSING_AUTHORITY_BINDING", "Gherkin authority assertion has no owner binding", step.line)
    for step in intent.steps:
        if step.keyword == "When" and re.search(r"\b(production|publish|publication|submit)\b", step.text, re.I):
            _require(any(effect.requested_by_step == step.line for effect in effects),
                     "NOT_READY_MISSING_AUTHORITY_BINDING", "side-effecting action lacks explicit requested effect and binding",
                     step.line)
        if step.keyword == "When" and re.search(r"\b(edit|write|modify|change|move|advance|delete|retire|remove|merge|integrate|unblind)\b",
                                                step.text, re.I) and not (
                shape == "dependent_continuation" and
                data["accepted_effect_state"]["consumer_outcome"] == "OUTCOME_UNKNOWN" and
                not effects and [stage["stage_id"] for stage in data["stages"]] == ["readback"]):
            _require(any(effect.requested_by_step == step.line for effect in effects),
                     "NOT_READY_MISSING_AUTHORITY_BINDING", "mutating action lacks explicit effect and binding",
                     step.line)
    for effect in effects:
        source_step = next(step for step in intent.steps if step.line == effect.requested_by_step)
        implicit_commit = (effect.effect == "local_git_ref_write" and
                           any(other.effect == "tracked_write" and
                               other.stage_id == effect.stage_id and
                               other.requested_by_step == effect.requested_by_step for other in effects))
        if implicit_commit:
            carrier_contract = next((s for s in data.get("stages", []) if s["stage_id"] == effect.stage_id), prompt)
            carrier_branch = carrier_contract.get("target_branch", carrier_contract.get("feature_branch"))
            _require(effect.target == "refs/heads/" + str(carrier_branch),
                     'NOT_READY_NEW_DECISION_BOUNDARY',
                     "commit closure cannot introduce an unrelated ref effect", effect.requested_by_step)
        semantic_integration = (effect.effect == "local_git_ref_write" and
                                effect.stage_id == "integration" and bool(_composition_dependencies(intent)))
        _require(source_step.keyword == "When" and
                 (bool(re.search(EFFECT_ACTION_WORDS[effect.effect], source_step.text, re.I)) or
                  implicit_commit or semantic_integration or shape == "controller_local_workflow"),
                 "COMPILER_INVARIANT_FAILURE", f"{effect.effect} is not traced to matching When action",
                 effect.requested_by_step)
        binding = by_id.get(effect.positive_authority_binding)
        _require(binding is not None and binding.acquisition == "acquired" and
                 binding.source_kind == "owner_decision" and binding.authorizes_effect and
                 binding.effect == effect.effect and binding.target == effect.target,
                 "NOT_READY_MISSING_AUTHORITY_BINDING", f"{effect.effect} lacks exact positive owner binding",
                 effect.requested_by_step)
        effect_stage = next((s for s in data.get("stages", []) if s["stage_id"] == effect.stage_id), None)
        effect_repo = (effect_stage.get("repository_id") if effect_stage else None) or (
            next(iter(data["repositories"])) if len(data["repositories"]) == 1 else None)
        _require(effect_repo is not None and _scope_names_repo(binding.validity_scope, effect_repo) and
                 _scope_contains(prompt["allowed_to_modify"].get(effect_repo, {}), effect.target),
                 "NOT_READY_MISSING_AUTHORITY_BINDING", f"{effect.effect} lacks repository-local authority/scope",
                 effect.requested_by_step)
        _require(_declared_grant(effect, prompt, data.get("stages", [])),
                 "NOT_READY_MISSING_AUTHORITY_BINDING", f"{effect.effect} lacks local positive grant",
                 effect.requested_by_step)
        _require(_scope_contains(prompt["allowed_to_modify"], effect.target),
                 "NOT_READY_MISSING_AUTHORITY_BINDING", f"{effect.effect} target exceeds outer allowed_to_modify",
                 effect.requested_by_step)
        action_context = next(s for s in data["stages"] if s["stage_id"] == effect.stage_id) \
            if data.get("stages") else prompt
        effective_mode = action_context["stage_mode"] if data.get("stages") else mode
        branch_policy = action_context.get("stage_branch_policy") if data.get("stages") else branch
        if effect.effect == "tracked_write":
            _require(effective_mode in {"coding", "documentation_only", "test_alignment_only"} and
                     branch_policy != "read_only_current_branch",
                     "COMPILER_INVARIANT_FAILURE", "tracked write has invalid mode or read-only branch policy")
            _require(_scope_contains(action_context.get("authorized_commit_scope", {}), effect.target) and
                     action_context.get("explicitly_adopted_inherited_changes") == "none" and
                     action_context.get("foreign_dirty_change_policy") == "preserve_and_exclude" and
                     action_context.get("staging_policy") == "exact_path_only",
                     "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "tracked edit lacks exact commit/foreign-work closure")
        if data.get("stages"):
            envelope = prompt.get("workflow_effect_envelope", {})
            key = EFFECT_KEYS[effect.effect]
            _require(key in envelope and envelope[key] not in (False, "no", None),
                     "COMPILER_INVARIANT_FAILURE", "stage grant exceeds outer ceiling")
            if key == "allowed_to_modify":
                _require(effect.target in str(envelope[key]), "COMPILER_INVARIANT_FAILURE",
                         "stage path/ref grant exceeds outer exact ceiling")
            if effect.effect in {"delete_local_branch", "delete_remote_branch"}:
                _require(_scope_contains(envelope.get("allowed_to_modify", {}), effect.target),
                         "COMPILER_INVARIANT_FAILURE", "terminal ref exceeds outer exact ceiling")
        if effect.effect in {"remote_git_write", "publication", "merge", "delete_remote_branch",
                             "scheduler_query", "scheduler_submit_condor", "scheduler_submit_work_queue"}:
            grants = next(s for s in data["stages"] if s["stage_id"] == effect.stage_id)["stage_effect_permissions"] \
                if data.get("stages") else prompt["heavy_command_permissions"]
            _require(grants.get("network_access") in (True, "yes"),
                     "NOT_READY_MISSING_AUTHORITY_BINDING", "outbound effect lacks network_access")
        if effect.effect == "merge":
            _require(grants.get("merge_allowed") in (True, "yes"),
                     "NOT_READY_MISSING_AUTHORITY_BINDING", "merge requires separate merge_allowed")
        if effect.effect in {"scheduler_submit_condor", "scheduler_submit_work_queue", "production_storage_write"}:
            effective_mode = next(s for s in data["stages"] if s["stage_id"] == effect.stage_id)["stage_mode"] \
                if data.get("stages") else mode
            _require(effective_mode == "production_execution", "COMPILER_INVARIANT_FAILURE",
                     "production effect requires production_execution mode")
            action = next(s for s in data["stages"] if s["stage_id"] == effect.stage_id) \
                if data.get("stages") else prompt
            _require({"production_action", "production_target", "input_lineage", "effect_surface",
                      "execution_owner", "intended_output_paths", "overwrite_or_resume_policy",
                      "interruption_retry_policy"} <= action.keys(),
                     "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "production action contract incomplete")
        if effect.effect in {"remote_git_write", "publication", "merge", "delete_remote_branch"}:
            effective_mode = next(s for s in data["stages"] if s["stage_id"] == effect.stage_id)["stage_mode"] \
                if data.get("stages") else mode
            _require(effective_mode == "pr_publication", "COMPILER_INVARIANT_FAILURE",
                     "remote publication effect requires pr_publication mode")
            _require(not (data.get("stages") and effect.effect == "merge"),
                     "COMPILER_INVARIANT_FAILURE", "PR/MR merge forbidden in orchestration")
        authorized.append(effect.effect_id)
        edges.extend((Trace_edge(f"line:{effect.requested_by_step}", f"effect:{effect.effect_id}", "requests"),
                      Trace_edge(f"binding:{binding.binding_id}", f"effect:{effect.effect_id}", "authorizes"),
                      Trace_edge(f"effect:{effect.effect_id}", "prompt:allowed_to_modify", "bounds_target")))
        if not data.get("stages"):
            edges.append(Trace_edge(f"effect:{effect.effect_id}",
                                    "prompt:heavy_command_permissions", "granted_at_prompt"))
    if not data.get("stages") and any(e.effect == "tracked_write" for e in effects):
        branch_name = prompt.get("feature_branch") if branch == "create_feature_branch_from_reference" else prompt.get("target_branch")
        ref = "refs/heads/" + str(branch_name)
        repo_id = next(iter(data["repositories"])) if len(data["repositories"]) == 1 else ""
        allowed_area = prompt["allowed_to_modify"].get(repo_id, {})
        granted_area = prompt["heavy_command_permissions"].get("allowed_to_modify", {}).get(repo_id, {})
        _require(any(e.effect == "local_git_ref_write" and e.target == ref for e in effects) and
                 ref in allowed_area.get("local_refs", []) and ref in granted_area.get("local_refs", []) and
                 all(e.target in allowed_area.get("git_index_entries", []) and
                     e.target in granted_area.get("git_index_entries", [])
                     for e in effects if e.effect == "tracked_write"),
                 "NOT_READY_MISSING_AUTHORITY_BINDING", "simple tracked edit lacks exact index/ref commit authority")
    if not data.get("stages"):
        _verify_simple_scope(prompt, effects, bindings, data["repositories"])
    grant_maps = [prompt.get("heavy_command_permissions", {})] if not data.get("stages") else [
        stage["stage_effect_permissions"] for stage in data["stages"]]
    for grants in grant_maps:
        for key in _positive_keys(grants):
            _require(any(_grant_key_matches_effect(key, e) and _declared_grant(e, prompt, data.get("stages", []))
                         for e in effects), "COMPILER_INVARIANT_FAILURE", f"untraced positive grant {key}")
    if data.get("stages"):
        for stage in data["stages"]:
            stage_id = stage["stage_id"]
            local_effects = [effect for effect in effects if effect.stage_id == stage_id]
            scope = stage["stage_effect_permissions"].get("allowed_to_modify", {})
            for repo_id, area in scope.items():
                _require(repo_id in data["repositories"] and isinstance(area, dict),
                         "COMPILER_INVARIANT_FAILURE", f"{stage_id} has unbound repository scope")
                for category in ("tracked_paths", "git_index_entries", "local_refs", "worktree_paths"):
                    for target in area.get(category, []):
                        _require(_scope_contains(prompt["allowed_to_modify"].get(repo_id, {}), target) and
                                 _scope_contains(prompt["workflow_effect_envelope"].get(
                                     "allowed_to_modify", {}).get(repo_id, {}), target) and
                                 (any(effect.target == target or
                                     (category == "git_index_entries" and effect.effect == "tracked_write" and
                                      effect.target == target) for effect in local_effects) or
                                  (category == "git_index_entries" and shape == "controller_local_workflow" and
                                   stage["stage_mode"] == "commit_preparation" and
                                   any(e.effect == "tracked_write" and e.target == target and
                                       e.stage_id in {ancestor for parent in data["_result_graph"].predecessors(stage_id)
                                                     for ancestor in data["_result_graph"].predecessors(parent)}
                                       for e in effects)) or
                                  (category == "git_index_entries" and stage["stage_mode"] == "integration_only" and
                                   any(e.effect == "tracked_write" and e.target == target and
                                       f"stage:{e.stage_id}:observed_commit_head" in stage["stage_inputs"]
                                       for e in effects))),
                                 "COMPILER_INVARIANT_FAILURE", f"{stage_id} has untraced or pooled {category} {target}")
            if stage["stage_mode"] == "coding" and stage.get("deferred_commit_stage"):
                closure = stage["deferred_commit_stage"]
                target_stage = next((s for s in data["stages"] if s["stage_id"] == closure), {})
                _require((closure == "exact_union" or
                          (target_stage.get("stage_mode") == "commit_preparation" and
                           (f"stage:{stage_id}:frozen_postimages" in target_stage["stage_inputs"] or
                            (shape == "controller_local_workflow" and stage_id in {
                                ancestor for parent in data["_result_graph"].predecessors(closure)
                                for ancestor in data["_result_graph"].predecessors(parent)})) and
                           target_stage.get("repository_id") == stage.get("repository_id"))) and
                         stage["stage_outputs"] == ["frozen_postimages"] and
                         not any(e.effect == "local_git_ref_write" for e in local_effects) and
                         any(e.stage_id == closure and e.effect == "local_git_ref_write" for e in effects) and
                         all(set(area) <= ({"tracked_paths"} if closure == "exact_union" else {"tracked_paths", "git_index_entries"})
                             for area in scope.values()),
                         "NOT_READY_MISSING_AUTHORITY_BINDING", "invalid deferred writer closure")
            elif stage["stage_mode"] == "coding":
                ref = "refs/heads/" + stage["target_branch"]
                _require(any(e.effect == "local_git_ref_write" and e.target == ref for e in local_effects) and
                         _scope_contains(scope, ref),
                         "NOT_READY_MISSING_AUTHORITY_BINDING", f"{stage_id} commit has no exact ref authority")
            for key in _positive_keys(stage["stage_effect_permissions"]):
                _require(any(e.stage_id == stage["stage_id"] and _grant_key_matches_effect(key, e) for e in effects),
                         "COMPILER_INVARIANT_FAILURE", f"stage {stage['stage_id']} has untraced grant {key}")
    if data.get("foreign_dirty"):
        _require(prompt.get("foreign_dirty_change_policy") == "preserve_and_exclude" and
                 not data.get("adopt_foreign_work"), "COMPILER_INVARIANT_FAILURE", "foreign work would be adopted")
    if data.get("outcome_unknown"):
        _require(data.get("readback_before_retry") is True and not data.get("automatic_retry"),
                 "COMPILER_INVARIANT_FAILURE", "OUTCOME_UNKNOWN requires readback before retry")
        readback = by_id.get(data.get("readback_authority_binding"))
        _require(readback is not None and readback.acquisition == "acquired" and
                 readback.source_kind == "owner_decision",
                 "NOT_READY_MISSING_AUTHORITY_BINDING", "OUTCOME_UNKNOWN readback lacks exact authority")
    if data.get("commit_contract"):
        contract = data["commit_contract"]
        _require(mode == "commit_preparation" and not data.get("stages") and
                 data.get("outcome_unknown") is True and data.get("automatic_retry") is False and
                 contract.get("recovery_authorized") is False and
                 _safe_local_branch_ref(contract.get("ref")) and
                 contract["ref"] == "refs/heads/" + prompt.get("target_branch", "") and
                 contract.get("repository") in data["repositories"] and
                 contract.get("index_paths") == prompt.get("authorized_commit_scope", {}).get(contract["repository"]) and
                 bool(contract.get("index_identity")) and
                 any(e.effect == "local_git_ref_write" and e.target == contract["ref"] for e in effects),
                 "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "commit ambiguity lacks exact effect/base/index/recovery boundary")
        location = prompt["repo_locations"][contract["repository"]]
        _require(contract.get("worktree") == location, "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "commit readback carrier mismatch")
        prompt["ambiguous_effect_contract"] = {
            "outcome": "OUTCOME_UNKNOWN", "effect_ids": [e.effect_id for e in effects],
            "working_directory": location, "recorded_base_oid": contract.get("base_oid"),
            "index_paths": contract["index_paths"], "index_identity": contract["index_identity"],
            "readback_argv": [["git", "rev-parse", "--verify", contract["ref"]],
                              ["git", "rev-parse", "--verify", "HEAD"],
                              ["git", "diff", "--cached", "--raw"], ["git", "ls-files", "--stage"]],
            "automatic_retry": False, "new_effect_before_explicit_idempotence_or_recovery_authority": False,
            "on_ambiguous_readback": "stop and preserve state; do not infer failure"}
    if data.get("deterministic_edit"):
        edit = data["deterministic_edit"]
        writes = [e.target for e in effects if e.effect == "tracked_write"]
        _require(shape == "simple_non_orchestrated" and writes == [edit.get("path")] and
                 bool(re.fullmatch(r"[0-9a-f]{64}", str(edit.get("preimage_file_sha256", "")))) and
                 edit.get("literal_count") == 1 and edit.get("preimage_excerpt") and edit.get("replacement") and
                 edit.get("established_semantics_source"),
                 "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "deterministic edit lacks exact established one-file replacement")
        prompt["deterministic_edit"] = edit
        prompt["static_validation"] = "require exact preimage hash and one literal match before edit; inspect exact one-file diff and git diff --check; no workflow or worker creation"
    # Ordinary unavailable identity is tracking, including when no optional
    # materiality annotation was supplied. Explicit profile comparisons retain
    # the CPC evidence boundary; observation text alone cannot satisfy it.
    if data.get("runtime_model_materiality") not in (None, "not_decision_material"):
        _require(isinstance(data.get("runtime_model_observation"), str) and
                 data["runtime_model_observation"] not in {"", "not_observable"} and
                 bool(prompt.get("required_profile_agreement_evidence")) and
                 prompt.get("profile_agreement_failure_policy") == "fail_closed",
                 "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "exact runtime identity is decision-material")
    if data.get("multi_repository_state") and shape != "dependent_continuation":
        _require(not data.get("automatic_rollback") and not data.get("global_git_transaction"),
                 "COMPILER_INVARIANT_FAILURE", "multi-repository atomicity or rollback invented")
        _require(all(r.get("candidate") and r.get("authority_binding")
                     for r in data.get("repositories", {}).values()),
                 "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "repo-local base/candidate/authority missing")
        _require(bool(data.get("candidate_pair_order")), "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
                 "candidate pair validation order missing")
        _require(set(data.get("candidate_pair_order", [])) == set(data.get("repositories", {})),
                 "COMPILER_INVARIANT_FAILURE", "candidate tuple names differ from repository bindings")
        stage_ids = [stage["stage_id"] for stage in data.get("stages", [])]
        pair_stage = data.get("candidate_pair_validation_stage")
        _require(pair_stage in stage_ids, "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
                 "candidate-pair validation stage missing")
        for repo_id, repo in data["repositories"].items():
            local_stage = repo.get("stage_id")
            _require(local_stage in stage_ids and stage_ids.index(local_stage) < stage_ids.index(pair_stage),
                     "COMPILER_INVARIANT_FAILURE", f"{repo_id} candidate must precede pair validation")
            stage = next(stage for stage in data["stages"] if stage["stage_id"] == local_stage)
            _require(stage.get("repository_id") == repo_id and stage.get("stage_mode") == "coding" and
                     "stage_branch_policy" in stage,
                     "COMPILER_INVARIANT_FAILURE", f"{repo_id} candidate stage lacks repo-local branch authority")
            _require(any(e.stage_id == local_stage and e.effect in {"tracked_write", "local_git_ref_write"} and
                         _scope_names_repo(by_id[e.positive_authority_binding].validity_scope, repo_id)
                         for e in effects),
                     "NOT_READY_MISSING_AUTHORITY_BINDING", f"{repo_id} candidate has no local positive effect")
        _require(all(stage_ids.index(pair_stage) < stage_ids.index(s) for s in data.get("integration_stages", [])),
                 "COMPILER_INVARIANT_FAILURE", "candidate pair must be validated before integration")
        if data["multi_repository_state"] in {"PARTIAL", "PARTIALLY_INTEGRATED", "qualification_failed_after_effects"}:
            _require(not data.get("automatic_rollback") and not data.get("retirement") and
                     not any(e.effect == "publication" for e in effects),
                     "COMPILER_INVARIANT_FAILURE", "partial state must preserve real effects and stop retirement/publication")
            partial = data.get("partial_effects", {})
            _require(bool(partial.get("integrated_repo_identity") and partial.get("preserved_candidate_identity") and
                          partial.get("unresolved_recovery")),
                     "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "partial effects and candidate preservation missing")
            observed = by_id.get(data.get("partial_state_binding"))
            _require(observed is not None and observed.source_kind == "repository_readback" and
                     observed.acquisition == "acquired",
                     "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "partial-state readback binding missing")
        _require(data["multi_repository_state"] in {"NOT_STARTED", "PARTIAL", "PARTIALLY_INTEGRATED",
                                                      "COMPLETE", "qualification_failed_after_effects"},
                 "COMPILER_INVARIANT_FAILURE", "unknown coordinated state")
    if data.get("worker_contract"):
        workers = data["worker_contract"]
        stage_ids = {stage["stage_id"] for stage in data.get("stages", [])}
        paths = [set(worker["write_paths"]) for worker in workers.get("writers", [])]
        _require(len(paths) >= 2 and all(not (a & b) for i, a in enumerate(paths) for b in paths[i + 1:]),
                 "COMPILER_INVARIANT_FAILURE", "worker writers must have disjoint exact paths")
        protected = data.get("continuation", {}).get("checks_not_to_repeat", [])
        _require(all((worker["stage_id"] in stage_ids or worker["stage_id"] in protected) and
                     worker.get("isolated_worktree") for worker in workers["writers"]),
                 "COMPILER_INVARIANT_FAILURE", "writer isolation or stage missing")
        for worker in workers["writers"]:
            if worker["stage_id"] in protected:
                continue
            stage = next(stage for stage in data["stages"] if stage["stage_id"] == worker["stage_id"])
            _require(stage["stage_mode"] == "coding" and "stage_branch_policy" in stage,
                     "COMPILER_INVARIANT_FAILURE", "writer lacks coding mode or branch policy")
            _require(all(any(e.stage_id == worker["stage_id"] and e.effect == "tracked_write" and
                             e.target == path for e in effects) for path in worker["write_paths"]),
                     "COMPILER_INVARIANT_FAILURE", "writer path lacks stage-local authorized effect")
        _require(workers.get("independent_review_stage") in stage_ids and
                 workers.get("review_independent_of_writers") and
                 workers.get("worker_permanent_authority") is False,
                 "COMPILER_INVARIANT_FAILURE", "writer review independence missing")
        if "exact_union" in _parallel_roles(intent):
            _require(workers.get("independent_review_stage") in stage_ids and
                     workers.get("exact_union_stage") in stage_ids and
                     workers.get("conditional_reconciled_review_stage") in stage_ids,
                     "COMPILER_INVARIANT_FAILURE", "review/union/reconciled-review stages missing")
            _require(bool(workers.get("review_independent_of_writers")) and
                     isinstance(workers.get("union_paths"), list) and
                     len(workers["union_paths"]) == len(set(workers["union_paths"])) and
                     set(workers["union_paths"]) == set().union(*paths) and
                     bool(workers.get("reconciled_review_if_rewritten")) and
                     workers.get("worker_permanent_authority") is False,
                     "COMPILER_INVARIANT_FAILURE", "review independence or exact union missing")
    if data.get("retirement"):
        life = data["retirement"]
        _require(all(life.get(k) for k in ("exact_owned_surface", "authority_binding", "preservation_evidence",
                                            "retention_satisfied", "terminal_stage")),
                 "COMPILER_INVARIANT_FAILURE", "retirement lacks ownership, preservation or terminal gate")
        _require(life.get("cleanup_failure_invalidates_semantic_result") is False,
                 "COMPILER_INVARIANT_FAILURE", "cleanup failure cannot erase preserved semantic result")
        stage_ids = [stage["stage_id"] for stage in data.get("stages", [])]
        _require(bool(stage_ids) and stage_ids[-1] == life["terminal_stage"],
                 "COMPILER_INVARIANT_FAILURE", "retirement is not the last declared stage")
        _require(life["authority_binding"] in by_id and by_id[life["authority_binding"]].acquisition == "acquired",
                 "NOT_READY_MISSING_AUTHORITY_BINDING", "retirement authority binding not acquired")
        owned = by_id.get(life.get("ownership_readback_binding"))
        preserved = by_id.get(life.get("preservation_binding"))
        _require(owned is not None and owned.acquisition == "acquired" and
                 owned.source_kind == "repository_readback" and
                 preserved is not None and preserved.acquisition == "acquired" and
                 preserved.source_kind == "accepted_evidence",
                 "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
                 "retirement ownership and portable preservation provenance missing")
        _require(any(e.stage_id == life["terminal_stage"] and e.effect in {"delete_local_branch",
                    "delete_remote_branch"} and e.target == life["exact_owned_surface"] and
                    e.positive_authority_binding == life["authority_binding"] for e in effects),
                 "NOT_READY_MISSING_AUTHORITY_BINDING", "terminal retirement lacks exact delete effect")
        terminal = data["stages"][-1]
        _require(terminal["stage_mode"] == "branch_maintenance_only" and
                 terminal.get("branch_maintenance_action") == "delete_exact_temporary_ref" and
                 terminal.get("affected_local_branches") == [life["exact_owned_surface"]],
                 "COMPILER_INVARIANT_FAILURE", "terminal retirement lacks exact local lifecycle action")
    for step in intent.steps:
        if step.keyword == "Then":
            if step.text in intent.negative_assertions:
                edges.append(Trace_edge(f"line:{step.line}", f"constraint:line:{step.line}",
                                        "negative_boundary"))
                edges.append(Trace_edge("governance:AGENTS.md", f"constraint:line:{step.line}",
                                        "governed_boundary"))
            edges.append(Trace_edge(f"line:{step.line}", f"evidence_requirement:line:{step.line}",
                                    "requires_post_execution_evidence"))
            edges.append(Trace_edge(f"evidence_requirement:line:{step.line}",
                                    f"acceptance_assertion:line:{step.line}", "supports_assertion"))
            edges.append(Trace_edge(f"evidence_requirement:line:{step.line}",
                                    "evaluation_path:external_evidence_review", "evaluated_after_execution"))
            if data.get("stages"):
                validation_stage = ("readback" if shape == "dependent_continuation" else
                                    data["stages"][-1]["stage_id"] if shape == "ordered_workflow" else
                                    "pair_validation" if shape == "multi_repository_coordination" else
                                    "exact_union" if "exact_union" in _parallel_roles(intent) else "independent_review")
                edges.append(Trace_edge(f"acceptance_assertion:line:{step.line}",
                                        f"gate:{validation_stage}", "validated_at_gate"))
            else:
                edges.append(Trace_edge(f"acceptance_assertion:line:{step.line}",
                                        "prompt:validation_ceiling", "validated_by_prompt"))
    for line, index, gate in data["_assertion_paths"]:
        assertion = f"assertion:{line}:{index}"
        edges.append(Trace_edge(f"line:{line}", assertion, "material_clause"))
        edges.append(Trace_edge(assertion, gate, "requires_concrete_gate"))
        edges.append(Trace_edge(gate, f"evidence:{assertion}", "requires_clause_evidence"))
    return edges, authorized, excluded


def _validator(prompt: str, policy: Policy_source_binding) -> dict[str, Any]:
    locator = '.agents/skills/correction-lib-prompt-contract/scripts/validate_prompt.py'
    raw = policy.read(locator)
    # Execute the maintained, trusted canonical validator bytes from the same
    # frozen snapshot as governance, without a checkout-local import or launcher.
    module = types.ModuleType('maintained_prompt_validator')
    module.__file__ = str(policy.repository / locator)
    sys.modules[module.__name__] = module
    exec(compile(raw, module.__file__, 'exec'), module.__dict__)
    result = module.validate_content(prompt.encode("utf-8"), Path("generated_prompt.md"))
    return {"executed": True, "result": "pass" if result["results"]["mechanical_validity"] and
            result["results"]["internal_consistency"] else "fail", "limit": "mechanical_only",
            "locator": locator, "sha256": hashlib.sha256(raw).hexdigest(),
            "version": result["producer"]["version"],
            "mechanical_validity": result["results"]["mechanical_validity"],
            "internal_consistency": result["results"]["internal_consistency"],
            "governance_completeness": result["governance_completeness"]}


def _rule_routing(data: dict[str, Any], shape: str, effects: tuple[Effect_intent, ...],
                  contents: dict[str, str], roles: dict[str, dict[str, str]]) -> dict[str, str]:
    """Verify live rule-owner text for each emitted conditional mechanic."""
    routes = {"authority_and_scope": "AGENTS.md", "prompt_shape": "CPC.md",
              "typed_repository": "governance/repositories.md",
              "model_profile": "governance/model_policy.md",
              "evidence_and_review": "governance/contracts/review_and_evidence.md",
              "ambiguous_outcome": "governance/contracts/autonomy_and_blocker_classification.md"}
    if effects and any(e.effect in {"tracked_write", "local_git_ref_write", "delete_local_branch",
                                   "delete_remote_branch", "remote_git_write", "publication", "merge"} for e in effects):
        routes["git_lifecycle"] = "governance/contracts/git_lifecycle.md"
    if shape in {"orchestrated_workflow", "multi_repository_coordination", "ordered_workflow", "dependent_continuation", "controller_local_workflow"}:
        routes["stage_isolation"] = "governance/contracts/orchestration.md"
        routes["independent_review_prose"] = "CONTRIBUTING.md"
    if any("@production" in step.tags for step in data["_intent"].steps) or any(
            e.effect.startswith("scheduler_") or e.effect == "production_storage_write" for e in effects):
        routes["production_routing"] = "governance/contracts/production.md"
    for repo_id in roles:
        routes[f"native_policy:{repo_id}"] = _canonical_repository(repo_id, contents)
    required_text = {
        "git_lifecycle": ("authorized_commit_scope", "integration_source_branch", "expected_preserved_head"),
        "stage_isolation": ("stage_effect_permissions", "stage_inputs", "Independent means"),
        "independent_review_prose": ("Review notes",),
        "production_routing": ("production_action",),
        "model_profile": ("preferred_codex_model",),
        "evidence_and_review": ("DECISION_MATERIAL",),
        "ambiguous_outcome": ("OUTCOME_UNKNOWN",),
    }
    for family, path in routes.items():
        _require(path in contents and all(token in contents[path] for token in required_text.get(family, ())),
                 'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE', f"live rule owner incomplete for {family}")
    return routes


def _stage_readiness(graph: Result_graph, effects: tuple[Effect_intent, ...],
                     blocked_effects: set[str]) -> list[dict[str, Any]]:
    """Project static blockers and entry roots, never execute or supply outputs.

    Exact effect eligibility does not split a stage. Typed predecessors must
    actually publish their outputs after passed gates before a consumer enters.
    Runtime-checkable premises permit preflight entry, not unchecked effects.
    """
    rows: list[dict[str, Any]] = []
    blocked_stages: set[str] = set()
    for stage in graph.stages:
        predecessors = graph.predecessors(stage.stage_id)
        local = sorted(e.effect_id for e in effects if e.stage_id == stage.stage_id and
                       e.effect_id in blocked_effects)
        upstream = sorted(predecessors & blocked_stages)
        if local or upstream:
            blocked_stages.add(stage.stage_id)
        rows.append({"stage_id": stage.stage_id,
                     "required_predecessors": sorted(predecessors),
                     "blocked_by_effects": local, "blocked_by_stages": upstream,
                     "eligible_to_enter_preflight": not predecessors and not local})
    return rows


def compile_contract(gherkin: str, bindings_yaml: str, source_id: str = "inline", *,
                     policy_repository: Optional[Path] = None) -> Compile_result:
    """Return a candidate and receipt, or a diagnostic receipt with no prompt."""
    receipt: dict[str, Any] = {"source_contract": {"identity": source_id},
                              "compiler_identity": {"path": "tools/governance_workflow_compiler.py",
                                                    "sha256": _source_hash(Path(__file__)),
                                                    "modules": {name: _source_hash(Path(__file__).with_name(name))
                                                        for name in ('governance_workflow_ir.py',
                                                                     'governance_workflow_semantics.py')}},
                              "compiler_result": "COMPILER_DEFECT",
                              "manual_fallback": "independently_evaluable_under_canonical_governance",
                              "dispatchability": {"prepared": False, "conformant": False,
                                                  "owner_authorized": False, "dispatchable": False},
                              "execution_assertions": "NOT_EVALUATED",
                              "result_assertions": "NOT_EVALUATED",
                              "traceability": {"complete": False, "edges": []}}
    bindings: tuple[Binding, ...] = ()
    effects: tuple[Effect_intent, ...] = ()
    intent: Optional[Semantic_intent] = None
    shape: Optional[str] = None
    try:
        data = yaml.safe_load(bindings_yaml)
        _require(isinstance(data, dict), "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "binding input must be mapping")
        data = canonical_mapping(data)
        _require(isinstance(data.get("bindings", []), list) and
                 isinstance(data.get("requested_effects", []), list) and
                 isinstance(data.get("stages", []), list) and
                 isinstance(data.get("repositories", {}), dict),
                 "COMPILER_INVARIANT_FAILURE", "binding collections have invalid types")
        intent = parse_gherkin(gherkin, source_id)
        receipt["source_contract"].update({"feature": intent.feature,
            "feature_tags": list(intent.feature_tags), "scenarios": list(intent.scenarios),
            "scenario_tags": [list(tags) for tags in intent.scenario_tags]})
        try:
            policy = Policy_source_binding(policy_repository or ROOT)
        except (OSError, ValueError, subprocess.CalledProcessError) as exc:
            _error('NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE', f'canonical master unavailable: {exc}')
        contents, identities = _canonical_sources(policy)
        data['_policy_source'] = policy
        bindings = _bindings(data)
        effects = _effects(data, intent)
        intent = _normalize_semantics(intent, data, effects)
        if any(row.domain == "structured_action" for row in _partition_rows(intent)):
            effects = tuple(effect for row in _partition_rows(intent) for effect in row.effects)
        receipt["semantic_partition"] = asdict(intent.partition)
        continuation = _continuation(data)
        shape = _shape(data, intent, effects, bindings, continuation)
        if continuation and data.get("worker_contract") and shape == "orchestrated_workflow":
            protected = set(continuation.checks_not_to_repeat)
            receipt["reused_accepted_effects"] = [effect.effect_id for effect in effects
                                                   if effect.stage_id in protected]
            effects = tuple(effect for effect in effects if effect.stage_id not in protected)
            # The accepted postimage is portable. Historical carrier observations
            # may remain in the receipt, but cannot become executable preconditions.
            data["worker_contract"] = {**data["worker_contract"], "writers": [
                {key: value for key, value in worker.items()
                 if key not in {"branch", "base_oid", "observed_head", "worktree_path"}}
                if worker["stage_id"] in protected else worker
                for worker in data["worker_contract"]["writers"]]}
        if shape == "dependent_continuation":
            state = data["accepted_effect_state"]
            protected = set(state.get("completed_stages", []))
            receipt["reused_accepted_effects"] = [e.effect_id for e in effects if e.stage_id in protected]
            effects = tuple(e for e in effects if e.stage_id not in protected)
        if shape == "controller_local_workflow":
            context = data["prompt"]
            context["prompt_mode"] = "orchestrated_workflow"
            grants = context.pop("heavy_command_permissions", None)
            if grants is not None:
                _require("workflow_effect_envelope" not in context, "COMPILER_INVARIANT_FAILURE",
                         "conflicting outer permission maps")
                context["workflow_effect_envelope"] = grants
            context.pop("branch_policy", None)
            context.setdefault("workflow_goal", context["decision_question"])
            context.setdefault("workflow_stop_policy", "stop_on_failed_gate_or_new_decision_boundary")
            context.setdefault("workflow_stage_ledger_path", context["prompt_id"] + "_stage_ledger.yaml")
        data["_assertion_paths"] = _assertion_paths(intent, shape, data)
        receipt["selected_execution_shape"] = shape
        _check_closed_fields(data["prompt"], data.get("stages", []), contents)
        roles = _repository_modules(data, contents, identities)
        data["prompt"]["repository_branch_roles"] = roles
        data["prompt"]["repository_modules"] = {
            repo_id: {"module": _canonical_repository(repo_id, contents),
                      "native_policy": "applicable repository-native and upstream policy required"}
            for repo_id in roles}
        data["_intent"] = intent
        routes = _rule_routing(data, shape, effects, contents, roles)
        if shape in {"orchestrated_workflow", "multi_repository_coordination", "ordered_workflow", "dependent_continuation", "controller_local_workflow"}:
            data["stages"] = _plan_stages(data, intent, shape, effects, roles)
            if shape == "controller_local_workflow":
                for field in ("target_branch", "authorized_commit_scope", "explicitly_adopted_inherited_changes"):
                    data["prompt"].pop(field, None)
        try:
            data['_result_graph'] = Result_graph.from_stages(data.get('stages', []))
        except ValueError as exc:
            _error('COMPILER_INVARIANT_FAILURE', str(exc))
        tracked = any(effect.effect == "tracked_write" for effect in effects)
        expected_patch = "prompt_local" if tracked else "empty_no_changes"
        _require(data["prompt"].get("patch_kind_expected") == expected_patch,
                 "COMPILER_INVARIANT_FAILURE", f"patch_kind_expected must be {expected_patch} for generated plan")
        isolation_audit: dict[str, Any] = {"relation_local_consistency": False,
                                            "cross_role_isolation": False,
                                            "cross_repository_isolation": (False if shape == "multi_repository_coordination"
                                                                           else "not_applicable")}
        receipt["isolation_verification"] = isolation_audit
        edges, authorized, excluded = _verify(data, intent, bindings, effects, continuation, shape,
                                               contents, roles, isolation_audit)
        try:
            graph = Result_graph.from_stages(data.get('stages', []))
        except ValueError as exc:
            _error('COMPILER_INVARIANT_FAILURE', str(exc))
        data['_result_graph'] = graph
        receipt['result_graph'] = graph.projection()
        for stage in graph.stages:
            for ref in stage.inputs:
                edges.append(Trace_edge(ref.transport(), 'stage:' + stage.stage_id, 'consumes_result'))
        edges.sort(key=lambda edge: (edge.source, edge.output, edge.relation))
        required_relations: list[tuple[str, str]] = []
        if shape == "orchestrated_workflow":
            required_relations.extend((f"worker_contract.writers.{worker['stage_id']}.carrier",
                                       worker["stage_id"])
                                      for worker in data["worker_contract"]["writers"]
                                      if worker["stage_id"] not in
                                      (continuation.checks_not_to_repeat if continuation else ()))
            if "exact_union" in _parallel_roles(intent):
                required_relations.append(("worker_contract.composition_carrier", "exact_union"))
            if continuation:
                required_relations.append(("q04.accepted_writer_result", "exact_union"))
            if data.get("common_validation_contract"):
                required_relations.append(("common_validation.target_relation", "common_validation"))
        elif shape == "multi_repository_coordination":
            required_relations.extend((f"repositories.{repo_id}.candidate_carrier", repo["stage_id"])
                                      for repo_id, repo in data["repositories"].items())
            required_relations.append(("pair_validation.candidate_tuple", "pair_validation"))
            required_relations.extend((f"repositories.{repo_id}.permanent_target", "integrate_" + repo_id)
                                      for repo_id in data["candidate_pair_order"] if data["integration_stages"])
        if shape == "dependent_continuation":
            required_relations.append(("continuation.accepted_effect_state", "readback"))
        trace_complete = _trace_complete(intent, effects, data.get("stages", []), edges,
                                         data["_assertion_paths"], required_relations,
                                         isolation_audit.get("carrier_roles", []))
        receipt["traceability"] = {"complete": trace_complete, "edges": [asdict(e) for e in edges]}
        _require(trace_complete, "COMPILER_INVARIANT_FAILURE", "material semantic trace edge missing")
        visualization, workflow_diagram = _workflow_visualization(intent, data, shape, effects)
        receipt["workflow_visualization"] = visualization
        prompt_data = dict(data["prompt"])
        # Dispatch starts governed runtime preflight; it is not permission to
        # perform an effect before that effect's material checks have passed.
        blocked_effects = set(data.get("_blocked_given_effects", []))
        stage_readiness = _stage_readiness(graph, effects, blocked_effects)
        can_enter = not blocked_effects or any(row["eligible_to_enter_preflight"]
                                               for row in stage_readiness)
        runtime_responsibility = (
            "Runtime responsibility before dependent effects: read current master rules; "
            "verify the bound target and acquire material volatile facts only where consumed. ")
        if "git_lifecycle" in routes:
            runtime_responsibility += (
                "Verify repository/worktree/branch role, exact task/shared paths and conflicts, "
                "and the complete index before commit under the selected dirty-worktree policy. ")
        runtime_responsibility += (
            "Stop the dependent effect on ambiguous target/ownership, pertinent failed check "
            "or unresolved outcome. Do not retry an ambiguous effect without authoritative "
            "readback and exact idempotence or recovery authority. Author-side live readback "
            "is not required.")
        prompt_data["evidence_requirements"] = [*prompt_data.get("evidence_requirements", []),
                                                 runtime_responsibility]
        if data.get("stages"):
            prompt_data["evidence_requirements"].append(
                "Enter only stages whose typed predecessor outputs are available after passed "
                "acceptance gates. Every stage input, including material Given prerequisites, is a "
                "precondition before any effect in that stage. An unsupported material premise "
                "is unresolved evidence, never PASS or an executable check; acquire and revalidate "
                "it before its consumer can run. A blocked stage produces no outputs. Independent "
                "graph branches may progress under their own exact grants; dispatchability and "
                "authorized_effects do not waive any stage input or runtime check.")
        if data.get("stages"):
            prompt_data["workflow_stages"] = data["stages"]
        if continuation:
            prompt_data.update({key: value for key, value in asdict(continuation).items()
                                if key != "prior_artifact_identity"})
            prompt_data["continuation_of"] = continuation.prior_artifact_identity
        lines = [f"# {prompt_data['prompt_id']}", "", "## Semantic contract", ""]
        if intent.feature_tags:
            lines.append(" ".join(intent.feature_tags))
        lines.append(f"Feature: {intent.feature}")
        for scenario_index, (title, tags) in enumerate(zip(intent.scenarios, intent.scenario_tags)):
            if tags:
                lines.append(" ".join(tags))
            lines.append(f"Scenario: {title}")
            for step in intent.steps:
                if step.scenario_index == scenario_index:
                    lines.append(f"- [{step.semantic_id}] line {step.line} {step.source_keyword}: {step.text}")
        lines.extend(["", "## Workflow visualization", "",
                      "Arrows show dependencies; the separate stop panel shows failure exits. "
                      "derived_external_acceptance is an external evidence/owner boundary, not an execution stage.",
                      "", "```text", workflow_diagram, "```", ""])
        lines.extend(["", "## Bound CPC prompt candidate", "", "```yaml",
                      yaml.safe_dump(canonical_mapping(prompt_data), sort_keys=False, allow_unicode=True).rstrip(), "```", ""])
        lines.extend(["Node correspondence (documentary; never an effect grant):", "", "```yaml",
                      yaml.safe_dump({"workflow_visualization": visualization}, sort_keys=False).rstrip(), "```", ""])
        lines.extend(["## Post-execution evidence assertions", "",
                      "These assertions remain NOT_EVALUATED until separately authorized execution and evidence review."])
        lines.extend(f"- line {step.line}: {step.text}" for step in intent.steps if step.keyword == "Then")
        lines.append("")
        safety_constraints = {key: data[key] for key in ("worker_contract", "repositories", "candidate_pair_order",
                        "candidate_pair_validation_stage", "integration_stages", "partial_effects",
                        "partial_state_binding",
                        "multi_repository_state", "outcome_unknown", "readback_before_retry", "automatic_retry", "retirement",
                        "lifecycle_contract", "commit_contract", "accepted_effect_state",
                        "readback_authority_binding", "runtime_model_observation", "runtime_model_materiality",
                        "scientific_selection_binding")
                              if key in data}
        if safety_constraints:
            lines.extend(["## Bound safety and readback constraints", "", "```yaml",
                          yaml.safe_dump(canonical_mapping(safety_constraints), sort_keys=False, allow_unicode=True).rstrip(), "```", ""])
        prompt = "\n".join(lines)
        try:
            lint = _validator(prompt, policy)
        except (OSError, UnicodeError, ValueError, subprocess.CalledProcessError) as exc:
            _error('NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE', f'canonical validator unavailable: {exc}')
        _require(lint["result"] == "pass", "COMPILER_INVARIANT_FAILURE", "maintained mechanical validator failed")
        try:
            policy.revalidate()
        except (OSError, ValueError, subprocess.CalledProcessError) as exc:
            _error('NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE', f'canonical policy revalidation failed: {exc}')
        receipt['policy_source_binding'] = policy.receipt()
        by_binding_id = {binding.binding_id: binding for binding in bindings}
        dispatch_gate = data.get("dispatch_gate", {})
        owner_gate_binding = by_binding_id.get(dispatch_gate.get("owner_authorization_binding"))
        review_binding = by_binding_id.get(dispatch_gate.get("manual_governance_review_binding"))
        owner_ready = bool(owner_gate_binding and owner_gate_binding.acquisition == "acquired" and
                           owner_gate_binding.source_kind == "owner_decision")
        manual_conformant = bool(review_binding and review_binding.acquisition == "acquired" and
                                 review_binding.source_kind == "accepted_evidence")
        compiler_result = ("COMPILED_CONFORMING_CANDIDATE" if can_enter else
                           "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE")
        receipt.update({
            "source_contract": {"identity": source_id, "feature": intent.feature,
                                "feature_tags": list(intent.feature_tags),
                                "scenarios": list(intent.scenarios),
                                "scenario_tags": [list(tags) for tags in intent.scenario_tags],
                                "sha256": hashlib.sha256(gherkin.encode()).hexdigest()},
            "canonical_governance": {"applicable_sources": identities},
            "input_binding_identity": {"sha256": hashlib.sha256(bindings_yaml.encode()).hexdigest()},
            "given_readiness": data.get("_given_readiness", []),
            "stage_readiness": stage_readiness,
            "rule_routing": routes,
            "owner_decisions_bound": [b.binding_id for b in bindings if b.source_kind == "owner_decision"],
            "material_bindings": {state: [asdict(b) for b in bindings if b.acquisition == state]
                                  for state in ("acquired", "pending", "not_acquired", "last_observed")},
            "selected_execution_shape": shape,
            "execution_shape_classification": "SUPPORTED_EXECUTION_SHAPE",
            "requested_effects": [asdict(e) for e in effects],
            "authorized_effects": [effect_id for effect_id in authorized if effect_id not in blocked_effects],
            "excluded_effects": sorted(set(excluded) | blocked_effects),
            "unresolved_decisions": [],
            "unresolved_evidence": [b.binding_id for b in bindings
                                    if b.acquisition in {"pending", "not_acquired"} and
                                    not _historical_protected_carrier(b, continuation)] +
                                   ([] if owner_ready else ["owner_authorization_gate"]) +
                                   ([] if manual_conformant else ["manual_governance_review"]),
            "traceability": receipt["traceability"],
            "derived_fields": {"selected_execution_shape": DERIVATION, "prompt_mode": DERIVATION,
                               "canonical_vocabulary": READBACK, "authority_and_runtime_facts": READBACK,
                               "source_to_output_traceability": DERIVATION,
                               "unbound_scientific_selection": NEW_DECISION,
                               "unsupported_construct": UNSUPPORTED},
            "maintained_validator": lint, "compiler_result": compiler_result,
            "dispatchability": {"prepared": True, "conformant": manual_conformant,
                                "owner_authorized": owner_ready,
                                "dispatchable": owner_ready and manual_conformant and can_enter},
            "dispatch_gate_bindings": dispatch_gate,
            "dispatchability_limit": "binding_claims_require_separate_dispatch_and_external_acceptance",
            "generated_prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "historical_qualification": "NOT_EVALUATED",
            "safety_constraints": safety_constraints,
            "historical_case_readiness": {case_id: {"required_input": requirement,
                                                       "state": "NOT_EVALUATED"}
                                          for case_id, requirement in HISTORICAL_CASES.items()},
        })
        return Compile_result(compiler_result, prompt, receipt)
    except yaml.YAMLError as exc:
        exc = Compile_error("COMPILER_INVARIANT_FAILURE", f"invalid binding YAML: {exc}")
        receipt["compiler_result"] = exc.result
        receipt["diagnostics"] = [{"line": None, "message": str(exc)}]
        receipt["maintained_validator"] = {"executed": False, "result": "not_run", "limit": "mechanical_only"}
        return Compile_result(exc.result, "", receipt)
    except Compile_error as exc:
        receipt["compiler_result"] = exc.result
        if 'routes' in locals():
            receipt['rule_routing'] = routes
        if exc.result in {"UNSUPPORTED_CANONICAL_CONSTRUCT", "IMPLEMENTATION_GAP",
                          "ARCHITECTURE_BOUNDARY_UNRESOLVED"}:
            receipt["unsupported_construct"] = _architecture_boundary(exc, intent, effects, shape)
            receipt["execution_shape_classification"] = exc.result
        receipt["diagnostics"] = [{"line": exc.line, "message": str(exc)}]
        receipt["requested_effects"] = [asdict(effect) for effect in effects]
        receipt["authorized_effects"] = []
        receipt["excluded_effects"] = [effect.effect_id for effect in effects]
        receipt["material_bindings"] = {state: [asdict(b) for b in bindings if b.acquisition == state]
                                        for state in ("acquired", "pending", "not_acquired", "last_observed")}
        if isinstance(locals().get("data"), dict) and data.get("multi_repository_state") in {
                "PARTIAL", "PARTIALLY_INTEGRATED", "qualification_failed_after_effects"}:
            receipt["partial_state"] = {"state": data["multi_repository_state"],
                                        "observed_effects": data.get("partial_effects", {}),
                                        "readback_binding": data.get("partial_state_binding")}
        receipt["derived_fields"] = {"blocked_value": NEW_DECISION if exc.result == "NOT_READY_NEW_DECISION_BOUNDARY"
                                     else UNSUPPORTED if exc.result == "UNSUPPORTED_CANONICAL_CONSTRUCT"
                                     else READBACK}
        receipt["maintained_validator"] = {"executed": False, "result": "not_run", "limit": "mechanical_only"}
        return Compile_result(exc.result, "", receipt)
    except (AttributeError, IndexError, KeyError, StopIteration, TypeError, ValueError) as exc:
        receipt["compiler_result"] = "COMPILER_DEFECT"
        receipt["diagnostics"] = [{"line": None, "message": f"source/parser invariant failed: {exc}"}]
        receipt["maintained_validator"] = {"executed": False, "result": "not_run", "limit": "mechanical_only"}
        return Compile_result("COMPILER_DEFECT", "", receipt)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare a non-normative CPC prompt candidate and receipt; never dispatch.")
    parser.add_argument("--feature", type=Path, required=True, help="bounded UTF-8 Gherkin source")
    parser.add_argument("--bindings", type=Path, required=True, help="separate explicit authority/evidence YAML")
    parser.add_argument("--prompt-out", type=Path, required=True)
    parser.add_argument("--receipt-out", type=Path, required=True)
    parser.add_argument('--policy-repository', type=Path,
                        help='trusted canonical Git repository; policy is read only from refs/heads/master')
    args = parser.parse_args(argv)
    if args.prompt_out.exists() or args.receipt_out.exists():
        parser.error("output collision; choose absent exact paths")
    try:
        result = compile_contract(args.feature.read_text(encoding="utf-8"),
                                  args.bindings.read_text(encoding="utf-8"), str(args.feature),
                                  policy_repository=args.policy_repository)
        args.receipt_out.write_text(yaml.safe_dump(result.receipt, sort_keys=False), encoding="utf-8")
        if result.prompt:
            args.prompt_out.write_text(result.prompt, encoding="utf-8")
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        parser.error(str(exc))
    print(result.compiler_result)
    if result.receipt.get("diagnostics"):
        for diagnostic in result.receipt["diagnostics"]:
            print(f"line {diagnostic['line']}: {diagnostic['message']}")
    return 0 if result.compiler_result == "COMPILED_CONFORMING_CANDIDATE" else 3


if __name__ == "__main__":
    raise SystemExit(main())
