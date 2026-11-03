"""Current D8 functional checks; execution and owner acceptance remain external."""

import hashlib
from copy import deepcopy
import re
from pathlib import Path

import yaml
import pytest

from tools import governance_workflow_compiler as compiler
from tools.governance_workflow_compiler import HISTORICAL_CASES, compile_contract


SIMPLE = """Feature: bounded inspection
  # A comment remains inert.
  Scenario: inspect one document
    Given the document identity is acquired
    When I inspect the document
    Then the report cites evidence
    But no remote repository is modified
"""
PARALLEL = "Feature: parallel writers\nScenario: disjoint\nGiven isolated worktrees\nWhen writers edit, integrate, and retire branches\nThen exact union is reviewed"
MULTI_REPO = "Feature: provider consumer\nScenario: candidate pair\nGiven exact bases\nWhen provider and consumer write candidates\nThen the pair is validated"


def base_data():
    return {
        "bindings": [{
            "binding_id": "owner_task", "claim": "bounded inspection",
            "materiality": "DECISION_MATERIAL", "source_kind": "owner_decision",
            "source_identity": "owner:task-1", "acquisition": "acquired",
            "validity_scope": "TOP26006_fw bounded inspection",
            "authorizes_effect": False,
        }],
        "repositories": {"TOP26006_fw": {}},
        "prompt": {
            "prompt_id": "sample_q01", "short_title": "bounded_inspection",
            "prompt_mode": "investigation_only", "preferred_codex_model": "gpt-6-sol",
            "reasoning_level": "high", "delegation_policy": "forbidden",
            "model_selection_rationale": "bounded source inspection",
            "workspace_root": "/workspace", "repo_locations": {"TOP26006_fw": "/workspace"},
            "branch_policy": "read_only_current_branch",
            "allowed_to_modify": {"TOP26006_fw": {"storage_paths": ["diagnostics/sample_q01/"]}},
            "read_only": {"TOP26006_fw": ["AGENTS.md"]},
            "validation_ceiling": "static_inspection_only",
            "decision_question": "What does the bounded document show?",
            "patch_kind_expected": "empty_no_changes",
            "final_chat_deliverable": "Evidence-bounded report.",
            "heavy_command_permissions": {},
        },
    }


def run(feature=SIMPLE, data=None):
    return compile_fixture(feature, yaml.safe_dump(base_data() if data is None else data), "inline-case")


def fixture_graph(feature, bindings_yaml):
    """Migrate legacy behavioral fixtures; graph regressions use literal drawings.

    Three description lines keep original source-line dependencies mechanically
    rebindable. This helper is test-only and never repairs user input.
    """
    if '```text' in feature:
        return feature, bindings_yaml
    lines = feature.splitlines()
    insertion = next((i + 1 for i, line in enumerate(lines) if line.strip().startswith('Feature:')), 0)
    scenarios = []
    phase = None
    for i, line in enumerate(lines):
        if line.strip().startswith('Scenario:'):
            scenarios.append([])
            phase = None
        match = re.match(r'(\s*)(Given|When|Then|And|But) (.+)', line)
        if match and scenarios:
            indent, keyword, body = match.groups()
            phase = phase if keyword in {'And', 'But'} else keyword
            node = f's{i + 1}'
            scenarios[-1].append((node, phase))
            lines[i] = f'{indent}{keyword} [{node}] {body}'
    arrows = []
    for steps in scenarios:
        givens = [n for n, p in steps if p == 'Given']
        actions = [n for n, p in steps if p == 'When']
        assertions = [n for n, p in steps if p == 'Then']
        if actions:
            arrows += [(g, actions[0]) for g in givens]
            arrows += list(zip(actions, actions[1:]))
            arrows += [(actions[-1], t) for t in assertions]
    drawing = '    '.join(f'[{a}] --> [{b}]' for a, b in arrows)
    lines[insertion:insertion] = ['  ```text', '  ' + drawing, '  ```']
    data = yaml.safe_load(bindings_yaml)
    for effect in data.get('requested_effects', []):
        if effect['requested_by_step'] > insertion:
            effect['requested_by_step'] += 3
    if 'given_bindings' in data:
        data['given_bindings'] = {str(int(k) + 3 if int(k) > insertion else int(k)): v
                                  for k, v in data['given_bindings'].items()}
    return '\n'.join(lines), yaml.safe_dump(data, sort_keys=False)


def compile_fixture(feature, bindings_yaml, source_id='inline-case'):
    return compile_contract(*fixture_graph(feature, bindings_yaml), source_id)


def bind_state(data, identity_path, value, repo_id="TOP26006_fw"):
    data["bindings"].append({
        "binding_id": "state_" + str(len(data["bindings"])),
        "claim": identity_path, "materiality": "DECISION_MATERIAL",
        "source_kind": "repository_readback", "source_identity": "readback:" + identity_path,
        "acquisition": "acquired", "validity_scope": repo_id,
        "observed_state": {"identity_path": identity_path, "value": value},
    })


def bind_relation(data, identity_path, value, repo_id="TOP26006_fw",
                  source_kind="repository_readback"):
    """Capture a completed acquired observation, independent of current state."""
    data["bindings"].append({
        "binding_id": "relation_" + str(len(data["bindings"])),
        "claim": identity_path, "materiality": "IDENTITY_CRITICAL",
        "source_kind": source_kind, "source_identity": "readback:" + identity_path,
        "acquisition": "acquired", "validity_scope": repo_id,
        "observed_state": {"identity_path": identity_path, "value": deepcopy(value)},
    })


def add_effect(data, effect, target, line, permission, stage_id=""):
    data["bindings"].append({
        "binding_id": "owner_effect", "claim": effect, "materiality": "DECISION_MATERIAL",
        "source_kind": "owner_decision", "source_identity": "owner:effect-1",
        "acquisition": "acquired", "validity_scope": f"TOP26006_fw {target}",
        "authorizes_effect": True, "effect": effect, "target": target,
    })
    data["requested_effects"] = [{"effect_id": "effect_1", "effect": effect, "target": target,
                                  "requested_by_step": line, "positive_authority_binding": "owner_effect",
                                  "stage_id": stage_id}]
    if stage_id:
        next(s for s in data["stages"] if s["stage_id"] == stage_id)["stage_effect_permissions"][permission] = True
        data["prompt"]["workflow_effect_envelope"][permission] = True
    else:
        if permission != "allowed_to_modify":
            data["prompt"]["heavy_command_permissions"][permission] = True


def stage(stage_id, grants=None):
    return {"stage_id": stage_id, "stage_mode": "investigation_only", "stage_goal": stage_id,
            "stage_effect_permissions": grants or {}, "stage_inputs": ["bound source"],
            "stage_acceptance_gate": "reopen evidence", "stage_outputs": ["report"],
            "stage_failure_behavior": "preserve partial state"}


def orchestrated(data):
    data["prompt"]["prompt_mode"] = "orchestrated_workflow"
    del data["prompt"]["branch_policy"]
    del data["prompt"]["heavy_command_permissions"]
    data["prompt"]["workflow_effect_envelope"] = {}
    data["prompt"]["workflow_goal"] = "ordered bounded work"
    data["prompt"]["workflow_stop_policy"] = "stop_on_failed_gate_or_new_decision_boundary"
    data["prompt"]["workflow_stage_ledger_path"] = "diagnostics/stage_ledger.yml"
    data["stages"] = [stage("writer_a"), stage("review"), stage("join")]


def multi_repo_data():
    data = base_data()
    orchestrated(data)
    data["prompt"]["delegation_policy"] = "required"
    data["prompt"]["patch_kind_expected"] = "prompt_local"
    data["prompt"]["validation_ceiling"] = "targeted_unit_test"
    data["stages"] = [stage("provider_candidate"), stage("consumer_candidate"),
                      stage("independent_review"), stage("pair_validation")]
    data["repositories"] = {
        "topcoffea": {"base": "a" * 40, "candidate": "stage:provider_candidate:observed_commit_head", "authority_binding": "repo_a",
                      "stage_id": "provider_candidate", "development_branch": "tc/dev-live",
                      "candidate_branch": "tc/q05_candidate", "candidate_worktree": "/workspace/topcoffea_candidate",
                      "candidate_head": "a" * 40, "candidate_base_oid": "a" * 40,
                      "candidate_carrier_authority_binding": "commit_topcoffea_owner"},
        "topeft": {"base": "b" * 40, "candidate": "stage:consumer_candidate:observed_commit_head", "authority_binding": "repo_b",
                   "stage_id": "consumer_candidate", "development_branch": "te/datacard_sr_reco",
                   "candidate_branch": "te/q05_candidate", "candidate_worktree": "/workspace/topeft_candidate",
                   "candidate_head": "b" * 40, "candidate_base_oid": "b" * 40,
                   "candidate_carrier_authority_binding": "commit_topeft_owner"},
    }
    data["prompt"]["repo_locations"] = {"topcoffea": "/workspace/topcoffea",
                                         "topeft": "/workspace/topeft"}
    data["prompt"]["read_only"] = {"topcoffea": ["AGENTS.md"], "topeft": ["AGENTS.md"]}
    data["candidate_pair_order"] = ["topcoffea", "topeft"]
    data["candidate_pair_validation_stage"] = "pair_validation"
    data["integration_stages"] = []
    data["pair_validation_contract"] = {"test_target": "tests/test_candidate_pair.py::test_contract",
                                          "covers": ["provider", "consumer", "common"]}
    data["multi_repository_state"] = "NOT_STARTED"
    data["bindings"] += [{**data["bindings"][0], "binding_id": "repo_a", "validity_scope": "topcoffea"},
                         {**data["bindings"][0], "binding_id": "repo_b", "validity_scope": "topeft"}]
    for repo_id, stage_id, target, source_branch in (
            ("topcoffea", "provider_candidate", "file.py", "tc/q05_candidate"),
            ("topeft", "consumer_candidate", "file.py", "te/q05_candidate")):
        item = next(s for s in data["stages"] if s["stage_id"] == stage_id)
        item.update(repository_id=repo_id, stage_mode="coding",
                    stage_branch_policy="continue_existing_branch", target_branch=source_branch)
        item["stage_effect_permissions"] = {"allowed_to_modify": {repo_id: [target]}}
        data["bindings"].append({**data["bindings"][0], "binding_id": f"write_{repo_id}",
                                 "validity_scope": repo_id, "authorizes_effect": True,
                                 "effect": "tracked_write", "target": target})
        data.setdefault("requested_effects", []).append({"effect_id": f"write_{repo_id}",
            "effect": "tracked_write", "target": target, "requested_by_step": 4,
            "positive_authority_binding": f"write_{repo_id}", "stage_id": stage_id})
        source_ref = f"refs/heads/{source_branch}"
        data["bindings"].append({**data["bindings"][0], "binding_id": f"commit_{repo_id}_owner",
                                 "validity_scope": repo_id, "authorizes_effect": True,
                                 "effect": "local_git_ref_write", "target": source_ref})
        data["requested_effects"].append({"effect_id": f"commit_{repo_id}",
            "effect": "local_git_ref_write", "target": source_ref, "requested_by_step": 4,
            "positive_authority_binding": f"commit_{repo_id}_owner", "stage_id": stage_id})
        repo = data["repositories"][repo_id]
        bind_relation(data, f"repositories.{repo_id}.candidate_carrier",
                      {"repository": repo_id,
                       "permanent_live_development_branch": repo["development_branch"],
                       "permanent_live_head": repo["base"], "candidate_branch": repo["candidate_branch"],
                       "candidate_worktree": repo["candidate_worktree"], "candidate_head": repo["candidate_head"],
                       "candidate_base_oid": repo["candidate_base_oid"]}, repo_id)
    data["prompt"]["workflow_effect_envelope"] = {"allowed_to_modify": {
        "topcoffea": ["file.py", "refs/heads/tc/q05_candidate"],
        "topeft": ["file.py", "refs/heads/te/q05_candidate"]}}
    data["prompt"]["allowed_to_modify"] = data["prompt"]["workflow_effect_envelope"]["allowed_to_modify"]
    for repo_id in ("topcoffea", "topeft"):
        for key in ("base", "development_branch"):
            bind_state(data, f"repositories.{repo_id}.{key}", data["repositories"][repo_id][key], repo_id)
    bind_relation(data, "pair_validation.candidate_tuple",
                  {"validation_locator": data["pair_validation_contract"]["test_target"],
                   "covers": ["provider", "consumer", "common"],
                   "provider_repository": "topcoffea", "consumer_repository": "topeft",
                   "provider_head": "stage:provider_candidate:observed_commit_head",
                   "consumer_head": "stage:consumer_candidate:observed_commit_head"},
                  "topcoffea", "accepted_evidence")
    return data


def multi_repo_advancement_data():
    data = multi_repo_data()
    for repo_id, repo in data["repositories"].items():
        repo["permanent_target_branch"] = repo["development_branch"]
        target = "refs/heads/" + repo["permanent_target_branch"]
        data["prompt"]["allowed_to_modify"][repo_id].append(target)
        data["bindings"].append({**data["bindings"][0], "binding_id": "advance_" + repo_id,
                                 "validity_scope": repo_id, "authorizes_effect": True,
                                 "effect": "local_git_ref_write", "target": target})
        data["requested_effects"].append({"effect_id": "advance_" + repo_id,
            "effect": "local_git_ref_write", "target": target, "requested_by_step": 4,
            "positive_authority_binding": "advance_" + repo_id, "stage_id": "integrate_" + repo_id})
        bind_relation(data, f"repositories.{repo_id}.permanent_target",
                      {"repository": repo_id, "worktree": data["prompt"]["repo_locations"][repo_id],
                       "attached_branch": repo["permanent_target_branch"], "head": repo["base"]}, repo_id)
    return data


def test_q01_simple_read_only_and_traceability(tmp_path):
    result = run()
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    assert result.receipt["selected_execution_shape"] == "simple_non_orchestrated"
    assert result.receipt["authorized_effects"] == []
    assert "orchestrated_workflow" not in result.prompt
    assert any(edge["relation"] == "requires_post_execution_evidence"
               for edge in result.receipt["traceability"]["edges"])
    output = tmp_path / "prompt.md"
    output.write_text(result.prompt)
    assert output.read_text() == result.prompt


def documentation_data():
    data = base_data()
    data["prompt"].update(prompt_mode="documentation_only", branch_policy="create_feature_branch_from_reference",
                          reference_branch="master", feature_branch="docs/example",
                          validation_ceiling="targeted_unit_test", authorized_commit_scope={"TOP26006_fw": ["docs/a.md"]},
                          patch_kind_expected="prompt_local",
                          foreign_dirty_change_policy="preserve_and_exclude",
                          explicitly_adopted_inherited_changes="none", staging_policy="exact_path_only")
    commit_scope = {"TOP26006_fw": {"tracked_paths": ["docs/a.md"],
                                      "git_index_entries": ["docs/a.md"],
                                      "local_refs": ["refs/heads/docs/example"],
                                      "git_effects": ["create_feature_branch_from_reference",
                                                      "create_one_prompt_local_commit"]}}
    data["prompt"]["allowed_to_modify"] = commit_scope
    data["prompt"]["heavy_command_permissions"]["allowed_to_modify"] = commit_scope
    feature = "Feature: document\nScenario: edit\nGiven semantics are established\nWhen I edit docs/a.md\nThen docs/a.md is validated"
    add_effect(data, "tracked_write", "docs/a.md", 4, "allowed_to_modify")
    data["bindings"].append({**data["bindings"][0], "binding_id": "commit_owner",
                             "authorizes_effect": True, "effect": "local_git_ref_write",
                             "target": "refs/heads/docs/example"})
    data["requested_effects"].append({"effect_id": "commit_ref", "effect": "local_git_ref_write",
        "target": "refs/heads/docs/example", "requested_by_step": 4,
        "positive_authority_binding": "commit_owner"})
    return feature, data


def test_q02_bounded_documentation_mutation():
    feature, data = documentation_data()
    result = run(feature, data)
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    assert result.receipt["selected_execution_shape"] == "simple_non_orchestrated"
    assert result.receipt["authorized_effects"] == ["effect_1", "commit_ref"]
    assert "preserve_and_exclude" in result.prompt


def parallel_data():
    data = base_data()
    orchestrated(data)
    data["prompt"]["delegation_policy"] = "required"
    data["prompt"]["patch_kind_expected"] = "prompt_local"
    data["stages"] = [stage("writer_a"), stage("writer_b"), stage("independent_review"),
                      stage("exact_union"), stage("reconciled_review"), stage("integration"), stage("retirement")]
    for name in ("writer_a", "writer_b"):
        target = f"docs/{name}.md"
        writer = next(s for s in data["stages"] if s["stage_id"] == name)
        writer.update(stage_mode="coding", stage_branch_policy="create_feature_branch_from_reference",
                      reference_branch="master", feature_branch=f"temporary/{name}")
        writer["stage_effect_permissions"] = {"allowed_to_modify": {"TOP26006_fw": [target]}}
        data["bindings"].append({**data["bindings"][0], "binding_id": f"owner_{name}",
                                 "authorizes_effect": True, "effect": "tracked_write", "target": target})
        data.setdefault("requested_effects", []).append({"effect_id": name, "effect": "tracked_write",
            "target": target, "requested_by_step": 4, "positive_authority_binding": f"owner_{name}", "stage_id": name})
        branch_ref = f"refs/heads/temporary/{name}"
        data["bindings"].append({**data["bindings"][0], "binding_id": f"commit_{name}_owner",
                                 "authorizes_effect": True, "effect": "local_git_ref_write", "target": branch_ref})
        data["requested_effects"].append({"effect_id": f"commit_{name}", "effect": "local_git_ref_write",
            "target": branch_ref, "requested_by_step": 4,
            "positive_authority_binding": f"commit_{name}_owner", "stage_id": name})
    for name in ("writer_a", "writer_b"):
        target = f"docs/{name}.md"
        data["bindings"].append({**data["bindings"][0], "binding_id": f"owner_compose_{name}",
                                 "authorizes_effect": True, "effect": "tracked_write", "target": target})
        data["requested_effects"].append({"effect_id": f"compose_{name}", "effect": "tracked_write",
            "target": target, "requested_by_step": 4,
            "positive_authority_binding": f"owner_compose_{name}", "stage_id": "exact_union"})
    data["bindings"].append({**data["bindings"][0], "binding_id": "commit_controller_owner",
                             "authorizes_effect": True, "effect": "local_git_ref_write",
                             "target": "refs/heads/controller_candidate"})
    data["requested_effects"].append({"effect_id": "commit_controller", "effect": "local_git_ref_write",
        "target": "refs/heads/controller_candidate", "requested_by_step": 4,
        "positive_authority_binding": "commit_controller_owner", "stage_id": "exact_union"})
    data["stages"][5].update(stage_mode="integration_only", stage_branch_policy="continue_existing_branch",
                             target_branch="master", integration_source_branch="controller_candidate",
                             integration_target_branch="master", integration_method="ff_only",
                             expected_source_head="candidate-oid")
    data["stages"][5]["stage_effect_permissions"] = {"allowed_to_modify": {"TOP26006_fw": ["refs/heads/master"]}}
    data["stages"][6].update(stage_mode="branch_maintenance_only",
                             stage_branch_policy="continue_existing_branch", target_branch="master",
                             branch_maintenance_action="delete_exact_temporary_ref",
                             affected_local_branches=["refs/heads/temp-worker"])
    data["stages"][6]["stage_effect_permissions"] = {"allowed_to_modify": {
        "TOP26006_fw": ["refs/heads/temp-worker"]}, "local_branch_deletion": True}
    for effect_id, effect, target, stage_id in (("integrate", "local_git_ref_write", "refs/heads/master", "integration"),
                                                 ("retire", "delete_local_branch", "refs/heads/temp-worker", "retirement")):
        data["bindings"].append({**data["bindings"][0], "binding_id": f"owner_{effect_id}",
                                 "authorizes_effect": True, "effect": effect, "target": target})
        data["requested_effects"].append({"effect_id": effect_id, "effect": effect,
            "target": target, "requested_by_step": 4, "positive_authority_binding": f"owner_{effect_id}",
            "stage_id": stage_id})
    data["prompt"]["workflow_effect_envelope"] = {"allowed_to_modify": {"TOP26006_fw": [
        "docs/writer_a.md", "docs/writer_b.md", "refs/heads/master", "refs/heads/temp-worker",
        "refs/heads/temporary/writer_a", "refs/heads/temporary/writer_b",
        "refs/heads/controller_candidate"]},
        "local_branch_deletion": True}
    data["prompt"]["allowed_to_modify"] = {"TOP26006_fw": [
        "docs/writer_a.md", "docs/writer_b.md", "refs/heads/master", "refs/heads/temp-worker",
        "refs/heads/temporary/writer_a", "refs/heads/temporary/writer_b",
        "refs/heads/controller_candidate"]}
    data["retirement"] = {"exact_owned_surface": "refs/heads/temp-worker", "authority_binding": "owner_retire",
                          "preservation_evidence": "reviewed patch and exact postimages", "retention_satisfied": True,
                          "terminal_stage": "retirement", "cleanup_failure_invalidates_semantic_result": False,
                          "exact_old_oid": "c" * 40, "expected_preserved_head": "c" * 40,
                          "preservation_ref": "refs/heads/master", "ownership_readback_binding": "owned_temp_ref",
                          "preservation_binding": "portable_preservation"}
    data["bindings"].append({**data["bindings"][0], "binding_id": "owned_temp_ref",
                             "source_kind": "repository_readback",
                             "source_identity": "refs/heads/temp-worker@" + "c" * 40,
                             "observed_state": {"identity_path": "retirement.owned_ref",
                                                "value": {"exact_owned_surface": "refs/heads/temp-worker",
                                                          "exact_old_oid": "c" * 40}}})
    data["bindings"].append({**data["bindings"][0], "binding_id": "portable_preservation",
                             "source_kind": "accepted_evidence",
                             "source_identity": "portable:refs/heads/master@" + "c" * 40,
                             "observed_state": {"identity_path": "retirement.preserved_ref",
                                                "value": {"preservation_ref": "refs/heads/master",
                                                          "expected_preserved_head": "c" * 40}}})
    data["prompt"]["workflow_goal"] = "disjoint writer results with conditional reconciled review"
    data["prompt"]["workflow_stop_policy"] = "stop_on_failed_gate_or_new_decision_boundary"
    data["prompt"]["workflow_stage_ledger_path"] = "diagnostics/ledger.yml"
    data["worker_contract"] = {
        "writers": [{"stage_id": "writer_a", "write_paths": ["docs/writer_a.md"], "isolated_worktree": True,
                     "branch": "temporary/writer_a", "base_oid": "a" * 40,
                     "observed_head": "a" * 40, "worktree_path": "/workspace/worker_a"},
                    {"stage_id": "writer_b", "write_paths": ["docs/writer_b.md"], "isolated_worktree": True,
                     "branch": "temporary/writer_b", "base_oid": "a" * 40,
                     "observed_head": "a" * 40, "worktree_path": "/workspace/worker_b"}],
        "independent_review_stage": "independent_review", "review_independent_of_writers": True,
        "exact_union_stage": "exact_union", "union_paths": ["docs/writer_a.md", "docs/writer_b.md"],
        "conditional_reconciled_review_stage": "reconciled_review", "reconciled_review_if_rewritten": True,
        "worker_permanent_authority": False, "composition_branch": "controller_candidate",
        "composition_base_oid": "a" * 40, "composition_worktree_path": "/workspace/controller_candidate",
        "integration_target_branch": "master",
    }
    for worker in data["worker_contract"]["writers"]:
        for key in ("branch", "base_oid", "observed_head", "worktree_path"):
            bind_state(data, f"worker_contract.writers.{worker['stage_id']}.{key}", worker[key])
        bind_relation(data, f"worker_contract.writers.{worker['stage_id']}.carrier",
                      {"repository": "TOP26006_fw", "worktree": worker["worktree_path"],
                       "attached_branch": worker["branch"], "head": worker["observed_head"],
                       "base_oid": worker["base_oid"]})
    for key in ("composition_branch", "composition_base_oid", "composition_worktree_path",
                "integration_target_branch"):
        bind_state(data, f"worker_contract.{key}", data["worker_contract"][key])
    bind_relation(data, "worker_contract.composition_carrier",
                  {"repository": "TOP26006_fw", "worktree": "/workspace/controller_candidate",
                   "attached_branch": "controller_candidate", "head": "a" * 40,
                   "base_oid": "a" * 40})
    data["prompt"]["validation_ceiling"] = "targeted_unit_test"
    data["common_validation_contract"] = {
        "test_target": "tests/test_exact_union.py::test_common_validation",
        "target": "controller_candidate",
    }
    bind_relation(data, "common_validation.target_relation",
                  {"validation_locator": "tests/test_exact_union.py::test_common_validation",
                   "repository": "TOP26006_fw", "worktree": "/workspace/controller_candidate",
                   "attached_branch": "controller_candidate",
                   "head": "stage:exact_union:observed_commit_head",
                   "covers": ["exact_union", "common_validation"]},
                  source_kind="accepted_evidence")
    return data


