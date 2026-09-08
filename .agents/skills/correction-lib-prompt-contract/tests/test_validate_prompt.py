from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "validate_prompt.py"
SCHEMA = SKILL_ROOT / "references" / "prompt_schema.json"
SPEC = importlib.util.spec_from_file_location("prompt_linter", SCRIPT)
helper = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = helper
SPEC.loader.exec_module(helper)


def prompt(*lines: str) -> bytes:
    return ("# Prompt\n\n```text\n" + "\n".join(lines) + "\n```\n").encode()


class PromptLintTests(unittest.TestCase):
    def test_local_schema_matches_helper_format(self) -> None:
        schema = json.loads(SCHEMA.read_text())
        self.assertEqual(schema["schema_version"], helper.SCHEMA_VERSION)
        self.assertEqual(schema["validator_version"], helper.VALIDATOR_VERSION)
        self.assertEqual(schema["governance_completeness"], "not_assessed")

    def test_unknown_future_field_is_accepted(self) -> None:
        content = prompt(
            "prompt_id: example",
            "commit_expected: yes",
            "do_not_commit: no",
            "future_workspace_capability: newly_defined_value",
        )
        result = helper.validate_content(content, Path("prompt.md"))
        self.assertTrue(result["mechanical_validity"])
        self.assertTrue(result["internal_consistency"])
        self.assertEqual(result["normalized_fields"]["future_workspace_capability"], "newly_defined_value")
        self.assertEqual(result["governance_completeness"], "not_assessed")
        self.assertTrue(result["governance_completeness_not_assessed"])

    def test_unrelated_workspace_policy_bytes_are_not_an_input(self) -> None:
        content = prompt("prompt_id: stable", "commit_expected: no", "do_not_commit: yes")
        first = helper.validate_content(content, Path("first.md"))
        with tempfile.TemporaryDirectory() as temporary:
            unrelated = Path(temporary) / "workspace_policy.txt"
            unrelated.write_text("version one\n")
            unrelated.write_text("version two with unrelated changes\n")
            second = helper.validate_content(content, Path("second.md"))
        self.assertEqual(first["mechanical_validity"], second["mechanical_validity"])
        self.assertEqual(first["internal_consistency"], second["internal_consistency"])
        self.assertNotIn("governance", first["capabilities"])

    def test_duplicate_field_is_rejected_deterministically(self) -> None:
        content = prompt("prompt_id: first", "prompt_id: second")
        result = helper.validate_content(content, Path("prompt.md"))
        self.assertFalse(result["mechanical_validity"])
        self.assertEqual([item["diagnostic_id"] for item in result["diagnostics"]], ["PARSE002"])

    def test_unclosed_fence_and_placeholder_are_reported(self) -> None:
        content = b"# Prompt\n```text\nprompt_id: <supply_id>\n"
        result = helper.validate_content(content, Path("prompt.md"))
        self.assertFalse(result["mechanical_validity"])
        self.assertEqual(
            {item["diagnostic_id"] for item in result["diagnostics"]},
            {"PARSE001", "PLACEHOLDER001"},
        )

    def test_supplied_commit_values_are_normalized_and_checked(self) -> None:
        content = prompt("commit_expected: YES", "do_not_commit: true")
        result = helper.validate_content(content, Path("prompt.md"))
        self.assertTrue(result["mechanical_validity"])
        self.assertFalse(result["internal_consistency"])
        self.assertEqual(result["normalized_fields"]["commit_expected"], True)
        self.assertEqual(result["normalized_fields"]["do_not_commit"], True)
        self.assertEqual(result["diagnostics"][0]["diagnostic_id"], "CONSISTENCY001")

    def test_execution_and_materialization_contradictions(self) -> None:
        content = prompt(
            "execution_not_authorized: yes",
            "execution_requested: yes",
            "materialization_requested: no",
            "materialization_completed: yes",
        )
        result = helper.validate_content(content, Path("prompt.md"))
        self.assertEqual(
            [item["diagnostic_id"] for item in result["diagnostics"]],
            ["CONSISTENCY002", "CONSISTENCY003"],
        )

    def test_cli_json_result_and_no_execution_or_policy_binding_surface(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "prompt.md"
            path.write_bytes(prompt("prompt_id: cli", "commit_expected: no", "do_not_commit: yes"))
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--format", "json", str(path)],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["mechanical_validity"])
        self.assertEqual(payload["governance_completeness"], "not_assessed")
        help_result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            text=True,
            capture_output=True,
            check=False,
        )
        for option in ("--execute", "--governance-" + "binding", "--workspace-root"):
            self.assertNotIn(option, help_result.stdout)

    def test_json_output_is_exclusive(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "prompt.md"
            output = root / "result.json"
            path.write_bytes(prompt("prompt_id: cli", "commit_expected: no", "do_not_commit: yes"))
            first = helper.main(["--format", "json", "--json-out", str(output), str(path)])
            second = helper.main(["--format", "json", "--json-out", str(output), str(path)])
        self.assertEqual(first, 0)
        self.assertEqual(second, 4)


if __name__ == "__main__":
    unittest.main()
