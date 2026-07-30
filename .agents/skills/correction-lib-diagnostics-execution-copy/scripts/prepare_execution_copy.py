#!/usr/bin/env python3
"""Validate and materialize bounded diagnostics copies without execution."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import difflib
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import secrets
import stat
import subprocess
import sys
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


SKILL_VERSION = "1.0.0"
RENDERER_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"
MANIFEST_VERSION = "1.0.0"
MAX_ROOTS = 8
MAX_ENTRIES = 64
MAX_FILE_BYTES = 16_777_216
MAX_TOTAL_BYTES = 67_108_864
MAX_TRANSFORMS = 16

DIAGNOSTIC_ORDER = [
    "PATH001", "PATH002", "PATH003", "PATH004",
    "TYPE001", "TYPE002", "TYPE003",
    "SIZE001", "SIZE002",
    "COLLISION001", "COLLISION002",
    "TRANSFORM001", "TRANSFORM002", "TRANSFORM003",
    "HASH001", "HASH002",
    "SECRET001", "SECRET002", "SECRET003",
    "PROVENANCE001", "PROVENANCE002",
    "EXECUTION001",
    "GOVERNANCE001", "GOVERNANCE002",
    "RENDER001", "RENDER002",
]
DIAGNOSTIC_INDEX = {value: index for index, value in enumerate(DIAGNOSTIC_ORDER)}
FAMILY = {value: value.rstrip("0123456789") for value in DIAGNOSTIC_ORDER}
BUILTIN_PATH_COMPONENTS = {".ssh", ".gnupg", ".aws"}
PRIVATE_KEY_FILENAMES = {"id_rsa", "id_dsa", "id_ecdsa", "id_ed25519"}
CREDENTIAL_FILENAMES = {".netrc", "credentials", "credentials.json", "token", "tokens.json"}
PRIVATE_KEY_HEADERS = (
    "-----BEGIN PRIVATE KEY-----",
    "-----BEGIN ENCRYPTED PRIVATE KEY-----",
    "-----BEGIN RSA PRIVATE KEY-----",
    "-----BEGIN DSA PRIVATE KEY-----",
    "-----BEGIN EC PRIVATE KEY-----",
    "-----BEGIN OPENSSH PRIVATE KEY-----",
)
FORBIDDEN_FIELDS = {
    "command", "commands", "argv", "shell", "execute", "run", "submit",
    "retry", "resume", "overwrite", "cleanup", "callback",
    "environment_activation", "activation_command",
}
TOP_FIELDS = {
    "manifest_version", "copy_id", "title", "source_roots",
    "destination_root", "entries", "limits", "secret_policy", "provenance",
    "execution_boundary",
}
ENTRY_FIELDS = {
    "entry_id", "source_path", "destination_path", "copy_mode",
    "expected_source_sha256", "expected_source_state", "transformations",
    "preserve_executable_bit",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def make_diag(
    diagnostic_id: str,
    message: str,
    *,
    entry_id: Optional[str] = None,
    field: Optional[str] = None,
    safe_path: Optional[str] = None,
    locator: str = "copy contract 1.0.0",
) -> Dict[str, Any]:
    warning = diagnostic_id == "PROVENANCE002"
    return {
        "diagnostic_id": diagnostic_id,
        "family": FAMILY[diagnostic_id],
        "severity": "warning" if warning else "error",
        "blocking": not warning,
        "entry_id": entry_id,
        "field": field,
        "safe_path": safe_path,
        "message": message,
        "contract_locator": locator,
    }


def sort_diagnostics(diags: Iterable[Dict[str, Any]], entry_order: Dict[Optional[str], int]) -> List[Dict[str, Any]]:
    return sorted(
        diags,
        key=lambda d: (
            entry_order.get(d.get("entry_id"), -1),
            DIAGNOSTIC_INDEX.get(d["diagnostic_id"], 999),
            d.get("field") or "",
            d.get("safe_path") or "",
            d["message"],
        ),
    )


class CopyError(Exception):
    def __init__(self, exit_code: int, diagnostics: Sequence[Dict[str, Any]], summary: Optional[Dict[str, Any]] = None):
        super().__init__("diagnostics execution copy failed")
        self.exit_code = exit_code
        self.diagnostics = list(diagnostics)
        self.summary = summary or {}


def workspace_root() -> Path:
    return Path(__file__).resolve().parents[4]


def verify_governance(binding_path: Path) -> Dict[str, Any]:
    try:
        binding = json.loads(binding_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CopyError(4, [make_diag("GOVERNANCE002", f"Governance binding is invalid: {exc}", field="governance_binding")])
    required = {"binding_version", "schema_version", "renderer_version", "agents_path", "agents_sha256", "cpc_path", "cpc_sha256"}
    if not required.issubset(binding) or binding.get("schema_version") != SCHEMA_VERSION or binding.get("renderer_version") != RENDERER_VERSION:
        raise CopyError(4, [make_diag("GOVERNANCE002", "Governance binding metadata is incomplete or inconsistent.", field="governance_binding")])
    root = workspace_root()
    try:
        agents_hash = sha256_bytes((root / binding["agents_path"]).read_bytes())
        cpc_hash = sha256_bytes((root / binding["cpc_path"]).read_bytes())
    except OSError as exc:
        raise CopyError(4, [make_diag("GOVERNANCE002", f"Governance source cannot be read: {exc}", field="governance_binding")])
    if agents_hash != binding["agents_sha256"] or cpc_hash != binding["cpc_sha256"]:
        raise CopyError(4, [make_diag("GOVERNANCE001", "Governance binding does not match complete live AGENTS.md and CPC.md bytes.", field="governance_binding")])
    return {"agents_sha256": agents_hash, "cpc_sha256": cpc_hash}


def _find_forbidden_key(value: Any, prefix: str = "") -> Optional[Tuple[str, str]]:
    if isinstance(value, dict):
        for key, child in value.items():
            location = f"{prefix}.{key}" if prefix else key
            if str(key).lower() in FORBIDDEN_FIELDS:
                return str(key), location
            found = _find_forbidden_key(child, location)
            if found:
                return found
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found = _find_forbidden_key(child, f"{prefix}[{index}]")
            if found:
                return found
    return None


def _type_error(field: str, message: str) -> Dict[str, Any]:
    return make_diag("TYPE001", message, field=field, locator="manifest schema 1.0.0")


def validate_manifest_shape(manifest: Any) -> Tuple[List[Dict[str, Any]], Dict[Optional[str], int]]:
    diags: List[Dict[str, Any]] = []
    entry_order: Dict[Optional[str], int] = {None: -1}
    if not isinstance(manifest, dict):
        return [_type_error("<root>", "Manifest must be a JSON object.")], entry_order
    forbidden = _find_forbidden_key(manifest)
    if forbidden:
        diags.append(make_diag("EXECUTION001", f"Execution-related field '{forbidden[0]}' is forbidden.", field=forbidden[1]))
    unknown = set(manifest) - TOP_FIELDS
    missing = TOP_FIELDS - set(manifest)
    for field in sorted(unknown):
        diags.append(_type_error(field, "Additional manifest properties are forbidden."))
    for field in sorted(missing):
        diags.append(_type_error(field, "Required manifest field is missing."))
    if missing:
        return diags, entry_order
    if manifest["manifest_version"] != MANIFEST_VERSION:
        diags.append(_type_error("manifest_version", "manifest_version must be 1.0.0."))
    if not isinstance(manifest["copy_id"], str) or not manifest["copy_id"] or len(manifest["copy_id"]) > 64 or manifest["copy_id"] != manifest["copy_id"].lower() or not manifest["copy_id"].replace("_", "a").isalnum() or not manifest["copy_id"][0].isalpha():
        diags.append(_type_error("copy_id", "copy_id must be a lowercase snake_case identifier of at most 64 characters."))
    if not isinstance(manifest["title"], str) or not manifest["title"].strip():
        diags.append(_type_error("title", "title must be a nonempty string."))
    roots = manifest["source_roots"]
    if not isinstance(roots, list) or not (1 <= len(roots) <= MAX_ROOTS) or not all(isinstance(p, str) and os.path.isabs(p) for p in roots):
        diags.append(_type_error("source_roots", "source_roots must contain 1 to 8 absolute paths."))
    if not isinstance(manifest["destination_root"], str) or not os.path.isabs(manifest["destination_root"]):
        diags.append(_type_error("destination_root", "destination_root must be absolute."))
    limits = manifest["limits"]
    if not isinstance(limits, dict) or set(limits) != {"max_entries", "max_file_bytes", "max_total_bytes"}:
        diags.append(_type_error("limits", "limits must contain exactly max_entries, max_file_bytes, and max_total_bytes."))
    else:
        for field, hard in (("max_entries", MAX_ENTRIES), ("max_file_bytes", MAX_FILE_BYTES), ("max_total_bytes", MAX_TOTAL_BYTES)):
            value = limits[field]
            if not isinstance(value, int) or isinstance(value, bool) or not (1 <= value <= hard):
                diags.append(_type_error(f"limits.{field}", f"{field} must be a positive integer no greater than {hard}."))
    secret_policy = manifest["secret_policy"]
    if not isinstance(secret_policy, dict) or set(secret_policy) != {"mode", "additional_forbidden_path_components"}:
        diags.append(_type_error("secret_policy", "secret_policy must contain exactly mode and additional_forbidden_path_components."))
    else:
        if secret_policy["mode"] != "block_documented_matches_no_redaction":
            diags.append(make_diag("SECRET001", "Built-in secret policy cannot be disabled or weakened.", field="secret_policy.mode"))
        additions = secret_policy["additional_forbidden_path_components"]
        if not isinstance(additions, list) or not all(isinstance(x, str) and x and "/" not in x for x in additions):
            diags.append(_type_error("secret_policy.additional_forbidden_path_components", "Additional forbidden components must be nonempty path-component strings."))
    provenance = manifest["provenance"]
    expected_provenance = {
        "record_git_when_available": True,
        "require_working_tree_sha256": True,
        "require_source_mode": True,
    }
    if provenance != expected_provenance:
        diags.append(make_diag("PROVENANCE001", "The required provenance policy must be enabled exactly.", field="provenance"))
    boundary = manifest["execution_boundary"]
    expected_boundary = {
        "copy_preparation_authorized": True,
        "execution_not_authorized": True,
        "render_execution_command": False,
    }
    if boundary != expected_boundary:
        diags.append(make_diag("EXECUTION001", "The fixed no-execution boundary is required.", field="execution_boundary"))
    entries = manifest["entries"]
    if not isinstance(entries, list) or not entries:
        diags.append(_type_error("entries", "entries must be a nonempty array."))
        return diags, entry_order
    max_entries = limits.get("max_entries", MAX_ENTRIES) if isinstance(limits, dict) else MAX_ENTRIES
    if len(entries) > min(MAX_ENTRIES, max_entries):
        diags.append(make_diag("SIZE002", "Entry count exceeds the manifest or implementation limit.", field="entries"))
    seen_ids: set[str] = set()
    seen_destinations: set[str] = set()
    states = {"tracked_clean", "tracked_modified", "untracked", "outside_git", "any_recorded"}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            diags.append(_type_error(f"entries[{index}]", "Every entry must be an object."))
            continue
        entry_id = entry.get("entry_id") if isinstance(entry.get("entry_id"), str) else f"<entry_{index}>"
        entry_order[entry_id] = index
        unknown_entry = set(entry) - ENTRY_FIELDS
        missing_entry = ENTRY_FIELDS - set(entry)
        for field in sorted(unknown_entry):
            diags.append(make_diag("TYPE001", "Additional entry properties are forbidden.", entry_id=entry_id, field=field))
        for field in sorted(missing_entry):
            diags.append(make_diag("TYPE001", "Required entry field is missing.", entry_id=entry_id, field=field))
        if missing_entry:
            continue
        if not entry_id or len(entry_id) > 64 or entry_id != entry_id.lower() or not entry_id.replace("_", "a").isalnum() or not entry_id[0].isalpha():
            diags.append(make_diag("TYPE001", "entry_id must be lowercase snake_case.", entry_id=entry_id, field="entry_id"))
        if entry_id in seen_ids:
            diags.append(make_diag("TYPE001", "entry_id must be unique.", entry_id=entry_id, field="entry_id"))
        seen_ids.add(entry_id)
        source_path = entry["source_path"]
        if not isinstance(source_path, str) or not os.path.isabs(source_path):
            diags.append(make_diag("PATH001", "source_path must be absolute.", entry_id=entry_id, field="source_path"))
        destination_path = entry["destination_path"]
        if not isinstance(destination_path, str) or not valid_relative_path(destination_path):
            diags.append(make_diag("PATH002", "destination_path must be normalized, relative, and contain no empty, dot, or dot-dot component.", entry_id=entry_id, field="destination_path"))
        elif destination_path in seen_destinations:
            diags.append(make_diag("PATH002", "destination_path must be unique.", entry_id=entry_id, field="destination_path"))
        seen_destinations.add(destination_path if isinstance(destination_path, str) else "")
        if entry["copy_mode"] not in {"exact_copy", "declared_text_transform"}:
            diags.append(make_diag("TRANSFORM001", "Unsupported copy_mode.", entry_id=entry_id, field="copy_mode"))
        source_hash = entry["expected_source_sha256"]
        if not isinstance(source_hash, str) or len(source_hash) != 64 or any(c not in "0123456789abcdef" for c in source_hash):
            diags.append(make_diag("HASH001", "expected_source_sha256 must be a lowercase SHA-256.", entry_id=entry_id, field="expected_source_sha256"))
        if entry["expected_source_state"] not in states:
            diags.append(make_diag("PROVENANCE001", "Unsupported expected_source_state.", entry_id=entry_id, field="expected_source_state"))
        if not isinstance(entry["preserve_executable_bit"], bool):
            diags.append(make_diag("TYPE001", "preserve_executable_bit must be boolean.", entry_id=entry_id, field="preserve_executable_bit"))
        transforms = entry["transformations"]
        if not isinstance(transforms, list):
            diags.append(make_diag("TRANSFORM001", "transformations must be an array.", entry_id=entry_id, field="transformations"))
            continue
        if entry["copy_mode"] == "exact_copy" and transforms:
            diags.append(make_diag("TRANSFORM001", "exact_copy requires an empty transformations array.", entry_id=entry_id, field="transformations"))
        if entry["copy_mode"] == "declared_text_transform" and not (1 <= len(transforms) <= MAX_TRANSFORMS):
            diags.append(make_diag("TRANSFORM001", "declared_text_transform requires 1 to 16 transformations.", entry_id=entry_id, field="transformations"))
        for t_index, transform in enumerate(transforms):
            field = f"transformations[{t_index}]"
            if not isinstance(transform, dict) or set(transform) != {"operation", "old", "new", "expected_match_count"}:
                diags.append(make_diag("TRANSFORM001", "Transformation fields are invalid.", entry_id=entry_id, field=field))
                continue
            if transform["operation"] != "exact_text_replacement" or not isinstance(transform["old"], str) or not transform["old"] or not isinstance(transform["new"], str) or not isinstance(transform["expected_match_count"], int) or isinstance(transform["expected_match_count"], bool) or transform["expected_match_count"] < 1:
                diags.append(make_diag("TRANSFORM001", "Only exact_text_replacement with literal text and a positive count is supported.", entry_id=entry_id, field=field))
    return sort_diagnostics(diags, entry_order), entry_order


def valid_relative_path(value: str) -> bool:
    if not value or value.startswith("/") or "\\" in value:
        return False
    parts = value.split("/")
    return all(part not in {"", ".", ".."} for part in parts) and str(PurePosixPath(value)) == value


def _open_abs_dir_nofollow(path: Path) -> int:
    if not path.is_absolute() or not hasattr(os, "O_NOFOLLOW"):
        raise OSError("absolute descriptor no-follow support is required")
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for component in path.parts[1:]:
            next_fd = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        return fd
    except Exception:
        os.close(fd)
        raise


def _choose_source_root(source: Path, roots: Sequence[Path]) -> Optional[Path]:
    candidates = []
    for root in roots:
        try:
            source.relative_to(root)
            candidates.append(root)
        except ValueError:
            pass
    return max(candidates, key=lambda p: len(p.parts)) if candidates else None


def _open_source_descriptor(source: Path, root: Path) -> int:
    relative = source.relative_to(root)
    if not relative.parts:
        raise OSError("source cannot equal source root")
    fd = _open_abs_dir_nofollow(root)
    try:
        for component in relative.parts[:-1]:
            next_fd = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        file_fd = os.open(relative.parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        os.close(fd)
        return file_fd
    except Exception:
        os.close(fd)
        raise


def _read_stable(fd: int, max_bytes: int) -> Tuple[bytes, os.stat_result]:
    before = os.fstat(fd)
    chunks: List[bytes] = []
    total = 0
    while True:
        chunk = os.read(fd, min(1_048_576, max_bytes + 1 - total))
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
        if total > max_bytes:
            break
    after = os.fstat(fd)
    stable_fields = ("st_dev", "st_ino", "st_size", "st_mode", "st_mtime_ns", "st_ctime_ns")
    if any(getattr(before, name) != getattr(after, name) for name in stable_fields):
        raise RuntimeError("source metadata changed during read")
    return b"".join(chunks), after


def _git(command: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *command],
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=10,
    )


def collect_git_provenance(source: Path) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    probe = source.parent
    repository: Optional[Path] = None
    for candidate in (probe, *probe.parents):
        if (candidate / ".git").exists():
            repository = candidate
            break
    empty = {
        "repository_root": None,
        "repository_relative_path": None,
        "git_branch_record": None,
        "git_commit_record": None,
        "tracked_state": "outside_git",
        "git_blob_hash": None,
    }
    if repository is None:
        return empty, make_diag("PROVENANCE002", "Optional Git provenance is unavailable.", field="git")
    try:
        relative = source.relative_to(repository).as_posix()
        branch_result = _git(["branch", "--show-current"], repository)
        commit_result = _git(["rev-parse", "HEAD"], repository)
        tracked_result = _git(["ls-files", "--error-unmatch", "--", relative], repository)
        tracked = tracked_result.returncode == 0
        status_result = _git(["status", "--porcelain=v1", "--", relative], repository)
        if tracked:
            state = "tracked_modified" if status_result.stdout.strip() else "tracked_clean"
            blob_result = _git(["ls-files", "-s", "--", relative], repository)
            blob_hash = blob_result.stdout.split()[1] if blob_result.returncode == 0 and blob_result.stdout.split() else None
        else:
            state = "untracked"
            blob_hash = None
        return {
            "repository_root": str(repository),
            "repository_relative_path": relative,
            "git_branch_record": branch_result.stdout.strip() or None,
            "git_commit_record": commit_result.stdout.strip() if commit_result.returncode == 0 else None,
            "tracked_state": state,
            "git_blob_hash": blob_hash,
        }, None
    except (OSError, subprocess.SubprocessError, ValueError):
        return empty, make_diag("PROVENANCE002", "Optional Git provenance is unavailable.", field="git")


def _path_secret_diagnostics(path: Path, additional: Sequence[str], entry_id: str, field: str) -> List[Dict[str, Any]]:
    components = {part.lower() for part in path.parts}
    blocked = BUILTIN_PATH_COMPONENTS | {item.lower() for item in additional}
    diags = []
    if components & blocked:
        diags.append(make_diag("SECRET001", "Path contains a forbidden secret-bearing component.", entry_id=entry_id, field=field, safe_path=str(path)))
    name = path.name.lower()
    if name in PRIVATE_KEY_FILENAMES:
        diags.append(make_diag("SECRET001", "Private-key filename is forbidden.", entry_id=entry_id, field=field, safe_path=str(path)))
    if name in CREDENTIAL_FILENAMES:
        diags.append(make_diag("SECRET003", "Credential-like filename is forbidden.", entry_id=entry_id, field=field, safe_path=str(path)))
    return diags


def _mode_class(mode: int) -> Tuple[bool, bool]:
    return stat.S_ISREG(mode), bool(mode & 0o111)


def _apply_transforms(entry: Dict[str, Any], source_text: str) -> Tuple[str, List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    current = source_text
    inventory = []
    for transform in entry["transformations"]:
        input_hash = sha256_bytes(current.encode("utf-8"))
        count = current.count(transform["old"])
        if count != transform["expected_match_count"]:
            return current, inventory, make_diag(
                "TRANSFORM002",
                f"Observed {count} literal matches; expected {transform['expected_match_count']}.",
                entry_id=entry["entry_id"],
                field="transformations",
            )
        current = current.replace(transform["old"], transform["new"])
        inventory.append({
            "input_sha256": input_hash,
            "operation": "exact_text_replacement",
            "old": transform["old"],
            "new": transform["new"],
            "expected_match_count": transform["expected_match_count"],
            "observed_match_count": count,
            "output_sha256": sha256_bytes(current.encode("utf-8")),
        })
    return current, inventory, None


def preflight(manifest: Dict[str, Any], entry_order: Dict[Optional[str], int]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], int]:
    diags: List[Dict[str, Any]] = []
    prepared: List[Dict[str, Any]] = []
    roots = [Path(value) for value in manifest["source_roots"]]
    destination_root = Path(manifest["destination_root"])
    root_fds: List[int] = []
    try:
        for root in roots:
            try:
                root_fds.append(_open_abs_dir_nofollow(root))
            except OSError as exc:
                diags.append(make_diag("PATH004", f"Source root cannot be opened without following links: {exc}", field="source_roots", safe_path=str(root)))
        try:
            destination_fd = _open_abs_dir_nofollow(destination_root)
        except OSError as exc:
            diags.append(make_diag("PATH004", f"Destination root cannot be opened without following links: {exc}", field="destination_root", safe_path=str(destination_root)))
            destination_fd = -1
        for root in roots:
            try:
                destination_root.relative_to(root)
                diags.append(make_diag("PATH003", "destination_root must not equal or be contained under a source_root.", field="destination_root", safe_path=str(destination_root)))
            except ValueError:
                pass
        if destination_fd >= 0 and os.path.lexists(destination_root / manifest["copy_id"]):
            diags.append(make_diag("COLLISION001", "Final copy root already exists.", field="copy_id", safe_path=str(destination_root / manifest["copy_id"])))
        total = 0
        additional = manifest["secret_policy"]["additional_forbidden_path_components"]
        for entry in manifest["entries"]:
            entry_id = entry["entry_id"]
            source = Path(entry["source_path"])
            destination = Path(entry["destination_path"])
            diags.extend(_path_secret_diagnostics(source, additional, entry_id, "source_path"))
            diags.extend(_path_secret_diagnostics(destination, additional, entry_id, "destination_path"))
            root = _choose_source_root(source, roots)
            if root is None:
                diags.append(make_diag("PATH001", "Source is outside every allowed source root.", entry_id=entry_id, field="source_path", safe_path=str(source)))
                continue
            try:
                fd = _open_source_descriptor(source, root)
            except OSError as exc:
                diagnostic_id = "PATH004" if isinstance(exc, (OSError,)) else "TYPE001"
                diags.append(make_diag(diagnostic_id, f"Source cannot be opened descriptor-safely: {exc}", entry_id=entry_id, field="source_path", safe_path=str(source)))
                continue
            try:
                initial = os.fstat(fd)
                if not stat.S_ISREG(initial.st_mode):
                    diags.append(make_diag("TYPE001", "Source must be a regular file.", entry_id=entry_id, field="source_path", safe_path=str(source)))
                    continue
                if initial.st_nlink != 1:
                    diags.append(make_diag("TYPE003", "Hard-linked source is forbidden.", entry_id=entry_id, field="source_path", safe_path=str(source)))
                    continue
                max_file = manifest["limits"]["max_file_bytes"]
                if initial.st_size > max_file:
                    diags.append(make_diag("SIZE001", "Source exceeds the per-file byte limit.", entry_id=entry_id, field="source_path", safe_path=str(source)))
                    continue
                try:
                    data, final_stat = _read_stable(fd, max_file)
                except RuntimeError:
                    diags.append(make_diag("HASH001", "Source changed during read.", entry_id=entry_id, field="source_path", safe_path=str(source)))
                    continue
                if len(data) > max_file:
                    diags.append(make_diag("SIZE001", "Source exceeds the per-file byte limit.", entry_id=entry_id, field="source_path", safe_path=str(source)))
                    continue
            finally:
                os.close(fd)
            total += len(data)
            try:
                text = data.decode("utf-8", "strict")
            except UnicodeDecodeError:
                diags.append(make_diag("TYPE002", "Source is not strict UTF-8 text.", entry_id=entry_id, field="source_path", safe_path=str(source)))
                continue
            source_hash = sha256_bytes(data)
            if source_hash != entry["expected_source_sha256"]:
                diags.append(make_diag("HASH001", "Source SHA-256 does not match expected_source_sha256.", entry_id=entry_id, field="expected_source_sha256", safe_path=str(source)))
                continue
            if any(header in text for header in PRIVATE_KEY_HEADERS):
                diags.append(make_diag("SECRET002", "PEM private-key content is forbidden.", entry_id=entry_id, field="source_path", safe_path=str(source)))
                continue
            output_text, transform_inventory, transform_diag = _apply_transforms(entry, text)
            if transform_diag:
                diags.append(transform_diag)
                continue
            output = output_text.encode("utf-8")
            destination_mode = 0o750 if entry["preserve_executable_bit"] and bool(final_stat.st_mode & 0o111) else 0o640
            git_record, git_warning = collect_git_provenance(source)
            if git_warning:
                git_warning["entry_id"] = entry_id
                git_warning["safe_path"] = str(source)
                diags.append(git_warning)
            observed_state = git_record["tracked_state"]
            if entry["expected_source_state"] != "any_recorded" and entry["expected_source_state"] != observed_state:
                diags.append(make_diag("PROVENANCE001", f"Observed source state '{observed_state}' does not match expected '{entry['expected_source_state']}'.", entry_id=entry_id, field="expected_source_state", safe_path=str(source)))
                continue
            diff = ""
            if entry["copy_mode"] == "declared_text_transform":
                diff = "".join(difflib.unified_diff(
                    text.splitlines(keepends=True),
                    output_text.splitlines(keepends=True),
                    fromfile=f"a/{entry['destination_path']}",
                    tofile=f"b/{entry['destination_path']}",
                    lineterm="\n",
                ))
            prepared.append({
                "entry": entry,
                "source_root": str(root),
                "source_data": data,
                "output_data": output,
                "source_sha256": source_hash,
                "destination_sha256": sha256_bytes(output),
                "source_size": len(data),
                "destination_size": len(output),
                "source_mode": stat.S_IMODE(final_stat.st_mode),
                "destination_mode": destination_mode,
                "source_device": final_stat.st_dev,
                "source_inode": final_stat.st_ino,
                "source_mtime_ns": final_stat.st_mtime_ns,
                "source_mode_class": _mode_class(final_stat.st_mode),
                "resolved_source_path": os.path.realpath(source),
                "git": git_record,
                "transformation_inventory": transform_inventory,
                "diff": diff,
            })
        if total > manifest["limits"]["max_total_bytes"]:
            diags.append(make_diag("SIZE002", "Aggregate source bytes exceed max_total_bytes.", field="limits.max_total_bytes"))
        return sort_diagnostics(diags, entry_order), prepared, destination_fd
    finally:
        for fd in root_fds:
            os.close(fd)


def _mkdirs_at(root_fd: int, parts: Sequence[str], mode: int = 0o750) -> int:
    fd = os.dup(root_fd)
    try:
        for part in parts:
            try:
                os.mkdir(part, mode=mode, dir_fd=fd)
            except FileExistsError:
                pass
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        return fd
    except Exception:
        os.close(fd)
        raise


def _write_exclusive_at(root_fd: int, relative: str, data: bytes, mode: int) -> None:
    parts = PurePosixPath(relative).parts
    parent_fd = _mkdirs_at(root_fd, parts[:-1])
    try:
        fd = os.open(parts[-1], os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode, dir_fd=parent_fd)
        try:
            offset = 0
            while offset < len(data):
                offset += os.write(fd, data[offset:])
            os.fsync(fd)
            os.fchmod(fd, mode)
        finally:
            os.close(fd)
    finally:
        os.close(parent_fd)


def _read_at(root_fd: int, relative: str) -> Tuple[bytes, int]:
    parts = PurePosixPath(relative).parts
    parent_fd = _mkdirs_at(root_fd, parts[:-1])
    try:
        fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent_fd)
        try:
            info = os.fstat(fd)
            chunks = []
            while True:
                chunk = os.read(fd, 1_048_576)
                if not chunk:
                    break
                chunks.append(chunk)
            return b"".join(chunks), stat.S_IMODE(info.st_mode)
        finally:
            os.close(fd)
    finally:
        os.close(parent_fd)


def _recheck_source(prepared: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    source = Path(prepared["entry"]["source_path"])
    root = Path(prepared["source_root"])
    try:
        fd = _open_source_descriptor(source, root)
        try:
            data, info = _read_stable(fd, MAX_FILE_BYTES)
        finally:
            os.close(fd)
    except (OSError, RuntimeError):
        return make_diag("HASH001", "Source could not be reopened stably before publication.", entry_id=prepared["entry"]["entry_id"], field="source_path", safe_path=str(source))
    if (
        info.st_dev != prepared["source_device"]
        or info.st_ino != prepared["source_inode"]
        or len(data) != prepared["source_size"]
        or _mode_class(info.st_mode) != tuple(prepared["source_mode_class"])
        or sha256_bytes(data) != prepared["source_sha256"]
    ):
        return make_diag("HASH001", "Source identity, mode class, size, or SHA-256 changed before publication.", entry_id=prepared["entry"]["entry_id"], field="source_path", safe_path=str(source))
    return None


def _inventory_bytes(prepared: Sequence[Dict[str, Any]]) -> bytes:
    output = io.StringIO(newline="")
    fields = [
        "entry_id", "copy_mode", "source_path", "destination_path",
        "source_size", "destination_size", "source_sha256", "destination_sha256",
        "source_mode", "destination_mode", "tracked_state", "transformation_count",
    ]
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for item in prepared:
        entry = item["entry"]
        writer.writerow({
            "entry_id": entry["entry_id"],
            "copy_mode": entry["copy_mode"],
            "source_path": entry["source_path"],
            "destination_path": entry["destination_path"],
            "source_size": item["source_size"],
            "destination_size": item["destination_size"],
            "source_sha256": item["source_sha256"],
            "destination_sha256": item["destination_sha256"],
            "source_mode": oct(item["source_mode"]),
            "destination_mode": oct(item["destination_mode"]),
            "tracked_state": item["git"]["tracked_state"],
            "transformation_count": len(item["transformation_inventory"]),
        })
    return output.getvalue().encode("utf-8")


def _resolved_manifest(manifest: Dict[str, Any], prepared: Sequence[Dict[str, Any]], manifest_hash: str) -> Dict[str, Any]:
    resolved = json.loads(json.dumps(manifest))
    resolved["manifest_hash"] = manifest_hash
    resolved["skill_version"] = SKILL_VERSION
    resolved["renderer_version"] = RENDERER_VERSION
    resolved["schema_version"] = SCHEMA_VERSION
    roots = {item["entry"]["entry_id"]: item["source_root"] for item in prepared}
    for entry in resolved["entries"]:
        entry["selected_source_root"] = roots[entry["entry_id"]]
    return resolved


def _provenance(manifest: Dict[str, Any], prepared: Sequence[Dict[str, Any]], manifest_hash: str, governance: Dict[str, Any], timestamp: str, warnings: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    records = []
    for item in prepared:
        entry = item["entry"]
        record = {
            "entry_id": entry["entry_id"],
            "absolute_source_path": entry["source_path"],
            "resolved_source_path": item["resolved_source_path"],
            "source_root": item["source_root"],
            **item["git"],
            "working_tree_sha256": item["source_sha256"],
            "source_size": item["source_size"],
            "source_mode": item["source_mode"],
            "source_device": item["source_device"],
            "source_inode": item["source_inode"],
            "copy_timestamp": timestamp,
            "copy_tool_version": RENDERER_VERSION,
            "manifest_hash": manifest_hash,
            "destination_relative_path": entry["destination_path"],
            "destination_sha256": item["destination_sha256"],
            "destination_mode": item["destination_mode"],
            "transformation_inventory": item["transformation_inventory"],
        }
        records.append(record)
    return {
        "copy_id": manifest["copy_id"],
        "copy_timestamp": timestamp,
        "skill_version": SKILL_VERSION,
        "renderer_version": RENDERER_VERSION,
        "schema_version": SCHEMA_VERSION,
        "manifest_hash": manifest_hash,
        "governance": governance,
        "warnings": list(warnings),
        "entries": records,
        "execution_not_authorized": True,
    }


def materialize(
    manifest: Dict[str, Any],
    prepared: Sequence[Dict[str, Any]],
    destination_fd: int,
    governance: Dict[str, Any],
    warnings: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    nonce = secrets.token_hex(6)
    staging_name = f".staging_{manifest['copy_id']}_{nonce}"
    incomplete_name = f".incomplete_{manifest['copy_id']}_{nonce}"
    staging_fd = -1
    staging_created = False
    timestamp = utc_now()
    manifest_hash = sha256_bytes(canonical_json(manifest))
    try:
        try:
            os.mkdir(staging_name, mode=0o750, dir_fd=destination_fd)
        except FileExistsError:
            raise CopyError(3, [make_diag("COLLISION002", "Generated staging identity already exists.", field="copy_id")])
        staging_created = True
        staging_fd = os.open(staging_name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=destination_fd)
        resolved = _resolved_manifest(manifest, prepared, manifest_hash)
        provenance = _provenance(manifest, prepared, manifest_hash, governance, timestamp, warnings)
        generated: Dict[str, bytes] = {
            "copy_manifest.resolved.json": json.dumps(resolved, indent=2, sort_keys=True).encode("utf-8") + b"\n",
            "copy_inventory.csv": _inventory_bytes(prepared),
            "copy_provenance.json": json.dumps(provenance, indent=2, sort_keys=True).encode("utf-8") + b"\n",
            "copy_diff.patch": "".join(item["diff"] for item in prepared).encode("utf-8"),
        }
        for relative, data in generated.items():
            _write_exclusive_at(staging_fd, relative, data, 0o640)
        for item in prepared:
            relative = f"materialized/{item['entry']['destination_path']}"
            _write_exclusive_at(staging_fd, relative, item["output_data"], item["destination_mode"])
        artifact_hashes: Dict[str, str] = {}
        for relative, expected in generated.items():
            actual, mode = _read_at(staging_fd, relative)
            if actual != expected or mode != 0o640:
                raise CopyError(5, [make_diag("RENDER002", f"Generated artifact reopening failed for {relative}.", field=relative)])
            artifact_hashes[relative] = sha256_bytes(actual)
        for item in prepared:
            relative = f"materialized/{item['entry']['destination_path']}"
            actual, mode = _read_at(staging_fd, relative)
            if sha256_bytes(actual) != item["destination_sha256"] or mode != item["destination_mode"]:
                raise CopyError(5, [make_diag("HASH002", "Materialized file hash or mode failed independent reopening.", entry_id=item["entry"]["entry_id"], field="destination_path", safe_path=relative)])
            artifact_hashes[relative] = sha256_bytes(actual)
        for item in prepared:
            source_diag = _recheck_source(item)
            if source_diag:
                raise CopyError(5, [source_diag])
        validation = {
            "valid_schema": True,
            "materialization_requested": True,
            "materialization_completed": True,
            "copy_preparation_authorized": True,
            "copy_materialization_completed": True,
            "execution_not_authorized": True,
            "error_count": 0,
            "warning_count": len(warnings),
            "diagnostics": list(warnings),
            "artifact_hashes": artifact_hashes,
            "final_root": str(Path(manifest["destination_root"]) / manifest["copy_id"]),
            "incomplete_root": None,
        }
        validation_bytes = json.dumps(validation, indent=2, sort_keys=True).encode("utf-8") + b"\n"
        _write_exclusive_at(staging_fd, "copy_validation.json", validation_bytes, 0o640)
        reopened_validation, validation_mode = _read_at(staging_fd, "copy_validation.json")
        if reopened_validation != validation_bytes or validation_mode != 0o640:
            raise CopyError(5, [make_diag("RENDER002", "copy_validation.json failed independent reopening.", field="copy_validation.json")])
        os.fsync(staging_fd)
        os.close(staging_fd)
        staging_fd = -1
        os.rename(staging_name, manifest["copy_id"], src_dir_fd=destination_fd, dst_dir_fd=destination_fd)
        staging_created = False
        return validation
    except CopyError as exc:
        if staging_fd >= 0:
            os.close(staging_fd)
            staging_fd = -1
        if staging_created:
            incomplete_root = _preserve_incomplete(destination_fd, staging_name, incomplete_name, manifest, exc.diagnostics)
            exc.summary["incomplete_root"] = incomplete_root
            if exc.exit_code != 3:
                exc.exit_code = 5
        raise
    except Exception as exc:
        if staging_fd >= 0:
            os.close(staging_fd)
        diagnostic = make_diag("RENDER001", f"Staging or atomic publication failed: {exc}", field="destination_root")
        incomplete_root = _preserve_incomplete(destination_fd, staging_name, incomplete_name, manifest, [diagnostic]) if staging_created else None
        raise CopyError(5, [diagnostic], {"incomplete_root": incomplete_root})


def _preserve_incomplete(destination_fd: int, staging_name: str, incomplete_name: str, manifest: Dict[str, Any], diagnostics: Sequence[Dict[str, Any]]) -> Optional[str]:
    try:
        stage_fd = os.open(staging_name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=destination_fd)
        try:
            validation = {
                "valid_schema": True,
                "materialization_requested": True,
                "materialization_completed": False,
                "copy_preparation_authorized": True,
                "copy_materialization_completed": False,
                "execution_not_authorized": True,
                "error_count": sum(bool(d["blocking"]) for d in diagnostics),
                "warning_count": sum(not d["blocking"] for d in diagnostics),
                "diagnostics": list(diagnostics),
                "artifact_hashes": {},
                "final_root": str(Path(manifest["destination_root"]) / manifest["copy_id"]),
                "incomplete_root": str(Path(manifest["destination_root"]) / incomplete_name),
            }
            try:
                _write_exclusive_at(stage_fd, "copy_validation.json", json.dumps(validation, indent=2, sort_keys=True).encode("utf-8") + b"\n", 0o640)
            except FileExistsError:
                pass
        finally:
            os.close(stage_fd)
        os.rename(staging_name, incomplete_name, src_dir_fd=destination_fd, dst_dir_fd=destination_fd)
        return str(Path(manifest["destination_root"]) / incomplete_name)
    except Exception:
        return str(Path(manifest["destination_root"]) / staging_name)


def validate_and_prepare(manifest_path: Path, binding_path: Path, validate_only: bool) -> Dict[str, Any]:
    governance = verify_governance(binding_path)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CopyError(2, [_type_error("<manifest>", f"Manifest is not readable strict-UTF-8 JSON: {exc}")])
    shape_diags, entry_order = validate_manifest_shape(manifest)
    blocking_shape = [diag for diag in shape_diags if diag["blocking"]]
    if blocking_shape:
        exit_code = 3 if any(diag["diagnostic_id"] in {"SIZE002", "EXECUTION001", "SECRET001", "PROVENANCE001"} for diag in blocking_shape) else 2
        raise CopyError(exit_code, shape_diags)
    preflight_diags, prepared, destination_fd = preflight(manifest, entry_order)
    warnings = [diag for diag in preflight_diags if not diag["blocking"]]
    blocking = [diag for diag in preflight_diags if diag["blocking"]]
    if blocking:
        if destination_fd >= 0:
            os.close(destination_fd)
        raise CopyError(3, preflight_diags)
    manifest_hash = sha256_bytes(canonical_json(manifest))
    if validate_only:
        if destination_fd >= 0:
            os.close(destination_fd)
        return {
            "valid_schema": True,
            "materialization_requested": False,
            "materialization_completed": False,
            "copy_preparation_authorized": True,
            "copy_materialization_completed": False,
            "execution_not_authorized": True,
            "error_count": 0,
            "warning_count": len(warnings),
            "diagnostics": warnings,
            "manifest_hash": manifest_hash,
            "final_root": str(Path(manifest["destination_root"]) / manifest["copy_id"]),
            "incomplete_root": None,
        }
    try:
        return materialize(manifest, prepared, destination_fd, governance, warnings)
    finally:
        if destination_fd >= 0:
            os.close(destination_fd)


def render_human(summary: Dict[str, Any], diagnostics: Sequence[Dict[str, Any]]) -> str:
    lines = []
    for diag in diagnostics:
        location = f" [{diag['entry_id']}]" if diag.get("entry_id") else ""
        lines.append(f"{diag['severity'].upper()} {diag['diagnostic_id']}{location}: {diag['message']}")
    lines.append(
        f"validation: errors={summary.get('error_count', sum(d['blocking'] for d in diagnostics))} "
        f"warnings={summary.get('warning_count', sum(not d['blocking'] for d in diagnostics))} "
        f"materialized={str(summary.get('materialization_completed', False)).lower()} "
        "execution_not_authorized=true"
    )
    return "\n".join(lines)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Validate or materialize a bounded diagnostics copy without executing copied files.")
    skill_root = Path(__file__).resolve().parents[1]
    result.add_argument("--schema", type=Path, default=skill_root / "references" / "copy_schema.json")
    result.add_argument("--governance-binding", type=Path, default=skill_root / "references" / "governance_binding.json")
    result.add_argument("--format", choices=("human", "json"), default="human")
    result.add_argument("--json-out", type=Path)
    result.add_argument("--validate-only", action="store_true")
    result.add_argument("manifest", type=Path)
    return result


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parser().parse_args(argv)
    try:
        # Reopen the schema to ensure the installed derived contract is valid.
        schema = json.loads(args.schema.read_text(encoding="utf-8"))
        if schema.get("schema_version") != SCHEMA_VERSION or schema.get("renderer_version") != RENDERER_VERSION:
            raise CopyError(2, [_type_error("--schema", "Schema version metadata is invalid.")])
        summary = validate_and_prepare(args.manifest, args.governance_binding, args.validate_only)
        diagnostics = summary.get("diagnostics", [])
        exit_code = 0
    except CopyError as exc:
        diagnostics = exc.diagnostics
        summary = {
            "valid_schema": exc.exit_code not in {2, 4},
            "materialization_requested": not args.validate_only,
            "materialization_completed": False,
            "copy_preparation_authorized": True,
            "copy_materialization_completed": False,
            "execution_not_authorized": True,
            "error_count": sum(diag["blocking"] for diag in diagnostics),
            "warning_count": sum(not diag["blocking"] for diag in diagnostics),
            "diagnostics": diagnostics,
            "final_root": None,
            "incomplete_root": exc.summary.get("incomplete_root"),
        }
        exit_code = exc.exit_code
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        diagnostics = [_type_error("--schema", f"Schema is not readable strict-UTF-8 JSON: {exc}")]
        summary = {
            "valid_schema": False,
            "materialization_requested": not args.validate_only,
            "materialization_completed": False,
            "copy_preparation_authorized": True,
            "copy_materialization_completed": False,
            "execution_not_authorized": True,
            "error_count": 1,
            "warning_count": 0,
            "diagnostics": diagnostics,
            "final_root": None,
            "incomplete_root": None,
        }
        exit_code = 2
    serialized = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        args.json_out.write_text(serialized, encoding="utf-8")
    if args.format == "json":
        sys.stdout.write(serialized)
    else:
        sys.stdout.write(render_human(summary, diagnostics) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
