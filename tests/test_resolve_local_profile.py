"""Focused contract checks for TOP26006_fw YAML installation profiles."""

import importlib.util
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("resolve_local_profile", ROOT / "tools" / "resolve_local_profile.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
SCHEMA = MODULE.read_yaml(ROOT / "config" / "local_profile.schema.yml")


def valid_profile(tmp_path):
    return {
        "profile_version": 1,
        "profile_name": "local-installation",
        "workspace_root": str(tmp_path),
        "evidence_root": "reports/diagnostics",
        "provider_procedure": "openai_codex",
        "tooling": {"command_wrapper": "codex-run.sh", "python_interpreter": "/outside/python"},
        "repositories": {"TOP26006_fw": {"path": ".", "remote_aliases": {"publication": "origin"}}},
    }


def test_example_is_structural_only():
    example = MODULE.read_yaml(ROOT / "config" / "local_profile.example.yml")
    assert MODULE.resolve(example, SCHEMA) == example
    with pytest.raises(MODULE.ProfileError, match="placeholder"):
        MODULE.resolve(example, SCHEMA, execution_ready=True)


def test_relative_resolution_and_absolute_spelling(tmp_path):
    profile = valid_profile(tmp_path)
    resolved = MODULE.resolve(profile, SCHEMA, execution_ready=True)
    assert resolved["workspace_root"] == str(tmp_path)
    assert resolved["evidence_root"] == str(tmp_path / "reports" / "diagnostics")
    assert resolved["tooling"]["command_wrapper"] == str(tmp_path / "codex-run.sh")
    assert resolved["tooling"]["python_interpreter"] == "/outside/python"
    assert resolved["repositories"]["TOP26006_fw"]["path"] == str(tmp_path)


def test_duplicate_keys_rejected(tmp_path):
    path = tmp_path / "duplicate.yml"
    path.write_text("profile_version: 1\nprofile_version: 1\n", encoding="utf-8")
    with pytest.raises(MODULE.ProfileError, match="duplicate mapping key"):
        MODULE.read_yaml(path)


@pytest.mark.parametrize("field,value", [("profile_version", 2), ("profile_version", True), ("tooling", "bad"), ("workspace_root", 4)])
def test_wrong_types_and_versions_rejected(tmp_path, field, value):
    profile = valid_profile(tmp_path)
    profile[field] = value
    with pytest.raises(MODULE.ProfileError):
        MODULE.resolve(profile, SCHEMA, execution_ready=True)


def test_missing_required_and_unknown_keys_rejected(tmp_path):
    profile = valid_profile(tmp_path)
    del profile["provider_procedure"]
    with pytest.raises(MODULE.ProfileError, match="required"):
        MODULE.resolve(profile, SCHEMA)
    profile = valid_profile(tmp_path)
    profile["validation_ceiling"] = "production_execution"
    with pytest.raises(MODULE.ProfileError, match="unknown key"):
        MODULE.resolve(profile, SCHEMA)
    profile = valid_profile(tmp_path)
    profile["tooling"]["unknown"] = "value"
    with pytest.raises(MODULE.ProfileError, match="unknown key"):
        MODULE.resolve(profile, SCHEMA)


@pytest.mark.parametrize("key", ["token", "password", "secret", "credential", "private_key", "api-key", "access_key", "refresh_token", "MySecretValue"])
def test_credential_keys_rejected_recursively(tmp_path, key):
    profile = valid_profile(tmp_path)
    profile["repositories"]["TOP26006_fw"]["remote_aliases"][key] = "do-not-print-this-value"
    with pytest.raises(MODULE.ProfileError, match="credential-like key") as caught:
        MODULE.resolve(profile, SCHEMA)
    assert "do-not-print-this-value" not in str(caught.value)


def test_absolute_outside_paths_allowed_and_relative_escape_rejected(tmp_path):
    profile = valid_profile(tmp_path)
    profile["repositories"]["TOP26006_fw"]["path"] = "/elsewhere/repository"
    assert MODULE.resolve(profile, SCHEMA, True)["repositories"]["TOP26006_fw"]["path"] == "/elsewhere/repository"
    profile["repositories"]["TOP26006_fw"]["path"] = "../escape"
    with pytest.raises(MODULE.ProfileError, match="escapes workspace_root"):
        MODULE.resolve(profile, SCHEMA, True)


def test_remote_alias_is_name_not_url(tmp_path):
    profile = valid_profile(tmp_path)
    profile["repositories"]["TOP26006_fw"]["remote_aliases"]["publication"] = "https://example.invalid/repo"
    with pytest.raises(MODULE.ProfileError, match="local Git alias"):
        MODULE.resolve(profile, SCHEMA)


def test_nonabsolute_workspace_rejected_for_execution(tmp_path):
    profile = valid_profile(tmp_path)
    profile["workspace_root"] = "relative/workspace"
    with pytest.raises(MODULE.ProfileError, match="absolute"):
        MODULE.resolve(profile, SCHEMA, True)


def test_cli_human_and_yaml_agree(tmp_path, capsys):
    path = tmp_path / "profile.yml"
    path.write_text(yaml.safe_dump(valid_profile(tmp_path)), encoding="utf-8")
    args = ["--profile", str(path), "--execution-ready"]
    assert MODULE.main(args + ["--format", "human"]) == 0
    human = capsys.readouterr().out
    assert MODULE.main(args + ["--format", "yaml"]) == 0
    machine = capsys.readouterr().out
    assert "workspace_root: " + str(tmp_path) in human
    assert yaml.safe_load(machine)["tooling"]["command_wrapper"] == str(tmp_path / "codex-run.sh")


def test_default_profile_uses_checkout_not_caller_cwd(tmp_path, monkeypatch, capsys):
    checkout = tmp_path / "checkout"
    (checkout / "tools").mkdir(parents=True)
    (checkout / "config").mkdir()
    (checkout / ".top26006").mkdir()
    (checkout / "config" / "local_profile.schema.yml").write_text(
        (ROOT / "config" / "local_profile.schema.yml").read_text(encoding="utf-8"), encoding="utf-8"
    )
    default = checkout / ".top26006" / "local_profile.yml"
    default.write_text(yaml.safe_dump(valid_profile(checkout)), encoding="utf-8")
    caller = tmp_path / "caller"
    caller.mkdir()
    monkeypatch.chdir(caller)
    monkeypatch.setattr(MODULE, "__file__", str(checkout / "tools" / "resolve_local_profile.py"))
    assert MODULE.main(["--execution-ready", "--format", "yaml"]) == 0
    assert yaml.safe_load(capsys.readouterr().out)["workspace_root"] == str(checkout)

    override = tmp_path / "override.yml"
    override.write_text(yaml.safe_dump(valid_profile(tmp_path)), encoding="utf-8")
    assert MODULE.main(["--profile", str(override), "--execution-ready", "--format", "yaml"]) == 0
    assert yaml.safe_load(capsys.readouterr().out)["workspace_root"] == str(tmp_path)

    default.unlink()
    with pytest.raises(SystemExit) as caught:
        MODULE.main(["--execution-ready"])
    assert caught.value.code == 2
    error = capsys.readouterr().err
    assert "local profile error" in error and str(default) in error
    assert "Traceback" not in error


def test_recursive_yaml_alias_fails_cleanly(tmp_path, capsys):
    path = tmp_path / "cyclic.yml"
    path.write_text("self: &loop\n  child: *loop\n", encoding="utf-8")
    with pytest.raises(MODULE.ProfileError, match="recursive YAML alias"):
        MODULE.read_yaml(path)
    with pytest.raises(SystemExit) as caught:
        MODULE.main(["--profile", str(path)])
    assert caught.value.code == 2
    error = capsys.readouterr().err
    assert "recursive YAML alias" in error
    assert "Traceback" not in error and "RecursionError" not in error