def test_q03_parallel_work_is_explicitly_staged_and_isolated():
    data = parallel_data()
    result = run(PARALLEL, data)
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    assert result.receipt["selected_execution_shape"] == "orchestrated_workflow"
    stages = yaml.safe_load(result.prompt.split("```yaml\n", 1)[1].split("\n```", 1)[0])["workflow_stages"]
    assert [s["stage_id"] for s in stages] == ["writer_a", "writer_b", "independent_review",
                                                 "exact_union", "reconciled_review", "common_validation",
                                                 "integration", "retirement"]
    assert stages[2]["stage_effect_permissions"] == stages[4]["stage_effect_permissions"] == {}
    assert stages[3]["stage_effect_permissions"] != {}
    assert stages[0]["stage_effect_permissions"] != stages[1]["stage_effect_permissions"]
    assert set(result.receipt["authorized_effects"]) == {
        "writer_a", "writer_b", "commit_writer_a", "commit_writer_b", "compose_writer_a",
        "compose_writer_b", "commit_controller", "integrate", "retire"}
    assert result.receipt["safety_constraints"]["worker_contract"]["union_paths"] == [
        "docs/writer_a.md", "docs/writer_b.md"]
    assert stages[3]["target_branch"] != stages[6]["target_branch"]
    assert "stage:common_validation:common_validation_evidence" in stages[6]["stage_inputs"]
    composed = run(PARALLEL.replace("writers edit, integrate, and retire branches", "writers edit"),
                   parallel_subset_data(True))
    assert composed.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    composition_stages = prompt_yaml(composed)["workflow_stages"]
    assert [s["stage_id"] for s in composition_stages] == [
        "writer_a", "writer_b", "independent_review", "exact_union", "reconciled_review"]
    assert not any(s["stage_mode"] == "integration_only" for s in composition_stages)


def test_q04_continuation_reuses_accepted_closure():
    data = base_data()
    data["continuation"] = {"prior_artifact_identity": "accepted-009-r1", "accepted_closure_layers": ["writer_b"],
                            "accepted_prior_evidence": ["writer_b:sha256:abc"],
                            "invalidation_boundary": ["writer_a"], "delta_scope": ["writer_a", "join"],
                            "unresolved_checks_only": ["writer_a"], "checks_not_to_repeat": ["writer_b"]}
    data["bindings"].append({**data["bindings"][0], "binding_id": "accepted_009",
                             "source_kind": "accepted_evidence", "source_identity": "accepted-009-r1"})
    result = run(data=data)
    assert result.receipt["selected_execution_shape"] == "continuation"
    assert "checks_not_to_repeat:" in result.prompt and "writer_b" in result.prompt


def q04_data():
    data = parallel_data()
    accepted = {"writer_id": "writer_b", "observed_commit_head": "b" * 40,
                "reviewed_evidence": "reviewed:writer_b", "base_oid": "a" * 40}
    data["continuation"] = {
        "prior_artifact_identity": "accepted-009-r1",
        "accepted_closure_layers": ["writer_b"], "accepted_prior_evidence": [accepted],
        "invalidation_boundary": ["writer_a"],
        "delta_scope": ["writer_a", "independent_review", "exact_union", "reconciled_review",
                        "common_validation", "integration", "retirement"],
        "unresolved_checks_only": ["writer_a", "exact_union", "common_validation"],
        "checks_not_to_repeat": ["writer_b"],
    }
    bind_relation(data, "q04.accepted_writer_result", accepted, source_kind="accepted_evidence")
    data["bindings"][-1]["source_identity"] = "accepted-009-r1"
    data["bindings"].append({**data["bindings"][0], "binding_id": "accepted_009",
                             "source_kind": "accepted_evidence", "source_identity": "accepted-009-r1"})
    return data


def test_q04_positive_delta_preserves_accepted_writer():
    feature = PARALLEL.replace("Then exact union is reviewed",
                               "Then exact union is reviewed and common validation passes")
    result = run(feature, q04_data())
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE", result.receipt.get("diagnostics")
    stages = prompt_yaml(result)["workflow_stages"]
    ids = [item["stage_id"] for item in stages]
    assert "writer_b" not in ids
    assert result.receipt["reused_accepted_effects"] == ["writer_b", "commit_writer_b"]
    assert ids == ["writer_a", "independent_review", "exact_union", "reconciled_review",
                   "common_validation", "integration", "retirement"]
    union = next(item for item in stages if item["stage_id"] == "exact_union")
    assert "prior:accepted-009-r1:writer_b@" + "b" * 40 in union["stage_inputs"]


def test_q05_multi_repository_candidate_tuple_and_local_authority(monkeypatch):
    data = multi_repo_data()
    result = run(MULTI_REPO, data)
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    assert result.receipt["selected_execution_shape"] == "multi_repository_coordination"
    assert set(result.receipt["authorized_effects"]) == {
        "write_topcoffea", "commit_topcoffea", "write_topeft", "commit_topeft"}
    assert result.receipt["safety_constraints"]["candidate_pair_order"] == ["topcoffea", "topeft"]
    assert "global_git_transaction" not in result.prompt
    prompt = prompt_yaml(result)
    assert [stage["stage_id"] for stage in prompt["workflow_stages"]] == [
        "provider_candidate", "consumer_candidate", "independent_review", "pair_validation"]
    assert [stage["target_branch"] for stage in prompt["workflow_stages"][:2]] == [
        "tc/q05_candidate", "te/q05_candidate"]
    assert "refs/heads/tc/dev-live" not in str(prompt["allowed_to_modify"])
    assert "refs/heads/te/datacard_sr_reco" not in str(prompt["allowed_to_modify"])
    assert all(set(roles) == {"permanent_live_development_branch",
                              "permanent_personal_reference_branch",
                              "permanent_integration_branch", "feature_development_namespace"}
               for roles in prompt["repository_branch_roles"].values())

    # Q05 preparation is distinct from Q06 permanent authority advancement.
    feature = MULTI_REPO.replace("write candidates", "write candidates and integrate")
    advanced = run(feature, multi_repo_advancement_data())
    assert advanced.compiler_result == "COMPILED_CONFORMING_CANDIDATE", advanced.receipt.get("diagnostics")
    plan = prompt_yaml(advanced)
    stages = plan["workflow_stages"]
    assert [s["stage_id"] for s in stages] == ["provider_candidate", "consumer_candidate",
        "independent_review", "pair_validation", "integrate_topcoffea", "integrate_topeft"]
    assert advanced.receipt["execution_assertions"] == "NOT_EVALUATED"
    assert advanced.receipt["workflow_visualization"]["consistency"] is True
    assert advanced.receipt["traceability"]["complete"] is True
    for position, repo_id in enumerate(("topcoffea", "topeft")):
        item = stages[4 + position]
        repo = multi_repo_advancement_data()["repositories"][repo_id]
        assert item["repository_id"] == repo_id and item["stage_mode"] == "integration_only"
        assert item["integration_source_branch"] != item["integration_target_branch"]
        assert item["expected_source_head"] == repo["candidate"]
        target_observation = f"stage:{item['stage_id']}:pre_effect_target_oid"
        assert item["expected_target_head"] == target_observation
        guard = item["must_pass_before_effects"]
        assert guard["target_head"] == target_observation
        assert guard["target_ref"] == "refs/heads/" + repo["development_branch"]
        assert guard["fresh_target_readback"] == [
            "git", "rev-parse", "--verify", guard["target_ref"]]
        assert guard["reject_movement_after_readback"] is True
        assert guard["on_mismatch"] == "stop_before_effect_and_preserve_state"
        assert item["runtime_observations"] == [{
            "output": target_observation, "argv": guard["fresh_target_readback"],
            "before_effect": True, "require_exit_zero": True, "require_full_oid": True}]
        assert "pre_effect_target_oid" in item["stage_outputs"]
        assert item["must_pass_before_effects"]["candidate_tuple"] == plan["candidate_pair"]
        assert item["must_pass_before_effects"]["require_fast_forward_ancestry"] is True
        assert "stage:pair_validation:candidate_pair_evidence" in item["stage_inputs"]
        assert "stage:independent_review:review_evidence" in item["stage_inputs"]
        scope = item["stage_effect_permissions"]["allowed_to_modify"]
        assert set(scope) == {repo_id}
        assert scope[repo_id]["local_refs"] == ["refs/heads/" + repo["development_branch"]]
        assert scope[repo_id]["git_effects"] == ["integrate_exact_source"]
        assert "no automatic rollback or retry" in item["stage_failure_behavior"]
        assert set(item["failure_outcomes"]) == {"failed_before_effect", "observed_effect", "OUTCOME_UNKNOWN"}
    assert "stage:integrate_topcoffea:observed_target_head" in stages[-1]["stage_inputs"]
    graph_edges = advanced.receipt["workflow_visualization"]["generated_graph"]["connectors"]
    assert {"source": "derived_pair_validation", "target": "derived_integrate_topcoffea"} in graph_edges
    assert {"source": "derived_integrate_topcoffea", "target": "derived_integrate_topeft"} in graph_edges
    assert {"source": "derived_integrate_topeft", "target": "derived_stop"} in graph_edges

    # An inventory cannot insert advancement into preparation-only semantics.
    injected = run(MULTI_REPO, multi_repo_advancement_data())
    assert not injected.prompt and injected.receipt["authorized_effects"] == []
    for mutation in ("missing_authority", "wrong_repo", "missing_effect", "wrong_tuple",
                     "missing_target_relation", "aliased_target", "pooled_envelope"):
        invalid = multi_repo_advancement_data()
        if mutation == "missing_authority":
            invalid["bindings"] = [b for b in invalid["bindings"] if b["binding_id"] != "advance_topeft"]
        elif mutation == "wrong_repo":
            next(b for b in invalid["bindings"] if b["binding_id"] == "advance_topeft")["validity_scope"] = "topcoffea"
        elif mutation == "missing_effect":
            invalid["requested_effects"] = [e for e in invalid["requested_effects"] if e["effect_id"] != "advance_topeft"]
        elif mutation == "wrong_tuple":
            _binding(invalid, "pair_validation.candidate_tuple")["observed_state"]["value"]["consumer_head"] = "d" * 40
        elif mutation == "missing_target_relation":
            invalid["bindings"].remove(_binding(invalid, "repositories.topeft.permanent_target"))
        elif mutation == "aliased_target":
            invalid["repositories"]["topeft"]["permanent_target_branch"] = "te/q05_candidate"
        else:
            invalid["prompt"]["workflow_effect_envelope"] = deepcopy(invalid["prompt"]["workflow_effect_envelope"])
            invalid["prompt"]["workflow_effect_envelope"]["allowed_to_modify"]["topeft"].remove("refs/heads/te/datacard_sr_reco")
        failure = run(feature, invalid)
        assert failure.compiler_result in {"NOT_READY_MISSING_AUTHORITY_BINDING",
                                           "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE",
                                           "COMPILER_INVARIANT_FAILURE"}, (mutation, failure.receipt)
        assert not failure.prompt and failure.receipt["authorized_effects"] == []

    original = compiler._plan_stages
    for mutation in ("order", "validation_dependency", "candidate_tuple"):
        def damaged(*args):
            stages = original(*args)
            if mutation == "order":
                stages[3], stages[4] = stages[4], stages[3]
            elif mutation == "validation_dependency":
                stages[-1]["stage_inputs"].remove("stage:pair_validation:candidate_pair_evidence")
            else:
                stages[-1]["must_pass_before_effects"]["candidate_tuple"]["topeft"] = "d" * 40
            return stages
        with monkeypatch.context() as scoped:
            scoped.setattr(compiler, "_plan_stages", damaged)
            failure = run(feature, multi_repo_advancement_data())
        assert failure.compiler_result == "COMPILER_INVARIANT_FAILURE", (mutation, failure.receipt)
        assert not failure.prompt


def test_q06_partial_integration_preserves_real_effect():
    data = multi_repo_data()
    data["multi_repository_state"] = "PARTIAL"
    data["bindings"].append({**data["bindings"][0], "binding_id": "partial_readback",
                             "source_kind": "repository_readback", "source_identity": "topcoffea@a1/topeft@b1"})
    data["partial_state_binding"] = "partial_readback"
    data["partial_effects"] = {"integrated_repo_identity": "topcoffea@a1",
                               "preserved_candidate_identity": "topeft@b1",
                               "unresolved_recovery": "owner decision pending"}
    result = run(MULTI_REPO, data)
    assert result.compiler_result == 'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE' and result.prompt == ""
    assert result.receipt["selected_execution_shape"] == "multi_repository_coordination"
    assert result.receipt["partial_state"]["observed_effects"]["integrated_repo_identity"] == "topcoffea@a1"
    assert "rollback" not in result.receipt["diagnostics"][0]["message"].lower()


def test_q07_outcome_unknown_requires_readback():
    data = base_data()
    data["bindings"].append({**data["bindings"][0], "binding_id": "readback_owner",
                             "claim": "bounded readback"})
    data.update(outcome_unknown=True, readback_before_retry=True, automatic_retry=False,
                readback_authority_binding="readback_owner")
    assert run(data=data).compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    data["automatic_retry"] = True
    assert run(data=data).compiler_result == "COMPILER_INVARIANT_FAILURE"


def test_q08_terminal_retirement_needs_all_gates():
    data = parallel_data()
    assert run(PARALLEL, data).compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    data["retirement"]["preservation_evidence"] = ""
    assert run(PARALLEL, data).compiler_result == "COMPILER_INVARIANT_FAILURE"


def test_q09_envelope_is_not_stage_grant():
    data = parallel_data()
    data["bindings"] = [binding for binding in data["bindings"] if binding["binding_id"] != "owner_writer_a"]
    result = run(PARALLEL, data)
    assert result.compiler_result == "NOT_READY_MISSING_AUTHORITY_BINDING"
    assert result.prompt == ""


def test_q10_gherkin_authority_without_binding_fails_closed():
    feature = "Feature: publication\nScenario: publish\nGiven remote publication is authorized\nWhen I publish a branch\nThen the branch appears"
    result = run(feature)
    assert result.compiler_result == "NOT_READY_MISSING_AUTHORITY_BINDING"
    assert result.prompt == "" and result.receipt["dispatchability"]["dispatchable"] is False
    assert result.receipt["diagnostics"][0]["line"] == 6


def test_q11_wrong_repository_branch_authority_is_rejected():
    data = base_data()
    data["repositories"] = {"topeft": {"development_branch": "master"}}
    result = run(data=data)
    assert result.compiler_result == "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE"
    assert "topeft" in result.receipt["diagnostics"][0]["message"]


def test_q12_foreign_dirty_work_preserved_or_stopped():
    data = base_data()
    data["foreign_dirty"] = True
    data["prompt"]["foreign_dirty_change_policy"] = "preserve_and_exclude"
    assert run(data=data).compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    data["adopt_foreign_work"] = True
    assert run(data=data).compiler_result == "COMPILER_INVARIANT_FAILURE"


def test_q13_production_tag_routes_but_never_grants():
    feature = "Feature: campaign\n@production\nScenario: run\nGiven inputs are known\nWhen I run production\nThen the report cites evidence"
    result = run(feature)
    assert result.compiler_result == "NOT_READY_MISSING_AUTHORITY_BINDING"
    assert result.prompt == ""


def test_q14_compile_without_dispatch_is_not_evaluated():
    data = base_data()
    data["bindings"].append({**data["bindings"][0], "binding_id": "manual_review",
                             "source_kind": "accepted_evidence", "source_identity": "review:fixture"})
    data["bindings"].append({**data["bindings"][0], "binding_id": "live_readback",
                             "source_kind": "repository_readback", "source_identity": "readback:fixture"})
    data["dispatch_gate"] = {"owner_authorization_binding": "owner_task",
                             "manual_governance_review_binding": "manual_review",
                             "live_applicability_binding": "live_readback"}
    result = run(data=data)
    assert result.receipt["dispatchability"]["conformant"] is True
    assert result.receipt["dispatchability"]["owner_authorized"] is True
    assert result.receipt["dispatchability"]["dispatchable"] is True
    assert result.receipt["execution_assertions"] == "NOT_EVALUATED"
    assert result.receipt["result_assertions"] == "NOT_EVALUATED"


def test_q15_runtime_model_unobservable_is_recorded_without_blocking():
    data = base_data()
    data["runtime_model_observation"] = "not_observable"
    data["runtime_model_materiality"] = "not_decision_material"
    result = run(data=data)
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    assert "gpt-6-sol" in result.prompt
    assert result.receipt["safety_constraints"]["runtime_model_observation"] == "not_observable"
    assert result.receipt["execution_assertions"] == "NOT_EVALUATED"


def test_q16_small_edit_does_not_force_orchestration():
    result = run()
    assert result.receipt["selected_execution_shape"] == "simple_non_orchestrated"
    assert "workflow_stages" not in result.prompt


def test_q17_contradictory_gherkin_has_no_prompt():
    feature = "Feature: ref\nScenario: contradiction\nGiven reference branch master remains unchanged\nWhen I move reference branch master\nThen the report cites evidence"
    result = run(feature)
    assert result.compiler_result == "NOT_READY_NEW_DECISION_BOUNDARY"
    assert result.prompt == ""


def test_q18_invented_branch_policy_is_unsupported():
    data = base_data()
    data["prompt"]["branch_policy"] = "historical_parallel_worktree_policy"
    result = run(data=data)
    assert result.compiler_result == "UNSUPPORTED_CANONICAL_CONSTRUCT"
    assert result.prompt == ""


def test_q19_scientific_choice_preserves_preparation():
    feature = "Feature: mapping\nScenario: choose\nGiven inputs are acquired\nWhen I choose a mapping\nThen result is reported"
    result = run(feature)
    assert result.compiler_result == "NOT_READY_NEW_DECISION_BOUNDARY"
    assert result.receipt["manual_fallback"] == "independently_evaluable_under_canonical_governance"


def test_q20_unsupported_compiler_construct_does_not_revoke_manual_work():
    feature = "Feature: manual valid task\nScenario Outline: examples\nGiven a value\nThen success"
    result = run(feature)
    assert result.compiler_result == 'IMPLEMENTATION_GAP'
    assert result.receipt["manual_fallback"] == "independently_evaluable_under_canonical_governance"
    assert result.receipt["dispatchability"]["dispatchable"] is False
    assert result.receipt["unsupported_construct"]["affected_behavior_steps"]
    for header in ("Background: shared premises", "Scenario Outline: bounded examples"):
        result = run("Feature: standard input\n" + header + "\nGiven known inputs\nWhen I inspect the document\nThen the report cites evidence")
        assert result.compiler_result == "IMPLEMENTATION_GAP"
        assert result.receipt["unsupported_construct"]["current_architecture_boundary"]["classification"] == "implementation_gap"

    # A known shape with no evaluable oracle is an evidence problem. A truly
    # undefined action has no authoritative architectural execution contract.
    missing = run(SIMPLE.replace("the report cites evidence", "the undefined oracle succeeds"))
    assert missing.compiler_result == "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE"
    assert "unsupported_construct" not in missing.receipt
    unknown = run(SIMPLE.replace("I inspect the document", "I invoke an undefined operation"))
    assert unknown.compiler_result == "ARCHITECTURE_BOUNDARY_UNRESOLVED"
    assert unknown.receipt["unsupported_construct"]["current_architecture_boundary"]["classification"] == "unresolved"
    malformed = run("Feature: misplaced\nWhen I inspect the document")
    assert malformed.compiler_result == "COMPILER_INVARIANT_FAILURE"
    inventory = base_data()
    inventory["requested_effects"] = [{"effect_id": "unknown", "effect": "invented_effect",
        "target": "document", "requested_by_step": 5, "positive_authority_binding": "owner_task"}]
    invalid_inventory = run(SIMPLE, inventory)
    assert invalid_inventory.compiler_result == "COMPILER_INVARIANT_FAILURE"
    supported = run()
    assert supported.receipt["execution_shape_classification"] == "SUPPORTED_EXECUTION_SHAPE"
    data = base_data()
    data["prompt"]["branch_policy"] = "invented_branch_policy"
    unsupported = run(data=data)
    assert unsupported.compiler_result == "UNSUPPORTED_CANONICAL_CONSTRUCT"
    assert unsupported.receipt["unsupported_construct"]["current_architecture_boundary"]["classification"] == "normative"
    for stopped in (missing, unknown, malformed, invalid_inventory, unsupported):
        assert stopped.prompt == "" and stopped.receipt["authorized_effects"] == []
        assert stopped.receipt["manual_fallback"] == "independently_evaluable_under_canonical_governance"


def test_n1_syntax_tag_cannot_create_authority():
    result = run("Feature: publish\n@production\nScenario: now\nGiven publication is authorized\nWhen I publish\nThen the report cites evidence")
    assert result.prompt == "" and result.compiler_result == "NOT_READY_MISSING_AUTHORITY_BINDING"


def test_n2_envelope_cannot_become_stage_permission():
    data = base_data()
    orchestrated(data)
    data["prompt"]["workflow_effect_envelope"] = {"network_access": True}
    result = run(data=data)
    assert result.receipt.get("authorized_effects", []) == []
    assert all(not stage["stage_effect_permissions"] for stage in data["stages"])


def test_n3_repo_authority_cannot_cross_to_another_repo():
    data = base_data()
    data["repositories"] = {"topeft": {"authority_binding": "owner_task"}}
    result = run(data=data)
    assert result.compiler_result == "NOT_READY_MISSING_AUTHORITY_BINDING"


def test_n4_foreign_work_cannot_be_cleaned_or_adopted():
    data = base_data()
    data.update(foreign_dirty=True, adopt_foreign_work=True)
    result = run(data=data)
    assert result.prompt == "" and result.compiler_result == "COMPILER_INVARIANT_FAILURE"


def test_n5_ambiguous_effect_cannot_blind_retry():
    data = base_data()
    data.update(outcome_unknown=True, readback_before_retry=False, automatic_retry=True)
    assert run(data=data).prompt == ""


def test_n6_multi_repo_cannot_rollback_automatically():
    data = base_data()
    data.update(multi_repository_state="PARTIAL", automatic_rollback=True)
    assert run(data=data).prompt == ""


def test_n7_cleanup_cannot_precede_preservation():
    data = base_data()
    data["retirement"] = {"exact_owned_surface": "temp", "authority_binding": "owner_task",
                          "preservation_evidence": "", "retention_satisfied": True, "terminal_stage": "last"}
    assert run(data=data).prompt == ""


def test_n8_scientific_decision_cannot_be_chosen_by_compiler():
    feature = "Feature: science\nScenario: choice\nGiven two mappings exist\nWhen I choose a mapping\nThen the report cites evidence"
    assert run(feature).compiler_result == "NOT_READY_NEW_DECISION_BOUNDARY"
    data = base_data()
    data["scientific_selection_binding"] = "missing_scientific_owner"
    assert run(feature, data).compiler_result == "NOT_READY_NEW_DECISION_BOUNDARY"


def test_n9_receipt_cannot_claim_execution_or_acceptance():
    result = run()
    assert "executed" not in result.receipt["dispatchability"]
    assert "accepted" not in result.receipt["dispatchability"]
    assert result.receipt["execution_assertions"] == "NOT_EVALUATED"


