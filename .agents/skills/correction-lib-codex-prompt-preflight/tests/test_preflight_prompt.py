from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_ROOT / "scripts/preflight_prompt.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
SPEC = importlib.util.spec_from_file_location("preflight_prompt", SCRIPT_PATH)
assert SPEC and SPEC.loader
preflight_prompt = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = preflight_prompt
SPEC.loader.exec_module(preflight_prompt)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = json.loads((SKILL_ROOT / "references/section_ownership.json").read_text())

    def test_all_author_owned_headings_and_aliases(self) -> None:
        self.assertEqual(len(self.registry["author_owned"]), 14)
        self.assertEqual(len(self.registry["aliases"]), 5)
        lookup, errors = preflight_prompt.build_registry(self.registry)
        self.assertEqual(errors, [])
        for heading in self.registry["author_owned"]:
            self.assertEqual(lookup[preflight_prompt.normalized_heading(heading)][1], "author_owned")
        for alias, canonical in self.registry["aliases"].items():
            self.assertEqual(lookup[preflight_prompt.normalized_heading(alias)][0], canonical)

    def test_all_skill_and_shared_headings(self) -> None:
        self.assertEqual(len(self.registry["skill_owned"]), 10)
        self.assertEqual(len(self.registry["shared_structured"]), 9)

    def test_every_author_heading_and_alias_preserves_exact_bytes(self) -> None:
        live = {
            "meta_repo": {"path": str(WORKSPACE_ROOT), "branch": "master", "head": "a" * 40},
            "topeft": {"path": str(WORKSPACE_ROOT / "topeft"), "branch": "r", "head": "b" * 40},
            "topcoffea": {"path": str(WORKSPACE_ROOT / "topcoffea"), "branch": "r", "head": "c" * 40},
        }
        headings = list(self.registry["author_owned"]) + list(self.registry["aliases"])
        for heading in headings:
            with self.subTest(heading=heading):
                text = f"# Prompt X\n\n## {heading}\n\n  sentinel  \n"
                sections, diagnostics, _ = preflight_prompt.parse_sections(text, self.registry)
                _, manifest = preflight_prompt.canonicalize("X", "x", {}, sections, WORKSPACE_ROOT, live, diagnostics)
                self.assertEqual(manifest[0]["source_sha256"], manifest[0]["canonical_sha256"])
                self.assertTrue(manifest[0]["preserved_exactly"])

    def test_every_shared_heading_classifies_and_every_skill_heading_generates(self) -> None:
        for heading in self.registry["shared_structured"]:
            with self.subTest(heading=heading):
                sections, _, _ = preflight_prompt.parse_sections(f"# Prompt X\n\n## {heading}\nvalue\n", self.registry)
                self.assertEqual(sections[0].ownership, "shared_structured")
        live = {
            "meta_repo": {"path": str(WORKSPACE_ROOT), "branch": "master", "head": "a" * 40},
            "topeft": {"path": str(WORKSPACE_ROOT / "topeft"), "branch": "r", "head": "b" * 40},
            "topcoffea": {"path": str(WORKSPACE_ROOT / "topcoffea"), "branch": "r", "head": "c" * 40},
        }
        generated = preflight_prompt.generated_skill_sections("X", WORKSPACE_ROOT, live)
        self.assertEqual(set(generated) | {"Metadata and governance"}, set(self.registry["skill_owned"]))

    def test_closed_diagnostic_catalog(self) -> None:
        expected = {f"PROMPT-PREFLIGHT-E{index:03d}" for index in range(1, 16)}
        expected |= {f"PROMPT-PREFLIGHT-W{index:03d}" for index in range(1, 4)}
        self.assertEqual(set(self.registry["diagnostics"]), expected)
        source = SCRIPT_PATH.read_text()
        self.assertTrue(all(diagnostic_id in source for diagnostic_id in expected))

    def test_closed_state_catalog_and_transition(self) -> None:
        self.assertEqual(len(self.registry["states"]), 9)
        self.assertIn(["prompt_contract_passed", "ready_for_same_session_execution"], self.registry["allowed_transitions"])
        self.assertIn(["ready_for_same_session_execution", "execution_started"], self.registry["allowed_transitions"])


class MarkdownParserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = json.loads((SKILL_ROOT / "references/section_ownership.json").read_text())

    def parse(self, text: str):
        return preflight_prompt.parse_sections(text, self.registry)

    def test_headings_inside_fences_and_nested_headings_are_body(self) -> None:
        text = "# Prompt X\n\n## Context\n\n````text\n## not a section\n```\n````\n### nested\n\n## Goal\nvalue\n"
        sections, diagnostics, _ = self.parse(text)
        self.assertEqual([item.canonical_heading for item in sections], ["Context", "Goal"])
        self.assertFalse([item for item in diagnostics if item.severity == "error"])

    def test_tilde_fence_and_exact_length(self) -> None:
        good = "# Prompt X\n\n## Context\n~~~text\n## inert\n~~~\n"
        sections, diagnostics, _ = self.parse(good)
        self.assertEqual(len(sections), 1)
        self.assertFalse([item for item in diagnostics if item.severity == "error"])
        bad = good.replace("~~~\n", "~~~~\n", 1)
        _, diagnostics, _ = self.parse(bad)
        self.assertIn("PROMPT-PREFLIGHT-E002", {item.id for item in diagnostics})

    def test_unclosed_fence(self) -> None:
        _, diagnostics, _ = self.parse("# Prompt X\n\n## Context\n```text\nvalue\n")
        self.assertIn("PROMPT-PREFLIGHT-E002", {item.id for item in diagnostics})

    def test_duplicate_alias_blocks(self) -> None:
        text = "# Prompt X\n\n## Known findings\na\n\n## Known defects\nb\n"
        _, diagnostics, _ = self.parse(text)
        self.assertIn("PROMPT-PREFLIGHT-E003", {item.id for item in diagnostics})

    def test_unknown_safe_preserved_and_permission_unknown_blocks(self) -> None:
        safe = "# Prompt X\n\n## Reviewer intuition\nkeep me\n"
        sections, diagnostics, _ = self.parse(safe)
        self.assertEqual(sections[0].ownership, "author_owned")
        self.assertIn("PROMPT-PREFLIGHT-W003", {item.id for item in diagnostics})
        unsafe = "# Prompt X\n\n## Special authority\nnetwork access is allowed\n"
        _, diagnostics, _ = self.parse(unsafe)
        self.assertIn("PROMPT-PREFLIGHT-E004", {item.id for item in diagnostics})


class RegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = json.loads((SKILL_ROOT / "references/section_ownership.json").read_text())
        cls.live = {
            "meta_repo": {"path": str(WORKSPACE_ROOT), "branch": "master", "head": "a" * 40},
            "topeft": {"path": str(WORKSPACE_ROOT / "topeft"), "branch": "run3_test_mmerged_anpicci", "head": "b" * 40},
            "topcoffea": {"path": str(WORKSPACE_ROOT / "topcoffea"), "branch": "run3_test_mmerged_anpicci", "head": "c" * 40},
        }

    def fixture(self, name: str) -> str:
        return (FIXTURES / name).read_text(encoding="utf-8")

    def fields_for(self, name: str):
        sections, diagnostics, _ = preflight_prompt.parse_sections(self.fixture(name), self.registry)
        fields, _ = preflight_prompt.merge_semantic_fields(sections)
        prompt_id = preflight_prompt.scalar(fields.get("prompt_id")) or "fixture"
        completed, repairs = preflight_prompt.complete_fields(fields, sections, prompt_id, WORKSPACE_ROOT, self.live, {"continuation": "no", "evidence_round": "yes", "user_run_handoff": "no"}, diagnostics)
        return sections, completed, repairs, diagnostics

    def test_r1_transport_identity_blocks(self) -> None:
        diagnostics = preflight_prompt.transport_diagnostics(self.fixture("r1_transport_identity.md"))
        self.assertEqual([item.id for item in diagnostics], ["PROMPT-PREFLIGHT-E015"])
        safe = "Transport bytes are unavailable, not required, and not claimed."
        self.assertEqual(preflight_prompt.transport_diagnostics(safe), [])

    def test_r2_metadata_envelope_generated(self) -> None:
        sections, fields, repairs, diagnostics = self.fields_for("r2_missing_envelope.md")
        canonical, _ = preflight_prompt.canonicalize("R2", "missing_envelope", fields, sections, WORKSPACE_ROOT, self.live, diagnostics)
        self.assertIn("## Metadata and governance\n\n```text\n", canonical)
        self.assertIn("workspace_root", {item["field"] for item in repairs})

    def test_r3_exact_evidence_representations(self) -> None:
        _, fields, repairs, _ = self.fields_for("r3_prose_evidence.md")
        self.assertIn(preflight_prompt.EVIDENCE_COMPACT, fields["evidence_validation_method"])
        for phase in preflight_prompt.EVIDENCE_SEQUENCE:
            self.assertIn(f"    - {phase}", fields["evidence_requirements"])
        self.assertIn("evidence_requirements", {item["field"] for item in repairs})

    def test_r5_workspace_generated(self) -> None:
        _, fields, repairs, _ = self.fields_for("r5_missing_workspace.md")
        self.assertEqual(preflight_prompt.scalar(fields["workspace_root"]), str(WORKSPACE_ROOT))
        self.assertIn("workspace_root", {item["field"] for item in repairs})

    def test_r5_vocabulary_repaired_without_rewriting_rationale(self) -> None:
        sections, fields, repairs, diagnostics = self.fields_for("r5_vocabulary.md")
        canonical, manifest = preflight_prompt.canonicalize("R5B", "vocabulary", fields, sections, WORKSPACE_ROOT, self.live, diagnostics)
        self.assertIn("patch_kind_expected: prompt_local", canonical)
        self.assertIn("This is a corrective follow-up.", canonical)
        rationale = next(item for item in manifest if item["canonical_heading"] == "Technical rationale")
        self.assertTrue(rationale["preserved_exactly"])
        self.assertIn("patch_kind_expected", {item["field"] for item in repairs})


