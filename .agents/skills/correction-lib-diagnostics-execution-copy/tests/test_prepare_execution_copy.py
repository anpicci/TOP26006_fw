import contextlib
import csv
import hashlib
import importlib.util
import inspect
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("copy_tool", ROOT / "scripts/prepare_execution_copy.py")
tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tool)


class CopyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.src = self.base / "sources"; self.src.mkdir()
        self.dst = self.base / "diagnostics"; self.dst.mkdir()
        self.file = self.src / "wrapper.sh"
        self.file.write_bytes(b"#!/bin/sh\ndry_run=false\n")
        self.manifest_file = self.base / "manifest.json"

    def tearDown(self):
        self.tmp.cleanup()

    def manifest(self, **updates):
        entry = {
            "entry_id": "wrapper", "source_path": str(self.file),
            "destination_path": "wrapper.sh", "copy_mode": "exact_copy",
            "expected_source_sha256": hashlib.sha256(self.file.read_bytes()).hexdigest(),
            "expected_source_state": "any_recorded", "transformations": [],
            "preserve_executable_bit": False,
        }
        entry.update(updates)
        return {
            "manifest_version": "1.0.0", "copy_id": "copy_one",
            "title": "Synthetic inert copy", "source_roots": [str(self.src)],
            "destination_root": str(self.dst), "entries": [entry],
            "limits": {"max_entries": 64, "max_file_bytes": 16777216, "max_total_bytes": 67108864},
            "secret_policy": {"mode": "block_documented_matches_no_redaction", "additional_forbidden_path_components": []},
            "provenance": {"record_git_when_available": True, "require_working_tree_sha256": True, "require_source_mode": True},
            "execution_boundary": {"copy_requested": True, "execution_not_authorized": True, "render_execution_command": False},
        }

    def execute(self, manifest, validate=False):
        self.manifest_file.write_text(json.dumps(manifest))
        return tool.validate_and_prepare(self.manifest_file, validate)

    def diag(self, manifest, diagnostic, code=None, validate=True):
        with self.assertRaises(tool.CopyError) as caught:
            self.execute(manifest, validate)
        self.assertIn(diagnostic, [d["diagnostic_id"] for d in caught.exception.diagnostics])
        if code is not None:
            self.assertEqual(caught.exception.exit_code, code)
        return caught.exception

    def test_renderer_version_is_1_0_1(self):
        self.assertEqual(tool.RENDERER_VERSION, "1.0.1")

    def test_schema_and_manifest_versions_remain_1_0_0(self):
        schema = json.loads((ROOT / "references/copy_schema.json").read_text())
        self.assertEqual(tool.SCHEMA_VERSION, "1.0.0")
        self.assertEqual(tool.MANIFEST_VERSION, "1.0.0")
        self.assertEqual(schema["schema_version"], "1.0.0")
        self.assertEqual(schema["manifest_version"], "1.0.0")

    def test_additional_property(self):
        m = self.manifest(); m["extra"] = True
        self.diag(m, "TYPE001", 2)

    def test_absolute_source(self):
        self.diag(self.manifest(source_path="relative"), "PATH001", 2)

    def test_secret_policy_immutable(self):
        m = self.manifest(); m["secret_policy"]["mode"] = "disabled"
        self.diag(m, "SECRET001", 3)

    def test_duplicate_id(self):
        m = self.manifest(); m["entries"].append(dict(m["entries"][0], destination_path="two"))
        self.diag(m, "TYPE001", 2)

    def test_duplicate_destination(self):
        m = self.manifest(); m["entries"].append(dict(m["entries"][0], entry_id="two"))
        self.diag(m, "PATH002", 2)

    def test_source_escape(self):
        other = self.base / "other"; other.write_text("x\n")
        self.diag(self.manifest(source_path=str(other), expected_source_sha256=hashlib.sha256(other.read_bytes()).hexdigest()), "PATH001", 3)

    def test_destination_escape(self):
        self.diag(self.manifest(destination_path="../x"), "PATH002", 2)

    def test_destination_inside_source(self):
        m = self.manifest(); m["destination_root"] = str(self.src)
        self.diag(m, "PATH003", 3)

    def test_source_symlink(self):
        target = self.src / "target"; target.write_text("x\n")
        link = self.src / "link"; link.symlink_to(target)
        self.diag(self.manifest(source_path=str(link), expected_source_sha256=hashlib.sha256(target.read_bytes()).hexdigest()), "PATH004", 3)

    def test_source_root_symlink(self):
        real = self.base / "real"; real.mkdir()
        source = real / "x"; source.write_text("x\n")
        link = self.base / "linked"; link.symlink_to(real, target_is_directory=True)
        m = self.manifest(source_path=str(link / "x"), expected_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
        m["source_roots"] = [str(link)]
        self.diag(m, "PATH004", 3)

    def test_destination_symlink(self):
        real = self.base / "real_dst"; real.mkdir()
        link = self.base / "linked_dst"; link.symlink_to(real, target_is_directory=True)
        m = self.manifest(); m["destination_root"] = str(link)
        self.diag(m, "PATH004", 3)

    def test_hard_link(self):
        os.link(self.file, self.src / "other")
        self.diag(self.manifest(), "TYPE003", 3)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "mkfifo unavailable")
    def test_special_file(self):
        fifo = self.src / "fifo"; os.mkfifo(fifo)
        self.diag(self.manifest(source_path=str(fifo), expected_source_sha256="0" * 64), "TYPE001", 3)

    def test_binary(self):
        self.file.write_bytes(b"\xff")
        self.diag(self.manifest(expected_source_sha256=hashlib.sha256(self.file.read_bytes()).hexdigest()), "TYPE002", 3)

    def test_hash(self):
        self.diag(self.manifest(expected_source_sha256="0" * 64), "HASH001", 3)

    def test_state_mismatch(self):
        self.diag(self.manifest(expected_source_state="tracked_clean"), "PROVENANCE001", 3)

    def test_file_limit(self):
        m = self.manifest(); m["limits"]["max_file_bytes"] = 2
        self.diag(m, "SIZE001", 3)

    def test_total_limit(self):
        m = self.manifest(); m["limits"]["max_total_bytes"] = 2
        self.diag(m, "SIZE002", 3)

    def test_entry_limit(self):
        m = self.manifest(); m["limits"]["max_entries"] = 1
        m["entries"].append(dict(m["entries"][0], entry_id="two", destination_path="two"))
        self.diag(m, "SIZE002", 3)

    def test_secret_path(self):
        folder = self.src / ".ssh"; folder.mkdir()
        secret = folder / "note"; secret.write_text("x\n")
        self.diag(self.manifest(source_path=str(secret), expected_source_sha256=hashlib.sha256(secret.read_bytes()).hexdigest()), "SECRET001", 3)

    def test_credential_name(self):
        secret = self.src / "credentials.json"; secret.write_text("{}\n")
        self.diag(self.manifest(source_path=str(secret), expected_source_sha256=hashlib.sha256(secret.read_bytes()).hexdigest()), "SECRET003", 3)

    def test_private_key_header(self):
        self.file.write_text("-----BEGIN PRIVATE KEY-----\nx\n")
        self.diag(self.manifest(expected_source_sha256=hashlib.sha256(self.file.read_bytes()).hexdigest()), "SECRET002", 3)

    def test_additive_secret(self):
        folder = self.src / "internal"; folder.mkdir()
        source = folder / "note"; source.write_text("x\n")
        m = self.manifest(source_path=str(source), expected_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
        m["secret_policy"]["additional_forbidden_path_components"] = ["internal"]
        self.diag(m, "SECRET001", 3)

    def test_exact_copy_zero_diff(self):
        self.execute(self.manifest())
        final = self.dst / "copy_one"
        self.assertEqual((final / "materialized/wrapper.sh").read_bytes(), self.file.read_bytes())
        self.assertEqual((final / "copy_diff.patch").read_bytes(), b"")

    def test_transform_order_newlines_diff(self):
        m = self.manifest(copy_mode="declared_text_transform", transformations=[
            {"operation": "exact_text_replacement", "old": "dry_run=false", "new": "dry_run=true", "expected_match_count": 1},
            {"operation": "exact_text_replacement", "old": "#!/bin/sh", "new": "#!/usr/bin/env sh", "expected_match_count": 1},
        ])
        self.execute(m)
        final = self.dst / "copy_one"
        self.assertEqual((final / "materialized/wrapper.sh").read_bytes(), b"#!/usr/bin/env sh\ndry_run=true\n")
        self.assertIn("+dry_run=true", (final / "copy_diff.patch").read_text())

    def test_transform_count(self):
        m = self.manifest(copy_mode="declared_text_transform", transformations=[
            {"operation": "exact_text_replacement", "old": "missing", "new": "x", "expected_match_count": 1}
        ])
        self.diag(m, "TRANSFORM002", 3)
        self.assertFalse((self.dst / "copy_one").exists())

    def test_modes(self):
        os.chmod(self.file, 0o6777)
        self.execute(self.manifest(expected_source_sha256=hashlib.sha256(self.file.read_bytes()).hexdigest()))
        self.assertEqual(stat.S_IMODE((self.dst / "copy_one/materialized/wrapper.sh").stat().st_mode), 0o640)

    def test_executable_mode_and_not_run(self):
        marker = self.base / "ran"
        self.file.write_text(f"#!/bin/sh\ntouch {marker}\n"); os.chmod(self.file, 0o755)
        m = self.manifest(preserve_executable_bit=True, expected_source_sha256=hashlib.sha256(self.file.read_bytes()).hexdigest())
        self.execute(m)
        self.assertEqual(stat.S_IMODE((self.dst / "copy_one/materialized/wrapper.sh").stat().st_mode), 0o750)
        self.assertFalse(marker.exists())

    def test_final_collision_repeat(self):
        m = self.manifest(); self.execute(m)
        self.diag(m, "COLLISION001", 3)

    def _final_collision_race(self, object_kind):
        original = tool._rename_noreplace_at
        final = self.dst / "copy_one"
        state = {}

        def inject(directory_fd, staging_name, destination_name):
            if object_kind == "directory":
                final.mkdir()
                state["inode"] = final.lstat().st_ino
            else:
                target = self.base / "race_target"
                target.write_text("unchanged\n")
                final.symlink_to(target)
                state["target"] = os.readlink(final)
                state["target_bytes"] = target.read_bytes()
            return original(directory_fd, staging_name, destination_name)

        with mock.patch.object(tool, "_rename_noreplace_at", side_effect=inject):
            error = self.diag(self.manifest(), "COLLISION001", 5, False)
        return error, final, state

    def test_final_publication_collision_race_does_not_replace_empty_directory(self):
        _, final, state = self._final_collision_race("directory")
        self.assertTrue(final.is_dir())
        self.assertEqual(final.lstat().st_ino, state["inode"])
        self.assertEqual(list(final.iterdir()), [])

    def test_final_publication_collision_race_does_not_replace_symlink(self):
        _, final, state = self._final_collision_race("symlink")
        self.assertTrue(final.is_symlink())
        self.assertEqual(os.readlink(final), state["target"])
        self.assertEqual(final.resolve().read_bytes(), state["target_bytes"])

    def test_final_publication_collision_preserves_incomplete_tree(self):
        error, _, _ = self._final_collision_race("directory")
        incomplete = Path(error.summary["incomplete_root"])
        self.assertTrue(incomplete.is_dir())
        validation = json.loads((incomplete / "copy_validation.json").read_text())
        self.assertFalse(validation["materialization_completed"])
        self.assertEqual(validation["diagnostics"][0]["diagnostic_id"], "COLLISION001")

    def test_final_publication_collision_returns_exit_5(self):
        error, _, _ = self._final_collision_race("directory")
        self.assertEqual(error.exit_code, 5)

    def test_rename_noreplace_unavailable_fails_closed(self):
        with mock.patch.object(
            tool.ctypes,
            "CDLL",
            side_effect=OSError("renameat2 unavailable"),
        ):
            error = self.diag(self.manifest(), "RENDER001", 5, False)
        self.assertTrue(Path(error.summary["incomplete_root"]).is_dir())
        self.assertFalse((self.dst / "copy_one").exists())

    def test_no_ordinary_rename_fallback(self):
        source = inspect.getsource(tool._rename_noreplace_at)
        self.assertNotIn("os.rename", source)
        self.assertNotIn("os.replace", source)
        materialize_source = inspect.getsource(tool.materialize)
        self.assertIn("_rename_noreplace_at", materialize_source)
        self.assertNotIn("os.rename(", materialize_source)

    def _hard_link_race(self):
        original = tool._recheck_source
        link = self.src / "late_link"

        def inject(prepared):
            if not link.exists():
                os.link(self.file, link)
            return original(prepared)

        with mock.patch.object(tool, "_recheck_source", side_effect=inject):
            error = self.diag(self.manifest(), "TYPE003", 5, False)
        return error, link

    def test_hard_link_added_before_publication_is_rejected(self):
        error, link = self._hard_link_race()
        self.assertEqual(error.exit_code, 5)
        self.assertTrue(link.exists())
        self.assertFalse((self.dst / "copy_one").exists())

    def test_hard_link_race_preserves_incomplete_tree(self):
        error, _ = self._hard_link_race()
        incomplete = Path(error.summary["incomplete_root"])
        self.assertTrue(incomplete.is_dir())
        validation = json.loads((incomplete / "copy_validation.json").read_text())
        self.assertFalse(validation["copy_materialization_completed"])
        self.assertEqual(validation["diagnostics"][0]["diagnostic_id"], "TYPE003")

    def test_read_stability_includes_nlink(self):
        self.assertIn('"st_nlink"', inspect.getsource(tool._read_stable))

    def test_prepublication_checks_nlink(self):
        source = inspect.getsource(tool._recheck_source)
        self.assertIn("info.st_nlink != 1", source)
        self.assertIn('"TYPE003"', source)

    def test_staging_collision(self):
        (self.dst / ".staging_copy_one_dead").mkdir()
        with mock.patch.object(tool.secrets, "token_hex", return_value="dead"):
            self.diag(self.manifest(), "COLLISION002", 3, False)

    def test_validate_only_no_writes(self):
        summary = self.execute(self.manifest(), True)
        self.assertFalse(summary["materialization_requested"])
        self.assertEqual(list(self.dst.iterdir()), [])

    def test_source_changes_during_read(self):
        with mock.patch.object(tool, "_read_stable", side_effect=RuntimeError("changed")):
            self.diag(self.manifest(), "HASH001", 3)

    def test_source_changes_before_publication(self):
        d = tool.make_diag("HASH001", "changed", entry_id="wrapper")
        with mock.patch.object(tool, "_recheck_source", return_value=d):
            error = self.diag(self.manifest(), "HASH001", 5, False)
        self.assertFalse((self.dst / "copy_one").exists())
        self.assertTrue(Path(error.summary["incomplete_root"]).exists())

    def test_write_failure_preserves_incomplete(self):
        original = tool._write_exclusive_at
        count = {"n": 0}
        def fail(*args, **kwargs):
            count["n"] += 1
            if count["n"] == 2: raise OSError("synthetic")
            return original(*args, **kwargs)
        with mock.patch.object(tool, "_write_exclusive_at", side_effect=fail):
            with self.assertRaises(tool.CopyError) as caught: self.execute(self.manifest())
        self.assertEqual(caught.exception.exit_code, 5)
        self.assertTrue(Path(caught.exception.summary["incomplete_root"]).name.startswith(".incomplete_"))

    def test_generated_consistency(self):
        self.execute(self.manifest())
        final = self.dst / "copy_one"
        validation = json.loads((final / "copy_validation.json").read_text())
        provenance = json.loads((final / "copy_provenance.json").read_text())
        with (final / "copy_inventory.csv").open() as stream:
            inventory = list(csv.DictReader(stream))
        self.assertEqual(inventory[0]["destination_sha256"], provenance["entries"][0]["destination_sha256"])
        for path, digest in validation["artifact_hashes"].items():
            self.assertEqual(hashlib.sha256((final / path).read_bytes()).hexdigest(), digest)

    def init_git(self):
        subprocess.run(["git", "init", "-q"], cwd=self.src, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=self.src, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.src, check=True)
        subprocess.run(["git", "add", "wrapper.sh"], cwd=self.src, check=True)
        subprocess.run(["git", "commit", "-qm", "test"], cwd=self.src, check=True)

    def test_git_clean(self):
        self.init_git(); self.execute(self.manifest(expected_source_state="tracked_clean"))
        p = json.loads((self.dst / "copy_one/copy_provenance.json").read_text())["entries"][0]
        self.assertEqual(p["tracked_state"], "tracked_clean"); self.assertTrue(p["git_blob_hash"])

    def test_git_modified(self):
        self.init_git(); self.file.write_text("modified\n")
        m = self.manifest(expected_source_state="tracked_modified", expected_source_sha256=hashlib.sha256(self.file.read_bytes()).hexdigest())
        self.execute(m)
        self.assertEqual(json.loads((self.dst / "copy_one/copy_provenance.json").read_text())["entries"][0]["tracked_state"], "tracked_modified")

    def test_git_untracked(self):
        self.init_git(); other = self.src / "new"; other.write_text("new\n")
        m = self.manifest(source_path=str(other), expected_source_sha256=hashlib.sha256(other.read_bytes()).hexdigest(), expected_source_state="untracked")
        self.execute(m)
        self.assertEqual(json.loads((self.dst / "copy_one/copy_provenance.json").read_text())["entries"][0]["tracked_state"], "untracked")

    def test_outside_git_warning(self):
        record = {
            "repository_root": None, "repository_relative_path": None,
            "git_branch_record": None, "git_commit_record": None,
            "tracked_state": "outside_git", "git_blob_hash": None,
        }
        warning = tool.make_diag("PROVENANCE002", "Optional Git provenance is unavailable.", field="git")
        with mock.patch.object(tool, "collect_git_provenance", return_value=(record, warning)):
            summary = self.execute(self.manifest(expected_source_state="outside_git"), True)
        self.assertEqual(summary["diagnostics"][0]["diagnostic_id"], "PROVENANCE002")

    def test_unrelated_workspace_policy_content_does_not_disable_copy(self):
        (self.base / "workspace_policy.txt").write_text("changed independently\n")
        summary = self.execute(self.manifest(), True)
        self.assertEqual(summary["error_count"], 0)

    def test_execution_fields_rejected(self):
        for field in tool.FORBIDDEN_FIELDS:
            m = self.manifest(); m[field] = "x"
            self.diag(m, "EXECUTION001", 3)

    def test_cli_surface(self):
        options = {x for action in tool.parser()._actions for x in action.option_strings}
        self.assertTrue(options.isdisjoint({"--execute", "--run", "--submit", "--retry", "--resume", "--overwrite", "--cleanup", "--shell", "--command"}))
        self.assertNotIn("--governance-" + "binding", options)

    def test_local_safety_failure_is_copy_operation_local(self):
        error = self.diag(self.manifest(expected_source_sha256="0" * 64), "HASH001", 3)
        self.assertEqual(error.summary, {})
        self.assertNotIn("workflow_authorized", error.summary)
        self.assertNotIn("workflow_revoked", error.summary)

    def test_human_json_equivalence(self):
        self.manifest_file.write_text(json.dumps(self.manifest(expected_source_sha256="0" * 64)))
        human = io.StringIO(); machine = io.StringIO()
        with contextlib.redirect_stdout(human): hcode = tool.main(["--validate-only", str(self.manifest_file)])
        with contextlib.redirect_stdout(machine): jcode = tool.main(["--validate-only", "--format", "json", str(self.manifest_file)])
        payload = json.loads(machine.getvalue())
        self.assertEqual((hcode, jcode), (3, 3))
        self.assertIn(payload["diagnostics"][0]["diagnostic_id"], human.getvalue())

    def test_stable_diagnostic_order(self):
        with self.assertRaises(tool.CopyError) as caught:
            self.execute(self.manifest(source_path="relative", destination_path="../x", expected_source_sha256="bad"), True)
        ranks = [tool.DIAGNOSTIC_INDEX[x["diagnostic_id"]] for x in caught.exception.diagnostics]
        self.assertEqual(ranks, sorted(ranks))

    def test_fixture_inventory(self):
        fixtures = {x.stem for x in (ROOT / "tests/fixtures").rglob("*.json")}
        required = {
            "valid_exact_single_file", "valid_multiple_explicit_files", "valid_declared_replacement",
            "valid_executable_bit_preserved", "valid_modified_tracked_source_recorded", "valid_untracked_source_recorded",
            "invalid_source_escape", "invalid_destination_escape", "invalid_destination_exists",
            "invalid_source_hash_mismatch", "invalid_replacement_count", "invalid_symlink",
            "invalid_hard_link", "invalid_special_file", "invalid_binary_when_disallowed",
            "invalid_oversize", "invalid_too_many_files", "invalid_private_key_path",
            "invalid_private_key_header", "invalid_destination_inside_source",
            "invalid_source_equals_destination", "invalid_undeclared_execution",
            "final_publication_collision_race",
            "hard_link_added_before_publication",
        }
        self.assertTrue(required <= fixtures)


if __name__ == "__main__":
    unittest.main()