def test_n10_closed_vocabulary_is_checked_against_live_governance():
    data = base_data()
    data["prompt"]["prompt_mode"] = "d8_super_mode"
    assert run(data=data).compiler_result == "UNSUPPORTED_CANONICAL_CONSTRUCT"


def test_h1_h5_readiness_is_declared_but_unevaluated():
    result = run()
    assert set(result.receipt["historical_case_readiness"]) == set(HISTORICAL_CASES)
    assert all(item["state"] == "NOT_EVALUATED" for item in result.receipt["historical_case_readiness"].values())
    assert set(result.receipt["historical_case_readiness"]) == {"H1", "H2", "H3", "H4", "H5"}


def test_f_b01_inert_caller_stages_cannot_force_orchestration():
    data = base_data()
    orchestrated(data)
    data["stages"] = [stage("unneeded_a"), stage("unneeded_b")]
    result = run(SIMPLE, data)
    assert result.receipt["selected_execution_shape"] == "simple_non_orchestrated"
    assert result.compiler_result == "COMPILER_INVARIANT_FAILURE"
    assert "compiler-selected" in result.receipt["diagnostics"][0]["message"]
    assert result.prompt == ""
    direct = base_data()
    direct["prompt"]["workflow_stages"] = [stage("injected")]
    injected = run(SIMPLE, direct)
    assert injected.receipt["selected_execution_shape"] == "simple_non_orchestrated"
    assert injected.prompt == "" and injected.compiler_result == "COMPILER_INVARIANT_FAILURE"
    forced_mode = base_data()
    forced_mode["prompt"]["prompt_mode"] = "coding"
    forced_mode["prompt"]["branch_policy"] = "continue_existing_branch"
    forced_mode["prompt"]["target_branch"] = "governance/workflow-compiler"
    forced = run(SIMPLE, forced_mode)
    assert forced.compiler_result == "COMPILER_INVARIANT_FAILURE" and forced.prompt == ""


@pytest.mark.parametrize("field,value", [
    ("dirty_worktree_policy", "invented_dirty_policy"),
    ("preflight_profile", "invented_preflight"),
    ("patch_kind_expected", "invented_patch_kind"),
    ("foreign_dirty_change_policy", "invented_foreign_policy"),
    ("staging_policy", "invented_stage_policy"),
    ("publication_action", "invented_publication_action"),
    ("duplicate_pr_or_mr_policy", "invented_duplicate_policy"),
    ("execution_owner", "invented_execution_owner"),
])
def test_f_b02_simple_closed_fields_reject_invented_value(field, value):
    data = base_data()
    data["prompt"][field] = value
    result = run(data=data)
    assert result.compiler_result == "UNSUPPORTED_CANONICAL_CONSTRUCT"
    assert result.prompt == ""


def test_f_b02_live_dirty_alternative_and_typed_repository_scope():
    data = base_data()
    data["prompt"]["dirty_worktree_policy"] = "work_on_dirty_branch_as_is"
    assert run(data=data).compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    data["prompt"]["repo_locations"]["invented_repository"] = "/workspace/invented"
    result = run(data=data)
    assert result.prompt == ""
    assert result.compiler_result == "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE"


def test_f_b02_source_extraction_retains_current_valid_values():
    contents, _ = compiler._canonical_sources()
    assert "work_on_dirty_branch_as_is" in compiler._closed_values("dirty_worktree_policy", contents)
    assert "stop_on_failed_gate_or_new_decision_boundary" in compiler._closed_values(
        "workflow_stop_policy", contents)
    assert "ff_only" in compiler._closed_values("integration_method", contents)
    assert "create_or_reuse_open_pr_or_mr" in compiler._closed_values("publication_action", contents)


@pytest.mark.parametrize("location,field,value", [
    ("prompt", "workflow_stop_policy", "invented_stop_policy"),
    ("stage", "integration_method", "invented_integration_method"),
])
def test_f_b02_orchestrated_closed_fields_reject_invented_value(location, field, value):
    data = parallel_data()
    if location == "prompt":
        data["prompt"][field] = value
    else:
        next(s for s in data["stages"] if s["stage_id"] == "integration")[field] = value
    result = run(PARALLEL, data)
    assert result.compiler_result == "UNSUPPORTED_CANONICAL_CONSTRUCT"
    assert result.prompt == ""


def test_f_b03_stage_trace_is_earned_and_missing_edge_fails_closed(monkeypatch):
    result = run(PARALLEL, parallel_data())
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    assert result.receipt["traceability"]["complete"] is True
    edges = result.receipt["traceability"]["edges"]
    assert {f"stage:{s['stage_id']}" for s in parallel_data()["stages"]} <= {
        edge["source"] for edge in edges if edge["relation"] == "serialized_as"}
    original = compiler._stage_trace

    def missing_one_edge(*args):
        return [edge for edge in original(*args)
                if not (edge.source == "stage:integration" and edge.relation == "serialized_as")]

    monkeypatch.setattr(compiler, "_stage_trace", missing_one_edge)
    broken = run(PARALLEL, parallel_data())
    assert broken.receipt["traceability"]["complete"] is False
    assert broken.compiler_result == "COMPILER_INVARIANT_FAILURE" and broken.prompt == ""


def test_f_m01_but_inherits_given_role():
    feature = ("Feature: Example\nScenario: Inspect\nGiven condition A\n"
               "But condition B is not true\nWhen I inspect the state\nThen result C is reported")
    intent = compiler.parse_gherkin(feature, "inline")
    assert intent.steps[1].keyword == "Given"
    assert intent.negative_assertions == ()
    result = run(feature)
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    assert "condition B is not true" not in result.prompt.split("## Post-execution evidence assertions", 1)[1]


def test_f_m02_feature_and_scenario_tags_are_retained_without_authority():
    feature = ("@production\nFeature: Example\n@inspection\nScenario: Inspect only\n"
               "Given state X\nWhen I inspect state X\nThen result Y is reported")
    result = run(feature)
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    assert result.receipt["selected_execution_shape"] == "simple_non_orchestrated"
    assert result.receipt["source_contract"]["feature_tags"] == ["@production"]
    assert result.receipt["source_contract"]["scenario_tags"] == [["@inspection"]]
    assert "@production\nFeature:" in result.prompt
    assert result.receipt["authorized_effects"] == []
    two = ("@feature\nFeature: Example\n@first\nScenario: First\n"
           "Given state A\nWhen I inspect A\nThen A is reported\n"
           "@second\nScenario: Second\nGiven state B\nWhen I inspect B\nThen B is reported")
    scoped = run(two)
    assert scoped.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    first_block = scoped.prompt.split("@first\nScenario: First", 1)[1].split("@second", 1)[0]
    second_block = scoped.prompt.split("@second\nScenario: Second", 1)[1].split("## Bound CPC", 1)[0]
    assert "inspect A" in first_block and "inspect B" not in first_block
    assert "inspect B" in second_block and "inspect A" not in second_block


def test_f_m03_canonical_sources_cover_encoded_evidence_and_recovery_rules(monkeypatch):
    sources = compiler.GOVERNANCE
    for owner in ("governance/contracts/review_and_evidence.md",
                  "governance/contracts/autonomy_and_blocker_classification.md"):
        assert owner in sources
        assert owner in run().receipt["canonical_governance"]["applicable_sources"]
    monkeypatch.setattr(compiler, "GOVERNANCE", {key: value for key, value in sources.items()
                         if key != "governance/contracts/autonomy_and_blocker_classification.md"})
    omitted = run()
    assert omitted.compiler_result == "COMPILER_DEFECT"
    assert omitted.prompt == ""


def prompt_yaml(result):
    return yaml.safe_load(result.prompt.split("```yaml\n", 1)[1].split("\n```", 1)[0])


def test_e2_poisoned_stage_bodies_and_order_cannot_become_plan():
    clean = run(PARALLEL, parallel_data())
    data = parallel_data()
    data["stages"].reverse()
    for item in data["stages"]:
        item.update(stage_goal="delete unrelated database", stage_mode="pr_publication",
                    stage_inputs=["do nothing unrelated to union"],
                    stage_acceptance_gate="publish unrelated branch", stage_outputs=["unrelated result"],
                    stage_failure_behavior="blind retry")
        item["stage_effect_permissions"] = {"remote_git_write": "yes"}
    poisoned = run(PARALLEL, data)
    assert poisoned.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    assert prompt_yaml(poisoned)["workflow_stages"] == prompt_yaml(clean)["workflow_stages"]
    assert "delete unrelated database" not in poisoned.prompt
    assert "blind retry" not in poisoned.prompt


def test_e2_unrecognized_semantic_action_is_unsupported():
    feature = "Feature: policy\nScenario: unknown\nGiven a scope\nWhen I arbitrate database ownership\nThen the report cites evidence"
    result = run(feature)
    assert result.compiler_result == 'ARCHITECTURE_BOUNDARY_UNRESOLVED' and result.prompt == ""


def test_e2_missing_stage_generation_provenance_fails(monkeypatch):
    original = compiler._plan_stages

    def damaged(*args):
        stages = original(*args)
        stages[0].pop("generation_provenance")
        return stages

    monkeypatch.setattr(compiler, "_plan_stages", damaged)
    result = run(PARALLEL, parallel_data())
    assert result.compiler_result == "COMPILER_INVARIANT_FAILURE" and result.prompt == ""


def test_e2_missing_then_evidence_or_evaluation_edge_fails(monkeypatch):
    original = compiler._verify

    def damaged(*args):
        edges, authorized, excluded = original(*args)
        return ([edge for edge in edges if edge.relation != "supports_assertion"], authorized, excluded)

    monkeypatch.setattr(compiler, "_verify", damaged)
    result = run(PARALLEL, parallel_data())
    assert result.receipt["traceability"]["complete"] is False
    assert result.compiler_result == "COMPILER_INVARIANT_FAILURE"


def test_e2_untraced_grant_or_ref_fails(monkeypatch):
    original = compiler._plan_stages

    def damaged(*args):
        stages = original(*args)
        stages[2]["stage_effect_permissions"]["storage_writes"] = "yes"
        return stages

    monkeypatch.setattr(compiler, "_plan_stages", damaged)
    result = run(PARALLEL, parallel_data())
    assert result.compiler_result == "COMPILER_INVARIANT_FAILURE" and result.prompt == ""


def test_e2_simple_and_orchestrated_traceability_is_bidirectional():
    for result in (run(), run(PARALLEL, parallel_data()), run(MULTI_REPO, multi_repo_data())):
        assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
        assert result.receipt["traceability"]["complete"] is True
        edges = result.receipt["traceability"]["edges"]
        assert any(edge["relation"] == "supports_assertion" for edge in edges)
        if "workflow_stages" in prompt_yaml(result):
            assert any(edge["relation"] == "governed_by" for edge in edges)
            assert any(edge["relation"] == "generated_from" for edge in edges)


def test_e2_registry_selected_modules_and_repo_local_roles():
    result = run(MULTI_REPO, multi_repo_data())
    prompt = prompt_yaml(result)
    assert result.receipt["rule_routing"]["native_policy:topeft"] == "governance/modules/topeft.md"
    assert result.receipt["rule_routing"]["native_policy:topcoffea"] == "governance/modules/topcoffea.md"
    assert prompt["repository_branch_roles"]["topeft"] == {
        "permanent_live_development_branch": "te/datacard_sr_reco",
        "permanent_personal_reference_branch": "run3_test_mmerged_anpicci",
        "permanent_integration_branch": "run3_test_mmerged",
        "feature_development_namespace": "te/*"}
    assert prompt["repository_branch_roles"]["topcoffea"]["permanent_live_development_branch"] == "tc/dev-live"
    assert prompt["repository_branch_roles"]["topcoffea"]["feature_development_namespace"] == "tc/*"
    assert "repository-native" in prompt["repository_modules"]["topeft"]["native_policy"]
    assert "global_git_transaction" not in result.prompt


@pytest.mark.parametrize("repo_id,branch", [
    ("topeft", "master"), ("topeft", "feature/topeft"), ("topeft", "invented/topeft"),
    ("topcoffea", "te/datacard_sr_reco")])
def test_e2_wrong_native_development_branch_fails(repo_id, branch):
    data = multi_repo_data()
    data["repositories"][repo_id]["development_branch"] = branch
    result = run(MULTI_REPO, data)
    assert result.prompt == "" and result.compiler_result == "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE"


def test_e2_namespace_is_not_branch_creation_authority():
    data = multi_repo_data()
    data["repositories"]["topeft"]["feature_branch"] = "te/another_feature"
    result = run(MULTI_REPO, data)
    assert result.prompt == "" and result.compiler_result == "NOT_READY_MISSING_AUTHORITY_BINDING"


def test_e2_missing_registry_module_fails_closed(monkeypatch):
    original = compiler._canonical_repository

    def missing(repo_id, contents):
        return "governance/modules/missing.md" if repo_id == "topeft" else original(repo_id, contents)

    monkeypatch.setattr(compiler, "_canonical_repository", missing)
    result = run(MULTI_REPO, multi_repo_data())
    assert result.prompt == "" and result.compiler_result == 'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE'


def test_e2_unparseable_registry_module_fails_closed(monkeypatch, tmp_path):
    module = tmp_path / "governance/modules/topeft.md"
    module.parent.mkdir(parents=True)
    module.write_text("native policy is required\npermanent_live_development_branch: te/dev\n")
    original = compiler.Policy_source_binding.read
    def read(binding, path):
        return module.read_bytes() if path == 'governance/modules/topeft.md' else original(binding, path)
    monkeypatch.setattr(compiler.Policy_source_binding, 'read', read)
    data = base_data()
    data["repositories"] = {"topeft": {}}
    data["prompt"]["repo_locations"] = {"topeft": "/workspace/topeft"}
    result = run(data=data)
    assert result.prompt == "" and result.compiler_result == 'IMPLEMENTATION_GAP'


def test_e2_q03_git_review_and_retirement_contracts():
    result = run(PARALLEL, parallel_data())
    prompt = prompt_yaml(result)
    stages = {item["stage_id"]: item for item in prompt["workflow_stages"]}
    assert prompt["delegation_policy"] == "required"
    assert prompt["patch_kind_expected"] == "prompt_local"
    for stage_id in ("writer_a", "writer_b", "exact_union"):
        item = stages[stage_id]
        assert item["authorized_commit_scope"]
        assert item["explicitly_adopted_inherited_changes"] == "none"
        assert item["foreign_dirty_change_policy"] == "preserve_and_exclude"
        assert item["staging_policy"] == "exact_path_only"
        assert item["stage_effect_permissions"]["allowed_to_modify"]
        assert "observed_commit_head" in item["stage_outputs"]
    integration = stages["integration"]
    assert integration["integration_source_branch"] == stages["exact_union"]["target_branch"]
    assert integration["expected_source_head"] == "stage:exact_union:observed_commit_head"
    assert integration["target_branch"] == integration["integration_target_branch"]
    assert integration["integration_method"] == "ff_only"
    retirement = stages["retirement"]
    assert prompt["workflow_stages"][-1]["stage_id"] == "retirement"
    for field_name in ("affected_local_branches", "expected_preserved_head", "preservation_ref",
                       "reference_restore_source", "non_fast_forward_ref_move_authorized",
                       "local_branch_deletion", "remote_branch_deletion", "expected_old_oid",
                       "safety_critical_ref_command"):
        assert field_name in retirement
    assert stages["independent_review"]["stage_effect_permissions"] == {}
    assert stages["reconciled_review"]["stage_effect_permissions"] == {}


def test_e2_independent_review_cannot_be_forbidden():
    data = parallel_data()
    data["prompt"]["delegation_policy"] = "forbidden"
    result = run(PARALLEL, data)
    assert result.prompt == "" and result.compiler_result == "COMPILER_INVARIANT_FAILURE"


def test_e2_commit_requires_owner_bound_local_ref():
    feature, data = documentation_data()
    data["bindings"] = [item for item in data["bindings"] if item["binding_id"] != "commit_owner"]
    result = run(feature, data)
    assert result.prompt == "" and result.compiler_result == "NOT_READY_MISSING_AUTHORITY_BINDING"


def test_e2_q05_candidate_pair_binds_prior_observations_without_pooled_authority():
    result = run(MULTI_REPO, multi_repo_data())
    prompt = prompt_yaml(result)
    assert prompt["candidate_pair"] == {
        "topcoffea": "stage:provider_candidate:observed_commit_head",
        "topeft": "stage:consumer_candidate:observed_commit_head"}
    stages = {item["stage_id"]: item for item in prompt["workflow_stages"]}
    assert set(stages["provider_candidate"]["stage_effect_permissions"]["allowed_to_modify"]) == {"topcoffea"}
    assert set(stages["consumer_candidate"]["stage_effect_permissions"]["allowed_to_modify"]) == {"topeft"}
    assert stages["pair_validation"]["stage_inputs"][:2] == [
        "stage:provider_candidate:observed_commit_head",
        "stage:consumer_candidate:observed_commit_head"]
    assert all("integrate" not in stage_id for stage_id in stages)


def test_e2_q05_cross_repo_binding_cannot_authorize_other_repo():
    data = multi_repo_data()
    next(item for item in data["bindings"] if item["binding_id"] == "commit_topeft_owner")[
        "validity_scope"] = "topcoffea"
    result = run(MULTI_REPO, data)
    assert result.prompt == "" and result.compiler_result == "NOT_READY_MISSING_AUTHORITY_BINDING"


def test_e2_stage_grants_cannot_pool_from_envelope():
    data = parallel_data()
    data["prompt"]["workflow_effect_envelope"]["allowed_to_modify"]["TOP26006_fw"].remove(
        "refs/heads/controller_candidate")
    result = run(PARALLEL, data)
    assert result.prompt == "" and result.compiler_result == "COMPILER_INVARIANT_FAILURE"


def test_e2_patch_kind_matches_whole_plan():
    assert prompt_yaml(run())["patch_kind_expected"] == "empty_no_changes"
    feature, data = documentation_data()
    assert prompt_yaml(run(feature, data))["patch_kind_expected"] == "prompt_local"
    assert prompt_yaml(run(PARALLEL, parallel_data()))["patch_kind_expected"] == "prompt_local"
    data = parallel_data()
    data["prompt"]["patch_kind_expected"] = "empty_no_changes"
    assert run(PARALLEL, data).compiler_result == "COMPILER_INVARIANT_FAILURE"
    data = base_data()
    data["prompt"]["patch_kind_expected"] = "cumulative"
    assert run(data=data).compiler_result == "COMPILER_INVARIANT_FAILURE"


def test_e3_unrequested_integration_effect_cannot_create_stage():
    feature = ("Feature: parallel writers\nScenario: disjoint\nGiven isolated worktrees\n"
               "When writers edit and retire branches\nThen exact union is reviewed")
    result = run(feature, parallel_data())
    assert result.compiler_result == "NOT_READY_NEW_DECISION_BOUNDARY"
    assert result.prompt == ""
    assert result.receipt["dispatchability"]["dispatchable"] is False
    assert "no composition dependency" in result.receipt["diagnostics"][0]["message"]
    assert result.receipt["authorized_effects"] == []


def test_e3_commit_is_governance_mechanic_without_commit_word():
    feature, data = documentation_data()
    result = run(feature, data)
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    assert "commit_ref" in result.receipt["authorized_effects"]
    assert "commit" not in feature.lower()


def test_e3_exact_union_assertion_has_concrete_gate():
    result = run(PARALLEL, parallel_data())
    edges = result.receipt["traceability"]["edges"]
    stages = prompt_yaml(result)["workflow_stages"]
    assert all(stage["generation_provenance"]["provenance_class"] in
               {"requested_behavior", "necessary_governance_mechanic"} for stage in stages)
    assert next(stage for stage in stages if stage["stage_id"] == "integration")[
        "generation_provenance"]["provenance_class"] == "requested_behavior"
    assert {"source": "assertion:8:1", "output": "gate:exact_union",
            "relation": "requires_concrete_gate"} in edges


def test_e3_common_validation_requires_supplied_exact_contract():
    feature = PARALLEL.replace("Then exact union is reviewed",
                               "Then exact union is reviewed and common validation passes")
    missing_data = parallel_data()
    del missing_data["common_validation_contract"]
    missing = run(feature, missing_data)
    assert missing.compiler_result == 'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE' and missing.prompt == ""
    data = parallel_data()
    result = run(feature, data)
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    stages = prompt_yaml(result)["workflow_stages"]
    ids = [stage["stage_id"] for stage in stages]
    assert ids.index("exact_union") < ids.index("common_validation") < ids.index("integration")
    assert stages[ids.index("integration")]["stage_inputs"][-1] == \
        "stage:common_validation:common_validation_evidence"
    assert stages[ids.index("common_validation")]["validation_test_target"] == \
        data["common_validation_contract"]["test_target"]
    assert stages[ids.index("common_validation")]["stage_acceptance_gate"].startswith("must_pass:")
    assert {"source": "assertion:8:2", "output": "gate:common_validation",
            "relation": "requires_concrete_gate"} in result.receipt["traceability"]["edges"]


def test_e3_unknown_material_assertion_fails_closed():
    feature = PARALLEL.replace("Then exact union is reviewed",
                               "Then exact union is reviewed and unknown condition holds")
    result = run(feature, parallel_data())
    assert result.compiler_result == 'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE'
    assert result.prompt == "" and result.receipt["traceability"]["complete"] is False


def test_e3_common_validation_cannot_add_arbitrary_command():
    feature = PARALLEL.replace("Then exact union is reviewed",
                               "Then exact union is reviewed and common validation passes")
    data = parallel_data()
    data["prompt"]["validation_ceiling"] = "targeted_unit_test"
    data["common_validation_contract"] = {"command": "arbitrary shell action",
                                          "target": "controller_candidate",
                                          "acceptance_gate": "claimed pass"}
    result = run(feature, data)
    assert result.compiler_result == 'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE' and result.prompt == ""


@pytest.mark.parametrize("feature,data", [(PARALLEL, parallel_data), (MULTI_REPO, multi_repo_data)])
def test_e3_protected_continuation_never_replays_full_plan(feature, data):
    instance = data()
    instance["continuation"] = {
        "prior_artifact_identity": "accepted-009-r1", "accepted_closure_layers": ["writer_b"],
        "accepted_prior_evidence": ["writer_b:sha256:abc"],
        "invalidation_boundary": ["writer_a"],
        "delta_scope": ["writer_a", "exact_union", "integration", "retirement"],
        "unresolved_checks_only": ["writer_a"], "checks_not_to_repeat": ["writer_b"],
    }
    instance["bindings"].append({**instance["bindings"][0], "binding_id": "accepted_009",
                                 "source_kind": "accepted_evidence", "source_identity": "accepted-009-r1"})
    result = run(feature, instance)
    assert result.compiler_result == ("NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE" if feature == MULTI_REPO else
                                      "NOT_READY_NEW_DECISION_BOUNDARY")
    assert result.prompt == ""
    assert any(term in result.receipt["diagnostics"][0]["message"] for term in
               ("accepted effect-state", "Q04 invalidation/protection"))


def test_e3_bogus_worker_identities_are_not_authenticated_by_generic_gates():
    data = parallel_data()
    worker = data["worker_contract"]["writers"][0]
    worker.update(base_oid="d" * 40, observed_head="e" * 40,
                  worktree_path="/workspace/bogus")
    data["bindings"].extend([
        {**data["bindings"][0], "binding_id": "manual_review", "source_kind": "accepted_evidence"},
        {**data["bindings"][0], "binding_id": "live_applicability",
         "source_kind": "repository_readback", "observed_state": {"status": "live"}},
    ])
    data["dispatch_gate"] = {"owner_authorization_binding": "owner_task",
                             "manual_governance_review_binding": "manual_review",
                             "live_applicability_binding": "live_applicability"}
    result = run(PARALLEL, data)
    assert result.compiler_result == "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE"
    assert result.prompt == "" and result.receipt["dispatchability"]["dispatchable"] is False


