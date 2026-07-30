#!/usr/bin/env python3
"""Validate and render a manual production handoff without executing it."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Any


RENDERER_VERSION = "1.0.1"
SCHEMA_VERSION = "1.0.0"
EXIT_OK = 0
EXIT_VALIDATION = 2
EXIT_UNSAFE = 3
EXIT_GOVERNANCE = 4
EXIT_RENDER = 5
COMMAND_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
ENV_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
VARIABLE_RE = re.compile(r"\$(?:\{[A-Za-z_][A-Za-z0-9_]*\}|[A-Za-z_][A-Za-z0-9_]*)")
GLOB_RE = re.compile(r"[*?\[\]]")
SECRET_KEY_RE = re.compile(
    r"(?i)(?:^|_)(?:password|passwd|secret|token|private_key|api_key|credential)(?:$|_)"
)
SECRET_VALUE_RE = re.compile(
    r"(?i)(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{12,}|"
    r"(?:password|passwd|secret|token|api[_-]?key)\s*[:=]\s*\S+)"
)
SHELL_EXECUTABLES = {"bash", "sh", "dash", "zsh", "ksh", "fish", "csh", "tcsh"}
DELETION_EXECUTABLES = {"rm", "rmdir", "unlink", "shred"}
SHELL_CONTROL_TOKENS = {";", "&&", "||", "|", ">", ">>", "<", "<<", "&"}


def diagnostic(
    diagnostic_id: str,
    path: str,
    message: str,
    severity: str = "error",
) -> dict[str, str]:
    return {
        "id": diagnostic_id,
        "severity": severity,
        "path": path,
        "message": message,
    }


def sort_diagnostics(items: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(items, key=lambda item: (item["path"], item["id"], item["message"]))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label}: {exc}") from exc


def validate_governance(binding_path: Path) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    try:
        binding = load_json(binding_path, "governance binding")
    except ValueError as exc:
        return None, [diagnostic("GOV001", "$", str(exc))]
    if not isinstance(binding, dict):
        return None, [diagnostic("GOV001", "$", "governance binding must be an object")]
    required = {
        "binding_version",
        "schema_version",
        "renderer_version",
        "workspace_root",
        "agents_path",
        "agents_sha256",
        "cpc_path",
        "cpc_sha256",
    }
    missing = sorted(required - set(binding))
    if missing:
        return binding, [
            diagnostic("GOV001", "$", f"governance binding missing: {', '.join(missing)}")
        ]
    if (
        binding["schema_version"] != SCHEMA_VERSION
        or binding["renderer_version"] != RENDERER_VERSION
    ):
        return binding, [
            diagnostic("GOV001", "$", "governance binding version mismatch")
        ]
    workspace_value = binding["workspace_root"]
    if not isinstance(workspace_value, str) or not Path(workspace_value).is_absolute():
        return binding, [
            diagnostic("GOV001", "$.workspace_root", "must be an absolute path")
        ]
    workspace_root = Path(workspace_value)
    checks = (
        ("AGENTS.md", binding["agents_path"], binding["agents_sha256"]),
        ("CPC.md", binding["cpc_path"], binding["cpc_sha256"]),
    )
    diagnostics: list[dict[str, str]] = []
    for label, relative_path, expected_hash in checks:
        if not isinstance(relative_path, str) or not isinstance(expected_hash, str):
            diagnostics.append(
                diagnostic("GOV001", label, "binding path and hash must be strings")
            )
            continue
        governed_path = workspace_root / relative_path
        try:
            observed_hash = sha256_file(governed_path)
        except OSError as exc:
            diagnostics.append(diagnostic("GOV001", label, f"cannot hash: {exc}"))
            continue
        if observed_hash != expected_hash:
            diagnostics.append(
                diagnostic(
                    "GOV001",
                    label,
                    f"governance drift: expected {expected_hash}, observed {observed_hash}",
                )
            )
    return binding, sort_diagnostics(diagnostics)


def require_mapping(
    value: Any,
    path: str,
    diagnostics: list[dict[str, str]],
) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        diagnostics.append(diagnostic("TYPE001", path, "must be an object"))
        return None
    return value


def require_string(
    value: Any,
    path: str,
    diagnostics: list[dict[str, str]],
    *,
    allow_null: bool = False,
) -> str | None:
    if allow_null and value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        diagnostics.append(diagnostic("TYPE001", path, "must be a nonempty string"))
        return None
    return value


def require_string_list(
    value: Any,
    path: str,
    diagnostics: list[dict[str, str]],
    *,
    nonempty: bool = False,
) -> list[str] | None:
    if not isinstance(value, list) or (nonempty and not value):
        qualifier = "nonempty " if nonempty else ""
        diagnostics.append(
            diagnostic("TYPE001", path, f"must be a {qualifier}array of strings")
        )
        return None
    if not all(isinstance(item, str) and item.strip() for item in value):
        diagnostics.append(
            diagnostic("TYPE001", path, "must contain only nonempty strings")
        )
        return None
    return value


def check_exact_keys(
    value: dict[str, Any],
    path: str,
    required: set[str],
    optional: set[str],
    diagnostics: list[dict[str, str]],
) -> None:
    for name in sorted(required - set(value)):
        diagnostics.append(
            diagnostic("REQ001", f"{path}.{name}", "required field is missing")
        )
    for name in sorted(set(value) - required - optional):
        diagnostics.append(
            diagnostic("TYPE001", f"{path}.{name}", "unsupported field")
        )


def scan_for_secrets(value: Any, path: str, diagnostics: list[dict[str, str]]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if SECRET_KEY_RE.search(str(key)):
                diagnostics.append(
                    diagnostic("SECRET001", child_path, "credential-like key is forbidden")
                )
            scan_for_secrets(child, child_path, diagnostics)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_for_secrets(child, f"{path}[{index}]", diagnostics)
    elif isinstance(value, str) and SECRET_VALUE_RE.search(value):
        diagnostics.append(
            diagnostic("SECRET001", path, "credential-like value is forbidden")
        )


def validate_output(
    output: Any,
    path: str,
    schema: dict[str, Any],
    command_status: str | None,
    command_evidence: list[str] | None,
    diagnostics: list[dict[str, str]],
) -> None:
    mapping = require_mapping(output, path, diagnostics)
    if mapping is None:
        return
    required = set(schema["output_required_fields"])
    check_exact_keys(mapping, path, required, set(), diagnostics)
    if required - set(mapping):
        return
    output_path = require_string(mapping["path"], f"{path}.path", diagnostics)
    require_string(mapping["role"], f"{path}.role", diagnostics)
    behavior = require_string(
        mapping["collision_behavior"], f"{path}.collision_behavior", diagnostics
    )
    artifacts = require_string_list(
        mapping["qualification_artifacts"],
        f"{path}.qualification_artifacts",
        diagnostics,
    )
    if output_path is not None:
        if (
            GLOB_RE.search(output_path)
            or VARIABLE_RE.search(output_path)
            or "\n" in output_path
            or "\x00" in output_path
        ):
            diagnostics.append(
                diagnostic(
                    "OUTPUT001",
                    f"{path}.path",
                    "output identity must be an explicit path without globs or variables",
                )
            )
    if behavior not in schema["collision_behaviors"]:
        diagnostics.append(
            diagnostic(
                "ENUM001",
                f"{path}.collision_behavior",
                "unsupported collision behavior",
            )
        )
    if behavior == "allow_existing_qualified" and (
        not artifacts or not command_evidence
    ):
        diagnostics.append(
            diagnostic(
                "OUTPUT002",
                path,
                "allow_existing_qualified requires qualification artifacts and accepted command evidence",
            )
        )
    if command_status in {"pending", "not_started", "failed_known"}:
        if behavior != "must_be_absent":
            diagnostics.append(
                diagnostic(
                    "OUTPUT003",
                    f"{path}.collision_behavior",
                    "runnable commands require collision_behavior=must_be_absent",
                )
            )
    elif command_status == "completed_valid":
        if behavior == "allow_existing_qualified" and (
            not artifacts or not command_evidence
        ):
            diagnostics.append(
                diagnostic(
                    "OUTPUT004",
                    path,
                    "completed_valid allow_existing_qualified outputs require command evidence and output qualification artifacts",
                )
            )
        elif behavior == "informational_only":
            diagnostics.append(
                diagnostic(
                    "OUTPUT005",
                    f"{path}.collision_behavior",
                    "informational_only is inconsistent with completed_valid status",
                )
            )
    elif command_status == "interrupted_ambiguous":
        if behavior != "informational_only":
            diagnostics.append(
                diagnostic(
                    "OUTPUT005",
                    f"{path}.collision_behavior",
                    "interrupted_ambiguous outputs require informational_only collision behavior",
                )
            )


def validate_command(
    command: Any,
    index: int,
    schema: dict[str, Any],
    cwd_mode: str | None,
    diagnostics: list[dict[str, str]],
) -> str | None:
    path = f"$.commands[{index}]"
    mapping = require_mapping(command, path, diagnostics)
    if mapping is None:
        return None
    required = set(schema["command_required_fields"])
    optional = set(schema["command_optional_fields"])
    check_exact_keys(mapping, path, required, optional, diagnostics)
    if required - set(mapping):
        return None
    command_id = require_string(mapping["command_id"], f"{path}.command_id", diagnostics)
    if command_id is not None and not COMMAND_ID_RE.fullmatch(command_id):
        diagnostics.append(
            diagnostic(
                "CMD001",
                f"{path}.command_id",
                "must use snake_case beginning with a letter",
            )
        )
    status = require_string(mapping["status"], f"{path}.status", diagnostics)
    if status not in schema["command_statuses"]:
        diagnostics.append(
            diagnostic("ENUM001", f"{path}.status", "unsupported command status")
        )
    argv = mapping["argv"]
    if isinstance(argv, str):
        diagnostics.append(
            diagnostic(
                "CMD001",
                f"{path}.argv",
                "shell command strings are forbidden; use an argument array",
            )
        )
    elif (
        not isinstance(argv, list)
        or not argv
        or not all(isinstance(arg, str) and arg and "\x00" not in arg for arg in argv)
    ):
        diagnostics.append(
            diagnostic("CMD001", f"{path}.argv", "must be a nonempty string array")
        )
    else:
        executable = Path(argv[0]).name
        if executable in SHELL_EXECUTABLES:
            diagnostics.append(
                diagnostic(
                    "SHELL001",
                    f"{path}.argv[0]",
                    "shell interpreters are forbidden in generated command arrays",
                )
            )
        if executable in DELETION_EXECUTABLES:
            diagnostics.append(
                diagnostic(
                    "SHELL001",
                    f"{path}.argv[0]",
                    "deletion commands are forbidden",
                )
            )
        for argument_index, argument in enumerate(argv):
            argument_path = f"{path}.argv[{argument_index}]"
            if VARIABLE_RE.search(argument):
                diagnostics.append(
                    diagnostic(
                        "ENV001",
                        argument_path,
                        "argv must not depend on shell variable expansion",
                    )
                )
            if argument in SHELL_CONTROL_TOKENS:
                diagnostics.append(
                    diagnostic(
                        "SHELL001",
                        argument_path,
                        "shell control syntax is forbidden in argv",
                    )
                )
    require_string(mapping["description"], f"{path}.description", diagnostics)
    command_evidence = require_string_list(
        mapping["qualification_evidence"],
        f"{path}.qualification_evidence",
        diagnostics,
    )
    outputs = mapping["expected_outputs"]
    if not isinstance(outputs, list) or not outputs:
        diagnostics.append(
            diagnostic(
                "TYPE001",
                f"{path}.expected_outputs",
                "must be a nonempty array of explicit outputs",
            )
        )
    else:
        for output_index, output in enumerate(outputs):
            validate_output(
                output,
                f"{path}.expected_outputs[{output_index}]",
                schema,
                status,
                command_evidence,
                diagnostics,
            )
    if status == "completed_valid" and not command_evidence:
        diagnostics.append(
            diagnostic(
                "STATUS001",
                f"{path}.qualification_evidence",
                "completed_valid requires explicit accepted evidence",
            )
        )
    if status == "failed_known":
        if mapping.get("retry_authorized") is not True or not isinstance(
            mapping.get("retry_reason"), str
        ) or not mapping.get("retry_reason", "").strip():
            diagnostics.append(
                diagnostic(
                    "STATUS002",
                    path,
                    "failed_known requires retry_authorized=true and a retry_reason",
                )
            )
    elif mapping.get("retry_authorized") is True:
        diagnostics.append(
            diagnostic(
                "STATUS002",
                f"{path}.retry_authorized",
                "retry authorization is supported only for failed_known",
            )
        )
    override = mapping.get("working_directory_override")
    if override is not None:
        override_value = require_string(
            override, f"{path}.working_directory_override", diagnostics
        )
        if cwd_mode == "caller_managed":
            diagnostics.append(
                diagnostic(
                    "CWD001",
                    f"{path}.working_directory_override",
                    "caller_managed wrappers cannot contain a directory change",
                )
            )
        if override_value is not None and (
            VARIABLE_RE.search(override_value) or GLOB_RE.search(override_value)
        ):
            diagnostics.append(
                diagnostic(
                    "CWD001",
                    f"{path}.working_directory_override",
                    "directory override must be an explicit path",
                )
            )
    environment_overrides = mapping.get("environment_overrides", {})
    if not isinstance(environment_overrides, dict):
        diagnostics.append(
            diagnostic(
                "TYPE001",
                f"{path}.environment_overrides",
                "must be a string mapping",
            )
        )
    else:
        for name, value in environment_overrides.items():
            if not isinstance(name, str) or not ENV_NAME_RE.fullmatch(name):
                diagnostics.append(
                    diagnostic(
                        "ENV001",
                        f"{path}.environment_overrides",
                        "environment override names must be valid identifiers",
                    )
                )
            if not isinstance(value, str) or VARIABLE_RE.search(value):
                diagnostics.append(
                    diagnostic(
                        "ENV001",
                        f"{path}.environment_overrides.{name}",
                        "environment override values must be literal strings",
                    )
                )
    return command_id


def validate_logging(
    logging: Any,
    schema: dict[str, Any],
    diagnostics: list[dict[str, str]],
) -> None:
    path = "$.logging"
    mapping = require_mapping(logging, path, diagnostics)
    if mapping is None:
        return
    required = set(schema["logging_required_fields"])
    optional = set(schema["logging_optional_fields"])
    check_exact_keys(mapping, path, required, optional, diagnostics)
    if required - set(mapping):
        return
    boolean_fields = (
        "enabled",
        "one_log_per_command",
        "capture_start_time",
        "capture_end_time",
        "capture_exit_code",
        "tee_to_console",
    )
    for field in boolean_fields:
        if not isinstance(mapping[field], bool):
            diagnostics.append(
                diagnostic("TYPE001", f"{path}.{field}", "must be boolean")
            )
    for field in ("directory", "default_directory"):
        if mapping[field] is not None and (
            not isinstance(mapping[field], str) or not mapping[field].strip()
        ):
            diagnostics.append(
                diagnostic("TYPE001", f"{path}.{field}", "must be null or nonempty string")
            )
        elif isinstance(mapping[field], str) and (
            VARIABLE_RE.search(mapping[field]) or GLOB_RE.search(mapping[field])
        ):
            diagnostics.append(
                diagnostic("LOG001", f"{path}.{field}", "must be an explicit path")
            )
    if mapping["enabled"]:
        if not mapping["directory"] and not mapping["default_directory"]:
            diagnostics.append(
                diagnostic(
                    "LOG001",
                    path,
                    "enabled logging requires directory or default_directory",
                )
            )
        required_true = (
            "one_log_per_command",
            "capture_start_time",
            "capture_end_time",
            "capture_exit_code",
        )
        for field in required_true:
            if mapping[field] is not True:
                diagnostics.append(
                    diagnostic(
                        "LOG001",
                        f"{path}.{field}",
                        "version 1 logging requires this field to be true",
                    )
                )
    override = mapping.get("directory_env_override")
    if override is not None and (
        not isinstance(override, str) or not ENV_NAME_RE.fullmatch(override)
    ):
        diagnostics.append(
            diagnostic(
                "ENV001",
                f"{path}.directory_env_override",
                "must be a valid explicitly declared environment variable name",
            )
        )


def validate_provenance(
    provenance: Any,
    schema: dict[str, Any],
    diagnostics: list[dict[str, str]],
) -> None:
    path = "$.provenance"
    mapping = require_mapping(provenance, path, diagnostics)
    if mapping is None:
        return
    check_exact_keys(mapping, path, {"record", "enforce"}, set(), diagnostics)
    if "record" not in mapping or "enforce" not in mapping:
        return
    record = require_mapping(mapping["record"], f"{path}.record", diagnostics)
    enforce = require_mapping(mapping["enforce"], f"{path}.enforce", diagnostics)
    if record is None or enforce is None:
        return
    check_exact_keys(
        record,
        f"{path}.record",
        set(schema["provenance_record_fields"]),
        set(),
        diagnostics,
    )
    check_exact_keys(
        enforce,
        f"{path}.enforce",
        set(schema["provenance_enforce_fields"]),
        set(),
        diagnostics,
    )
    if set(schema["provenance_record_fields"]) - set(record) or set(
        schema["provenance_enforce_fields"]
    ) - set(enforce):
        return
    for field in ("branch", "commit"):
        if record[field] is not None and (
            not isinstance(record[field], str) or not record[field].strip()
        ):
            diagnostics.append(
                diagnostic(
                    "TYPE001",
                    f"{path}.record.{field}",
                    "must be null or a nonempty string",
                )
            )
        if not isinstance(enforce[field], bool):
            diagnostics.append(
                diagnostic("TYPE001", f"{path}.enforce.{field}", "must be boolean")
            )
        elif enforce[field] and not record[field]:
            diagnostics.append(
                diagnostic(
                    "PROV001",
                    f"{path}.enforce.{field}",
                    "enforcement requires the corresponding recorded value",
                )
            )
    hashes = record["configuration_hashes"]
    if not isinstance(hashes, dict):
        diagnostics.append(
            diagnostic(
                "TYPE001",
                f"{path}.record.configuration_hashes",
                "must be a path-to-sha256 mapping",
            )
        )
    else:
        for config_path, digest in hashes.items():
            if (
                not isinstance(config_path, str)
                or not config_path.strip()
                or VARIABLE_RE.search(config_path)
                or GLOB_RE.search(config_path)
                or not isinstance(digest, str)
                or not HASH_RE.fullmatch(digest)
            ):
                diagnostics.append(
                    diagnostic(
                        "PROV001",
                        f"{path}.record.configuration_hashes",
                        "configuration hashes require explicit paths and lowercase SHA-256 values",
                    )
                )


def validate_manifest(
    manifest: Any,
    schema: dict[str, Any],
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, Any]]]:
    errors: list[dict[str, str]] = []
    unsafe: list[dict[str, str]] = []
    runnable: list[dict[str, Any]] = []
    mapping = require_mapping(manifest, "$", errors)
    if mapping is None:
        return sort_diagnostics(errors), unsafe, runnable
    scan_for_secrets(mapping, "$", errors)
    required = set(schema["required_top_level_fields"])
    check_exact_keys(mapping, "$", required, set(), errors)
    if required - set(mapping):
        return sort_diagnostics(errors), unsafe, runnable
    if mapping["manifest_version"] != SCHEMA_VERSION:
        errors.append(
            diagnostic("ENUM001", "$.manifest_version", "unsupported manifest version")
        )
    handoff_id = require_string(mapping["handoff_id"], "$.handoff_id", errors)
    if handoff_id is not None and not COMMAND_ID_RE.fullmatch(handoff_id):
        errors.append(
            diagnostic("TYPE001", "$.handoff_id", "must be a snake_case identifier")
        )
    require_string(mapping["title"], "$.title", errors)
    if mapping["execution_owner"] != "user":
        errors.append(
            diagnostic("ENUM001", "$.execution_owner", "version 1 execution owner must be user")
        )
    cwd = require_string(mapping["execution_cwd"], "$.execution_cwd", errors)
    cwd_mode = require_string(
        mapping["execution_cwd_mode"], "$.execution_cwd_mode", errors
    )
    if cwd_mode not in schema["execution_cwd_modes"]:
        errors.append(
            diagnostic("ENUM001", "$.execution_cwd_mode", "unsupported working-directory mode")
        )
    elif cwd is not None:
        cwd_path = Path(cwd)
        if cwd_mode == "fixed" and not cwd_path.is_absolute():
            errors.append(
                diagnostic("CWD001", "$.execution_cwd", "fixed mode requires an absolute path")
            )
        if cwd_mode == "script_relative" and (
            cwd_path.is_absolute() or ".." in cwd_path.parts or VARIABLE_RE.search(cwd)
        ):
            errors.append(
                diagnostic(
                    "CWD001",
                    "$.execution_cwd",
                    "script_relative mode requires a non-escaping relative target",
                )
            )
    require_string_list(
        mapping["environment_requirements"],
        "$.environment_requirements",
        errors,
        nonempty=True,
    )
    commands = mapping["commands"]
    command_ids: list[str] = []
    if not isinstance(commands, list) or not commands:
        errors.append(diagnostic("TYPE001", "$.commands", "must be a nonempty array"))
    else:
        for index, command in enumerate(commands):
            command_id = validate_command(command, index, schema, cwd_mode, errors)
            if command_id is not None:
                command_ids.append(command_id)
            if isinstance(command, dict) and command.get("status") in {
                "pending",
                "not_started",
            }:
                runnable.append(command)
            elif (
                isinstance(command, dict)
                and command.get("status") == "failed_known"
                and command.get("retry_authorized") is True
                and isinstance(command.get("retry_reason"), str)
                and command.get("retry_reason", "").strip()
            ):
                runnable.append(command)
            if isinstance(command, dict) and command.get("status") == "interrupted_ambiguous":
                unsafe.append(
                    diagnostic(
                        "STATUS003",
                        f"$.commands[{index}].status",
                        "ambiguous interruption requires stop_and_classify before wrapper rendering",
                        "unsafe",
                    )
                )
    duplicates = sorted({item for item in command_ids if command_ids.count(item) > 1})
    for duplicate in duplicates:
        errors.append(
            diagnostic("CMD002", "$.commands", f"duplicate command_id: {duplicate}")
        )
    validate_logging(mapping["logging"], schema, errors)
    if mapping["output_collision_policy"] not in schema["output_collision_policies"]:
        errors.append(
            diagnostic(
                "ENUM001",
                "$.output_collision_policy",
                "version 1 requires fail_closed",
            )
        )
    interruption = require_mapping(
        mapping["interruption_policy"], "$.interruption_policy", errors
    )
    if interruption is not None:
        required_interruption = {
            "stop_on_first_failure",
            "automatic_retry",
            "ambiguous_interruption_action",
        }
        check_exact_keys(
            interruption, "$.interruption_policy", required_interruption, set(), errors
        )
        if not (required_interruption - set(interruption)):
            if interruption["stop_on_first_failure"] is not True:
                errors.append(
                    diagnostic(
                        "RETRY001",
                        "$.interruption_policy.stop_on_first_failure",
                        "version 1 requires stop_on_first_failure=true",
                    )
                )
            if interruption["automatic_retry"] is not False:
                errors.append(
                    diagnostic(
                        "RETRY001",
                        "$.interruption_policy.automatic_retry",
                        "automatic retry is forbidden",
                    )
                )
            if (
                interruption["ambiguous_interruption_action"]
                not in schema["ambiguous_interruption_actions"]
            ):
                errors.append(
                    diagnostic(
                        "ENUM001",
                        "$.interruption_policy.ambiguous_interruption_action",
                        "unsupported ambiguous interruption action",
                    )
                )
    require_string_list(
        mapping["evidence_return_contract"],
        "$.evidence_return_contract",
        errors,
        nonempty=True,
    )
    validate_provenance(mapping["provenance"], schema, errors)
    if not runnable:
        unsafe.append(
            diagnostic(
                "SAFE001",
                "$.commands",
                "no commands remain for a runnable wrapper",
                "unsafe",
            )
        )
    if not errors:
        errors.append(
            diagnostic("OK000", "$", "manifest schema is valid", "info")
        )
    return sort_diagnostics(errors), sort_diagnostics(unsafe), runnable


def shell_quote(value: str) -> str:
    return shlex.quote(value)


def render_collision_checks(command: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    command_id = command["command_id"]
    for output in command["expected_outputs"]:
        output_path = shell_quote(output["path"])
        lines.extend(
            [
                f"if [[ -e {output_path} ]]; then",
                f"  printf 'Refusing {command_id}: output collision: %s\\n' {output_path} >&2",
                "  exit 73",
                "fi",
            ]
        )
    return lines


def render_command_call(command: dict[str, Any]) -> str:
    prefix = ["env"]
    for name, value in sorted(command.get("environment_overrides", {}).items()):
        prefix.append(f"{name}={value}")
    argv = prefix + command["argv"]
    call = " ".join(shell_quote(item) for item in argv)
    return f"run_handoff_command {shell_quote(command['command_id'])} {call}"


def render_wrapper(manifest: dict[str, Any], runnable: list[dict[str, Any]]) -> str:
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        "# Generated for manual user execution. This file was not executed by Codex.",
    ]
    cwd_mode = manifest["execution_cwd_mode"]
    cwd = manifest["execution_cwd"]
    if cwd_mode == "fixed":
        lines.extend([f"cd -- {shell_quote(cwd)}", ""])
    elif cwd_mode == "script_relative":
        lines.extend(
            [
                'script_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"',
                f"cd -- \"${{script_dir}}\"/{shell_quote(cwd)}",
                "",
            ]
        )
    provenance = manifest["provenance"]
    if provenance["enforce"]["branch"]:
        lines.extend(
            [
                'actual_branch="$(git branch --show-current)"',
                f"expected_branch={shell_quote(provenance['record']['branch'])}",
                '[[ "${actual_branch}" == "${expected_branch}" ]] || {',
                '  printf "Branch provenance mismatch: expected %s, observed %s\\n" "${expected_branch}" "${actual_branch}" >&2',
                "  exit 74",
                "}",
                "",
            ]
        )
    if provenance["enforce"]["commit"]:
        lines.extend(
            [
                'actual_commit="$(git rev-parse HEAD)"',
                f"expected_commit={shell_quote(provenance['record']['commit'])}",
                '[[ "${actual_commit}" == "${expected_commit}" ]] || {',
                '  printf "Commit provenance mismatch: expected %s, observed %s\\n" "${expected_commit}" "${actual_commit}" >&2',
                "  exit 75",
                "}",
                "",
            ]
        )
    logging = manifest["logging"]
    if logging["enabled"]:
        selected = logging["directory"] or logging["default_directory"]
        lines.append(f"log_dir_default={shell_quote(selected)}")
        if logging.get("directory_env_override"):
            variable = logging["directory_env_override"]
            lines.append(f'log_dir="${{{variable}:-${{log_dir_default}}}}"')
        else:
            lines.append('log_dir="${log_dir_default}"')
        lines.extend(['mkdir -p -- "${log_dir}"', ""])
    lines.extend(
        [
            "run_handoff_command() {",
            '  local command_id="$1"',
            "  shift",
        ]
    )
    if logging["enabled"]:
        lines.extend(
            [
                '  local log_path="${log_dir}/${command_id}.log"',
                "  local command_status",
                "  local tee_status",
            ]
        )
        redirect = '  } 2>&1 | tee -a "${log_path}"' if logging["tee_to_console"] else '  } >>"${log_path}" 2>&1'
        lines.extend(
            [
                "  {",
                "    printf 'start_time: %s\\n' \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"",
                "    printf 'command:'",
                "    printf ' %q' \"$@\"",
                "    printf '\\n'",
                "    set +e",
                '    "$@"',
                "    command_status=$?",
                "    set -e",
                "    printf 'end_time: %s\\n' \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"",
                "    printf 'exit_code: %s\\n' \"${command_status}\"",
                "    return \"${command_status}\"",
                redirect,
            ]
        )
        if logging["tee_to_console"]:
            lines.extend(
                [
                    '  command_status="${PIPESTATUS[0]}" tee_status="${PIPESTATUS[1]}"',
                    '  if (( command_status != 0 )); then',
                    '    return "${command_status}"',
                    "  fi",
                    '  if (( tee_status != 0 )); then',
                    '    printf "Logging failure for %s: tee exited with status %s while writing %s\\n" "${command_id}" "${tee_status}" "${log_path}" >&2',
                    '    return "${tee_status}"',
                    "  fi",
                    "  return 0",
                ]
            )
        else:
            lines.append("  return $?")
    else:
        lines.extend(
            [
                "  local command_status",
                "  printf 'start_time: %s\\n' \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"",
                "  printf 'command:'",
                "  printf ' %q' \"$@\"",
                "  printf '\\n'",
                "  set +e",
                '  "$@"',
                "  command_status=$?",
                "  set -e",
                "  printf 'end_time: %s\\n' \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"",
                "  printf 'exit_code: %s\\n' \"${command_status}\"",
                '  return "${command_status}"',
            ]
        )
    lines.extend(["}", ""])
    for command in runnable:
        lines.extend(render_collision_checks(command))
        call = render_command_call(command)
        override = command.get("working_directory_override")
        lines.extend(["set +e"])
        if override:
            lines.extend(
                [
                    "(",
                    f"  cd -- {shell_quote(override)}",
                    f"  {call}",
                    ")",
                ]
            )
        else:
            lines.append(call)
        lines.extend(
            [
                "command_status=$?",
                "set -e",
                'if (( command_status != 0 )); then',
                f"  printf 'Stopping after {command['command_id']} failed with exit code %s\\n' \"${{command_status}}\" >&2",
                '  exit "${command_status}"',
                "fi",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def markdown_cell(value: Any) -> str:
    if value is None:
        return "not supplied"
    if isinstance(value, (dict, list)):
        text = json.dumps(value, sort_keys=True)
    else:
        text = str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def render_runbook(
    manifest: dict[str, Any],
    runnable: list[dict[str, Any]],
    artifact_paths: dict[str, str],
    wrapper_safe: bool,
) -> str:
    completed = [
        command["command_id"]
        for command in manifest["commands"]
        if command["status"] == "completed_valid"
    ]
    failed_or_ambiguous = [
        command["command_id"]
        for command in manifest["commands"]
        if command["status"] in {"failed_known", "interrupted_ambiguous"}
    ]
    provenance = manifest["provenance"]
    logging = manifest["logging"]
    lines = [
        f"# {manifest['title']}",
        "",
        "## Scope",
        "",
        f"- Handoff ID: `{manifest['handoff_id']}`",
        "- Scope: prepare-only manual production handoff.",
        f"- Execution owner: `{manifest['execution_owner']}`",
        "- Codex did not execute, monitor, retry, or inspect production.",
        f"- Runnable wrapper safety: `{'safe' if wrapper_safe else 'blocked'}`",
        "",
        "## Required execution directory",
        "",
        f"- Mode: `{manifest['execution_cwd_mode']}`",
        f"- Required directory or target: `{manifest['execution_cwd']}`",
        "",
        "## Environment requirements",
        "",
    ]
    lines.extend(f"- {item}" for item in manifest["environment_requirements"])
    lines.extend(
        [
            "",
            "## Provenance recording",
            "",
            f"- Branch: `{markdown_cell(provenance['record']['branch'])}`",
            f"- Commit: `{markdown_cell(provenance['record']['commit'])}`",
            f"- Configuration hashes: `{markdown_cell(provenance['record']['configuration_hashes'])}`",
            "",
            "## Provenance enforcement",
            "",
            f"- Branch gate: `{str(provenance['enforce']['branch']).lower()}`",
            f"- Commit gate: `{str(provenance['enforce']['commit']).lower()}`",
            "",
            "## Command inventory",
            "",
            "| Order | Command ID | Status | Description | Exact argv |",
            "| ---: | --- | --- | --- | --- |",
        ]
    )
    for index, command in enumerate(manifest["commands"], start=1):
        lines.append(
            f"| {index} | `{command['command_id']}` | `{command['status']}` | "
            f"{markdown_cell(command['description'])} | `{markdown_cell(command['argv'])}` |"
        )
    lines.extend(
        [
            "",
            "## Completed-valid commands",
            "",
            f"- Excluded from execution: `{markdown_cell(completed)}`",
            "",
            "## Commands to execute",
            "",
        ]
    )
    if runnable:
        for index, command in enumerate(runnable, start=1):
            lines.append(f"{index}. `{command['command_id']}` — `{markdown_cell(command['argv'])}`")
    else:
        lines.append("- None. Render and review the runbook only.")
    lines.extend(
        [
            "",
            "## Failed or ambiguous commands",
            "",
            f"- Inventory: `{markdown_cell(failed_or_ambiguous)}`",
            "- An `interrupted_ambiguous` command blocks wrapper generation until explicitly classified.",
            "",
            "## Output collision policy",
            "",
            f"- Global policy: `{manifest['output_collision_policy']}`",
        ]
    )
    for command in manifest["commands"]:
        for output in command["expected_outputs"]:
            lines.append(
                f"- `{command['command_id']}`: `{output['path']}` "
                f"({output['role']}, `{output['collision_behavior']}`); "
                f"qualification artifacts: `{markdown_cell(output['qualification_artifacts'])}`"
            )
    lines.extend(
        [
            "",
            "## Logging policy",
            "",
            f"- Enabled: `{str(logging['enabled']).lower()}`",
            f"- Explicit directory: `{markdown_cell(logging['directory'])}`",
            f"- Local default directory: `{markdown_cell(logging['default_directory'])}`",
            f"- Optional environment override: `{markdown_cell(logging.get('directory_env_override'))}`",
            f"- One log per command: `{str(logging['one_log_per_command']).lower()}`",
            f"- Tee to console: `{str(logging['tee_to_console']).lower()}`",
            "- Each enabled command log records exact argv, start time, end time, and exit code.",
            "- With `tee_to_console=true`, stdout and stderr are merged, the merged stream is displayed live, and the merged stream is saved to the command log.",
            "- `tee_to_console=true` does not preserve child TTY detection and may disable or degrade in-place progress bars.",
            f"- TTY-preserving logging is not supported in renderer version {RENDERER_VERSION}; it requires a separate explicit design and implementation round.",
            "",
            "## Interruption policy",
            "",
            f"- Stop on first failure: `{str(manifest['interruption_policy']['stop_on_first_failure']).lower()}`",
            f"- Automatic retry: `{str(manifest['interruption_policy']['automatic_retry']).lower()}`",
            f"- Ambiguous interruption: `{manifest['interruption_policy']['ambiguous_interruption_action']}`",
            "",
            "## Evidence to return",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in manifest["evidence_return_contract"])
    lines.extend(["", "## Exact generated artifact paths", ""])
    for name, path in artifact_paths.items():
        lines.append(f"- `{name}`: `{path}`")
    return "\n".join(lines).rstrip() + "\n"


def command_inventory(
    manifest: dict[str, Any],
    runnable: list[dict[str, Any]],
) -> dict[str, Any]:
    runnable_ids = [command["command_id"] for command in runnable]
    return {
        "renderer_version": RENDERER_VERSION,
        "schema_version": SCHEMA_VERSION,
        "handoff_id": manifest["handoff_id"],
        "commands": [
            {
                "order": index,
                "command_id": command["command_id"],
                "status": command["status"],
                "argv": command["argv"],
                "included_in_wrapper": command["command_id"] in runnable_ids,
                "expected_outputs": command["expected_outputs"],
            }
            for index, command in enumerate(manifest["commands"], start=1)
        ],
        "commands_to_execute": runnable_ids,
    }


def json_text(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def write_exclusive(path: Path, content: str, mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, mode or 0o644)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(content)
    except Exception:
        try:
            path.unlink()
        except OSError:
            pass
        raise
    if mode is not None:
        path.chmod(mode)


def result_payload(
    manifest_path: Path,
    schema_valid: bool,
    wrapper_safe: bool,
    runbook_only: bool,
    diagnostics: list[dict[str, str]],
    artifacts: dict[str, str],
) -> dict[str, Any]:
    return {
        "renderer_version": RENDERER_VERSION,
        "schema_version": SCHEMA_VERSION,
        "manifest_path": str(manifest_path.resolve()),
        "schema_valid": schema_valid,
        "wrapper_safe": wrapper_safe,
        "runbook_only": runbook_only,
        "diagnostics": diagnostics,
        "artifacts": artifacts,
        "production_executed": False,
    }


def human_output(payload: dict[str, Any]) -> str:
    lines = [
        f"renderer_version: {payload['renderer_version']}",
        f"schema_version: {payload['schema_version']}",
        f"manifest: {payload['manifest_path']}",
        f"schema_valid: {str(payload['schema_valid']).lower()}",
        f"wrapper_safe: {str(payload['wrapper_safe']).lower()}",
        f"runbook_only: {str(payload['runbook_only']).lower()}",
        "diagnostics:",
    ]
    for item in payload["diagnostics"]:
        lines.append(
            f"  {item['severity']} {item['id']} {item['path']}: {item['message']}"
        )
    lines.append("artifacts:")
    for name, path in sorted(payload["artifacts"].items()):
        lines.append(f"  {name}: {path}")
    lines.append("production_executed: false")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate and render a non-executing manual production handoff."
    )
    parser.add_argument("--schema", type=Path)
    parser.add_argument("--governance-binding", type=Path)
    parser.add_argument("--format", choices=("human", "json"), default="human")
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--runbook-only", action="store_true")
    parser.add_argument("manifest", type=Path)
    return parser


def emit(payload: dict[str, Any], output_format: str) -> None:
    if output_format == "json":
        sys.stdout.write(json_text(payload))
    else:
        sys.stdout.write(human_output(payload) + "\n")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    skill_root = Path(__file__).resolve().parents[1]
    schema_path = (args.schema or skill_root / "references/handoff_schema.json").resolve()
    binding_path = (
        args.governance_binding
        or skill_root / "references/governance_binding.json"
    ).resolve()
    _, governance_diagnostics = validate_governance(binding_path)
    if governance_diagnostics:
        payload = result_payload(
            args.manifest,
            False,
            False,
            args.runbook_only,
            governance_diagnostics,
            {},
        )
        emit(payload, args.format)
        return EXIT_GOVERNANCE
    try:
        schema = load_json(schema_path, "schema")
        manifest = load_json(args.manifest, "manifest")
    except ValueError as exc:
        payload = result_payload(
            args.manifest,
            False,
            False,
            args.runbook_only,
            [diagnostic("JSON001", "$", str(exc))],
            {},
        )
        emit(payload, args.format)
        return EXIT_VALIDATION
    if not isinstance(schema, dict) or schema.get("schema_version") != SCHEMA_VERSION:
        payload = result_payload(
            args.manifest,
            False,
            False,
            args.runbook_only,
            [diagnostic("JSON001", "$", "invalid or unsupported schema resource")],
            {},
        )
        emit(payload, args.format)
        return EXIT_VALIDATION
    schema_diagnostics, unsafe_diagnostics, runnable = validate_manifest(manifest, schema)
    schema_errors = [
        item for item in schema_diagnostics if item["severity"] == "error"
    ]
    if schema_errors:
        payload = result_payload(
            args.manifest,
            False,
            False,
            args.runbook_only,
            schema_diagnostics,
            {},
        )
        if args.json_out:
            try:
                write_exclusive(args.json_out, json_text(payload))
            except OSError as exc:
                print(f"output_error: {exc}", file=sys.stderr)
                return EXIT_RENDER
        emit(payload, args.format)
        return EXIT_VALIDATION
    wrapper_safe = not unsafe_diagnostics
    output_dir = (
        args.output_dir
        or args.manifest.resolve().parent / f"{manifest['handoff_id']}_handoff"
    ).resolve()
    artifact_paths = {
        "handoff_runbook.md": str(output_dir / "handoff_runbook.md"),
        "handoff_commands.json": str(output_dir / "handoff_commands.json"),
        "handoff_validation.json": str(output_dir / "handoff_validation.json"),
    }
    render_wrapper_requested = not args.runbook_only
    if render_wrapper_requested and wrapper_safe:
        artifact_paths["handoff_wrapper.sh"] = str(output_dir / "handoff_wrapper.sh")
    diagnostics = sort_diagnostics(schema_diagnostics + unsafe_diagnostics)
    payload = result_payload(
        args.manifest,
        True,
        wrapper_safe,
        args.runbook_only,
        diagnostics,
        artifact_paths,
    )
    try:
        runbook = render_runbook(manifest, runnable, artifact_paths, wrapper_safe)
        write_exclusive(Path(artifact_paths["handoff_runbook.md"]), runbook)
        write_exclusive(
            Path(artifact_paths["handoff_commands.json"]),
            json_text(command_inventory(manifest, runnable)),
        )
        write_exclusive(
            Path(artifact_paths["handoff_validation.json"]), json_text(payload)
        )
        if render_wrapper_requested and wrapper_safe:
            write_exclusive(
                Path(artifact_paths["handoff_wrapper.sh"]),
                render_wrapper(manifest, runnable),
                0o755,
            )
        if args.json_out:
            if args.json_out.resolve() in {
                Path(path).resolve() for path in artifact_paths.values()
            }:
                raise OSError("--json-out collides with a generated artifact")
            write_exclusive(args.json_out, json_text(payload))
    except OSError as exc:
        print(f"output_error: {exc}", file=sys.stderr)
        return EXIT_RENDER
    emit(payload, args.format)
    if render_wrapper_requested and not wrapper_safe:
        return EXIT_UNSAFE
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
