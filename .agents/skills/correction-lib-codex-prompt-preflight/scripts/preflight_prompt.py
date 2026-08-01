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
import secrets
import stat
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


SKILL_VERSION = "1.0.2"
RENDERER_VERSION = "1.0.2"
SCHEMA_VERSION = "1.0.2"
OWNERSHIP_CONTRACT_VERSION = "1.0.2"
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
    "readiness_binding.json",
)
JSON_OUTPUTS = {
    "section_manifest.json",
    "shared_value_manifest.json",
    "prompt_contract_validation.json",
    "preflight_state.json",
    "readiness_binding.json",
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
    [f"PROMPT-PREFLIGHT-E{index:03d}" for index in range(1, 24)]
    + [f"PROMPT-PREFLIGHT-W{index:03d}" for index in range(1, 5)]
)
DIAGNOSTIC_CATALOG_LITERAL = """
PROMPT-PREFLIGHT-E001 PROMPT-PREFLIGHT-E002 PROMPT-PREFLIGHT-E003
PROMPT-PREFLIGHT-E004 PROMPT-PREFLIGHT-E005 PROMPT-PREFLIGHT-E006
PROMPT-PREFLIGHT-E007 PROMPT-PREFLIGHT-E008 PROMPT-PREFLIGHT-E009
PROMPT-PREFLIGHT-E010 PROMPT-PREFLIGHT-E011 PROMPT-PREFLIGHT-E012
PROMPT-PREFLIGHT-E013 PROMPT-PREFLIGHT-E014 PROMPT-PREFLIGHT-E015
PROMPT-PREFLIGHT-E016 PROMPT-PREFLIGHT-E017 PROMPT-PREFLIGHT-E018
PROMPT-PREFLIGHT-E019 PROMPT-PREFLIGHT-E020 PROMPT-PREFLIGHT-E021
PROMPT-PREFLIGHT-E022 PROMPT-PREFLIGHT-E023 PROMPT-PREFLIGHT-W001
PROMPT-PREFLIGHT-W002 PROMPT-PREFLIGHT-W003 PROMPT-PREFLIGHT-W004
"""
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
    authority_phrases = (
        r"authorized\s+to", r"authorization\s+to", r"(?:feel\s+)?free\s+to",
        r"go\s+ahead", r"permission(?:s)?(?:\s+to)?", r"entitled\s+to",
        r"at\s+liberty\s+to", r"yours\s+to",
    )
    if any(re.search(rf"\b{phrase}\b", normal) for phrase in authority_phrases):
        return True
    modal = r"(?:may|can|must|should|shall|permitted|allowed|forbidden|required|optional)"
    action = r"(?:edit|modify|change|write|delete|remove|create|stage|commit|push|publish|merge|switch|reset|restore|clean|install|execute|run|inspect|access|read|rewrite|alter|revise|touch|overwrite|replace|reconfigure|grant)(?:s|ed|ing)?"
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


def validate_shared_section_grammar(section: Section, diagnostics: list[Diagnostic], registry: dict[str, Any]) -> None:
    """Enforce the one-fenced-text-mapping grammar for shared input."""
    body = section_body(section).splitlines()
    inside = False
    opened = 0
    closed = 0
    fence_character = ""
    fence_length = 0
    for offset, line in enumerate(body, 1):
        line_number = section.start_line + offset
        if inside:
            close = re.match(r"^ {0,3}([`~]+)[ \t]*$", line)
            if close and close.group(1)[0] == fence_character and len(close.group(1)) == fence_length:
                inside = False
                closed += 1
            continue
        opening = re.match(r"^ {0,3}([`~]{3,})([^`]*)$", line)
        if opening and len(set(opening.group(1))) == 1:
            opened += 1
            if opening.group(2).strip().casefold() != "text":
                diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E021", "error", "Shared structured sections permit only one fenced text mapping.", section.source_heading, line_number))
            inside = True
            fence_character = opening.group(1)[0]
            fence_length = len(opening.group(1))
            continue
        stripped = line.strip()
        if not stripped:
            continue
        if re.fullmatch(r"<!--\s*[A-Za-z0-9 .,_:-]{0,160}\s*-->", stripped):
            if unknown_is_normative(section.source_heading, stripped, registry):
                diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E021", "error", "Normative comments are forbidden outside a shared mapping.", section.source_heading, line_number))
            continue
        diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E021", "error", "Shared structured content outside its single fenced text mapping is forbidden.", section.source_heading, line_number))
    if opened != 1 or closed != 1 or inside:
        diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E021", "error", "Shared structured sections require exactly one closed fenced text mapping.", section.source_heading, section.start_line))


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


def merge_semantic_fields(sections: list[Section], diagnostics: list[Diagnostic] | None = None, registry: dict[str, Any] | None = None) -> tuple[dict[str, str], list[dict[str, Any]]]:
    diagnostics = diagnostics if diagnostics is not None else []
    fields: dict[str, str] = {}
    records: list[dict[str, Any]] = []
    global_paths: dict[tuple[str, ...], tuple[str, int]] = {}
    for section in sections:
        if section.ownership != "shared_structured" and section.canonical_heading != "Metadata and governance":
            continue
        if registry is not None:
            validate_shared_section_grammar(section, diagnostics, registry)
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


def metadata_text(fields: dict[str, str]) -> str:
    ordered = [name for name in FIELD_ORDER if name in fields]
    ordered.extend(sorted(set(fields) - set(ordered)))
    return "\n\n".join(fields[name] for name in ordered)


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
    metadata = metadata_text(fields)
    skill_sections = generated_skill_sections(prompt_id, workspace_root, live_state)
    if preamble is None:
        preamble = f"# Prompt `{prompt_id}`\n\n"
    canonical = preamble + "## Metadata and governance\n\n```text\n" + metadata + "\n```\n\n"
    canonical += "\n".join(skill_sections.values()) + "\n"
    # Source shared sections are audit input, not a second executable authority.
    # Their validated author-intent values appear once in generated metadata.
    canonical += "".join(section.raw for section in sections if section.ownership == "author_owned")
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
        authoritative = section.ownership == "author_owned"
        count = canonical.count(section.raw) if authoritative else 0
        canonical_hash = section.sha256 if count == 1 else generated_hashes.get(section.canonical_heading, "")
        preserved = authoritative and count == 1 and canonical_hash == section.sha256
        if section.ownership == "skill_owned":
            diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-W001", "warning", "Authored skill-owned content was replaced in the canonical prompt.", section.source_heading, section.start_line))
        elif section.ownership == "author_owned" and not preserved:
            diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E007", "error", "Author-owned source bytes changed or became ambiguous in canonical output.", section.source_heading, section.start_line))
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


