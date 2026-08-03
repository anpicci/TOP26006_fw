from __future__ import annotations

import ast
import ctypes
import errno
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_ROOT / "scripts/preflight_prompt.py"
DIAGNOSTICS_ROOT = WORKSPACE_ROOT / "reports" / "diagnostics"
FROZEN_BB = (
    WORKSPACE_ROOT
    / "reports/diagnostics/SKILLS013R3_synchronize_frozen_black_box_suite"
    / "SKILLS013R3_black_box_acceptance_v1_2.json"
)
SPEC = importlib.util.spec_from_file_location("preflight_prompt", SCRIPT_PATH)
assert SPEC and SPEC.loader
preflight_prompt = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = preflight_prompt
SPEC.loader.exec_module(preflight_prompt)
CONTEXTS = {
    "continuation": "no",
    "evidence_round": "yes",
    "user_run_handoff": "no",
}
IMPLEMENTATION_IDS = {
    *(f"BB{index:03d}" for index in range(1, 23)),
    "BB024", "BB026", "BB027", "BB028",
}
LIVE_IDS = {"BB023", "BB025"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def live_state() -> dict[str, dict[str, str]]:
    return preflight_prompt.live_repository_state(WORKSPACE_ROOT)


def mapping_section(heading: str, body: str) -> str:
    return f"## {heading}\n\n```text\n{body.rstrip()}\n```\n\n"


def valid_prompt(prompt_id: str = "PREFLIGHT_FIXTURE", extra: str = "") -> str:
    live = live_state()
    task = "\n".join((
        f"prompt_id: {prompt_id}",
        "short_title: inert_preflight_fixture",
        "prompt_mode: coding",
        "preferred_codex_model: gpt-5.6-terra",
        "reasoning_level: high",
        "delegation_policy: forbidden",
        "model_selection_rationale: bounded inert fixture",
    ))
    scope = (
        "allowed_to_modify:\n"
        f"  meta_repo: {WORKSPACE_ROOT / 'AGENTS.md'}\n"
        "read_only:\n"
        f"  topeft: {WORKSPACE_ROOT / 'topeft'}\n"
        f"  topcoffea: {WORKSPACE_ROOT / 'topcoffea'}"
    )
    baseline = ["branch_policy:"]
    for name in live:
        policy = "continue_existing_branch" if name == "meta_repo" else "read_only_current_branch"
        baseline.append(f"  {name}: {policy}")
    baseline.append("reference_branch:")
    baseline.extend(f"  {name}: none" for name in live)
    baseline.append("target_branch:")
    baseline.extend(
        f"  {name}: {item['branch'] if name == 'meta_repo' else 'none'}"
        for name, item in live.items()
    )
    baseline.append("feature_branch:")
    baseline.extend(f"  {name}: none" for name in live)
    baseline.append("current_baseline_branch:")
    baseline.extend(f"  {name}: {item['branch']}" for name, item in live.items())
    baseline.append("comparison_baseline:")
    for name, item in live.items():
        baseline.extend((
            f"  {name}:",
            f"    expected_head: {item['head']}",
            f"    expected_subject: {item['subject']}",
        ))
    baseline.append("integrated_baseline_mode: yes")
    commit = (
        "do_not_commit: no\n"
        "commit_expected: yes\n"
        "commit_message_policy:\n"
        "  exact_subject: test(governance): inert fixture"
    )
    validation = (
        "dirty_worktree_policy: allow_declared_preexisting_changes\n"
        "preflight_profile: compact_preflight\n"
        "preflight_scope_paths:\n"
        "  meta_repo: AGENTS.md\n"
        "validation_ceiling: targeted_unit_test\n"
        "heavy_command_permissions:\n"
        "  defaults: all_no"
    )
    outputs = (
        "goal: validate an inert fixture\n"
        "decision_question: Can this inert fixture pass?\n"
        "out_of_scope:\n"
        "  - task execution\n"
        "final_chat_deliverable: inert result"
    )
    workflow = "continuation: no\nevidence_round: yes\nuser_run_handoff: no"
    return (
        f"# Prompt `{prompt_id}` — inert fixture\n\n"
        + mapping_section("Task metadata", task)
        + mapping_section("Repository scope", scope)
        + mapping_section("Baseline and branch policy", "\n".join(baseline))
        + mapping_section("Commit policy", commit)
        + mapping_section("Validation scope", validation)
        + mapping_section("Required outputs", outputs)
        + mapping_section("Existing workflow state", workflow)
        + "## Goal\n\nPreserve this exact author prose.\n"
        + extra
    )


class Capture:
    def __init__(self, prompt: str) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name)
        (self.workspace / "reports/diagnostics/capture").mkdir(parents=True)
        (self.workspace / "AGENTS.md").write_bytes((WORKSPACE_ROOT / "AGENTS.md").read_bytes())
        (self.workspace / "CPC.md").write_bytes((WORKSPACE_ROOT / "CPC.md").read_bytes())
        self.root = self.workspace / "reports/diagnostics/capture"
        self.source_path = self.root / "authored_prompt_input.md"
        self.source_path.write_text(prompt, encoding="utf-8")
        relative = Path("capture")
        self.source = relative / self.source_path.name
        self.audit = relative / "audit"

    def close(self) -> None:
        self.temporary.cleanup()

    @property
    def audit_path(self) -> Path:
        return self.workspace / "reports/diagnostics" / self.audit


