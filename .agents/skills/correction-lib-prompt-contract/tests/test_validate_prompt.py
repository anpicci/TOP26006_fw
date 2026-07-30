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
    }:
        raise AssertionError(f"unhandled mode {mode}")
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


if __name__ == "__main__":
    unittest.main()
