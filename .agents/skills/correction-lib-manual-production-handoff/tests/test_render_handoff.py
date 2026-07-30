from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
RENDERER = SKILL_ROOT / "scripts/render_handoff.py"
VALID = SKILL_ROOT / "tests/fixtures/valid"
INVALID = SKILL_ROOT / "tests/fixtures/invalid"
BINDING = SKILL_ROOT / "references/governance_binding.json"
SCHEMA = SKILL_ROOT / "references/handoff_schema.json"


class RenderHandoffTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_cli(
        self,
        fixture: Path,
        *,
        output_name: str = "rendered",
        runbook_only: bool = False,
        output_format: str = "json",
        extra: list[str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command = [
            sys.executable,
            str(RENDERER),
            "--format",
            output_format,
            "--output-dir",
            str(self.temp_path / output_name),
        ]
        if runbook_only:
            command.append("--runbook-only")
        if extra:
            command.extend(extra)
        command.append(str(fixture))
        return subprocess.run(command, text=True, capture_output=True, check=False)

    def payload(self, result: subprocess.CompletedProcess[str]) -> dict:
        return json.loads(result.stdout)

    def wrapper_for(self, fixture_name: str, output_name: str = "rendered") -> str:
        result = self.run_cli(VALID / fixture_name, output_name=output_name)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return (self.temp_path / output_name / "handoff_wrapper.sh").read_text()

    def test_schema_versions(self) -> None:
        schema = json.loads(SCHEMA.read_text())
        self.assertEqual(schema["schema_version"], "1.0.0")
        self.assertEqual(schema["renderer_version"], "1.0.0")

    def test_all_valid_fixtures(self) -> None:
        for fixture in sorted(VALID.glob("*.json")):
            with self.subTest(fixture=fixture.name):
                result = self.run_cli(
                    fixture,
                    output_name=fixture.stem,
                    runbook_only=fixture.name == "runbook_only_with_ambiguous_command.json",
                )
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                self.assertTrue(self.payload(result)["schema_valid"])

    def test_all_invalid_fixtures(self) -> None:
        unsafe = {
            "interrupted_ambiguous_runnable_request.json",
            "empty_pending_execution_set_without_runbook_only.json",
        }
        for fixture in sorted(INVALID.glob("*.json")):
            with self.subTest(fixture=fixture.name):
                result = self.run_cli(fixture, output_name=fixture.stem)
                expected = 3 if fixture.name in unsafe else 2
                self.assertEqual(result.returncode, expected, result.stderr + result.stdout)

    def test_stable_diagnostic_identifiers(self) -> None:
        expected = {
            "missing_execution_owner.json": "REQ001",
            "command_as_shell_string.json": "CMD001",
            "completed_valid_without_evidence.json": "STATUS001",
            "interrupted_ambiguous_runnable_request.json": "STATUS003",
            "failed_known_without_retry_authorization.json": "STATUS002",
            "automatic_retry_true.json": "RETRY001",
            "existing_output_allowed_without_qualification.json": "OUTPUT002",
            "logging_enabled_without_directory_or_default.json": "LOG001",
            "fixed_cwd_without_absolute_path.json": "CWD001",
            "script_relative_without_relative_target.json": "CWD001",
            "git_enforcement_without_expected_value.json": "PROV001",
            "undeclared_environment_variable_dependency.json": "ENV001",
            "duplicate_command_id.json": "CMD002",
            "empty_pending_execution_set_without_runbook_only.json": "SAFE001",
            "credential_like_fixture_value.json": "SECRET001",
        }
        for name, diagnostic_id in expected.items():
            with self.subTest(fixture=name):
                result = self.run_cli(INVALID / name, output_name=f"diagnostic_{name}")
                ids = {item["id"] for item in self.payload(result)["diagnostics"]}
                self.assertIn(diagnostic_id, ids)

    def test_human_and_json_diagnostics_are_equivalent(self) -> None:
        fixture = INVALID / "automatic_retry_true.json"
        json_result = self.run_cli(fixture, output_name="json", output_format="json")
        human_result = self.run_cli(fixture, output_name="human", output_format="human")
        ids = {item["id"] for item in self.payload(json_result)["diagnostics"]}
        human_ids = set(re.findall(r"\b[A-Z]+[0-9]{3}\b", human_result.stdout))
        self.assertEqual(ids, human_ids)

    def test_governance_drift_exits_four(self) -> None:
        binding = json.loads(BINDING.read_text())
        binding["agents_sha256"] = "0" * 64
        drifted = self.temp_path / "drifted_binding.json"
        drifted.write_text(json.dumps(binding))
        result = self.run_cli(
            VALID / "caller_managed_no_git_gates.json",
            extra=["--governance-binding", str(drifted)],
        )
        self.assertEqual(result.returncode, 4)
        self.assertIn("GOV001", result.stdout)

    def test_cli_has_no_execution_flag(self) -> None:
        result = subprocess.run(
            [sys.executable, str(RENDERER), "--help"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("--execute", result.stdout)
        self.assertNotIn("--run-wrapper", result.stdout)

    def test_json_out_matches_stdout_payload(self) -> None:
        json_out = self.temp_path / "cli_result.json"
        result = self.run_cli(
            VALID / "caller_managed_no_git_gates.json",
            extra=["--json-out", str(json_out)],
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads(json_out.read_text()), self.payload(result))

    def test_output_rendering_collision_exits_five(self) -> None:
        fixture = VALID / "caller_managed_no_git_gates.json"
        first = self.run_cli(fixture)
        second = self.run_cli(fixture)
        self.assertEqual(first.returncode, 0, first.stderr + first.stdout)
        self.assertEqual(second.returncode, 5)
        self.assertIn("output_error:", second.stderr)

    def test_caller_managed_wrapper_has_no_cd(self) -> None:
        wrapper = self.wrapper_for("caller_managed_no_git_gates.json")
        self.assertNotRegex(wrapper, r"(?m)^\s*cd(?:\s|$)")
        self.assertNotIn("script_dir=", wrapper)

    def test_fixed_wrapper_has_explicit_cd(self) -> None:
        wrapper = self.wrapper_for("fixed_cwd_with_explicit_git_enforcement.json")
        self.assertIn("cd -- /tmp/synthetic_handoff", wrapper)

    def test_script_relative_wrapper_self_locates(self) -> None:
        wrapper = self.wrapper_for("script_relative_cwd.json")
        self.assertIn('BASH_SOURCE[0]', wrapper)
        self.assertIn('cd -- "${script_dir}"/execution_area', wrapper)

    def test_default_logging_needs_no_exported_variable(self) -> None:
        wrapper = self.wrapper_for("local_default_log_directory.json")
        self.assertIn("log_dir_default=local_handoff_logs", wrapper)
        self.assertNotIn(":?", wrapper)
        self.assertNotIn("RUNCR_LOG_DIR", wrapper)

    def test_explicit_logging_override_works(self) -> None:
        wrapper = self.wrapper_for("explicit_log_directory.json")
        wrapper_path = self.temp_path / "rendered/handoff_wrapper.sh"
        override_dir = self.temp_path / "override_logs"
        environment = os.environ.copy()
        environment["HANDOFF_LOG_DIRECTORY"] = str(override_dir)
        result = subprocess.run(
            ["bash", str(wrapper_path)],
            cwd=self.temp_path,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertTrue((override_dir / "write_alpha.log").is_file())
        self.assertFalse((self.temp_path / "explicit_logs").exists())

    def test_default_wrapper_has_no_git_gate(self) -> None:
        wrapper = self.wrapper_for("caller_managed_no_git_gates.json")
        self.assertNotIn("git branch", wrapper)
        self.assertNotIn("git rev-parse", wrapper)

    def test_explicit_strict_provenance_adds_git_gates(self) -> None:
        wrapper = self.wrapper_for("fixed_cwd_with_explicit_git_enforcement.json")
        self.assertIn("git branch --show-current", wrapper)
        self.assertIn("git rev-parse HEAD", wrapper)
        self.assertIn("validated_branch", wrapper)
        self.assertIn("2222222222222222222222222222222222222222", wrapper)

    def test_completed_valid_is_excluded(self) -> None:
        wrapper = self.wrapper_for("completed_valid_then_pending_continuation.json")
        self.assertNotIn("already_done", wrapper)
        self.assertNotIn("accepted evidence row done", wrapper)
        self.assertIn("run_next", wrapper)
        inventory = json.loads(
            (self.temp_path / "rendered/handoff_commands.json").read_text()
        )
        self.assertEqual(inventory["commands_to_execute"], ["run_next"])

    def test_runnable_order_is_preserved(self) -> None:
        self.wrapper_for("multiple_commands_exact_order.json")
        inventory = json.loads(
            (self.temp_path / "rendered/handoff_commands.json").read_text()
        )
        self.assertEqual(
            inventory["commands_to_execute"],
            ["first_pending", "second_not_started", "third_retry"],
        )

    def test_ambiguous_interruption_blocks_wrapper(self) -> None:
        result = self.run_cli(
            INVALID / "interrupted_ambiguous_runnable_request.json"
        )
        self.assertEqual(result.returncode, 3)
        self.assertFalse((self.temp_path / "rendered/handoff_wrapper.sh").exists())
        self.assertTrue((self.temp_path / "rendered/handoff_runbook.md").exists())

    def test_known_failure_requires_explicit_retry_authorization(self) -> None:
        invalid = self.run_cli(
            INVALID / "failed_known_without_retry_authorization.json",
            output_name="invalid_failure",
        )
        valid = self.run_cli(
            VALID / "failed_known_with_explicit_retry_authorization.json",
            output_name="valid_failure",
        )
        self.assertEqual(invalid.returncode, 2)
        self.assertEqual(valid.returncode, 0)

    def test_output_existence_is_not_qualification(self) -> None:
        result = self.run_cli(
            INVALID / "existing_output_allowed_without_qualification.json"
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("OUTPUT002", result.stdout)

    def test_collision_checks_are_manifest_derived(self) -> None:
        wrapper = self.wrapper_for("caller_managed_no_git_gates.json")
        self.assertIn("out/alpha.done", wrapper)
        self.assertNotIn(".pkl", wrapper)
        self.assertNotIn("sidecar", wrapper.lower())

    def test_existing_output_collision_fails_closed(self) -> None:
        self.wrapper_for("caller_managed_no_git_gates.json")
        (self.temp_path / "out").mkdir()
        (self.temp_path / "out/alpha.done").write_text("existing")
        result = subprocess.run(
            ["bash", str(self.temp_path / "rendered/handoff_wrapper.sh")],
            cwd=self.temp_path,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 73)
        self.assertIn("output collision", result.stderr)

    def test_no_automatic_retry_path(self) -> None:
        wrapper = self.wrapper_for("caller_managed_no_git_gates.json")
        self.assertNotRegex(wrapper, r"(?m)^\s*(?:while|until)\b")
        self.assertNotIn("retry", wrapper.lower())

    def test_no_deletion_command(self) -> None:
        wrapper = self.wrapper_for("caller_managed_no_git_gates.json")
        self.assertNotRegex(wrapper, r"(?m)^\s*(?:rm|rmdir|unlink|shred)\b")

    def test_one_log_per_command(self) -> None:
        self.wrapper_for("multiple_commands_exact_order.json")
        result = subprocess.run(
            ["bash", str(self.temp_path / "rendered/handoff_wrapper.sh")],
            cwd=self.temp_path,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        logs = sorted(path.name for path in (self.temp_path / "handoff_logs").glob("*.log"))
        self.assertEqual(
            logs,
            ["first_pending.log", "second_not_started.log", "third_retry.log"],
        )
        for name in logs:
            content = (self.temp_path / "handoff_logs" / name).read_text()
            self.assertIn("start_time:", content)
            self.assertIn("end_time:", content)
            self.assertIn("exit_code: 0", content)
            self.assertIn("command:", content)

    def test_nonzero_command_stops_later_commands(self) -> None:
        manifest = json.loads(
            (VALID / "multiple_commands_exact_order.json").read_text()
        )
        marker = self.temp_path / "later_was_run"
        manifest["handoff_id"] = "nonzero_stops_later"
        manifest["commands"] = [
            {
                "command_id": "fail_first",
                "status": "pending",
                "argv": [sys.executable, "-c", "import sys; sys.exit(7)"],
                "description": "Exit nonzero without side effects.",
                "expected_outputs": [
                    {
                        "path": str(self.temp_path / "failure.marker"),
                        "role": "synthetic marker",
                        "collision_behavior": "must_be_absent",
                        "qualification_artifacts": [],
                    }
                ],
                "qualification_evidence": [],
            },
            {
                "command_id": "later_command",
                "status": "not_started",
                "argv": [
                    sys.executable,
                    "-c",
                    f"from pathlib import Path; Path({str(marker)!r}).write_text('ran')",
                ],
                "description": "Would create a temporary marker.",
                "expected_outputs": [
                    {
                        "path": str(marker),
                        "role": "synthetic marker",
                        "collision_behavior": "must_be_absent",
                        "qualification_artifacts": [],
                    }
                ],
                "qualification_evidence": [],
            },
        ]
        manifest_path = self.temp_path / "nonzero.json"
        manifest_path.write_text(json.dumps(manifest))
        rendered = self.run_cli(manifest_path)
        self.assertEqual(rendered.returncode, 0, rendered.stderr + rendered.stdout)
        executed = subprocess.run(
            ["bash", str(self.temp_path / "rendered/handoff_wrapper.sh")],
            cwd=self.temp_path,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(executed.returncode, 7)
        self.assertFalse(marker.exists())

    def test_runbook_only_renders_without_wrapper(self) -> None:
        result = self.run_cli(
            VALID / "runbook_only_with_ambiguous_command.json",
            runbook_only=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertTrue((self.temp_path / "rendered/handoff_runbook.md").is_file())
        self.assertFalse((self.temp_path / "rendered/handoff_wrapper.sh").exists())

    def test_runbook_contains_required_sections(self) -> None:
        self.wrapper_for("completed_valid_then_pending_continuation.json")
        runbook = (self.temp_path / "rendered/handoff_runbook.md").read_text()
        for heading in (
            "Scope",
            "Required execution directory",
            "Environment requirements",
            "Provenance recording",
            "Provenance enforcement",
            "Command inventory",
            "Completed-valid commands",
            "Commands to execute",
            "Failed or ambiguous commands",
            "Output collision policy",
            "Logging policy",
            "Interruption policy",
            "Evidence to return",
            "Exact generated artifact paths",
        ):
            self.assertIn(f"## {heading}", runbook)
        self.assertIn("Codex did not execute", runbook)

    def test_generated_bash_passes_syntax_validation(self) -> None:
        for fixture in sorted(VALID.glob("*.json")):
            if fixture.name == "runbook_only_with_ambiguous_command.json":
                continue
            with self.subTest(fixture=fixture.name):
                output_name = f"syntax_{fixture.stem}"
                self.run_cli(fixture, output_name=output_name)
                result = subprocess.run(
                    ["bash", "-n", str(self.temp_path / output_name / "handoff_wrapper.sh")],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_generated_artifacts_are_json_reopenable(self) -> None:
        self.wrapper_for("caller_managed_no_git_gates.json")
        for name in ("handoff_commands.json", "handoff_validation.json"):
            payload = json.loads((self.temp_path / "rendered" / name).read_text())
            self.assertIsInstance(payload, dict)

    def test_fixture_inventory_has_required_count(self) -> None:
        self.assertGreaterEqual(len(list(VALID.glob("*.json"))), 10)
        self.assertGreaterEqual(len(list(INVALID.glob("*.json"))), 15)

    def test_fixtures_contain_no_real_production_commands(self) -> None:
        forbidden = ("fullR3_run.sh", "Work Queue", "condor_", "root://", ".pkl")
        for fixture in sorted((SKILL_ROOT / "tests/fixtures").glob("*/*.json")):
            text = fixture.read_text()
            with self.subTest(fixture=fixture.name):
                for token in forbidden:
                    self.assertNotIn(token, text)


if __name__ == "__main__":
    unittest.main()
