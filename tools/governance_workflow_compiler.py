"""Compile bounded Gherkin intent with separately acquired governance bindings.

This non-normative D8 tool prepares a CPC candidate. It never dispatches it.
The binding YAML is a task instance, not a policy registry or an authority source.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import hashlib
import importlib.util
from pathlib import Path
import re
import sys
from typing import Any, Optional

import yaml


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
    "remote_git_write": "remote_git_write", "network_read": "network_access",
    "scheduler_query": "scheduler_query", "scheduler_submit_condor": "condor_submission",
    "scheduler_submit_work_queue": "work_queue_or_lobster_submission",
    "production_storage_write": "storage_writes", "publication": "pr_or_mr_write",
    "merge": "pr_or_mr_merge", "delete_local_branch": "local_branch_deletion",
    "delete_remote_branch": "remote_branch_deletion", "unblind": "unblind",
}
EFFECT_ACTION_WORDS = {
    "tracked_write": r"\b(edit|write|modify|change|prepare)\b",
    "local_git_ref_write": r"\b(branch|ref|commit|integrat)\w*\b",
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
    "H6": "one exact current simple non-orchestrated manual prompt oracle",
}


@dataclass(frozen=True)
class Source_line:
    line: int
    keyword: str
    source_keyword: str
    text: str
    tags: tuple[str, ...] = ()
    scenario_index: int = 0


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


@dataclass(frozen=True)
class Effect_intent:
    effect_id: str
    effect: str
    target: str
    requested_by_step: int
    positive_authority_binding: str
    stage_id: str = ""


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
    def __init__(self, result: str, message: str, line: Optional[int] = None):
        super().__init__(message)
        self.result = result
        self.line = line


def _error(result: str, message: str, line: Optional[int] = None) -> None:
    raise Compile_error(result, message, line)


def _require(condition: bool, result: str, message: str, line: Optional[int] = None) -> None:
    if not condition:
        _error(result, message, line)


def _source_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sources() -> tuple[dict[str, str], dict[str, str]]:
    _require(set(ENCODED_RULE_OWNERS.values()) <= GOVERNANCE.keys(), "COMPILER_DEFECT",
             "encoded rule family lacks its live canonical owner")
    try:
        contents = {name: path.read_text(encoding="utf-8") for name, path in GOVERNANCE.items()}
        identities = {name: _source_hash(path) for name, path in GOVERNANCE.items()}
    except (OSError, UnicodeError) as exc:
        _error("UNSUPPORTED_CANONICAL_CONSTRUCT", f"live governance source unreadable: {exc}")
    return contents, identities


def _canonical_repository(repo_id: str, contents: dict[str, str]) -> str:
    for line in contents["governance/repositories.md"].splitlines():
        columns = [column.strip() for column in line.split("|")]
        if len(columns) < 9 or columns[1] != f"`{repo_id}`":
            continue
        _require(columns[2] not in {"`CONDITIONAL_INACTIVE`", "`KNOWN_OUT_OF_SCOPE_SURFACE`"},
                 "UNSUPPORTED_CANONICAL_CONSTRUCT", f"{repo_id!r} is inactive")
        module = columns[7]
        if module in {"root", "inherited"}:
            return ""
        matches = set(re.findall(r"modules/([a-z0-9_]+\.md)", module))
        _require(len(matches) == 1, "UNSUPPORTED_CANONICAL_CONSTRUCT",
                 f"{repo_id!r} has no uniquely selected module")
        return "governance/modules/" + next(iter(matches))
    _error("UNSUPPORTED_CANONICAL_CONSTRUCT", f"{repo_id!r} is not an active typed repository")


def _repository_modules(data: dict[str, Any], contents: dict[str, str],
                        identities: dict[str, str]) -> dict[str, dict[str, str]]:
    roles: dict[str, dict[str, str]] = {}
    for repo_id in data.get("repositories", {}):
        module = _canonical_repository(repo_id, contents)
        if not module:
            continue
        path = ROOT / module
        _require(path.is_file(), "UNSUPPORTED_CANONICAL_CONSTRUCT", f"selected module missing: {module}")
        try:
            body = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            _error("UNSUPPORTED_CANONICAL_CONSTRUCT", f"selected module unreadable: {exc}")
        contents[module] = body
        identities[module] = _source_hash(path)
        fields = ("permanent_live_development_branch", "permanent_personal_reference_branch",
                  "permanent_integration_branch", "feature_development_namespace")
        parsed = {}
        for field_name in fields:
            found = re.findall(r"^" + field_name + r": ([A-Za-z0-9_/*.-]+)$", body, re.M)
            _require(len(found) == 1, "UNSUPPORTED_CANONICAL_CONSTRUCT",
                     f"cannot uniquely parse {field_name} in {module}")
            parsed[field_name] = found[0]
        _require("native" in body.lower(), "UNSUPPORTED_CANONICAL_CONSTRUCT",
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
    _require(value in modes, "UNSUPPORTED_CANONICAL_CONSTRUCT", f"{value!r} is not a live prompt mode")


def _canonical_branch(value: str, contents: dict[str, str]) -> None:
    paragraph = contents["CPC.md"].split("Branch policies remain ", 1)[1].split("\n\n", 1)[0]
    _require(bool(re.search(r"(?<![A-Za-z0-9_])" + re.escape(value) + r"(?![A-Za-z0-9_])", paragraph)),
             "UNSUPPORTED_CANONICAL_CONSTRUCT", f"{value!r} is not a live branch policy")


def _canonical_ceiling(value: str, contents: dict[str, str]) -> None:
    section = contents["AGENTS.md"].split("Declare validation_ceiling:", 1)[1].split("## Reuse", 1)[0]
    values = set(re.findall(r"\b([a-z]+(?:_[a-z0-9]+)+) (?:permits|additionally permits|adds)\b", section))
    _require(value in values, "UNSUPPORTED_CANONICAL_CONSTRUCT",
             f"{value!r} is not a live validation ceiling")


def _canonical_model_field(key: str, value: str, contents: dict[str, str]) -> None:
    text = contents["governance/model_policy.md"]
    heading = {"preferred_codex_model": "Concrete Codex model labels:",
               "reasoning_level": "Reasoning levels:", "delegation_policy": "Delegation:"}[key]
    block = text.split(heading, 1)[1].split("```text", 1)[1].split("```", 1)[0]
    _require(value in block.split(), "UNSUPPORTED_CANONICAL_CONSTRUCT",
             f"{value!r} is not a live {key} value")


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
            _require(bool(allowed) and owner[key] in allowed, "UNSUPPORTED_CANONICAL_CONSTRUCT",
                     f"{owner[key]!r} is not a source-derived live {key} value")


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
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("@"):
            _require(bool(re.fullmatch(r"@[A-Za-z0-9_]+(?:\s+@[A-Za-z0-9_]+)*", line)),
                     "UNSUPPORTED_CANONICAL_CONSTRUCT", "invalid tag line", number)
            pending_tags.extend(line.split())
            continue
        if line.startswith("Feature:"):
            _require(not feature and not scenarios and bool(line[8:].strip()),
                     "UNSUPPORTED_CANONICAL_CONSTRUCT", "invalid or repeated Feature", number)
            feature = line[8:].strip()
            feature_tags = tuple(pending_tags)
            pending_tags.clear()
            continue
        if line.startswith("Scenario:"):
            _require(bool(feature) and bool(line[9:].strip()),
                     "UNSUPPORTED_CANONICAL_CONSTRUCT", "Scenario needs Feature and title", number)
            _require(not scenarios or len(steps) > prior_scenario_step_count,
                     "UNSUPPORTED_CANONICAL_CONSTRUCT", "previous Scenario has no steps", number)
            if scenarios:
                previous = steps[prior_scenario_step_count:]
                _require(any(step.keyword == "When" for step in previous) and
                         any(step.keyword == "Then" for step in previous),
                         "UNSUPPORTED_CANONICAL_CONSTRUCT", "previous Scenario lacks When or Then", number)
            scenarios.append(line[9:].strip())
            prior_scenario_step_count = len(steps)
            current_tags = tuple(pending_tags)
            scenario_tags.append(current_tags)
            pending_tags.clear()
            phase = ""
            continue
        match = re.fullmatch(r"(Given|When|Then|And|But)\s+(.+)", line)
        _require(match is not None and bool(scenarios), "UNSUPPORTED_CANONICAL_CONSTRUCT",
                 f"unsupported or misplaced Gherkin construct: {line}", number)
        keyword, body = match.groups()
        if keyword in {"And", "But"}:
            _require(bool(phase), "UNSUPPORTED_CANONICAL_CONSTRUCT", "And/But has no preceding step", number)
            effective = phase
        else:
            effective = keyword
            phase = keyword
        steps.append(Source_line(number, effective, keyword, body, feature_tags + current_tags,
                                 len(scenarios) - 1))
    _require(bool(feature and scenarios and steps) and len(steps) > prior_scenario_step_count and not pending_tags,
             "UNSUPPORTED_CANONICAL_CONSTRUCT", "Feature, Scenario, steps or tag target missing")
    latest = steps[prior_scenario_step_count:]
    _require(any(step.keyword == "When" for step in latest) and any(step.keyword == "Then" for step in latest),
             "UNSUPPORTED_CANONICAL_CONSTRUCT", "bounded Scenario needs When and observable Then")
    actions = tuple(step.text for step in steps if step.keyword == "When")
    assertions = tuple(step.text for step in steps if step.keyword == "Then")
    negative = tuple(step.text for step in steps if step.keyword == "Then" and
                     (step.source_keyword == "But" or re.search(r"\b(no|never|not|without)\b", step.text, re.I)))
    return Semantic_intent(source_id, feature, tuple(scenarios), tuple(steps), actions, assertions,
                           negative, feature_tags, tuple(scenario_tags))


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
                      "acquisition", "validity_scope", "effect", "target")),
                 "COMPILER_INVARIANT_FAILURE", "binding fields must be strings")
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


def _exact_related_identity(bindings: tuple[Binding, ...], identity_path: str,
                            values: dict[str, str], repo_id: str,
                            source_kind: str) -> str:
    _require(all(isinstance(value, str) and value for value in values.values()),
             "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
             f"{identity_path} has an incomplete exact relation")
    matches = [binding for binding in bindings
               if binding.acquisition == "acquired" and
               binding.materiality in {"IDENTITY_CRITICAL", "DECISION_MATERIAL"} and
               binding.source_kind == source_kind and
               _scope_names_repo(binding.validity_scope, repo_id) and
               binding.observed_state == {"identity_path": identity_path, "value": values}]
    _require(len(matches) == 1, "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
             f"{identity_path} lacks one exact acquired related readback")
    return matches[0].binding_id


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
        _require(effect.effect in EFFECT_KEYS, "UNSUPPORTED_CANONICAL_CONSTRUCT", f"unsupported effect {effect.effect}")
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


def _shape(data: dict[str, Any], intent: Semantic_intent, effects: tuple[Effect_intent, ...],
           bindings: tuple[Binding, ...], continuation: Optional[Continuation]) -> str:
    if continuation:
        _require(not data.get("worker_contract") and not data.get("multi_repository_state"),
                 "UNSUPPORTED_CANONICAL_CONSTRUCT",
                 "dependent Q03/Q05 continuation needs an exact delta planner; protected work cannot be replayed")
        return "continuation"
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
    if len(repositories) > 1 and len(changed_repositories) > 1:
        _require("provider" in action_text and "consumer" in action_text,
                 "UNSUPPORTED_CANONICAL_CONSTRUCT", "multi-repository dependency is outside bounded planner")
        return "multi_repository_coordination"
    if (re.search(r"\bwriters?\b", action_text) and re.search(r"\bedit\b", action_text) and
            len([effect for effect in effects if effect.effect == "tracked_write"]) >= 2):
        _require(bool(data.get("worker_contract")), "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
                 "parallel writers need bound isolation and review constraints")
        return "orchestrated_workflow"
    if len(intent.actions) > 1:
        _require(all(re.search(r"\b(inspect|read|compare|review|check|validate|report)\b", action, re.I)
                     for action in intent.actions), "UNSUPPORTED_CANONICAL_CONSTRUCT",
                 "multi-action serial pattern is outside bounded planner")
        return "serial_single_repository"
    return "simple_non_orchestrated"


def _planned_mode(shape: str, intent: Semantic_intent,
                  effects: tuple[Effect_intent, ...]) -> str:
    if shape in {"orchestrated_workflow", "multi_repository_coordination"}:
        return "orchestrated_workflow"
    kinds = {effect.effect for effect in effects}
    if kinds & {"scheduler_submit_condor", "scheduler_submit_work_queue", "production_storage_write"}:
        return "production_execution"
    if kinds & {"remote_git_write", "publication", "merge", "delete_remote_branch"}:
        return "pr_publication"
    if "delete_local_branch" in kinds:
        return "branch_maintenance_only"
    if "local_git_ref_write" in kinds and "tracked_write" not in kinds:
        return "integration_only" if "integrat" in " ".join(intent.actions).lower() else "branch_maintenance_only"
    if "tracked_write" in kinds:
        if all(effect.target.startswith("docs/") for effect in effects if effect.effect == "tracked_write") and \
                "document" in intent.feature.lower():
            return "documentation_only"
        return "coding"
    return "investigation_only"


def _assertion_paths(intent: Semantic_intent, shape: str,
                     data: dict[str, Any]) -> list[tuple[int, int, str]]:
    """Recognize bounded material clauses and name their concrete gate."""
    paths: list[tuple[int, int, str]] = []
    common_requested = False
    for step in intent.steps:
        if step.keyword != "Then":
            continue
        for index, raw in enumerate(re.split(r"\s+and\s+", step.text, flags=re.I), 1):
            clause = raw.strip().lower()
            if shape == "orchestrated_workflow":
                if re.fullmatch(r"(?:the )?exact union is reviewed", clause):
                    gate = "gate:exact_union"
                elif re.fullmatch(r"common validation passes", clause):
                    common_requested = True
                    _require(bool(data.get("common_validation_contract")),
                             "UNSUPPORTED_CANONICAL_CONSTRUCT",
                             "common validation needs an exact supplied validation contract", step.line)
                    _require(data.get("prompt", {}).get("validation_ceiling") == "targeted_unit_test",
                             "UNSUPPORTED_CANONICAL_CONSTRUCT",
                             "common validation exceeds the frozen validation ceiling", step.line)
                    gate = "gate:common_validation"
                else:
                    _error("UNSUPPORTED_CANONICAL_CONSTRUCT", f"unsupported material Then clause: {raw}", step.line)
            elif shape == "multi_repository_coordination":
                _require(bool(re.fullmatch(r"(?:the )?pair is validated", clause)),
                         "UNSUPPORTED_CANONICAL_CONSTRUCT",
                         f"unsupported material Then clause: {raw}", step.line)
                gate = "gate:pair_validation"
            else:
                simple = (r"(?:the )?report cites evidence|docs/[\w.-]+ is validated|"
                          r"(?:the )?branch appears|output exists|success|"
                          r"it exists|"
                          r"(?:the )?result(?: [\w.-]+)? is (?:reported|ready)|"
                          r"[\w.-]+ is reported|no remote repository is modified")
                _require(bool(re.fullmatch(simple, clause)), "UNSUPPORTED_CANONICAL_CONSTRUCT",
                         f"unsupported material Then clause: {raw}", step.line)
                gate = "prompt:validation_ceiling"
            paths.append((step.line, index, gate))
    _require(not data.get("common_validation_contract") or common_requested,
             "UNSUPPORTED_CANONICAL_CONSTRUCT",
             "common validation contract has no requested assertion")
    return paths


def _plan_stages(data: dict[str, Any], intent: Semantic_intent, shape: str, effects: tuple[Effect_intent, ...],
                 roles: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    """Build the two bounded dependent patterns; supplied stage prose is inert.

    Historical stage input binds no executable value. Exact identities arrive
    through the typed worker and repository bindings.
    """
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
    integration_action = r"\bintegrat\w*\b|\badvance\s+(?:the\s+)?(?:integration\s+)?(?:branch|ref|target)\b"
    if shape == "orchestrated_workflow":
        _require(bool(re.search(integration_action, " ".join(intent.actions), re.I)),
                 "UNSUPPORTED_CANONICAL_CONSTRUCT",
                 "integration stage has no requested integration or advancement behavior")
        workers = data.get("worker_contract", {})
        writers = workers.get("writers", [])
        _require(len(writers) == 2 and [w.get("stage_id") for w in writers] == ["writer_a", "writer_b"],
                 "UNSUPPORTED_CANONICAL_CONSTRUCT", "bounded planner supports two named disjoint writers")
        _require(len(data["repositories"]) == 1, "UNSUPPORTED_CANONICAL_CONSTRUCT",
                 "parallel writer pattern needs one repository")
        repo_id = next(iter(data["repositories"]))
        for worker in writers:
            stage_id = worker["stage_id"]
            branch = worker.get("branch")
            _require(bool(branch and worker.get("base_oid") and worker.get("worktree_path") and
                          worker.get("observed_head")), "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
                     f"{stage_id} needs exact existing worker branch/worktree/base identities")
            paths = worker.get("write_paths", [])
            _require(sorted(paths) == sorted(e.target for e in stage_effects(stage_id)
                                                if e.effect == "tracked_write"),
                     "NOT_READY_MISSING_AUTHORITY_BINDING", f"{stage_id} paths lack exact effects")
            item = make(stage_id, "coding", f"Write and commit {stage_id} owned paths",
                        [f"base:{worker['base_oid']}", f"worktree:{worker['worktree_path']}",
                         f"head:{worker['observed_head']}"],
                        "reopen exact diff, commit and frozen postimages", ["observed_commit_head", "frozen_postimages"])
            item.update(stage_branch_policy="continue_existing_branch", target_branch=branch,
                        authorized_commit_scope={repo_id: paths}, explicitly_adopted_inherited_changes="none",
                        foreign_dirty_change_policy="preserve_and_exclude", staging_policy="exact_path_only")
            item["stage_effect_permissions"] = {"allowed_to_modify": local_scope(repo_id, paths, branch)}
            stages.append(item)
        stages.append(make("independent_review", "validation_only", "Independently review frozen writer results",
                           ["stage:writer_a:observed_commit_head", "stage:writer_b:observed_commit_head"],
                           "independent reviewer findings disposed", ["review_evidence"]))
        union_paths = workers.get("union_paths", [])
        composition_branch = workers.get("composition_branch")
        _require(bool(workers.get("composition_base_oid") and workers.get("composition_worktree_path")),
                 "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "composition carrier identity missing")
        _require(bool(composition_branch) and sorted(union_paths) ==
                 sorted(e.target for e in stage_effects("exact_union") if e.effect == "tracked_write"),
                 "NOT_READY_MISSING_AUTHORITY_BINDING", "exact union needs bound composition branch and write effects")
        item = make("exact_union", "coding", "Compose exact frozen byte union and commit controller candidate",
                    ["stage:writer_a:observed_commit_head", "stage:writer_b:observed_commit_head",
                     "stage:independent_review:review_evidence",
                     f"base:{workers['composition_base_oid']}",
                     f"worktree:{workers['composition_worktree_path']}"],
                    "exact byte union, independent combined semantic review and committed candidate readback",
                    ["observed_commit_head", "union_postimages", "combined_review_evidence"])
        item.update(stage_branch_policy="continue_existing_branch", target_branch=composition_branch,
                    authorized_commit_scope={repo_id: union_paths}, explicitly_adopted_inherited_changes="none",
                    foreign_dirty_change_policy="preserve_and_exclude", staging_policy="exact_path_only")
        item["stage_effect_permissions"] = {"allowed_to_modify": local_scope(repo_id, union_paths, composition_branch)}
        stages.append(item)
        stages.append(make("reconciled_review", "validation_only",
                           "Review any controller rewrite of worker postimages",
                           ["stage:exact_union:union_postimages"],
                           "if a worker postimage changed, independent review and validation of that surface pass",
                           ["reconciled_review_evidence"]))
        if data.get("common_validation_contract"):
            contract = data["common_validation_contract"]
            _require(isinstance(contract, dict) and set(contract) ==
                     {"test_target", "target", "acceptance_gate"} and
                     all(isinstance(value, str) and value.strip() for value in contract.values()),
                     "UNSUPPORTED_CANONICAL_CONSTRUCT", "common validation contract is not exact")
            _require(bool(re.fullmatch(r"tests/(?!.*\.\.)[A-Za-z0-9_./-]+\.py(?:::test_[A-Za-z0-9_]+)?",
                                       contract["test_target"])),
                     "UNSUPPORTED_CANONICAL_CONSTRUCT", "common validation needs a bounded named test target")
            _require(contract["target"] == workers.get("composition_branch"),
                     "UNSUPPORTED_CANONICAL_CONSTRUCT", "common validation target is not composed candidate")
            stages.append(make("common_validation", "validation_only",
                               "Run supplied targeted unit test through resolved wrapper and interpreter",
                               ["stage:exact_union:observed_commit_head", "stage:reconciled_review:reconciled_review_evidence",
                                f"target:{contract['target']}"], contract["acceptance_gate"],
                               ["common_validation_evidence"]))
            stages[-1]["validation_test_target"] = contract["test_target"]
        integration_effect = stage_effects("integration")
        target = workers.get("integration_target_branch")
        _require(len(integration_effect) == 1 and integration_effect[0].effect == "local_git_ref_write" and
                 integration_effect[0].target == "refs/heads/" + str(target),
                 "NOT_READY_MISSING_AUTHORITY_BINDING", "integration needs exact target ref effect")
        integration_inputs = ["stage:exact_union:observed_commit_head",
                              "stage:reconciled_review:reconciled_review_evidence"]
        if data.get("common_validation_contract"):
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
        life = data.get("retirement", {})
        _require(life.get("exact_owned_surface") and life.get("exact_old_oid") and
                 life.get("preservation_ref") and life.get("expected_preserved_head") and
                 re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", life["exact_old_oid"]) and
                 re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", life["expected_preserved_head"]),
                 "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "retirement identity/preservation inputs missing")
        item = make("retirement", "branch_maintenance_only", "Retire exact owned temporary ref",
                    ["stage:integration:observed_target_head", "portable preservation evidence",
                     "reopened semantic and review gates"],
                    "exact old-OID compare-and-delete and ref/worktree readback",
                    ["retirement_readback"])
        item.update(stage_branch_policy="continue_existing_branch", target_branch=target,
                    branch_maintenance_action="delete_exact_temporary_ref",
                    affected_local_branches=[life["exact_owned_surface"]],
                    expected_preserved_head=life["expected_preserved_head"],
                    preservation_ref=life["preservation_ref"], reference_restore_source="none: deletion only",
                    non_fast_forward_ref_move_authorized="no", local_branch_deletion="yes",
                    remote_branch_deletion="no", expected_old_oid=life["exact_old_oid"],
                    safety_critical_ref_command=("git update-ref -d " + life["exact_owned_surface"] + " " +
                                                 life["exact_old_oid"]))
        item["stage_effect_permissions"] = {"allowed_to_modify": {repo_id: {
            "local_refs": [life["exact_owned_surface"]], "git_effects": ["delete_exact_temporary_ref"]}},
                                            "local_branch_deletion": "yes"}
        stages.append(item)
    else:
        _require(bool(re.search(integration_action, " ".join(intent.actions), re.I)),
                 "UNSUPPORTED_CANONICAL_CONSTRUCT",
                 "integration stages have no requested integration or advancement behavior")
        _require(data.get("multi_repository_state") == "NOT_STARTED",
                 "UNSUPPORTED_CANONICAL_CONSTRUCT",
                 "partial or completed multi-repository state needs a separately bound recovery/continuation plan")
        repo_ids = list(data["repositories"])
        _require(len(repo_ids) == 2 and repo_ids == data.get("candidate_pair_order"),
                 "UNSUPPORTED_CANONICAL_CONSTRUCT", "bounded provider/consumer plan needs exact ordered pair")
        for position, repo_id in enumerate(repo_ids):
            stage_id = ("provider_candidate", "consumer_candidate")[position]
            role = roles.get(repo_id)
            _require(role is not None, "UNSUPPORTED_CANONICAL_CONSTRUCT", "candidate repository needs native module")
            repo = data["repositories"][repo_id]
            branch = role["permanent_live_development_branch"]
            _require(repo.get("development_branch") == branch and repo.get("stage_id") == stage_id,
                     "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", f"{repo_id} live branch identity mismatch")
            _require(bool(re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", str(repo.get("base", "")))) and
                     repo.get("candidate") == f"stage:{stage_id}:observed_commit_head",
                     "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
                     f"{repo_id} needs exact base and derived observed candidate binding")
            paths = [e.target for e in stage_effects(stage_id) if e.effect == "tracked_write"]
            _require(bool(paths), "NOT_READY_MISSING_AUTHORITY_BINDING", f"{repo_id} candidate lacks tracked effect")
            item = make(stage_id, "coding", f"Write and commit {repo_id} candidate",
                        [f"{repo_id} observed base {repo.get('base')} and native policy"],
                        "reopen local commit, task diff and native-policy evidence", ["observed_commit_head"])
            item.update(repository_id=repo_id, stage_branch_policy="continue_existing_branch", target_branch=branch,
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
                           "task-specific compatibility evidence reopened", ["candidate_pair_evidence"]))
        prompt["candidate_pair"] = {repo_id: data["repositories"][repo_id]["candidate"]
                                    for repo_id in repo_ids}
        for position, repo_id in enumerate(repo_ids):
            stage_id = ("integrate_provider", "integrate_consumer")[position]
            source_stage = ("provider_candidate", "consumer_candidate")[position]
            target = roles[repo_id]["permanent_integration_branch"]
            matched = stage_effects(stage_id)
            _require(len(matched) == 1 and matched[0].effect == "local_git_ref_write" and
                     matched[0].target == "refs/heads/" + target,
                     "NOT_READY_MISSING_AUTHORITY_BINDING", f"{repo_id} integration target lacks exact authority")
            item = make(stage_id, "integration_only", f"Integrate exact {repo_id} candidate",
                        [f"stage:{source_stage}:observed_commit_head", "stage:pair_validation:candidate_pair_evidence"],
                        "local fast-forward and repo-local readback pass", ["observed_target_head"])
            item.update(repository_id=repo_id, stage_branch_policy="continue_existing_branch", target_branch=target,
                        integration_source_branch=roles[repo_id]["permanent_live_development_branch"],
                        integration_target_branch=target, integration_method="ff_only",
                        expected_source_head=f"stage:{source_stage}:observed_commit_head")
            item["stage_effect_permissions"] = {"allowed_to_modify": {repo_id: {
                "git_index_entries": [e.target for e in effects if e.stage_id == source_stage and
                                      e.effect == "tracked_write"],
                "local_refs": [matched[0].target], "git_effects": ["integrate_exact_source"]}}}
            stages.append(item)
    _require({e.stage_id for e in effects} <= {s["stage_id"] for s in stages},
             "UNSUPPORTED_CANONICAL_CONSTRUCT", "effect targets an unsupported stage role")
    when = next(step for step in intent.steps if step.keyword == "When")
    then = next(step for step in intent.steps if step.keyword == "Then")
    for item in stages:
        role = item["stage_id"]
        rule = ("governance/contracts/git_lifecycle.md" if item["stage_mode"] in
                {"coding", "integration_only", "branch_maintenance_only"} else
                "governance/contracts/review_and_evidence.md")
        item["generation_provenance"] = {
            "role": role, "semantic_line": when.line if item["stage_mode"] in
            {"coding", "integration_only", "branch_maintenance_only"} else then.line,
            "rule_source": rule, "evidence_gate": "gate:" + role,
            "provenance_class": ("necessary_governance_mechanic" if role in
                                 {"independent_review", "reconciled_review"} else "requested_behavior")}
    return stages


def _stage_trace(data: dict[str, Any], intent: Semantic_intent,
                 effects: tuple[Effect_intent, ...], shape: str) -> list[Trace_edge]:
    stages = data.get("stages", [])
    if shape not in {"orchestrated_workflow", "multi_repository_coordination"}:
        _require(not stages and not data.get("worker_contract"), "COMPILER_INVARIANT_FAILURE",
                 "caller stages are not a compiler-selected minimum-sufficient workflow")
        return []
    _require(bool(stages), "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
             "semantic workflow needs bound stage details")
    when = next((step for step in intent.steps if step.keyword == "When"), None)
    then = next((step for step in intent.steps if step.keyword == "Then"), None)
    _require(when is not None and then is not None, "COMPILER_INVARIANT_FAILURE",
             "workflow needs action and observable result")
    if shape == "orchestrated_workflow":
        _require(bool(re.search(r"\b(review|validat|union)\w*\b", then.text, re.I)),
                 "COMPILER_INVARIANT_FAILURE", "review stages lack observable Then behavior")
        workers = data["worker_contract"]
        expected = [worker["stage_id"] for worker in workers.get("writers", [])]
        expected += [workers.get("independent_review_stage"), workers.get("exact_union_stage"),
                     workers.get("conditional_reconciled_review_stage")]
        if data.get("common_validation_contract"):
            expected.append("common_validation")
        expected += [effect.stage_id for effect in effects if effect.effect in
                     {"local_git_ref_write", "delete_local_branch", "delete_remote_branch"} and
                     effect.stage_id not in {"writer_a", "writer_b", "exact_union"}]
    else:
        _require("pair" in then.text.lower() and "validat" in then.text.lower(),
                 "COMPILER_INVARIANT_FAILURE", "candidate-pair stage lacks observable Then behavior")
        expected = [repo.get("stage_id") for repo in data["repositories"].values()]
        expected += ["independent_review", data.get("candidate_pair_validation_stage")]
        expected += data.get("integration_stages", [])
        _require("integrat" in when.text.lower() or not data.get("integration_stages"),
                 "COMPILER_INVARIANT_FAILURE", "integration stages lack requested action")
    actual = [stage.get("stage_id") for stage in stages]
    _require(actual == expected and all(expected) and len(set(expected)) == len(expected),
             "COMPILER_INVARIANT_FAILURE", "supplied stages differ from semantic minimum-sufficient plan")
    edges = []
    for stage in stages:
        stage_id = stage["stage_id"]
        provenance = stage.get("generation_provenance", {})
        _require(provenance.get("role") == stage_id and
                 provenance.get("semantic_line") in {when.line, then.line} and
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
                    assertion_paths: list[tuple[int, int, str]]) -> bool:
    pairs = {(edge.source, edge.output) for edge in edges}
    provenance = {(edge.source, edge.output) for edge in edges if edge.relation == "generated_from"}
    return (all((f"line:{step.line}", "semantic_intent") in pairs for step in intent.steps) and
            all((f"line:{step.line}", f"precondition_evidence:line:{step.line}") in pairs
                and (any(source == f"precondition_evidence:line:{step.line}" and
                         (target.startswith("binding:") or target.startswith("unresolved_readback:"))
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


def _verify(data: dict[str, Any], intent: Semantic_intent, bindings: tuple[Binding, ...],
            effects: tuple[Effect_intent, ...], continuation: Optional[Continuation],
            shape: str, contents: dict[str, str],
            roles: dict[str, dict[str, str]]) -> tuple[list[Trace_edge], list[str], list[str]]:
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
    for binding in bindings:
        if binding.materiality in {"IDENTITY_CRITICAL", "DECISION_MATERIAL"} and binding.acquisition != "acquired":
            _error("NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
                   f"material binding {binding.binding_id} is {binding.acquisition}")
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
    if shape in {"orchestrated_workflow", "multi_repository_coordination"}:
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
    if not effects:
        supported_words = (r"\b(inspect|read|compare|review|check|validate|report|production|publish|"
                           r"submit|edit|write|modify|change|move|advance|delete|retire|remove|"
                           r"merge|integrate|unblind|choose)\b")
        _require(all(re.search(supported_words, step.text, re.I) for step in intent.steps
                     if step.keyword == "When"), "UNSUPPORTED_CANONICAL_CONSTRUCT",
                 "action pattern is outside bounded planner")
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
        if repo_id in roles and stage.get("stage_mode") == "coding":
            _require(stage.get("target_branch") == roles[repo_id]["permanent_live_development_branch"],
                     "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", f"{repo_id} writer branch is not native live line")
    authorized: list[str] = []
    excluded: list[str] = []
    edges = [Trace_edge(f"line:{s.line}", "semantic_intent", "intent_or_assertion") for s in intent.steps]
    edges.append(Trace_edge("semantic_intent", "prompt:prompt_mode", "selects_minimum_shape"))
    edges.extend(Trace_edge(f"line:{s.line}", "prompt:prompt_mode", "requests_action")
                 for s in intent.steps if s.keyword == "When")
    edges.extend(stage_edges)
    def bind_identity(path: str, value: str, repo_id: str, stage_id: str, oid: bool = False) -> None:
        binding_id = _exact_identity(bindings, path, value, repo_id, oid)
        identity = f"identity:{path}={value}"
        edges.append(Trace_edge(f"binding:{binding_id}", identity, "observes_exact_value"))
        edges.append(Trace_edge(identity, f"stage:{stage_id}", "consumed_by"))

    if shape == "orchestrated_workflow":
        repo_id = next(iter(data["repositories"]))
        workers = data["worker_contract"]
        for worker in workers["writers"]:
            stage_id = worker["stage_id"]
            for key in ("branch", "base_oid", "observed_head", "worktree_path"):
                bind_identity(f"worker_contract.writers.{stage_id}.{key}", worker.get(key),
                              repo_id, stage_id, key.endswith("oid") or key == "observed_head")
        for key in ("composition_branch", "composition_base_oid", "composition_worktree_path"):
            bind_identity(f"worker_contract.{key}", workers.get(key), repo_id, "exact_union",
                          key.endswith("oid"))
        bind_identity("worker_contract.integration_target_branch", workers.get("integration_target_branch"),
                      repo_id, "integration")
    if shape == "multi_repository_coordination":
        for repo_id, repo in data["repositories"].items():
            for key in ("base", "development_branch"):
                bind_identity(f"repositories.{repo_id}.{key}", repo.get(key), repo_id,
                              repo["stage_id"], key == "base")
            bind_identity(f"repositories.{repo_id}.integration_branch",
                          roles[repo_id]["permanent_integration_branch"], repo_id,
                          "integrate_provider" if repo["stage_id"] == "provider_candidate" else "integrate_consumer")
    if data.get("retirement") and shape == "orchestrated_workflow":
        life = data["retirement"]
        repo_id = next(iter(data["repositories"]))
        for key in ("exact_old_oid", "expected_preserved_head"):
            _require(bool(re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", str(life.get(key, "")))),
                     "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", f"retirement.{key} is not an exact OID")
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
    for step in intent.steps:
        if step.keyword == "Given":
            edges.append(Trace_edge(f"line:{step.line}", f"precondition_evidence:line:{step.line}",
                                    "requires_acquisition_or_readback"))
            linked = data.get("given_bindings", {}).get(str(step.line))
            if linked:
                _require(linked in by_id and by_id[linked].acquisition == "acquired",
                         "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "Given binding not acquired", step.line)
                edges.append(Trace_edge(f"precondition_evidence:line:{step.line}",
                                        f"binding:{linked}", "resolved_by"))
            else:
                edges.append(Trace_edge(f"precondition_evidence:line:{step.line}",
                                        f"unresolved_readback:line:{step.line}", "requires_runtime_readback"))
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
                                                step.text, re.I):
            _require(any(effect.requested_by_step == step.line for effect in effects),
                     "NOT_READY_MISSING_AUTHORITY_BINDING", "mutating action lacks explicit effect and binding",
                     step.line)
    for effect in effects:
        source_step = next(step for step in intent.steps if step.line == effect.requested_by_step)
        implicit_commit = (effect.effect == "local_git_ref_write" and
                           any(other.effect == "tracked_write" and
                               other.requested_by_step == effect.requested_by_step for other in effects))
        _require(source_step.keyword == "When" and
                 (bool(re.search(EFFECT_ACTION_WORDS[effect.effect], source_step.text, re.I)) or implicit_commit),
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
                for category in ("tracked_paths", "git_index_entries", "local_refs"):
                    for target in area.get(category, []):
                        _require(_scope_contains(prompt["allowed_to_modify"].get(repo_id, {}), target) and
                                 _scope_contains(prompt["workflow_effect_envelope"].get(
                                     "allowed_to_modify", {}).get(repo_id, {}), target) and
                                 (any(effect.target == target or
                                     (category == "git_index_entries" and effect.effect == "tracked_write" and
                                      effect.target == target) for effect in local_effects) or
                                  (category == "git_index_entries" and stage["stage_mode"] == "integration_only" and
                                   any(e.effect == "tracked_write" and e.target == target and
                                       f"stage:{e.stage_id}:observed_commit_head" in stage["stage_inputs"]
                                       for e in effects))),
                                 "COMPILER_INVARIANT_FAILURE", f"{stage_id} has untraced or pooled {category} {target}")
            if stage["stage_mode"] == "coding":
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
    if data.get("runtime_model_observation") == "not_observable":
        _require(data.get("runtime_model_materiality") == "not_decision_material",
                 "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "exact runtime identity is decision-material")
    if data.get("multi_repository_state"):
        _require(not data.get("automatic_rollback") and not data.get("global_git_transaction"),
                 "COMPILER_INVARIANT_FAILURE", "multi-repository atomicity or rollback invented")
        _require(all(r.get("base") and r.get("candidate") and r.get("authority_binding")
                     for r in data.get("repositories", {}).values()),
                 "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "repo-local base/candidate/authority missing")
        _require(bool(data.get("candidate_pair_order")), "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
                 "candidate pair validation order missing")
        _require(data.get("candidate_pair_order") == list(data.get("repositories", {})),
                 "COMPILER_INVARIANT_FAILURE", "candidate tuple/order differs from repository binding order")
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
        _require(all(worker["stage_id"] in stage_ids and worker.get("isolated_worktree") for worker in workers["writers"]),
                 "COMPILER_INVARIANT_FAILURE", "writer isolation or stage missing")
        for worker in workers["writers"]:
            stage = next(stage for stage in data["stages"] if stage["stage_id"] == worker["stage_id"])
            _require(stage["stage_mode"] == "coding" and "stage_branch_policy" in stage,
                     "COMPILER_INVARIANT_FAILURE", "writer lacks coding mode or branch policy")
            _require(all(any(e.stage_id == worker["stage_id"] and e.effect == "tracked_write" and
                             e.target == path for e in effects) for path in worker["write_paths"]),
                     "COMPILER_INVARIANT_FAILURE", "writer path lacks stage-local authorized effect")
        _require(workers.get("independent_review_stage") in stage_ids and
                 workers.get("exact_union_stage") in stage_ids and
                 workers.get("conditional_reconciled_review_stage") in stage_ids,
                 "COMPILER_INVARIANT_FAILURE", "review/union/reconciled-review stages missing")
        _require(bool(workers.get("review_independent_of_writers")) and
                 workers.get("union_paths") == sorted(set().union(*paths)) and
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
                validation_stage = "pair_validation" if shape == "multi_repository_coordination" else "exact_union"
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


def _validator(prompt: str) -> dict[str, Any]:
    spec = importlib.util.spec_from_file_location("maintained_prompt_validator", VALIDATOR)
    _require(spec is not None and spec.loader is not None, "COMPILER_DEFECT", "validator import unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    result = module.validate_content(prompt.encode("utf-8"), Path("generated_prompt.md"))
    return {"executed": True, "result": "pass" if result["results"]["mechanical_validity"] and
            result["results"]["internal_consistency"] else "fail", "limit": "mechanical_only",
            "locator": str(VALIDATOR.relative_to(ROOT)), "version": result["producer"]["version"],
            "mechanical_validity": result["results"]["mechanical_validity"],
            "internal_consistency": result["results"]["internal_consistency"]}


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
    if shape in {"orchestrated_workflow", "multi_repository_coordination"}:
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
                 "UNSUPPORTED_CANONICAL_CONSTRUCT", f"live rule owner incomplete for {family}")
    return routes


def compile_contract(gherkin: str, bindings_yaml: str, source_id: str = "inline") -> Compile_result:
    """Return a candidate and receipt, or a diagnostic receipt with no prompt."""
    receipt: dict[str, Any] = {"source_contract": {"identity": source_id},
                              "compiler_identity": {"path": "tools/governance_workflow_compiler.py",
                                                    "sha256": _source_hash(Path(__file__))},
                              "compiler_result": "COMPILER_DEFECT",
                              "manual_fallback": "independently_evaluable_under_canonical_governance",
                              "dispatchability": {"prepared": False, "conformant": False,
                                                  "owner_authorized": False, "dispatchable": False},
                              "execution_assertions": "NOT_EVALUATED",
                              "result_assertions": "NOT_EVALUATED",
                              "traceability": {"complete": False, "edges": []}}
    bindings: tuple[Binding, ...] = ()
    effects: tuple[Effect_intent, ...] = ()
    try:
        data = yaml.safe_load(bindings_yaml)
        _require(isinstance(data, dict), "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", "binding input must be mapping")
        _require(isinstance(data.get("bindings", []), list) and
                 isinstance(data.get("requested_effects", []), list) and
                 isinstance(data.get("stages", []), list) and
                 isinstance(data.get("repositories", {}), dict),
                 "COMPILER_INVARIANT_FAILURE", "binding collections have invalid types")
        intent = parse_gherkin(gherkin, source_id)
        receipt["source_contract"].update({"feature": intent.feature,
            "feature_tags": list(intent.feature_tags), "scenarios": list(intent.scenarios),
            "scenario_tags": [list(tags) for tags in intent.scenario_tags]})
        contents, identities = _canonical_sources()
        bindings = _bindings(data)
        effects = _effects(data, intent)
        continuation = _continuation(data)
        shape = _shape(data, intent, effects, bindings, continuation)
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
        if shape in {"orchestrated_workflow", "multi_repository_coordination"}:
            data["stages"] = _plan_stages(data, intent, shape, effects, roles)
        tracked = any(effect.effect == "tracked_write" for effect in effects)
        expected_patch = "prompt_local" if tracked else "empty_no_changes"
        _require(data["prompt"].get("patch_kind_expected") == expected_patch,
                 "COMPILER_INVARIANT_FAILURE", f"patch_kind_expected must be {expected_patch} for generated plan")
        edges, authorized, excluded = _verify(data, intent, bindings, effects, continuation, shape, contents, roles)
        trace_complete = _trace_complete(intent, effects, data.get("stages", []), edges,
                                         data["_assertion_paths"])
        receipt["traceability"] = {"complete": trace_complete, "edges": [asdict(e) for e in edges]}
        _require(trace_complete, "COMPILER_INVARIANT_FAILURE", "material semantic trace edge missing")
        prompt_data = dict(data["prompt"])
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
                    lines.append(f"- line {step.line} {step.source_keyword}: {step.text}")
        lines.extend(["", "## Bound CPC prompt candidate", "", "```yaml",
                      yaml.safe_dump(prompt_data, sort_keys=False, allow_unicode=True).rstrip(), "```", ""])
        lines.extend(["## Post-execution evidence assertions", "",
                      "These assertions remain NOT_EVALUATED until separately authorized execution and evidence review."])
        lines.extend(f"- line {step.line}: {step.text}" for step in intent.steps if step.keyword == "Then")
        lines.append("")
        safety_constraints = {key: data[key] for key in ("worker_contract", "repositories", "candidate_pair_order",
                        "candidate_pair_validation_stage", "integration_stages", "partial_effects",
                        "partial_state_binding",
                        "multi_repository_state", "outcome_unknown", "readback_before_retry", "retirement",
                        "readback_authority_binding", "runtime_model_observation", "runtime_model_materiality",
                        "scientific_selection_binding")
                              if key in data}
        if safety_constraints:
            lines.extend(["## Bound safety and readback constraints", "", "```yaml",
                          yaml.safe_dump(safety_constraints, sort_keys=False, allow_unicode=True).rstrip(), "```", ""])
        prompt = "\n".join(lines)
        lint = _validator(prompt)
        _require(lint["result"] == "pass", "COMPILER_INVARIANT_FAILURE", "maintained mechanical validator failed")
        by_binding_id = {binding.binding_id: binding for binding in bindings}
        dispatch_gate = data.get("dispatch_gate", {})
        owner_gate_binding = by_binding_id.get(dispatch_gate.get("owner_authorization_binding"))
        review_binding = by_binding_id.get(dispatch_gate.get("manual_governance_review_binding"))
        live_binding = by_binding_id.get(dispatch_gate.get("live_applicability_binding"))
        owner_ready = bool(owner_gate_binding and owner_gate_binding.acquisition == "acquired" and
                           owner_gate_binding.source_kind == "owner_decision")
        manual_conformant = bool(review_binding and review_binding.acquisition == "acquired" and
                                 review_binding.source_kind == "accepted_evidence")
        live_ready = bool(live_binding and live_binding.acquisition == "acquired" and
                          live_binding.source_kind == "repository_readback")
        receipt.update({
            "source_contract": {"identity": source_id, "feature": intent.feature,
                                "feature_tags": list(intent.feature_tags),
                                "scenarios": list(intent.scenarios),
                                "scenario_tags": [list(tags) for tags in intent.scenario_tags],
                                "sha256": hashlib.sha256(gherkin.encode()).hexdigest()},
            "canonical_governance": {"applicable_sources": identities},
            "rule_routing": routes,
            "owner_decisions_bound": [b.binding_id for b in bindings if b.source_kind == "owner_decision"],
            "material_bindings": {state: [asdict(b) for b in bindings if b.acquisition == state]
                                  for state in ("acquired", "pending", "not_acquired", "last_observed")},
            "selected_execution_shape": shape,
            "requested_effects": [asdict(e) for e in effects],
            "authorized_effects": authorized, "excluded_effects": excluded,
            "unresolved_decisions": [],
            "unresolved_evidence": [b.binding_id for b in bindings if b.acquisition in {"pending", "not_acquired"}] +
                                   ([] if owner_ready else ["owner_authorization_gate"]) +
                                   ([] if manual_conformant else ["manual_governance_review"]) +
                                   ([] if live_ready else ["live_dispatch_applicability"]),
            "traceability": receipt["traceability"],
            "derived_fields": {"selected_execution_shape": DERIVATION, "prompt_mode": DERIVATION,
                               "canonical_vocabulary": READBACK, "authority_and_runtime_facts": READBACK,
                               "source_to_output_traceability": DERIVATION,
                               "unbound_scientific_selection": NEW_DECISION,
                               "unsupported_construct": UNSUPPORTED},
            "maintained_validator": lint, "compiler_result": "COMPILED_CONFORMING_CANDIDATE",
            "dispatchability": {"prepared": True, "conformant": manual_conformant,
                                "owner_authorized": owner_ready,
                                "dispatchable": owner_ready and manual_conformant and live_ready},
            "dispatch_gate_bindings": dispatch_gate,
            "dispatchability_limit": "binding_claims_require_separate_dispatch_and_external_acceptance",
            "generated_prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "historical_qualification": "NOT_EVALUATED",
            "safety_constraints": safety_constraints,
            "historical_case_readiness": {case_id: {"required_input": requirement,
                                                       "state": "NOT_EVALUATED"}
                                          for case_id, requirement in HISTORICAL_CASES.items()},
        })
        return Compile_result("COMPILED_CONFORMING_CANDIDATE", prompt, receipt)
    except yaml.YAMLError as exc:
        exc = Compile_error("COMPILER_INVARIANT_FAILURE", f"invalid binding YAML: {exc}")
        receipt["compiler_result"] = exc.result
        receipt["diagnostics"] = [{"line": None, "message": str(exc)}]
        receipt["maintained_validator"] = {"executed": False, "result": "not_run", "limit": "mechanical_only"}
        return Compile_result(exc.result, "", receipt)
    except Compile_error as exc:
        receipt["compiler_result"] = exc.result
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
    args = parser.parse_args(argv)
    if args.prompt_out.exists() or args.receipt_out.exists():
        parser.error("output collision; choose absent exact paths")
    try:
        result = compile_contract(args.feature.read_text(encoding="utf-8"),
                                  args.bindings.read_text(encoding="utf-8"), str(args.feature))
        args.receipt_out.write_text(yaml.safe_dump(result.receipt, sort_keys=False), encoding="utf-8")
        if result.prompt:
            args.prompt_out.write_text(result.prompt, encoding="utf-8")
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        parser.error(str(exc))
    print(result.compiler_result)
    if result.receipt.get("diagnostics"):
        for diagnostic in result.receipt["diagnostics"]:
            print(f"line {diagnostic['line']}: {diagnostic['message']}")
    return 0 if result.prompt else 3


if __name__ == "__main__":
    raise SystemExit(main())