def test_e3_bogus_q05_base_is_not_authenticated_by_generic_gates():
    data = multi_repo_data()
    data["repositories"]["topcoffea"]["base"] = "historical-observation"
    result = run(MULTI_REPO, data)
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    assert not result.receipt["dispatchability"]["dispatchable"]
    data["repositories"]["topcoffea"]["candidate_worktree"] = "/foreign"
    assert not run(MULTI_REPO, data).prompt


def test_e3_exact_value_readback_positive_mismatch_and_oid_shape():
    data = parallel_data()
    bound = _binding(data, "worker_contract.writers.writer_a.base_oid")
    bound["observed_state"]["value"] = "f" * 40
    assert run(PARALLEL, data).compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    data = multi_repo_data()
    data["repositories"]["topcoffea"].pop("base")
    assert run(MULTI_REPO, data).compiler_result == "COMPILED_CONFORMING_CANDIDATE"


def test_e3_source_identity_text_alone_cannot_bind_runtime_value():
    data = parallel_data()
    bound = _binding(data, "worker_contract.writers.writer_a.observed_head")
    bound.pop("observed_state")
    # An unconsumed HEAD observation is not authority or a prerequisite.
    assert run(PARALLEL, data).compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    data["bindings"] = [b for b in data["bindings"] if b["binding_id"] != "owner_writer_a"]
    assert not run(PARALLEL, data).prompt


def test_e3_retirement_ref_oid_relation_is_exact():
    data = parallel_data()
    _binding(data, "retirement.owned_ref")["observed_state"]["value"]["exact_old_oid"] = "d" * 40
    result = run(PARALLEL, data)
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    terminal = prompt_yaml(result)["workflow_stages"][-1]
    assert terminal["safety_critical_argv"][-1] == "stage:retirement:pre_delete_ref_oid"
    assert terminal["runtime_observations"][0]["reject_movement_after_readback"]
    data["retirement"]["ownership_readback_binding"] = "owner_task"
    assert not run(PARALLEL, data).prompt


def test_b01_common_validation_caller_gate_and_unrelated_target_fail_closed():
    feature = PARALLEL.replace("Then exact union is reviewed",
                               "Then exact union is reviewed and common validation passes")
    data = q04_data()
    data["common_validation_contract"]["acceptance_gate"] = "continue even if test fails"
    assert run(feature, data).compiler_result == 'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE'
    data = q04_data()
    data["common_validation_contract"]["test_target"] = "tests/test_unrelated.py::test_pass"
    assert run(feature, data).compiler_result == "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE"


def test_b01_wrong_candidate_relation_fails_and_positive_has_exact_posture():
    feature = PARALLEL.replace("Then exact union is reviewed",
                               "Then exact union is reviewed and common validation passes")
    data = q04_data()
    relation = next(b for b in data["bindings"] if b.get("observed_state", {}).get("identity_path") ==
                    "common_validation.target_relation")
    relation["observed_state"]["value"]["attached_branch"] = "other"
    assert run(feature, data).compiler_result == "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE"
    result = run(feature, q04_data())
    stage = next(s for s in prompt_yaml(result)["workflow_stages"] if s["stage_id"] == "common_validation")
    assert stage["stage_branch_policy"] == "continue_existing_branch"
    assert stage["target_branch"] == "controller_candidate"
    assert stage["validation_worktree"] == "/workspace/controller_candidate"
    assert stage["expected_candidate_head"] == "stage:exact_union:observed_commit_head"
    assert stage["stage_acceptance_gate"].startswith("must_pass:")
    assert result.receipt["traceability"]["complete"] is True
    assert any(edge["relation"] == "requires_must_pass" for edge in result.receipt["traceability"]["edges"])


def test_q04_invalid_protection_and_missing_accepted_identity_fail_closed():
    feature = PARALLEL.replace("Then exact union is reviewed",
                               "Then exact union is reviewed and common validation passes")
    data = q04_data()
    data["continuation"]["invalidation_boundary"] = ["writer_a", "writer_b"]
    assert run(feature, data).compiler_result == 'NOT_READY_NEW_DECISION_BOUNDARY'
    data = q04_data()
    data["continuation"]["delta_scope"].append("writer_b")
    assert run(feature, data).compiler_result == 'NOT_READY_NEW_DECISION_BOUNDARY'
    data = q04_data()
    data["bindings"] = [b for b in data["bindings"] if b.get("observed_state", {}).get("identity_path") !=
                        "q04.accepted_writer_result"]
    assert run(feature, data).compiler_result == "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE"


def test_q05_candidate_carrier_and_pair_contract_fail_closed():
    data = multi_repo_data()
    del data["repositories"]["topcoffea"]["candidate_branch"]
    assert run(MULTI_REPO, data).compiler_result == 'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE'
    data = multi_repo_data()
    data["repositories"]["topcoffea"]["candidate_branch"] = "wrong/candidate"
    assert run(MULTI_REPO, data).compiler_result == 'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE'
    data = multi_repo_data()
    data["pair_validation_contract"]["covers"] = ["provider"]
    assert run(MULTI_REPO, data).compiler_result == 'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE'
    data = multi_repo_data()
    data["bindings"] = [b for b in data["bindings"] if b.get("observed_state", {}).get("identity_path") !=
                        "pair_validation.candidate_tuple"]
    assert run(MULTI_REPO, data).compiler_result == "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE"
    data = multi_repo_data()
    data["repositories"]["topcoffea"]["candidate_branch"] = "tc/dev-live"
    assert run(MULTI_REPO, data).compiler_result == 'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE'


def test_b04_split_or_contradictory_relations_fail_closed():
    data = parallel_data()
    data["bindings"] = [b for b in data["bindings"] if b.get("observed_state", {}).get("identity_path") !=
                        "worker_contract.writers.writer_a.carrier"]
    result = run(PARALLEL, data)
    assert result.compiler_result == "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE"
    assert result.prompt == "" and result.receipt["traceability"]["complete"] is False
    data = parallel_data()
    relation = next(b for b in data["bindings"] if b.get("observed_state", {}).get("identity_path") ==
                    "worker_contract.writers.writer_a.carrier")
    relation["observed_state"]["value"]["head"] = "f" * 40
    assert run(PARALLEL, data).compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    data = multi_repo_data()
    relation = next(b for b in data["bindings"] if b.get("observed_state", {}).get("identity_path") ==
                    "repositories.topcoffea.candidate_carrier")
    relation["observed_state"]["value"]["permanent_live_head"] = "f" * 40
    assert run(MULTI_REPO, data).compiler_result == "COMPILED_CONFORMING_CANDIDATE"

    relation["observed_state"]["value"]["candidate_worktree"] = "/foreign"
    assert not run(MULTI_REPO, data).prompt


def test_b04_missing_relation_trace_cannot_claim_completeness(monkeypatch):
    original = compiler._relation_edge

    def drop_trace(bindings, edges, identity_path, values, repo_id, stage_id,
                   source_kind="repository_readback"):
        original(bindings, edges, identity_path, values, repo_id, stage_id, source_kind)
        if identity_path == "worker_contract.writers.writer_a.carrier":
            edges.pop()

    monkeypatch.setattr(compiler, "_relation_edge", drop_trace)
    result = run(PARALLEL, parallel_data())
    assert result.compiler_result == "COMPILER_INVARIANT_FAILURE"
    assert result.prompt == "" and result.receipt["traceability"]["complete"] is False


def test_q05_partial_candidate_state_is_preserved_without_rollback():
    data = multi_repo_data()
    data["multi_repository_state"] = "PARTIAL"
    data["partial_effects"] = {"prepared_repo_identity": "topcoffea@" + "c" * 40,
                               "unresolved_recovery": "consumer candidate failed"}
    result = run(MULTI_REPO, data)
    assert result.compiler_result == 'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE'
    assert result.prompt == "" and result.receipt["partial_state"]["state"] == "PARTIAL"
    assert "rollback" not in str(result.receipt).lower()

    # A observed advancement survives B's certain pre-effect failure, and an
    # uncertain effect remains a distinct record. Neither permits replay.
    for outcome in ("failed_before_effect", "OUTCOME_UNKNOWN"):
        partial = multi_repo_advancement_data()
        partial["multi_repository_state"] = "PARTIALLY_INTEGRATED"
        partial["partial_effects"] = {
            "integrated_repo_identity": "topcoffea@" + "c" * 40,
            "preserved_candidate_identity": "topeft@" + "d" * 40,
            "consumer_effect_outcome": outcome,
            "unresolved_recovery": "readback required" if outcome == "OUTCOME_UNKNOWN" else "stopped before B effect"}
        stopped = run(MULTI_REPO.replace("write candidates", "write candidates and integrate"), partial)
        assert stopped.compiler_result == "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE"
        assert stopped.receipt["partial_state"]["observed_effects"] == partial["partial_effects"]
        assert stopped.receipt["authorized_effects"] == [] and not stopped.prompt


Q04_FEATURE = PARALLEL.replace("Then exact union is reviewed",
                               "Then exact union is reviewed and common validation passes")


def _binding(data, identity_path):
    return next(item for item in data["bindings"]
                if item.get("observed_state", {}).get("identity_path") == identity_path)


def _replace_literal(value, old, new):
    if isinstance(value, dict):
        return {key: _replace_literal(item, old, new) for key, item in value.items()}
    if isinstance(value, list):
        return [_replace_literal(item, old, new) for item in value]
    return value.replace(old, new) if isinstance(value, str) else value


def _plan(result):
    return prompt_yaml(result)["workflow_stages"]


def test_q04_m1_retired_protected_carrier_is_not_reacquired():
    data = q04_data()
    worker = data["worker_contract"]["writers"][1]
    for key in ("branch", "worktree_path", "observed_head", "base_oid"):
        del worker[key]
    data["bindings"] = [item for item in data["bindings"]
                        if not item.get("observed_state", {}).get("identity_path", "").startswith(
                            "worker_contract.writers.writer_b.")]
    result = run(Q04_FEATURE, data)
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE", result.receipt.get("diagnostics")
    assert "writer_b" not in [stage["stage_id"] for stage in _plan(result)]
    assert "prior:accepted-009-r1:writer_b@" + "b" * 40 in _plan(result)[2]["stage_inputs"]
    assert not any("writer_b.carrier" in str(edge) for edge in result.receipt["traceability"]["edges"])


@pytest.mark.parametrize("change", ["head", "worktree", "absent", "last_observed"])
def test_q04_m2_m3_later_carrier_observations_are_inert(change):
    baseline = run(Q04_FEATURE, q04_data())
    data = q04_data()
    worker = data["worker_contract"]["writers"][1]
    if change == "head":
        worker["observed_head"] = "f" * 40
        _binding(data, "worker_contract.writers.writer_b.observed_head")["observed_state"]["value"] = "f" * 40
        _binding(data, "worker_contract.writers.writer_b.carrier")["observed_state"]["value"]["head"] = "f" * 40
    elif change == "worktree":
        worker["worktree_path"] = "/retired/elsewhere"
        _binding(data, "worker_contract.writers.writer_b.worktree_path")["observed_state"]["value"] = "/retired/elsewhere"
        _binding(data, "worker_contract.writers.writer_b.carrier")["observed_state"]["value"]["worktree"] = "/retired/elsewhere"
    elif change == "absent":
        del worker["worktree_path"]
        data["bindings"] = [item for item in data["bindings"] if item.get("observed_state", {}).get(
            "identity_path") not in {"worker_contract.writers.writer_b.worktree_path",
                                     "worker_contract.writers.writer_b.carrier"}]
    else:
        for item in data["bindings"]:
            if item.get("observed_state", {}).get("identity_path", "").startswith(
                    "worker_contract.writers.writer_b."):
                item["acquisition"] = "last_observed"
    result = run(Q04_FEATURE, data)
    assert result.compiler_result == baseline.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    assert _plan(result) == _plan(baseline)
    assert result.receipt["safety_constraints"]["worker_contract"] == baseline.receipt[
        "safety_constraints"]["worker_contract"]


def test_q04_m4_m5_accepted_result_or_protection_change_fails_closed():
    data = yaml.safe_load(yaml.safe_dump(q04_data()))
    data["continuation"]["accepted_prior_evidence"][0] = dict(
        data["continuation"]["accepted_prior_evidence"][0])
    data["continuation"]["accepted_prior_evidence"][0]["observed_commit_head"] = "e" * 40
    assert run(Q04_FEATURE, data).compiler_result == "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE"
    data = q04_data()
    data["continuation"]["invalidation_boundary"] = ["writer_a", "writer_b"]
    assert run(Q04_FEATURE, data).compiler_result == 'NOT_READY_NEW_DECISION_BOUNDARY'


def test_q04_m6_m7_order_and_documentary_literals_do_not_create_authority():
    baseline = run(Q04_FEATURE, q04_data())
    data = q04_data()
    data["bindings"].reverse()
    data["bindings"].append({"binding_id": "documentary_oid", "claim": "unrelated note",
                             "materiality": "DOCUMENTARY", "source_kind": "other",
                             "source_identity": "note:" + "b" * 40, "acquisition": "acquired",
                             "validity_scope": "TOP26006_fw",
                             "observed_state": {"identity_path": "unrelated.note", "value": "b" * 40}})
    result = run(Q04_FEATURE, data)
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    assert _plan(result) == _plan(baseline)
    assert result.receipt["authorized_effects"] == baseline.receipt["authorized_effects"]
    data = q04_data()
    _binding(data, "q04.accepted_writer_result")["materiality"] = "DOCUMENTARY"
    assert run(Q04_FEATURE, data).compiler_result == "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE"


@pytest.mark.parametrize("old,new", [
    ("/workspace/worker_b", "/workspace/worker_a/../worker_a"),
    ("temporary/writer_b", "temporary/writer_a"),
    ("/workspace/controller_candidate", "/workspace/worker_a"),
    ("controller_candidate", "temporary/writer_a"),
])
def test_q03_i1_i4_all_material_path_and_ref_aliases_fail_after_local_binding(old, new):
    data = _replace_literal(parallel_data(), old, new)
    result = run(PARALLEL, data)
    assert result.compiler_result == "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE"
    assert result.receipt["isolation_verification"]["relation_local_consistency"] is True
    assert result.receipt["isolation_verification"]["cross_role_isolation"] is False


def test_q03_i5_i6_order_and_documentary_literals_are_inert():
    baseline = run(PARALLEL, parallel_data())
    data = parallel_data()
    data["bindings"].reverse()
    data["bindings"].append({"binding_id": "documentary_carrier", "claim": "unrelated",
                             "materiality": "DOCUMENTARY", "source_kind": "other",
                             "source_identity": "/workspace/worker_a", "acquisition": "acquired",
                             "validity_scope": "TOP26006_fw"})
    result = run(PARALLEL, data)
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    assert _plan(result) == _plan(baseline)
    assert result.receipt["isolation_verification"]["cross_role_isolation"] is True


@pytest.mark.parametrize("role_a,role_b", [
    ("topcoffea:candidate", "topeft:candidate"),
    ("topcoffea:candidate", "topeft:primary"),
    ("topeft:candidate", "topcoffea:primary"),
])
def test_q05_i1_i3_all_cross_repository_path_aliases_fail(role_a, role_b):
    data = multi_repo_data()
    def path_of(role):
        repo_id, carrier = role.split(":")
        return (data["prompt"]["repo_locations"][repo_id] if carrier == "primary" else
                data["repositories"][repo_id]["candidate_worktree"])
    repo_id, carrier = role_a.split(":")
    new_path = path_of(role_b) + ("/../" + path_of(role_b).rsplit("/", 1)[-1] if
                                  carrier == "candidate" else "")
    if carrier == "primary":
        data["prompt"]["repo_locations"][repo_id] = new_path
    else:
        data["repositories"][repo_id]["candidate_worktree"] = new_path
        _binding(data, f"repositories.{repo_id}.candidate_carrier")["observed_state"]["value"][
            "candidate_worktree"] = new_path
    result = run(MULTI_REPO, data)
    assert result.compiler_result == "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE"
    assert result.receipt["isolation_verification"]["relation_local_consistency"] is True
    assert result.receipt["isolation_verification"]["cross_repository_isolation"] is False


def test_q05_i4_wrong_repository_relation_fails_locally():
    data = multi_repo_data()
    _binding(data, "repositories.topcoffea.candidate_carrier")["observed_state"]["value"][
        "repository"] = "topeft"
    assert run(MULTI_REPO, data).compiler_result == "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE"


def test_q05_i5_i7_valid_carriers_and_permuted_repository_map():
    baseline = run(MULTI_REPO, multi_repo_data())
    assert baseline.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    data = multi_repo_data()
    data["repositories"] = dict(reversed(list(data["repositories"].items())))
    data["prompt"]["repo_locations"] = dict(reversed(list(data["prompt"]["repo_locations"].items())))
    data["bindings"].reverse()
    result = run(MULTI_REPO, data)
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE", result.receipt.get("diagnostics")
    assert _plan(result) == _plan(baseline)
    assert result.receipt["isolation_verification"]["cross_repository_isolation"] is True


def test_q05_i6_repository_aware_branch_check_does_not_pool_refs():
    data = multi_repo_data()
    data["repositories"]["topeft"]["candidate_branch"] = data["repositories"]["topcoffea"][
        "candidate_branch"]
    audit = {}
    edges = []
    compiler._verify_carrier_isolation(data, "multi_repository_coordination", edges, audit)
    assert audit["cross_repository_isolation"] is True
    assert run(MULTI_REPO, data).compiler_result == 'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE'


@pytest.mark.parametrize("shape", ["orchestrated_workflow", "multi_repository_coordination"])
def test_generic_material_carrier_path_alias_matrix(shape):
    data = parallel_data() if shape == "orchestrated_workflow" else multi_repo_data()
    audit = {}
    compiler._verify_carrier_isolation(data, shape, [], audit)
    roles = audit["carrier_roles"]
    for left in range(len(roles)):
        for right in range(left + 1, len(roles)):
            altered = yaml.safe_load(yaml.safe_dump(data))
            if shape == "orchestrated_workflow":
                carriers = altered["worker_contract"]["writers"]
                carriers.append({"stage_id": "exact_union", "worktree_path": altered[
                    "worker_contract"]["composition_worktree_path"], "branch": altered[
                    "worker_contract"]["composition_branch"]})
                carriers[left]["worktree_path"] = carriers[right]["worktree_path"]
            else:
                def get_path(role):
                    repo_id, kind = role.split(":")
                    return (altered["prompt"]["repo_locations"][repo_id] if kind == "primary" else
                            altered["repositories"][repo_id]["candidate_worktree"])
                repo_id, kind = roles[left].split(":")
                if kind == "primary":
                    altered["prompt"]["repo_locations"][repo_id] = get_path(roles[right])
                else:
                    altered["repositories"][repo_id]["candidate_worktree"] = get_path(roles[right])
            if shape == "multi_repository_coordination" and roles[left].endswith(":primary") and \
                    roles[right].endswith(":primary"):
                compiler._verify_carrier_isolation(altered, shape, [], {})
            else:
                with pytest.raises(compiler.Compile_error, match="material carrier path aliases"):
                    compiler._verify_carrier_isolation(altered, shape, [], {})


def test_generic_q03_material_ref_alias_matrix():
    data = parallel_data()
    branches = [worker["branch"] for worker in data["worker_contract"]["writers"]] + [
        data["worker_contract"]["composition_branch"]]
    for left in range(len(branches)):
        for right in range(left + 1, len(branches)):
            altered = yaml.safe_load(yaml.safe_dump(data))
            if left < 2:
                altered["worker_contract"]["writers"][left]["branch"] = branches[right]
            else:
                altered["worker_contract"]["composition_branch"] = branches[right]
            with pytest.raises(compiler.Compile_error, match="material mutable ref aliases"):
                compiler._verify_carrier_isolation(altered, "orchestrated_workflow", [], {})


def test_f01_controller_cannot_be_permanent_target_but_preservation_can():
    data = parallel_data()
    assert run(PARALLEL, data).compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    data["worker_contract"]["composition_branch"] = "master"
    bind = _binding(data, "worker_contract.composition_branch")
    bind["observed_state"]["value"] = "master"
    _binding(data, "worker_contract.composition_carrier")["observed_state"]["value"][
        "attached_branch"] = "master"
    data["common_validation_contract"]["target"] = "master"
    _binding(data, "common_validation.target_relation")["observed_state"]["value"][
        "attached_branch"] = "master"
    result = run(PARALLEL, data)
    assert result.compiler_result == "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE"
    assert "permanent integration target" in result.receipt["diagnostics"][0]["message"]
    data = parallel_data()
    data["retirement"]["exact_owned_surface"] = "refs/heads/master"
    assert run(PARALLEL, data).compiler_result != "COMPILED_CONFORMING_CANDIDATE"
    data = parallel_data()
    data["worker_contract"]["integration_target_branch"] = "temporary/writer_a"
    with pytest.raises(compiler.Compile_error, match="permanent integration target"):
        compiler._verify_carrier_isolation(data, "orchestrated_workflow", [], {})


def test_f01_repository_roots_may_share_location_while_candidates_stay_isolated():
    data = multi_repo_data()
    data["prompt"]["repo_locations"]["topeft"] = data["prompt"]["repo_locations"]["topcoffea"]
    assert run(MULTI_REPO, data).compiler_result == "COMPILED_CONFORMING_CANDIDATE"


def test_f02_raw_yaml_repository_permutation_reaches_parser_and_preserves_pair_order():
    data = multi_repo_data()
    raw = yaml.safe_dump(data, sort_keys=False)
    start = raw.index("  topcoffea:", raw.index("\nrepositories:\n"))
    middle = raw.index("  topeft:", start)
    end = raw.index("\nprompt:\n", middle)
    transformed = raw[:start] + raw[middle:end] + "\n" + raw[start:middle].rstrip("\n") + raw[end:]
    assert transformed != raw
    assert transformed.index("  topeft:", start) < transformed.index("  topcoffea:", start)
    assert list(yaml.safe_load(transformed)["repositories"]) == ["topeft", "topcoffea"]
    baseline = compile_fixture(MULTI_REPO, raw, "raw-map")
    result = compile_fixture(MULTI_REPO, transformed, "raw-map")
    assert result.compiler_result == baseline.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    assert _plan(result) == _plan(baseline)
    assert result.receipt["safety_constraints"]["candidate_pair_order"] == ["topcoffea", "topeft"]
    data["candidate_pair_order"] = ["topeft", "topcoffea"]
    assert run(MULTI_REPO, data).compiler_result == 'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE'


def test_f02_union_paths_are_set_like_but_pair_order_is_not():
    baseline = run(PARALLEL, parallel_data())
    data = parallel_data()
    data["worker_contract"]["union_paths"].reverse()
    result = run(PARALLEL, data)
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    assert _plan(result) == _plan(baseline)


@pytest.mark.parametrize("surface", ["allowed_to_modify", "heavy_command_permissions"])
def test_f03a_extra_simple_executable_scope_fails_closed(surface):
    feature, data = documentation_data()
    area = data["prompt"][surface]
    if surface == "heavy_command_permissions":
        area = area["allowed_to_modify"]
    area["TOP26006_fw"]["tracked_paths"].append("docs/unrequested.md")
    result = run(feature, data)
    assert result.compiler_result == "COMPILER_INVARIANT_FAILURE"
    assert "unrequested" in result.receipt["diagnostics"][0]["message"]
    assert run(*documentation_data()).compiler_result == "COMPILED_CONFORMING_CANDIDATE"


def test_f03a_extra_lifecycle_mechanic_and_wrong_repository_scope_fail():
    feature, data = documentation_data()
    data["prompt"]["allowed_to_modify"]["TOP26006_fw"]["git_effects"].append("integrate_exact_source")
    assert run(feature, data).compiler_result == "COMPILER_INVARIANT_FAILURE"
    feature, data = documentation_data()
    data["prompt"]["allowed_to_modify"]["topeft"] = ["docs/a.md"]
    with pytest.raises(compiler.Compile_error, match="unrequested"):
        compiler._verify_simple_scope(data["prompt"], compiler._effects(data, compiler.parse_gherkin(feature, "f")),
                                      compiler._bindings(data), {"TOP26006_fw": {}, "topeft": {}})