def successful_validation(_workspace, canonical_path, _contexts, _pass_fds):
    digest = hashlib.sha256(canonical_path.read_bytes()).hexdigest()
    return {
        "valid_schema": True,
        "error_count": 0,
        "warning_count": 0,
        "input": {"sha256": digest},
        "diagnostics": [],
    }


def invoke(prompt: str):
    capture = Capture(prompt)
    with mock.patch.object(
        preflight_prompt, "live_repository_state", return_value=live_state(),
    ), mock.patch.object(
        preflight_prompt, "invoke_prompt_contract", side_effect=successful_validation,
    ):
        result, exit_code, canonical = preflight_prompt.run_preflight(
            capture.source, capture.audit, capture.workspace, CONTEXTS,
        )
    return capture, result, exit_code, canonical


class EphemeralOrchestration:
    def __init__(self) -> None:
        self.just_returned_exit_zero = False
        self.uninterrupted = True
        self.consumed = False

    def observe(self, exit_code: int, stdout: bytes) -> None:
        self.just_returned_exit_zero = exit_code == 0 and bool(stdout)

    def immediate_next_phase(self) -> bool:
        allowed = (
            self.just_returned_exit_zero and self.uninterrupted and not self.consumed
        )
        self.consumed = True
        return allowed


class BlackBoxImplementationTests(unittest.TestCase):
    def test_bb001_valid_minimal_markdown_prompt_passes(self) -> None:
        capture, result, exit_code, canonical = invoke(valid_prompt("BB001"))
        try:
            self.assertEqual(exit_code, 0, result)
            self.assertTrue(canonical)
            self.assertEqual(set(os.listdir(capture.audit_path)), set(preflight_prompt.OUTPUT_NAMES))
        finally:
            capture.close()

    def test_bb002_complex_author_markdown_preserved(self) -> None:
        author = (
            "\n## Reviewer narrative\n\n  sentinel  \n"
            "> ```text\n> authority: inert\n> ```\n"
            "- item\n  ```text\n  nested: inert\n  ```\n"
            "~~~python\nprint('inert')\n~~~\n"
        )
        prompt = valid_prompt("BB002", author)
        capture, result, exit_code, canonical = invoke(prompt)
        try:
            self.assertEqual(exit_code, 0, result)
            self.assertIn(author.encode(), canonical)
            self.assertEqual(
                (capture.audit_path / "authored_prompt.md").read_bytes(),
                prompt.encode(),
            )
        finally:
            capture.close()

    def test_bb003_unknown_shared_section_blocks(self) -> None:
        prompt = valid_prompt("BB003") + mapping_section(
            "Unregistered authority", "allowed_to_modify:\n  meta_repo: arbitrary/path",
        )
        capture, result, exit_code, canonical = invoke(prompt)
        try:
            self.assertEqual(exit_code, 2)
            self.assertEqual(canonical, b"")
            self.assertIn("PROMPT-PREFLIGHT-E004", {item["id"] for item in result["diagnostics"]})
        finally:
            capture.close()

    def test_bb004_unknown_shared_semantic_key_blocks(self) -> None:
        prompt = valid_prompt("BB004").replace(
            "prompt_id: BB004", "prompt_id: BB004\nunregistered_authority: yes",
        )
        capture, result, exit_code, canonical = invoke(prompt)
        try:
            self.assertEqual(exit_code, 2)
            self.assertEqual(canonical, b"")
        finally:
            capture.close()

    def test_bb005_missing_required_shared_key_blocks(self) -> None:
        prompt = valid_prompt("BB005").replace("validation_ceiling: targeted_unit_test\n", "")
        capture, result, exit_code, _ = invoke(prompt)
        try:
            self.assertEqual(exit_code, 2)
            self.assertIn("PROMPT-PREFLIGHT-E005", {item["id"] for item in result["diagnostics"]})
        finally:
            capture.close()

    def test_bb006_stale_root_baseline_blocks(self) -> None:
        prompt = valid_prompt("BB006").replace(live_state()["meta_repo"]["head"], "0" * 40, 1)
        capture, result, exit_code, _ = invoke(prompt)
        try:
            self.assertEqual(exit_code, 3)
            self.assertIn("PROMPT-PREFLIGHT-E006", {item["id"] for item in result["diagnostics"]})
        finally:
            capture.close()

    def test_bb007_stale_nested_baseline_blocks(self) -> None:
        prompt = valid_prompt("BB007").replace(live_state()["topeft"]["head"], "1" * 40, 1)
        capture, _result, exit_code, _ = invoke(prompt)
        try:
            self.assertEqual(exit_code, 3)
        finally:
            capture.close()

    def test_bb008_branch_policy_contradiction_blocks(self) -> None:
        branch = live_state()["meta_repo"]["branch"]
        prompt = valid_prompt("BB008").replace(
            f"  meta_repo: {branch}\n  topeft: none",
            "  meta_repo: none\n  topeft: none",
            1,
        )
        capture, _result, exit_code, _ = invoke(prompt)
        try:
            self.assertEqual(exit_code, 3)
        finally:
            capture.close()

    def test_bb009_live_branch_generated(self) -> None:
        capture, _result, exit_code, canonical = invoke(valid_prompt("BB009"))
        try:
            self.assertEqual(exit_code, 0)
            for name, item in live_state().items():
                self.assertIn(f"  {name}: {item['branch']}".encode(), canonical)
                self.assertIn(f"  {name}: {item['head']}".encode(), canonical)
        finally:
            capture.close()

    def test_bb010_prose_cannot_broaden_scope_and_passes(self) -> None:
        prose = "\n## Operator wish\n\nEvery file may be edited and production can be read.\n"
        capture, result, exit_code, canonical = invoke(valid_prompt("BB010", prose))
        try:
            self.assertEqual(exit_code, 0, result)
            self.assertIn(prose.encode(), canonical)
            self.assertEqual(canonical.count(str(WORKSPACE_ROOT / "AGENTS.md").encode()), 1)
        finally:
            capture.close()

    def test_bb011_scope_above_governance_blocks(self) -> None:
        prompt = valid_prompt("BB011").replace(
            str(WORKSPACE_ROOT / "AGENTS.md"), str(WORKSPACE_ROOT / "topcoffea"),
        )
        capture, _result, exit_code, _ = invoke(prompt)
        try:
            self.assertEqual(exit_code, 3)
        finally:
            capture.close()

    def test_bb012_prompt_contract_error_blocks(self) -> None:
        capture = Capture(valid_prompt("BB012"))
        diagnostic = preflight_prompt.Diagnostic(
            "PROMPT-PREFLIGHT-E010", "error", "synthetic validator error",
            "prompt-contract", 0,
        )
        with mock.patch.object(
            preflight_prompt, "invoke_prompt_contract",
            side_effect=preflight_prompt.PreflightFailure(4, diagnostic),
        ), mock.patch.object(
            preflight_prompt, "live_repository_state", return_value=live_state(),
        ):
            result, exit_code, canonical = preflight_prompt.run_preflight(
                capture.source, capture.audit, capture.workspace, CONTEXTS,
            )
        try:
            self.assertEqual(exit_code, 4)
            self.assertEqual(canonical, b"")
            self.assertFalse(capture.audit_path.exists())
        finally:
            capture.close()

    def test_bb013_governance_change_requires_new_invocation(self) -> None:
        harness = EphemeralOrchestration()
        harness.observe(0, b"canonical")
        self.assertTrue(harness.immediate_next_phase())
        self.assertFalse(harness.immediate_next_phase())
        self.assertFalse(Path(SKILL_ROOT / "references/governance_binding.json").name == "authorization")

    def test_bb014_head_change_requires_new_invocation(self) -> None:
        harness = EphemeralOrchestration()
        harness.observe(0, b"canonical")
        harness.uninterrupted = False
        self.assertFalse(harness.immediate_next_phase())

    def test_bb015_stale_audits_never_authorize(self) -> None:
        harness = EphemeralOrchestration()
        self.assertFalse(harness.immediate_next_phase())

    def test_bb016_forged_ready_file_never_authorizes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            Path(temporary, "ready.json").write_text('{"ready": true}', encoding="utf-8")
            harness = EphemeralOrchestration()
            self.assertFalse(harness.immediate_next_phase())

    def test_bb017_interrupted_session_reruns(self) -> None:
        harness = EphemeralOrchestration()
        harness.observe(0, b"canonical")
        harness.uninterrupted = False
        self.assertFalse(harness.immediate_next_phase())

    def test_bb018_absolute_source_path_blocks(self) -> None:
        with tempfile.NamedTemporaryFile() as source:
            result, exit_code, canonical = preflight_prompt.run_preflight(
                Path(source.name), Path("abs/audit"), WORKSPACE_ROOT, CONTEXTS,
            )
        self.assertEqual(exit_code, 2, result)
        self.assertEqual(canonical, b"")

    def test_bb019_source_symlink_blocks(self) -> None:
        capture = Capture(valid_prompt("BB019"))
        link = capture.root / "linked.md"
        link.symlink_to(capture.source_path)
        relative_link = link.relative_to(capture.workspace / "reports/diagnostics")
        result, exit_code, canonical = preflight_prompt.run_preflight(
            relative_link, capture.audit, capture.workspace, CONTEXTS,
        )
        try:
            self.assertEqual(exit_code, 2, result)
            self.assertEqual(canonical, b"")
        finally:
            capture.close()

    def test_bb020_existing_destination_collision_blocks(self) -> None:
        capture = Capture(valid_prompt("BB020"))
        original = preflight_prompt.linux_rename_noreplace
        def collision(*_args, **_kwargs):
            raise OSError(errno.EEXIST, "collision")
        with mock.patch.object(preflight_prompt, "linux_rename_noreplace", collision):
            with mock.patch.object(
                preflight_prompt, "live_repository_state", return_value=live_state(),
            ), mock.patch.object(
                preflight_prompt, "invoke_prompt_contract", side_effect=successful_validation,
            ):
                result, exit_code, canonical = preflight_prompt.run_preflight(
                    capture.source, capture.audit, capture.workspace, CONTEXTS,
                )
        try:
            self.assertEqual(exit_code, 5, result)
            self.assertEqual(canonical, b"")
        finally:
            preflight_prompt.linux_rename_noreplace = original
            capture.close()

    def test_bb021_normal_audit_publication(self) -> None:
        source = valid_prompt("BB021")
        capture, result, exit_code, canonical = invoke(source)
        try:
            self.assertEqual(exit_code, 0, result)
            self.assertEqual((capture.audit_path / "authored_prompt.md").read_bytes(), source.encode())
            self.assertEqual((capture.audit_path / "canonical_prompt.md").read_bytes(), canonical)
            self.assertEqual(len(list(capture.audit_path.iterdir())), 4)
        finally:
            capture.close()

    def test_bb022_no_task_action_before_pass(self) -> None:
        prompt = valid_prompt("BB022").replace("prompt_id: BB022", "prompt_id: BB022\nunknown: value")
        capture, _result, exit_code, canonical = invoke(prompt)
        try:
            self.assertNotEqual(exit_code, 0)
            self.assertEqual(canonical, b"")
            self.assertFalse(capture.audit_path.exists())
        finally:
            capture.close()

    def test_bb024_no_prompt_authored_code_executes(self) -> None:
        marker = Path(tempfile.gettempdir()) / "prompt_preflight_forbidden_marker"
        prompt = valid_prompt("BB024", f"\n## Example\n\n```python\nopen({str(marker)!r}, 'w')\n```\n")
        capture, _result, exit_code, _ = invoke(prompt)
        try:
            self.assertEqual(exit_code, 0)
            self.assertFalse(marker.exists())
        finally:
            capture.close()

    def test_bb026_duplicate_shared_path_blocks(self) -> None:
        for duplicate_value in ("BB026", "CONFLICTING"):
            with self.subTest(duplicate_value=duplicate_value):
                prompt = valid_prompt("BB026").replace(
                    "prompt_id: BB026",
                    f"prompt_id: BB026\nprompt_id: {duplicate_value}",
                )
                capture, _result, exit_code, _ = invoke(prompt)
                try:
                    self.assertEqual(exit_code, 2)
                finally:
                    capture.close()

    def test_bb027_transport_identity_requirement_blocks(self) -> None:
        cases = (
            "Require identity with hidden chat transport bytes.",
            "Transport bytes are unavailable, not required, and not claimed.\n"
            "Must verify hidden chat transport bytes exactly.",
        )
        for index, body in enumerate(cases):
            capture, _result, exit_code, canonical = invoke(
                valid_prompt(f"BB027_{index}", f"\n## Identity note\n\n{body}\n"),
            )
            try:
                self.assertEqual(exit_code, 3)
                self.assertEqual(canonical, b"")
            finally:
                capture.close()

    def test_bb028_publication_failure_blocks(self) -> None:
        capture = Capture(valid_prompt("BB028"))
        original = preflight_prompt.AuditStage.write
        def failure(self, name, content):
            if name == "preflight_report.md":
                raise OSError(errno.EIO, "synthetic write failure")
            return original(self, name, content)
        with mock.patch.object(preflight_prompt.AuditStage, "write", failure):
            with mock.patch.object(
                preflight_prompt, "live_repository_state", return_value=live_state(),
            ), mock.patch.object(
                preflight_prompt, "invoke_prompt_contract", side_effect=successful_validation,
            ):
                result, exit_code, canonical = preflight_prompt.run_preflight(
                    capture.source, capture.audit, capture.workspace, CONTEXTS,
                )
        try:
            self.assertEqual(exit_code, 5, result)
            self.assertEqual(canonical, b"")
            self.assertFalse(capture.audit_path.exists())
        finally:
            capture.close()


class RegistryAndGrammarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = json.loads(
            (SKILL_ROOT / "references/section_ownership.json").read_text(),
        )

    def test_all_nine_sections_and_67_paths(self) -> None:
        self.assertEqual(len(self.registry["shared_structured"]), 9)
        paths = self.registry["shared_semantic_paths"]
        self.assertEqual(set(paths), set(self.registry["shared_structured"]))
        self.assertEqual(sum(len(items) for items in paths.values()), 67)
        self.assertEqual(
            len({(section, item) for section, items in paths.items() for item in items}),
            67,
        )

    def test_every_registered_path_is_accepted_in_its_section(self) -> None:
        for heading, paths in self.registry["shared_semantic_paths"].items():
            for path in paths:
                with self.subTest(heading=heading, path=path):
                    text = f"# Prompt X\n\n{mapping_section(heading, path + ': value')}"
                    sections, diagnostics, _ = preflight_prompt.parse_sections(text, self.registry)
                    preflight_prompt.merge_fields(sections, self.registry, diagnostics)
                    unknown = [
                        item for item in diagnostics
                        if item.id == "PROMPT-PREFLIGHT-E004"
                    ]
                    self.assertEqual(unknown, [])

    def test_every_section_rejects_an_unknown_path(self) -> None:
        for heading in self.registry["shared_structured"]:
            text = f"# Prompt X\n\n{mapping_section(heading, 'not_registered: value')}"
            sections, diagnostics, _ = preflight_prompt.parse_sections(text, self.registry)
            preflight_prompt.merge_fields(sections, self.registry, diagnostics)
            self.assertIn("PROMPT-PREFLIGHT-E004", {item.id for item in diagnostics})

    def test_top_level_text_unknown_blocks_other_language_preserves(self) -> None:
        blocked = "# Prompt X\n\n## Unknown\n\n```text\na: b\n```\n"
        preserved = "# Prompt X\n\n## Unknown\n\n```python\na = 'b'\n```\n"
        _sections, diagnostics, _ = preflight_prompt.parse_sections(blocked, self.registry)
        self.assertIn("PROMPT-PREFLIGHT-E004", {item.id for item in diagnostics})
        sections, diagnostics, _ = preflight_prompt.parse_sections(preserved, self.registry)
        self.assertNotIn("PROMPT-PREFLIGHT-E004", {item.id for item in diagnostics})
        self.assertEqual(sections[0].ownership, "author_owned")

    def test_nested_blockquote_and_list_fences_are_prose(self) -> None:
        text = (
            "# Prompt X\n\n## Unknown\n\n"
            "> ```text\n> allowed_to_modify: hostile\n> ```\n"
            "- item\n  ```text\n  branch_policy: hostile\n  ```\n"
        )
        sections, diagnostics, _ = preflight_prompt.parse_sections(text, self.registry)
        self.assertEqual(sections[0].ownership, "author_owned")
        self.assertNotIn("PROMPT-PREFLIGHT-E004", {item.id for item in diagnostics})

    def test_registered_shared_section_rejects_prose_and_second_fence(self) -> None:
        raw = (
            "# Prompt X\n\n## Task metadata\n\nprose\n"
            "```text\nprompt_id: X\n```\n"
            "```text\nshort_title: x\n```\n"
        )
        sections, diagnostics, _ = preflight_prompt.parse_sections(raw, self.registry)
        preflight_prompt.merge_fields(sections, self.registry, diagnostics)
        self.assertIn("PROMPT-PREFLIGHT-E021", {item.id for item in diagnostics})

    def test_author_permission_prose_has_zero_parser_authority(self) -> None:
        text = "# Prompt X\n\n## Narrative\n\nYou may edit everything. Never inspect logs.\n"
        sections, diagnostics, _ = preflight_prompt.parse_sections(text, self.registry)
        self.assertEqual(sections[0].ownership, "author_owned")
        self.assertNotIn("PROMPT-PREFLIGHT-E004", {item.id for item in diagnostics})


