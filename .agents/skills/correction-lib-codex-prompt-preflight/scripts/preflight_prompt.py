#!/usr/bin/env python3
"""Render an inert correction-lib Markdown prompt after bounded preflight."""

from __future__ import annotations

import argparse
import ctypes
import errno
import hashlib
import json
import os
import re
import secrets
import stat
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


SKILL_VERSION = "1.1.0"
RENDERER_VERSION = "1.1.0"
OWNERSHIP_CONTRACT_VERSION = "1.1.0"
SCHEMA_VERSION = "1.1.0"
BLACK_BOX_SUITE_VERSION = "1.2.0"
TRUST_MODEL_ID = "TM-1.0-LOCAL-UNINTERRUPTED"
AUTHORITY_MODEL_ID = "AM-1.0-CLOSED-INTERSECTION"
SHARED_REGISTRY_ID = "SKR-1.0-CLOSED"
RUNTIME_INTERFACE_ID = "diagnostics_source_capture_v1_1"
READINESS_THEOREM_ID = "RT-1.1-IMMEDIATE"
FILESYSTEM_CONTRACT_ID = "FS-1.1-LINUX-NOREPLACE"
CONTEXT_VALUES = ("yes", "no", "unknown")
EVIDENCE_SEQUENCE = (
    "collect_direct_evidence",
    "serialize_evidence",
    "reopen_and_validate_evidence",
    "classify_evidence",
    "derive_verdict",
)
EVIDENCE_COMPACT = " -> ".join(EVIDENCE_SEQUENCE)
OUTPUT_NAMES = (
    "authored_prompt.md",
    "canonical_prompt.md",
    "preflight_result.json",
    "preflight_report.md",
)
RENAME_NOREPLACE = 1
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")

FIELD_ORDER = (
    "prompt_id", "short_title", "prompt_mode", "preferred_codex_model",
    "reasoning_level", "delegation_policy", "model_selection_rationale",
    "workspace_root", "repo_locations", "current_checked_out_branch",
    "current_repository_heads", "allowed_to_modify", "read_only",
    "branch_policy", "reference_branch", "target_branch", "feature_branch",
    "current_baseline_branch", "comparison_baseline",
    "integrated_baseline_mode", "dirty_worktree_policy", "preflight_profile",
    "preflight_scope_paths", "validation_ceiling", "heavy_command_permissions",
    "source_control_policy", "do_not_commit", "commit_expected",
    "commit_message_policy", "goal", "decision_question", "out_of_scope",
    "continuation", "evidence_round", "user_run_handoff",
    "diagnostics_root", "report_path", "patch_path", "patch_kind_expected",
    "final_chat_deliverable", "accepted_prior_evidence",
    "unresolved_checks_only", "checks_not_to_repeat", "evidence_requirements",
    "classification_rules", "anti_self_certification_rules",
    "evidence_validation_method", "governance_binding_expectations",
    "execution_owner", "overwrite_or_resume_policy",
    "interruption_retry_policy", "codex_post_run_interpretation",
    "stop_conditions", "acceptance_logic",
)
FIXED_LIVE_FIELDS = {
    "workspace_root", "repo_locations", "current_checked_out_branch",
    "current_repository_heads", "diagnostics_root", "report_path", "patch_path",
    "patch_kind_expected", "source_control_policy", "evidence_requirements",
    "evidence_validation_method", "governance_binding_expectations",
}
REQUIRED_AUTHOR_FIELDS = {
    "prompt_id", "short_title", "prompt_mode", "preferred_codex_model",
    "reasoning_level", "delegation_policy", "model_selection_rationale",
    "allowed_to_modify", "read_only", "branch_policy",
    "current_baseline_branch", "comparison_baseline",
    "integrated_baseline_mode", "dirty_worktree_policy", "preflight_profile",
    "preflight_scope_paths", "validation_ceiling",
    "heavy_command_permissions", "do_not_commit", "commit_expected",
    "goal", "decision_question", "out_of_scope",
}


@dataclass(frozen=True)
class Diagnostic:
    id: str
    severity: str
    message: str
    section: str
    line: int


@dataclass(frozen=True)
class Section:
    source_heading: str
    canonical_heading: str
    ownership: str
    start_line: int
    end_line: int
    raw: str
    alias_applied: bool


@dataclass(frozen=True)
class MappingOccurrence:
    semantic_path: tuple[str, ...]
    value: str
    line: int
    raw_line: str


class PreflightFailure(Exception):
    def __init__(self, exit_code: int, diagnostic: Diagnostic) -> None:
        super().__init__(diagnostic.message)
        self.exit_code = exit_code
        self.diagnostic = diagnostic


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PreflightFailure(3, Diagnostic(
            "PROMPT-PREFLIGHT-E011", "error", f"Cannot load fixed registry: {exc}",
            str(path), 0,
        )) from exc
    if not isinstance(value, dict):
        raise PreflightFailure(3, Diagnostic(
            "PROMPT-PREFLIGHT-E011", "error", "Fixed registry is not an object.",
            str(path), 0,
        ))
    return value