def invoke_prompt_contract(workspace_root: Path, canonical_path: Path, contexts: dict[str, str], pass_fds: tuple[int, ...] = ()) -> tuple[dict[str, Any], int]:
    validator = workspace_root / ".agents/skills/correction-lib-prompt-contract/scripts/validate_prompt.py"
    argv = [sys.executable, str(validator), "--workspace-root", str(workspace_root), "--continuation", contexts["continuation"], "--evidence-round", contexts["evidence_round"], "--user-run-handoff", contexts["user_run_handoff"], "--format", "json", str(canonical_path)]
    completed = subprocess.run(argv, check=False, shell=False, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60, pass_fds=pass_fds)
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


def _relative_parts(path: Path) -> tuple[str, ...]:
    if path.is_absolute():
        raise PreflightInputError("diagnostics source and output paths must be relative")
    parts = tuple(path.parts)
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise PreflightInputError("diagnostics paths may not contain empty, dot, or parent components")
    return parts


def _read_fd_all(fd: int) -> bytes:
    os.lseek(fd, 0, os.SEEK_SET)
    chunks: list[bytes] = []
    while True:
        chunk = os.read(fd, 1024 * 1024)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


def _descriptor_is_below(child_fd: int, root_fd: int) -> bool:
    try:
        child = Path(os.readlink(f"/proc/self/fd/{child_fd}"))
        root = Path(os.readlink(f"/proc/self/fd/{root_fd}"))
        child.relative_to(root)
        return True
    except (OSError, ValueError):
        return False


class DescriptorRoot:
    """No-follow, descriptor-rooted diagnostics I/O."""

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root
        self.path = workspace_root / "reports" / "diagnostics"
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0)
        self.fd = os.open(self.path, flags)

    def close(self) -> None:
        if self.fd >= 0:
            os.close(self.fd)
            self.fd = -1

    def __enter__(self) -> "DescriptorRoot":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

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

    def read_source(self, relative: Path) -> tuple[bytes, dict[str, int]]:
        parts = _relative_parts(relative)
        parent_fd = self.open_directory(parts[:-1])
        try:
            flags = os.O_RDONLY | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0)
            fd = os.open(parts[-1], flags, dir_fd=parent_fd)
        finally:
            os.close(parent_fd)
        try:
            before = os.fstat(fd)
            if not stat.S_ISREG(before.st_mode):
                raise PreflightInputError("source capture must be a regular nonsymlink file")
            content = _read_fd_all(fd)
            after = os.fstat(fd)
            identity = (before.st_dev, before.st_ino, before.st_size)
            if identity != (after.st_dev, after.st_ino, after.st_size) or len(content) != before.st_size:
                raise PreflightInputError("source identity changed while it was read")
            return content, {"device": before.st_dev, "inode": before.st_ino, "size": before.st_size}
        finally:
            os.close(fd)

    def create_stage(self, relative: Path) -> "DescriptorStage":
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
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0)
        staging_fd = os.open(staging_name, flags, dir_fd=parent_fd)
        identity = os.fstat(staging_fd)
        return DescriptorStage(self, parent_fd, staging_fd, staging_name, final_name, relative, identity.st_dev, identity.st_ino)

    def open_output(self, relative: Path) -> int:
        return self.open_directory(_relative_parts(relative))


class DescriptorStage:
    def __init__(self, root: DescriptorRoot, parent_fd: int, fd: int, staging_name: str, final_name: str, relative: Path, device: int, inode: int) -> None:
        self.root = root
        self.parent_fd = parent_fd
        self.fd = fd
        self.staging_name = staging_name
        self.final_name = final_name
        self.relative = relative
        self.device = device
        self.inode = inode
        self.published = False

    def close(self) -> None:
        for attribute in ("fd", "parent_fd"):
            descriptor = getattr(self, attribute)
            if descriptor >= 0:
                os.close(descriptor)
                setattr(self, attribute, -1)

    def write(self, name: str, content: bytes) -> None:
        if name not in OUTPUT_NAMES:
            raise PreflightInputError(f"unregistered output artifact: {name}")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0)
        file_fd = os.open(name, flags, 0o600, dir_fd=self.fd)
        try:
            view = memoryview(content)
            while view:
                written = os.write(file_fd, view)
                view = view[written:]
            os.fsync(file_fd)
        finally:
            os.close(file_fd)

    def replace(self, name: str, content: bytes) -> None:
        temporary = f".{name}.{secrets.token_hex(8)}"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0)
        file_fd = os.open(temporary, flags, 0o600, dir_fd=self.fd)
        try:
            os.write(file_fd, content)
            os.fsync(file_fd)
        finally:
            os.close(file_fd)
        os.rename(temporary, name, src_dir_fd=self.fd, dst_dir_fd=self.fd)

    def read(self, name: str) -> bytes:
        flags = os.O_RDONLY | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0)
        file_fd = os.open(name, flags, dir_fd=self.fd)
        try:
            info = os.fstat(file_fd)
            if not stat.S_ISREG(info.st_mode):
                raise PreflightInputError(f"artifact is not regular: {name}")
            return _read_fd_all(file_fd)
        finally:
            os.close(file_fd)

    def inventory(self) -> set[str]:
        return set(os.listdir(self.fd))

    def proc_path(self, name: str) -> Path:
        return Path(f"/proc/self/fd/{self.fd}/{name}")

    def publish(self) -> None:
        os.fsync(self.fd)
        if not _descriptor_is_below(self.parent_fd, self.root.fd) or not _descriptor_is_below(self.fd, self.root.fd):
            raise PreflightInputError("held output descriptors no longer remain below diagnostics")
        observed = os.stat(self.staging_name, dir_fd=self.parent_fd, follow_symlinks=False)
        if not stat.S_ISDIR(observed.st_mode) or (observed.st_dev, observed.st_ino) != (self.device, self.inode):
            raise PreflightInputError("staging directory identity changed before publication")
        try:
            os.stat(self.final_name, dir_fd=self.parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise PreflightInputError("output destination appeared before publication")
        os.rename(self.staging_name, self.final_name, src_dir_fd=self.parent_fd, dst_dir_fd=self.parent_fd)
        final_fd = os.open(self.final_name, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0), dir_fd=self.parent_fd)
        try:
            final = os.fstat(final_fd)
            if (final.st_dev, final.st_ino) != (self.device, self.inode):
                raise PreflightInputError("published output identity differs from validated staging")
        finally:
            os.close(final_fd)
        os.fsync(self.parent_fd)
        if not _descriptor_is_below(self.parent_fd, self.root.fd):
            raise PreflightInputError("published parent moved outside diagnostics")
        self.published = True


