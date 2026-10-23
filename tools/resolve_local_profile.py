#!/usr/bin/env python3
"""Validate and resolve TOP26006_fw installation facts from YAML only.

The profile is configuration input. This tool never executes configured paths
or grants repository, branch, validation, publication, or scientific authority.
"""

import argparse
import os
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError as exc:
    raise SystemExit("PyYAML is required; run with the locally configured Python environment") from exc


class ProfileError(ValueError):
    """A profile or schema violates the local-configuration contract."""


class UniqueKeyLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        self.flatten_mapping(node)
        result = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise ProfileError("mapping keys must be strings")
            if key in result:
                raise ProfileError("duplicate mapping key: " + key)
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def read_yaml(path):
    try:
        with Path(path).open(encoding="utf-8") as stream:
            return yaml.load(stream, Loader=UniqueKeyLoader)
    except (OSError, yaml.YAMLError) as exc:
        raise ProfileError("cannot read valid YAML from " + str(path) + ": " + str(exc)) from exc


SENSITIVE_KEY = re.compile(
    r"(?:token|password|secret|credential|private.?key|api.?key|access.?key|refresh.?token)",
    re.IGNORECASE,
)
PLACEHOLDER = re.compile(r"<[^>]+>|\b(?:TODO|CHANGEME|PLACEHOLDER)\b|/absolute/local/|/path/to/|your[-_]", re.IGNORECASE)
GIT_ALIAS = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")


def reject_sensitive_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            # Never examine or print the value of a sensitive field.
            if isinstance(key, str) and SENSITIVE_KEY.search(key.replace("-", "_")):
                raise ProfileError("credential-like key is forbidden")
            reject_sensitive_keys(child)
    elif isinstance(value, list):
        for child in value:
            reject_sensitive_keys(child)


def validate_node(value, rule, label):
    if isinstance(rule, str):
        if rule == "integer_1":
            if type(value) is not int or value != 1:
                raise ProfileError(label + " must be profile version 1")
        elif rule in ("string", "path", "git_alias"):
            if not isinstance(value, str) or not value.strip():
                raise ProfileError(label + " must be a nonempty string")
            if rule == "git_alias" and not GIT_ALIAS.fullmatch(value):
                raise ProfileError(label + " must be a local Git alias name")
        else:
            raise ProfileError("unsupported schema rule at " + label)
        return
    if not isinstance(rule, dict) or not isinstance(value, dict):
        raise ProfileError(label + " must be a mapping")
    required = rule.get("required", {})
    optional = rule.get("optional", {})
    values_rule = rule.get("values")
    if not isinstance(required, dict) or not isinstance(optional, dict):
        raise ProfileError("invalid schema at " + label)
    for key, child_rule in required.items():
        if key not in value:
            raise ProfileError(label + "." + key + " is required")
        validate_node(value[key], child_rule, label + "." + key)
    for key, child in value.items():
        if key in required:
            continue
        if key in optional:
            validate_node(child, optional[key], label + "." + key)
        elif values_rule is not None:
            validate_node(child, values_rule, label + "." + key)
        else:
            raise ProfileError("unknown key: " + label + "." + key)


def resolve_path(raw, root, label):
    path = Path(raw).expanduser()
    if path.is_absolute():
        return os.path.normpath(str(path))
    resolved = Path(os.path.normpath(str(root / path)))
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ProfileError(label + " escapes workspace_root") from exc
    return str(resolved)


def resolve(profile, schema, execution_ready=False):
    if not isinstance(schema, dict) or schema.get("schema_version") != 1 or "profile" not in schema:
        raise ProfileError("unsupported or malformed local-profile schema")
    reject_sensitive_keys(profile)
    validate_node(profile, schema["profile"], "profile")
    if execution_ready:
        def check_placeholders(value):
            if isinstance(value, str) and PLACEHOLDER.search(value):
                raise ProfileError("execution-ready profile contains a placeholder")
            if isinstance(value, dict):
                for child in value.values():
                    check_placeholders(child)
        check_placeholders(profile)
    root = Path(profile["workspace_root"]).expanduser()
    if not root.is_absolute():
        if execution_ready:
            raise ProfileError("workspace_root must be absolute in execution-ready mode")
        return profile
    root = Path(os.path.normpath(str(root)))
    result = dict(profile)
    result["workspace_root"] = str(root)
    result["evidence_root"] = resolve_path(profile["evidence_root"], root, "evidence_root")
    result["tooling"] = {
        key: resolve_path(value, root, "tooling." + key)
        for key, value in profile["tooling"].items()
    }
    result["repositories"] = {
        key: dict(value, path=resolve_path(value["path"], root, "repositories." + key + ".path"))
        for key, value in profile["repositories"].items()
    }
    return result


def human_lines(value, prefix=""):
    for key, child in value.items():
        label = prefix + key
        if isinstance(child, dict):
            yield from human_lines(child, label + ".")
        else:
            yield label + ": " + str(child)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, help="YAML local profile path")
    parser.add_argument("--execution-ready", action="store_true")
    parser.add_argument("--format", choices=("human", "yaml"), default="human")
    args = parser.parse_args(argv)
    schema_path = Path(__file__).resolve().parents[1] / "config" / "local_profile.schema.yml"
    try:
        result = resolve(read_yaml(args.profile), read_yaml(schema_path), args.execution_ready)
    except ProfileError as exc:
        parser.exit(2, "local profile error: " + str(exc) + "\n")
    if args.format == "yaml":
        yaml.safe_dump(result, sys.stdout, sort_keys=False)
    else:
        print("\n".join(human_lines(result)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