def test_f03b_material_given_uses_local_preflight_and_documentary_given_is_inert():
    feature, data = documentation_data()
    data["bindings"].append({
        "binding_id": "given_head", "claim": "branch applicability", "materiality": "DECISION_MATERIAL",
        "source_kind": "repository_readback", "source_identity": "branch:docs/example",
        "acquisition": "pending", "validity_scope": "TOP26006_fw",
        "dependent_effect_ids": ["commit_ref"],
        "runtime_preflight": "verify refs/heads/docs/example still names the authorized commit target",
        "material_reason": "the local ref write would otherwise target a different branch",
    })
    data["given_bindings"] = {"3": "given_head"}
    unsupported = run(feature, data)
    assert unsupported.receipt["given_readiness"][0]["state"] == "unsupported_material_premise"
    assert unsupported.receipt["excluded_effects"] == ["commit_ref"]
    feature = feature.replace("semantics are established", "the selected commit branch is checked out")
    result = run(feature, data)
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE", result.receipt.get("diagnostics")
    assert "must_pass_before_effects" in result.prompt
    assert result.receipt["given_readiness"][0]["state"] == "runtime_preflight_requirement"
    data["bindings"][-1]["runtime_preflight"] = ""
    # Removing prose cannot remove a compiler-derived check.
    assert prompt_yaml(run(feature, data)) == prompt_yaml(result)
    missing = run(feature.replace("the selected commit branch is checked out", "magic holds"), data)
    assert missing.compiler_result == "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE"
    assert missing.prompt and missing.receipt["excluded_effects"] == ["commit_ref"]
    assert missing.receipt["authorized_effects"] == ["effect_1"]
    assert missing.receipt["dispatchability"]["dispatchable"] is False
    data["bindings"][-1]["runtime_preflight"] = "verify HEAD_required"
    assert prompt_yaml(run(feature, data)) == prompt_yaml(result)
    data["bindings"][-1]["materiality"] = "DOCUMENTARY"
    assert run(feature, data).compiler_result == "COMPILED_CONFORMING_CANDIDATE"


def test_f03b_nonmaterial_head_drift_does_not_block_simple_task():
    feature, data = documentation_data()
    data["bindings"].append({
        "binding_id": "given_head", "claim": "observed head", "materiality": "DOCUMENTARY",
        "source_kind": "repository_readback", "source_identity": "branch:docs/example",
        "acquisition": "acquired", "validity_scope": "TOP26006_fw",
        "observed_state": {"identity_path": "ordinary_head", "value": "a" * 40},
        "dependent_effect_ids": [],
    })
    data["given_bindings"] = {"3": "given_head"}
    baseline = run(feature, data)
    data["bindings"][-1]["observed_state"]["value"] = "b" * 40
    result = run(feature, data)
    assert result.compiler_result == baseline.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    assert prompt_yaml(result) == prompt_yaml(baseline)


def test_f03c_negative_remote_assertion_constrains_effects():
    data = base_data()
    data["prompt"].update(prompt_mode="pr_publication", branch_policy="continue_existing_branch",
                          target_branch="main")
    data["prompt"]["allowed_to_modify"] = {"TOP26006_fw": ["refs/heads/main"]}
    data["prompt"]["heavy_command_permissions"] = {"remote_git_write": True, "network_access": True}
    add_effect(data, "remote_git_write", "refs/heads/main", 4, "remote_git_write")
    feature = "Feature: remote publication\nScenario: publish\nGiven authority is bound\nWhen I push remote ref\nThen the report cites evidence\nBut no remote repository is modified"
    assert run(feature, data).compiler_result == "NOT_READY_NEW_DECISION_BOUNDARY"
    assert run(feature.replace("\nBut no remote repository is modified", ""), data).compiler_result == \
        "COMPILED_CONFORMING_CANDIDATE"


@pytest.mark.parametrize("unsafe", ["refs/heads/-oops;rm", "refs/heads/../../main",
                                           "refs/heads/temp.lock", "refs/heads/temp name"])
def test_f04_unsafe_retirement_ref_never_becomes_command(unsafe):
    data = _replace_literal(parallel_data(), "refs/heads/temp-worker", unsafe)
    result = run(PARALLEL, data)
    assert result.prompt == ""
    assert result.compiler_result in {'COMPILER_INVARIANT_FAILURE',
                                       "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE"}
    assert run(PARALLEL, parallel_data()).compiler_result == "COMPILED_CONFORMING_CANDIDATE"


def test_f05_receipt_source_and_validator_identities_are_current():
    result = run()
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    receipt = result.receipt
    assert receipt["generated_prompt_sha256"] == hashlib.sha256(result.prompt.encode()).hexdigest()
    assert receipt["compiler_identity"]["sha256"] == hashlib.sha256(Path(
        compiler.__file__).read_bytes()).hexdigest()
    assert receipt["canonical_governance"]["applicable_sources"]["AGENTS.md"] == \
        hashlib.sha256((Path(compiler.__file__).resolve().parents[1] / "AGENTS.md").read_bytes()).hexdigest()
    assert receipt["maintained_validator"]["sha256"] == hashlib.sha256(compiler.VALIDATOR.read_bytes()).hexdigest()
    assert receipt["maintained_validator"]["locator"] == str(compiler.VALIDATOR.relative_to(compiler.ROOT))
    assert receipt["maintained_validator"]["version"]
    assert receipt["input_binding_identity"]["sha256"] == hashlib.sha256(
        fixture_graph(SIMPLE, yaml.safe_dump(base_data()))[1].encode()).hexdigest()


@pytest.mark.parametrize("assertion", ["exact union is reviewed", "the composed candidate is reviewed",
                                      "combined worker results are reviewed"])
def test_composition_behavior_derives_common_validation_without_magic_words(assertion):
    feature = PARALLEL.replace("exact union is reviewed", assertion)
    result = run(feature, parallel_data())
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE", result.receipt.get("diagnostics")
    stages = prompt_yaml(result)["workflow_stages"]
    ids = [stage["stage_id"] for stage in stages]
    assert ids.index("exact_union") < ids.index("common_validation") < ids.index("integration")
    assert "stage:common_validation:common_validation_evidence" in stages[-2]["stage_inputs"]
    data = parallel_data()
    del data["common_validation_contract"]
    assert run(feature, data).compiler_result == 'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE'


def test_validation_words_without_composition_do_not_invent_gate():
    feature = SIMPLE.replace("bounded inspection", "common validation passes")
    result = run(feature)
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    assert "workflow_stages" not in prompt_yaml(result)


@pytest.mark.parametrize("damage", ["remove_dependency", "move_after_integration", "remove_stage"])
def test_integration_validation_dependency_is_verified_independently(monkeypatch, damage):
    original = compiler._plan_stages
    def damaged(*args, **kwargs):
        stages = original(*args, **kwargs)
        validation = next(s for s in stages if s["stage_id"] == "common_validation")
        integration = next(s for s in stages if s["stage_id"] == "integration")
        if damage == "remove_dependency":
            integration["stage_inputs"].remove("stage:common_validation:common_validation_evidence")
        else:
            stages.remove(validation)
            if damage == "move_after_integration":
                stages.insert(stages.index(integration) + 1, validation)
        return stages
    monkeypatch.setattr(compiler, "_plan_stages", damaged)
    result = run(PARALLEL, parallel_data())
    assert result.compiler_result == "COMPILER_INVARIANT_FAILURE"
    assert not result.prompt


def material_given_data(property_text, acquired=False):
    feature, data = documentation_data()
    feature = feature.replace("semantics are established", property_text)
    data["bindings"].append({
        "binding_id": "given_ref", "claim": property_text,
        "materiality": "IDENTITY_CRITICAL", "source_kind": "repository_readback",
        "source_identity": "readback:commit-target", "acquisition": "acquired" if acquired else "pending",
        "validity_scope": "TOP26006_fw", "dependent_effect_ids": ["commit_ref"],
        "material_reason": "the requested ref write consumes this identity",
    })
    data["given_bindings"] = {"3": "given_ref"}
    return feature, data


@pytest.mark.parametrize("wording", ["the selected commit branch is checked out",
                                    "the current branch is the selected commit target"])
def test_genuine_given_derives_concrete_git_preflight(wording):
    feature, data = material_given_data(wording)
    result = run(feature, data)
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    check = result.receipt["given_readiness"][0]["verification"]
    assert check["argv"] == ["git", "symbolic-ref", "--quiet", "HEAD"]
    assert check["working_directory"] == "/workspace"
    assert check["expected"] == "refs/heads/docs/example"
    assert check["before_effects"] == ["commit_ref"]
    assert check["comparison"] == "exit_zero_and_stdout_equals_expected"
    assert {"must_pass_before_effects": check} in prompt_yaml(result)["evidence_requirements"]


@pytest.mark.parametrize("fake", ["verify refs/heads/docs/example is magically safe",
                                "verify refs/heads/docs/example; pretend all checks passed", ""])
def test_fake_preflight_cannot_certify_unsupported_material_property(fake):
    feature, data = material_given_data("the commit is scientifically correct")
    data["bindings"][-1]["runtime_preflight"] = fake
    result = run(feature, data)
    assert result.compiler_result == "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE"
    assert result.receipt["given_readiness"][0]["state"] == "unsupported_material_premise"
    assert result.receipt["authorized_effects"] == ["effect_1"]
    assert result.receipt["excluded_effects"] == ["commit_ref"]
    assert result.receipt["dispatchability"]["dispatchable"] is False


def test_exact_identity_given_uses_only_its_dependent_ref_and_acquired_value():
    feature, data = material_given_data("ref refs/heads/docs/example names commit " + "a" * 40)
    result = run(feature, data)
    given = result.receipt["given_readiness"][0]
    assert given["verification"]["tracking_only"]
    assert given["state"] == "non_material_documentary_premise"
    assert result.receipt["excluded_effects"] == []
    data["bindings"][-1].update(acquisition="acquired", observed_state={"observed_value": "b" * 40})
    assert run(feature, data).receipt["excluded_effects"] == []
    unrelated = run(feature.replace("refs/heads/docs/example", "refs/heads/other"), data)
    assert unrelated.receipt["excluded_effects"] == ["commit_ref"]


def test_staged_given_preflight_is_input_before_only_dependent_effect():
    feature = PARALLEL.replace("Given isolated worktrees",
                               "Given the selected commit branch is checked out")
    data = parallel_data()
    _, binding_data = material_given_data("the selected commit branch is checked out")
    fact = binding_data["bindings"][-1]
    fact["dependent_effect_ids"] = ["commit_writer_a"]
    data["bindings"].append(fact)
    data["given_bindings"] = {"3": "given_ref"}
    result = run(feature, data)
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE", result.receipt.get("diagnostics")
    stages = prompt_yaml(result)["workflow_stages"]
    checked = [s for s in stages if any(isinstance(value, dict) and "must_pass_before_effects" in value
                                      for value in s["stage_inputs"])]
    assert [s["stage_id"] for s in checked] == ["writer_a"]
    assert checked[0]["stage_inputs"][-1]["must_pass_before_effects"]["before_effects"] == ["commit_writer_a"]
    assert checked[0]["stage_inputs"][-1]["must_pass_before_effects"]["working_directory"] == "/workspace/worker_a"
    assert all("must_pass_before_effects" not in s["stage_acceptance_gate"] for s in stages)


def test_documentary_given_with_declared_dependencies_does_not_create_gate():
    feature, data = material_given_data("historical SHA was recorded")
    data["bindings"][-1]["materiality"] = "DOCUMENTARY"
    result = run(feature, data)
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    readiness = result.receipt["given_readiness"][0]
    assert readiness["state"] == "non_material_documentary_premise"
    assert readiness["dependent_effect_ids"] == []
    assert readiness["verification"] is None


@pytest.mark.parametrize("action", [
    "writers edit, integrate, and retire branches",
    "two writers write disjoint files, advance the target, and remove temporary branches",
])
def test_r2_composition_dependency_is_semantic_and_role_sensitive(action):
    feature = PARALLEL.replace("writers edit, integrate, and retire branches", action)
    result = run(feature, parallel_data())
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE", result.receipt.get("diagnostics")
    stages = prompt_yaml(result)["workflow_stages"]
    assert [s["stage_id"] for s in stages][-3:] == ["common_validation", "integration", "retirement"]
    assert {"source": "gate:common_validation", "output": "stage:integration",
            "relation": "required_predecessor"} in result.receipt["traceability"]["edges"]


@pytest.mark.parametrize("action", [
    "writers edit and retire branches",
    "writers edit integration documentation and retire branches",
    "writers edit but do not integrate, and retire branches",
])
def test_r2_inventory_or_mentions_cannot_request_integration(action):
    result = run(PARALLEL.replace("writers edit, integrate, and retire branches", action), parallel_data())
    assert result.compiler_result == ("NOT_READY_NEW_DECISION_BOUNDARY"
                                      if action == "writers edit and retire branches" else
                                      "IMPLEMENTATION_GAP")
    assert not result.prompt


def test_r2_orchestration_without_composition_has_no_common_gate():
    result = run(MULTI_REPO, multi_repo_data())
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    assert prompt_yaml(result)["prompt_mode"] == "orchestrated_workflow"
    assert "common_validation" not in [s["stage_id"] for s in prompt_yaml(result)["workflow_stages"]]


@pytest.mark.parametrize("assertion", ["success", "output exists", "the result is ready",
                                      "common validation passes"])
def test_r2_generic_or_unrepresentable_assertion_cannot_claim_completeness(assertion):
    result = run(SIMPLE.replace("the report cites evidence", assertion))
    assert result.compiler_result == 'NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE'
    assert not result.receipt["traceability"]["complete"]


def given_observation(check, fact):
    return {**{key: check[key] for key in
               ("property", "repository_id", "working_directory", "target", "argv", "comparison")},
            "observed_value": check["expected"], "source_identity": fact["source_identity"],
            "validity_scope": fact["validity_scope"],
            "dependent_effect_ids": sorted(fact["dependent_effect_ids"])}


def staged_given_data(effect_id="commit_writer_a", source_kind="repository_readback", data=None):
    data = parallel_data() if data is None else data
    feature = PARALLEL.replace("isolated worktrees", "the selected commit branch is checked out")
    _, simple = material_given_data("the selected commit branch is checked out")
    fact = simple["bindings"][-1]
    fact.update(dependent_effect_ids=[effect_id], source_kind=source_kind)
    data["bindings"].append(fact)
    data["given_bindings"] = {"3": fact["binding_id"]}
    return feature, data, fact


@pytest.mark.parametrize("effect_id,carrier", [
    ("commit_writer_a", "/workspace/worker_a"),
    ("commit_controller", "/workspace/controller_candidate"),
])
def test_r2_given_uses_effect_carrier_independently_of_root(effect_id, carrier):
    feature, data, fact = staged_given_data(effect_id)
    result = run(feature, data)
    check = result.receipt["given_readiness"][0]["verification"]
    assert check["working_directory"] == carrier
    data["prompt"]["repo_locations"]["TOP26006_fw"] = "/unrelated/root"
    bind_state(data, "root.current_branch", "wrong-root-branch")
    changed = run(feature, data)
    assert changed.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    assert changed.receipt["given_readiness"] == result.receipt["given_readiness"]
    fact["acquisition"] = "acquired"
    fact["observed_state"] = given_observation(check, fact)
    assert run(feature, data).receipt["given_readiness"][0]["state"] == "already_acquired_material_fact"
    fact["observed_state"]["observed_value"] = "refs/heads/wrong_writer"
    bind_state(data, "root.current_branch", check["expected"])
    wrong = run(feature, data)
    assert wrong.receipt["excluded_effects"] == [effect_id]
    assert not wrong.receipt["dispatchability"]["dispatchable"]


@pytest.mark.parametrize("source_kind", ["repository_readback", "accepted_evidence"])
@pytest.mark.parametrize("damage", ["working_directory", "source_identity", "argv", "validity_scope",
                                    "observed_value", "dependent_effect_ids"])
def test_r2_acquired_fact_binds_exact_context_and_evidence_identity(source_kind, damage):
    feature, data, fact = staged_given_data(source_kind=source_kind)
    check = run(feature, data).receipt["given_readiness"][0]["verification"]
    fact.update(acquisition="acquired", observed_state=given_observation(check, fact))
    accepted = run(feature, data)
    assert accepted.receipt["given_readiness"][0]["state"] == "already_acquired_material_fact"
    assert "must_pass_before_effects" not in accepted.prompt
    if damage == "source_identity":
        # Even unchanged observed content cannot silently authenticate a new locator.
        fact["source_identity"] = "different:artifact"
    else:
        fact["observed_state"][damage] = "/workspace" if damage == "working_directory" else "wrong"
    rejected = run(feature, data)
    assert rejected.receipt["excluded_effects"] == ["commit_writer_a"]
    assert "writer_b" in rejected.receipt["authorized_effects"]
    assert not rejected.receipt["dispatchability"]["dispatchable"]


def test_r2_generic_live_evidence_cannot_authenticate_exact_given():
    feature, data = material_given_data("ref refs/heads/docs/example names commit " + "f" * 40, acquired=True)
    fact = data["bindings"][-1]
    fact["source_identity"] = "generic:live_applicability"
    fact["observed_state"] = {"value": "f" * 40}
    result = run(feature, data)
    assert result.receipt["given_readiness"][0]["state"] == "non_material_documentary_premise"
    assert not result.receipt["dispatchability"]["dispatchable"]
    # The hash-only observation supplies no missing effect authority.
    data["bindings"] = [b for b in data["bindings"] if b["binding_id"] != "commit_owner"]
    assert not run(feature, data).prompt


@pytest.mark.parametrize("acquisition", ["pending", "superseded", "last_observed"])
def test_r2_expired_accepted_current_fact_requires_fresh_exact_check(acquisition):
    feature, data, fact = staged_given_data(source_kind="accepted_evidence")
    check = run(feature, data).receipt["given_readiness"][0]["verification"]
    fact.update(acquisition=acquisition, observed_state=given_observation(check, fact))
    result = run(feature, data)
    assert result.receipt["given_readiness"][0]["state"] == "runtime_preflight_requirement"
    assert "must_pass_before_effects" in result.prompt


def test_r2_invalidated_accepted_fact_is_not_reused():
    feature, data, fact = staged_given_data(source_kind="accepted_evidence", data=q04_data())
    check = run(feature, data).receipt["given_readiness"][0]["verification"]
    fact.update(acquisition="acquired", observed_state=given_observation(check, fact))
    result = run(feature, data)
    assert result.receipt["given_readiness"][0]["state"] == "runtime_preflight_requirement"
    assert "writer_b" not in [s["stage_id"] for s in prompt_yaml(result)["workflow_stages"]]


def test_r2_q04_given_consumes_portable_accepted_result_without_carrier_readback():
    data = q04_data()
    accepted = data["continuation"]["accepted_prior_evidence"][0]
    fact = _binding(data, "q04.accepted_writer_result")
    fact["dependent_effect_ids"] = ["commit_controller"]
    data["given_bindings"] = {"3": fact["binding_id"]}
    feature = PARALLEL.replace("isolated worktrees",
        "accepted writer writer_b result names commit " + accepted["observed_commit_head"])
    for worker in data["worker_contract"]["writers"]:
        if worker["stage_id"] == "writer_b":
            worker.update(branch="retired", worktree_path="/retired", observed_head="f" * 40)
    result = run(feature, data)
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE", result.receipt.get("diagnostics")
    assert result.receipt["given_readiness"][0]["state"] == "already_acquired_material_fact"
    assert "must_pass_before_effects" not in result.prompt
    assert "/retired" not in result.prompt
    assert "writer_b" not in [s["stage_id"] for s in prompt_yaml(result)["workflow_stages"]]
    wrong = run(feature.replace(accepted["observed_commit_head"], "d" * 40), data)
    assert wrong.receipt["excluded_effects"] == ["commit_controller"]


def test_r2_permanent_target_given_needs_explicit_target_carrier():
    feature, data, fact = staged_given_data("integrate")
    assert run(feature, data).receipt["excluded_effects"] == ["integrate"]
    bind_relation(data, "worker_contract.integration_target_carrier", {
        "repository": "TOP26006_fw", "worktree": "/permanent/target", "attached_branch": "master",
        "head": "a" * 40})
    result = run(feature, data)
    assert result.receipt["given_readiness"][0]["verification"]["working_directory"] == "/permanent/target"
    assert result.receipt["given_readiness"][0]["state"] == "runtime_preflight_requirement"


def test_r2_q05_given_uses_repository_local_candidate():
    data = multi_repo_data()
    effect = next(e for e in data["requested_effects"] if e["stage_id"] == "provider_candidate" and
                  e["effect"] == "local_git_ref_write")
    _, simple = material_given_data("the selected commit branch is checked out")
    fact = simple["bindings"][-1]
    fact.update(validity_scope="topcoffea", dependent_effect_ids=[effect["effect_id"]])
    data["bindings"].append(fact); data["given_bindings"] = {"3": fact["binding_id"]}
    result = run(MULTI_REPO.replace("exact bases", fact["claim"]), data)
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE", result.receipt.get("diagnostics")
    check = result.receipt["given_readiness"][0]["verification"]
    assert check["working_directory"] == data["repositories"]["topcoffea"]["candidate_worktree"]
    assert check["repository_id"] == "topcoffea"


def test_r2_given_plan_follows_writer_carrier_and_ignores_yaml_order():
    feature, data, fact = staged_given_data()
    baseline = run(feature, data)
    moved = _replace_literal(data, "/workspace/worker_a", "/new/writer_a")
    result = compile_fixture(feature, yaml.safe_dump(moved, sort_keys=False))
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    assert result.receipt["given_readiness"][0]["verification"]["working_directory"] == "/new/writer_a"
    assert result.receipt["given_readiness"] != baseline.receipt["given_readiness"]
    reordered = compile_fixture(feature, yaml.safe_dump(moved, sort_keys=True))
    assert prompt_yaml(reordered) == prompt_yaml(result)


def test_r2_only_material_observed_oid_changes_effect_readiness():
    feature, data = material_given_data("ref refs/heads/docs/example names commit " + "a" * 40)
    fact = data["bindings"][-1]
    fact.update(acquisition="acquired", source_kind="accepted_evidence", observed_state={"observed_value": "b" * 40})
    result = run(feature, data)
    assert result.receipt["excluded_effects"] == []
    assert result.receipt["given_readiness"][0]["verification"]["tracking_only"]


def parallel_subset_data(composition=True):
    """Owner bindings for a smaller behavior; no orphan effects are retained."""
    data = parallel_data()
    roles = {'writer_a', 'writer_b'} | ({'exact_union'} if composition else set())
    data['requested_effects'] = [e for e in data['requested_effects'] if e['stage_id'] in roles]
    data.pop('retirement')
    data.pop('common_validation_contract')
    return data


@pytest.mark.parametrize('composition', [True, False])
def test_r3_parallel_subset_is_implemented_without_invented_integration(composition):
    assertion = 'exact union is reviewed' if composition else 'writer results are reviewed'
    feature = PARALLEL.replace('writers edit, integrate, and retire branches', 'writers edit').replace(
        'exact union is reviewed', assertion)
    result = run(feature, parallel_subset_data(composition))
    assert result.compiler_result == 'COMPILED_CONFORMING_CANDIDATE', result.receipt.get('diagnostics')
    ids = [s['stage_id'] for s in prompt_yaml(result)['workflow_stages']]
    assert ids == ['writer_a', 'writer_b', 'independent_review'] + (
        ['exact_union', 'reconciled_review'] if composition else [])
    assert not {'integration', 'retirement', 'common_validation'} & set(ids)
    assert result.receipt['execution_shape_classification'] == 'SUPPORTED_EXECUTION_SHAPE'


def test_r3_effect_inventory_cannot_request_absent_parallel_phases():
    feature = PARALLEL.replace('writers edit, integrate, and retire branches', 'writers edit')
    data = parallel_data()
    data.pop('common_validation_contract')
    result = run(feature, data)
    assert result.compiler_result == 'COMPILER_INVARIANT_FAILURE'
    assert not result.prompt