def normalized_heading(heading: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[`*_]", "", heading)).strip().casefold()


def build_registry(registry: dict[str, Any]) -> dict[str, tuple[str, str]]:
    lookup: dict[str, tuple[str, str]] = {}
    for ownership in ("author_owned", "skill_owned", "shared_structured"):
        for heading in registry[ownership]:
            key = normalized_heading(heading)
            if key in lookup:
                raise PreflightFailure(2, Diagnostic(
                    "PROMPT-PREFLIGHT-E003", "error",
                    "Duplicate heading in the installed closed registry.", heading, 0,
                ))
            lookup[key] = (heading, ownership)
    for alias, canonical in registry["aliases"].items():
        key = normalized_heading(alias)
        target = lookup.get(normalized_heading(canonical))
        if key in lookup or target is None:
            raise PreflightFailure(2, Diagnostic(
                "PROMPT-PREFLIGHT-E003", "error",
                "Ambiguous alias in the installed closed registry.", alias, 0,
            ))
        lookup[key] = target
    return lookup


def _without_ending(line: str) -> str:
    return line[:-2] if line.endswith("\r\n") else line[:-1] if line.endswith("\n") else line


def _top_level_fences(raw: str) -> list[tuple[str, str, int]]:
    body = raw.splitlines()[1:]
    found: list[tuple[str, str, int]] = []
    active: tuple[str, int, str, int] | None = None
    for offset, line in enumerate(body, 2):
        if active:
            character, length, language, opening_line = active
            close = re.match(r"^ {0,3}([`~]+)[ \t]*$", line)
            if close and close.group(1)[0] == character and len(close.group(1)) == length:
                found.append((language, character * length, opening_line))
                active = None
            continue
        opening = re.match(r"^([`~]{3,})([^`~]*)$", line)
        if opening and len(set(opening.group(1))) == 1:
            active = (
                opening.group(1)[0], len(opening.group(1)),
                opening.group(2).strip().casefold(), offset,
            )
    if active:
        raise PreflightFailure(2, Diagnostic(
            "PROMPT-PREFLIGHT-E002", "error", "Unclosed Markdown fence.",
            "<fence>", active[3],
        ))
    return found


def parse_sections(text: str, registry: dict[str, Any]) -> tuple[list[Section], list[Diagnostic], str]:
    lines = text.splitlines(keepends=True)
    diagnostics: list[Diagnostic] = []
    first = next((index for index, line in enumerate(lines) if line.strip()), None)
    if first is None or not re.match(r"^# Prompt(?:\s|$)", _without_ending(lines[first])):
        diagnostics.append(Diagnostic(
            "PROMPT-PREFLIGHT-E001", "error",
            "The first nonblank line must begin with # Prompt.", "<prompt>", 0,
        ))
    lookup = build_registry(registry)
    starts: list[tuple[int, str]] = []
    active: tuple[str, int, int] | None = None
    for index, line in enumerate(lines):
        bare = _without_ending(line)
        if active:
            close = re.match(r"^ {0,3}([`~]+)[ \t]*$", bare)
            if close and close.group(1)[0] == active[0] and len(close.group(1)) == active[1]:
                active = None
            continue
        opening = re.match(r"^ {0,3}([`~]{3,})(?:[^`~].*)?$", bare)
        if opening and len(set(opening.group(1))) == 1:
            active = (opening.group(1)[0], len(opening.group(1)), index + 1)
            continue
        heading = re.match(r"^ {0,3}##(?!#)[ \t]+(.+?)[ \t]*$", bare)
        if heading:
            starts.append((index, heading.group(1)))
    if active:
        diagnostics.append(Diagnostic(
            "PROMPT-PREFLIGHT-E002", "error", "Unclosed Markdown fence.",
            "<fence>", active[2],
        ))
    if not starts:
        diagnostics.append(Diagnostic(
            "PROMPT-PREFLIGHT-E005", "error",
            "No level-2 task section was found.", "<prompt>", 0,
        ))
    sections: list[Section] = []
    seen: set[str] = set()
    for position, (start, heading) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        raw = "".join(lines[start:end])
        registered = lookup.get(normalized_heading(heading))
        if registered:
            canonical, ownership = registered
            alias = normalized_heading(canonical) != normalized_heading(heading)
            duplicate_key = normalized_heading(canonical)
            if ownership in {"author_owned", "shared_structured"} and duplicate_key in seen:
                diagnostics.append(Diagnostic(
                    "PROMPT-PREFLIGHT-E003", "error",
                    f"Duplicate registered section {canonical!r}.", heading, start + 1,
                ))
            seen.add(duplicate_key)
        else:
            canonical, ownership, alias = heading, "author_owned", False
            try:
                fences = _top_level_fences(raw)
            except PreflightFailure as exc:
                diagnostics.append(exc.diagnostic)
                fences = []
            if any(language == "text" for language, _fence, _line in fences):
                diagnostics.append(Diagnostic(
                    "PROMPT-PREFLIGHT-E004", "error",
                    "Unknown heading contains a top-level fenced text mapping.",
                    heading, start + 1,
                ))
            else:
                diagnostics.append(Diagnostic(
                    "PROMPT-PREFLIGHT-W003", "warning",
                    "Unknown ordinary Markdown is preserved as author-owned prose.",
                    heading, start + 1,
                ))
        sections.append(Section(
            heading, canonical, ownership, start + 1, end, raw, alias,
        ))
    preamble_end = starts[0][0] if starts else len(lines)
    return sections, diagnostics, "".join(lines[:preamble_end])


def section_body(section: Section) -> str:
    return "".join(section.raw.splitlines(keepends=True)[1:])