def validate_paths(source_path: Path, output_root: Path, workspace_root: Path) -> list[Diagnostic]:
    try:
        with DescriptorRoot(workspace_root) as root:
            source_parts = _relative_parts(source_path)
            output_parts = _relative_parts(output_root)
            if output_parts == source_parts[:-1]:
                raise PreflightInputError("output root cannot equal the source parent")
            root.read_source(source_path)
            parent_fd = root.open_directory(output_parts[:-1])
            try:
                try:
                    os.stat(output_parts[-1], dir_fd=parent_fd, follow_symlinks=False)
                except FileNotFoundError:
                    return []
                return [Diagnostic("PROMPT-PREFLIGHT-E012", "error", "The output root already exists; overwrite and resume are forbidden.", str(output_root), 0)]
            finally:
                os.close(parent_fd)
    except (OSError, PreflightInputError) as exc:
        return [Diagnostic("PROMPT-PREFLIGHT-E023", "error", f"Descriptor-rooted diagnostics path validation failed: {exc}.", str(source_path), 0)]


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


def _exact_keys(value: Any, expected: set[str], label: str, failures: list[str]) -> bool:
    if not isinstance(value, dict):
        failures.append(f"{label} is not an object")
        return False
    if set(value) != expected:
        failures.append(f"{label} keys differ: {sorted(set(value) ^ expected)}")
        return False
    return True


def _exact_int(value: Any) -> bool:
    return type(value) is int


def _decode_payloads(reader: Any, names: Iterable[str]) -> tuple[dict[str, bytes], dict[str, Any], list[str]]:
    raw: dict[str, bytes] = {}
    parsed: dict[str, Any] = {}
    failures: list[str] = []
    for name in names:
        try:
            raw[name] = reader(name)
            raw[name].decode("utf-8")
            if name in JSON_OUTPUTS:
                parsed[name] = json.loads(raw[name])
        except (OSError, UnicodeError, json.JSONDecodeError, PreflightInputError) as exc:
            failures.append(f"{name}: {exc}")
    return raw, parsed, failures


