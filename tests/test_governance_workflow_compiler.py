"""Focused D8-E implementation checks; retrospective H1-H6 oracle review is D8-F."""

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
MULTI_REPO = "Feature: provider consumer\nScenario: candidate pair\nGiven exact bases\nWhen provider and consumer write and integrate candidates\nThen the pair is validated"


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
    data["stages"] = [stage("provider_candidate"), stage("consumer_candidate"),
                      stage("pair_validation"), stage("integrate_provider"), stage("integrate_consumer")]
    data["repositories"] = {
        "topcoffea": {"base": "a", "candidate": "a1", "authority_binding": "repo_a",
                      "stage_id": "provider_candidate"},
        "topeft": {"base": "b", "candidate": "b1", "authority_binding": "repo_b",
                   "stage_id": "consumer_candidate"},
    }
    data["prompt"]["repo_locations"] = {"topcoffea": "/workspace/topcoffea",
                                         "topeft": "/workspace/topeft"}
    data["prompt"]["read_only"] = {"topcoffea": ["AGENTS.md"], "topeft": ["AGENTS.md"]}
    data["candidate_pair_order"] = ["topcoffea", "topeft"]
    data["candidate_pair_validation_stage"] = "pair_validation"
    data["integration_stages"] = ["integrate_provider", "integrate_consumer"]
    data["multi_repository_state"] = "NOT_STARTED"
    data["bindings"] += [{**data["bindings"][0], "binding_id": "repo_a", "validity_scope": "topcoffea"},
                         {**data["bindings"][0], "binding_id": "repo_b", "validity_scope": "topeft"}]
    for repo_id, stage_id, target in (("topcoffea", "provider_candidate", "topcoffea/file.py"),
                                      ("topeft", "consumer_candidate", "topeft/file.py")):
        item = next(s for s in data["stages"] if s["stage_id"] == stage_id)
        item.update(repository_id=repo_id, stage_mode="coding",
                    stage_branch_policy="create_feature_branch_from_reference", reference_branch="development",
                    feature_branch=f"feature/{repo_id}")
        item["stage_effect_permissions"] = {"allowed_to_modify": {repo_id: [target]}}
        data["bindings"].append({**data["bindings"][0], "binding_id": f"write_{repo_id}",
                                 "validity_scope": repo_id, "authorizes_effect": True,
                                 "effect": "tracked_write", "target": target})
        data.setdefault("requested_effects", []).append({"effect_id": f"write_{repo_id}",
            "effect": "tracked_write", "target": target, "requested_by_step": 4,
            "positive_authority_binding": f"write_{repo_id}", "stage_id": stage_id})
        integration_stage = "integrate_provider" if repo_id == "topcoffea" else "integrate_consumer"
        ref = f"refs/heads/{repo_id}_development"
        integration = next(s for s in data["stages"] if s["stage_id"] == integration_stage)
        integration.update(repository_id=repo_id, stage_mode="integration_only",
                           stage_branch_policy="continue_existing_branch",
                           target_branch=f"{repo_id}_development",
                           integration_source_branch=f"feature/{repo_id}",
                           integration_target_branch=f"{repo_id}_development",
                           integration_method="ff_only", expected_source_head=data["repositories"][repo_id]["candidate"])
        integration["stage_effect_permissions"] = {"allowed_to_modify": {repo_id: [ref]}}
        data["bindings"].append({**data["bindings"][0], "binding_id": f"integrate_{repo_id}_owner",
                                 "validity_scope": repo_id, "authorizes_effect": True,
                                 "effect": "local_git_ref_write", "target": ref})
        data["requested_effects"].append({"effect_id": f"integrate_{repo_id}",
            "effect": "local_git_ref_write", "target": ref, "requested_by_step": 4,
            "positive_authority_binding": f"integrate_{repo_id}_owner", "stage_id": integration_stage})
    data["prompt"]["workflow_effect_envelope"] = {"allowed_to_modify": {
        "topcoffea": ["topcoffea/file.py", "refs/heads/topcoffea_development"],
        "topeft": ["topeft/file.py", "refs/heads/topeft_development"]}}
    data["prompt"]["allowed_to_modify"] = data["prompt"]["workflow_effect_envelope"]["allowed_to_modify"]
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