def validate_shared_grammar(section: Section, diagnostics: list[Diagnostic]) -> None:
    try:
        fences = _top_level_fences(section.raw)
    except PreflightFailure as exc:
        diagnostics.append(exc.diagnostic)
        return
    if len(fences) != 1 or fences[0][0] != "text":
        diagnostics.append(Diagnostic(
            "PROMPT-PREFLIGHT-E021", "error",
            "A registered shared section requires exactly one top-level text fence.",
            section.source_heading, section.start_line,
        ))
        return
    inside = False
    character = ""
    length = 0
    for offset, line in enumerate(section_body(section).splitlines(), 1):
        if inside:
            close = re.match(r"^ {0,3}([`~]+)[ \t]*$", line)
            if close and close.group(1)[0] == character and len(close.group(1)) == length:
                inside = False
            continue
        opening = re.match(r"^([`~]{3,})text[ \t]*$", line, re.IGNORECASE)
        if opening and len(set(opening.group(1))) == 1:
            inside = True
            character, length = opening.group(1)[0], len(opening.group(1))
            continue
        stripped = line.strip()
        if stripped and not re.fullmatch(r"<!--\s*[A-Za-z0-9 .,_:-]{0,160}\s*-->", stripped):
            diagnostics.append(Diagnostic(
                "PROMPT-PREFLIGHT-E021", "error",
                "Material outside the shared mapping fence is forbidden.",
                section.source_heading, section.start_line + offset,
            ))


def mapping_lines(section: Section) -> list[tuple[int, str]]:
    collected: list[tuple[int, str]] = []
    inside = False
    character = ""
    length = 0
    for offset, line in enumerate(section_body(section).splitlines(), 1):
        if inside:
            close = re.match(r"^ {0,3}([`~]+)[ \t]*$", line)
            if close and close.group(1)[0] == character and len(close.group(1)) == length:
                break
            collected.append((section.start_line + offset, line))
            continue
        opening = re.match(r"^([`~]{3,})text[ \t]*$", line, re.IGNORECASE)
        if opening and len(set(opening.group(1))) == 1:
            inside = True
            character, length = opening.group(1)[0], len(opening.group(1))
    return collected


def parse_mapping_occurrences(section: Section, diagnostics: list[Diagnostic]) -> list[MappingOccurrence]:
    lines = mapping_lines(section)
    occurrences: list[MappingOccurrence] = []
    stack: dict[int, str] = {}
    seen: dict[tuple[str, ...], int] = {}
    for line_number, line in lines:
        if not line.strip() or line.lstrip().startswith(("#", "- ")):
            continue
        leading = line[:len(line) - len(line.lstrip(" \t"))]
        if "\t" in leading:
            diagnostics.append(Diagnostic(
                "PROMPT-PREFLIGHT-E017", "error",
                "Tabs are forbidden in structured indentation.",
                section.source_heading, line_number,
            ))
            continue
        match = re.match(r"^( *)([A-Za-z_][A-Za-z0-9_]*):[ \t]*(.*)$", line)
        if not match:
            continue
        indent = len(match.group(1))
        if indent % 2 or (indent and indent - 2 not in stack):
            diagnostics.append(Diagnostic(
                "PROMPT-PREFLIGHT-E017", "error",
                "Malformed mapping indentation.", section.source_heading, line_number,
            ))
            continue
        for level in list(stack):
            if level >= indent:
                del stack[level]
        path = tuple(stack[level] for level in sorted(stack)) + (match.group(2),)
        value = match.group(3).strip().strip("\"'")
        if path in seen:
            diagnostics.append(Diagnostic(
                "PROMPT-PREFLIGHT-E016", "error",
                f"Duplicate semantic path {'.'.join(path)!r}.",
                section.source_heading, line_number,
            ))
        else:
            seen[path] = line_number
        occurrences.append(MappingOccurrence(path, value, line_number, line))
        stack[indent] = match.group(2)
    return occurrences


def top_level_fields(section: Section) -> dict[str, str]:
    lines = [line for _number, line in mapping_lines(section)]
    starts = [
        (index, match.group(1))
        for index, line in enumerate(lines)
        if (match := re.match(r"^([A-Za-z_][A-Za-z0-9_]*):", line))
    ]
    fields: dict[str, str] = {}
    for position, (start, key) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        fields.setdefault(key, "\n".join(lines[start:end]).rstrip())
    return fields


def scalar(block: str | None) -> str:
    if not block or ":" not in block.splitlines()[0]:
        return ""
    first, *rest = block.splitlines()
    value = first.split(":", 1)[1].strip()
    if value in {"", ">", "|"}:
        return "\n".join(item.strip() for item in rest if item.strip())
    return value.strip("\"'")


