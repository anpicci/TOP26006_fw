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
    "governance/model_policy.md": ROOT / "governance/model_policy.md",
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


@dataclass(frozen=True)
class Semantic_intent:
    source_id: str
    feature: str
    scenarios: tuple[str, ...]
    steps: tuple[Source_line, ...]
    actions: tuple[str, ...]
    assertions: tuple[str, ...]
    negative_assertions: tuple[str, ...]


@dataclass(frozen=True)
class Binding:
    binding_id: str
    claim: str
    materiality: str
    source_kind: str
    source_identity: str
    acquisition: str
    validity_scope: str
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
    contents = {name: path.read_text(encoding="utf-8") for name, path in GOVERNANCE.items()}
    identities = {name: _source_hash(path) for name, path in GOVERNANCE.items()}
    return contents, identities


def _canonical_value(value: str, source: str, contents: dict[str, str]) -> None:
    _require(bool(re.search(r"(?<![A-Za-z0-9_])" + re.escape(value) + r"(?![A-Za-z0-9_])", contents[source])),
             "UNSUPPORTED_CANONICAL_CONSTRUCT", f"{value!r} is absent from live {source}")


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
    values = {"static_inspection_only", "lightweight_import_or_cli_probe", "targeted_unit_test",
              "workflow_dry_run_or_config_validation", "production_execution"}
    _require(value in values and value in section, "UNSUPPORTED_CANONICAL_CONSTRUCT",
             f"{value!r} is not a live validation ceiling")


def _canonical_model_field(key: str, value: str, contents: dict[str, str]) -> None:
    text = contents["governance/model_policy.md"]
    heading = {"preferred_codex_model": "Concrete Codex model labels:",
               "reasoning_level": "Reasoning levels:", "delegation_policy": "Delegation:"}[key]
    block = text.split(heading, 1)[1].split("```text", 1)[1].split("```", 1)[0]
    _require(value in block.split(), "UNSUPPORTED_CANONICAL_CONSTRUCT",
             f"{value!r} is not a live {key} value")


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
            pending_tags.clear()
            continue
        if line.startswith("Scenario:"):
            _require(bool(feature) and bool(line[9:].strip()),
                     "UNSUPPORTED_CANONICAL_CONSTRUCT", "Scenario needs Feature and title", number)
            _require(not scenarios or len(steps) > prior_scenario_step_count,
                     "UNSUPPORTED_CANONICAL_CONSTRUCT", "previous Scenario has no steps", number)
            scenarios.append(line[9:].strip())
            prior_scenario_step_count = len(steps)
            current_tags = tuple(pending_tags)
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
        steps.append(Source_line(number, effective, keyword, body, current_tags))
    _require(bool(feature and scenarios and steps) and len(steps) > prior_scenario_step_count and not pending_tags,
             "UNSUPPORTED_CANONICAL_CONSTRUCT", "Feature, Scenario, steps or tag target missing")
    actions = tuple(step.text for step in steps if step.keyword == "When")
    assertions = tuple(step.text for step in steps if step.keyword == "Then")
    negative = tuple(step.text for step in steps if step.source_keyword == "But" or
                     (step.keyword == "Then" and re.search(r"\b(no|never|not|without)\b", step.text, re.I)))
    return Semantic_intent(source_id, feature, tuple(scenarios), tuple(steps), actions, assertions, negative)


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


