"""Standard-library tests for the correction-lib prompt contract validator."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from collections import OrderedDict
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = SKILL_ROOT.parents[2]
SCRIPT_PATH = SKILL_ROOT / "scripts/validate_prompt.py"
SCHEMA_PATH = SKILL_ROOT / "references/prompt_schema.json"
BINDING_PATH = SKILL_ROOT / "references/governance_binding.json"
VALID_MANIFEST = SKILL_ROOT / "tests/fixtures/valid/fixtures.json"
INVALID_MANIFEST = SKILL_ROOT / "tests/fixtures/invalid/fixtures.json"

SPEC = importlib.util.spec_from_file_location("prompt_contract_validator", SCRIPT_PATH)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = VALIDATOR
SPEC.loader.exec_module(VALIDATOR)


def render_value(lines: list[str], key: str, value: object, indent: int = 0) -> None:
    prefix = " " * indent
    if isinstance(value, dict):
        lines.append(f"{prefix}{key}:")
        for child_key, child_value in value.items():
            render_value(lines, child_key, child_value, indent + 2)
    elif isinstance(value, list):
        lines.append(f"{prefix}{key}:")
        for item in value:
            lines.append(f"{prefix}  - {item}")
    elif isinstance(value, str) and "\n" in value:
        lines.append(f"{prefix}{key}: |")
        for child_line in value.splitlines():
            lines.append(f"{prefix}  {child_line}")
    else:
        lines.append(f"{prefix}{key}: {value}")


def render_prompt(fields: OrderedDict[str, object]) -> bytes:
    lines = ["# Synthetic prompt", "", "## Metadata and governance", "", "```text"]
    for key, value in fields.items():
        render_value(lines, key, value)
    lines.append("```")
    return ("\n".join(lines) + "\n").encode("utf-8")


def base_fields(mode: str) -> OrderedDict[str, object]:
    read_only_modes = {
        "investigation_only",
        "validation_only",
        "pr_preparation",
        "pr_publication",
        "integration_only",
        "branch_maintenance_only",
    }
    fields: OrderedDict[str, object] = OrderedDict(
        [
            ("prompt_id", f"SYNTHETIC_{mode.upper()}"),
            ("short_title", f"synthetic_{mode}"),
            ("prompt_mode", mode),
            ("preferred_codex_model", "gpt-5.6-terra"),
            ("reasoning_level", "high"),
            ("delegation_policy", "forbidden"),
            ("model_selection_rationale", "bounded synthetic fixture"),
            ("workspace_root", "/users/apiccine/work/correction-lib"),
            (
                "repo_locations",
                {
                    "meta_repo": "/users/apiccine/work/correction-lib",
                    "topeft": "/users/apiccine/work/correction-lib/topeft",
                    "topcoffea": "/users/apiccine/work/correction-lib/topcoffea",
                },
            ),
            (
                "allowed_to_modify",
                {"diagnostics_only": "/tmp/correction_lib_synthetic"},
            ),
            (
                "read_only",
                {
                    "meta_repo": "governance and unrelated paths",
                    "topeft": "entire repository",
                    "topcoffea": "entire repository",
                },
            ),
            ("branch_policy", "read_only_current_branch"),
            ("current_checked_out_branch", "synthetic_current"),
            ("reference_branch", "none, read-only"),
            ("target_branch", "none, read-only"),
            ("feature_branch", "none, read-only"),
            ("current_baseline_branch", "synthetic_current"),
            ("comparison_baseline", "synthetic immutable baseline"),
            ("integrated_baseline_mode", "yes"),
            ("dirty_worktree_policy", "allow_declared_preexisting_changes"),
            ("preflight_profile", "compact_preflight"),
            ("preflight_scope_paths", ["/tmp/correction_lib_synthetic"]),
            ("validation_ceiling", "static_inspection_only"),
            (
                "heavy_command_permissions",
                {"defaults": "all_no", "overrides": "none"},
            ),
            ("source_control_policy", "inherit_AGENTS_defaults"),
            ("do_not_commit", "yes"),
            ("commit_expected", "no"),
            (
                "commit_message_policy",
                {
                    "format": "none",
                    "prompt_ids_allowed": "no",
                    "codex_jargon_allowed": "no",
                    "internal_workflow_labels_allowed": "no",
                },
            ),
            ("goal", "perform one bounded synthetic task"),
            (
                "decision_question",
                "does the synthetic evidence answer the bounded question?",
            ),
            ("out_of_scope", ["all real analysis and production"]),
            (
                "report_path",
                "/tmp/correction_lib_prompt_contract/synthetic_report.md",
            ),
            (
                "patch_path",
                "/tmp/correction_lib_prompt_contract/synthetic_diff.patch",
            ),
            ("patch_kind_expected", "empty_no_changes"),
            ("final_chat_deliverable", ["synthetic verdict"]),
        ]
    )
    if mode in {"coding", "documentation_only", "test_alignment_only"}:
        fields["allowed_to_modify"] = {"meta_repo": "/tmp/synthetic_tracked_file"}
        fields["branch_policy"] = "create_feature_branch_from_reference"
        fields["reference_branch"] = "synthetic_reference"
        fields["target_branch"] = "none, creating feature branch"
        fields["feature_branch"] = "synthetic_feature"
        fields["validation_ceiling"] = "targeted_unit_test"
        fields["do_not_commit"] = "no"
        fields["commit_expected"] = "yes"
        fields["patch_kind_expected"] = "prompt_local"
    if mode == "test_alignment_only":
        fields["runtime_intent_evidence"] = "synthetic accepted runtime contract"
    if mode == "commit_preparation":
        fields["allowed_to_modify"] = {"meta_repo": "/tmp/synthetic_existing_change"}
        fields["branch_policy"] = "commit_preparation_on_existing_branch"
        fields["reference_branch"] = "none, no branch creation"
        fields["target_branch"] = "synthetic_current"
        fields["feature_branch"] = "none, no branch creation"
        fields["do_not_commit"] = "no"
        fields["commit_expected"] = "yes"
        fields["patch_kind_expected"] = "prompt_local"
    if mode == "pr_publication":
        fields.update(
            {
                "publication_action": "create_or_reuse_open_pr_or_mr",
                "publication_platform": "github",
                "publication_repository": "synthetic/example",
                "publication_remote": "synthetic_remote",
                "publication_base_branch": "synthetic_base",
                "publication_feature_branch": "synthetic_feature",
                "expected_local_head": "0" * 40,
                "network_access": "yes",
                "remote_git_write": "yes",
                "pr_or_mr_write": "yes",
                "pr_or_mr_merge": "no",
                "remote_branch_deletion": "no",
                "duplicate_pr_or_mr_policy": "reuse_exact_open_match_else_create_one",
                "force_push_allowed": "no",
                "merge_allowed": "no",
                "draft_allowed": "no",
            }
        )
    if mode == "integration_only":
        fields.update(
            {
                "integration_source_branch": "synthetic_feature",
                "integration_target_branch": "synthetic_integration",
                "integration_method": "ff_only",
                "expected_source_head": "1" * 40,
                "local_branch_deletion": "no",
            }
        )
    if mode == "branch_maintenance_only":
        fields.update(
            {
                "branch_maintenance_action": "verify_declared_local_ref",
                "affected_local_branches": ["synthetic_current"],
                "expected_preserved_head": "none, no ref movement",
                "preservation_ref": "none, no ref movement",
                "reference_restore_source": "none, no ref movement",
                "non_fast_forward_ref_move_authorized": "no",
                "local_branch_deletion": "no",
            }
        )
    if mode == "orchestrated_workflow":
        fields.update(
            {
                "workflow_goal": "complete one synthetic gated decision",
                "workflow_stages": (
                    "- stage_id: stage_1\n"
                    "  stage_mode: investigation_only\n"
                    "  stage_goal: collect synthetic evidence\n"
                    "  stage_preconditions: baseline identity is exact\n"
                    "  stage_acceptance_gate: evidence was serialized\n"
                    "  stage_outputs: observed_evidence\n"
                    "  stage_inputs_from_prior: none, first stage\n"
                    "  stage_on_failure: stop_remaining_stages\n"
                    "- stage_id: stage_2\n"
                    "  stage_mode: validation_only\n"
                    "  stage_goal: validate synthetic evidence\n"
                    "  stage_preconditions: stage_1 accepted\n"
                    "  stage_acceptance_gate: evidence is consistent\n"
                    "  stage_outputs: validated_result\n"
                    "  stage_inputs_from_prior: stage_1.observed_evidence\n"
                    "  stage_on_failure: stop_remaining_stages"
                ),
                "workflow_stop_policy": "stop_on_failed_gate_or_new_decision_boundary",
                "workflow_stage_ledger_path": "/tmp/correction_lib_synthetic/stages.tsv",
            }
        )
    if mode == "production_execution":
        fields.update(
            {
                "execution_owner": "codex",
                "intended_output_paths": ["/tmp/synthetic_production/output"],
                "overwrite_or_resume_policy": "no overwrite and no resume",
                "interruption_retry_policy": "do not retry after ambiguous interruption",
            }
        )
    if mode not in read_only_modes and mode not in {
        "coding",
        "documentation_only",
        "test_alignment_only",
        "commit_preparation",
        "production_execution",
        "integration_only",
        "branch_maintenance_only",
        "orchestrated_workflow",
    }:
        raise AssertionError(f"unhandled mode {mode}")
    return fields


def repository_branch_fields(
    policies: dict[str, str] | None = None,
) -> OrderedDict[str, object]:
    fields = base_fields("coding")
    policies = policies or {
        "meta_repo": "continue_existing_branch",
        "topeft": "read_only_current_branch",
        "topcoffea": "read_only_current_branch",
    }
    fields["branch_policy"] = dict(policies)
    fields["current_checked_out_branch"] = {
        "meta_repo": "master",
        "topeft": "run3_test_mmerged_anpicci",
        "topcoffea": "run3_test_mmerged_anpicci",
    }
    fields["reference_branch"] = {
        repository: (
            "synthetic_reference"
            if policy == "create_feature_branch_from_reference"
            else "none"
        )
        for repository, policy in policies.items()
    }
    fields["target_branch"] = {
        repository: (
            "synthetic_target"
            if policy
            in (
                "continue_existing_branch",
                "commit_preparation_on_existing_branch",
            )
            else "none"
        )
        for repository, policy in policies.items()
    }
    fields["feature_branch"] = {
        repository: (
            "synthetic_feature"
            if policy == "create_feature_branch_from_reference"
            else "none"
        )
        for repository, policy in policies.items()
    }
    fields["current_baseline_branch"] = {
        "meta_repo": "master",
        "topeft": "current checked-out branch",
        "topcoffea": "current checked-out branch",
    }
    return fields


def contexts_for(case: dict[str, object]) -> dict[str, str]:
    contexts = {
        "continuation": "no",
        "evidence_round": "no",
        "user_run_handoff": "no",
    }
    contexts.update(case.get("contexts", {}))
    return contexts


def apply_case(case: dict[str, object]) -> OrderedDict[str, object]:
    fields = base_fields(str(case["mode"]))
    for key in case.get("remove", []):
        fields.pop(key, None)
    fields.update(case.get("set", {}))
    return fields


def validate_bytes(
    content: bytes,
    contexts: dict[str, str] | None = None,
    binding_path: Path = BINDING_PATH,
    strict_unknown: bool = False,
) -> tuple[dict[str, object], int]:
    return VALIDATOR.validate_content(
        "synthetic.md",
        content,
        WORKSPACE_ROOT,
        SCHEMA_PATH,
        binding_path,
        contexts
        or {
            "continuation": "no",
            "evidence_round": "no",
            "user_run_handoff": "no",
        },
        strict_unknown,
    )


class PromptContractValidatorTests(unittest.TestCase):
    maxDiff = None

    def test_all_valid_fixture_families(self) -> None:
        cases = json.loads(VALID_MANIFEST.read_text(encoding="utf-8"))
        modes: set[str] = set()
        for case in cases:
            with self.subTest(case=case["name"]):
                payload, exit_code = validate_bytes(
                    render_prompt(apply_case(case)), contexts_for(case)
                )
                self.assertEqual(exit_code, 0, payload["diagnostics"])
                self.assertTrue(payload["valid_schema"])
                self.assertEqual(payload["error_count"], 0)
                ids = {item["id"] for item in payload["diagnostics"]}
                self.assertIn("OK000", ids)
                for expected in case.get("expected_warning_ids", []):
                    self.assertIn(expected, ids)
                modes.add(str(case["mode"]))
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(modes, set(schema["closed_vocabularies"]["prompt_mode"]))

    def test_all_invalid_fixture_families(self) -> None:
        cases = json.loads(INVALID_MANIFEST.read_text(encoding="utf-8"))
        for case in cases:
            with self.subTest(case=case["name"]):
                payload, exit_code = validate_bytes(
                    render_prompt(apply_case(case)), contexts_for(case)
                )
                self.assertEqual(exit_code, 3, payload["diagnostics"])
                self.assertFalse(payload["valid_schema"])
                diagnostics = payload["diagnostics"]
                self.assertEqual(
                    payload["error_count"],
                    sum(item["severity"] == "error" for item in diagnostics),
                )
                self.assertEqual(
                    payload["warning_count"],
                    sum(item["severity"] == "warning" for item in diagnostics),
                )
                for expected in case["expected"]:
                    matches = [
                        item
                        for item in diagnostics
                        if item["id"] == expected["id"]
                        and item["severity"] == expected["severity"]
                        and (
                            "field" not in expected
                            or expected["field"] in item["field"]
                        )
                    ]
                    self.assertTrue(matches, (expected, diagnostics))

    def test_runcr008_corrected_and_invalid_files(self) -> None:
        corrected = SKILL_ROOT / "tests/fixtures/valid/runcr008_corrected.md"
        invalid = SKILL_ROOT / "tests/fixtures/invalid/runcr008_invalid.md"
        corrected_payload, corrected_exit = validate_bytes(corrected.read_bytes())
        invalid_payload, invalid_exit = validate_bytes(invalid.read_bytes())
        self.assertEqual(corrected_exit, 0, corrected_payload["diagnostics"])
        self.assertEqual(invalid_exit, 3)
        invalid_ids = {item["id"] for item in invalid_payload["diagnostics"]}
        self.assertTrue({"VOC001", "REQ001"}.issubset(invalid_ids))

    def test_duplicate_and_unsupported_mapping_constructs(self) -> None:
        content = render_prompt(base_fields("investigation_only"))
        missing_block_payload, missing_block_exit = validate_bytes(
            b"# Synthetic prompt without structured metadata\n"
        )
        self.assertEqual(missing_block_exit, 3)
        self.assertIn(
            "PARSE001",
            {item["id"] for item in missing_block_payload["diagnostics"]},
        )
        duplicate = content.replace(
            b"prompt_id: SYNTHETIC_INVESTIGATION_ONLY\n",
            b"prompt_id: FIRST\nprompt_id: SECOND\n",
            1,
        )
        duplicate_payload, duplicate_exit = validate_bytes(duplicate)
        self.assertEqual(duplicate_exit, 3)
        self.assertIn(
            "PARSE002", {item["id"] for item in duplicate_payload["diagnostics"]}
        )
        unsupported = content.replace(
            b"short_title: synthetic_investigation_only\n",
            b"short_title: &synthetic_anchor title\n",
            1,
        )
        unsupported_payload, unsupported_exit = validate_bytes(unsupported)
        self.assertEqual(unsupported_exit, 3)
        self.assertIn(
            "PARSE003", {item["id"] for item in unsupported_payload["diagnostics"]}
        )
        unlabeled = content.replace(b"```text\n", b"```\n", 1)
        unlabeled_payload, unlabeled_exit = validate_bytes(unlabeled)
        self.assertEqual(unlabeled_exit, 0, unlabeled_payload["diagnostics"])
        self.assertIn(
            "WARN005", {item["id"] for item in unlabeled_payload["diagnostics"]}
        )

    def test_governance_hash_perturbation_exits_four(self) -> None:
        binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
        binding["agents_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as temporary:
            bad_binding = Path(temporary) / "binding.json"
            bad_binding.write_text(json.dumps(binding), encoding="utf-8")
            payload, exit_code = validate_bytes(
                render_prompt(base_fields("investigation_only")),
                binding_path=bad_binding,
            )
        self.assertEqual(exit_code, 4)
        self.assertFalse(payload["valid_schema"])
        self.assertIn("GOV001", {item["id"] for item in payload["diagnostics"]})
        with tempfile.TemporaryDirectory() as temporary:
            malformed_binding = Path(temporary) / "binding.json"
            malformed_binding.write_text("{}", encoding="utf-8")
            command = [
                sys.executable,
                str(SCRIPT_PATH),
                "--workspace-root",
                str(WORKSPACE_ROOT),
                "--governance-binding",
                str(malformed_binding),
                "--format",
                "json",
                str(SKILL_ROOT / "tests/fixtures/valid/runcr008_corrected.md"),
            ]
            completed = subprocess.run(
                command, check=False, capture_output=True, text=True
            )
        self.assertEqual(completed.returncode, 4)
        malformed_payload = json.loads(completed.stdout)
        self.assertIn(
            "GOV002",
            {item["id"] for item in malformed_payload["diagnostics"]},
        )

    def test_workflow_graph_and_checkpoint_text_are_inert(self) -> None:
        content = render_prompt(base_fields("orchestrated_workflow"))
        additions = (
            b"\n## Workflow graph\n\n```text\nA -> B\n```\n"
            b"\n## Cumulative checkpoint\n\n"
            b"This is evidence and context only; stale remote state must be refreshed.\n"
        )
        baseline, baseline_exit = validate_bytes(content)
        amended, amended_exit = validate_bytes(content + additions)
        self.assertEqual(baseline_exit, 0, baseline["diagnostics"])
        self.assertEqual(amended_exit, 0, amended["diagnostics"])
        self.assertEqual(
            [(item["id"], item["field"]) for item in baseline["diagnostics"]],
            [(item["id"], item["field"]) for item in amended["diagnostics"]],
        )

    def test_orchestration_rejects_multistep_prose_and_merge_stage(self) -> None:
        fields = base_fields("orchestrated_workflow")
        fields["workflow_stages"] = "first investigate, then publish"
        prose_payload, prose_exit = validate_bytes(render_prompt(fields))
        self.assertEqual(prose_exit, 3)
        self.assertIn("ORCH001", {item["id"] for item in prose_payload["diagnostics"]})

        fields = base_fields("orchestrated_workflow")
        fields["workflow_stages"] = fields["workflow_stages"].replace(
            "stage_mode: validation_only",
            "stage_mode: pr_publication\n"
            "  publication_action: merge_existing_pr_or_mr",
        )
        merge_payload, merge_exit = validate_bytes(render_prompt(fields))
        self.assertEqual(merge_exit, 3)
        self.assertIn("ORCH001", {item["id"] for item in merge_payload["diagnostics"]})

    def test_orchestrated_normalization_rejects_generic_force(self) -> None:
        fields = base_fields("orchestrated_workflow")
        exact_ref = "refs/heads/synthetic_staging"
        old_sha = "4" * 40
        fields["workflow_stages"] = fields["workflow_stages"].replace(
            "stage_mode: validation_only\n",
            "stage_mode: pr_publication\n"
            "  publication_action: normalize_declared_post_squash_staging_ref\n"
            "  publication_platform: github\n"
            "  publication_repository: synthetic/example\n"
            "  publication_remote: synthetic_remote\n"
            "  expected_local_head: " + "5" * 40 + "\n"
            "  network_access: yes\n"
            "  remote_git_write: yes\n"
            "  pr_or_mr_write: no\n"
            "  pr_or_mr_merge: no\n"
            "  remote_branch_deletion: no\n"
            "  force_push_allowed: yes\n"
            "  merge_allowed: no\n"
            f"  exact_remote_ref: {exact_ref}\n"
            f"  exact_observed_old_sha: {old_sha}\n"
            "  exact_target_sha: " + "5" * 40 + "\n"
            "  verified_local_archive_ref: refs/heads/archive/synthetic_old\n"
            "  verified_remote_archive_ref_when_remote_history_is_being_rewritten: refs/heads/archive/synthetic_old\n"
            "  archive_reachability: verified\n"
            "  normalization_identity_basis: tree equivalence\n"
            f"  force_with_lease_argument: --force-with-lease={exact_ref}:{old_sha}\n"
            "  generic_force: allowed\n"
            "  lease_refresh_after_unexplained_remote_movement: forbidden\n"
            "  post_write_remote_readback: required\n"
            "  final_expected_identity_readback: required\n"
            "  explicit_user_authorization_for_the_exact_ref_rewrite: exact user authorization\n",
        )
        payload, exit_code = validate_bytes(render_prompt(fields))
        self.assertEqual(exit_code, 3)
        self.assertIn("ORCH001", {item["id"] for item in payload["diagnostics"]})

    def test_publication_actions_have_disjoint_contracts(self) -> None:
        create = base_fields("pr_publication")
        create_payload, create_exit = validate_bytes(render_prompt(create))
        self.assertEqual(create_exit, 0, create_payload["diagnostics"])

        synchronize = base_fields("pr_publication")
        for field in (
            "publication_base_branch",
            "publication_feature_branch",
            "duplicate_pr_or_mr_policy",
            "draft_allowed",
        ):
            synchronize.pop(field)
        synchronize.update(
            {
                "publication_action": "synchronize_declared_remote_branch",
                "publication_local_branch": "synthetic_local",
                "publication_remote_branch": "synthetic_remote_branch",
                "publication_remote_tracking_ref": "refs/remotes/synthetic_remote/synthetic_remote_branch",
                "pr_or_mr_write": "no",
                "remote_git_write": "no",
            }
        )
        sync_payload, sync_exit = validate_bytes(render_prompt(synchronize))
        self.assertEqual(sync_exit, 0, sync_payload["diagnostics"])
        synchronize["force_push_allowed"] = "yes"
        unsafe_sync_payload, unsafe_sync_exit = validate_bytes(render_prompt(synchronize))
        self.assertEqual(unsafe_sync_exit, 3)
        self.assertIn(
            "force_push_allowed",
            {item["field"] for item in unsafe_sync_payload["diagnostics"]},
        )

        normalize = base_fields("pr_publication")
        for field in (
            "publication_base_branch",
            "publication_feature_branch",
            "duplicate_pr_or_mr_policy",
            "draft_allowed",
        ):
            normalize.pop(field)
        exact_ref = "refs/heads/synthetic_staging"
        old_sha = "2" * 40
        normalize.update(
            {
                "publication_action": "normalize_declared_post_squash_staging_ref",
                "exact_remote_ref": exact_ref,
                "exact_observed_old_sha": old_sha,
                "exact_target_sha": "3" * 40,
                "verified_local_archive_ref": "refs/heads/archive/synthetic_old",
                "verified_remote_archive_ref_when_remote_history_is_being_rewritten": "refs/heads/archive/synthetic_old",
                "archive_reachability": "verified exact old SHA reachable",
                "normalization_identity_basis": "tree equivalence verified",
                "force_with_lease_argument": f"--force-with-lease={exact_ref}:{old_sha}",
                "generic_force": "forbidden",
                "lease_refresh_after_unexplained_remote_movement": "forbidden",
                "post_write_remote_readback": "required",
                "final_expected_identity_readback": "required",
                "explicit_user_authorization_for_the_exact_ref_rewrite": "user authorized this exact ref rewrite",
                "remote_git_write": "yes",
                "pr_or_mr_write": "no",
                "force_push_allowed": "yes",
            }
        )
        normalize_payload, normalize_exit = validate_bytes(render_prompt(normalize))
        self.assertEqual(normalize_exit, 0, normalize_payload["diagnostics"])
        normalize["force_with_lease_argument"] = "--force-with-lease"
        invalid_payload, invalid_exit = validate_bytes(render_prompt(normalize))
        self.assertEqual(invalid_exit, 3)
        self.assertIn(
            "force_with_lease_argument",
            {item["field"] for item in invalid_payload["diagnostics"]},
        )
        normalize["force_with_lease_argument"] = f"--force-with-lease={exact_ref}:{old_sha}"
        normalize["generic_force"] = "allowed"
        generic_force_payload, generic_force_exit = validate_bytes(render_prompt(normalize))
        self.assertEqual(generic_force_exit, 3)
        self.assertIn(
            "generic_force",
            {item["field"] for item in generic_force_payload["diagnostics"]},
        )

    def test_ordinary_coding_needs_no_publication_grade_fields(self) -> None:
        payload, exit_code = validate_bytes(render_prompt(base_fields("coding")))
        self.assertEqual(exit_code, 0, payload["diagnostics"])
        fields = {item["field"] for item in payload["diagnostics"]}
        self.assertTrue(
            {
                "confirmed_blockers",
                "additional_unresolved_risks",
                "not_yet_evaluated",
                "closed_with_evidence",
                "confidence_in_completeness",
            }.isdisjoint(fields)
        )

    def test_authorized_non_fast_forward_integration_is_not_false_blocked(self) -> None:
        fields = base_fields("integration_only")
        fields["integration_method"] = "squash"
        fields["resulting_local_commit_behavior"] = "create one declared local squash commit"
        fields["user_override_locator"] = "explicit user authorization for this exact method"
        payload, exit_code = validate_bytes(render_prompt(fields))
        self.assertEqual(exit_code, 0, payload["diagnostics"])
        fields.pop("user_override_locator")
        invalid_payload, invalid_exit = validate_bytes(render_prompt(fields))
        self.assertEqual(invalid_exit, 3)
        self.assertIn("MODE001", {item["id"] for item in invalid_payload["diagnostics"]})

    def test_human_and_json_outputs_use_one_diagnostic_array(self) -> None:
        case = json.loads(INVALID_MANIFEST.read_text(encoding="utf-8"))[0]
        payload, _exit_code = validate_bytes(
            render_prompt(apply_case(case)), contexts_for(case)
        )
        human = VALIDATOR.human_output(payload)
        human_ids = [
            line.split()[1]
            for line in human.splitlines()
            if line.startswith(("  error ", "  warning ", "  info "))
        ]
        json_ids = [item["id"] for item in json.loads(json.dumps(payload))["diagnostics"]]
        self.assertEqual(human_ids, json_ids)

    def test_prompt_and_governance_are_not_modified(self) -> None:
        prompt_path = SKILL_ROOT / "tests/fixtures/valid/runcr008_corrected.md"
        paths = [prompt_path, WORKSPACE_ROOT / "AGENTS.md", WORKSPACE_ROOT / "CPC.md"]
        before = {
            path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths
        }
        payload, exit_code = validate_bytes(prompt_path.read_bytes())
        after = {
            path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths
        }
        self.assertEqual(exit_code, 0, payload["diagnostics"])
        self.assertEqual(before, after)

    def test_template_fails_only_as_unreplaced_required_decisions(self) -> None:
        template = SKILL_ROOT / "assets/prompt_template.md"
        payload, exit_code = validate_bytes(template.read_bytes())
        self.assertEqual(exit_code, 3)
        error_ids = {
            item["id"]
            for item in payload["diagnostics"]
            if item["severity"] == "error"
        }
        self.assertEqual(error_ids, {"REQ001"})

    def test_strict_unknown_turns_warning_into_error(self) -> None:
        fields = base_fields("investigation_only")
        fields["x_project_note"] = "synthetic extension"
        payload, exit_code = validate_bytes(render_prompt(fields), strict_unknown=True)
        self.assertEqual(exit_code, 0, payload["diagnostics"])
        fields["unexpected_note"] = "synthetic unknown"
        payload, exit_code = validate_bytes(render_prompt(fields), strict_unknown=True)
        self.assertEqual(exit_code, 3)
        match = [
            item
            for item in payload["diagnostics"]
            if item["id"] == "WARN001" and item["field"] == "unexpected_note"
        ]
        self.assertEqual(match[0]["severity"], "error")

    def test_cli_json_and_input_exit_codes(self) -> None:
        fixture = SKILL_ROOT / "tests/fixtures/invalid/runcr008_invalid.md"
        command = [
            sys.executable,
            str(SCRIPT_PATH),
            "--workspace-root",
            str(WORKSPACE_ROOT),
            "--continuation",
            "no",
            "--evidence-round",
            "no",
            "--user-run-handoff",
            "no",
            "--format",
            "json",
            str(fixture),
        ]
        completed = subprocess.run(command, check=False, capture_output=True, text=True)
        self.assertEqual(completed.returncode, 3, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(
            payload["error_count"],
            sum(
                item["severity"] == "error" for item in payload["diagnostics"]
            ),
        )
        missing = command[:-1] + [str(fixture.with_name("missing.md"))]
        completed = subprocess.run(missing, check=False, capture_output=True, text=True)
        self.assertEqual(completed.returncode, 2)

    def test_validator_has_no_autofix_or_task_execution_option(self) -> None:
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        self.assertNotIn('add_argument("--fix"', source)
        self.assertNotIn('add_argument("--defaults"', source)
        self.assertNotIn("subprocess.run", source)
        self.assertNotIn("os.system", source)

    def test_valid_scalar_branch_contract_unchanged(self) -> None:
        fields = base_fields("coding")
        fields["branch_policy"] = "continue_existing_branch"
        fields["current_checked_out_branch"] = "master"
        fields["reference_branch"] = "none"
        fields["target_branch"] = "master"
        fields["feature_branch"] = "none"
        fields["current_baseline_branch"] = "master"
        payload, exit_code = validate_bytes(render_prompt(fields))
        self.assertEqual(exit_code, 0, payload["diagnostics"])
        self.assertTrue(payload["valid_schema"])

    def test_valid_three_repository_branch_contract(self) -> None:
        fixture = (
            SKILL_ROOT
            / "tests/fixtures/valid/repository_scoped_skills002_style.md"
        )
        payload, exit_code = validate_bytes(fixture.read_bytes())
        self.assertEqual(exit_code, 0, payload["diagnostics"])
        self.assertTrue(payload["valid_schema"])
        ids = {item["id"] for item in payload["diagnostics"]}
        self.assertTrue(
            {"VOC001", "BRANCH001", "BRANCH002", "XFLD001"}.isdisjoint(ids)
        )

        fields = repository_branch_fields()
        fields["target_branch"]["topeft"] = "a_writable_branch"
        invalid_payload, invalid_exit = validate_bytes(render_prompt(fields))
        self.assertEqual(invalid_exit, 3)
        matches = [
            item
            for item in invalid_payload["diagnostics"]
            if item["id"] == "BRANCH002"
            and item["field"] == "target_branch.topeft"
        ]
        self.assertEqual(len(matches), 1, invalid_payload["diagnostics"])

    def test_valid_mixed_repository_policies(self) -> None:
        policies = {
            "meta_repo": "continue_existing_branch",
            "topeft": "create_feature_branch_from_reference",
            "topcoffea": "commit_preparation_on_existing_branch",
        }
        payload, exit_code = validate_bytes(
            render_prompt(repository_branch_fields(policies))
        )
        self.assertEqual(exit_code, 0, payload["diagnostics"])

    def test_invalid_repository_branch_policy_value(self) -> None:
        fields = repository_branch_fields()
        fields["branch_policy"]["topeft"] = "readonly"
        content = render_prompt(fields)
        expected_line = next(
            index
            for index, line in enumerate(content.decode().splitlines(), 1)
            if line.strip() == "topeft: readonly"
        )
        payload, exit_code = validate_bytes(content)
        self.assertEqual(exit_code, 3)
        matches = [
            item
            for item in payload["diagnostics"]
            if item["id"] == "VOC001"
            and item["field"] == "branch_policy.topeft"
        ]
        self.assertEqual(matches[0]["line"], expected_line)

    def test_missing_repository_in_branch_policy(self) -> None:
        fields = repository_branch_fields()
        del fields["branch_policy"]["topcoffea"]
        payload, exit_code = validate_bytes(render_prompt(fields))
        self.assertEqual(exit_code, 3)
        self.assertIn(
            ("BRANCH001", "branch_policy.topcoffea"),
            {(item["id"], item["field"]) for item in payload["diagnostics"]},
        )

    def test_extra_repository_in_branch_policy(self) -> None:
        fields = repository_branch_fields()
        fields["branch_policy"]["extra_repo"] = "read_only_current_branch"
        payload, exit_code = validate_bytes(render_prompt(fields))
        self.assertEqual(exit_code, 3)
        self.assertIn(
            ("BRANCH002", "branch_policy.extra_repo"),
            {(item["id"], item["field"]) for item in payload["diagnostics"]},
        )

    def test_scalar_mapping_shape_conflict(self) -> None:
        fields = repository_branch_fields()
        fields["target_branch"] = "master"
        payload, exit_code = validate_bytes(render_prompt(fields))
        self.assertEqual(exit_code, 3)
        self.assertIn(
            ("XFLD001", "target_branch"),
            {(item["id"], item["field"]) for item in payload["diagnostics"]},
        )

    def test_missing_repository_in_target_branch(self) -> None:
        fields = repository_branch_fields()
        del fields["target_branch"]["topeft"]
        payload, exit_code = validate_bytes(render_prompt(fields))
        self.assertEqual(exit_code, 3)
        self.assertIn(
            ("BRANCH001", "target_branch.topeft"),
            {(item["id"], item["field"]) for item in payload["diagnostics"]},
        )

    def test_extra_repository_in_feature_branch(self) -> None:
        fields = repository_branch_fields()
        fields["feature_branch"]["extra_repo"] = "none"
        payload, exit_code = validate_bytes(render_prompt(fields))
        self.assertEqual(exit_code, 3)
        self.assertIn(
            ("BRANCH002", "feature_branch.extra_repo"),
            {(item["id"], item["field"]) for item in payload["diagnostics"]},
        )

    def test_per_repository_create_feature_conflict(self) -> None:
        policies = {
            "meta_repo": "continue_existing_branch",
            "topeft": "create_feature_branch_from_reference",
            "topcoffea": "read_only_current_branch",
        }
        fields = repository_branch_fields(policies)
        fields["feature_branch"]["topeft"] = "none"
        payload, exit_code = validate_bytes(render_prompt(fields))
        self.assertEqual(exit_code, 3)
        self.assertIn(
            ("BRANCH001", "feature_branch.topeft"),
            {(item["id"], item["field"]) for item in payload["diagnostics"]},
        )

    def test_per_repository_continue_existing_conflict(self) -> None:
        fields = repository_branch_fields()
        fields["reference_branch"]["meta_repo"] = "unexpected_reference"
        payload, exit_code = validate_bytes(render_prompt(fields))
        self.assertEqual(exit_code, 3)
        self.assertIn(
            ("BRANCH002", "reference_branch.meta_repo"),
            {(item["id"], item["field"]) for item in payload["diagnostics"]},
        )

    def test_per_repository_read_only_conflict(self) -> None:
        fields = repository_branch_fields()
        fields["target_branch"]["topeft"] = "unexpected_target"
        payload, exit_code = validate_bytes(render_prompt(fields))
        self.assertEqual(exit_code, 3)
        self.assertIn(
            ("BRANCH002", "target_branch.topeft"),
            {(item["id"], item["field"]) for item in payload["diagnostics"]},
        )

    def test_per_repository_commit_preparation_conflict(self) -> None:
        policies = {
            "meta_repo": "continue_existing_branch",
            "topeft": "read_only_current_branch",
            "topcoffea": "commit_preparation_on_existing_branch",
        }
        fields = repository_branch_fields(policies)
        fields["feature_branch"]["topcoffea"] = "unexpected_feature"
        payload, exit_code = validate_bytes(render_prompt(fields))
        self.assertEqual(exit_code, 3)
        self.assertIn(
            ("BRANCH002", "feature_branch.topcoffea"),
            {(item["id"], item["field"]) for item in payload["diagnostics"]},
        )

    def test_placeholder_child_value(self) -> None:
        fields = repository_branch_fields()
        fields["current_checked_out_branch"]["topeft"] = (
            "<author_must_supply_branch>"
        )
        payload, exit_code = validate_bytes(render_prompt(fields))
        self.assertEqual(exit_code, 3)
        self.assertIn(
            ("REQ001", "current_checked_out_branch.topeft"),
            {(item["id"], item["field"]) for item in payload["diagnostics"]},
        )

    def test_unsupported_deeper_branch_mapping(self) -> None:
        fields = repository_branch_fields()
        fields["branch_policy"]["topeft"] = {
            "nested_policy": "read_only_current_branch"
        }
        payload, exit_code = validate_bytes(render_prompt(fields))
        self.assertEqual(exit_code, 3)
        self.assertIn(
            ("PARSE003", "branch_policy.topeft"),
            {(item["id"], item["field"]) for item in payload["diagnostics"]},
        )

    def test_child_diagnostic_line_number(self) -> None:
        fields = repository_branch_fields()
        fields["target_branch"]["topcoffea"] = "unexpected_target"
        content = render_prompt(fields)
        target_heading_seen = False
        expected_line = 0
        for index, line in enumerate(content.decode().splitlines(), 1):
            if line == "target_branch:":
                target_heading_seen = True
            elif target_heading_seen and line.strip() == "topcoffea: unexpected_target":
                expected_line = index
                break
        payload, exit_code = validate_bytes(content)
        self.assertEqual(exit_code, 3)
        match = next(
            item
            for item in payload["diagnostics"]
            if item["id"] == "BRANCH002"
            and item["field"] == "target_branch.topcoffea"
        )
        self.assertGreater(expected_line, 0)
        self.assertEqual(match["line"], expected_line)


if __name__ == "__main__":
    unittest.main()
