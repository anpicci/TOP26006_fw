"""Focused D8-E implementation checks; retrospective H1-H6 oracle review is D8-F."""

import hashlib
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
    return compile_contract(feature, yaml.safe_dump(base_data() if data is None else data), "inline-case")


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
    data["bindings"].append({
        "binding_id": "relation_" + str(len(data["bindings"])),
        "claim": identity_path, "materiality": "IDENTITY_CRITICAL",
        "source_kind": source_kind, "source_identity": "readback:" + identity_path,
        "acquisition": "acquired", "validity_scope": repo_id,
        "observed_state": {"identity_path": identity_path, "value": value},
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
    return data


def test_q03_parallel_work_is_explicitly_staged_and_isolated():
    data = parallel_data()
    result = run(PARALLEL, data)
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    assert result.receipt["selected_execution_shape"] == "orchestrated_workflow"
    stages = yaml.safe_load(result.prompt.split("```yaml\n", 1)[1].split("\n```", 1)[0])["workflow_stages"]
    assert [s["stage_id"] for s in stages] == ["writer_a", "writer_b", "independent_review",
                                                 "exact_union", "reconciled_review", "integration", "retirement"]
    assert stages[2]["stage_effect_permissions"] == stages[4]["stage_effect_permissions"] == {}
    assert stages[3]["stage_effect_permissions"] != {}
    assert stages[0]["stage_effect_permissions"] != stages[1]["stage_effect_permissions"]
    assert set(result.receipt["authorized_effects"]) == {
        "writer_a", "writer_b", "commit_writer_a", "commit_writer_b", "compose_writer_a",
        "compose_writer_b", "commit_controller", "integrate", "retire"}
    assert result.receipt["safety_constraints"]["worker_contract"]["union_paths"] == [
        "docs/writer_a.md", "docs/writer_b.md"]


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


def test_q05_multi_repository_candidate_tuple_and_local_authority():
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
    assert result.compiler_result == "UNSUPPORTED_CANONICAL_CONSTRUCT" and result.prompt == ""
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
    assert result.receipt["diagnostics"][0]["line"] == 3


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
    feature = "Feature: campaign\n@production\nScenario: run\nGiven inputs are known\nWhen I run production\nThen output exists"
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
    feature = "Feature: ref\nScenario: contradiction\nGiven reference branch master remains unchanged\nWhen I move reference branch master\nThen success"
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
    assert result.compiler_result == "UNSUPPORTED_CANONICAL_CONSTRUCT"
    assert result.receipt["manual_fallback"] == "independently_evaluable_under_canonical_governance"
    assert result.receipt["dispatchability"]["dispatchable"] is False


def test_n1_syntax_tag_cannot_create_authority():
    result = run("Feature: publish\n@production\nScenario: now\nGiven publication is authorized\nWhen I publish\nThen it exists")
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
    feature = "Feature: science\nScenario: choice\nGiven two mappings exist\nWhen I choose a mapping\nThen result is ready"
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


def test_historical_h1_h6_inputs_are_declared_but_unevaluated():
    result = run()
    assert set(result.receipt["historical_case_readiness"]) == set(HISTORICAL_CASES)
    assert all(item["state"] == "NOT_EVALUATED" for item in result.receipt["historical_case_readiness"].values())
    assert "H6" in result.receipt["historical_case_readiness"]


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
    feature = "Feature: policy\nScenario: unknown\nGiven a scope\nWhen I arbitrate database ownership\nThen the answer is recorded"
    result = run(feature)
    assert result.compiler_result == "UNSUPPORTED_CANONICAL_CONSTRUCT" and result.prompt == ""


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
    assert result.prompt == "" and result.compiler_result == "UNSUPPORTED_CANONICAL_CONSTRUCT"


def test_e2_unparseable_registry_module_fails_closed(monkeypatch, tmp_path):
    module = tmp_path / "governance/modules/topeft.md"
    module.parent.mkdir(parents=True)
    module.write_text("native policy is required\npermanent_live_development_branch: te/dev\n")
    monkeypatch.setattr(compiler, "ROOT", tmp_path)
    data = base_data()
    data["repositories"] = {"topeft": {}}
    data["prompt"]["repo_locations"] = {"topeft": "/workspace/topeft"}
    result = run(data=data)
    assert result.prompt == "" and result.compiler_result == "UNSUPPORTED_CANONICAL_CONSTRUCT"


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
    assert result.compiler_result == "UNSUPPORTED_CANONICAL_CONSTRUCT"
    assert result.prompt == ""
    assert result.receipt["dispatchability"]["dispatchable"] is False
    assert "integration" in result.receipt["diagnostics"][0]["message"]


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
    assert {"source": "assertion:5:1", "output": "gate:exact_union",
            "relation": "requires_concrete_gate"} in edges


def test_e3_common_validation_requires_supplied_exact_contract():
    feature = PARALLEL.replace("Then exact union is reviewed",
                               "Then exact union is reviewed and common validation passes")
    missing = run(feature, parallel_data())
    assert missing.compiler_result == "UNSUPPORTED_CANONICAL_CONSTRUCT" and missing.prompt == ""
    data = parallel_data()
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
    assert {"source": "assertion:5:2", "output": "gate:common_validation",
            "relation": "requires_concrete_gate"} in result.receipt["traceability"]["edges"]


def test_e3_unknown_material_assertion_fails_closed():
    feature = PARALLEL.replace("Then exact union is reviewed",
                               "Then exact union is reviewed and unknown condition holds")
    result = run(feature, parallel_data())
    assert result.compiler_result == "UNSUPPORTED_CANONICAL_CONSTRUCT"
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
    assert result.compiler_result == "UNSUPPORTED_CANONICAL_CONSTRUCT" and result.prompt == ""


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
    assert result.compiler_result == "UNSUPPORTED_CANONICAL_CONSTRUCT"
    assert result.prompt == ""
    assert any(term in result.receipt["diagnostics"][0]["message"] for term in
               ("delta planner", "Q04 invalidation/protection"))


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
    data["repositories"]["topcoffea"]["base"] = "d" * 40
    data["bindings"].extend([
        {**data["bindings"][0], "binding_id": "manual_review", "source_kind": "accepted_evidence"},
        {**data["bindings"][0], "binding_id": "live_applicability",
         "source_kind": "repository_readback", "observed_state": {"status": "live"}},
    ])
    data["dispatch_gate"] = {"owner_authorization_binding": "owner_task",
                             "manual_governance_review_binding": "manual_review",
                             "live_applicability_binding": "live_applicability"}
    result = run(MULTI_REPO, data)
    assert result.compiler_result == "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE"
    assert result.prompt == "" and result.receipt["dispatchability"]["dispatchable"] is False


def test_e3_exact_value_readback_positive_mismatch_and_oid_shape():
    data = parallel_data()
    assert run(PARALLEL, data).compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    path = "worker_contract.writers.writer_a.base_oid"
    bound = next(b for b in data["bindings"] if b.get("observed_state", {}).get("identity_path") == path)
    bound["observed_state"]["value"] = "f" * 40
    assert run(PARALLEL, data).compiler_result == "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE"
    data = multi_repo_data()
    assert run(MULTI_REPO, data).compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    data["repositories"]["topcoffea"]["base"] = "not-an-oid"
    assert run(MULTI_REPO, data).compiler_result == "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE"


def test_e3_source_identity_text_alone_cannot_bind_runtime_value():
    data = parallel_data()
    path = "worker_contract.writers.writer_a.observed_head"
    bound = next(b for b in data["bindings"] if b.get("observed_state", {}).get("identity_path") == path)
    bound["source_identity"] = path + "@" + "a" * 40
    del bound["observed_state"]
    result = run(PARALLEL, data)
    assert result.compiler_result == "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE"
    assert result.prompt == ""


def test_e3_retirement_ref_oid_relation_is_exact():
    data = parallel_data()
    bound = next(b for b in data["bindings"] if b["binding_id"] == "owned_temp_ref")
    bound["observed_state"]["value"]["exact_old_oid"] = "d" * 40
    result = run(PARALLEL, data)
    assert result.compiler_result == "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE"
    assert result.prompt == ""
    data = parallel_data()
    data["retirement"]["ownership_readback_binding"] = "owner_task"
    result = run(PARALLEL, data)
    assert result.compiler_result == "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE"
    assert result.prompt == ""


def test_b01_common_validation_caller_gate_and_unrelated_target_fail_closed():
    feature = PARALLEL.replace("Then exact union is reviewed",
                               "Then exact union is reviewed and common validation passes")
    data = q04_data()
    data["common_validation_contract"]["acceptance_gate"] = "continue even if test fails"
    assert run(feature, data).compiler_result == "UNSUPPORTED_CANONICAL_CONSTRUCT"
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
    assert run(feature, data).compiler_result == "UNSUPPORTED_CANONICAL_CONSTRUCT"
    data = q04_data()
    data["continuation"]["delta_scope"].append("writer_b")
    assert run(feature, data).compiler_result == "UNSUPPORTED_CANONICAL_CONSTRUCT"
    data = q04_data()
    data["bindings"] = [b for b in data["bindings"] if b.get("observed_state", {}).get("identity_path") !=
                        "q04.accepted_writer_result"]
    assert run(feature, data).compiler_result == "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE"


def test_q05_candidate_carrier_and_pair_contract_fail_closed():
    data = multi_repo_data()
    del data["repositories"]["topcoffea"]["candidate_branch"]
    assert run(MULTI_REPO, data).compiler_result == "UNSUPPORTED_CANONICAL_CONSTRUCT"
    data = multi_repo_data()
    data["repositories"]["topcoffea"]["candidate_branch"] = "wrong/candidate"
    assert run(MULTI_REPO, data).compiler_result == "UNSUPPORTED_CANONICAL_CONSTRUCT"
    data = multi_repo_data()
    data["pair_validation_contract"]["covers"] = ["provider"]
    assert run(MULTI_REPO, data).compiler_result == "UNSUPPORTED_CANONICAL_CONSTRUCT"
    data = multi_repo_data()
    data["bindings"] = [b for b in data["bindings"] if b.get("observed_state", {}).get("identity_path") !=
                        "pair_validation.candidate_tuple"]
    assert run(MULTI_REPO, data).compiler_result == "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE"
    data = multi_repo_data()
    data["repositories"]["topcoffea"]["candidate_branch"] = "tc/dev-live"
    assert run(MULTI_REPO, data).compiler_result == "UNSUPPORTED_CANONICAL_CONSTRUCT"


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
    assert run(PARALLEL, data).compiler_result == "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE"
    data = multi_repo_data()
    relation = next(b for b in data["bindings"] if b.get("observed_state", {}).get("identity_path") ==
                    "repositories.topcoffea.candidate_carrier")
    relation["observed_state"]["value"]["permanent_live_head"] = "f" * 40
    assert run(MULTI_REPO, data).compiler_result == "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE"


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
    assert result.compiler_result == "UNSUPPORTED_CANONICAL_CONSTRUCT"
    assert result.prompt == "" and result.receipt["partial_state"]["state"] == "PARTIAL"
    assert "rollback" not in str(result.receipt).lower()


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
    assert run(Q04_FEATURE, data).compiler_result == "UNSUPPORTED_CANONICAL_CONSTRUCT"


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
    assert run(MULTI_REPO, data).compiler_result == "UNSUPPORTED_CANONICAL_CONSTRUCT"


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
    baseline = compile_contract(MULTI_REPO, raw, "raw-map")
    result = compile_contract(MULTI_REPO, transformed, "raw-map")
    assert result.compiler_result == baseline.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    assert _plan(result) == _plan(baseline)
    assert result.receipt["safety_constraints"]["candidate_pair_order"] == ["topcoffea", "topeft"]
    data["candidate_pair_order"] = ["topeft", "topcoffea"]
    assert run(MULTI_REPO, data).compiler_result == "UNSUPPORTED_CANONICAL_CONSTRUCT"


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
    result = run(feature, data)
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE", result.receipt.get("diagnostics")
    assert "must_pass before effects commit_ref" in result.prompt
    assert result.receipt["given_readiness"][0]["state"] == "runtime_preflight"
    data["bindings"][-1]["runtime_preflight"] = ""
    missing = run(feature, data)
    assert missing.compiler_result == "NOT_READY_MISSING_DECISION_MATERIAL_EVIDENCE"
    assert missing.prompt and missing.receipt["excluded_effects"] == ["commit_ref"]
    assert missing.receipt["authorized_effects"] == ["effect_1"]
    assert missing.receipt["dispatchability"]["dispatchable"] is False
    data["bindings"][-1]["runtime_preflight"] = "verify HEAD_required"
    assert run(feature, data).receipt["excluded_effects"] == ["commit_ref"]
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
    feature = "Feature: remote publication\nScenario: publish\nGiven authority is bound\nWhen I push remote ref\nThen success\nBut no remote repository is modified"
    assert run(feature, data).compiler_result == "NOT_READY_NEW_DECISION_BOUNDARY"
    assert run(feature.replace("\nBut no remote repository is modified", ""), data).compiler_result == \
        "COMPILED_CONFORMING_CANDIDATE"


@pytest.mark.parametrize("unsafe", ["refs/heads/-oops;rm", "refs/heads/../../main",
                                           "refs/heads/temp.lock", "refs/heads/temp name"])
def test_f04_unsafe_retirement_ref_never_becomes_command(unsafe):
    data = _replace_literal(parallel_data(), "refs/heads/temp-worker", unsafe)
    result = run(PARALLEL, data)
    assert result.prompt == ""
    assert result.compiler_result in {"UNSUPPORTED_CANONICAL_CONSTRUCT",
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
        yaml.safe_dump(base_data()).encode()).hexdigest()