def _shape(data: dict[str, Any], continuation: Optional[Continuation]) -> str:
    stages = data.get("stages", [])
    repositories = data.get("repositories", {})
    if len(repositories) > 1:
        _require(bool(stages), "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
                 "multi-repository coordination needs repo-local ordered stages")
        return "multi_repository_coordination"
    if len(stages) > 1:
        return "orchestrated_workflow"
    if continuation:
        return "continuation"
    if data.get("serial_steps"):
        return "serial_single_repository"
    return "simple_non_orchestrated"


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
            shape: str, contents: dict[str, str]) -> tuple[list[Trace_edge], list[str], list[str]]:
    prompt = data.get("prompt", {})
    _require(isinstance(prompt, dict), "COMPILER_INVARIANT_FAILURE", "prompt must be mapping")
    _require(PROMPT_CORE <= prompt.keys(), "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
             "required current CPC prompt field missing")
    _require(not ({"executed", "accepted", "execution_complete", "result_accepted"} & prompt.keys()),
             "COMPILER_INVARIANT_FAILURE", "compile candidate cannot assert execution or acceptance")
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
        _require("heavy_command_permissions" in prompt, "COMPILER_INVARIANT_FAILURE",
                 "non-orchestrated positive grant map missing")
    for key in ("preferred_codex_model", "reasoning_level", "delegation_policy"):
        _require(bool(prompt.get(key)), "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE", f"{key} missing")
        _canonical_model_field(key, str(prompt[key]), contents)
    _canonical_ceiling(str(prompt.get("validation_ceiling", "")), contents)
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
    if any("@production" in step.tags for step in intent.steps):
        _require(any(effect.effect in {"production_storage_write", "scheduler_submit_condor",
                                       "scheduler_submit_work_queue"} for effect in effects),
                 "NOT_READY_MISSING_AUTHORITY_BINDING", "production tag routes to production contract but grants no effect",
                 next(step.line for step in intent.steps if "@production" in step.tags))
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
    for repo_id, repo in data.get("repositories", {}).items():
        _canonical_value(repo_id, "governance/repositories.md", contents)
        if repo_id != "TOP26006_fw" and repo.get("development_branch") == "master":
            _error("NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
                   f"{repo_id} master is not inferred development authority")
        if repo.get("authority_binding"):
            bound = by_id.get(repo["authority_binding"])
            _require(bound is not None and bound.acquisition == "acquired" and
                     repo_id in bound.validity_scope,
                     "NOT_READY_MISSING_AUTHORITY_BINDING", f"repo-local authority missing for {repo_id}")
    authorized: list[str] = []
    excluded: list[str] = []
    edges = [Trace_edge(f"line:{s.line}", "semantic_intent", "intent_or_assertion") for s in intent.steps]
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
        _require(source_step.keyword == "When" and
                 bool(re.search(EFFECT_ACTION_WORDS[effect.effect], source_step.text, re.I)),
                 "COMPILER_INVARIANT_FAILURE", f"{effect.effect} is not traced to matching When action",
                 effect.requested_by_step)
        binding = by_id.get(effect.positive_authority_binding)
        _require(binding is not None and binding.acquisition == "acquired" and
                 binding.source_kind == "owner_decision" and binding.authorizes_effect and
                 binding.effect == effect.effect and binding.target == effect.target,
                 "NOT_READY_MISSING_AUTHORITY_BINDING", f"{effect.effect} lacks exact positive owner binding",
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
            if not data.get("stages"):
                _require(_scope_contains(prompt.get("authorized_commit_scope", {}), effect.target) and
                         prompt.get("explicitly_adopted_inherited_changes") == "none" and
                         prompt.get("foreign_dirty_change_policy") == "preserve_and_exclude" and
                         prompt.get("staging_policy") == "exact_path_only",
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
                      Trace_edge(f"binding:{binding.binding_id}", f"effect:{effect.effect_id}", "authorizes")))
    grant_maps = [prompt.get("heavy_command_permissions", {})] if not data.get("stages") else [
        stage["stage_effect_permissions"] for stage in data["stages"]]
    for grants in grant_maps:
        for key in _positive_keys(grants):
            _require(any(_grant_key_matches_effect(key, e) and _declared_grant(e, prompt, data.get("stages", []))
                         for e in effects), "COMPILER_INVARIANT_FAILURE", f"untraced positive grant {key}")
    if data.get("stages"):
        for stage in data["stages"]:
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
                         repo_id in by_id[e.positive_authority_binding].validity_scope for e in effects),
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
        _require(any(e.stage_id == life["terminal_stage"] and e.effect in {"delete_local_branch",
                    "delete_remote_branch"} and e.target == life["exact_owned_surface"] and
                    e.positive_authority_binding == life["authority_binding"] for e in effects),
                 "NOT_READY_MISSING_AUTHORITY_BINDING", "terminal retirement lacks exact delete effect")
        terminal = data["stages"][-1]
        _require(terminal["stage_mode"] == "branch_maintenance_only" and
                 terminal.get("branch_maintenance_action") == "delete_exact_temporary_ref" and
                 terminal.get("affected_local_branches") == [life["exact_owned_surface"]],
                 "COMPILER_INVARIANT_FAILURE", "terminal retirement lacks exact local lifecycle action")
    for assertion in dict.fromkeys(intent.assertions + intent.negative_assertions):
        edges.append(Trace_edge(f"assertion:{assertion}", "evidence_requirement", "requires_post_execution_evidence"))
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
                              "result_assertions": "NOT_EVALUATED"}
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
        contents, identities = _canonical_sources()
        bindings = _bindings(data)
        effects = _effects(data, intent)
        continuation = _continuation(data)
        shape = _shape(data, continuation)
        edges, authorized, excluded = _verify(data, intent, bindings, effects, continuation, shape, contents)
        prompt_data = dict(data["prompt"])
        if data.get("stages"):
            prompt_data["workflow_stages"] = data["stages"]
        if continuation:
            prompt_data.update({key: value for key, value in asdict(continuation).items()
                                if key != "prior_artifact_identity"})
            prompt_data["continuation_of"] = continuation.prior_artifact_identity
        lines = [f"# {prompt_data['prompt_id']}", "", "## Semantic contract", "",
                 f"Feature: {intent.feature}"]
        for step in intent.steps:
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
                                "scenarios": list(intent.scenarios), "sha256": hashlib.sha256(gherkin.encode()).hexdigest()},
            "canonical_governance": {"applicable_sources": identities},
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
            "traceability": {"complete": True, "edges": [asdict(e) for e in edges]},
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
        receipt["derived_fields"] = {"blocked_value": NEW_DECISION if exc.result == "NOT_READY_NEW_DECISION_BOUNDARY"
                                     else UNSUPPORTED if exc.result == "UNSUPPORTED_CANONICAL_CONSTRUCT"
                                     else READBACK}
        receipt["maintained_validator"] = {"executed": False, "result": "not_run", "limit": "mechanical_only"}
        return Compile_result(exc.result, "", receipt)


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
