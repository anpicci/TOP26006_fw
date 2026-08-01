#!/usr/bin/env python3
"""Canonicalize and validate a visible correction-lib Markdown prompt.

This module treats prompt text as inert UTF-8 data.  Its only subprocesses are
fixed, shell-false Git reads and the fixed installed prompt-contract validator.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


SKILL_VERSION = "1.0.0"
RENDERER_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"
OWNERSHIP_CONTRACT_VERSION = "1.0.0"
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
FIELD_ORDER = (
    "prompt_id",
    "short_title",
    "prompt_mode",
    "preferred_codex_model",
    "reasoning_level",
    "delegation_policy",
    "model_selection_rationale",
    "workspace_root",
    "repo_locations",
    "allowed_to_modify",
    "read_only",
    "branch_policy",
    "current_checked_out_branch",
    "reference_branch",
    "target_branch",
    "feature_branch",
    "current_baseline_branch",
    "comparison_baseline",
    "integrated_baseline_mode",
    "dirty_worktree_policy",
    "preflight_profile",
    "preflight_scope_paths",
    "validation_ceiling",
    "heavy_command_permissions",
    "source_control_policy",
    "do_not_commit",
    "commit_expected",
    "commit_message_policy",
    "goal",
    "decision_question",
    "out_of_scope",
    "report_path",
    "patch_path",
    "patch_kind_expected",
    "final_chat_deliverable",
    "accepted_prior_evidence",
    "unresolved_checks_only",
    "checks_not_to_repeat",
    "evidence_requirements",
    "classification_rules",
    "anti_self_certification_rules",
    "evidence_validation_method",
    "execution_owner",
    "overwrite_or_resume_policy",
    "interruption_retry_policy",
    "codex_post_run_interpretation",
)
AUTHOR_SEMANTIC_FIELDS = {
    "prompt_id",
    "short_title",
    "prompt_mode",
    "preferred_codex_model",
    "reasoning_level",
    "delegation_policy",
    "model_selection_rationale",
    "allowed_to_modify",
    "read_only",
    "branch_policy",
    "reference_branch",
    "target_branch",
    "feature_branch",
    "comparison_baseline",
    "integrated_baseline_mode",
    "dirty_worktree_policy",
    "preflight_profile",
    "preflight_scope_paths",
    "validation_ceiling",
    "heavy_command_permissions",
    "do_not_commit",
    "commit_expected",
    "commit_message_policy",
    "goal",
    "decision_question",
    "out_of_scope",
}
REPAIRABLE_FIELDS = {
    "workspace_root",
    "repo_locations",
    "current_checked_out_branch",
    "current_baseline_branch",
    "report_path",
    "patch_path",
    "patch_kind_expected",
    "source_control_policy",
    "final_chat_deliverable",
    "evidence_requirements",
    "classification_rules",
    "anti_self_certification_rules",
    "evidence_validation_method",
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

    @property
    def sha256(self) -> str:
        return sha256_text(self.raw)


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
            continue
        lookup[alias_key] = (lookup[canonical_key][0], lookup[canonical_key][1])
    return lookup, errors


def _line_without_ending(line: str) -> str:
    return line[:-2] if line.endswith("\r\n") else line[:-1] if line.endswith("\n") else line


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

    sections: list[Section] = []
    seen: dict[str, str] = {}
    permission_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in registry["permission_bearing_patterns"]]
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
            if any(pattern.search(heading + "\n" + raw) for pattern in permission_patterns):
                diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E004", "error", "An unknown section attempts to define permission-bearing semantics.", heading, start + 1))
            else:
                diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-W003", "warning", "An unknown safe section is preserved as author-owned.", heading, start + 1))
        sections.append(Section(heading, canonical, ownership, start + 1, end, raw, alias_applied))
    preamble_end = starts[0][0] if starts else len(lines)
    return sections, diagnostics, "".join(lines[:preamble_end])


def section_body(section: Section) -> str:
    lines = section.raw.splitlines(keepends=True)
    return "".join(lines[1:])


def mapping_payload(section: Section) -> str:
    body = section_body(section)
    lines = body.splitlines()
    inside = False
    fence = ""
    collected: list[str] = []
    found_fence = False
    for line in lines:
        if not inside:
            opening = re.match(r"^ {0,3}([`~]{3,})(?:text|yaml)?[ \t]*$", line, re.IGNORECASE)
            if opening:
                inside = True
                fence = opening.group(1)
                found_fence = True
            elif line.strip():
                collected.append(line)
        elif re.match(rf"^ {{0,3}}{re.escape(fence)}[ \t]*$", line):
            inside = False
        else:
            collected.append(line)
    return "\n".join(collected if found_fence else body.splitlines())


def parse_top_level_fields(mapping: str) -> dict[str, str]:
    lines = mapping.splitlines()
    starts: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):(?:.*)$", line)
        if match:
            starts.append((index, match.group(1)))
    fields: dict[str, str] = {}
    for position, (start, key) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        fields.setdefault(key, "\n".join(lines[start:end]).rstrip())
    return fields


def scalar(field_block: str | None) -> str:
    if not field_block:
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
        ["git", "-C", str(repository), *arguments],
        check=False,
        shell=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=15,
    )
    if completed.returncode:
        raise PreflightInputError(f"fixed Git read failed for {repository}: {completed.stderr.strip()}")
    return completed.stdout.strip()


def live_repository_state(workspace_root: Path) -> dict[str, dict[str, str]]:
    locations = {
        "meta_repo": workspace_root,
        "topeft": workspace_root / "topeft",
        "topcoffea": workspace_root / "topcoffea",
    }
    return {
        name: {
            "path": str(path),
            "branch": fixed_git_read(path, "branch", "--show-current"),
            "head": fixed_git_read(path, "rev-parse", "HEAD"),
        }
        for name, path in locations.items()
    }


def binding_diagnostics(workspace_root: Path, skill_root: Path) -> list[Diagnostic]:
    binding_path = skill_root / "references/governance_binding.json"
    if not binding_path.is_file():
        return [Diagnostic("PROMPT-PREFLIGHT-E011", "error", "The prompt-preflight governance binding is missing.", "Governance-binding evidence", 0)]
    binding = load_json(binding_path)
    agents_hash = sha256_bytes((workspace_root / "AGENTS.md").read_bytes())
    cpc_hash = sha256_bytes((workspace_root / "CPC.md").read_bytes())
    if binding.get("agents_sha256") != agents_hash or binding.get("cpc_sha256") != cpc_hash:
        return [Diagnostic("PROMPT-PREFLIGHT-E011", "error", "The prompt-preflight governance binding is stale.", "Governance-binding evidence", 0)]
    return []


def merge_semantic_fields(sections: list[Section]) -> tuple[dict[str, str], list[dict[str, Any]]]:
    fields: dict[str, str] = {}
    records: list[dict[str, Any]] = []
    for section in sections:
        if section.ownership != "shared_structured" and section.canonical_heading != "Metadata and governance":
            continue
        for key, block in parse_top_level_fields(mapping_payload(section)).items():
            record = {
                "field": key,
                "source_section": section.source_heading,
                "source_text": block,
                "source_sha256": sha256_text(block),
            }
            if key in fields and fields[key] != block:
                record["conflict"] = True
            else:
                fields.setdefault(key, block)
                record["conflict"] = False
            records.append(record)
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


def add_repair(diagnostics: list[Diagnostic], repairs: list[dict[str, str]], field: str, reason: str) -> None:
    repairs.append({"field": field, "reason": reason})
    diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-W002", "warning", f"Mechanical skill-owned repair applied: {reason}.", field, 0))


def complete_fields(
    fields: dict[str, str],
    sections: list[Section],
    prompt_id: str,
    workspace_root: Path,
    live_state: dict[str, dict[str, str]],
    contexts: dict[str, str],
    diagnostics: list[Diagnostic],
) -> tuple[dict[str, str], list[dict[str, str]]]:
    completed = dict(fields)
    repairs: list[dict[str, str]] = []
    if not scalar(completed.get("goal")):
        value = author_section_value(sections, "Goal")
        if value:
            completed["goal"] = field_block("goal", value)
    if not scalar(completed.get("decision_question")):
        value = author_section_value(sections, "Decision question")
        if value:
            completed["decision_question"] = field_block("decision_question", value)
    if "out_of_scope" not in completed:
        value = author_section_value(sections, "Out of scope")
        if value:
            completed["out_of_scope"] = field_block("out_of_scope", value)

    fixed = {
        "workspace_root": field_block("workspace_root", str(workspace_root)),
        "repo_locations": mapping_block("repo_locations", {name: item["path"] for name, item in live_state.items()}),
        "current_checked_out_branch": mapping_block("current_checked_out_branch", {name: item["branch"] for name, item in live_state.items()}),
        "current_baseline_branch": mapping_block("current_baseline_branch", {name: item["branch"] for name, item in live_state.items()}),
        "source_control_policy": "source_control_policy:\n  - inherit live AGENTS defaults\n  - stage exact authorized paths only\n  - no remote mutation without explicit authority",
        "report_path": field_block("report_path", str(workspace_root / "reports/diagnostics" / prompt_id / f"{prompt_id}_report.md")),
        "patch_path": field_block("patch_path", str(workspace_root / "reports/diagnostics" / prompt_id / f"{prompt_id}_worktree_diff.patch")),
        "final_chat_deliverable": "final_chat_deliverable:\n  final_status, decision_question, branch and HEAD, files changed, validation results, report path, patch path, commit hash, caveats, recommended next action, and final cleanliness",
    }
    for name, block in fixed.items():
        if name not in completed or not scalar(completed.get(name)):
            completed[name] = block
            add_repair(diagnostics, repairs, name, f"generated missing {name}")

    valid_patch_kinds = {"prompt_local", "cumulative", "touched_file_cumulative", "empty_no_changes"}
    if scalar(completed.get("patch_kind_expected")) not in valid_patch_kinds:
        completed["patch_kind_expected"] = "patch_kind_expected: prompt_local"
        add_repair(diagnostics, repairs, "patch_kind_expected", "used prompt-contract vocabulary prompt_local")

    branch_policy = completed.get("branch_policy")
    if branch_policy and not child_scalars(branch_policy):
        value = scalar(branch_policy)
        if value:
            completed["branch_policy"] = mapping_block("branch_policy", {name: value for name in live_state})
            add_repair(diagnostics, repairs, "branch_policy", "expanded scalar branch policy into the repository triplet")
    policies = child_scalars(completed.get("branch_policy"))
    for field in ("reference_branch", "target_branch", "feature_branch"):
        values = child_scalars(completed.get(field))
        if not values and policies:
            generated: dict[str, str] = {}
            blocked = False
            for repository, policy in policies.items():
                if field == "target_branch" and policy in {"continue_existing_branch", "commit_preparation_on_existing_branch"}:
                    diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E005", "error", f"{field}.{repository} is an author decision and is missing.", field, 0))
                    blocked = True
                elif field == "feature_branch" and policy == "create_feature_branch_from_reference":
                    diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E005", "error", f"{field}.{repository} is an author decision and is missing.", field, 0))
                    blocked = True
                elif field == "reference_branch" and policy == "create_feature_branch_from_reference":
                    diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E005", "error", f"{field}.{repository} is an author decision and is missing.", field, 0))
                    blocked = True
                else:
                    generated[repository] = "none"
            if not blocked:
                completed[field] = mapping_block(field, generated)
                add_repair(diagnostics, repairs, field, f"completed inapplicable {field} repository triplet")

    evidence_block = "evidence_requirements:\n  ordered_method:\n" + "\n".join(f"    - {phase}" for phase in EVIDENCE_SEQUENCE)
    evidence_fixed = {
        "evidence_requirements": evidence_block,
        "classification_rules": "classification_rules:\n  - classify only after reopening serialized evidence",
        "anti_self_certification_rules": "anti_self_certification_rules:\n  - do not copy expected values into observed evidence",
        "evidence_validation_method": field_block("evidence_validation_method", EVIDENCE_COMPACT),
    }
    if contexts["evidence_round"] == "yes":
        for name, block in evidence_fixed.items():
            if name not in completed or (name == "evidence_validation_method" and scalar(completed.get(name)) != EVIDENCE_COMPACT):
                completed[name] = block
                add_repair(diagnostics, repairs, name, f"generated canonical {name}")

    required = (
        "prompt_id", "short_title", "prompt_mode", "preferred_codex_model",
        "reasoning_level", "delegation_policy", "model_selection_rationale",
        "allowed_to_modify", "read_only", "branch_policy", "comparison_baseline",
        "integrated_baseline_mode", "dirty_worktree_policy", "preflight_profile",
        "preflight_scope_paths", "validation_ceiling", "heavy_command_permissions",
        "do_not_commit", "commit_expected", "commit_message_policy", "goal",
        "decision_question", "out_of_scope",
    )
    for name in required:
        if name not in completed or not scalar(completed.get(name)):
            diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E005", "error", f"Required shared semantic decision {name!r} is missing.", name, 0))
    if scalar(completed.get("do_not_commit")) == scalar(completed.get("commit_expected")) and scalar(completed.get("do_not_commit")) in {"yes", "no"}:
        diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E009", "error", "do_not_commit and commit_expected must be logical opposites.", "Commit policy", 0))

    for repository, declared in child_scalars(completed.get("current_checked_out_branch")).items():
        if repository in live_state and declared != live_state[repository]["branch"]:
            diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E006", "error", f"Declared branch {declared!r} does not match the live read-only branch.", repository, 0))
    return completed, repairs


def generated_skill_sections(
    prompt_id: str,
    workspace_root: Path,
    live_state: dict[str, dict[str, str]],
) -> dict[str, str]:
    agents_sha = sha256_bytes((workspace_root / "AGENTS.md").read_bytes())
    cpc_sha = sha256_bytes((workspace_root / "CPC.md").read_bytes())
    return {
        "Prompt preflight result": "## Prompt preflight result\n\nCanonicalization completed; execution remains gated on the retained prompt-contract result.\n",
        "Repository envelope": "## Repository envelope\n\n" + "\n".join(f"- `{name}`: `{item['branch']}` at `{item['head']}`" for name, item in live_state.items()) + "\n",
        "Standard execution boundaries": "## Standard execution boundaries\n\nNo task-specific action is authorized before `ready_for_same_session_execution`.\n",
        "Evidence-order contract": "## Evidence-order contract\n\n" + "\n".join(f"{index}. `{phase}`" for index, phase in enumerate(EVIDENCE_SEQUENCE, 1)) + f"\n\n`{EVIDENCE_COMPACT}`\n",
        "Source-control policy": "## Source-control policy\n\nFollow live `AGENTS.md`; stage exact authorized paths only and perform no remote mutation without explicit authority.\n",
        "Diagnostics and publication paths": f"## Diagnostics and publication paths\n\nDiagnostics derive deterministically from `{prompt_id}`. Publication authority is never inferred.\n",
        "Standard report sections": "## Standard report sections\n\nReport the decision, evidence, validation, files, patch, commit, caveats, next action, and final cleanliness required by live governance.\n",
        "Standard final-response fields": "## Standard final-response fields\n\nReturn final status, decision question, branch and HEAD, validation, files changed, commit, artifact paths, caveats, next action, and cleanliness.\n",
        "Governance-binding evidence": f"## Governance-binding evidence\n\n- `AGENTS.md`: `{agents_sha}`\n- `CPC.md`: `{cpc_sha}`\n",
    }


def canonicalize(
    prompt_id: str,
    short_title: str,
    fields: dict[str, str],
    sections: list[Section],
    workspace_root: Path,
    live_state: dict[str, dict[str, str]],
    diagnostics: list[Diagnostic],
) -> tuple[str, list[dict[str, Any]]]:
    metadata = "\n\n".join(fields[name] for name in FIELD_ORDER if name in fields)
    skill_sections = generated_skill_sections(prompt_id, workspace_root, live_state)
    generated_parts = [f"# Prompt `{prompt_id}` — `{short_title}`\n\n## Metadata and governance\n\n```text\n{metadata}\n```\n"]
    generated_parts.extend("\n" + skill_sections[name] for name in skill_sections)
    preserved = [section.raw for section in sections if section.ownership != "skill_owned"]
    canonical = "".join(generated_parts) + "\n" + "".join(preserved)
    if not canonical.endswith("\n"):
        canonical += "\n"

    generated_hashes = {"Metadata and governance": sha256_text(f"## Metadata and governance\n\n```text\n{metadata}\n```\n")}
    generated_hashes.update({name: sha256_text(raw) for name, raw in skill_sections.items()})
    manifest: list[dict[str, Any]] = []
    for section in sections:
        authoritative = section.ownership != "skill_owned"
        if authoritative:
            count = canonical.count(section.raw)
            canonical_hash = section.sha256 if count == 1 else ""
            preserved_exactly = count == 1 and canonical_hash == section.sha256
        else:
            canonical_hash = generated_hashes.get(section.canonical_heading, "")
            preserved_exactly = False
            diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-W001", "warning", "Authored skill-owned content was replaced in the canonical prompt.", section.source_heading, section.start_line))
        manifest.append({
            "source_heading": section.source_heading,
            "canonical_heading": section.canonical_heading,
            "ownership": section.ownership,
            "source_start_line": section.start_line,
            "source_end_line": section.end_line,
            "source_sha256": section.sha256,
            "canonical_sha256": canonical_hash,
            "preserved_exactly": preserved_exactly,
            "alias_applied": section.alias_applied,
            "authoritative_in_canonical": authoritative,
        })
        if section.ownership == "author_owned" and not preserved_exactly:
            diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E007", "error", "Author-owned section bytes changed or became ambiguous in the canonical prompt.", section.source_heading, section.start_line))
        if section.ownership == "shared_structured" and not preserved_exactly:
            diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E008", "error", "Shared-structured source bytes changed or became ambiguous in the canonical prompt.", section.source_heading, section.start_line))
    return canonical, manifest


def transport_diagnostics(text: str) -> list[Diagnostic]:
    lowered = text.casefold()
    if "transport" not in lowered or "byte" not in lowered:
        return []
    safe = all(phrase in lowered for phrase in ("unavailable", "not required", "not claimed"))
    claim = bool(re.search(r"(?:require|must|exact|identical|reproduce).{0,80}(?:transport|hidden).{0,40}bytes|(?:transport|hidden).{0,40}bytes.{0,80}(?:exact|identical|reproduce)", lowered, re.DOTALL))
    return [] if safe or not claim else [Diagnostic("PROMPT-PREFLIGHT-E015", "error", "The prompt requires or claims inaccessible transport-byte identity.", "<prompt>", 0)]


def invoke_prompt_contract(
    workspace_root: Path,
    canonical_path: Path,
    contexts: dict[str, str],
) -> tuple[dict[str, Any], int]:
    validator = workspace_root / ".agents/skills/correction-lib-prompt-contract/scripts/validate_prompt.py"
    argv = [
        sys.executable,
        str(validator),
        "--workspace-root", str(workspace_root),
        "--continuation", contexts["continuation"],
        "--evidence-round", contexts["evidence_round"],
        "--user-run-handoff", contexts["user_run_handoff"],
        "--format", "json",
        str(canonical_path),
    ]
    completed = subprocess.run(
        argv,
        check=False,
        shell=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=60,
        cwd=workspace_root,
    )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        payload = {
            "valid_schema": False,
            "error_count": 1,
            "warning_count": 0,
            "diagnostics": [],
            "stderr": completed.stderr,
        }
    payload["invoked"] = True
    payload["subprocess_returncode"] = completed.returncode
    payload["canonical_sha256_recomputed"] = sha256_bytes(canonical_path.read_bytes())
    payload["validator_input_sha256_matches_canonical"] = payload.get("input", {}).get("sha256") == payload["canonical_sha256_recomputed"]
    return payload, completed.returncode


def report_text(state: dict[str, Any], diagnostics: list[Diagnostic]) -> str:
    lines = [
        "# Prompt preflight report",
        "",
        f"- final_state: `{state['current_state']}`",
        f"- blocking_error_count: `{state['blocking_error_count']}`",
        f"- warning_count: `{state['warning_count']}`",
        f"- canonical_prompt_sha256: `{state.get('canonical_prompt_sha256', 'unavailable')}`",
        f"- prompt_contract_invoked: `{str(state.get('prompt_contract_invoked', False)).lower()}`",
        "",
        "## Repairs",
        "",
    ]
    if state["repairs"]:
        lines.extend(f"- `{item['field']}`: {item['reason']}" for item in state["repairs"])
    else:
        lines.append("- none")
    lines.extend(["", "## Diagnostics", ""])
    if diagnostics:
        lines.extend(f"- {item.severity} `{item.id}` {item.section} (line {item.line or 'global'}): {item.message}" for item in diagnostics)
    else:
        lines.append("- none")
    lines.extend(["", "## Execution boundary", "", "The renderer did not execute the task or launch Codex. Same-session task action is allowed only from `ready_for_same_session_execution`.", ""])
    return "\n".join(lines)


def assert_ready_for_task_action(state_path: Path) -> None:
    state = load_json(state_path)
    if state.get("current_state") != "ready_for_same_session_execution" or state.get("blocking_error_count") != 0:
        raise PreflightBlocked(Diagnostic("PROMPT-PREFLIGHT-E014", "error", "Task action was attempted before preflight passed.", "preflight_state", 0))


def run_preflight(
    source_path: Path,
    output_root: Path,
    workspace_root: Path,
    contexts: dict[str, str],
) -> tuple[dict[str, Any], int]:
    if output_root.exists():
        diagnostic = Diagnostic("PROMPT-PREFLIGHT-E012", "error", "The output root already exists; overwrite and resume are forbidden.", str(output_root), 0)
        return {"current_state": "blocked_semantic_ambiguity", "blocking_error_count": 1, "diagnostics": [asdict(diagnostic)]}, 3
    try:
        source_bytes = source_path.read_bytes()
        source_text = source_bytes.decode("utf-8")
    except (OSError, UnicodeError) as exc:
        raise PreflightInputError(f"cannot read UTF-8 prompt source: {exc}") from exc

    skill_root = Path(__file__).resolve().parents[1]
    registry = load_json(skill_root / "references/section_ownership.json")
    schema = load_json(skill_root / "references/preflight_schema.json")
    if registry.get("prompt_section_ownership_version") != OWNERSHIP_CONTRACT_VERSION or schema.get("schema_version") != SCHEMA_VERSION:
        raise PreflightInputError("skill schema or ownership-contract version mismatch")

    output_root.mkdir(parents=True, exist_ok=False)
    (output_root / "authored_prompt.md").write_bytes(source_bytes)
    states = ["not_triggered", "source_captured"]
    sections, diagnostics, _preamble = parse_sections(source_text, registry)
    diagnostics.extend(transport_diagnostics(source_text))
    diagnostics.extend(binding_diagnostics(workspace_root, skill_root))
    states.append("classified")
    fields, shared_records = merge_semantic_fields(sections)
    prompt_id = scalar(fields.get("prompt_id"))
    if not prompt_id:
        diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E001", "error", "The trigger matched but prompt_id is missing.", "Task metadata or Metadata and governance", 0))
        prompt_id = "unresolved_prompt_id"
    live_state = live_repository_state(workspace_root)
    fields, repairs = complete_fields(fields, sections, prompt_id, workspace_root, live_state, contexts, diagnostics)
    short_title = scalar(fields.get("short_title")) or "unresolved_short_title"
    canonical, section_manifest = canonicalize(prompt_id, short_title, fields, sections, workspace_root, live_state, diagnostics)
    states.append("canonicalized")
    canonical_path = output_root / "canonical_prompt.md"
    canonical_path.write_text(canonical, encoding="utf-8")

    for record in shared_records:
        generated = fields.get(record["field"], "")
        record["canonical_text"] = generated
        record["canonical_sha256"] = sha256_text(generated) if generated else ""
        record["semantic_value_preserved"] = record["source_text"] == generated
        record["mechanical_repair"] = record["field"] in REPAIRABLE_FIELDS and record["source_text"] != generated
        if record["field"] in AUTHOR_SEMANTIC_FIELDS and not record["semantic_value_preserved"]:
            diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E008", "error", "An author-supplied shared semantic value changed.", record["field"], 0))
        if record.get("conflict") and record["field"] in AUTHOR_SEMANTIC_FIELDS:
            diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E006", "error", "Conflicting shared branch, baseline, or task values were supplied.", record["field"], 0))

    blocking = [item for item in diagnostics if item.severity == "error"]
    validation: dict[str, Any]
    if blocking:
        states.append("blocked_semantic_ambiguity")
        validation = {
            "invoked": False,
            "valid_schema": False,
            "error_count": 0,
            "warning_count": 0,
            "reason": "semantic ambiguity blocked validator invocation",
            "canonical_sha256_recomputed": sha256_bytes(canonical_path.read_bytes()),
        }
        exit_code = 3
    else:
        validation, validator_returncode = invoke_prompt_contract(workspace_root, canonical_path, contexts)
        if validator_returncode or validation.get("error_count") or not validation.get("validator_input_sha256_matches_canonical"):
            diagnostics.append(Diagnostic("PROMPT-PREFLIGHT-E010", "error", "The installed prompt-contract validator rejected the canonical prompt or its input hash did not match.", "Metadata and governance", 0))
            states.append("blocked_prompt_contract")
            exit_code = 3
        else:
            states.extend(["prompt_contract_passed", "ready_for_same_session_execution"])
            exit_code = 0

    diagnostics = sorted(diagnostics, key=lambda item: (item.line if item.line else 10**9, item.id, item.section, item.message))
    state = {
        "skill_version": SKILL_VERSION,
        "renderer_version": RENDERER_VERSION,
        "schema_version": SCHEMA_VERSION,
        "ownership_contract_version": OWNERSHIP_CONTRACT_VERSION,
        "transport_byte_identity_claimed": False,
        "source_representation": "normalized_visible_message_utf8",
        "states_visited": states,
        "current_state": states[-1],
        "allowed_execution_transition": ["prompt_contract_passed", "ready_for_same_session_execution", "execution_started"],
        "blocking_error_count": sum(item.severity == "error" for item in diagnostics),
        "warning_count": sum(item.severity == "warning" for item in diagnostics),
        "repairs": repairs,
        "diagnostics": [asdict(item) for item in diagnostics],
        "source_sha256": sha256_bytes(source_bytes),
        "canonical_prompt_sha256": sha256_bytes(canonical_path.read_bytes()),
        "prompt_contract_invoked": validation.get("invoked", False),
        "task_execution_performed": False,
        "nested_codex_launched": False,
    }
    artifacts = {
        "section_manifest.json": section_manifest,
        "shared_value_manifest.json": {
            "records": shared_records,
            "author_semantic_invention_count": 0,
            "author_semantic_change_count": sum(record["field"] in AUTHOR_SEMANTIC_FIELDS and not record["semantic_value_preserved"] for record in shared_records),
        },
        "prompt_contract_validation.json": validation,
        "preflight_state.json": state,
    }
    for name, value in artifacts.items():
        (output_root / name).write_text(json_text(value), encoding="utf-8")
    (output_root / "preflight_report.md").write_text(report_text(state, diagnostics), encoding="utf-8")

    try:
        for name in OUTPUT_NAMES:
            path = output_root / name
            if name.endswith(".json"):
                json.loads(path.read_text(encoding="utf-8"))
            else:
                path.read_text(encoding="utf-8")
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        diagnostic = Diagnostic("PROMPT-PREFLIGHT-E013", "error", f"Generated artifact reopening failed: {exc}", str(output_root), 0)
        state["diagnostics"].append(asdict(diagnostic))
        state["blocking_error_count"] += 1
        state["current_state"] = "blocked_prompt_contract"
        (output_root / "preflight_state.json").write_text(json_text(state), encoding="utf-8")
        return state, 3
    return state, exit_code


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
    contexts = {
        "continuation": args.continuation,
        "evidence_round": args.evidence_round,
        "user_run_handoff": args.user_run_handoff,
    }
    try:
        state, exit_code = run_preflight(
            args.source_prompt.resolve(),
            args.output_root.resolve(),
            args.workspace_root.resolve(),
            contexts,
        )
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
