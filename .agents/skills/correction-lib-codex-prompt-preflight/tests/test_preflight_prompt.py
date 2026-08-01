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


def current_prompt(prompt_id: str = "FIXTURE101", preamble: str | None = None) -> str:
    live = preflight_prompt.live_repository_state(WORKSPACE_ROOT)
    preamble = preamble if preamble is not None else f"# Prompt `{prompt_id}` — current fixture\n\n"
    lines = [preamble, "## Task metadata\n\n```text\n", f"prompt_id: {prompt_id}\n", "short_title: current_fixture\n", "prompt_mode: coding\n", "preferred_codex_model: gpt-5.6-terra\n", "reasoning_level: high\n", "delegation_policy: forbidden\n", "model_selection_rationale: bounded inert current-state fixture\n", "allowed_to_modify:\n  meta_repo: AGENTS.md\n", "read_only:\n  topeft: branch and HEAD only\n  topcoffea: branch and HEAD only\n", "branch_policy:\n"]
    for repository in live:
        policy = "continue_existing_branch" if repository == "meta_repo" else "read_only_current_branch"
        lines.append(f"  {repository}: {policy}\n")
    lines.append("current_checked_out_branch:\n")
    lines.extend(f"  {repository}: {item['branch']}\n" for repository, item in live.items())
    lines.append("reference_branch:\n")
    lines.extend(f"  {repository}: none\n" for repository in live)
    lines.append("target_branch:\n")
    lines.extend(f"  {repository}: {item['branch'] if repository == 'meta_repo' else 'none'}\n" for repository, item in live.items())
    lines.append("feature_branch:\n")
    lines.extend(f"  {repository}: none\n" for repository in live)
    lines.append("current_baseline_branch:\n")
    lines.extend(f"  {repository}: {item['branch']}\n" for repository, item in live.items())
    lines.append("comparison_baseline:\n")
    for repository, item in live.items():
        lines.extend((f"  {repository}:\n", f"    expected_head: {item['head']}\n", f"    expected_subject: {item['subject']}\n"))
    lines.extend(("integrated_baseline_mode: yes\n", "dirty_worktree_policy: allow_declared_preexisting_changes\n", "preflight_profile: compact_preflight\n", "preflight_scope_paths:\n  meta_repo: AGENTS.md\n", "validation_ceiling: targeted_unit_test\n", "heavy_command_permissions:\n  defaults: all_no\n", "do_not_commit: no\n", "commit_expected: yes\n", "commit_message_policy:\n  exact_subject: feat(governance): inert fixture\n", "goal: validate an inert current-state prompt\n", "decision_question: Can the inert fixture reach readiness?\n", "out_of_scope:\n  - task execution\n", "continuation: no\n", "evidence_round: yes\n", "user_run_handoff: no\n", "```\n\n", "## Goal\n\nPreserve this exact author section.\n"))
    return "".join(lines)


def diagnostics_capture(prompt_text: str):
    parent = tempfile.TemporaryDirectory(dir=WORKSPACE_ROOT / "reports/diagnostics")
    root = Path(parent.name)
    source = root / "source.md"
    source.write_text(prompt_text, encoding="utf-8")
    return parent, source, root / "output"


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
        expected = {f"PROMPT-PREFLIGHT-E{index:03d}" for index in range(1, 21)}
        expected |= {f"PROMPT-PREFLIGHT-W{index:03d}" for index in range(1, 5)}
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
        temporary, source, output = diagnostics_capture(current_prompt())
        with temporary:
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
        temporary, source, existing = diagnostics_capture(current_prompt())
        with temporary:
            existing.mkdir()
            state, exit_code = preflight_prompt.run_preflight(source, existing, WORKSPACE_ROOT, {"continuation": "no", "evidence_round": "yes", "user_run_handoff": "no"})
            self.assertEqual(exit_code, 3)
            self.assertEqual(state["diagnostics"][0]["id"], "PROMPT-PREFLIGHT-E012")
            self.assertEqual(list(existing.iterdir()), [])

    def test_fixed_subprocesses_are_shell_false_and_prompt_is_not_argv(self) -> None:
        source_text = current_prompt()
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
                if "--format=%s" in argv:
                    return subprocess.CompletedProcess(argv, 0, "synthetic subject\n", "")
                return subprocess.CompletedProcess(argv, 0, "a" * 40 + "\n", "")
            canonical = Path(argv[-1])
            digest = hashlib.sha256(canonical.read_bytes()).hexdigest()
            payload = {"valid_schema": True, "error_count": 0, "warning_count": 0, "input": {"sha256": digest}, "diagnostics": []}
            return subprocess.CompletedProcess(argv, 0, json.dumps(payload), "")

        temporary, source, output = diagnostics_capture(source_text)
        with temporary, mock.patch.object(preflight_prompt.subprocess, "run", side_effect=fake_run):
            state, exit_code = preflight_prompt.run_preflight(source, output, WORKSPACE_ROOT, {"continuation": "no", "evidence_round": "yes", "user_run_handoff": "no"})
        self.assertIn(exit_code, (0, 3), state)
        self.assertTrue(calls)
        self.assertTrue(all(not call[1]["shell"] for call in calls))

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


class HardeningRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = json.loads((SKILL_ROOT / "references/section_ownership.json").read_text())
        cls.live = preflight_prompt.live_repository_state(WORKSPACE_ROOT)
        cls.contexts = {"continuation": "no", "evidence_round": "yes", "user_run_handoff": "no"}

    def parsed_current(self, text: str | None = None):
        sections, diagnostics, preamble = preflight_prompt.parse_sections(text or current_prompt(), self.registry)
        fields, records = preflight_prompt.merge_semantic_fields(sections, diagnostics)
        return sections, fields, records, diagnostics, preamble

    def test_duplicate_top_level_nested_identical_and_conflicting_paths_block(self) -> None:
        cases = (
            "prompt_id: ONE\nprompt_id: ONE",
            "prompt_id: ONE\nprompt_id: TWO",
            "repo_locations:\n  meta_repo: /one\n  meta_repo: /one",
            "repo_locations:\n  meta_repo: /one\n  meta_repo: /two",
        )
        for mapping in cases:
            with self.subTest(mapping=mapping):
                text = f"# Prompt X\n\n## Task metadata\n\n```text\n{mapping}\n```\n"
                _, _, _, diagnostics, _ = self.parsed_current(text)
                self.assertIn("PROMPT-PREFLIGHT-E016", {item.id for item in diagnostics})

    def test_malformed_mapping_indentation_blocks(self) -> None:
        text = "# Prompt X\n\n## Task metadata\n\n```text\nbranch_policy:\n   meta_repo: continue_existing_branch\n```\n"
        _, _, _, diagnostics, _ = self.parsed_current(text)
        self.assertIn("PROMPT-PREFLIGHT-E017", {item.id for item in diagnostics})

    def test_complete_branch_policy_tuple_table_and_unsupported_policies(self) -> None:
        sections, fields, records, diagnostics, _ = self.parsed_current()
        preflight_prompt.complete_fields(fields, sections, "FIXTURE101", WORKSPACE_ROOT, self.live, self.contexts, diagnostics, records)
        self.assertNotIn("PROMPT-PREFLIGHT-E006", {item.id for item in diagnostics})
        branch = self.live["meta_repo"]["branch"]
        contradictory = current_prompt().replace(f"  meta_repo: {branch}\n  topeft: none", "  meta_repo: other_branch\n  topeft: none", 1)
        sections, fields, records, diagnostics, _ = self.parsed_current(contradictory)
        preflight_prompt.complete_fields(fields, sections, "FIXTURE101", WORKSPACE_ROOT, self.live, self.contexts, diagnostics, records)
        self.assertIn("PROMPT-PREFLIGHT-E006", {item.id for item in diagnostics})
        unsupported = current_prompt().replace("  meta_repo: continue_existing_branch", "  meta_repo: create_feature_branch_from_reference")
        sections, fields, records, diagnostics, _ = self.parsed_current(unsupported)
        preflight_prompt.complete_fields(fields, sections, "FIXTURE101", WORKSPACE_ROOT, self.live, self.contexts, diagnostics, records)
        self.assertIn("PROMPT-PREFLIGHT-E006", {item.id for item in diagnostics})

    def test_legacy_scalar_and_structured_baseline_forms(self) -> None:
        one_live = {"meta_repo": self.live["meta_repo"]}
        fields = {
            "branch_policy": "branch_policy:\n  meta_repo: continue_existing_branch",
            "current_checked_out_branch": f"current_checked_out_branch:\n  meta_repo: {one_live['meta_repo']['branch']}",
            "current_baseline_branch": f"current_baseline_branch:\n  meta_repo: {one_live['meta_repo']['branch']}",
            "reference_branch": "reference_branch:\n  meta_repo: none",
            "target_branch": f"target_branch:\n  meta_repo: {one_live['meta_repo']['branch']}",
            "feature_branch": "feature_branch:\n  meta_repo: none",
            "comparison_baseline": f"comparison_baseline: {one_live['meta_repo']['head']}",
        }
        diagnostics = []
        preflight_prompt.validate_branch_and_baseline(fields, [], one_live, diagnostics)
        self.assertEqual(diagnostics, [])
        sections, fields, records, diagnostics, _ = self.parsed_current()
        preflight_prompt.validate_branch_and_baseline(fields, records, self.live, diagnostics)
        self.assertNotIn("PROMPT-PREFLIGHT-E006", {item.id for item in diagnostics})

    def test_stale_head_subject_missing_and_unknown_repository_block(self) -> None:
        probes = (
            current_prompt().replace(self.live["meta_repo"]["head"], "0" * 40, 1),
            current_prompt().replace(self.live["meta_repo"]["subject"], "hostile subject", 1),
            current_prompt().replace("comparison_baseline:\n", "comparison_baseline:\n  unknown_repo:\n    expected_head: " + "a" * 40 + "\n", 1),
        )
        for text in probes:
            with self.subTest(probe=text[:40]):
                sections, fields, records, diagnostics, _ = self.parsed_current(text)
                preflight_prompt.complete_fields(fields, sections, "FIXTURE101", WORKSPACE_ROOT, self.live, self.contexts, diagnostics, records)
                self.assertIn("PROMPT-PREFLIGHT-E006", {item.id for item in diagnostics})

    def test_fixed_skill_owned_table_always_replaced(self) -> None:
        text = current_prompt().replace("prompt_mode: coding", "prompt_mode: coding\nworkspace_root: /hostile\nreport_path: /hostile/report\npatch_path: /hostile/patch\nevidence_validation_method: wrong")
        sections, fields, records, diagnostics, _ = self.parsed_current(text)
        completed, repairs = preflight_prompt.complete_fields(fields, sections, "FIXTURE101", WORKSPACE_ROOT, self.live, self.contexts, diagnostics, records)
        expected = {
            "workspace_root", "repo_locations", "current_checked_out_branch",
            "current_repository_heads", "evidence_requirements",
            "evidence_validation_method", "diagnostics_root", "report_path",
            "patch_path", "patch_kind_expected", "source_control_policy",
            "final_chat_deliverable", "classification_rules",
            "anti_self_certification_rules", "governance_binding_expectations",
        }
        self.assertTrue(expected.issubset(completed))
        self.assertNotIn("/hostile", completed["workspace_root"])
        self.assertEqual(preflight_prompt.scalar(completed["evidence_validation_method"]), preflight_prompt.EVIDENCE_COMPACT)
        for phase in preflight_prompt.EVIDENCE_SEQUENCE:
            self.assertIn(f"    - {phase}", completed["evidence_requirements"])
        self.assertTrue(expected.issubset({item["field"] for item in repairs} | {key for key in expected if key in fields and fields[key] == completed[key]}))

    def test_unknown_descriptive_and_normative_adversarial_corpora(self) -> None:
        safe = (
            "Historical motivation from the 2024 review.",
            "A narrative description of prior observations.",
            "The color palette is blue and green.",
            "This paragraph records an inert quotation from a paper.",
        )
        unsafe = (
            "You may edit any file in this workspace.",
            "Files **CAN** be modified.",
            "- Push the repository branch.",
            "Do not inspect production logs.",
            "NEVER delete sidecars.",
            "network_access: yes",
            "The worker is permitted to read outputs.",
            "Install dependencies.",
        )
        for body in safe:
            _, diagnostics, _ = preflight_prompt.parse_sections(f"# Prompt X\n\n## Reviewer intuition\n\n{body}\n", self.registry)
            self.assertNotIn("PROMPT-PREFLIGHT-E004", {item.id for item in diagnostics}, body)
        for body in unsafe:
            _, diagnostics, _ = preflight_prompt.parse_sections(f"# Prompt X\n\n## Special notes\n\n{body}\n", self.registry)
            self.assertIn("PROMPT-PREFLIGHT-E004", {item.id for item in diagnostics}, body)

    def test_complete_preamble_preservation_corpus(self) -> None:
        preambles = (
            "# Prompt X\n\n",
            "# Prompt X  \n\nPreamble sentinel.  \n\n",
            "# Prompt X\n\n<!-- comment -->\n### Nested\n\n",
            "# Prompt X\n\n````text\n## inert\n```\n````\n\n",
        )
        for preamble in preambles:
            with self.subTest(preamble=preamble):
                text = preamble + "## Goal\n\nbody\n"
                sections, diagnostics, observed = preflight_prompt.parse_sections(text, self.registry)
                canonical, manifest = preflight_prompt.canonicalize("X", "x", {}, sections, WORKSPACE_ROOT, self.live, diagnostics, observed)
                self.assertTrue(canonical.startswith(preamble))
                self.assertEqual(manifest[0]["source_sha256"], manifest[0]["canonical_sha256"])
                self.assertTrue(manifest[0]["preserved_exactly"])

    def test_transport_requirement_contradiction_corpus(self) -> None:
        safe = "Transport bytes are unavailable, not required, and not claimed."
        prohibited = (
            "Require exact identity with hidden chat transport bytes.",
            "VERIFY user-interface bytes are identical.",
            "acceptance: must match composer bytes",
            "Message transport bytes are required to be exact.",
            "Claim identity with unobservable original bytes.",
        )
        self.assertEqual(preflight_prompt.transport_diagnostics(safe), [])
        for statement in prohibited:
            for text in (statement, safe + "\n" + statement, statement + "\n" + safe, f"```text\n{statement}\n```"):
                with self.subTest(text=text):
                    self.assertEqual([item.id for item in preflight_prompt.transport_diagnostics(text)], ["PROMPT-PREFLIGHT-E015"])

    def test_closed_state_graph_all_edges_and_invalid_transition(self) -> None:
        for source, destination in self.registry["allowed_transitions"]:
            states = [source]
            preflight_prompt.transition_state(states, destination, self.registry, renderer_owned=False)
            self.assertEqual(states, [source, destination])
        with self.assertRaises(preflight_prompt.PreflightBlocked):
            preflight_prompt.transition_state(["source_captured"], "ready_for_same_session_execution", self.registry)
        with self.assertRaises(preflight_prompt.PreflightBlocked):
            preflight_prompt.transition_state(["ready_for_same_session_execution"], "execution_started", self.registry)

    def test_semantic_block_never_writes_canonical_prompt(self) -> None:
        text = current_prompt().replace("allowed_to_modify:", "declared_scope_note:", 1)
        temporary, source, output = diagnostics_capture(text)
        with temporary:
            state, exit_code = preflight_prompt.run_preflight(source, output, WORKSPACE_ROOT, self.contexts)
            self.assertEqual(exit_code, 3)
            self.assertEqual(state["current_state"], "blocked_semantic_ambiguity")
            self.assertNotIn("canonicalized", state["states_visited"])
            self.assertFalse((output / "canonical_prompt.md").exists())

    def test_source_and_output_path_confinement(self) -> None:
        with tempfile.TemporaryDirectory() as outside:
            source = Path(outside) / "source.md"
            source.write_text(current_prompt(), encoding="utf-8")
            state, _ = preflight_prompt.run_preflight(source, WORKSPACE_ROOT / "reports/diagnostics/path_test_output", WORKSPACE_ROOT, self.contexts)
            self.assertEqual(state["diagnostics"][0]["id"], "PROMPT-PREFLIGHT-E018")
        temporary, source, output = diagnostics_capture(current_prompt())
        with temporary:
            escaped = output.parent / ".." / ".." / "escape"
            state, _ = preflight_prompt.run_preflight(source, escaped, WORKSPACE_ROOT, self.contexts)
            self.assertEqual(state["diagnostics"][0]["id"], "PROMPT-PREFLIGHT-E018")
        temporary, source, output = diagnostics_capture(current_prompt())
        with temporary:
            link = source.parent / "link.md"
            link.symlink_to(source)
            state, _ = preflight_prompt.run_preflight(link, output, WORKSPACE_ROOT, self.contexts)
            self.assertEqual(state["diagnostics"][0]["id"], "PROMPT-PREFLIGHT-E018")
        temporary, source, output = diagnostics_capture(current_prompt())
        with temporary:
            nonregular = source.parent / "source_directory"
            nonregular.mkdir()
            state, _ = preflight_prompt.run_preflight(nonregular, output, WORKSPACE_ROOT, self.contexts)
            self.assertEqual(state["diagnostics"][0]["id"], "PROMPT-PREFLIGHT-E018")
        temporary, source, output = diagnostics_capture(current_prompt())
        with temporary:
            state, _ = preflight_prompt.run_preflight(source, source.parent, WORKSPACE_ROOT, self.contexts)
            self.assertIn(state["diagnostics"][0]["id"], {"PROMPT-PREFLIGHT-E012", "PROMPT-PREFLIGHT-E018"})
        temporary, source, output = diagnostics_capture(current_prompt())
        with temporary:
            real_parent = source.parent / "real_parent"
            real_parent.mkdir()
            linked_parent = source.parent / "linked_parent"
            linked_parent.symlink_to(real_parent, target_is_directory=True)
            state, _ = preflight_prompt.run_preflight(source, linked_parent / "output", WORKSPACE_ROOT, self.contexts)
            self.assertEqual(state["diagnostics"][0]["id"], "PROMPT-PREFLIGHT-E018")

    def test_generated_artifact_schema_is_enforced_after_reopening(self) -> None:
        temporary, source, output = diagnostics_capture(current_prompt("FIXTURE_SCHEMA"))
        with temporary:
            state, exit_code = preflight_prompt.run_preflight(source, output, WORKSPACE_ROOT, self.contexts)
            self.assertEqual(exit_code, 0, state)
            manifest_path = output / "section_manifest.json"
            manifest = json.loads(manifest_path.read_text())
            del manifest[0]["source_sha256"]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            diagnostics = preflight_prompt.validate_generated_artifacts(output, state)
            self.assertEqual([item.id for item in diagnostics], ["PROMPT-PREFLIGHT-E019"])

    def test_generated_artifact_reopening_failure_uses_stable_diagnostic(self) -> None:
        temporary, source, output = diagnostics_capture(current_prompt("FIXTURE_REOPEN"))
        with temporary:
            state, exit_code = preflight_prompt.run_preflight(source, output, WORKSPACE_ROOT, self.contexts)
            self.assertEqual(exit_code, 0, state)
            (output / "shared_value_manifest.json").write_text("{not json", encoding="utf-8")
            diagnostics = preflight_prompt.validate_generated_artifacts(output, state)
            self.assertEqual([item.id for item in diagnostics], ["PROMPT-PREFLIGHT-E013"])

    def test_csv_schema_helper_reopens_headers_and_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "evidence.csv"
            path.write_text("name,result\nprobe,pass\n", encoding="utf-8")
            self.assertEqual(preflight_prompt.validate_csv(path, ["name", "result"]), [])
            self.assertTrue(preflight_prompt.validate_csv(path, ["wrong", "header"]))


if __name__ == "__main__":
    unittest.main()