class IntegrationAndSafetyTests(unittest.TestCase):
    def test_author_and_shared_exact_preservation_with_live_validator(self) -> None:
        source = FIXTURES / "base_prompt.md"
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "preflight"
            state, exit_code = preflight_prompt.run_preflight(source, output, WORKSPACE_ROOT, {"continuation": "no", "evidence_round": "yes", "user_run_handoff": "no"})
            self.assertEqual(exit_code, 0, json.dumps(state, indent=2))
            self.assertEqual(state["current_state"], "ready_for_same_session_execution")
            manifest = json.loads((output / "section_manifest.json").read_text())
            author = [item for item in manifest if item["ownership"] == "author_owned"]
            self.assertTrue(author)
            self.assertTrue(all(item["source_sha256"] == item["canonical_sha256"] and item["preserved_exactly"] for item in author))
            shared = json.loads((output / "shared_value_manifest.json").read_text())
            self.assertEqual(shared["author_semantic_invention_count"], 0)
            self.assertEqual(shared["author_semantic_change_count"], 0)
            validation = json.loads((output / "prompt_contract_validation.json").read_text())
            self.assertEqual(validation["error_count"], 0)
            self.assertTrue(validation["validator_input_sha256_matches_canonical"])
            for name in preflight_prompt.OUTPUT_NAMES:
                path = output / name
                self.assertTrue(path.is_file())
                if path.suffix == ".json":
                    json.loads(path.read_text())

    def test_same_session_gate_rejects_before_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state.json"
            path.write_text(json.dumps({"current_state": "canonicalized", "blocking_error_count": 0}))
            with self.assertRaises(preflight_prompt.PreflightBlocked) as caught:
                preflight_prompt.assert_ready_for_task_action(path)
            self.assertEqual(caught.exception.diagnostic.id, "PROMPT-PREFLIGHT-E014")
            path.write_text(json.dumps({"current_state": "ready_for_same_session_execution", "blocking_error_count": 0}))
            preflight_prompt.assert_ready_for_task_action(path)

    def test_human_and_json_diagnostics_share_one_record_set(self) -> None:
        diagnostic = preflight_prompt.Diagnostic("PROMPT-PREFLIGHT-E005", "error", "missing sentinel", "Task metadata", 7)
        state = {
            "current_state": "blocked_semantic_ambiguity",
            "blocking_error_count": 1,
            "warning_count": 0,
            "canonical_prompt_sha256": "a" * 64,
            "prompt_contract_invoked": False,
            "repairs": [],
        }
        human = preflight_prompt.report_text(state, [diagnostic])
        machine = json.loads(preflight_prompt.json_text({"diagnostics": [preflight_prompt.asdict(diagnostic)]}))
        self.assertIn(diagnostic.id, human)
        self.assertEqual(machine["diagnostics"][0]["message"], "missing sentinel")

    def test_existing_output_root_blocks_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            existing = Path(temporary) / "existing"
            existing.mkdir()
            state, exit_code = preflight_prompt.run_preflight(FIXTURES / "base_prompt.md", existing, WORKSPACE_ROOT, {"continuation": "no", "evidence_round": "yes", "user_run_handoff": "no"})
            self.assertEqual(exit_code, 3)
            self.assertEqual(state["diagnostics"][0]["id"], "PROMPT-PREFLIGHT-E012")
            self.assertEqual(list(existing.iterdir()), [])

    def test_fixed_subprocesses_are_shell_false_and_prompt_is_not_argv(self) -> None:
        source_text = (FIXTURES / "base_prompt.md").read_text()
        calls = []

        def fake_run(argv, **kwargs):
            calls.append((list(argv), dict(kwargs)))
            self.assertFalse(kwargs["shell"])
            self.assertNotIn(source_text, argv)
            if argv[0] == "git":
                if argv[-2:] == ["branch", "--show-current"]:
                    repo = Path(argv[2])
                    branch = "master" if repo == WORKSPACE_ROOT else "run3_test_mmerged_anpicci"
                    return subprocess.CompletedProcess(argv, 0, branch + "\n", "")
                return subprocess.CompletedProcess(argv, 0, "a" * 40 + "\n", "")
            canonical = Path(argv[-1])
            digest = hashlib.sha256(canonical.read_bytes()).hexdigest()
            payload = {"valid_schema": True, "error_count": 0, "warning_count": 0, "input": {"sha256": digest}, "diagnostics": []}
            return subprocess.CompletedProcess(argv, 0, json.dumps(payload), "")

        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(preflight_prompt.subprocess, "run", side_effect=fake_run):
            state, exit_code = preflight_prompt.run_preflight(FIXTURES / "base_prompt.md", Path(temporary) / "output", WORKSPACE_ROOT, {"continuation": "no", "evidence_round": "yes", "user_run_handoff": "no"})
        self.assertEqual(exit_code, 0, state)
        self.assertEqual(len(calls), 7)

    def test_static_no_execution_interfaces(self) -> None:
        source = SCRIPT_PATH.read_text()
        tree = ast.parse(source)
        forbidden_calls = {"eval", "exec", "__import__", "compile"}
        called = {node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
        self.assertTrue(forbidden_calls.isdisjoint(called))
        self.assertNotIn("codex exec", source.casefold())
        self.assertNotIn("shell=True", source)
        self.assertNotIn("task_callback", source)

    def test_all_five_governance_bindings_match(self) -> None:
        agents_hash = sha256(WORKSPACE_ROOT / "AGENTS.md")
        cpc_hash = sha256(WORKSPACE_ROOT / "CPC.md")
        skills = (
            "correction-lib-codex-prompt-preflight",
            "correction-lib-prompt-contract",
            "correction-lib-manual-production-handoff",
            "correction-lib-diagnostics-execution-copy",
            "correction-lib-codex-evidence-package-review",
        )
        for skill in skills:
            with self.subTest(skill=skill):
                binding = json.loads((WORKSPACE_ROOT / ".agents/skills" / skill / "references/governance_binding.json").read_text())
                self.assertEqual(binding["agents_sha256"], agents_hash)
                self.assertEqual(binding["cpc_sha256"], cpc_hash)


if __name__ == "__main__":
    unittest.main()