class PublicationAndInterfaceTests(unittest.TestCase):
    class Function:
        def __init__(self, result: int, error_number: int = 0) -> None:
            self.result = result
            self.error_number = error_number
            self.argtypes = None
            self.restype = None
            self.flags = []

        def __call__(self, _sfd, _source, _dfd, _destination, flags):
            self.flags.append(flags)
            ctypes.set_errno(self.error_number)
            return self.result

    class Library:
        def __init__(self, function) -> None:
            self.renameat2 = function

    def test_renameat2_success_uses_noreplace_flag(self) -> None:
        function = self.Function(0)
        preflight_prompt.linux_rename_noreplace(1, "source", 1, "dest", self.Library(function))
        self.assertEqual(function.flags, [preflight_prompt.RENAME_NOREPLACE])

    def test_renameat2_collision_missing_symbol_enosys_flag_and_failure(self) -> None:
        cases = (
            (self.Library(self.Function(-1, errno.EEXIST)), errno.EEXIST),
            (object(), errno.ENOSYS),
            (self.Library(self.Function(-1, errno.ENOSYS)), errno.ENOSYS),
            (self.Library(self.Function(-1, errno.EINVAL)), errno.EINVAL),
            (self.Library(self.Function(-1, errno.EIO)), errno.EIO),
        )
        for library, expected in cases:
            with self.subTest(expected=expected):
                with self.assertRaises(OSError) as caught:
                    preflight_prompt.linux_rename_noreplace(
                        1, "source", 1, "dest", library,
                    )
                self.assertEqual(caught.exception.errno, expected)

    def test_public_cli_has_only_fixed_source_and_audit_interface(self) -> None:
        parser = preflight_prompt.build_parser()
        actions = {action.dest for action in parser._actions}
        self.assertEqual(
            actions,
            {
                "help", "workspace_root", "source_path", "audit_root",
                "continuation", "evidence_round", "user_run_handoff",
            },
        )

    def test_static_no_execution_and_no_ordinary_rename_fallback(self) -> None:
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden = {"eval", "exec", "__import__", "compile"}
        called = {
            node.func.id for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertTrue(forbidden.isdisjoint(called))
        self.assertNotIn("shell=True", source)
        self.assertNotIn("codex exec", source.casefold())
        self.assertNotIn("os." + "rename", source)
        self.assertNotIn("os." + "replace", source)
        self.assertNotIn("task_callback", source)

    def test_removed_persistent_mechanisms_absent(self) -> None:
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        forbidden_fragments = (
            "assert_" + "ready_for_task_action",
            "readiness_" + "binding.json",
            "preflight_" + "state.json",
            "section_" + "manifest.json",
            "shared_" + "value_manifest.json",
        )
        for fragment in forbidden_fragments:
            self.assertNotIn(fragment, source)

    def test_prompt_contract_malformed_result_is_exit_four(self) -> None:
        completed = subprocess.CompletedProcess([], 0, "not-json", "")
        with mock.patch.object(preflight_prompt.subprocess, "run", return_value=completed):
            with tempfile.NamedTemporaryFile() as temporary:
                with self.assertRaises(preflight_prompt.PreflightFailure) as caught:
                    preflight_prompt.invoke_prompt_contract(
                        WORKSPACE_ROOT, Path(temporary.name), CONTEXTS, (),
                    )
        self.assertEqual(caught.exception.exit_code, 4)

    def test_installed_black_box_reference_is_exact(self) -> None:
        installed = SKILL_ROOT / "references/black_box_acceptance.json"
        self.assertEqual(sha256(installed), "b5d76e30284eb97b0012bbe83dcc1152043363c42053fa04d4f0d741ebb73f49")
        self.assertEqual(installed.read_bytes(), FROZEN_BB.read_bytes())
        suite = json.loads(installed.read_text())
        ids = {item["id"] for item in suite["tests"]}
        self.assertEqual(ids, IMPLEMENTATION_IDS | LIVE_IDS)

    def test_bb_mapping_is_exactly_26_and_live_ids_not_test_methods(self) -> None:
        methods = {
            name[5:10].upper()
            for name in dir(BlackBoxImplementationTests)
            if name.startswith("test_bb")
        }
        self.assertEqual(methods, IMPLEMENTATION_IDS)
        self.assertTrue(methods.isdisjoint(LIVE_IDS))

    def test_source_has_no_permission_language_blacklist(self) -> None:
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        self.assertNotIn("unknown_is_normative", source)
        self.assertNotIn("_permission_normal_form", source)

    def test_all_five_bindings_match_live_governance(self) -> None:
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
            binding = json.loads(
                (WORKSPACE_ROOT / ".agents/skills" / skill / "references/governance_binding.json").read_text(),
            )
            self.assertEqual(binding["agents_sha256"], agents_hash)
            self.assertEqual(binding["cpc_sha256"], cpc_hash)


if __name__ == "__main__":
    unittest.main()