def validate_artifact_payloads(raw: dict[str, bytes], parsed: dict[str, Any], output_identity: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if set(raw) != set(OUTPUT_NAMES):
        failures.append("artifact inventory is not exactly the registered eight files")
        return failures
    state = parsed.get("preflight_state.json")
    state_keys = {
        "skill_version", "renderer_version", "ownership_contract_version", "schema_version",
        "prompt_id", "current_state", "states_visited", "source_representation",
        "source_sha256", "canonical_prompt_sha256", "agents_sha256", "cpc_sha256",
        "blocking_error_count", "warning_count", "diagnostics", "repairs",
        "prompt_contract_invoked", "prompt_contract_error_count",
        "task_execution_performed", "nested_codex_launched",
    }
    if not _exact_keys(state, state_keys, "preflight_state", failures):
        return failures
    assert isinstance(state, dict)
    for key in ("skill_version", "renderer_version", "ownership_contract_version", "schema_version", "prompt_id", "current_state", "source_representation"):
        if not isinstance(state[key], str):
            failures.append(f"state {key} type")
    for key, expected in (("skill_version", SKILL_VERSION), ("renderer_version", RENDERER_VERSION), ("ownership_contract_version", OWNERSHIP_CONTRACT_VERSION), ("schema_version", SCHEMA_VERSION)):
        if state[key] != expected:
            failures.append(f"state {key} version")
    for key in ("source_sha256", "canonical_prompt_sha256", "agents_sha256", "cpc_sha256"):
        if not isinstance(state[key], str) or not SHA256_RE.fullmatch(state[key]):
            failures.append(f"state {key} hash")
    for key in ("blocking_error_count", "warning_count", "prompt_contract_error_count"):
        if not _exact_int(state[key]) or state[key] < 0:
            failures.append(f"state {key} range/type")
    for key in ("prompt_contract_invoked", "task_execution_performed", "nested_codex_launched"):
        if type(state[key]) is not bool:
            failures.append(f"state {key} boolean type")
    registry_path = Path(__file__).resolve().parents[1] / "references/section_ownership.json"
    registry = load_json(registry_path)
    states = state["states_visited"]
    if not isinstance(states, list) or not states or any(not isinstance(item, str) or item not in registry["states"] for item in states):
        failures.append("state sequence values")
    else:
        for edge in zip(states, states[1:]):
            if list(edge) not in registry["allowed_transitions"]:
                failures.append(f"illegal state edge {edge}")
        if states[-1] != state["current_state"]:
            failures.append("current state does not end sequence")
    if state["current_state"] != "ready_for_same_session_execution" or state["blocking_error_count"] != 0:
        failures.append("package is not a zero-error ready package")
    diagnostics = state["diagnostics"]
    diagnostic_keys = {"id", "severity", "message", "section", "line"}
    if not isinstance(diagnostics, list):
        failures.append("diagnostics type")
    else:
        for index, item in enumerate(diagnostics):
            if not _exact_keys(item, diagnostic_keys, f"diagnostic {index}", failures):
                continue
            if item["id"] not in DIAGNOSTIC_IDS or item["severity"] not in {"error", "warning"}:
                failures.append(f"diagnostic {index} enum")
            if any(not isinstance(item[key], str) for key in ("id", "severity", "message", "section")) or not _exact_int(item["line"]) or item["line"] < 0:
                failures.append(f"diagnostic {index} type/range")
        if sum(item.get("severity") == "error" for item in diagnostics if isinstance(item, dict)) != state["blocking_error_count"]:
            failures.append("blocking diagnostic count")
    repairs = state["repairs"]
    if not isinstance(repairs, list) or any(not _exact_keys(item, {"field", "reason"}, f"repair {index}", failures) for index, item in enumerate(repairs)):
        failures.append("repairs structure")
    elif any(any(not isinstance(item[key], str) for key in ("field", "reason")) for item in repairs):
        failures.append("repair field types")
    if sha256_bytes(raw["authored_prompt.md"]) != state["source_sha256"]:
        failures.append("authored prompt hash")
    if sha256_bytes(raw["canonical_prompt.md"]) != state["canonical_prompt_sha256"]:
        failures.append("canonical prompt hash")

    section_manifest = parsed.get("section_manifest.json")
    section_top = {"prompt_id", "source_line_count", "source_section_count", "canonical_section_count", "records"}
    if _exact_keys(section_manifest, section_top, "section_manifest", failures):
        assert isinstance(section_manifest, dict)
        records = section_manifest["records"]
        if section_manifest["prompt_id"] != state["prompt_id"] or any(not _exact_int(section_manifest[key]) or section_manifest[key] < 0 for key in ("source_line_count", "source_section_count", "canonical_section_count")) or not isinstance(records, list):
            failures.append("section manifest summary")
        else:
            if section_manifest["source_section_count"] != len(records):
                failures.append("source section count")
            required = {"source_heading", "canonical_heading", "ownership", "source_start_line", "source_end_line", "source_sha256", "canonical_sha256", "preserved_exactly", "alias_applied", "authoritative_in_canonical"}
            for index, item in enumerate(records):
                if not _exact_keys(item, required, f"section {index}", failures):
                    continue
                if item["ownership"] not in {"author_owned", "skill_owned", "shared_structured"}:
                    failures.append(f"section {index} ownership")
                if any(not isinstance(item[key], str) for key in ("source_heading", "canonical_heading", "ownership", "source_sha256", "canonical_sha256")):
                    failures.append(f"section {index} string types")
                if type(item["preserved_exactly"]) is not bool or type(item["alias_applied"]) is not bool or type(item["authoritative_in_canonical"]) is not bool:
                    failures.append(f"section {index} booleans")
                if not _exact_int(item["source_start_line"]) or not _exact_int(item["source_end_line"]) or item["source_start_line"] < 1 or item["source_end_line"] < item["source_start_line"] or item["source_end_line"] > section_manifest["source_line_count"]:
                    failures.append(f"section {index} line range")
                for key in ("source_sha256", "canonical_sha256"):
                    if not isinstance(item[key], str) or (item[key] and not SHA256_RE.fullmatch(item[key])):
                        failures.append(f"section {index} {key}")
                if item["ownership"] == "author_owned" and (not item["preserved_exactly"] or item["source_sha256"] != item["canonical_sha256"]):
                    failures.append(f"section {index} author preservation")

    shared = parsed.get("shared_value_manifest.json")
    shared_top = {"prompt_id", "author_semantic_invention_count", "author_semantic_change_count", "records"}
    if _exact_keys(shared, shared_top, "shared_value_manifest", failures):
        assert isinstance(shared, dict)
        records = shared["records"]
        if shared["prompt_id"] != state["prompt_id"] or not _exact_int(shared["author_semantic_invention_count"]) or not _exact_int(shared["author_semantic_change_count"]) or not isinstance(records, list):
            failures.append("shared manifest summary")
        else:
            record_keys = {"source_path", "ownership_class", "source_value_sha256", "canonical_authoritative_location", "canonical_authoritative_value_sha256", "audit_only_source_location", "authoritative_location_count"}
            paths: set[str] = set()
            for index, item in enumerate(records):
                if not _exact_keys(item, record_keys, f"shared record {index}", failures):
                    continue
                if item["source_path"] in paths:
                    failures.append(f"duplicate shared semantic path {item['source_path']}")
                paths.add(item["source_path"])
                if item["ownership_class"] not in {"shared_structured", "skill_owned"} or item["authoritative_location_count"] != 1 or not _exact_int(item["authoritative_location_count"]):
                    failures.append(f"shared record {index} ownership/authority")
                if any(not isinstance(item[key], str) for key in ("source_path", "ownership_class", "source_value_sha256", "canonical_authoritative_location", "canonical_authoritative_value_sha256", "audit_only_source_location")):
                    failures.append(f"shared record {index} string types")
                for key in ("source_value_sha256", "canonical_authoritative_value_sha256"):
                    if not isinstance(item[key], str) or not SHA256_RE.fullmatch(item[key]):
                        failures.append(f"shared record {index} {key}")

    validation = parsed.get("prompt_contract_validation.json")
    validation_keys = {"context", "diagnostics", "error_count", "governance", "input", "schema_version", "valid_schema", "validator_version", "warning_count", "validator_input_sha256", "canonical_prompt_sha256", "validator_input_sha256_matches_canonical"}
    if _exact_keys(validation, validation_keys, "prompt_contract_validation", failures):
        assert isinstance(validation, dict)
        if type(validation["valid_schema"]) is not bool or type(validation["validator_input_sha256_matches_canonical"]) is not bool or not validation["valid_schema"] or not validation["validator_input_sha256_matches_canonical"]:
            failures.append("validator boolean status")
        if any(not _exact_int(validation[key]) or validation[key] < 0 for key in ("error_count", "warning_count")) or validation["error_count"] != 0:
            failures.append("validator counts")
        if validation["canonical_prompt_sha256"] != state["canonical_prompt_sha256"] or validation["validator_input_sha256"] != state["canonical_prompt_sha256"] or validation.get("input", {}).get("sha256") != state["canonical_prompt_sha256"]:
            failures.append("validator prompt hashes")
        governance = validation.get("governance")
        if not isinstance(governance, dict) or governance.get("agents_sha256") != state["agents_sha256"] or governance.get("cpc_sha256") != state["cpc_sha256"] or governance.get("binding_matches") is not True:
            failures.append("validator governance")
        external_diagnostics = validation.get("diagnostics")
        if not isinstance(external_diagnostics, list) or validation["warning_count"] != sum(item.get("severity") == "warning" for item in external_diagnostics if isinstance(item, dict)):
            failures.append("validator diagnostic counts")
        else:
            external_keys = {"category", "field", "governance_locator", "id", "line", "message", "severity", "suggestion"}
            for index, item in enumerate(external_diagnostics):
                if not _exact_keys(item, external_keys, f"validator diagnostic {index}", failures):
                    continue
                if any(not isinstance(item[key], str) for key in external_keys - {"line"}) or not _exact_int(item["line"]) or item["line"] < 0 or item["severity"] not in {"error", "warning", "info"}:
                    failures.append(f"validator diagnostic {index} types/enums")
        context = validation.get("context")
        if not _exact_keys(context, {"continuation", "evidence_round", "user_run_handoff"}, "validator context", failures) or any(context.get(key) not in CONTEXT_VALUES for key in ("continuation", "evidence_round", "user_run_handoff")):
            failures.append("validator context values")
        governance = validation.get("governance")
        if not _exact_keys(governance, {"agents_path", "agents_sha256", "binding_matches", "cpc_path", "cpc_sha256"}, "validator governance", failures):
            failures.append("validator governance keys")
        elif type(governance["binding_matches"]) is not bool or any(not isinstance(governance[key], str) for key in ("agents_path", "agents_sha256", "cpc_path", "cpc_sha256")):
            failures.append("validator governance types")
        validator_input = validation.get("input")
        if not _exact_keys(validator_input, {"path", "sha256"}, "validator input", failures) or not isinstance(validator_input.get("path"), str) or not isinstance(validator_input.get("sha256"), str):
            failures.append("validator input types")
        for key in ("schema_version", "validator_version", "validator_input_sha256", "canonical_prompt_sha256"):
            if not isinstance(validation[key], str):
                failures.append(f"validator {key} type")
        if state["warning_count"] != sum(item.get("severity") == "warning" for item in diagnostics if isinstance(item, dict)) + validation["warning_count"]:
            failures.append("combined warning count")

    report = raw["preflight_report.md"].decode("utf-8")
    for heading in ("# Prompt preflight report", "## Preflight result", "## Diagnostics", "## Governance hashes"):
        if heading not in report:
            failures.append(f"report missing {heading}")
    for digest in (state["source_sha256"], state["canonical_prompt_sha256"], state["agents_sha256"], state["cpc_sha256"]):
        if digest not in report:
            failures.append("report embedded hash")

    binding = parsed.get("readiness_binding.json")
    binding_keys = {"prompt_id", "authored_prompt_sha256", "canonical_prompt_sha256", "prompt_contract_input_sha256", "prompt_contract_validation_sha256", "section_manifest_sha256", "shared_value_manifest_sha256", "preflight_report_sha256", "preflight_state_sha256_without_self_field", "AGENTS_sha256", "CPC_sha256", "workspace_root", "diagnostics_root", "output_root_identity", "state_sequence", "current_state", "blocking_error_count", "warning_count", "created_by_skill_version", "created_by_renderer_version", "ownership_contract_version", "schema_version", "required_artifacts"}
    if _exact_keys(binding, binding_keys, "readiness_binding", failures):
        assert isinstance(binding, dict)
        string_fields = binding_keys - {"output_root_identity", "state_sequence", "blocking_error_count", "warning_count", "required_artifacts"}
        if any(not isinstance(binding[key], str) for key in string_fields):
            failures.append("binding string field types")
        for key in ("blocking_error_count", "warning_count"):
            if not _exact_int(binding[key]) or binding[key] < 0:
                failures.append(f"binding {key} type/range")
        if not isinstance(binding["state_sequence"], list) or any(not isinstance(item, str) for item in binding["state_sequence"]):
            failures.append("binding state sequence type")
        if not isinstance(binding["required_artifacts"], list) or any(not isinstance(item, str) for item in binding["required_artifacts"]):
            failures.append("binding artifact inventory type")
        identity_value = binding["output_root_identity"]
        if not _exact_keys(identity_value, {"relative_path", "device", "inode"}, "binding output identity", failures):
            failures.append("binding output identity keys")
        elif not isinstance(identity_value["relative_path"], str) or not _exact_int(identity_value["device"]) or not _exact_int(identity_value["inode"]) or identity_value["device"] < 0 or identity_value["inode"] <= 0:
            failures.append("binding output identity types/ranges")
        hash_fields = {key for key in binding if key.endswith("sha256") or key.endswith("sha256_without_self_field")}
        if any(not SHA256_RE.fullmatch(binding[key]) for key in hash_fields if isinstance(binding[key], str)):
            failures.append("binding hash syntax")
        expected_hashes = {
            "authored_prompt_sha256": sha256_bytes(raw["authored_prompt.md"]),
            "canonical_prompt_sha256": sha256_bytes(raw["canonical_prompt.md"]),
            "prompt_contract_input_sha256": sha256_bytes(raw["canonical_prompt.md"]),
            "prompt_contract_validation_sha256": sha256_bytes(raw["prompt_contract_validation.json"]),
            "section_manifest_sha256": sha256_bytes(raw["section_manifest.json"]),
            "shared_value_manifest_sha256": sha256_bytes(raw["shared_value_manifest.json"]),
            "preflight_report_sha256": sha256_bytes(raw["preflight_report.md"]),
            "preflight_state_sha256_without_self_field": sha256_bytes(raw["preflight_state.json"]),
        }
        for key, digest in expected_hashes.items():
            if binding[key] != digest:
                failures.append(f"binding {key}")
        if binding["prompt_id"] != state["prompt_id"] or binding["AGENTS_sha256"] != state["agents_sha256"] or binding["CPC_sha256"] != state["cpc_sha256"] or binding["state_sequence"] != state["states_visited"] or binding["current_state"] != state["current_state"] or binding["blocking_error_count"] != state["blocking_error_count"] or binding["warning_count"] != state["warning_count"]:
            failures.append("binding state/governance cross-reference")
        if binding["output_root_identity"] != output_identity:
            failures.append("binding output identity")
        if binding["required_artifacts"] != list(OUTPUT_NAMES):
            failures.append("binding required artifact inventory")
        for key, expected in (("created_by_skill_version", SKILL_VERSION), ("created_by_renderer_version", RENDERER_VERSION), ("ownership_contract_version", OWNERSHIP_CONTRACT_VERSION), ("schema_version", SCHEMA_VERSION)):
            if binding[key] != expected:
                failures.append(f"binding {key}")
    return failures


def validate_generated_artifacts(output_root: Path, state: dict[str, Any] | None = None, require_canonical: bool = True) -> list[Diagnostic]:
    del require_canonical
    try:
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0)
        directory_fd = os.open(output_root, flags)
        try:
            inventory = set(os.listdir(directory_fd))
            if inventory != set(OUTPUT_NAMES):
                failures = ["artifact inventory mismatch"]
                reopening: list[str] = []
                raw: dict[str, bytes] = {}
                parsed: dict[str, Any] = {}
            else:
                def reader(name: str) -> bytes:
                    fd = os.open(name, os.O_RDONLY | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0), dir_fd=directory_fd)
                    try:
                        if not stat.S_ISREG(os.fstat(fd).st_mode):
                            raise PreflightInputError("nonregular artifact")
                        return _read_fd_all(fd)
                    finally:
                        os.close(fd)
                raw, parsed, reopening = _decode_payloads(reader, OUTPUT_NAMES)
                info = os.fstat(directory_fd)
                identity = {"relative_path": str((state or {}).get("output_root", output_root)), "device": info.st_dev, "inode": info.st_ino}
                binding = parsed.get("readiness_binding.json")
                if isinstance(binding, dict) and isinstance(binding.get("output_root_identity"), dict):
                    identity["relative_path"] = binding["output_root_identity"].get("relative_path", identity["relative_path"])
                failures = validate_artifact_payloads(raw, parsed, identity) if not reopening else []
        finally:
            os.close(directory_fd)
    except (OSError, PreflightInputError) as exc:
        reopening = [str(exc)]
        failures = []
    if reopening:
        return [Diagnostic("PROMPT-PREFLIGHT-E013", "error", "Generated artifact reopening failed: " + "; ".join(reopening), str(output_root), 0)]
    return [] if not failures else [Diagnostic("PROMPT-PREFLIGHT-E019", "error", "Generated artifact schema validation failed: " + "; ".join(failures), str(output_root), 0)]


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json_text(value), encoding="utf-8")