def child_scalars(block: str | None) -> dict[str, str]:
    if not block:
        return {}
    values: dict[str, str] = {}
    for line in block.splitlines()[1:]:
        match = re.match(r"^  ([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if match:
            values[match.group(1)] = match.group(2).strip().strip("\"'")
    return values


def merge_fields(
    sections: list[Section], registry: dict[str, Any], diagnostics: list[Diagnostic],
) -> dict[str, str]:
    fields: dict[str, str] = {}
    allowed_by_section = registry["shared_semantic_paths"]
    all_allowed = {item for values in allowed_by_section.values() for item in values}
    for section in sections:
        if section.ownership not in {"shared_structured", "skill_owned"}:
            continue
        if section.ownership == "shared_structured":
            validate_shared_grammar(section, diagnostics)
            allowed = set(allowed_by_section[section.canonical_heading])
        elif section.canonical_heading == "Metadata and governance":
            allowed = all_allowed
        else:
            continue
        occurrences = parse_mapping_occurrences(section, diagnostics)
        for occurrence in occurrences:
            if (
                section.ownership == "shared_structured"
                and len(occurrence.semantic_path) == 1
                and occurrence.semantic_path[0] not in allowed
            ):
                diagnostics.append(Diagnostic(
                    "PROMPT-PREFLIGHT-E004", "error",
                    f"Unknown shared semantic path {occurrence.semantic_path[0]!r}.",
                    section.source_heading, occurrence.line,
                ))
        for key, block in top_level_fields(section).items():
            if key in allowed and key not in fields:
                fields[key] = block
    return fields


def fixed_git_read(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=False, shell=False, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15,
    )
    if completed.returncode:
        raise PreflightFailure(3, Diagnostic(
            "PROMPT-PREFLIGHT-E006", "error",
            f"Fixed repository observation failed: {' '.join(arguments)}.",
            str(repository), 0,
        ))
    return completed.stdout.strip()


def live_repository_state(workspace_root: Path) -> dict[str, dict[str, str]]:
    repositories = {
        "meta_repo": workspace_root,
        "topeft": workspace_root / "topeft",
        "topcoffea": workspace_root / "topcoffea",
    }
    return {
        name: {
            "path": str(path),
            "branch": fixed_git_read(path, "branch", "--show-current"),
            "head": fixed_git_read(path, "rev-parse", "HEAD"),
            "subject": fixed_git_read(path, "show", "-s", "--format=%s", "HEAD"),
        }
        for name, path in repositories.items()
    }


def _baseline_values(block: str | None) -> dict[str, dict[str, str]]:
    if not block:
        return {}
    result: dict[str, dict[str, str]] = {}
    current = ""
    for line in block.splitlines()[1:]:
        repo = re.match(r"^  ([A-Za-z_][A-Za-z0-9_]*):\s*$", line)
        if repo:
            current = repo.group(1)
            result[current] = {}
            continue
        value = re.match(r"^    (expected_head|expected_subject):\s*(.*)$", line)
        if value and current:
            result[current][value.group(1)] = value.group(2).strip().strip("\"'")
    return result


def validate_authority(
    fields: dict[str, str], live: dict[str, dict[str, str]], workspace_root: Path,
    diagnostics: list[Diagnostic],
) -> None:
    for key in REQUIRED_AUTHOR_FIELDS:
        if key not in fields or not scalar(fields[key]):
            diagnostics.append(Diagnostic(
                "PROMPT-PREFLIGHT-E005", "error",
                f"Missing required shared value {key!r}.", "<shared>", 0,
            ))
    policies = child_scalars(fields.get("branch_policy"))
    current_baselines = child_scalars(fields.get("current_baseline_branch"))
    references = child_scalars(fields.get("reference_branch"))
    targets = child_scalars(fields.get("target_branch"))
    features = child_scalars(fields.get("feature_branch"))
    baselines = _baseline_values(fields.get("comparison_baseline"))
    for name, observation in live.items():
        policy = policies.get(name)
        expected_tuple = {
            "continue_existing_branch": (
                observation["branch"], "none", observation["branch"],
            ),
            "read_only_current_branch": ("none", "none", observation["branch"]),
        }.get(policy or "")
        actual_tuple = (
            targets.get(name, ""), features.get(name, ""),
            current_baselines.get(name, ""),
        )
        if expected_tuple is None or actual_tuple != expected_tuple or references.get(name) != "none":
            diagnostics.append(Diagnostic(
                "PROMPT-PREFLIGHT-E006", "error",
                f"Branch tuple for {name} contradicts live policy.",
                "Baseline and branch policy", 0,
            ))
        expected = baselines.get(name, {})
        if expected.get("expected_head") != observation["head"]:
            diagnostics.append(Diagnostic(
                "PROMPT-PREFLIGHT-E006", "error",
                f"Baseline HEAD for {name} is stale or missing.",
                "Baseline and branch policy", 0,
            ))
        if expected.get("expected_subject") and expected["expected_subject"] != observation["subject"]:
            diagnostics.append(Diagnostic(
                "PROMPT-PREFLIGHT-E006", "error",
                f"Baseline subject for {name} is stale.",
                "Baseline and branch policy", 0,
            ))
    requested = fields.get("allowed_to_modify", "")
    if live["topcoffea"]["path"] in requested or "/groups/" in requested:
        diagnostics.append(Diagnostic(
            "PROMPT-PREFLIGHT-E011", "error",
            "Structured modification scope exceeds the live governance ceiling.",
            "Repository scope", 0,
        ))
    commit_expected = scalar(fields.get("commit_expected"))
    do_not_commit = scalar(fields.get("do_not_commit"))
    if commit_expected not in {"yes", "no"} or do_not_commit not in {"yes", "no"} or commit_expected == do_not_commit:
        diagnostics.append(Diagnostic(
            "PROMPT-PREFLIGHT-E009", "error",
            "Commit policy is contradictory.", "Commit policy", 0,
        ))


def transport_diagnostics(text: str) -> list[Diagnostic]:
    normalized = re.sub(r"[^a-z0-9]+", " ", text.casefold())
    hidden = r"(?:hidden )?(?:chat transport|user interface|composer|message transport|unobservable original) bytes?"
    requirement = r"(?:require|required|must|verify|claim|identity|identical|exact)"
    if re.search(rf"{requirement}.{{0,120}}{hidden}|{hidden}.{{0,120}}{requirement}", normalized):
        return [Diagnostic(
            "PROMPT-PREFLIGHT-E015", "error",
            "Inaccessible transport-byte identity is required or claimed.",
            "<prompt>", 0,
        )]
    return []


def binding_diagnostics(workspace_root: Path, skill_root: Path) -> list[Diagnostic]:
    binding = load_json(skill_root / "references/governance_binding.json")
    agents_hash = sha256_bytes((workspace_root / "AGENTS.md").read_bytes())
    cpc_hash = sha256_bytes((workspace_root / "CPC.md").read_bytes())
    if binding.get("agents_sha256") != agents_hash or binding.get("cpc_sha256") != cpc_hash:
        return [Diagnostic(
            "PROMPT-PREFLIGHT-E011", "error",
            "Installed governance binding is stale.",
            "Governance-binding evidence", 0,
        )]
    return []


def _field_block(name: str, value: str) -> str:
    return value if value.startswith(name + ":") else f"{name}: {value}"


def _mapping_block(name: str, values: dict[str, str]) -> str:
    return name + ":\n" + "\n".join(f"  {key}: {value}" for key, value in values.items())


def complete_fields(
    fields: dict[str, str], prompt_id: str, workspace_root: Path,
    live: dict[str, dict[str, str]], contexts: dict[str, str],
) -> dict[str, str]:
    completed = dict(fields)
    completed["workspace_root"] = f"workspace_root: {workspace_root}"
    completed["repo_locations"] = _mapping_block(
        "repo_locations", {name: item["path"] for name, item in live.items()},
    )
    completed["current_checked_out_branch"] = _mapping_block(
        "current_checked_out_branch", {name: item["branch"] for name, item in live.items()},
    )
    completed["current_repository_heads"] = _mapping_block(
        "current_repository_heads", {name: item["head"] for name, item in live.items()},
    )
    for key, value in contexts.items():
        completed[key] = f"{key}: {value}"
    diagnostics_root = workspace_root / "reports" / "diagnostics" / f"{prompt_id}_preflight"
    completed["diagnostics_root"] = f"diagnostics_root: {diagnostics_root}"
    completed["report_path"] = f"report_path: {diagnostics_root / (prompt_id + '_report.md')}"
    completed["patch_path"] = f"patch_path: {diagnostics_root / (prompt_id + '_worktree_diff.patch')}"
    completed["patch_kind_expected"] = "patch_kind_expected: prompt_local"
    completed["source_control_policy"] = (
        "source_control_policy:\n"
        "  - follow live AGENTS.md\n"
        "  - stage exact authorized paths only\n"
        "  - infer no remote authority"
    )
    completed["evidence_requirements"] = (
        "evidence_requirements:\n  ordered_method:\n"
        + "\n".join(f"    - {phase}" for phase in EVIDENCE_SEQUENCE)
    )
    completed["evidence_validation_method"] = (
        f"evidence_validation_method: {EVIDENCE_COMPACT}"
    )
    completed["classification_rules"] = (
        "classification_rules:\n"
        "  - classify only after serialized evidence is reopened\n"
        "  - author prose has zero repository-authority effect"
    )
    completed["anti_self_certification_rules"] = (
        "anti_self_certification_rules:\n"
        "  - derive observations independently of expected values\n"
        "  - reopen generated evidence before verdict"
    )
    completed["governance_binding_expectations"] = (
        "governance_binding_expectations:\n"
        f"  agents_sha256: {sha256_bytes((workspace_root / 'AGENTS.md').read_bytes())}\n"
        f"  cpc_sha256: {sha256_bytes((workspace_root / 'CPC.md').read_bytes())}"
    )
    return completed


def metadata_text(fields: dict[str, str]) -> str:
    ordered = [_field_block(name, fields[name]) for name in FIELD_ORDER if name in fields]
    ordered.extend(
        _field_block(name, value)
        for name, value in fields.items()
        if name not in FIELD_ORDER and name not in FIXED_LIVE_FIELDS
    )
    return "\n\n".join(ordered)


def canonicalize(
    fields: dict[str, str], sections: list[Section], preamble: str,
    workspace_root: Path, live: dict[str, dict[str, str]],
) -> bytes:
    metadata = metadata_text(fields)
    prompt_id = scalar(fields.get("prompt_id"))
    agents_hash = sha256_bytes((workspace_root / "AGENTS.md").read_bytes())
    cpc_hash = sha256_bytes((workspace_root / "CPC.md").read_bytes())
    generated = (
        "## Prompt preflight result\n\n"
        "This canonical prompt is authorized only for the immediate next phase "
        "after this invocation returns exit 0. Audit artifacts are observational.\n\n"
        "## Repository envelope\n\n"
        + "\n".join(
            f"- `{name}`: `{item['branch']}` at `{item['head']}`"
            for name, item in live.items()
        )
        + "\n\n## Standard execution boundaries\n\n"
        "The renderer performs no task action, prompt-authored execution, callback, "
        "nested session, publication, or environment handoff.\n\n"
        "## Evidence-order contract\n\n"
        + "\n".join(f"{index}. `{phase}`" for index, phase in enumerate(EVIDENCE_SEQUENCE, 1))
        + f"\n\n`{EVIDENCE_COMPACT}`\n\n"
        "## Source-control policy\n\nFollow live `AGENTS.md` and the validated structured intent.\n\n"
        "## Diagnostics and publication paths\n\n"
        f"Diagnostics for `{prompt_id}` remain observational under `{workspace_root / 'reports' / 'diagnostics'}`.\n\n"
        "## Standard report sections\n\n"
        "Report the decision, evidence, validation, files, patch, commit, caveats, next action, and cleanliness.\n\n"
        "## Standard final-response fields\n\n"
        "Return status, decision, repository observations, validation, files, commit, artifacts, caveats, and cleanliness.\n\n"
        "## Governance-binding evidence\n\n"
        f"- `AGENTS.md`: `{agents_hash}`\n- `CPC.md`: `{cpc_hash}`\n\n"
    )
    author_sections = "".join(
        section.raw for section in sections if section.ownership == "author_owned"
    )
    canonical = (
        preamble + "## Metadata and governance\n\n```text\n"
        + metadata + "\n```\n\n" + generated + author_sections
    )
    if not canonical.endswith("\n"):
        canonical += "\n"
    return canonical.encode("utf-8")


def invoke_prompt_contract(
    workspace_root: Path, canonical_path: Path, contexts: dict[str, str],
    pass_fds: tuple[int, ...],
) -> dict[str, Any]:
    validator = workspace_root / ".agents/skills/correction-lib-prompt-contract/scripts/validate_prompt.py"
    argv = [
        sys.executable, str(validator), "--workspace-root", str(workspace_root),
        "--continuation", contexts["continuation"],
        "--evidence-round", contexts["evidence_round"],
        "--user-run-handoff", contexts["user_run_handoff"],
        "--format", "json", str(canonical_path),
    ]
    validator_environment = os.environ.copy()
    validator_environment.pop("PYTHONPATH", None)
    validator_environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        argv, check=False, shell=False, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        timeout=60, pass_fds=pass_fds, env=validator_environment,
    )
    try:
        result = json.loads(completed.stdout)
    except (json.JSONDecodeError, TypeError) as exc:
        raise PreflightFailure(4, Diagnostic(
            "PROMPT-PREFLIGHT-E010", "error",
            "Installed prompt-contract validator returned malformed output.",
            "prompt-contract", 0,
        )) from exc
    canonical_hash = sha256_bytes(canonical_path.read_bytes())
    if (
        completed.returncode
        or not isinstance(result, dict)
        or result.get("error_count") != 0
        or result.get("input", {}).get("sha256") != canonical_hash
    ):
        raise PreflightFailure(4, Diagnostic(
            "PROMPT-PREFLIGHT-E010", "error",
            "Installed prompt-contract validator rejected canonical bytes.",
            "prompt-contract", 0,
        ))
    return result