def test_r3_boundary_payload_distinguishes_contract_gap_and_unknown():
    data = base_data()
    data['prompt']['branch_policy'] = 'historical_worker_magic'
    unsupported = run(data=data)
    assert unsupported.compiler_result == 'UNSUPPORTED_CANONICAL_CONSTRUCT'
    gap = run("Feature: standard input\nScenario Outline: bounded examples\nGiven known inputs\n"
              "When I inspect the document\nThen the report cites evidence")
    assert gap.compiler_result == 'IMPLEMENTATION_GAP'
    ambiguous = run(SIMPLE.replace('I inspect the document', 'I invoke an undefined operation'))
    assert ambiguous.compiler_result == 'ARCHITECTURE_BOUNDARY_UNRESOLVED'
    for result, classification in [(unsupported, 'normative'), (gap, 'implementation_gap'),
                                   (ambiguous, 'unresolved')]:
        boundary = result.receipt['unsupported_construct']
        assert boundary['current_architecture_boundary']['classification'] == classification
        assert boundary['current_architecture_boundary']['source_documents']
        assert boundary['current_architecture_boundary']['exact_contract_or_section']
        assert boundary['semantic_pattern'] and boundary['missing_capability']
        assert boundary['recommended_next_boundary'] and boundary['decision_options']
        assert result.receipt['authorized_effects'] == [] and not result.prompt
        assert result.receipt['manual_fallback'] == 'independently_evaluable_under_canonical_governance'


def move_writer_head(data, writer_id, new_head):
    worker = next(w for w in data['worker_contract']['writers'] if w['stage_id'] == writer_id)
    worker['observed_head'] = new_head
    for binding in data['bindings']:
        state = binding.get('observed_state')
        if not isinstance(state, dict):
            continue
        if state.get('identity_path') == f'worker_contract.writers.{writer_id}.observed_head':
            state['value'] = new_head
        if state.get('identity_path') == f'worker_contract.writers.{writer_id}.carrier':
            state['value']['head'] = new_head


def acquired_writer_ref_given(source_kind='accepted_evidence'):
    feature, data, fact = staged_given_data(source_kind=source_kind)
    feature = feature.replace('the selected commit branch is checked out',
                              'ref refs/heads/temporary/writer_a names commit ' + 'a' * 40)
    check = run(feature, data).receipt['given_readiness'][0]['verification']
    fact.update(acquisition='acquired', observed_state=given_observation(check, fact))
    return feature, data, fact


@pytest.mark.parametrize('source_kind', ['accepted_evidence', 'repository_readback'])
def test_r3_changed_consumed_carrier_invalidates_only_dependent_effect(source_kind):
    feature, data, fact = acquired_writer_ref_given(source_kind)
    move_writer_head(data, 'writer_a', 'b' * 40)
    result = run(feature, data)
    assert result.compiler_result == 'COMPILED_CONFORMING_CANDIDATE'
    assert result.receipt['excluded_effects'] == []
    assert result.receipt['given_readiness'][0]['verification']['tracking_only']
    # An actual resource substitution still fails independently of tracking values.
    data['worker_contract']['writers'][0]['worktree_path'] = '/foreign'
    assert not run(feature, data).prompt


def test_r3_unrelated_carrier_and_unconsumed_head_do_not_invalidate_given():
    feature, data, fact = acquired_writer_ref_given()
    move_writer_head(data, 'writer_b', 'd' * 40)
    assert run(feature, data).receipt['excluded_effects'] == []
    feature, data, fact = staged_given_data(source_kind='accepted_evidence')
    check = run(feature, data).receipt['given_readiness'][0]['verification']
    fact.update(acquisition='acquired', observed_state=given_observation(check, fact))
    move_writer_head(data, 'writer_a', 'e' * 40)
    result = run(feature, data)
    assert result.receipt['excluded_effects'] == []
    assert result.receipt['given_readiness'][0]['validity_relation']['state'] == 'unchanged_consumed_property'


def test_r3_validity_relation_is_property_based_for_simple_current_carrier():
    feature, data = material_given_data('the selected commit branch is checked out')
    fact = data['bindings'][-1]
    check = run(feature, data).receipt['given_readiness'][0]['verification']
    fact.update(acquisition='acquired', observed_state=given_observation(check, fact))
    bind_relation(data, 'repositories.TOP26006_fw.current_carrier', {
        'repository': 'TOP26006_fw', 'worktree': check['working_directory'],
        'attached_branch': 'other_branch', 'head': 'a' * 40})
    result = run(feature, data)
    assert result.receipt['excluded_effects'] == ['commit_ref']
    assert result.receipt['given_readiness'][0]['validity_relation']['observed_property'] == 'current_branch'


GRAPH_SIMPLE = '''Feature: bounded inspection
  This description documents the flow and grants no authority.
  ```text
  [G1] Given
    |
    v
  [W1] Inspect
    |
    v
  [T1] Evidence
  ```
  Scenario: inspect one document
    Given [G1] the document identity is acquired
    When [W1] I inspect the document
    Then [T1] the report cites evidence
'''


def test_r3_literal_source_and_generated_ascii_graphs_match_semantics():
    result = compile_contract(GRAPH_SIMPLE, yaml.safe_dump(base_data()))
    assert result.compiler_result == 'COMPILED_CONFORMING_CANDIDATE', result.receipt.get('diagnostics')
    visualization = result.receipt['workflow_visualization']
    assert visualization['source_graph']['nodes'] == ['G1', 'T1', 'W1']
    assert visualization['source_graph']['connectors'] == [
        {'source': 'G1', 'target': 'W1'}, {'source': 'W1', 'target': 'T1'}]
    assert visualization['consistency'] is True
    assert 'derived_external_acceptance' in visualization['generated_graph']['nodes']
    drawing = result.prompt.split('```text\n', 1)[1].split('\n```', 1)[0]
    assert compiler._ascii_graph(drawing) == visualization['generated_graph']
    assert result.receipt['maintained_validator']['result'] == 'pass'


@pytest.mark.parametrize('replacement', [
    ('[W1] Inspect', '[new_effect] Publish'),
    ('    |\n    v\n  [T1] Evidence', '  [T1] Evidence'),
    ('  [T1] Evidence\n  ```', '  [T1] Evidence\n  [T1] --> [G1]\n  ```'),
    ('    v\n  [W1]', '    |\n  [W1]'),
])
def test_r3_graph_cannot_add_omit_or_reverse_behavior(replacement):
    result = compile_contract(GRAPH_SIMPLE.replace(*replacement), yaml.safe_dump(base_data()))
    assert result.compiler_result == 'WORKFLOW_GRAPH_INCONSISTENT'
    assert not result.prompt and not result.receipt['dispatchability']['dispatchable']


def test_r3_missing_graph_cannot_emit_conforming_prompt():
    result = compile_contract(SIMPLE, yaml.safe_dump(base_data()))
    assert result.compiler_result == 'WORKFLOW_GRAPH_INCONSISTENT'
    assert not result.prompt


def test_r3_harmless_graph_captions_and_description_preserve_plan():
    first = compile_contract(GRAPH_SIMPLE, yaml.safe_dump(base_data()))
    second = compile_contract(GRAPH_SIMPLE.replace('Inspect\n', 'Read document\n').replace(
        'documents the flow', 'describes this same workflow'), yaml.safe_dump(base_data()))
    assert first.compiler_result == second.compiler_result == 'COMPILED_CONFORMING_CANDIDATE'
    assert first.receipt['workflow_visualization'] == second.receipt['workflow_visualization']


def test_r3_ascii_branch_and_join_geometry_without_edge_list():
    diagram = '''              +--> [W1] Writer A --+
              |                    |
[G1] Given ---+                    +--> [C1] Exact union
              |                    |
              +--> [W2] Writer B --+'''
    graph = compiler._ascii_graph(diagram)
    assert {(e['source'], e['target']) for e in graph['connectors']} == {
        ('G1', 'W1'), ('G1', 'W2'), ('W1', 'C1'), ('W2', 'C1')}


def test_r3_generated_parallel_graph_has_branches_join_validation_and_stop():
    result = run(PARALLEL, parallel_data())
    assert result.compiler_result == 'COMPILED_CONFORMING_CANDIDATE'
    graph = result.receipt['workflow_visualization']['generated_graph']
    edges = {(e['source'], e['target']) for e in graph['connectors']}
    assert {('s4', 'derived_writer_a'), ('s4', 'derived_writer_b'),
            ('derived_writer_a', 'derived_independent_review'),
            ('derived_writer_b', 'derived_independent_review'),
            ('derived_common_validation', 'derived_integration'),
            ('derived_integration', 'derived_retirement'),
            ('derived_integration', 'derived_stop')} <= edges
    assert ('derived_writer_a', 'derived_writer_b') not in edges
    assert set(graph['nodes']) == {m['node'] for m in result.receipt['workflow_visualization']['execution_mapping']}


def test_r3_preflight_graph_gates_only_consuming_effect():
    feature, data, fact = staged_given_data()
    result = run(feature, data)
    graph = result.receipt['workflow_visualization']['generated_graph']
    edges = {(e['source'], e['target']) for e in graph['connectors']}
    assert ('derived_preflight_s3', 'derived_writer_a') in edges
    assert ('derived_preflight_s3', 'derived_writer_b') not in edges
    assert ('derived_preflight_s3', 'derived_stop') in edges


def test_r3_generator_corruption_fails_graph_readback(monkeypatch):
    draw = compiler._draw_ascii
    monkeypatch.setattr(compiler, '_draw_ascii', lambda nodes, edges: draw(nodes, edges) + '\n[extra_effect]')
    result = compile_contract(GRAPH_SIMPLE, yaml.safe_dump(base_data()))
    assert result.compiler_result == 'WORKFLOW_GRAPH_INCONSISTENT'
    assert not result.prompt


GRAPH_PARALLEL = '''Feature: parallel writers
  ```text
                +--> [W1] Writer A --+
                |                    |
  [G1] Given ---+                    +--> [C1] Union --> [I1] Integrate --> [R1] Retire --> [T1]
                |                    |
                +--> [W2] Writer B --+
  ```
Scenario: disjoint writers compose and integrate
Given [G1] isolated worktrees
When [W1] I edit writer_a disjoint files
And [W2] I edit writer_b disjoint files
And [C1] I compose the exact union
And [I1] I integrate the composed candidate
And [R1] I retire temporary branches
Then [T1] exact union is reviewed
'''


def separate_parallel_data():
    data = parallel_data()
    ids = {re.search(r'\[([^]]+)\]', line).group(1): i for i, line in enumerate(
        GRAPH_PARALLEL.splitlines(), 1) if line.startswith(('Given', 'When', 'And', 'Then'))}
    role_nodes = {'writer_a': 'W1', 'writer_b': 'W2', 'exact_union': 'C1',
                  'integration': 'I1', 'retirement': 'R1'}
    for effect in data['requested_effects']:
        effect['requested_by_step'] = ids[role_nodes[effect['stage_id']]]
    return data


def test_r3_separate_gherkin_steps_show_semantic_parallelism_and_keep_ids():
    result = compile_contract(GRAPH_PARALLEL, yaml.safe_dump(separate_parallel_data()))
    assert result.compiler_result == 'COMPILED_CONFORMING_CANDIDATE', result.receipt.get('diagnostics')
    visual = result.receipt['workflow_visualization']
    source_edges = {(e['source'], e['target']) for e in visual['source_graph']['connectors']}
    assert {('G1', 'W1'), ('G1', 'W2'), ('W1', 'C1'), ('W2', 'C1'), ('C1', 'I1')} <= source_edges
    generated_edges = {(e['source'], e['target']) for e in visual['generated_graph']['connectors']}
    assert ('derived_common_validation', 'I1') in generated_edges
    assert ('W1', 'W2') not in generated_edges
    mapping = {m['node']: m for m in visual['execution_mapping']}
    assert mapping['W1']['stage_id'] == 'writer_a'
    assert mapping['W2']['stage_id'] == 'writer_b'
    assert mapping['C1']['stage_id'] == 'exact_union'
    assert mapping['I1']['stage_id'] == 'integration'


def test_r3_source_geometry_cannot_serialize_independent_writers():
    feature = GRAPH_PARALLEL.replace('[W2] Writer B --+', '[W1] Writer B --+')
    result = compile_contract(feature, yaml.safe_dump(separate_parallel_data()))
    assert result.compiler_result == 'WORKFLOW_GRAPH_INCONSISTENT'
    assert not result.prompt


def test_r3_q04_explicitly_invalidated_writer_is_regenerated_only():
    data = q04_data()
    data = _replace_literal(data, 'writer_a', 'writer_swap')
    data = _replace_literal(data, 'writer_b', 'writer_a')
    data = _replace_literal(data, 'writer_swap', 'writer_b')
    data['worker_contract']['writers'].sort(key=lambda worker: worker['stage_id'])
    result = run(PARALLEL, data)
    assert result.compiler_result == 'COMPILED_CONFORMING_CANDIDATE', result.receipt.get('diagnostics')
    ids = [s['stage_id'] for s in prompt_yaml(result)['workflow_stages']]
    assert 'writer_b' in ids and 'writer_a' not in ids
    assert result.receipt['reused_accepted_effects'] == ['writer_a', 'commit_writer_a']
    visual = result.receipt['workflow_visualization']
    reused = next(m for m in visual['execution_mapping'] if m['node'] == 'derived_writer_a')
    assert reused['role'] == 'reused_portable_result' and reused['effect'] is False


def test_r3_missing_vocabulary_extractor_is_gap_not_normative_boundary(monkeypatch):
    monkeypatch.setattr(compiler, '_closed_values', lambda field_name, contents: set())
    data = base_data()
    data['prompt']['dirty_worktree_policy'] = 'require_clean_worktree'
    result = run(data=data)
    assert result.compiler_result == 'IMPLEMENTATION_GAP'
    assert result.receipt['unsupported_construct']['current_architecture_boundary']['classification'] == 'implementation_gap'


LIFECYCLE = """Feature: exact carrier lifecycle
Scenario: preserve and retire
Given the exact task-owned clean unlocked worktree and ref are bound
When I preserve the portable result and evidence
And I remove the exact clean linked worktree
And I read back path and registration absence
And I delete the exact temporary ref using its old OID
Then the worktree and ref are absent and canonical master is unchanged
"""


def lifecycle_data():
    data = base_data()
    orchestrated(data)
    data["stages"] = []
    scope = {"TOP26006_fw": {"worktree_paths": ["/workspace/probe"],
                              "local_refs": ["refs/heads/probe"]}}
    data["prompt"]["allowed_to_modify"] = scope
    data["prompt"]["workflow_effect_envelope"] = {"allowed_to_modify": scope, "local_branch_deletion": True}
    data["lifecycle_contract"] = {
        "repository": "TOP26006_fw", "repository_path": "/workspace/repo",
        "worktree": "/workspace/probe", "ref": "refs/heads/probe",
        "head": "a" * 40, "base_oid": "a" * 40, "ownership": "task_owned",
        "state_required": {"tracked_clean": True, "index_clean": True, "conflict_free": True,
                           "untracked_empty": True, "ignored_empty": True, "unlocked": True},
        "state_source": "exact live readback required before removal",
        "preservation": ["result", "compiler receipt", "semantic review", "carrier identity"],
        "controller_branch": "controller", "automatic_retry": False}
    data["requested_effects"] = []
    for eid, kind, target, line, role in [
            ("remove", "worktree_remove", "/workspace/probe", 5, "remove_worktree"),
            ("delete", "delete_local_branch", "refs/heads/probe", 7, "delete_ref")]:
        data["bindings"].append({**data["bindings"][0], "binding_id": eid,
            "authorizes_effect": True, "effect": kind, "target": target})
        data["requested_effects"].append({"effect_id": eid, "effect": kind, "target": target,
            "requested_by_step": line, "positive_authority_binding": eid, "stage_id": role})
    return data


def test_exact_worktree_retirement_is_distinct_and_ordered():
    result = run(LIFECYCLE, lifecycle_data())
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE", result.receipt.get("diagnostics")
    stages = prompt_yaml(result)["workflow_stages"]
    assert [s["stage_id"] for s in stages] == ["preserve", "remove_worktree", "inspect", "delete_ref"]
    assert stages[1]["safety_critical_argv"] == ["git", "-C", "/workspace/repo", "worktree", "remove", "/workspace/probe"]
    assert stages[-1]["safety_critical_argv"] == ["git", "-C", "/workspace/repo", "update-ref", "-d", "refs/heads/probe", "stage:delete_ref:pre_delete_ref_oid"]
    assert stages[2]["required_readback"]["no_worktree_attached_to"] == "refs/heads/probe"
    assert "stage:inspect:readback" in stages[-1]["stage_inputs"]
    assert stages[1]["automatic_retry"] is False and stages[-1]["automatic_retry"] is False
    assert stages[0]["stage_effect_permissions"] == stages[2]["stage_effect_permissions"] == {}
    assert result.receipt["traceability"]["complete"]
    assert result.receipt["workflow_visualization"]["consistency"]


@pytest.mark.parametrize("field", ["tracked_clean", "index_clean", "conflict_free", "untracked_empty", "ignored_empty", "unlocked"])
def test_dirty_or_locked_retirement_cannot_relax_preconditions(field):
    data = lifecycle_data(); data["lifecycle_contract"]["state_required"][field] = False
    result = run(LIFECYCLE, data)
    assert not result.prompt and result.compiler_result == "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE"


@pytest.mark.parametrize("damage", ["missing_path", "foreign", "alias", "missing_preservation", "missing_effect", "wrong_owner", "pooled"])
def test_lifecycle_underbound_or_unauthorized_fails(damage):
    data = lifecycle_data()
    if damage == "missing_path": del data["lifecycle_contract"]["worktree"]
    elif damage == "foreign": data["lifecycle_contract"]["ownership"] = "foreign"
    elif damage == "alias": data["lifecycle_contract"]["worktree"] = "/workspace/repo"
    elif damage == "missing_preservation": data["lifecycle_contract"]["preservation"] = []
    elif damage == "missing_effect": data["requested_effects"].pop(0)
    elif damage == "wrong_owner": next(b for b in data["bindings"] if b["binding_id"] == "remove")["target"] = "/other"
    else: data["prompt"]["workflow_effect_envelope"] = {"allowed_to_modify": {}}
    result = run(LIFECYCLE, data)
    assert not result.prompt and not result.receipt.get("authorized_effects")


def test_lifecycle_readback_cannot_be_skipped_or_plan_corrupted(monkeypatch):
    data = lifecycle_data()
    feature = LIFECYCLE.replace("And I read back path and registration absence\n", "")
    data["requested_effects"][-1]["requested_by_step"] -= 1
    assert not run(feature, data).prompt
    original = compiler._plan_stages
    def corrupt(*args):
        stages = original(*args)
        stages[1]["safety_critical_argv"].insert(-1, "--force")
        return stages
    monkeypatch.setattr(compiler, "_plan_stages", corrupt)
    result = run(LIFECYCLE, lifecycle_data())
    assert not result.prompt and result.compiler_result == "COMPILER_INVARIANT_FAILURE"


def test_worktree_create_and_branch_creation_need_separate_effects():
    data = lifecycle_data()
    data["requested_effects"] = [{"effect_id": "create", "effect": "worktree_create", "target": "/workspace/probe",
        "requested_by_step": 4, "positive_authority_binding": "create", "stage_id": "create_worktree"}]
    data["bindings"].append({**data["bindings"][0], "binding_id": "create", "authorizes_effect": True,
                             "effect": "worktree_create", "target": "/workspace/probe"})
    intent = compiler.parse_gherkin("Feature: create\nScenario: exact\nGiven bound target\nWhen I create the exact isolated worktree\nThen the report cites evidence", "test")
    with pytest.raises(compiler.Compile_error, match="independent path/ref"):
        compiler._plan_ordered(data, intent, compiler._effects(data, intent))
    data["requested_effects"].append({"effect_id": "branch", "effect": "local_git_ref_write", "target": "refs/heads/probe",
        "requested_by_step": 4, "positive_authority_binding": "branch", "stage_id": "create_worktree"})
    stages = compiler._plan_ordered(data, intent, compiler._effects(data, intent))
    assert stages[0]["safety_critical_argv"] == ["git", "-C", "/workspace/repo", "worktree", "add", "-b", "probe", "/workspace/probe", "refs/heads/controller"]
    assert stages[0]["stage_branch_policy"] == "create_feature_branch_from_reference"
    assert stages[0]["feature_branch"] == "probe"
    assert stages[0]["reference_branch"] == "controller"
    assert "refs/heads/probe" in stages[0]["must_be_absent"]
    assert stages[0]["stage_effect_permissions"]["allowed_to_modify"]["TOP26006_fw"]["local_refs"] == ["refs/heads/probe"]


def test_uncommitted_writer_freezes_postimages_with_controller_closure():
    data = parallel_subset_data(True)
    data["requested_effects"] = [e for e in data["requested_effects"] if e["effect_id"] not in {"commit_writer_a", "commit_writer_b"}]
    feature = PARALLEL.replace("writers edit, integrate, and retire branches", "writers edit")
    result = run(feature, data)
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE", result.receipt.get("diagnostics")
    stages = prompt_yaml(result)["workflow_stages"]
    for worker in stages[:2]:
        assert worker["stage_outputs"] == ["frozen_postimages"]
        assert worker["deferred_commit_stage"] == "exact_union"
        area = worker["stage_effect_permissions"]["allowed_to_modify"]["TOP26006_fw"]
        assert set(area) == {"tracked_paths"}
    assert "stage:writer_a:frozen_postimages" in stages[3]["stage_inputs"]
    data["requested_effects"] = [e for e in data["requested_effects"] if e["effect_id"] != "commit_controller"]
    assert not run(feature, data).prompt


def dependent_data(outcome="failed_before_effect"):
    data = multi_repo_advancement_data()
    data["multi_repository_state"] = "PARTIALLY_INTEGRATED"
    state = {"candidate_heads": {"topcoffea": "c" * 40, "topeft": "d" * 40},
             "target_heads": {"topcoffea": "c" * 40, "topeft": "b" * 40},
             "completed_stages": ["provider_candidate", "consumer_candidate", "independent_review", "pair_validation", "integrate_topcoffea"],
             "review_evidence": "accepted_pair_review", "validation_evidence": "accepted_tuple_validation",
             "consumer_outcome": outcome, "readback_authority_binding": "readback_consumer"}
    data["accepted_effect_state"] = state
    data["continuation"] = {"prior_artifact_identity": "accepted_partial_tuple", "accepted_closure_layers": ["test_closure"],
        "accepted_prior_evidence": [state], "invalidation_boundary": ["integrate_topeft"],
        "delta_scope": ["readback", "integrate_topeft"], "unresolved_checks_only": ["readback"],
        "checks_not_to_repeat": state["completed_stages"]}
    bind_relation(data, "continuation.accepted_effect_state", state, "topcoffea", "accepted_evidence")
    data["bindings"][-1]["source_identity"] = "accepted_partial_tuple"
    data["bindings"].append({**data["bindings"][0], "binding_id": "readback_consumer", "validity_scope": "topeft"})
    if outcome == "OUTCOME_UNKNOWN":
        data["requested_effects"] = [e for e in data["requested_effects"] if e["stage_id"] != "integrate_topeft"]
        data["prompt"]["patch_kind_expected"] = "empty_no_changes"
    else:
        data["prompt"]["patch_kind_expected"] = "empty_no_changes"
    return data


def test_exact_dependent_continuation_preserves_provider_and_tuple():
    result = run(MULTI_REPO.replace("write candidates", "write candidates and integrate"), dependent_data())
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE", result.receipt.get("diagnostics")
    stages = prompt_yaml(result)["workflow_stages"]
    assert [s["stage_id"] for s in stages] == ["readback", "integrate_topeft"]
    assert result.receipt["authorized_effects"] == ["advance_topeft"]
    assert stages[-1]["expected_source_head"] == "d" * 40
    assert stages[-1]["expected_target_head"] == "stage:readback:observed_target_head"
    assert "provider_candidate" not in [s["stage_id"] for s in stages]
    assert "create_one_prompt_local_commit" not in str(stages)