def _blocked_without_output(diagnostic: Diagnostic) -> tuple[dict[str, Any], int]:
    return {"current_state": "blocked_semantic_ambiguity", "blocking_error_count": 1, "warning_count": 0, "diagnostics": [asdict(diagnostic)], "task_execution_performed": False, "nested_codex_launched": False}, 3


def _canonical_semantic_records(shared_records: list[dict[str, Any]], completed: dict[str, str], prompt_id: str, diagnostics: list[Diagnostic]) -> list[dict[str, Any]]:
    metadata = metadata_text(completed)
    fake = Section("Metadata and governance", "Metadata and governance", "skill_owned", 1, len(metadata.splitlines()) + 3, "## Metadata and governance\n\n```text\n" + metadata + "\n```\n", False)
    canonical_occurrences = parse_mapping_occurrences(fake, [])
    canonical_values = {".".join(item.semantic_path): item.value for item in canonical_occurrences}
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source in shared_records:
        path = source["semantic_path"]
        if path in seen:
            continue
        seen.add(path)
        canonical_value = canonical_values.get(path, "")
        ownership = "skill_owned" if source["field"] in FIXED_SKILL_FIELDS else "shared_structured"
        if ownership == "shared_structured" and canonical_value != source["source_value"]:
            diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E008", "error", f"Shared semantic value {path!r} changed during canonicalization.", source["source_section"], source["source_line"]))
        output.append({
            "source_path": path,
            "ownership_class": ownership,
            "source_value_sha256": sha256_text(source["source_value"]),
            "canonical_authoritative_location": f"canonical_prompt.md:Metadata and governance:{path}",
            "canonical_authoritative_value_sha256": sha256_text(canonical_value),
            "audit_only_source_location": f"authored_prompt.md:{source['source_section']}:{source['source_line']}",
            "authoritative_location_count": 1,
        })
    if len({item["source_path"] for item in output}) != len(output) or any(item["authoritative_location_count"] != 1 for item in output):
        diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E022", "error", "Canonical semantic authority is not unique.", "shared_value_manifest", 0))
    return output