def _relative_parts(path: Path) -> tuple[str, ...]:
    if path.is_absolute():
        raise PreflightFailure(2, Diagnostic(
            "PROMPT-PREFLIGHT-E018", "error",
            "Diagnostics paths must be relative.", str(path), 0,
        ))
    parts = tuple(path.parts)
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise PreflightFailure(2, Diagnostic(
            "PROMPT-PREFLIGHT-E018", "error",
            "Diagnostics paths may not contain empty, dot, or parent components.",
            str(path), 0,
        ))
    return parts


def _read_fd(fd: int) -> bytes:
    os.lseek(fd, 0, os.SEEK_SET)
    chunks: list[bytes] = []
    while True:
        chunk = os.read(fd, 1024 * 1024)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


class DiagnosticsRoot:
    def __init__(self, workspace_root: Path) -> None:
        self.path = workspace_root / "reports" / "diagnostics"
        self.fd = os.open(
            self.path,
            os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0),
        )

    def __enter__(self) -> "DiagnosticsRoot":
        return self

    def __exit__(self, *_args: object) -> None:
        os.close(self.fd)

    def open_directory(self, parts: Iterable[str]) -> int:
        current = os.dup(self.fd)
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0)
        try:
            for part in parts:
                next_fd = os.open(part, flags, dir_fd=current)
                os.close(current)
                current = next_fd
            return current
        except OSError:
            os.close(current)
            raise

    def read_source(self, relative: Path) -> bytes:
        parts = _relative_parts(relative)
        parent_fd = self.open_directory(parts[:-1])
        try:
            fd = os.open(
                parts[-1],
                os.O_RDONLY | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=parent_fd,
            )
        finally:
            os.close(parent_fd)
        try:
            before = os.fstat(fd)
            if not stat.S_ISREG(before.st_mode):
                raise OSError(errno.EINVAL, "source is not a regular file")
            content = _read_fd(fd)
            after = os.fstat(fd)
            if (
                (before.st_dev, before.st_ino, before.st_size)
                != (after.st_dev, after.st_ino, after.st_size)
                or len(content) != before.st_size
            ):
                raise OSError(errno.EIO, "source identity changed during read")
            return content
        finally:
            os.close(fd)

    def create_stage(self, relative: Path) -> "AuditStage":
        parts = _relative_parts(relative)
        parent_fd = self.open_directory(parts[:-1])
        final_name = parts[-1]
        try:
            os.stat(final_name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            os.close(parent_fd)
            raise FileExistsError(final_name)
        staging_name = f".{final_name}.preflight-{secrets.token_hex(8)}"
        os.mkdir(staging_name, 0o700, dir_fd=parent_fd)
        stage_fd = os.open(
            staging_name,
            os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=parent_fd,
        )
        return AuditStage(parent_fd, stage_fd, staging_name, final_name)


def _load_libc() -> Any:
    if sys.platform != "linux":
        raise OSError(errno.ENOSYS, "RENAME_NOREPLACE requires Linux")
    return ctypes.CDLL(None, use_errno=True)


def linux_rename_noreplace(
    source_dir_fd: int, source_name: str, destination_dir_fd: int,
    destination_name: str, library: Any | None = None,
) -> None:
    libc = library if library is not None else _load_libc()
    try:
        function = libc.renameat2
    except AttributeError as exc:
        raise OSError(errno.ENOSYS, "renameat2 symbol is unavailable") from exc
    function.argtypes = [
        ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p,
        ctypes.c_uint,
    ]
    function.restype = ctypes.c_int
    ctypes.set_errno(0)
    result = function(
        source_dir_fd, os.fsencode(source_name),
        destination_dir_fd, os.fsencode(destination_name),
        RENAME_NOREPLACE,
    )
    if result != 0:
        error_number = ctypes.get_errno() or errno.EIO
        raise OSError(error_number, os.strerror(error_number))


class AuditStage:
    def __init__(
        self, parent_fd: int, fd: int, staging_name: str, final_name: str,
    ) -> None:
        self.parent_fd = parent_fd
        self.fd = fd
        self.staging_name = staging_name
        self.final_name = final_name

    def close(self) -> None:
        for name in ("fd", "parent_fd"):
            descriptor = getattr(self, name)
            if descriptor >= 0:
                os.close(descriptor)
                setattr(self, name, -1)

    def write(self, name: str, content: bytes) -> None:
        if name not in OUTPUT_NAMES:
            raise OSError(errno.EINVAL, "unregistered audit artifact")
        fd = os.open(
            name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0),
            0o600, dir_fd=self.fd,
        )
        try:
            view = memoryview(content)
            while view:
                view = view[os.write(fd, view):]
            os.fsync(fd)
        finally:
            os.close(fd)

    def read(self, name: str) -> bytes:
        fd = os.open(
            name,
            os.O_RDONLY | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=self.fd,
        )
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise OSError(errno.EINVAL, "audit artifact is not regular")
            return _read_fd(fd)
        finally:
            os.close(fd)

    def proc_path(self, name: str) -> Path:
        return Path(f"/proc/self/fd/{self.fd}/{name}")

    def publish(self) -> None:
        os.fsync(self.fd)
        linux_rename_noreplace(
            self.parent_fd, self.staging_name, self.parent_fd, self.final_name,
        )
        os.fsync(self.parent_fd)