def test_unknown_dependent_effect_is_readback_only():
    result = run(MULTI_REPO.replace("write candidates", "write candidates and integrate"), dependent_data("OUTCOME_UNKNOWN"))
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE", result.receipt.get("diagnostics")
    assert result.receipt["authorized_effects"] == []
    assert [s["stage_id"] for s in prompt_yaml(result)["workflow_stages"]] == ["readback"]
    assert result.receipt["workflow_visualization"]["consistency"]


@pytest.mark.parametrize("damage", ["tuple", "rollback", "retry", "protection"])
def test_partial_state_evidence_or_safety_mismatch_fails(damage):
    data = deepcopy(dependent_data())
    if damage == "tuple": data["accepted_effect_state"] = {**data["accepted_effect_state"], "validation_evidence": "unbound"}
    elif damage == "rollback": data["automatic_rollback"] = True
    elif damage == "retry": data["automatic_retry"] = True
    else: data["continuation"]["checks_not_to_repeat"] = []
    result = run(MULTI_REPO.replace("write candidates", "write candidates and integrate"), data)
    assert not result.prompt


def test_small_deterministic_edit_with_static_check_remains_simple():
    feature, data = documentation_data()
    data["deterministic_edit"] = {"path": "docs/a.md", "preimage_file_sha256": "a" * 64,
        "preimage_excerpt": "old", "replacement": "established", "literal_count": 1,
        "established_semantics_source": "accepted contract"}
    feature = feature.replace("Then docs/a.md is validated", "And I run ordinary focused static validation\nThen the generated prompt remains minimum-sufficient and non-orchestrated\nAnd no worker, worktree, join, controller or multi-stage workflow is invented")
    result = run(feature, data)
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE", result.receipt.get("diagnostics")
    assert "workflow_stages" not in prompt_yaml(result)
    assert prompt_yaml(result)["deterministic_edit"]["path"] == "docs/a.md"



def test_committed_result_identity_flows_into_terminal_worktree_retirement():
    """Retirement must consume the new result, not the pre-commit carrier HEAD.

    This is a synthetic abstraction regression, not a historical input supplement
    or authorization to execute any generated action.
    """
    data = lifecycle_data()
    data["lifecycle_contract"]["head"] = "stage:edit:observed_commit_head"
    data["prompt"]["patch_kind_expected"] = "prompt_local"
    scope = data["prompt"]["allowed_to_modify"]["TOP26006_fw"]
    scope["tracked_paths"] = ["docs/change.md"]
    scope["git_index_entries"] = ["docs/change.md"]
    data["requested_effects"] = []
    for eid, kind, target, line, role in [
            ("edit", "tracked_write", "docs/change.md", 4, "edit"),
            ("commit", "local_git_ref_write", "refs/heads/probe", 4, "edit"),
            ("remove", "worktree_remove", "/workspace/probe", 6, "remove_worktree"),
            ("delete", "delete_local_branch", "refs/heads/probe", 8, "delete_ref")]:
        data["bindings"] = [b for b in data["bindings"] if b["binding_id"] != eid]
        data["bindings"].append({**data["bindings"][0], "binding_id": eid, "authorizes_effect": True,
                                 "effect": kind, "target": target})
        data["requested_effects"].append({"effect_id": eid, "effect": kind, "target": target,
            "requested_by_step": line, "positive_authority_binding": eid, "stage_id": role})
    data["ordered_action_bindings"] = {"s4": {
        "paths": ["docs/change.md"], "branch": "probe",
        "reviewed_postimages": {"docs/change.md": {"sha256": "e" * 64, "locator": "accepted/postimages/change.md"}}, "review_evidence": "accepted exact staged review"}}
    feature = """Feature: result identity across lifecycle
Scenario: one committed result then terminal retirement
Given the exact clean task-owned carrier and reviewed replacement are bound
When I edit the exact reviewed documentation path and commit once
And I preserve the portable result and evidence
And I remove the exact clean linked worktree
And I read back path and registration absence
And I delete the exact temporary ref using its old OID
Then the worktree and ref are absent and canonical master is unchanged
"""
    result = run(feature, data)
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE", result.receipt.get("diagnostics")
    stages = prompt_yaml(result)["workflow_stages"]
    terminal = stages[-1]
    assert terminal["expected_old_oid"] == "stage:edit:observed_commit_head"
    assert "stage:edit:observed_commit_head" in str(terminal["stage_inputs"])
    assert "a" * 40 not in str(terminal["safety_critical_argv"])


@pytest.mark.parametrize("head", [None, "a" * 40, "b" * 40, "stage:nonexistent:future_oid"])
def test_r4_retirement_has_no_authored_oid_prerequisite(head):
    data = lifecycle_data()
    data["lifecycle_contract"].pop("base_oid")
    data["lifecycle_contract"].pop("head")
    if head is not None:
        data["lifecycle_contract"]["head"] = head
    result = run(LIFECYCLE, data)
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE", result.receipt.get("diagnostics")
    terminal = prompt_yaml(result)["workflow_stages"][-1]
    observation = terminal["runtime_observations"][0]
    assert observation["argv"] == ["git", "-C", "/workspace/repo", "rev-parse", "--verify", "refs/heads/probe"]
    assert observation["require_full_oid"] and observation["require_exit_zero"]
    assert terminal["safety_critical_argv"][-1] == observation["output"]
    assert observation["reject_movement_after_readback"]
    assert "no refreshed lease" in observation["on_mismatch"]
    assert not terminal["automatic_retry"]


@pytest.mark.parametrize("shape", ["parallel", "pair"])
def test_r4_carrier_observations_can_be_absent_without_adopting_foreign_resources(shape):
    data = parallel_data() if shape == "parallel" else multi_repo_data()
    feature = PARALLEL if shape == "parallel" else MULTI_REPO
    if shape == "parallel":
        for worker in data["worker_contract"]["writers"]:
            worker.pop("observed_head"); worker.pop("base_oid")
        data["worker_contract"].pop("composition_base_oid")
        data["retirement"].pop("exact_old_oid")
        data["retirement"].pop("expected_preserved_head")
    else:
        for repo in data["repositories"].values():
            for key in ("base", "candidate_head", "candidate_base_oid"):
                repo.pop(key)
    result = run(feature, data)
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE", result.receipt.get("diagnostics")
    assert result.receipt["traceability"]["complete"]


def test_r4_integration_keeps_reviewed_source_and_fresh_target_safety():
    result = run(MULTI_REPO.replace("write candidates", "write candidates and integrate"), multi_repo_advancement_data())
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE", result.receipt.get("diagnostics")
    for stage in prompt_yaml(result)["workflow_stages"]:
        if stage["stage_mode"] == "integration_only":
            guard = stage["must_pass_before_effects"]
            assert guard["source_head"].startswith("stage:")
            assert guard["fresh_target_readback"][-1] == guard["target_ref"]
            assert guard["require_fast_forward_ancestry"] and guard["reject_movement_after_readback"]


def test_r4_stage_result_is_derived_without_future_head_input():
    # Existing mandatory regression remains byte-for-byte intact above.
    import inspect
    original = inspect.getsource(test_committed_result_identity_flows_into_terminal_worktree_retirement)
    variant = original.replace('def test_committed_result_identity_flows_into_terminal_worktree_retirement():',
                               'def without_future_input():').replace(
        'data["lifecycle_contract"]["head"] = "stage:edit:observed_commit_head"',
        'data["lifecycle_contract"].pop("head")')
    namespace = dict(globals())
    exec(variant, namespace)
    namespace["without_future_input"]()


def test_r4_ambiguous_commit_without_historical_base_still_requires_readback():
    data = base_data()
    area = {"git_index_entries": ["docs/change.md"], "local_refs": ["refs/heads/task"],
            "git_effects": ["create_one_prompt_local_commit"]}
    data["prompt"].update(prompt_mode="commit_preparation", branch_policy="continue_existing_branch",
        target_branch="task", authorized_commit_scope={"TOP26006_fw": ["docs/change.md"]},
        allowed_to_modify={"TOP26006_fw": area},
        heavy_command_permissions={"allowed_to_modify": {"TOP26006_fw": area}})
    data.update(outcome_unknown=True, readback_before_retry=True, automatic_retry=False,
                readback_authority_binding="owner_task")
    data["commit_contract"] = {"repository": "TOP26006_fw", "worktree": "/workspace",
        "ref": "refs/heads/task", "index_paths": ["docs/change.md"],
        "index_identity": "reviewed exact task index", "recovery_authorized": False}
    data["bindings"].append({**data["bindings"][0], "binding_id": "commit", "authorizes_effect": True,
        "effect": "local_git_ref_write", "target": "refs/heads/task"})
    data["requested_effects"] = [{"effect_id": "commit", "effect": "local_git_ref_write",
        "target": "refs/heads/task", "requested_by_step": 4, "positive_authority_binding": "commit"}]
    feature = ("Feature: ambiguous commit\nScenario: exact effect\nGiven the task index is bound\n"
        "When I create one local commit\nAnd the commit command returns an ambiguous terminal outcome\n"
        "Then I read back the exact branch ref, HEAD and index before any retry\n"
        "And no new effect is allowed without explicit idempotence or recovery authority\n")
    result = run(feature, data)
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE", result.receipt.get("diagnostics")
    contract = prompt_yaml(result)["ambiguous_effect_contract"]
    assert contract["recorded_base_oid"] is None
    assert contract["readback_argv"][0][-1] == "refs/heads/task"
    assert contract["automatic_retry"] is False
    data["automatic_retry"] = True
    assert not run(feature, data).prompt


def worktree_paths(porcelain):
    """Compare full normalized worktree records, never path substrings."""
    return {str(Path(line.removeprefix("worktree ")).resolve())
            for line in porcelain.splitlines() if line.startswith("worktree ")}


def ref_names(output):
    return set(output.splitlines())


def test_exact_fixture_path_and_ref_membership_with_shared_prefix(tmp_path):
    removed = tmp_path / "alpha"
    surviving = tmp_path / "alpha_repo"
    porcelain = f"worktree {surviving}\nHEAD {'a' * 40}\nbranch refs/heads/alpha_repo\n\n"
    assert str(removed) in porcelain  # Demonstrate why the historical assertion was false.
    assert str(removed.resolve()) not in worktree_paths(porcelain)
    assert worktree_paths(porcelain) == {str(surviving.resolve())}
    assert "refs/heads/alpha" not in ref_names("refs/heads/alpha_repo\n")
    assert ref_names("refs/heads/alpha\nrefs/heads/alpha_repo\n") == {
        "refs/heads/alpha", "refs/heads/alpha_repo"}


def test_empirical_worktree_retirement_and_compare_delete(tmp_path):
    """Execute compiler lifecycle argv only in a disposable, test-owned repository."""
    import json
    import subprocess

    repository = tmp_path / "repository"
    worktree = tmp_path / "probe"
    repository.mkdir()
    transcript = []
    receipt = tmp_path / "lifecycle_receipt.json"

    def execute(argv, expected=0):
        result = subprocess.run(argv, capture_output=True, text=True)
        transcript.append({"argv": argv, "returncode": result.returncode,
                           "stdout": result.stdout, "stderr": result.stderr})
        receipt.write_text(json.dumps(transcript, indent=2))
        assert result.returncode == expected, transcript[-1]
        return result.stdout.strip()

    def git(*args, expected=0):
        return execute(["git", "-C", str(repository), *args], expected)

    git("init", "--initial-branch=controller")
    git("-c", "user.name=Lifecycle Fixture", "-c", "user.email=fixture@example.invalid",
        "commit", "--allow-empty", "-m", "Initialize disposable lifecycle fixture")
    controller_head = git("rev-parse", "HEAD")
    data = _replace_literal(lifecycle_data(), "/workspace/repo", str(repository))
    data = _replace_literal(data, "/workspace/probe", str(worktree))
    data["prompt"]["workspace_root"] = str(repository)
    data["prompt"]["repo_locations"]["TOP26006_fw"] = str(repository)
    data["lifecycle_contract"].pop("head")
    data["lifecycle_contract"].pop("base_oid")

    creation = deepcopy(data)
    creation["requested_effects"] = []
    for eid, effect, target in [
            ("create", "worktree_create", str(worktree)),
            ("branch", "local_git_ref_write", "refs/heads/probe")]:
        creation["bindings"].append({**creation["bindings"][0], "binding_id": eid,
                                     "authorizes_effect": True, "effect": effect,
                                     "target": target})
        creation["requested_effects"].append({
            "effect_id": eid, "effect": effect, "target": target,
            "requested_by_step": 4, "positive_authority_binding": eid,
            "stage_id": "create_worktree"})
    intent = compiler.parse_gherkin(
        "Feature: create\nScenario: exact\nGiven bound target\n"
        "When I create the exact isolated worktree\nThen the report cites evidence", "test")
    stage = compiler._plan_ordered(
        creation, intent, compiler._effects(creation, intent))[0]
    assert stage["stage_branch_policy"] == "create_feature_branch_from_reference"
    assert stage["feature_branch"] == "probe" and stage["reference_branch"] == "controller"
    assert stage["safety_critical_argv"] == [
        "git", "-C", str(repository), "worktree", "add", "-b", "probe",
        str(worktree), "refs/heads/controller"]
    assert not worktree.exists()
    git("show-ref", "--verify", "--quiet", "refs/heads/probe", expected=1)
    execute(stage["safety_critical_argv"])
    result = run(LIFECYCLE, data)
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE", result.receipt
    (tmp_path / "generated_prompt.md").write_text(result.prompt)
    stages = prompt_yaml(result)["workflow_stages"]
    removal, inspection, deletion = stages[1:]
    assert removal["stage_branch_policy"] == "continue_existing_branch"
    assert removal["target_branch"] == deletion["target_branch"] == "controller"
    assert git("symbolic-ref", "--short", "HEAD") == "controller"
    assert execute(["git", "-C", str(worktree), "symbolic-ref", "HEAD"]) == "refs/heads/probe"
    assert execute(["git", "-C", str(worktree), "status", "--porcelain",
                    "--untracked-files=all", "--ignored"]) == ""
    registrations = git("worktree", "list", "--porcelain")
    assert str(worktree.resolve()) in worktree_paths(registrations) and "locked" not in registrations
    assert execute(["git", "-C", str(worktree), "rev-parse", "HEAD"]) == controller_head
    # Preserve and reopen receipts before the destructive lifecycle operations.
    assert json.loads(receipt.read_text()) == transcript
    assert (tmp_path / "generated_prompt.md").read_text() == result.prompt
    assert removal["safety_critical_argv"] == [
        "git", "-C", str(repository), "worktree", "remove", str(worktree)]
    execute(removal["safety_critical_argv"])
    assert not worktree.exists()
    registrations = git("worktree", "list", "--porcelain")
    assert str(worktree.resolve()) not in worktree_paths(registrations)
    assert worktree_paths(registrations) == {str(repository.resolve())}
    assert inspection["required_readback"]["path_absent"] == str(worktree)
    observation = deletion["runtime_observations"][0]
    assert observation["reject_movement_after_readback"]
    old_oid = execute(observation["argv"])
    assert re.fullmatch(r"[0-9a-f]{40}", old_oid)
    argv = deletion["safety_critical_argv"]
    assert argv[-1] == observation["output"]
    assert argv[:-1] == ["git", "-C", str(repository), "update-ref", "-d", "refs/heads/probe"]
    execute([*argv[:-1], old_oid])
    git("show-ref", "--verify", "--quiet", "refs/heads/probe", expected=1)
    assert git("rev-parse", "HEAD") == controller_head
    assert git("status", "--porcelain", "--untracked-files=all") == ""
    assert json.loads(receipt.read_text()) == transcript


def synthetic_artifact(path, content):
    """Synthetic task input owns these UTF-8 bytes; compilation only projects them."""
    import hashlib
    return {'path': path, 'sha256': hashlib.sha256(content.encode('utf-8')).hexdigest(),
            'source': {'kind': 'synthetic_literal', 'content': content},
            'review_evidence': 'exact reviewed synthetic replacement'}


def ordered_resource_fixture():
    """Input builder: temporary resources have no permanent-advancement effects."""
    data = base_data()
    orchestrated(data)
    data['stages'] = []
    data['prompt'].update(delegation_policy='required', patch_kind_expected='prompt_local',
                          validation_ceiling='targeted_unit_test')
    data['repositories'] = {'topcoffea': {}, 'topeft': {}}
    data['prompt']['repo_locations'] = {'topcoffea': '/workspace/alpha_repo', 'topeft': '/workspace/beta_repo'}
    data['prompt']['read_only'] = {'topcoffea': ['refs/heads/tc/dev-live'], 'topeft': ['refs/heads/te/datacard_sr_reco']}
    resources = {}
    for name, repo, branch, anchor in [('alpha','topcoffea','tc/fixture','tc/dev-live'),
                                       ('beta','topeft','te/fixture','te/datacard_sr_reco')]:
        life = deepcopy(lifecycle_data()['lifecycle_contract'])
        life.update(repository=repo, repository_path='/workspace/'+name+'_repo',
                    worktree='/workspace/'+name, ref='refs/heads/'+branch,
                    reference_ref='refs/heads/'+anchor, controller_branch=anchor)
        life.pop('head'); life.pop('base_oid')
        resources[name] = life
        bind_relation(data, 'lifecycle_resources.'+name+'.carrier',
                      {k:life[k] for k in ('repository','repository_path','worktree','ref','reference_ref')}, repo)
    data['lifecycle_resources'] = resources
    # Semantic sequence is independent of alphabetical resource order.
    rows = [
        ('create_worktree','I create the alpha worktree','alpha'),
        ('create_worktree_2','I create the beta worktree','beta'),
        ('edit','I edit the alpha baseline and commit','alpha'),
        ('edit_2','I edit the beta baseline and commit','beta'),
        ('edit_3','I edit the beta candidate and commit','beta'),
        ('static_validation','I run static validation of the partial tuple','beta'),
        ('edit_4','I edit the alpha candidate for later commit','alpha'),
        ('inspect','I review the staged alpha candidate independently','alpha'),
        ('commit','I create one alpha commit','alpha'),
        ('inspect_2','I read back the ambiguous alpha effect','alpha'),
        ('static_validation_2','I run static validation of four exact tuples','alpha'),
        ('inspect_3','I review the integrated evidence independently','alpha'),
        ('preserve','I preserve alpha portable evidence','alpha'),
        ('preserve_2','I preserve beta portable evidence','beta'),
        ('remove_worktree','I remove the alpha worktree','alpha'),
        ('inspect_4','I read back alpha path and registration absence','alpha'),
        ('delete_ref','I delete the alpha temporary ref','alpha'),
        ('remove_worktree_2','I remove the beta worktree','beta'),
        ('inspect_5','I read back beta path and registration absence','beta'),
        ('delete_ref_2','I delete the beta temporary ref','beta'),
    ]
    # Authoritative synthetic task inputs, serialized into the generated contract.
    fixture_content = {
        'edit': '{"contract": "sample", "protocol": 1}\n',
        'edit_2': '{"accepts": [1], "contract": "sample"}\n',
        'edit_3': '{"accepts": [1, 2], "contract": "sample"}\n',
        'edit_4': '{"contract": "sample", "protocol": 2}\n'}
    data['ordered_action_bindings'] = {}
    data['requested_effects'] = []
    scope = {repo:{'tracked_paths':['contract.json'], 'local_refs':[life['ref']],
                   'worktree_paths':[life['worktree']]} for repo,life in
             ((v['repository'],v) for v in resources.values())}
    data['prompt']['allowed_to_modify'] = scope
    data['prompt']['workflow_effect_envelope'] = {'allowed_to_modify':scope,'local_branch_deletion':True}
    for index,(stage_id,text,name) in enumerate(rows,4):
        life=resources[name]; repo=life['repository']; context={'resource':name}
        data['ordered_action_bindings']['s'+str(index)]=context
        if stage_id in {'inspect','inspect_3'}: context['independent_review']=True
        effects=[]
        if stage_id.startswith('create_worktree'):
            effects=[('worktree_create',life['worktree']),('local_git_ref_write',life['ref'])]
        elif stage_id.startswith('edit'):
            context.update(paths=['contract.json'],branch=life['ref'].removeprefix('refs/heads/'),
                           reviewed_postimages={'contract.json': synthetic_artifact('contract.json', fixture_content[stage_id])},
                           review_evidence='exact reviewed synthetic replacement')
            effects=[('tracked_write','contract.json')]
            if stage_id=='edit_4': context['deferred_commit_stage']='commit'
            else: effects.append(('local_git_ref_write',life['ref']))
        elif stage_id=='commit':
            context.update(review_evidence='stage:inspect:readback',ambiguous_outcome=True,
                           readback_before_retry=True,automatic_retry=False)
            effects=[('local_git_ref_write',life['ref'])]
        elif stage_id.startswith('static_validation'):
            pairs = [('edit', 'edit_3', 'PASS')]
            if stage_id.endswith('_2'):
                pairs = [('edit', 'edit_2', 'PASS'), ('edit', 'edit_3', 'PASS'),
                         ('inspect_2', 'edit_2', 'FAIL_EXPECTED'), ('inspect_2', 'edit_3', 'PASS')]
            cases = [{'provider': 'stage:'+a+':observed_commit_head',
                      'consumer': 'stage:'+b+':observed_commit_head', 'expected': outcome}
                     for a,b,outcome in pairs]
            context.update(evidence_locator='synthetic contract: equal contract and protocol in accepts',
                           result_inputs=sorted({row[key] for row in cases for key in ('provider','consumer')}),
                           validation_contract={'predicate':'contract equality and protocol membership',
                             'cases':cases, 'matrix':[row['expected'] for row in cases]})
        elif stage_id.startswith('remove_worktree'): effects=[('worktree_remove',life['worktree'])]
        elif stage_id.startswith('delete_ref'): effects=[('delete_local_branch',life['ref'])]
        for n,(kind,target) in enumerate(effects):
            eid=stage_id+'_'+str(n)
            data['bindings'].append({**data['bindings'][0], 'binding_id':eid, 'validity_scope':repo,
                                     'authorizes_effect':True,'effect':kind,'target':target})
            data['requested_effects'].append({'effect_id':eid,'effect':kind,'target':target,
                'requested_by_step':index,'positive_authority_binding':eid,'stage_id':stage_id})
    feature='Feature: explicitly ordered temporary resources\nScenario: candidate transitions\nGiven task-owned resources are bound\n'
    feature+='\n'.join(('When ' if i==0 else 'And ')+row[1] for i,row in enumerate(rows))
    return feature+'\nThen the report cites evidence\n',data


def test_ordered_resources_preserve_declared_order_and_ambiguous_readback(tmp_path):
    feature,data=ordered_resource_fixture()
    result=run(feature,data)
    assert result.compiler_result=='COMPILED_CONFORMING_CANDIDATE',result.receipt
    prompt=prompt_yaml(result); stages=prompt['workflow_stages']; ids=[s['stage_id'] for s in stages]
    assert ids.index('edit_3') < ids.index('edit_4') < ids.index('commit') < ids.index('inspect_2')
    commit=next(s for s in stages if s['stage_id']=='commit')
    assert commit['ambiguous_effect_contract']['initial_result']=='OUTCOME_UNKNOWN'
    readback=next(s for s in stages if s['stage_id']=='inspect_2')
    assert readback['required_readback']['unknown_blocks_downstream']
    assert not readback['required_readback']['automatic_retry']
    assert all(s['stage_mode']!='integration_only' for s in stages)
    for stage in stages:
        grants=str(stage['stage_effect_permissions'])
        assert 'refs/heads/tc/dev-live' not in grants
        assert 'refs/heads/te/datacard_sr_reco' not in grants
    (tmp_path/'generated_ordered_prompt.md').write_text(result.prompt)
    assert result.receipt['traceability']['complete']