def _binding_for(raw: dict[str, bytes], state: dict[str, Any], workspace_root: Path, output_relative: Path, stage: DescriptorStage) -> dict[str, Any]:
    return {
        "prompt_id": state["prompt_id"],
        "authored_prompt_sha256": sha256_bytes(raw["authored_prompt.md"]),
        "canonical_prompt_sha256": sha256_bytes(raw["canonical_prompt.md"]),
        "prompt_contract_input_sha256": sha256_bytes(raw["canonical_prompt.md"]),
        "prompt_contract_validation_sha256": sha256_bytes(raw["prompt_contract_validation.json"]),
        "section_manifest_sha256": sha256_bytes(raw["section_manifest.json"]),
        "shared_value_manifest_sha256": sha256_bytes(raw["shared_value_manifest.json"]),
        "preflight_report_sha256": sha256_bytes(raw["preflight_report.md"]),
        "preflight_state_sha256_without_self_field": sha256_bytes(raw["preflight_state.json"]),
        "AGENTS_sha256": state["agents_sha256"],
        "CPC_sha256": state["cpc_sha256"],
        "workspace_root": str(workspace_root),
        "diagnostics_root": str(workspace_root / "reports" / "diagnostics"),
        "output_root_identity": {"relative_path": str(output_relative), "device": stage.device, "inode": stage.inode},
        "state_sequence": state["states_visited"],
        "current_state": state["current_state"],
        "blocking_error_count": state["blocking_error_count"],
        "warning_count": state["warning_count"],
        "created_by_skill_version": SKILL_VERSION,
        "created_by_renderer_version": RENDERER_VERSION,
        "ownership_contract_version": OWNERSHIP_CONTRACT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "required_artifacts": list(OUTPUT_NAMES),
    }