def test_q02_bounded_documentation_mutation():
    data = base_data()
    data["prompt"].update(prompt_mode="documentation_only", branch_policy="create_feature_branch_from_reference",
                          reference_branch="master", feature_branch="docs/example",
                          validation_ceiling="targeted_unit_test", authorized_commit_scope={"TOP26006_fw": ["docs/a.md"]},
                          foreign_dirty_change_policy="preserve_and_exclude",
                          explicitly_adopted_inherited_changes="none", staging_policy="exact_path_only")
    data["prompt"]["allowed_to_modify"] = {"TOP26006_fw": {"tracked_paths": ["docs/a.md"]}}
    data["prompt"]["heavy_command_permissions"]["allowed_to_modify"] = {"TOP26006_fw": ["docs/a.md"]}
    feature = "Feature: document\nScenario: edit\nGiven semantics are established\nWhen I edit docs/a.md\nThen docs/a.md is validated"
    add_effect(data, "tracked_write", "docs/a.md", 4, "allowed_to_modify")
    result = run(feature, data)
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    assert result.receipt["selected_execution_shape"] == "simple_non_orchestrated"
    assert result.receipt["authorized_effects"] == ["effect_1"]
    assert "preserve_and_exclude" in result.prompt


def parallel_data():
    data = base_data()
    orchestrated(data)
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
        "docs/writer_a.md", "docs/writer_b.md", "refs/heads/master", "refs/heads/temp-worker"]},
        "local_branch_deletion": True}
    data["prompt"]["allowed_to_modify"] = {"TOP26006_fw": [
        "docs/writer_a.md", "docs/writer_b.md", "refs/heads/master", "refs/heads/temp-worker"]}
    data["retirement"] = {"exact_owned_surface": "refs/heads/temp-worker", "authority_binding": "owner_retire",
                          "preservation_evidence": "reviewed patch and exact postimages", "retention_satisfied": True,
                          "terminal_stage": "retirement", "cleanup_failure_invalidates_semantic_result": False}
    data["prompt"]["workflow_goal"] = "disjoint writer results with conditional reconciled review"
    data["prompt"]["workflow_stop_policy"] = "stop_on_failed_gate_or_new_decision_boundary"
    data["prompt"]["workflow_stage_ledger_path"] = "diagnostics/ledger.yml"
    data["worker_contract"] = {
        "writers": [{"stage_id": "writer_a", "write_paths": ["docs/writer_a.md"], "isolated_worktree": True},
                    {"stage_id": "writer_b", "write_paths": ["docs/writer_b.md"], "isolated_worktree": True}],
        "independent_review_stage": "independent_review", "review_independent_of_writers": True,
        "exact_union_stage": "exact_union", "union_paths": ["docs/writer_a.md", "docs/writer_b.md"],
        "conditional_reconciled_review_stage": "reconciled_review", "reconciled_review_if_rewritten": True,
        "worker_permanent_authority": False,
    }
    return data


def test_q03_parallel_work_is_explicitly_staged_and_isolated():
    data = parallel_data()
    result = run(PARALLEL, data)
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    assert result.receipt["selected_execution_shape"] == "orchestrated_workflow"
    stages = yaml.safe_load(result.prompt.split("```yaml\n", 1)[1].split("\n```", 1)[0])["workflow_stages"]
    assert [s["stage_id"] for s in stages] == ["writer_a", "writer_b", "independent_review",
                                                 "exact_union", "reconciled_review", "integration", "retirement"]
    assert all(s["stage_effect_permissions"] == {} for s in stages[2:5])
    assert stages[0]["stage_effect_permissions"] != stages[1]["stage_effect_permissions"]
    assert result.receipt["authorized_effects"] == ["writer_a", "writer_b", "integrate", "retire"]
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


def test_q05_multi_repository_candidate_tuple_and_local_authority():
    data = multi_repo_data()
    result = run(MULTI_REPO, data)
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    assert result.receipt["selected_execution_shape"] == "multi_repository_coordination"
    assert result.receipt["authorized_effects"] == ["write_topcoffea", "integrate_topcoffea",
                                                    "write_topeft", "integrate_topeft"]
    assert result.receipt["safety_constraints"]["candidate_pair_order"] == ["topcoffea", "topeft"]
    assert "global_git_transaction" not in result.prompt


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
    assert result.compiler_result == "COMPILED_CONFORMING_CANDIDATE"
    assert result.receipt["selected_execution_shape"] == "multi_repository_coordination"
    assert result.receipt["safety_constraints"]["partial_effects"]["integrated_repo_identity"] == "topcoffea@a1"
    assert "rollback" not in result.prompt.lower()


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
    data["stages"][0]["stage_effect_permissions"] = {}
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