@pytest.mark.parametrize('fault',['missing_create','pooled','duplicate','blind_retry','missing_readback','permanent_target'])
def test_ordered_resource_authority_counterexamples(fault):
    feature,data=ordered_resource_fixture()
    if fault=='missing_create': data['bindings'][next(i for i,b in enumerate(data['bindings']) if b['binding_id']=='create_worktree_0')]['authorizes_effect']=False
    elif fault=='pooled': next(b for b in data['bindings'] if b['binding_id']=='create_worktree_0')['validity_scope']='topeft'
    elif fault=='duplicate': data['lifecycle_resources']['beta']['worktree']=data['lifecycle_resources']['alpha']['worktree']
    elif fault=='blind_retry': data['ordered_action_bindings']['s12']['automatic_retry']=True
    elif fault=='missing_readback': feature=feature.replace('I read back the ambiguous alpha effect','I preserve alpha evidence prematurely')
    else: data['ordered_action_bindings']['s6']['branch']='tc/dev-live'
    assert not run(feature,data).prompt


def composed_resource_fixture():
    data=parallel_data()
    data.pop('retirement');data.pop('common_validation_contract')
    data['requested_effects']=[e for e in data['requested_effects'] if e['stage_id'] not in {'integration','retirement'}]
    data['prompt']['workflow_effect_envelope'].pop('local_branch_deletion')
    data['lifecycle_resources']={}
    data['ordered_action_bindings']={}
    # Existing controller is separate from the two newly created worker resources.
    for i,worker in enumerate(data['worker_contract']['writers']):
        name='alpha' if i==0 else 'beta'; stage_id='create_worktree'+('_2' if i else '')
        life=deepcopy(lifecycle_data()['lifecycle_contract'])
        life.update(repository_path=data['prompt']['repo_locations']['TOP26006_fw'],worktree=worker['worktree_path'],ref='refs/heads/'+worker['branch'],reference_ref='refs/heads/controller')
        life.pop('head');life.pop('base_oid')
        data['lifecycle_resources'][name]=life
        data['ordered_action_bindings']['s'+str(4+i)]={'resource':name}
        bind_relation(data,'lifecycle_resources.'+name+'.carrier',
                      {k:life[k] for k in ('repository','repository_path','worktree','ref','reference_ref')},'TOP26006_fw')
        for n,(kind,target) in enumerate([('worktree_create',life['worktree']),('local_git_ref_write',life['ref'])]):
            eid=stage_id+'_'+str(n)
            data['bindings'].append({**data['bindings'][0],'binding_id':eid,'authorizes_effect':True,'effect':kind,'target':target})
            data['requested_effects'].append({'effect_id':eid,'effect':kind,'target':target,'requested_by_step':4+i,
                                            'positive_authority_binding':eid,'stage_id':stage_id})
        data['prompt']['allowed_to_modify']['TOP26006_fw'].append(life['worktree'])
        data['prompt']['workflow_effect_envelope']['allowed_to_modify']['TOP26006_fw'].append(life['worktree'])
    for effect in data['requested_effects']:
        if effect['stage_id'] in {'writer_a','writer_b','exact_union'}: effect['requested_by_step']=6
    feature='Feature: composed resources\nScenario: isolated parallel body\nGiven isolated worktrees\nWhen I create the alpha worktree\nAnd I create the beta worktree\nAnd writers edit\nThen exact union is reviewed'
    return feature,data


def test_lifecycle_prelude_feeds_parallel_body(tmp_path):
    feature,data=composed_resource_fixture();result=run(feature,data)
    assert result.compiler_result=='COMPILED_CONFORMING_CANDIDATE',result.receipt
    stages=prompt_yaml(result)['workflow_stages']; ids=[s['stage_id'] for s in stages]
    assert ids[:4]==['create_worktree','create_worktree_2','writer_a','writer_b']
    for writer in stages[2:4]: assert 'stage:create_worktree_2:readback' in writer['stage_inputs']
    assert all('worktree_paths' not in s['stage_effect_permissions'].get('allowed_to_modify',{}).get('TOP26006_fw',{}) for s in stages[2:])
    (tmp_path/'generated_composed_prompt.md').write_text(result.prompt)
    assert result.receipt['traceability']['complete']


@pytest.mark.parametrize('fault',['missing','foreign','duplicate'])
def test_composed_creation_grants_are_independent(fault):
    feature,data=composed_resource_fixture()
    if fault=='missing': next(b for b in data['bindings'] if b['binding_id']=='create_worktree_0')['authorizes_effect']=False
    elif fault=='foreign': data['lifecycle_resources']['alpha']['worktree']='/workspace/foreign'
    else: data['lifecycle_resources']['beta']['worktree']=data['lifecycle_resources']['alpha']['worktree']
    assert not run(feature,data).prompt


def test_portable_accepted_writer_needs_no_commit_identity():
    data=q04_data(); accepted=data['continuation']['accepted_prior_evidence'][0]
    accepted.pop('observed_commit_head')
    accepted['frozen_postimages']={'docs/writer_b.md':{'sha256':'e'*64,'locator':'accepted/postimages/writer_b.md'}}
    _binding(data,'q04.accepted_writer_result')['observed_state']['value']=deepcopy(accepted)
    result=run(PARALLEL,data)
    assert result.compiler_result=='COMPILED_CONFORMING_CANDIDATE',result.receipt
    stages=prompt_yaml(result)['workflow_stages']
    assert 'writer_b' not in [s['stage_id'] for s in stages]
    assert 'prior:accepted-009-r1:writer_b@frozen_postimages' in next(s for s in stages if s['stage_id']=='exact_union')['stage_inputs']
    assert 'frozen_postimages' in result.prompt


def test_empirical_ordered_resource_partial_state_and_cleanup(tmp_path):
    import json
    import subprocess
    feature,data=ordered_resource_fixture()
    data=_replace_literal(data,'/workspace',str(tmp_path))
    transcript=[]; outputs={}; initial={}
    def execute(argv):
        completed=subprocess.run(argv,text=True,capture_output=True)
        transcript.append({'argv':argv,'returncode':completed.returncode,'stdout':completed.stdout,'stderr':completed.stderr})
        (tmp_path/'generic_lifecycle_receipt.json').write_text(json.dumps(transcript,indent=2))
        assert completed.returncode==0,transcript[-1]
        return completed.stdout.strip()
    def git(path,*args): return execute(['git','-C',str(path),*args])
    for life in data['lifecycle_resources'].values():
        repository=Path(life['repository_path']);repository.mkdir()
        git(repository,'init','--initial-branch='+life['controller_branch'])
        git(repository,'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','--allow-empty','-m','Initialize fixture')
        initial[life['repository']]=git(repository,'rev-parse','HEAD')
    result=run(feature,data)
    assert result.compiler_result=='COMPILED_CONFORMING_CANDIDATE',result.receipt
    (tmp_path/'generated_empirical_prompt.md').write_text(result.prompt)
    frozen={}; partial=None; artifacts={}; conformance=[]
    from tools.governance_workflow_ir import Artifact_spec
    for stage in prompt_yaml(result)['workflow_stages']:
        sid=stage['stage_id']; path=Path(stage['working_directory'])
        if stage['stage_goal']=='worktree_create': execute(stage['safety_critical_argv'])
        elif stage['stage_goal']=='edit':
            records=next(row['exact_reviewed_postimages'] for row in stage['stage_inputs']
                         if isinstance(row,dict) and 'exact_reviewed_postimages' in row)
            record=records['contract.json']
            artifact=Artifact_spec.from_record('contract.json',record,record['review_evidence'])
            artifacts[sid]=artifact
            (path/artifact.path).write_bytes(artifact.literal_bytes())
            artifact.verify_bytes((path/artifact.path).read_bytes())
            git(path,'add','--','contract.json')
            frozen[sid]=git(path,'write-tree')
            if not stage.get('deferred_commit_stage'):
                git(path,'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-m','Update synthetic contract')
                outputs[sid]=git(path,'rev-parse','HEAD')
            if sid=='edit_3':
                alpha=Path(data['lifecycle_resources']['alpha']['worktree'])
                partial=(git(alpha,'rev-parse','HEAD'),outputs[sid])
                assert partial==(outputs['edit'],outputs['edit_3'])
        elif sid=='commit':
            assert git(path,'write-tree')==frozen['edit_4']
            before=git(path,'rev-parse','HEAD')
            # Intentionally discard the commit process result. Resolution uses only fresh Git state.
            subprocess.run(['git','-C',str(path),'-c','user.name=Fixture','-c','user.email=fixture@example.invalid',
                            'commit','-m','Update staged synthetic contract'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            transcript.append({'effect':'commit','classification':'OUTCOME_UNKNOWN','attempt_count':1})
            outputs['pre_attempt']=before
        elif sid=='inspect_2':
            observed=git(path,'rev-parse','HEAD')
            assert git(path,'rev-parse','HEAD^')==outputs['pre_attempt']
            assert git(path,'rev-parse','HEAD^{tree}')==frozen['edit_4']
            assert not git(path,'status','--porcelain')
            outputs['commit']=observed
            outputs['inspect_2']=observed
            transcript.append({'classification':'effect_happened','retry_count':0})
        elif sid=='static_validation_2':
            def content(resource,oid):
                return json.loads(git(data['lifecycle_resources'][resource]['repository_path'],'show',oid+':contract.json'))
            # Compare exact Git blob bytes before interpreting the tuple predicate.
            import hashlib
            for edit_id,resource_id,result_id in [('edit','alpha','edit'),('edit_2','beta','edit_2'),
                                                   ('edit_3','beta','edit_3'),('edit_4','alpha','inspect_2')]:
                artifact=artifacts[edit_id]; oid=outputs[result_id]
                body=subprocess.check_output(['git','-C',data['lifecycle_resources'][resource_id]['repository_path'],
                                              'show',oid+':'+artifact.path])
                artifact.verify_bytes(body)
                assert body==artifact.literal_bytes()
                conformance.append({'stage':edit_id,'commit':oid,'artifact':artifact.projection(),
                                    'actual_sha256':hashlib.sha256(body).hexdigest(),'content':body.decode()})
            (tmp_path/'h4_empirical_postimage_conformance.json').write_text(json.dumps(conformance,indent=2))
            assert len(json.loads((tmp_path/'h4_empirical_postimage_conformance.json').read_text()))==4
            relation=stage['validation_contract']
            from tools.governance_workflow_ir import Result_ref
            def resolve(value):
                return outputs[Result_ref.parse(value).stage_id]
            pairs=[(resolve(row['provider']),resolve(row['consumer'])) for row in relation['cases']]
            observed=[]
            for a,b in pairs:
                left,right=content('alpha',a),content('beta',b)
                observed.append(left['contract']==right['contract'] and left['protocol'] in right['accepts'])
            assert observed==[row['expected']=='PASS' for row in relation['cases']]
            (tmp_path/'portable_results.json').write_text(json.dumps({'outputs':outputs,'pairs':pairs,'results':observed,'artifacts':{sid:a.projection() for sid,a in artifacts.items()},'conformance':conformance},indent=2))
            assert json.loads((tmp_path/'portable_results.json').read_text())['results']==observed
        elif stage['stage_goal']=='worktree_remove':
            assert (tmp_path/'portable_results.json').is_file()
            assert not git(path,'status','--porcelain','--untracked-files=all','--ignored')
            execute(stage['safety_critical_argv']);assert not path.exists()
        elif stage['stage_goal']=='delete_ref':
            observation=stage['runtime_observations'][0]
            old=execute(observation['argv']);argv=stage['safety_critical_argv']
            execute([*argv[:-1],old])
    for life in data['lifecycle_resources'].values():
        assert not Path(life['worktree']).exists()
        assert str(Path(life['worktree']).resolve()) not in worktree_paths(
            git(life['repository_path'],'worktree','list','--porcelain'))
        assert worktree_paths(git(life['repository_path'],'worktree','list','--porcelain')) == {
            str(Path(life['repository_path']).resolve())}
        assert life['ref'] not in ref_names(git(life['repository_path'],'for-each-ref','--format=%(refname)'))
        assert git(life['repository_path'],'rev-parse','HEAD')==initial[life['repository']]
    (tmp_path/'generic_lifecycle_receipt.json').write_text(json.dumps(transcript,indent=2))
    assert json.loads((tmp_path/'generic_lifecycle_receipt.json').read_text())==transcript


def composed_retirement_fixture():
    feature,data=composed_resource_fixture()
    lines=feature.splitlines(); tail=lines.pop()
    for i,(name,resource) in enumerate(data['lifecycle_resources'].items()):
        suffix='_2' if i else ''
        for kind,text in [('preserve','I preserve portable result evidence'),
                          ('remove_worktree','I remove the exact worktree'),
                          ('inspect','I read back path and registration absence'),
                          ('delete_ref','I delete the exact temporary ref')]:
            line=len(lines)+1;lines.append('And '+text)
            data['ordered_action_bindings']['s'+str(line)]={'resource':name}
            if kind not in {'remove_worktree','delete_ref'}:continue
            effect='worktree_remove' if kind=='remove_worktree' else 'delete_local_branch'
            target=resource['worktree'] if kind=='remove_worktree' else resource['ref']
            eid=kind+suffix
            data['bindings'].append({**data['bindings'][0],'binding_id':eid,'authorizes_effect':True,'effect':effect,'target':target})
            data['requested_effects'].append({'effect_id':eid,'effect':effect,'target':target,'requested_by_step':line,
                                            'positive_authority_binding':eid,'stage_id':eid})
    data['prompt']['workflow_effect_envelope']['local_branch_deletion']=True
    return '\n'.join([*lines,tail]),data


def test_composed_epilogue_waits_for_reviewed_body():
    feature,data=composed_retirement_fixture();result=run(feature,data)
    assert result.compiler_result=='COMPILED_CONFORMING_CANDIDATE',result.receipt
    stages=prompt_yaml(result)['workflow_stages'];ids=[s['stage_id'] for s in stages]
    assert ids.index('reconciled_review') < ids.index('preserve') < ids.index('remove_worktree') < ids.index('delete_ref')
    assert any('stage:reconciled_review:' in str(x) for x in next(s for s in stages if s['stage_id']=='preserve')['stage_inputs'])
    assert ids[-1]=='delete_ref_2'


def test_empirical_composed_creation_parallel_results_join_retirement(tmp_path):
    import subprocess,json
    feature,data=composed_retirement_fixture();data=_replace_literal(data,'/workspace',str(tmp_path))
    repository=tmp_path; transcript=[]
    def execute(argv):
        r=subprocess.run(argv,capture_output=True,text=True)
        transcript.append({'argv':argv,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
        assert r.returncode==0,transcript[-1]
        return r.stdout.strip()
    def git(path,*args):return execute(['git','-C',str(path),*args])
    git(repository,'init','--initial-branch=controller')
    git(repository,'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','--allow-empty','-m','Initialize fixture')
    initial=git(repository,'rev-parse','HEAD')
    composition=Path(data['worker_contract']['composition_worktree_path'])
    git(repository,'worktree','add','-b','controller_candidate',str(composition),'HEAD')
    result=run(feature,data)
    assert result.compiler_result=='COMPILED_CONFORMING_CANDIDATE',result.receipt
    (tmp_path/'generated_parallel_prompt.md').write_text(result.prompt)
    frozen={}
    for stage in prompt_yaml(result)['workflow_stages']:
        sid=stage['stage_id']
        if stage.get('stage_goal')=='worktree_create':execute(stage['safety_critical_argv'])
        elif sid in {'writer_a','writer_b'}:
            worker=next(w for w in data['worker_contract']['writers'] if w['stage_id']==sid)
            path=Path(worker['worktree_path']);rel=worker['write_paths'][0]
            (path/rel).parent.mkdir(parents=True,exist_ok=True);(path/rel).write_text(sid+' owned content\n')
            frozen[rel]=(path/rel).read_bytes()
            git(path,'add','--',rel)
            git(path,'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-m','Write isolated result')
        elif sid=='exact_union':
            assert len(frozen)==2
            for rel,content in frozen.items():
                target=composition/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(content)
            assert all((composition/rel).read_bytes()==content for rel,content in frozen.items())
            git(composition,'add','--',*frozen)
            git(composition,'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-m','Compose reviewed results')
            (tmp_path/'portable_union.json').write_text(json.dumps({p:hashlib.sha256(b).hexdigest() for p,b in frozen.items()}))
            assert json.loads((tmp_path/'portable_union.json').read_text())=={p:hashlib.sha256(b).hexdigest() for p,b in frozen.items()}
        elif stage.get('stage_goal')=='worktree_remove':
            assert (tmp_path/'portable_union.json').exists();execute(stage['safety_critical_argv'])
        elif stage.get('stage_goal')=='delete_ref':
            oid=execute(stage['runtime_observations'][0]['argv'])
            execute([*stage['safety_critical_argv'][:-1],oid])
    # The explicitly pre-existing test controller is also fixture-owned.
    oid=git(composition,'rev-parse','HEAD')
    git(repository,'worktree','remove',str(composition))
    git(repository,'update-ref','-d','refs/heads/controller_candidate',oid)
    assert git(repository,'rev-parse','HEAD')==initial
    assert ref_names(git(repository,'for-each-ref','--format=%(refname)')) == {'refs/heads/controller'}
    assert worktree_paths(git(repository,'worktree','list','--porcelain')) == {str(repository.resolve())}
    (tmp_path/'composed_lifecycle_receipt.json').write_text(json.dumps(transcript,indent=2))
    assert json.loads((tmp_path/'composed_lifecycle_receipt.json').read_text())==transcript


def separate_composed_fixture(retirement=False):
    feature, data = composed_retirement_fixture() if retirement else composed_resource_fixture()
    feature = feature.replace("And writers edit", "And I edit writer_a disjoint files\n"
                              "And I write writer_b disjoint files\nAnd I compose the exact union")
    for effect in data['requested_effects']:
        role = effect['stage_id']
        if role in {'writer_a', 'writer_b', 'exact_union'}:
            effect['requested_by_step'] = {'writer_a': 6, 'writer_b': 7, 'exact_union': 8}[role]
        elif effect['requested_by_step'] > 6:
            effect['requested_by_step'] += 2
    data['ordered_action_bindings'] = {
        's' + str(int(key[1:]) + (2 if int(key[1:]) > 6 else 0)): value
        for key, value in data['ordered_action_bindings'].items()}
    feature, bindings = fixture_graph(feature, yaml.safe_dump(data))
    # Literal independent oracle: prelude -> fork -> join -> ordered tail.
    final = len(feature.splitlines()) - 3
    edges = [('s3', 's4'), ('s4', 's5'), ('s5', 's6'), ('s5', 's7'),
             ('s6', 's8'), ('s7', 's8')]
    edges += [('s' + str(i), 's' + str(i + 1)) for i in range(8, final)]
    lines = feature.splitlines()
    lines[2] = '  ' + '    '.join(f'[{a}] --> [{b}]' for a, b in edges)
    return '\n'.join(lines), yaml.safe_load(bindings)


@pytest.mark.parametrize('retirement', [False, True])
def test_typed_partition_separate_composition_and_epilogue(retirement, tmp_path):
    feature, data = separate_composed_fixture(retirement)
    result = run(feature, data)
    assert result.compiler_result == 'COMPILED_CONFORMING_CANDIDATE', result.receipt
    stages = prompt_yaml(result)['workflow_stages']
    assert [s['stage_id'] for s in stages[:4]] == [
        'create_worktree', 'create_worktree_2', 'writer_a', 'writer_b']
    partition = result.receipt['semantic_partition']
    assignments = {row['semantic_id']: row for row in partition['assignments']}
    assert assignments['s6']['domain'] == assignments['s7']['domain'] == 'parallel_worker_or_join'
    assert assignments['s4']['resource'] == 'alpha'
    assert assignments['s5']['resource'] == 'beta'
    assert assignments['s6']['owners'] == ('writer_a',)
    visual = result.receipt['workflow_visualization']
    mapping = {m['node']: m for m in visual['execution_mapping']}
    for node, role in [('s4', 'create_worktree'), ('s5', 'create_worktree_2'),
                       ('s6', 'writer_a'), ('s7', 'writer_b'), ('s8', 'exact_union')]:
        assert mapping[node]['stage_id'] == role
        assert mapping[node]['semantic_steps'] == [node]
    edges = {(e['source'], e['target']) for e in visual['generated_graph']['connectors']}
    assert ('s6', 's7') not in edges and ('s7', 's6') not in edges
    assert {('s5', 's6'), ('s5', 's7'), ('s6', 'derived_independent_review'),
            ('s7', 'derived_independent_review'), ('derived_independent_review', 's8')} <= edges
    if retirement:
        preserve = next(s for s in stages if s['stage_id'] == 'preserve')
        assert 'stage:reconciled_review:reconciled_review_evidence' in preserve['stage_inputs']
        assert ('derived_reconciled_review', 's9') in edges
    assert result.receipt['traceability']['complete']
    assert set(visual['generated_graph']['nodes']) == set(mapping)
    (tmp_path / 'generated_prompt.md').write_text(result.prompt)
    (tmp_path / 'partition_receipt.yaml').write_text(yaml.safe_dump(result.receipt))


def test_typed_partition_explicit_ordered_edit_keeps_resource(tmp_path):
    feature, data = ordered_resource_fixture()
    feature = feature.replace('I edit the alpha baseline and commit', 'I edit writer_a disjoint files')
    result = run(feature, data)
    assert result.compiler_result == 'COMPILED_CONFORMING_CANDIDATE', result.receipt
    row = next(r for r in result.receipt['semantic_partition']['assignments'] if r['semantic_id'] == 's6')
    assert row['domain'] == 'ordered_lifecycle' and row['resource'] == 'alpha'
    assert row['owners'] == ('edit',)
    assert not result.receipt['semantic_partition']['parallel_roles']
    (tmp_path / 'generated_prompt.md').write_text(result.prompt)


@pytest.mark.parametrize('fault', ['contradictory', 'wrong_worker', 'unknown'])
def test_typed_partition_rejects_ambiguous_or_unclassified_actions(fault):
    feature, data = separate_composed_fixture()
    if fault == 'contradictory':
        data['ordered_action_bindings']['s6'] = {'resource': 'alpha'}
    elif fault == 'wrong_worker':
        next(e for e in data['requested_effects'] if e['stage_id'] == 'writer_a')['stage_id'] = 'writer_b'
    else:
        feature = feature.replace('I edit writer_a disjoint files', 'I invent an unclassified operation')
    result = run(feature, data)
    assert not result.prompt
    assert result.compiler_result == ('IMPLEMENTATION_GAP' if fault == 'unknown' else
                                      'NOT_READY_MISSING_AUTHORITY_BINDING')
    if fault == 'contradictory':
        assert 'contradictory typed ownership' in str(result.receipt['diagnostics'])


@pytest.mark.parametrize('case,expected', [
    ('A', 'NOT_READY_NEW_DECISION_BOUNDARY'),
    ('B', 'COMPILER_INVARIANT_FAILURE'),
    ('C', 'NOT_READY_MISSING_AUTHORITY_BINDING'),
    ('D', 'COMPILED_CONFORMING_CANDIDATE'),
    ('E', 'COMPILED_CONFORMING_CANDIDATE'),
    ('F', 'NOT_READY_MISSING_AUTHORITY_BINDING'),
])
def test_aggregate_diagnostic_precedence_matrix(case, expected, tmp_path):
    feature, data = PARALLEL, parallel_data()
    if case in {'A', 'B'}:
        feature = feature.replace('writers edit, integrate, and retire branches',
                                  'writers edit and retire branches')
        if case == 'B':
            data.pop('common_validation_contract')
    elif case in {'C', 'E', 'F'}:
        feature, data = separate_composed_fixture()
        if case == 'C':
            next(e for e in data['requested_effects'] if e['stage_id'] == 'writer_a')['stage_id'] = 'writer_b'
        elif case == 'F':
            data['ordered_action_bindings']['s6'] = {'resource': 'alpha'}
    result = run(feature, data)
    (tmp_path / 'diagnostic_receipt.yaml').write_text(yaml.safe_dump(result.receipt))
    (tmp_path / 'generated_prompt.md').write_text(result.prompt)
    assert result.compiler_result == expected, result.receipt
    if case in {'A', 'B', 'C', 'F'}:
        assert result.prompt == ''
        assert result.receipt['authorized_effects'] == []
    if case == 'F':
        assert 'contradictory typed ownership' in str(result.receipt['diagnostics'])