def run_preflight(source_path: Path, output_root: Path, workspace_root: Path, contexts: dict[str, str]) -> tuple[dict[str, Any], int]:
    try:
        with DescriptorRoot(workspace_root) as diagnostics_root:
            source_bytes, _source_identity = diagnostics_root.read_source(source_path)
            try:
                source_text = source_bytes.decode("utf-8")
            except UnicodeError as exc:
                raise PreflightInputError(f"source capture is not UTF-8: {exc}") from exc
            try:
                stage = diagnostics_root.create_stage(output_root)
            except FileExistsError:
                return _blocked_without_output(Diagnostic("PROMPT-PREFLIGHT-E012", "error", "The output root already exists; overwrite and resume are forbidden.", str(output_root), 0))
            try:
                skill_root = Path(__file__).resolve().parents[1]
                registry = load_json(skill_root / "references/section_ownership.json")
                schema = load_json(skill_root / "references/preflight_schema.json")
                if registry.get("prompt_section_ownership_version") != OWNERSHIP_CONTRACT_VERSION or schema.get("schema_version") != SCHEMA_VERSION:
                    raise PreflightInputError("skill schema or ownership-contract version mismatch")
                stage.write("authored_prompt.md", source_bytes)
                states = ["not_triggered"]
                transition_state(states, "source_captured", registry)
                sections, diagnostics, preamble = parse_sections(source_text, registry)
                diagnostics.extend(transport_diagnostics(source_text))
                diagnostics.extend(binding_diagnostics(workspace_root, skill_root))
                fields, source_records = merge_semantic_fields(sections, diagnostics, registry)
                transition_state(states, "classified", registry)
                prompt_id = scalar(fields.get("prompt_id")) or "unresolved_prompt_id"
                live_state = live_repository_state(workspace_root)
                completed, repairs = complete_fields(fields, sections, prompt_id, workspace_root, live_state, contexts, diagnostics, source_records)
                agents_hash = sha256_bytes((workspace_root / "AGENTS.md").read_bytes())
                cpc_hash = sha256_bytes((workspace_root / "CPC.md").read_bytes())
                source_hash = sha256_bytes(source_bytes)
                blocking = [item for item in diagnostics if item.severity == "error"]
                if blocking:
                    transition_state(states, "blocked_semantic_ambiguity", registry)
                    state = {"skill_version": SKILL_VERSION, "renderer_version": RENDERER_VERSION, "ownership_contract_version": OWNERSHIP_CONTRACT_VERSION, "schema_version": SCHEMA_VERSION, "prompt_id": prompt_id, "current_state": states[-1], "states_visited": states, "source_representation": "normalized_visible_message_utf8", "source_sha256": source_hash, "canonical_prompt_sha256": "", "agents_sha256": agents_hash, "cpc_sha256": cpc_hash, "blocking_error_count": len(blocking), "warning_count": sum(item.severity == "warning" for item in diagnostics), "diagnostics": [asdict(item) for item in diagnostics], "repairs": repairs, "prompt_contract_invoked": False, "prompt_contract_error_count": 0, "task_execution_performed": False, "nested_codex_launched": False}
                    manifest = {"prompt_id": prompt_id, "source_line_count": len(source_text.splitlines()), "source_section_count": 1, "canonical_section_count": 0, "records": [{"source_heading": "<preamble>", "canonical_heading": "<preamble>", "ownership": "author_owned", "source_start_line": 1, "source_end_line": max(1, len(preamble.splitlines())), "source_sha256": sha256_text(preamble), "canonical_sha256": "", "preserved_exactly": False, "alias_applied": False, "authoritative_in_canonical": False}]}
                    stage.write("section_manifest.json", json_text(manifest).encode())
                    stage.write("shared_value_manifest.json", json_text({"prompt_id": prompt_id, "records": [], "author_semantic_invention_count": 0, "author_semantic_change_count": 0}).encode())
                    stage.write("prompt_contract_validation.json", json_text({"invoked": False, "error_count": 0, "warning_count": 0}).encode())
                    stage.write("preflight_state.json", json_text(state).encode())
                    stage.write("preflight_report.md", report_text(state, diagnostics).encode())
                    stage.publish()
                    return state, 3
                short_title = scalar(completed.get("short_title")) or "unresolved_short_title"
                canonical, manifest_records = canonicalize(prompt_id, short_title, completed, sections, workspace_root, live_state, diagnostics, preamble)
                semantic_records = _canonical_semantic_records(source_records, completed, prompt_id, diagnostics)
                if any(item.severity == "error" for item in diagnostics):
                    raise PreflightInputError("semantic authority validation failed after canonicalization")
                transition_state(states, "canonicalized", registry)
                canonical_bytes = canonical.encode("utf-8")
                stage.write("canonical_prompt.md", canonical_bytes)
                validation, validator_exit = invoke_prompt_contract(workspace_root, stage.proc_path("canonical_prompt.md"), contexts, (stage.fd,))
                canonical_hash = sha256_bytes(canonical_bytes)
                if validator_exit or validation.get("error_count", 0) or not validation.get("validator_input_sha256_matches_canonical"):
                    diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E010", "error", "The authoritative prompt-contract validator rejected the canonical prompt.", "Metadata and governance", 0))
                    transition_state(states, "blocked_prompt_contract", registry)
                    raise PreflightInputError("prompt-contract validation failed")
                transition_state(states, "prompt_contract_passed", registry)
                transition_state(states, "ready_for_same_session_execution", registry)
                state = {"skill_version": SKILL_VERSION, "renderer_version": RENDERER_VERSION, "ownership_contract_version": OWNERSHIP_CONTRACT_VERSION, "schema_version": SCHEMA_VERSION, "prompt_id": prompt_id, "current_state": states[-1], "states_visited": states, "source_representation": "normalized_visible_message_utf8", "source_sha256": source_hash, "canonical_prompt_sha256": canonical_hash, "agents_sha256": agents_hash, "cpc_sha256": cpc_hash, "blocking_error_count": 0, "warning_count": sum(item.severity == "warning" for item in diagnostics) + int(validation.get("warning_count", 0)), "diagnostics": [asdict(item) for item in diagnostics], "repairs": repairs, "prompt_contract_invoked": True, "prompt_contract_error_count": 0, "task_execution_performed": False, "nested_codex_launched": False}
                section_manifest = {"prompt_id": prompt_id, "source_line_count": len(source_text.splitlines()), "source_section_count": len(manifest_records), "canonical_section_count": len(re.findall(r"(?m)^##(?!#) ", canonical)), "records": manifest_records}
                shared_manifest = {"prompt_id": prompt_id, "records": semantic_records, "author_semantic_invention_count": 0, "author_semantic_change_count": 0}
                artifact_bytes = {
                    "authored_prompt.md": source_bytes,
                    "canonical_prompt.md": canonical_bytes,
                    "section_manifest.json": json_text(section_manifest).encode(),
                    "shared_value_manifest.json": json_text(shared_manifest).encode(),
                    "prompt_contract_validation.json": json_text(validation).encode(),
                    "preflight_state.json": json_text(state).encode(),
                    "preflight_report.md": report_text(state, diagnostics).encode(),
                }
                for name in ("section_manifest.json", "shared_value_manifest.json", "prompt_contract_validation.json", "preflight_state.json", "preflight_report.md"):
                    stage.write(name, artifact_bytes[name])
                binding = _binding_for(artifact_bytes, state, workspace_root, output_root, stage)
                artifact_bytes["readiness_binding.json"] = json_text(binding).encode()
                stage.write("readiness_binding.json", artifact_bytes["readiness_binding.json"])
                reopened, parsed, reopening = _decode_payloads(stage.read, OUTPUT_NAMES)
                identity = {"relative_path": str(output_root), "device": stage.device, "inode": stage.inode}
                schema_failures = reopening + validate_artifact_payloads(reopened, parsed, identity)
                if schema_failures:
                    raise PreflightInputError("generated artifact schema validation failed: " + "; ".join(schema_failures))
                stage.publish()
                return state, 0
            finally:
                stage.close()
    except (OSError, PreflightInputError) as exc:
        diagnostic = Diagnostic("PROMPT-PREFLIGHT-E023", "error", f"Descriptor-rooted preflight failed closed: {exc}.", str(output_root), 0)
        return _blocked_without_output(diagnostic)