def _audit_result(
    prompt_id: str, source: bytes, canonical: bytes,
    contexts: dict[str, str], live: dict[str, dict[str, str]],
    diagnostics: list[Diagnostic], validation: dict[str, Any],
    workspace_root: Path,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "skill_version": SKILL_VERSION,
        "renderer_version": RENDERER_VERSION,
        "ownership_contract_version": OWNERSHIP_CONTRACT_VERSION,
        "black_box_suite_version": BLACK_BOX_SUITE_VERSION,
        "trust_model_id": TRUST_MODEL_ID,
        "authority_model_id": AUTHORITY_MODEL_ID,
        "shared_registry_id": SHARED_REGISTRY_ID,
        "runtime_interface_id": RUNTIME_INTERFACE_ID,
        "readiness_theorem_id": READINESS_THEOREM_ID,
        "filesystem_contract_id": FILESYSTEM_CONTRACT_ID,
        "prompt_id": prompt_id,
        "ready_for_immediate_next_phase": True,
        "authorization_scope": "immediate_next_phase_same_uninterrupted_turn_only",
        "audit_artifacts_authorize": False,
        "source_sha256": sha256_bytes(source),
        "canonical_sha256": sha256_bytes(canonical),
        "agents_sha256": sha256_bytes((workspace_root / "AGENTS.md").read_bytes()),
        "cpc_sha256": sha256_bytes((workspace_root / "CPC.md").read_bytes()),
        "contexts": contexts,
        "live_observations": live,
        "prompt_contract": {
            "invoked": True,
            "error_count": validation["error_count"],
            "warning_count": validation["warning_count"],
            "input_sha256": validation["input"]["sha256"],
        },
        "diagnostics": [asdict(item) for item in diagnostics],
        "artifact_names": list(OUTPUT_NAMES),
        "task_execution_performed": False,
        "nested_codex_launched": False,
    }


