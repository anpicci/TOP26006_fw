#!/usr/bin/env python3
"""Preflight an inert visible correction-lib Markdown prompt.

Prompt text is data.  The only subprocesses are fixed, shell-false, read-only
Git observations and the fixed installed prompt-contract validator.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


SKILL_VERSION = "1.0.1"
RENDERER_VERSION = "1.0.1"
SCHEMA_VERSION = "1.0.1"
OWNERSHIP_CONTRACT_VERSION = "1.0.1"
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
    "section_manifest.json",
    "shared_value_manifest.json",
    "prompt_contract_validation.json",
    "preflight_state.json",
    "preflight_report.md",
)
JSON_OUTPUTS = {
    "section_manifest.json",
    "shared_value_manifest.json",
    "prompt_contract_validation.json",
    "preflight_state.json",
}
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
    "diagnostics_root", "report_path", "patch_path", "patch_kind_expected",
    "final_chat_deliverable", "accepted_prior_evidence",
    "unresolved_checks_only", "checks_not_to_repeat", "evidence_requirements",
    "classification_rules", "anti_self_certification_rules",
    "evidence_validation_method", "governance_binding_expectations",
    "execution_owner", "overwrite_or_resume_policy",
    "interruption_retry_policy", "codex_post_run_interpretation",
)
AUTHOR_SEMANTIC_FIELDS = {
    "prompt_id", "short_title", "prompt_mode", "preferred_codex_model",
    "reasoning_level", "delegation_policy", "model_selection_rationale",
    "allowed_to_modify", "read_only", "branch_policy", "reference_branch",
    "target_branch", "feature_branch", "current_baseline_branch",
    "comparison_baseline", "integrated_baseline_mode", "dirty_worktree_policy",
    "preflight_profile", "preflight_scope_paths", "validation_ceiling",
    "heavy_command_permissions", "do_not_commit", "commit_expected",
    "commit_message_policy", "goal", "decision_question", "out_of_scope",
}
FIXED_SKILL_FIELDS = {
    "workspace_root", "repo_locations", "current_checked_out_branch",
    "current_repository_heads", "evidence_requirements",
    "evidence_validation_method", "diagnostics_root", "report_path",
    "patch_path", "patch_kind_expected", "source_control_policy",
    "final_chat_deliverable", "classification_rules",
    "anti_self_certification_rules", "governance_binding_expectations",
}
REQUIRED_AUTHOR_FIELDS = {
    "prompt_id", "short_title", "prompt_mode", "preferred_codex_model",
    "reasoning_level", "delegation_policy", "model_selection_rationale",
    "allowed_to_modify", "read_only", "branch_policy",
    "current_baseline_branch", "comparison_baseline", "integrated_baseline_mode",
    "dirty_worktree_policy", "preflight_profile", "preflight_scope_paths",
    "validation_ceiling", "heavy_command_permissions", "do_not_commit",
    "commit_expected", "goal", "decision_question", "out_of_scope",
}
SUPPORTED_BRANCH_POLICIES = {
    "continue_existing_branch",
    "read_only_current_branch",
}
UNSUPPORTED_BRANCH_POLICIES = {
    "create_feature_branch_from_reference",
    "commit_preparation_on_existing_branch",
}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
DIAGNOSTIC_IDS = tuple(
    [f"PROMPT-PREFLIGHT-E{index:03d}" for index in range(1, 21)]
    + [f"PROMPT-PREFLIGHT-W{index:03d}" for index in range(1, 5)]
)
# PROMPT-PREFLIGHT-E013 is the stable reopening-failure identity; enforced
# schema reopening reports E019 with E013 retained for catalog compatibility.


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

    @property
    def sha256(self) -> str:
        return sha256_text(self.raw)


@dataclass(frozen=True)
class MappingOccurrence:
    semantic_path: tuple[str, ...]
    key: str
    value: str
    line: int
    indent: int
    raw_line: str


class PreflightInputError(Exception):
    """Invalid CLI input or unreadable resource."""


class PreflightBlocked(Exception):
    """Task action is not permitted for the supplied state."""

    def __init__(self, diagnostic: Diagnostic) -> None:
        super().__init__(diagnostic.message)
        self.diagnostic = diagnostic


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_text(content: str) -> str:
    return sha256_bytes(content.encode("utf-8"))


def json_text(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PreflightInputError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PreflightInputError(f"{path} must contain a JSON object")
    return value


def normalized_heading(heading: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[`*_]", "", heading)).strip().casefold()


def build_registry(registry: dict[str, Any]) -> tuple[dict[str, tuple[str, str]], list[str]]:
    lookup: dict[str, tuple[str, str]] = {}
    errors: list[str] = []
    for ownership in ("author_owned", "skill_owned", "shared_structured"):
        for heading in registry[ownership]:
            key = normalized_heading(heading)
            if key in lookup:
                errors.append(heading)
            lookup[key] = (heading, ownership)
    for alias, canonical in registry["aliases"].items():
        alias_key = normalized_heading(alias)
        canonical_key = normalized_heading(canonical)
        if alias_key in lookup or canonical_key not in lookup:
            errors.append(alias)
        else:
            lookup[alias_key] = lookup[canonical_key]
    return lookup, errors


def _line_without_ending(line: str) -> str:
    if line.endswith("\r\n"):
        return line[:-2]
    if line.endswith("\n"):
        return line[:-1]
    return line


def _permission_normal_form(text: str) -> str:
    text = re.sub(r"[`*_~]", "", text.casefold())
    return re.sub(r"[^a-z0-9_]+", " ", text)


def unknown_is_normative(heading: str, raw: str, registry: dict[str, Any]) -> bool:
    normal = _permission_normal_form(heading + "\n" + raw)
    if re.search(r"\b(?:do\s+not|never|must\s+not|shall\s+not)\b", normal):
        return True
    modal = r"(?:may|can|must|should|shall|permitted|allowed|forbidden|required|optional)"
    action = r"(?:edit|modify|change|write|delete|remove|create|stage|commit|push|publish|merge|switch|reset|restore|clean|install|execute|run|inspect|access|read)s?"
    governed = r"(?:files?|paths?|repositories|repository|repos?|branches|refs?|heads?|baselines?|commits?|networks?|internet|environments?|dependencies|production|schedulers?|workers?|work\s+queues?|logs?|outputs?|pkls?|sidecars?)"
    if re.search(rf"\b{modal}\b", normal):
        return True
    if re.search(rf"\b{action}\b(?:\s+\w+){{0,5}}\s+\b{governed}\b", normal):
        return True
    for line in raw.splitlines():
        bullet = _permission_normal_form(line).strip()
        if re.match(rf"^(?:[-+]\s*)?{action}\b", bullet):
            return True
    governed_keys = {item.casefold() for item in registry.get("governance_mapping_keys", [])}
    for match in re.finditer(r"(?m)^\s*([A-Za-z_][A-Za-z0-9_]*):", raw):
        if match.group(1).casefold() in governed_keys:
            return True
    return False


def parse_sections(text: str, registry: dict[str, Any]) -> tuple[list[Section], list[Diagnostic], str]:
    lines = text.splitlines(keepends=True)
    diagnostics: list[Diagnostic] = []
    first_nonblank = next((i for i, line in enumerate(lines) if line.strip()), None)
    if first_nonblank is None or not re.match(r"^# Prompt(?:\s|$)", _line_without_ending(lines[first_nonblank])):
        diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E001", "error", "The first nonblank line is not a level-1 # Prompt heading.", "<prompt>", 0))
    lookup, registry_errors = build_registry(registry)
    if registry_errors:
        diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E003", "error", "The ownership registry contains duplicate or ambiguous aliases.", ", ".join(registry_errors), 0))
    starts: list[tuple[int, str]] = []
    fence_character = ""
    fence_length = 0
    fence_line = 0
    for index, line in enumerate(lines):
        bare = _line_without_ending(line)
        if fence_character:
            close = re.match(r"^ {0,3}([`~]+)[ \t]*$", bare)
            if close and close.group(1)[0] == fence_character and len(close.group(1)) == fence_length:
                fence_character = ""
                fence_length = 0
            continue
        opening = re.match(r"^ {0,3}([`~]{3,})(?:[^`~].*)?$", bare)
        if opening and len(set(opening.group(1))) == 1:
            fence_character = opening.group(1)[0]
            fence_length = len(opening.group(1))
            fence_line = index + 1
            continue
        heading = re.match(r"^ {0,3}##(?!#)[ \t]+(.+?)[ \t]*$", bare)
        if heading:
            starts.append((index, heading.group(1)))
    if fence_character:
        diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E002", "error", "The Markdown fence is not closed.", "<fence>", fence_line))
    if not starts:
        diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E005", "error", "The prompt has no level-2 structured task section.", "<prompt>", 0))
    sections: list[Section] = []
    seen: dict[str, str] = {}
    for position, (start, heading) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        raw = "".join(lines[start:end])
        key = normalized_heading(heading)
        if key in lookup:
            canonical, ownership = lookup[key]
            alias_applied = normalized_heading(canonical) != key
            duplicate_key = normalized_heading(canonical)
            if ownership in {"author_owned", "shared_structured"} and duplicate_key in seen:
                diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E003", "error", f"The canonical section {canonical!r} appears more than once.", heading, start + 1))
            seen[duplicate_key] = heading
        else:
            canonical, ownership, alias_applied = heading, "author_owned", False
            if unknown_is_normative(heading, raw, registry):
                diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E004", "error", "An unknown section contains normative, capability, or permission semantics and requires classification.", heading, start + 1))
            else:
                diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-W003", "warning", "An unknown descriptive section is preserved as author-owned.", heading, start + 1))
        sections.append(Section(heading, canonical, ownership, start + 1, end, raw, alias_applied))
    preamble_end = starts[0][0] if starts else len(lines)
    return sections, diagnostics, "".join(lines[:preamble_end])


def section_body(section: Section) -> str:
    return "".join(section.raw.splitlines(keepends=True)[1:])


def mapping_lines(section: Section) -> list[tuple[int, str]]:
    body = section_body(section).splitlines()
    inside = False
    fence_character = ""
    fence_length = 0
    found = False
    collected: list[tuple[int, str]] = []
    for offset, line in enumerate(body, 1):
        line_number = section.start_line + offset
        if not inside:
            opening = re.match(r"^ {0,3}([`~]{3,})(?:text|yaml)?[ \t]*$", line, re.IGNORECASE)
            if opening and len(set(opening.group(1))) == 1:
                inside = True
                found = True
                fence_character = opening.group(1)[0]
                fence_length = len(opening.group(1))
            elif not found:
                collected.append((line_number, line))
        else:
            close = re.match(r"^ {0,3}([`~]+)[ \t]*$", line)
            if close and close.group(1)[0] == fence_character and len(close.group(1)) == fence_length:
                inside = False
            else:
                collected.append((line_number, line))
    return collected


def parse_mapping_occurrences(section: Section, diagnostics: list[Diagnostic]) -> list[MappingOccurrence]:
    lines = mapping_lines(section)
    occurrences: list[MappingOccurrence] = []
    stack: dict[int, str] = {}
    seen: dict[tuple[str, ...], int] = {}
    for index, (line_number, line) in enumerate(lines):
        if not line.strip() or line.lstrip().startswith(("#", "- ")):
            continue
        if "\t" in line[: len(line) - len(line.lstrip(" \t"))]:
            diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E017", "error", "Tabs are forbidden in structured mapping indentation.", section.source_heading, line_number))
            continue
        match = re.match(r"^( *)([A-Za-z_][A-Za-z0-9_]*):[ \t]*(.*)$", line)
        if not match:
            continue
        indent = len(match.group(1))
        if indent % 2 or (indent and indent - 2 not in stack):
            diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E017", "error", "Malformed indentation changes the structured semantic path.", section.source_heading, line_number))
            continue
        for level in list(stack):
            if level >= indent:
                del stack[level]
        parents = tuple(stack[level] for level in sorted(stack) if level < indent)
        key = match.group(2)
        value = match.group(3).strip().strip("\"'")
        if not value:
            for _next_number, next_line in lines[index + 1:]:
                if not next_line.strip():
                    continue
                next_indent = len(next_line) - len(next_line.lstrip(" "))
                if next_indent <= indent:
                    break
                if re.match(r"^ *[A-Za-z_][A-Za-z0-9_]*:", next_line):
                    break
                value = next_line.strip().strip("\"'")
                break
        path = parents + (key,)
        if path in seen:
            diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E016", "error", f"Duplicate semantic path {'.'.join(path)!r}; first line {seen[path]}, duplicate line {line_number}.", section.source_heading, line_number))
        else:
            seen[path] = line_number
        occurrences.append(MappingOccurrence(path, key, value, line_number, indent, line))
        stack[indent] = key
    return occurrences


def parse_top_level_fields(mapping: str) -> dict[str, str]:
    lines = mapping.splitlines()
    starts = [(index, match.group(1)) for index, line in enumerate(lines) if (match := re.match(r"^([A-Za-z_][A-Za-z0-9_]*):", line))]
    fields: dict[str, str] = {}
    for position, (start, key) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        if key not in fields:
            fields[key] = "\n".join(lines[start:end]).rstrip()
    return fields


def mapping_payload(section: Section) -> str:
    return "\n".join(line for _number, line in mapping_lines(section))


def scalar(field_block: str | None) -> str:
    if not field_block or ":" not in field_block.splitlines()[0]:
        return ""
    first, *rest = field_block.splitlines()
    value = first.split(":", 1)[1].strip()
    if value in {">", "|", ""}:
        return "\n".join(line.strip() for line in rest if line.strip()).strip()
    return value.strip("\"'")


def child_scalars(field_block: str | None) -> dict[str, str]:
    if not field_block:
        return {}
    values: dict[str, str] = {}
    for line in field_block.splitlines()[1:]:
        match = re.match(r"^  ([A-Za-z_][A-Za-z0-9_]*):[ \t]*(.*)$", line)
        if match:
            values[match.group(1)] = match.group(2).strip().strip("\"'")
    return values


def fixed_git_read(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments], check=False, shell=False,
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, timeout=15,
    )
    if completed.returncode:
        raise PreflightInputError(f"fixed Git read failed for {repository}: {completed.stderr.strip()}")
    return completed.stdout.strip()


def live_repository_state(workspace_root: Path) -> dict[str, dict[str, str]]:
    locations = {"meta_repo": workspace_root, "topeft": workspace_root / "topeft", "topcoffea": workspace_root / "topcoffea"}
    state: dict[str, dict[str, str]] = {}
    for name, path in locations.items():
        if not path.is_dir() or not (path / ".git").exists():
            raise PreflightInputError(f"governed repository is missing or not Git-backed: {name} at {path}")
        state[name] = {
            "path": str(path),
            "branch": fixed_git_read(path, "branch", "--show-current"),
            "head": fixed_git_read(path, "rev-parse", "HEAD"),
            "subject": fixed_git_read(path, "show", "-s", "--format=%s", "HEAD"),
        }
    return state


def merge_semantic_fields(sections: list[Section], diagnostics: list[Diagnostic] | None = None) -> tuple[dict[str, str], list[dict[str, Any]]]:
    diagnostics = diagnostics if diagnostics is not None else []
    fields: dict[str, str] = {}
    records: list[dict[str, Any]] = []
    global_paths: dict[tuple[str, ...], tuple[str, int]] = {}
    for section in sections:
        if section.ownership != "shared_structured" and section.canonical_heading != "Metadata and governance":
            continue
        payload = mapping_payload(section)
        top_fields = parse_top_level_fields(payload)
        occurrences = parse_mapping_occurrences(section, diagnostics)
        for occurrence in occurrences:
            if occurrence.semantic_path in global_paths:
                old_section, old_line = global_paths[occurrence.semantic_path]
                diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E016", "error", f"Duplicate semantic path {'.'.join(occurrence.semantic_path)!r}; first at {old_section}:{old_line}.", section.source_heading, occurrence.line))
            else:
                global_paths[occurrence.semantic_path] = (section.source_heading, occurrence.line)
            records.append({
                "semantic_path": ".".join(occurrence.semantic_path),
                "path_components": list(occurrence.semantic_path),
                "field": occurrence.semantic_path[0],
                "source_section": section.source_heading,
                "source_line": occurrence.line,
                "source_value": occurrence.value,
                "source_text": occurrence.raw_line,
                "source_sha256": sha256_text(occurrence.raw_line),
            })
        for key, block in top_fields.items():
            if key not in fields:
                fields[key] = block
    return fields, records


def author_section_value(sections: list[Section], canonical: str) -> str:
    for section in sections:
        if section.canonical_heading == canonical:
            body = section_body(section).strip()
            fence = re.fullmatch(r"```(?:text)?\s*\n(.*?)\n```", body, re.DOTALL)
            return (fence.group(1) if fence else body).strip()
    return ""


def field_block(name: str, value: str) -> str:
    if "\n" not in value:
        return f"{name}: {value}"
    return f"{name}: >\n" + "\n".join(f"  {line}" for line in value.splitlines())


def mapping_block(name: str, values: dict[str, str]) -> str:
    return name + ":\n" + "\n".join(f"  {key}: {value}" for key, value in values.items())


def nested_mapping_block(name: str, values: dict[str, dict[str, str]]) -> str:
    lines = [name + ":"]
    for outer, inner in values.items():
        lines.append(f"  {outer}:")
        lines.extend(f"    {key}: {value}" for key, value in inner.items())
    return "\n".join(lines)


def add_repair(diagnostics: list[Diagnostic], repairs: list[dict[str, str]], field: str, reason: str, replacement: bool = False) -> None:
    repairs.append({"field": field, "reason": reason})
    diagnostic_id = "PROMPT-PREFLIGHT-W004" if replacement else "PROMPT-PREFLIGHT-W002"
    diagnostics.append(Diagnostic(diagnostic_id, "warning", reason + ".", field, 0))


def records_by_path(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    output: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        output.setdefault(record["semantic_path"], []).append(record)
    return output


def validate_branch_and_baseline(fields: dict[str, str], records: list[dict[str, Any]], live: dict[str, dict[str, str]], diagnostics: list[Diagnostic]) -> None:
    paths = records_by_path(records)
    repositories = set(live)
    policies = child_scalars(fields.get("branch_policy"))
    for unknown in sorted(set(policies) - repositories):
        diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E006", "error", f"Unknown repository in branch policy: {unknown}.", "branch_policy", 0))
    if set(policies) != repositories:
        diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E006", "error", "branch_policy must contain the complete governed repository set.", "branch_policy", 0))
    branch_fields = {name: child_scalars(fields.get(name)) for name in ("current_checked_out_branch", "current_baseline_branch", "reference_branch", "target_branch", "feature_branch")}
    for repository, state in live.items():
        policy = policies.get(repository, "")
        if policy in UNSUPPORTED_BRANCH_POLICIES or policy not in SUPPORTED_BRANCH_POLICIES:
            diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E006", "error", f"Unsupported prompt-preflight branch policy for {repository}: {policy or '<missing>'}.", "branch_policy", 0))
            continue
        expected = {
            "current_checked_out_branch": state["branch"],
            "current_baseline_branch": state["branch"],
            "reference_branch": "none",
            "feature_branch": "none",
            "target_branch": state["branch"] if policy == "continue_existing_branch" else "none",
        }
        for field, expected_value in expected.items():
            observed = branch_fields[field].get(repository, "")
            if observed != expected_value:
                diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E006", "error", f"{policy} requires {field}.{repository}={expected_value!r}; observed {observed or '<missing>'!r}.", field, 0))
    comparison = scalar(fields.get("comparison_baseline"))
    expected_baselines: dict[str, dict[str, str]] = {}
    if comparison and COMMIT_RE.fullmatch(comparison):
        if len(live) == 1:
            only = next(iter(live))
            expected_baselines[only] = {"expected_head": comparison}
        else:
            expected_baselines["meta_repo"] = {"expected_head": comparison}
    else:
        for repository in live:
            prefix = f"comparison_baseline.{repository}."
            expected_baselines[repository] = {}
            for key in ("expected_head", "expected_subject"):
                items = paths.get(prefix + key, [])
                if items:
                    expected_baselines[repository][key] = items[0]["source_value"]
    for unknown_path in paths:
        if unknown_path.startswith("comparison_baseline."):
            parts = unknown_path.split(".")
            if len(parts) > 1 and parts[1] not in live:
                diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E006", "error", f"Unknown repository in comparison_baseline: {parts[1]}.", "comparison_baseline", 0))
    for repository, state in live.items():
        expected = expected_baselines.get(repository, {})
        head = expected.get("expected_head", "")
        if not COMMIT_RE.fullmatch(head):
            diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E006", "error", f"comparison_baseline.{repository}.expected_head must be a full 40-hex commit.", "comparison_baseline", 0))
        elif head != state["head"]:
            diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E006", "error", f"Stale baseline for {repository}: expected {head}, live {state['head']}.", "comparison_baseline", 0))
        subject = expected.get("expected_subject")
        if subject is not None and subject != state["subject"]:
            diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E006", "error", f"Baseline subject mismatch for {repository}: expected {subject!r}, live {state['subject']!r}.", "comparison_baseline", 0))


def complete_fields(fields: dict[str, str], sections: list[Section], prompt_id: str, workspace_root: Path, live_state: dict[str, dict[str, str]], contexts: dict[str, str], diagnostics: list[Diagnostic], records: list[dict[str, Any]] | None = None) -> tuple[dict[str, str], list[dict[str, str]]]:
    del contexts
    completed = dict(fields)
    repairs: list[dict[str, str]] = []
    for field, section_name in (("goal", "Goal"), ("decision_question", "Decision question"), ("out_of_scope", "Out of scope")):
        if not scalar(completed.get(field)):
            value = author_section_value(sections, section_name)
            if value:
                completed[field] = field_block(field, value)
    short_title = scalar(completed.get("short_title")) or "unresolved_short_title"
    safe_title = re.sub(r"[^A-Za-z0-9_.-]+", "_", short_title).strip("_") or "prompt"
    diagnostics_root = workspace_root / "reports" / "diagnostics" / f"{prompt_id}_{safe_title}"
    agents_hash = sha256_bytes((workspace_root / "AGENTS.md").read_bytes())
    cpc_hash = sha256_bytes((workspace_root / "CPC.md").read_bytes())
    prompt_mode = scalar(completed.get("prompt_mode"))
    patch_kind = "prompt_local" if not prompt_mode or prompt_mode in {"coding", "documentation_only", "test_alignment_only", "commit_preparation"} else "empty_no_changes"
    fixed = {
        "workspace_root": field_block("workspace_root", str(workspace_root)),
        "repo_locations": mapping_block("repo_locations", {name: item["path"] for name, item in live_state.items()}),
        "current_checked_out_branch": mapping_block("current_checked_out_branch", {name: item["branch"] for name, item in live_state.items()}),
        "current_repository_heads": mapping_block("current_repository_heads", {name: item["head"] for name, item in live_state.items()}),
        "diagnostics_root": field_block("diagnostics_root", str(diagnostics_root)),
        "report_path": field_block("report_path", str(diagnostics_root / f"{prompt_id}_report.md")),
        "patch_path": field_block("patch_path", str(diagnostics_root / f"{prompt_id}_worktree_diff.patch")),
        "patch_kind_expected": field_block("patch_kind_expected", patch_kind),
        "source_control_policy": "source_control_policy:\n  - inherit live AGENTS defaults\n  - stage exact authorized paths only\n  - no remote mutation without explicit authority",
        "final_chat_deliverable": "final_chat_deliverable:\n  final status, decision question, live branch and HEAD observations, files changed, validation, report, patch, commit, caveats, next action, and cleanliness",
        "evidence_requirements": "evidence_requirements:\n  ordered_method:\n" + "\n".join(f"    - {phase}" for phase in EVIDENCE_SEQUENCE),
        "evidence_validation_method": field_block("evidence_validation_method", EVIDENCE_COMPACT),
        "classification_rules": "classification_rules:\n  - preserve author-owned content exactly\n  - validate shared intent without invention\n  - generate fixed skill-owned governance from live state",
        "anti_self_certification_rules": "anti_self_certification_rules:\n  - reopen serialized artifacts\n  - compare source and canonical hashes\n  - reject task action before readiness",
        "governance_binding_expectations": "governance_binding_expectations:\n  agents_sha256: " + agents_hash + "\n  cpc_sha256: " + cpc_hash,
    }
    for name, block in fixed.items():
        previous = completed.get(name)
        completed[name] = block
        if previous != block:
            add_repair(diagnostics, repairs, name, f"Generated authoritative skill-owned field {name}", replacement=bool(previous))
    for required in sorted(REQUIRED_AUTHOR_FIELDS):
        if not scalar(completed.get(required)) and not child_scalars(completed.get(required)):
            diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E005", "error", f"Required author semantic decision {required!r} is missing.", required, 0))
    commit_expected = scalar(completed.get("commit_expected"))
    do_not_commit = scalar(completed.get("do_not_commit"))
    if commit_expected not in {"yes", "no"} or do_not_commit not in {"yes", "no"} or commit_expected == do_not_commit:
        diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E009", "error", "Commit policy is unsupported or contradictory.", "commit policy", 0))
    validate_branch_and_baseline(fields, records or [], live_state, diagnostics)
    return completed, repairs


def generated_skill_sections(prompt_id: str, workspace_root: Path, live_state: dict[str, dict[str, str]]) -> dict[str, str]:
    agents_sha = sha256_bytes((workspace_root / "AGENTS.md").read_bytes())
    cpc_sha = sha256_bytes((workspace_root / "CPC.md").read_bytes())
    return {
        "Prompt preflight result": "## Prompt preflight result\n\nThe canonical task contract is inert until the state reaches `ready_for_same_session_execution`.\n",
        "Repository envelope": "## Repository envelope\n\n" + "\n".join(f"- `{name}`: `{item['branch']}` at `{item['head']}`" for name, item in live_state.items()) + "\n",
        "Standard execution boundaries": "## Standard execution boundaries\n\nNo task action, prompt-authored execution, nested Codex session, wrapper handoff, marker, or publication is performed by preflight.\n",
        "Evidence-order contract": "## Evidence-order contract\n\n" + "\n".join(f"{index}. `{phase}`" for index, phase in enumerate(EVIDENCE_SEQUENCE, 1)) + f"\n\n`{EVIDENCE_COMPACT}`\n",
        "Source-control policy": "## Source-control policy\n\nFollow live `AGENTS.md`; stage exact authorized paths only and infer no remote authority.\n",
        "Diagnostics and publication paths": f"## Diagnostics and publication paths\n\nDiagnostics derive from `{prompt_id}` under `{workspace_root / 'reports' / 'diagnostics'}`. Publication authority is never inferred.\n",
        "Standard report sections": "## Standard report sections\n\nReport the decision, evidence, validation, changed files, patch, commit, caveats, next action, and final cleanliness.\n",
        "Standard final-response fields": "## Standard final-response fields\n\nReturn final status, decision question, live branch and HEAD, validation, files, commit, artifact paths, caveats, next action, and cleanliness.\n",
        "Governance-binding evidence": f"## Governance-binding evidence\n\n- `AGENTS.md`: `{agents_sha}`\n- `CPC.md`: `{cpc_sha}`\n",
    }


def canonicalize(prompt_id: str, short_title: str, fields: dict[str, str], sections: list[Section], workspace_root: Path, live_state: dict[str, dict[str, str]], diagnostics: list[Diagnostic], preamble: str | None = None) -> tuple[str, list[dict[str, Any]]]:
    del short_title
    metadata = "\n\n".join(fields[name] for name in FIELD_ORDER if name in fields)
    skill_sections = generated_skill_sections(prompt_id, workspace_root, live_state)
    if preamble is None:
        preamble = f"# Prompt `{prompt_id}`\n\n"
    canonical = preamble + "## Metadata and governance\n\n```text\n" + metadata + "\n```\n\n"
    canonical += "\n".join(skill_sections.values()) + "\n"
    canonical += "".join(section.raw for section in sections if section.ownership != "skill_owned")
    if not canonical.endswith("\n"):
        canonical += "\n"
    manifest: list[dict[str, Any]] = [{
        "source_heading": "<preamble>", "canonical_heading": "<preamble>",
        "ownership": "author_owned", "source_start_line": 1,
        "source_end_line": len(preamble.splitlines()), "source_sha256": sha256_text(preamble),
        "canonical_sha256": sha256_text(preamble), "preserved_exactly": canonical.startswith(preamble),
        "alias_applied": False, "authoritative_in_canonical": True,
    }]
    if not manifest[0]["preserved_exactly"]:
        diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E007", "error", "The complete prompt preamble changed.", "<preamble>", 1))
    generated_hashes = {name: sha256_text(raw) for name, raw in skill_sections.items()}
    generated_hashes["Metadata and governance"] = sha256_text("## Metadata and governance\n\n```text\n" + metadata + "\n```\n")
    for section in sections:
        authoritative = section.ownership != "skill_owned"
        count = canonical.count(section.raw) if authoritative else 0
        canonical_hash = section.sha256 if count == 1 else generated_hashes.get(section.canonical_heading, "")
        preserved = authoritative and count == 1 and canonical_hash == section.sha256
        if section.ownership == "skill_owned":
            diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-W001", "warning", "Authored skill-owned content was replaced in the canonical prompt.", section.source_heading, section.start_line))
        elif not preserved:
            code = "PROMPT-PREFLIGHT-E007" if section.ownership == "author_owned" else "PROMPT-PREFLIGHT-E008"
            diagnostics.append(Diagnostic(code, "error", "Owned source bytes changed or became ambiguous in canonical output.", section.source_heading, section.start_line))
        manifest.append({"source_heading": section.source_heading, "canonical_heading": section.canonical_heading, "ownership": section.ownership, "source_start_line": section.start_line, "source_end_line": section.end_line, "source_sha256": section.sha256, "canonical_sha256": canonical_hash, "preserved_exactly": preserved, "alias_applied": section.alias_applied, "authoritative_in_canonical": authoritative})
    return canonical, manifest


def transport_diagnostics(text: str) -> list[Diagnostic]:
    normal = _permission_normal_form(text)
    hidden = r"(?:hidden\s+)?(?:chat\s+transport|user\s+interface|composer|message\s+transport|unobservable\s+original)\s+bytes?"
    requirement = r"(?:require|requires|required|must|verify|verifies|verified|claim|claims|claimed|condition|conditions|conditioned|exact|identical|identity)"
    patterns = (rf"\b{requirement}\b(?:\s+\w+){{0,14}}\s+\b{hidden}\b", rf"\b{hidden}\b(?:\s+\w+){{0,14}}\s+\b{requirement}\b")
    if any(re.search(pattern, normal) for pattern in patterns):
        return [Diagnostic("PROMPT-PREFLIGHT-E015", "error", "The prompt requires, claims, verifies, or conditions acceptance on inaccessible transport-byte identity.", "<prompt>", 0)]
    return []


def binding_diagnostics(workspace_root: Path, skill_root: Path) -> list[Diagnostic]:
    path = skill_root / "references/governance_binding.json"
    if not path.is_file():
        return [Diagnostic("PROMPT-PREFLIGHT-E011", "error", "The prompt-preflight governance binding is missing.", "Governance-binding evidence", 0)]
    binding = load_json(path)
    agents_hash = sha256_bytes((workspace_root / "AGENTS.md").read_bytes())
    cpc_hash = sha256_bytes((workspace_root / "CPC.md").read_bytes())
    if binding.get("agents_sha256") != agents_hash or binding.get("cpc_sha256") != cpc_hash:
        return [Diagnostic("PROMPT-PREFLIGHT-E011", "error", "The prompt-preflight governance binding is stale.", "Governance-binding evidence", 0)]
    return []


def invoke_prompt_contract(workspace_root: Path, canonical_path: Path, contexts: dict[str, str]) -> tuple[dict[str, Any], int]:
    validator = workspace_root / ".agents/skills/correction-lib-prompt-contract/scripts/validate_prompt.py"
    argv = [sys.executable, str(validator), "--workspace-root", str(workspace_root), "--continuation", contexts["continuation"], "--evidence-round", contexts["evidence_round"], "--user-run-handoff", contexts["user_run_handoff"], "--format", "json", str(canonical_path)]
    completed = subprocess.run(argv, check=False, shell=False, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)
    try:
        validation = json.loads(completed.stdout)
    except json.JSONDecodeError:
        validation = {"valid_schema": False, "error_count": 1, "warning_count": 0, "diagnostics": [], "stderr": completed.stderr, "stdout": completed.stdout}
    canonical_hash = sha256_bytes(canonical_path.read_bytes())
    validator_hash = validation.get("input", {}).get("sha256", "")
    validation["validator_input_sha256"] = validator_hash
    validation["canonical_prompt_sha256"] = canonical_hash
    validation["validator_input_sha256_matches_canonical"] = validator_hash == canonical_hash
    if not validation["validator_input_sha256_matches_canonical"]:
        validation["error_count"] = int(validation.get("error_count", 0)) + 1
    return validation, completed.returncode


def transition_state(states: list[str], next_state: str, registry: dict[str, Any], renderer_owned: bool = True) -> None:
    current = states[-1]
    edge = [current, next_state]
    if edge not in registry["allowed_transitions"] or (renderer_owned and next_state == "execution_started"):
        raise PreflightBlocked(Diagnostic("PROMPT-PREFLIGHT-E020", "error", f"Unregistered or renderer-forbidden state transition: {current} -> {next_state}.", "preflight_state", 0))
    states.append(next_state)


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _has_symlink_component(path: Path, stop: Path) -> bool:
    current = path
    while current != stop and current != current.parent:
        if current.exists() and current.is_symlink():
            return True
        current = current.parent
    return stop.is_symlink()


def validate_paths(source_path: Path, output_root: Path, workspace_root: Path) -> list[Diagnostic]:
    diagnostics_root = (workspace_root / "reports" / "diagnostics").resolve()
    source_absolute = source_path if source_path.is_absolute() else Path.cwd() / source_path
    output_absolute = output_root if output_root.is_absolute() else Path.cwd() / output_root
    try:
        source_resolved = source_absolute.resolve(strict=True)
    except OSError:
        return [Diagnostic("PROMPT-PREFLIGHT-E018", "error", "Source capture does not resolve to an existing regular diagnostics file.", str(source_path), 0)]
    if not _inside(source_absolute.absolute(), diagnostics_root) or not _inside(source_resolved, diagnostics_root):
        return [Diagnostic("PROMPT-PREFLIGHT-E018", "error", "Source capture escapes the diagnostics root.", str(source_path), 0)]
    source_mode = source_absolute.lstat().st_mode
    if stat.S_ISLNK(source_mode) or not stat.S_ISREG(source_mode) or _has_symlink_component(source_absolute.parent, diagnostics_root):
        return [Diagnostic("PROMPT-PREFLIGHT-E018", "error", "Source capture must be a regular nonsymlink diagnostics file.", str(source_path), 0)]
    output_lexical = Path(os.path.abspath(str(output_absolute)))
    if not _inside(output_lexical, diagnostics_root):
        return [Diagnostic("PROMPT-PREFLIGHT-E018", "error", "Output root escapes the diagnostics root.", str(output_root), 0)]
    if output_lexical.exists():
        return [Diagnostic("PROMPT-PREFLIGHT-E012", "error", "The output root already exists; overwrite and resume are forbidden.", str(output_root), 0)]
    parent = output_lexical.parent
    try:
        parent_resolved = parent.resolve(strict=True)
    except OSError:
        parent_resolved = parent.resolve(strict=False)
    if not _inside(parent_resolved, diagnostics_root) or _has_symlink_component(parent, diagnostics_root):
        return [Diagnostic("PROMPT-PREFLIGHT-E018", "error", "Output root has a resolved or symlink traversal outside diagnostics.", str(output_root), 0)]
    if output_lexical == source_absolute.parent.absolute():
        return [Diagnostic("PROMPT-PREFLIGHT-E018", "error", "Output root cannot equal the source parent.", str(output_root), 0)]
    return []


def report_text(state: dict[str, Any], diagnostics: list[Diagnostic]) -> str:
    lines = ["# Prompt preflight report", "", "## Preflight result", "", f"- current_state: `{state['current_state']}`", f"- source_sha256: `{state.get('source_sha256', '')}`", f"- canonical_prompt_sha256: `{state.get('canonical_prompt_sha256', '')}`", f"- blocking_error_count: `{state['blocking_error_count']}`", f"- warning_count: `{state['warning_count']}`", "", "## Repairs", ""]
    lines.extend(f"- `{item['field']}`: {item['reason']}" for item in state.get("repairs", []))
    if not state.get("repairs"):
        lines.append("- none")
    lines.extend(["", "## Diagnostics", ""])
    lines.extend(f"- `{item.id}` [{item.severity}] {item.message}" for item in diagnostics)
    if not diagnostics:
        lines.append("- none")
    lines.extend(["", "## Governance hashes", "", f"- AGENTS.md: `{state.get('agents_sha256', '')}`", f"- CPC.md: `{state.get('cpc_sha256', '')}`", ""])
    return "\n".join(lines)


def validate_csv(path: Path, exact_headers: list[str]) -> list[str]:
    try:
        with path.open(newline="", encoding="utf-8") as stream:
            reader = csv.reader(stream)
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        return [str(exc)]
    if not rows or rows[0] != exact_headers:
        return ["CSV header mismatch"]
    return [f"row {index} has {len(row)} columns, expected {len(exact_headers)}" for index, row in enumerate(rows[1:], 2) if len(row) != len(exact_headers)]


def validate_generated_artifacts(output_root: Path, state: dict[str, Any], require_canonical: bool = True) -> list[Diagnostic]:
    failures: list[str] = []
    reopening_failures: list[str] = []
    required = set(OUTPUT_NAMES if require_canonical else ("authored_prompt.md", "section_manifest.json", "shared_value_manifest.json", "prompt_contract_validation.json", "preflight_state.json", "preflight_report.md"))
    for name in required:
        path = output_root / name
        if not path.is_file():
            failures.append(f"missing {name}")
            continue
        try:
            content = path.read_text(encoding="utf-8")
            if name in JSON_OUTPUTS:
                value = json.loads(content)
                if not isinstance(value, (dict, list)):
                    failures.append(f"{name} top-level type")
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            reopening_failures.append(f"{name}: {exc}")
    if reopening_failures:
        return [Diagnostic("PROMPT-PREFLIGHT-E013", "error", "Generated artifact reopening failed: " + "; ".join(reopening_failures), str(output_root), 0)]
    if failures:
        return [Diagnostic("PROMPT-PREFLIGHT-E019", "error", "Generated artifact schema validation failed: " + "; ".join(failures), str(output_root), 0)]
    authored_hash = sha256_bytes((output_root / "authored_prompt.md").read_bytes())
    if authored_hash != state.get("source_sha256"):
        failures.append("authored_prompt source hash mismatch")
    manifest = load_json(output_root / "shared_value_manifest.json")
    if not isinstance(manifest.get("records"), list) or not isinstance(manifest.get("author_semantic_invention_count"), int) or not isinstance(manifest.get("author_semantic_change_count"), int):
        failures.append("shared_value_manifest required keys or types")
    sections = json.loads((output_root / "section_manifest.json").read_text(encoding="utf-8"))
    if not isinstance(sections, list) or not sections:
        failures.append("section_manifest must be a nonempty list")
    else:
        required_keys = {"source_heading", "canonical_heading", "ownership", "source_start_line", "source_end_line", "source_sha256", "canonical_sha256", "preserved_exactly", "alias_applied", "authoritative_in_canonical"}
        for index, item in enumerate(sections):
            if not isinstance(item, dict) or not required_keys.issubset(item):
                failures.append(f"section_manifest row {index} keys")
                continue
            if not SHA256_RE.fullmatch(item["source_sha256"]) or (item["canonical_sha256"] and not SHA256_RE.fullmatch(item["canonical_sha256"])):
                failures.append(f"section_manifest row {index} hash syntax")
            if not isinstance(item["source_start_line"], int) or not isinstance(item["source_end_line"], int) or item["source_end_line"] < item["source_start_line"]:
                failures.append(f"section_manifest row {index} line range")
    persisted_state = load_json(output_root / "preflight_state.json")
    if persisted_state.get("states_visited") != state.get("states_visited") or persisted_state.get("current_state") != state.get("current_state"):
        failures.append("preflight_state sequence mismatch")
    if not all(SHA256_RE.fullmatch(state.get(key, "")) for key in ("source_sha256", "agents_sha256", "cpc_sha256")):
        failures.append("state governance/source hash syntax")
    report = (output_root / "preflight_report.md").read_text(encoding="utf-8")
    for heading in ("# Prompt preflight report", "## Preflight result", "## Diagnostics", "## Governance hashes"):
        if heading not in report:
            failures.append(f"report missing {heading}")
    if state["source_sha256"] not in report or state["agents_sha256"] not in report or state["cpc_sha256"] not in report:
        failures.append("report missing embedded hashes")
    if require_canonical:
        canonical_hash = sha256_bytes((output_root / "canonical_prompt.md").read_bytes())
        if canonical_hash != state.get("canonical_prompt_sha256"):
            failures.append("canonical prompt hash mismatch")
        validation = load_json(output_root / "prompt_contract_validation.json")
        if validation.get("canonical_prompt_sha256") != canonical_hash or not validation.get("validator_input_sha256_matches_canonical"):
            failures.append("prompt-contract cross-artifact hash mismatch")
    return [] if not failures else [Diagnostic("PROMPT-PREFLIGHT-E019", "error", "Generated artifact schema validation failed: " + "; ".join(failures), str(output_root), 0)]


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json_text(value), encoding="utf-8")


def _blocked_without_output(diagnostic: Diagnostic) -> tuple[dict[str, Any], int]:
    return {"current_state": "blocked_semantic_ambiguity", "blocking_error_count": 1, "warning_count": 0, "diagnostics": [asdict(diagnostic)], "task_execution_performed": False, "nested_codex_launched": False}, 3


def run_preflight(source_path: Path, output_root: Path, workspace_root: Path, contexts: dict[str, str]) -> tuple[dict[str, Any], int]:
    path_diagnostics = validate_paths(source_path, output_root, workspace_root)
    if path_diagnostics:
        return _blocked_without_output(path_diagnostics[0])
    source_bytes = source_path.read_bytes()
    try:
        source_text = source_bytes.decode("utf-8")
    except UnicodeError as exc:
        raise PreflightInputError(f"source capture is not UTF-8: {exc}") from exc
    skill_root = Path(__file__).resolve().parents[1]
    registry = load_json(skill_root / "references/section_ownership.json")
    schema = load_json(skill_root / "references/preflight_schema.json")
    if registry.get("prompt_section_ownership_version") != OWNERSHIP_CONTRACT_VERSION or schema.get("schema_version") != SCHEMA_VERSION:
        raise PreflightInputError("skill schema or ownership-contract version mismatch")
    output_root.mkdir(parents=False, exist_ok=False)
    (output_root / "authored_prompt.md").write_bytes(source_bytes)
    states = ["not_triggered"]
    transition_state(states, "source_captured", registry)
    sections, diagnostics, preamble = parse_sections(source_text, registry)
    diagnostics.extend(transport_diagnostics(source_text))
    diagnostics.extend(binding_diagnostics(workspace_root, skill_root))
    fields, shared_records = merge_semantic_fields(sections, diagnostics)
    transition_state(states, "classified", registry)
    prompt_id = scalar(fields.get("prompt_id")) or "unresolved_prompt_id"
    live_state = live_repository_state(workspace_root)
    completed, repairs = complete_fields(fields, sections, prompt_id, workspace_root, live_state, contexts, diagnostics, shared_records)
    agents_hash = sha256_bytes((workspace_root / "AGENTS.md").read_bytes())
    cpc_hash = sha256_bytes((workspace_root / "CPC.md").read_bytes())
    source_hash = sha256_bytes(source_bytes)
    blocking = [item for item in diagnostics if item.severity == "error"]
    if blocking:
        transition_state(states, "blocked_semantic_ambiguity", registry)
        state = {"skill_version": SKILL_VERSION, "renderer_version": RENDERER_VERSION, "ownership_contract_version": OWNERSHIP_CONTRACT_VERSION, "schema_version": SCHEMA_VERSION, "current_state": states[-1], "states_visited": states, "source_representation": "normalized_visible_message_utf8", "source_sha256": source_hash, "canonical_prompt_sha256": "", "agents_sha256": agents_hash, "cpc_sha256": cpc_hash, "blocking_error_count": len(blocking), "warning_count": sum(item.severity == "warning" for item in diagnostics), "diagnostics": [asdict(item) for item in diagnostics], "repairs": repairs, "prompt_contract_invoked": False, "task_execution_performed": False, "nested_codex_launched": False}
        section_manifest = [{"source_heading": "<preamble>", "canonical_heading": "<preamble>", "ownership": "author_owned", "source_start_line": 1, "source_end_line": len(preamble.splitlines()), "source_sha256": sha256_text(preamble), "canonical_sha256": "", "preserved_exactly": False, "alias_applied": False, "authoritative_in_canonical": False}]
        _write_json(output_root / "section_manifest.json", section_manifest)
        _write_json(output_root / "shared_value_manifest.json", {"records": shared_records, "author_semantic_invention_count": 0, "author_semantic_change_count": 0})
        _write_json(output_root / "prompt_contract_validation.json", {"invoked": False, "error_count": 0, "warning_count": 0, "canonical_prompt_sha256": "", "validator_input_sha256_matches_canonical": False})
        _write_json(output_root / "preflight_state.json", state)
        (output_root / "preflight_report.md").write_text(report_text(state, diagnostics), encoding="utf-8")
        schema_diags = validate_generated_artifacts(output_root, state, require_canonical=False)
        if schema_diags:
            state["diagnostics"].extend(asdict(item) for item in schema_diags)
            state["blocking_error_count"] += len(schema_diags)
            _write_json(output_root / "preflight_state.json", state)
        return state, 3
    short_title = scalar(completed.get("short_title")) or "unresolved_short_title"
    canonical, section_manifest = canonicalize(prompt_id, short_title, completed, sections, workspace_root, live_state, diagnostics, preamble)
    transition_state(states, "canonicalized", registry)
    canonical_path = output_root / "canonical_prompt.md"
    canonical_path.write_text(canonical, encoding="utf-8")
    canonical_hash = sha256_bytes(canonical_path.read_bytes())
    validation, validator_exit = invoke_prompt_contract(workspace_root, canonical_path, contexts)
    if validator_exit or validation.get("error_count", 0) or not validation.get("validator_input_sha256_matches_canonical"):
        diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E010", "error", "The authoritative prompt-contract validator rejected the canonical prompt.", "Metadata and governance", 0))
        transition_state(states, "blocked_prompt_contract", registry)
        exit_code = 3
    else:
        transition_state(states, "prompt_contract_passed", registry)
        exit_code = 0
    for record in shared_records:
        semantic = record["field"] in AUTHOR_SEMANTIC_FIELDS
        record["semantic_value_preserved"] = semantic
        record["mechanical_replacement"] = record["field"] in FIXED_SKILL_FIELDS
        record["canonical_value"] = record["source_value"] if semantic else ""
        record["canonical_sha256"] = record["source_sha256"] if semantic else ""
    blocking = [item for item in diagnostics if item.severity == "error"]
    state = {"skill_version": SKILL_VERSION, "renderer_version": RENDERER_VERSION, "ownership_contract_version": OWNERSHIP_CONTRACT_VERSION, "schema_version": SCHEMA_VERSION, "current_state": states[-1], "states_visited": states, "source_representation": "normalized_visible_message_utf8", "source_sha256": source_hash, "canonical_prompt_sha256": canonical_hash, "agents_sha256": agents_hash, "cpc_sha256": cpc_hash, "blocking_error_count": len(blocking), "warning_count": sum(item.severity == "warning" for item in diagnostics) + int(validation.get("warning_count", 0)), "diagnostics": [asdict(item) for item in diagnostics], "repairs": repairs, "prompt_contract_invoked": True, "prompt_contract_error_count": int(validation.get("error_count", 0)), "task_execution_performed": False, "nested_codex_launched": False}
    _write_json(output_root / "section_manifest.json", section_manifest)
    _write_json(output_root / "shared_value_manifest.json", {"records": shared_records, "author_semantic_invention_count": 0, "author_semantic_change_count": 0})
    _write_json(output_root / "prompt_contract_validation.json", validation)
    _write_json(output_root / "preflight_state.json", state)
    (output_root / "preflight_report.md").write_text(report_text(state, diagnostics), encoding="utf-8")
    schema_diags = validate_generated_artifacts(output_root, state, require_canonical=True)
    if schema_diags and state["current_state"] == "prompt_contract_passed":
        diagnostics.extend(schema_diags)
        transition_state(states, "blocked_prompt_contract", registry)
        state["current_state"] = states[-1]
        state["states_visited"] = states
        state["blocking_error_count"] += len(schema_diags)
        state["diagnostics"] = [asdict(item) for item in diagnostics]
        exit_code = 3
    elif state["current_state"] == "prompt_contract_passed":
        candidate_states = list(states)
        transition_state(candidate_states, "ready_for_same_session_execution", registry)
        state["current_state"] = candidate_states[-1]
        state["states_visited"] = candidate_states
        _write_json(output_root / "preflight_state.json", state)
        (output_root / "preflight_report.md").write_text(report_text(state, diagnostics), encoding="utf-8")
        final_schema = validate_generated_artifacts(output_root, state, require_canonical=True)
        if final_schema:
            diagnostics.extend(final_schema)
            transition_state(states, "blocked_prompt_contract", registry)
            state["current_state"] = states[-1]
            state["states_visited"] = states
            state["blocking_error_count"] += len(final_schema)
            state["diagnostics"] = [asdict(item) for item in diagnostics]
            exit_code = 3
        else:
            states = candidate_states
    _write_json(output_root / "preflight_state.json", state)
    (output_root / "preflight_report.md").write_text(report_text(state, diagnostics), encoding="utf-8")
    return state, exit_code


def assert_ready_for_task_action(state_path: Path) -> None:
    state = load_json(state_path)
    if state.get("current_state") != "ready_for_same_session_execution" or state.get("blocking_error_count") != 0:
        raise PreflightBlocked(Diagnostic("PROMPT-PREFLIGHT-E014", "error", "Task action was attempted before preflight passed.", "preflight_state", 0))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preflight an inert visible correction-lib Markdown prompt.")
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--continuation", choices=CONTEXT_VALUES, required=True)
    parser.add_argument("--evidence-round", choices=CONTEXT_VALUES, required=True)
    parser.add_argument("--user-run-handoff", choices=CONTEXT_VALUES, required=True)
    parser.add_argument("--format", choices=("human", "json"), default="human")
    parser.add_argument("source_prompt", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    contexts = {"continuation": args.continuation, "evidence_round": args.evidence_round, "user_run_handoff": args.user_run_handoff}
    try:
        state, exit_code = run_preflight(args.source_prompt, args.output_root, args.workspace_root.resolve(), contexts)
    except PreflightInputError as exc:
        print(f"input_error: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        sys.stdout.write(json_text(state))
    else:
        print(f"state: {state['current_state']}")
        print(f"blocking_errors: {state['blocking_error_count']}")
        for diagnostic in state.get("diagnostics", []):
            print(f"{diagnostic['severity']} {diagnostic['id']}: {diagnostic['message']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