def assert_ready_for_task_action(workspace_root: Path, output_root: Path | None = None, current_authored_source_sha256: str | None = None, expected_prompt_id: str | None = None) -> None:
    if output_root is None or current_authored_source_sha256 is None or expected_prompt_id is None:
        raise PreflightBlocked(Diagnostic("PROMPT-PREFLIGHT-E022", "error", "A standalone state file cannot authorize task action; the complete current readiness package is required.", "readiness_binding", 0))
    try:
        with DescriptorRoot(workspace_root) as root:
            directory_fd = root.open_output(output_root)
            try:
                inventory = set(os.listdir(directory_fd))
                if inventory != set(OUTPUT_NAMES):
                    raise PreflightInputError("readiness package inventory is incomplete or has extra files")
                def reader(name: str) -> bytes:
                    fd = os.open(name, os.O_RDONLY | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0), dir_fd=directory_fd)
                    try:
                        info = os.fstat(fd)
                        if not stat.S_ISREG(info.st_mode):
                            raise PreflightInputError(f"nonregular readiness artifact: {name}")
                        return _read_fd_all(fd)
                    finally:
                        os.close(fd)
                raw, parsed, reopening = _decode_payloads(reader, OUTPUT_NAMES)
                info = os.fstat(directory_fd)
                identity = {"relative_path": str(output_root), "device": info.st_dev, "inode": info.st_ino}
                failures = reopening + validate_artifact_payloads(raw, parsed, identity)
                binding = parsed.get("readiness_binding.json", {})
                if binding.get("prompt_id") != expected_prompt_id:
                    failures.append("foreign prompt id")
                if binding.get("authored_prompt_sha256") != current_authored_source_sha256:
                    failures.append("current authored source identity mismatch")
                agents_hash = sha256_bytes((workspace_root / "AGENTS.md").read_bytes())
                cpc_hash = sha256_bytes((workspace_root / "CPC.md").read_bytes())
                if binding.get("AGENTS_sha256") != agents_hash or binding.get("CPC_sha256") != cpc_hash:
                    failures.append("live governance changed after preflight")
                if binding.get("workspace_root") != str(workspace_root) or binding.get("diagnostics_root") != str(workspace_root / "reports" / "diagnostics"):
                    failures.append("workspace or diagnostics root mismatch")
                if failures:
                    raise PreflightInputError("; ".join(failures))
            finally:
                os.close(directory_fd)
    except (OSError, PreflightInputError) as exc:
        raise PreflightBlocked(Diagnostic("PROMPT-PREFLIGHT-E022", "error", f"Readiness package assertion failed: {exc}.", "readiness_binding", 0)) from exc


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