def _report(result: dict[str, Any]) -> bytes:
    return (
        "# Prompt preflight report\n\n"
        "## Preflight result\n\n"
        "- status: `passed`\n"
        "- authorization: `immediate next phase of this uninterrupted turn only`\n"
        "- audit artifacts authorize: `false`\n\n"
        "## Source and canonical identity\n\n"
        f"- source_sha256: `{result['source_sha256']}`\n"
        f"- canonical_sha256: `{result['canonical_sha256']}`\n\n"
        "## Prompt-contract validation\n\n"
        f"- errors: `{result['prompt_contract']['error_count']}`\n"
        f"- warnings: `{result['prompt_contract']['warning_count']}`\n\n"
        "## Observational-only statement\n\n"
        "This report and every audit artifact are observational and do not authorize task action.\n"
    ).encode("utf-8")


def validate_audit(
    reopened: dict[str, bytes], source: bytes, canonical: bytes,
) -> None:
    if set(reopened) != set(OUTPUT_NAMES):
        raise OSError(errno.EINVAL, "audit inventory mismatch")
    if reopened["authored_prompt.md"] != source:
        raise OSError(errno.EINVAL, "authored source identity mismatch")
    if reopened["canonical_prompt.md"] != canonical:
        raise OSError(errno.EINVAL, "canonical identity mismatch")
    try:
        result = json.loads(reopened["preflight_result.json"])
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise OSError(errno.EINVAL, "invalid result JSON") from exc
    required = {
        "schema_version", "skill_version", "renderer_version",
        "ownership_contract_version", "black_box_suite_version",
        "trust_model_id", "authority_model_id", "shared_registry_id",
        "runtime_interface_id", "readiness_theorem_id",
        "filesystem_contract_id", "prompt_id",
        "ready_for_immediate_next_phase", "authorization_scope",
        "audit_artifacts_authorize", "source_sha256", "canonical_sha256",
        "agents_sha256", "cpc_sha256", "contexts", "live_observations",
        "prompt_contract", "diagnostics", "artifact_names",
        "task_execution_performed", "nested_codex_launched",
    }
    if set(result) != required:
        raise OSError(errno.EINVAL, "result schema is not closed")
    if (
        result["audit_artifacts_authorize"] is not False
        or result["ready_for_immediate_next_phase"] is not True
        or result["artifact_names"] != list(OUTPUT_NAMES)
        or result["source_sha256"] != sha256_bytes(source)
        or result["canonical_sha256"] != sha256_bytes(canonical)
        or result["prompt_contract"]["error_count"] != 0
    ):
        raise OSError(errno.EINVAL, "result cross-validation failed")
    report = reopened["preflight_report.md"].decode("utf-8")
    if "observational and do not authorize" not in report:
        raise OSError(errno.EINVAL, "report authorization disclaimer is absent")


def run_preflight(
    source_path: Path, audit_root: Path, workspace_root: Path,
    contexts: dict[str, str],
) -> tuple[dict[str, Any], int, bytes]:
    skill_root = Path(__file__).resolve().parents[1]
    try:
        with DiagnosticsRoot(workspace_root) as diagnostics_root:
            try:
                source = diagnostics_root.read_source(source_path)
            except (OSError, PreflightFailure) as exc:
                diagnostic = exc.diagnostic if isinstance(exc, PreflightFailure) else Diagnostic(
                    "PROMPT-PREFLIGHT-E018", "error",
                    f"Diagnostics source capture rejected: {exc}.", str(source_path), 0,
                )
                return {"diagnostics": [asdict(diagnostic)]}, 2, b""
            try:
                text = source.decode("utf-8")
            except UnicodeError as exc:
                diagnostic = Diagnostic(
                    "PROMPT-PREFLIGHT-E002", "error",
                    f"Source is not UTF-8: {exc}.", str(source_path), 0,
                )
                return {"diagnostics": [asdict(diagnostic)]}, 2, b""
            registry = load_json(skill_root / "references/section_ownership.json")
            sections, diagnostics, preamble = parse_sections(text, registry)
            diagnostics.extend(transport_diagnostics(text))
            diagnostics.extend(binding_diagnostics(workspace_root, skill_root))
            fields = merge_fields(sections, registry, diagnostics)
            prompt_id = scalar(fields.get("prompt_id")) or "unresolved_prompt_id"
            try:
                live = live_repository_state(workspace_root)
            except PreflightFailure as exc:
                return {"diagnostics": [asdict(exc.diagnostic)]}, exc.exit_code, b""
            validate_authority(fields, live, workspace_root, diagnostics)
            syntax_ids = {
                "PROMPT-PREFLIGHT-E001", "PROMPT-PREFLIGHT-E002",
                "PROMPT-PREFLIGHT-E003", "PROMPT-PREFLIGHT-E004",
                "PROMPT-PREFLIGHT-E005", "PROMPT-PREFLIGHT-E016",
                "PROMPT-PREFLIGHT-E017", "PROMPT-PREFLIGHT-E021",
            }
            errors = [item for item in diagnostics if item.severity == "error"]
            if errors:
                exit_code = 2 if any(item.id in syntax_ids for item in errors) else 3
                return {"diagnostics": [asdict(item) for item in diagnostics]}, exit_code, b""
            completed = complete_fields(fields, prompt_id, workspace_root, live, contexts)
            canonical = canonicalize(completed, sections, preamble, workspace_root, live)
            try:
                stage = diagnostics_root.create_stage(audit_root)
            except (OSError, PreflightFailure) as exc:
                diagnostic = Diagnostic(
                    "PROMPT-PREFLIGHT-E012", "error",
                    f"Absent audit root could not be staged: {exc}.", str(audit_root), 0,
                )
                return {"diagnostics": [asdict(diagnostic)]}, 5, b""
            try:
                stage.write("authored_prompt.md", source)
                stage.write("canonical_prompt.md", canonical)
                try:
                    validation = invoke_prompt_contract(
                        workspace_root, stage.proc_path("canonical_prompt.md"),
                        contexts, (stage.fd,),
                    )
                except PreflightFailure as exc:
                    return {"diagnostics": [asdict(exc.diagnostic)]}, 4, b""
                result = _audit_result(
                    prompt_id, source, canonical, contexts, live, diagnostics,
                    validation, workspace_root,
                )
                stage.write("preflight_result.json", json_bytes(result))
                stage.write("preflight_report.md", _report(result))
                reopened = {name: stage.read(name) for name in OUTPUT_NAMES}
                validate_audit(reopened, source, canonical)
                stage.publish()
                return result, 0, canonical
            except OSError as exc:
                diagnostic = Diagnostic(
                    "PROMPT-PREFLIGHT-E023", "error",
                    f"Audit write, validation, or no-replace publication failed: {exc}.",
                    str(audit_root), 0,
                )
                return {"diagnostics": [asdict(diagnostic)]}, 5, b""
            finally:
                stage.close()
    except PreflightFailure as exc:
        return {"diagnostics": [asdict(exc.diagnostic)]}, exc.exit_code, b""
    except OSError as exc:
        diagnostic = Diagnostic(
            "PROMPT-PREFLIGHT-E023", "error",
            f"Descriptor-rooted diagnostics I/O failed: {exc}.",
            str(audit_root), 0,
        )
        return {"diagnostics": [asdict(diagnostic)]}, 5, b""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preflight an inert diagnostics-local Markdown source capture.",
    )
    parser.add_argument(
        "--workspace-root", type=Path,
        default=Path(__file__).resolve().parents[4],
    )
    parser.add_argument("--source-path", type=Path, required=True)
    parser.add_argument("--audit-root", type=Path, required=True)
    parser.add_argument("--continuation", choices=CONTEXT_VALUES, required=True)
    parser.add_argument("--evidence-round", choices=CONTEXT_VALUES, required=True)
    parser.add_argument("--user-run-handoff", choices=CONTEXT_VALUES, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    contexts = {
        "continuation": args.continuation,
        "evidence_round": args.evidence_round,
        "user_run_handoff": args.user_run_handoff,
    }
    _result, exit_code, canonical = run_preflight(
        args.source_path, args.audit_root, args.workspace_root.resolve(), contexts,
    )
    if exit_code == 0:
        sys.stdout.buffer.write(canonical)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
