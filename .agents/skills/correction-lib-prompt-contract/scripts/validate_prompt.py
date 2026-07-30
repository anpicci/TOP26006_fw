#!/usr/bin/env python3
"""Validate correction-lib Codex prompt metadata without executing the prompt."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


VALIDATOR_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"
CONTEXT_VALUES = ("yes", "no", "unknown")
PRIMARY_HEADING = "metadata and governance"
AUXILIARY_HEADINGS = {
    "accepted prior evidence": "accepted_prior_evidence",
    "evidence requirements": "evidence_requirements",
    "classification rules": "classification_rules",
    "anti-self-certification rules": "anti_self_certification_rules",
    "evidence validation method": "evidence_validation_method",
}
REMOTE_CAPABILITIES = (
    "remote_git_write",
    "pr_or_mr_write",
    "pr_or_mr_merge",
    "remote_branch_deletion",
)
PRODUCTION_CAPABILITIES = (
    "condor_submission",
    "work_queue_or_lobster_submission",
    "storage_writes",
    "large_pkl_production",
    "plot_campaign",
    "datacard_production",
    "correction_payload_generation",
    "payload_installation",
)
PLACEHOLDER_RE = re.compile(
    r"(?i)(?:<[^>]+>|\bTBD\b|\bTODO\b|author_must_|choose_(?:a_)?value)"
)
KEY_RE = re.compile(r"^(?P<indent> *)(?P<key>[A-Za-z_][A-Za-z0-9_]*):(?P<rest>.*)$")
UNSUPPORTED_RE = re.compile(
    r"(^|[\s:])(?:&[A-Za-z0-9_-]+|\*[A-Za-z0-9_-]+|![A-Za-z0-9_-]+|<<:)|\$\(|\{\{"
)


@dataclass(frozen=True)
class Diagnostic:
    id: str
    severity: str
    category: str
    field: str
    line: int
    message: str
    governance_locator: str
    suggestion: str


@dataclass
class FieldRecord:
    value: str
    raw: str
    line: int


class InputFailure(Exception):
    """A CLI/input failure that maps to exit code 2."""


class ValidatorDefect(Exception):
    """A schema/binding failure that maps to exit code 4."""


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def normalize_heading(line: str) -> str | None:
    match = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*$", line)
    if not match:
        return None
    return re.sub(r"[`*_]", "", match.group(1)).strip().lower()


def normalize_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def none_like(value: str) -> bool:
    value = normalize_scalar(value).strip().lower().replace("-", "_")
    return (
        not value
        or value == "none"
        or value.startswith("none,")
        or value.startswith("none ")
        or value.startswith("not_applicable")
        or value.startswith("inapplicable")
    )


def value_is_missing(record: FieldRecord | None) -> bool:
    if record is None:
        return True
    text = (record.value + "\n" + record.raw).strip()
    return not text or bool(PLACEHOLDER_RE.search(text))


def parse_mapping_block(
    block_lines: list[tuple[int, str]],
    diagnostics: list[Diagnostic],
) -> dict[str, FieldRecord]:
    fields: dict[str, FieldRecord] = {}
    index = 0
    while index < len(block_lines):
        line_number, line = block_lines[index]
        if "\t" in line:
            diagnostics.append(
                Diagnostic(
                    "PARSE003",
                    "error",
                    "parse_error",
                    "<mapping>",
                    line_number,
                    "Tabs are not supported in CPC mappings.",
                    "CPC.md section 2",
                    "Use space indentation and resubmit the decision text.",
                )
            )
            index += 1
            continue
        if UNSUPPORTED_RE.search(line):
            diagnostics.append(
                Diagnostic(
                    "PARSE003",
                    "error",
                    "parse_error",
                    "<mapping>",
                    line_number,
                    "The mapping contains an unsupported anchor, alias, tag, merge, or interpolation construct.",
                    "CPC.md section 2",
                    "Express the value with the restricted CPC mapping grammar.",
                )
            )
        if not line.strip() or line.lstrip().startswith("#"):
            index += 1
            continue
        match = KEY_RE.match(line)
        if not match or len(match.group("indent")) != 0:
            index += 1
            continue
        key = match.group("key")
        rest = match.group("rest").strip()
        start = index + 1
        end = start
        while end < len(block_lines):
            candidate = KEY_RE.match(block_lines[end][1])
            if candidate and len(candidate.group("indent")) == 0:
                break
            end += 1
        children = block_lines[start:end]
        child_text = "\n".join(child for _, child in children)
        if rest in ("|", ">"):
            value = "\n".join(child.lstrip() for _, child in children).strip()
        elif rest:
            value = normalize_scalar(rest)
        else:
            value = child_text.strip()
        raw = (rest + ("\n" + child_text if child_text else "")).strip()
        if key in fields:
            diagnostics.append(
                Diagnostic(
                    "PARSE002",
                    "error",
                    "parse_error",
                    key,
                    line_number,
                    "The structured field is defined more than once.",
                    "CPC.md section 4",
                    "Keep one explicit definition; do not infer which duplicate should win.",
                )
            )
        else:
            fields[key] = FieldRecord(value=value, raw=raw, line=line_number)
        index = end
    return fields


def extract_fields(text: str) -> tuple[dict[str, FieldRecord], list[Diagnostic]]:
    lines = text.splitlines()
    heading = ""
    blocks: list[tuple[str, str, int, list[tuple[int, str]]]] = []
    diagnostics: list[Diagnostic] = []
    index = 0
    while index < len(lines):
        new_heading = normalize_heading(lines[index])
        if new_heading is not None:
            heading = new_heading
        fence = re.match(r"^\s*```([A-Za-z0-9_-]*)\s*$", lines[index])
        if not fence:
            index += 1
            continue
        label = fence.group(1).lower()
        start_line = index + 2
        body: list[tuple[int, str]] = []
        index += 1
        while index < len(lines) and not re.match(r"^\s*```\s*$", lines[index]):
            body.append((index + 1, lines[index]))
            index += 1
        if index >= len(lines):
            diagnostics.append(
                Diagnostic(
                    "PARSE001",
                    "error",
                    "parse_error",
                    "<fence>",
                    start_line - 1,
                    "The structured fence is not closed.",
                    "CPC.md section 2",
                    "Close the fenced block before validation.",
                )
            )
            break
        if heading == PRIMARY_HEADING or heading in AUXILIARY_HEADINGS:
            if label not in ("", "text", "yaml"):
                diagnostics.append(
                    Diagnostic(
                        "PARSE001",
                        "error",
                        "parse_error",
                        "<fence>",
                        start_line - 1,
                        "The authoritative structured fence must be text, yaml, or unlabeled.",
                        "CPC.md section 2",
                        "Use a supported syntax label without changing field values.",
                    )
                )
            elif label == "":
                diagnostics.append(
                    Diagnostic(
                        "WARN005",
                        "warning",
                        "warning_only",
                        "<fence>",
                        start_line - 1,
                        "The structured fence is unlabeled.",
                        "CPC.md section 2",
                        "Label the fence text or yaml for clarity.",
                    )
                )
            blocks.append((heading, label, start_line, body))
        index += 1

    primary_blocks = [block for block in blocks if block[0] == PRIMARY_HEADING]
    if len(primary_blocks) != 1:
        diagnostics.append(
            Diagnostic(
                "PARSE001",
                "error",
                "parse_error",
                "<metadata>",
                0,
                "Exactly one authoritative Metadata and governance block is required.",
                "CPC.md sections 2 and 4",
                "Supply one fenced CPC mapping under that heading.",
            )
        )
    fields: dict[str, FieldRecord] = {}
    for block_heading, _label, _start, body in blocks:
        parsed = parse_mapping_block(body, diagnostics)
        allowed_auxiliary = AUXILIARY_HEADINGS.get(block_heading)
        if allowed_auxiliary is not None:
            parsed = {
                key: record for key, record in parsed.items() if key == allowed_auxiliary
            }
        for key, record in parsed.items():
            if key in fields:
                diagnostics.append(
                    Diagnostic(
                        "PARSE002",
                        "error",
                        "parse_error",
                        key,
                        record.line,
                        "The structured field is duplicated across recognized blocks.",
                        "CPC.md section 4",
                        "Keep one explicit definition in its recognized block.",
                    )
                )
            else:
                fields[key] = record
    return fields, diagnostics


class PromptValidator:
    def __init__(
        self,
        schema: dict[str, Any],
        contexts: dict[str, str],
        strict_unknown: bool,
    ) -> None:
        self.schema = schema
        self.contexts = contexts
        self.strict_unknown = strict_unknown
        self.diagnostics: list[Diagnostic] = []
        self.fields: dict[str, FieldRecord] = {}

    def add(
        self,
        diagnostic_id: str,
        category: str,
        field: str,
        message: str,
        locator: str,
        suggestion: str,
        *,
        line: int | None = None,
        severity: str = "error",
    ) -> None:
        if line is None:
            line = self.fields.get(field, FieldRecord("", "", 0)).line
        self.diagnostics.append(
            Diagnostic(
                diagnostic_id,
                severity,
                category,
                field,
                line,
                message,
                locator,
                suggestion,
            )
        )

    def scalar(self, field: str) -> str:
        record = self.fields.get(field)
        return normalize_scalar(record.value).strip() if record else ""

    def raw(self, field: str) -> str:
        record = self.fields.get(field)
        return record.raw if record else ""

    def permission_values(self, name: str) -> list[tuple[str, str]]:
        values: list[tuple[str, str]] = []
        if name in self.fields:
            values.append(("top_level", self.scalar(name).lower()))
        heavy = self.raw("heavy_command_permissions")
        direct = re.search(
            rf"(?m)^\s{{2,}}{re.escape(name)}:\s*(yes|no|unknown)\s*$", heavy
        )
        if direct:
            values.append(("heavy_command_permissions", direct.group(1)))
        nested = re.search(
            rf"(?ms)^\s{{2,}}{re.escape(name)}:\s*$"
            rf"(?P<body>(?:^\s{{4,}}.*$\n?)*)",
            heavy,
        )
        if nested:
            allowed = re.search(
                r"(?m)^\s+allowed:\s*(yes|no|unknown)\s*$", nested.group("body")
            )
            if allowed:
                values.append(("heavy_command_permissions", allowed.group(1)))
        return values

    def permission(self, name: str) -> str:
        values = self.permission_values(name)
        return values[0][1] if values else ""

    def require_group(
        self,
        names: list[str],
        diagnostic_id: str,
        category: str,
        locator: str,
    ) -> None:
        missing = [name for name in names if value_is_missing(self.fields.get(name))]
        if missing:
            self.add(
                diagnostic_id,
                category,
                ",".join(missing),
                "A conditional contract is incomplete; required decisions are missing.",
                locator,
                "Supply each named decision explicitly without inferring its value.",
            )

    def validate_common(self) -> None:
        for field in self.schema["common_required_fields"]:
            if value_is_missing(self.fields.get(field)):
                self.add(
                    "REQ001",
                    "missing_required_field",
                    field,
                    "A common prompt-contract field is missing or still a placeholder.",
                    "CPC.md section 4",
                    "Supply the governing decision explicitly.",
                )
        for field, vocabulary in self.schema["closed_vocabularies"].items():
            if field in self.fields and not value_is_missing(self.fields[field]):
                if self.scalar(field) not in vocabulary:
                    self.add(
                        "VOC001",
                        "invalid_closed_vocabulary",
                        field,
                        "The value is not in the live bound vocabulary.",
                        self.schema["governance_locators"]["closed_vocabularies"],
                        "Choose and supply one published value.",
                    )

    def validate_unknown_fields(self) -> None:
        known = set(self.schema["common_required_fields"])
        for values in self.schema["conditional_rules"].values():
            known.update(values)
        known.update(
            {
                "accepted_prior_evidence",
                "unresolved_checks_only",
                "checks_not_to_repeat",
                "commit_override_reason",
                "runtime_intent_evidence",
                "user_override_locator",
                "task_specific",
                "stop_conditions",
                "acceptance_logic",
                "checks_not_to_repeat",
                "configured_codex_model",
                "reported_codex_model",
            }
        )
        protected = known | set(REMOTE_CAPABILITIES) | {
            "network_access",
            "force_push_allowed",
            "merge_allowed",
            "draft_allowed",
            "execution_owner",
        }
        for field, record in self.fields.items():
            if field in known or field.startswith("x_"):
                continue
            close = difflib.get_close_matches(field, sorted(protected), n=1, cutoff=0.82)
            if close:
                self.add(
                    "WARN002",
                    "warning_only",
                    field,
                    "The unknown field closely resembles a protected contract field.",
                    "CPC.md sections 4 and 7",
                    "Check the field name; an unknown field never grants authorization.",
                    line=record.line,
                    severity="error",
                )
            else:
                self.add(
                    "WARN001",
                    "warning_only",
                    field,
                    "The top-level field is not in the derived schema.",
                    "CPC.md section 4",
                    "Keep task-specific data namespaced; this field grants no authorization.",
                    line=record.line,
                    severity="error" if self.strict_unknown else "warning",
                )

    def validate_branch(self) -> None:
        policy = self.scalar("branch_policy")
        target = self.scalar("target_branch")
        feature = self.scalar("feature_branch")
        reference = self.scalar("reference_branch")
        if policy == "create_feature_branch_from_reference":
            if none_like(reference) or none_like(feature):
                self.add(
                    "BRANCH001",
                    "branch_contract_inconsistency",
                    "reference_branch,feature_branch",
                    "Branch creation requires explicit reference and feature branches.",
                    "AGENTS.md section 7",
                    "Supply both branch decisions.",
                )
            if not none_like(target):
                self.add(
                    "BRANCH002",
                    "branch_contract_inconsistency",
                    "target_branch",
                    "A target branch conflicts with feature-branch creation.",
                    "AGENTS.md section 7",
                    "Resolve the branch policy/value conflict explicitly.",
                )
        elif policy in ("continue_existing_branch", "commit_preparation_on_existing_branch"):
            if none_like(target):
                self.add(
                    "BRANCH001",
                    "branch_contract_inconsistency",
                    "target_branch",
                    "This branch policy requires an explicit target branch.",
                    "AGENTS.md section 7",
                    "Supply the target branch.",
                )
            if not none_like(feature):
                self.add(
                    "BRANCH002",
                    "branch_contract_inconsistency",
                    "feature_branch",
                    "This branch policy forbids creating a feature branch.",
                    "AGENTS.md section 7",
                    "Resolve the branch policy/value conflict explicitly.",
                )
        elif policy == "read_only_current_branch":
            for field, value in (
                ("target_branch", target),
                ("feature_branch", feature),
                ("reference_branch", reference),
            ):
                if not none_like(value):
                    self.add(
                        "BRANCH002",
                        "branch_contract_inconsistency",
                        field,
                        "Read-only current-branch work forbids branch switching or creation values.",
                        "AGENTS.md section 7",
                        "Mark the field inapplicable or choose a different explicit policy.",
                    )

    def validate_commit(self) -> None:
        do_not = self.scalar("do_not_commit").lower()
        expected = self.scalar("commit_expected").lower()
        if do_not in ("yes", "no") and expected in ("yes", "no"):
            if do_not == expected:
                self.add(
                    "COMMIT001",
                    "commit_contract_inconsistency",
                    "do_not_commit,commit_expected",
                    "The commit flags are not logical opposites.",
                    "AGENTS.md section 14",
                    "Choose the commit contract explicitly.",
                )
        mode = self.scalar("prompt_mode")
        read_only_modes = {
            "investigation_only",
            "validation_only",
            "pr_preparation",
            "pr_publication",
        }
        if mode in read_only_modes and (do_not != "yes" or expected != "no"):
            self.add(
                "COMMIT002",
                "commit_contract_inconsistency",
                "do_not_commit,commit_expected",
                "The mode requires a no-commit contract.",
                "AGENTS.md sections 6 and 14",
                "Resolve the mode and commit decisions without inferring either.",
            )
        if mode in ("coding", "documentation_only"):
            if (do_not, expected) == ("yes", "no") and value_is_missing(
                self.fields.get("commit_override_reason")
            ):
                self.add(
                    "COMMIT002",
                    "commit_contract_inconsistency",
                    "commit_override_reason",
                    "A no-commit coding/documentation exception needs an explicit user override locator.",
                    "AGENTS.md section 14",
                    "Supply the override reason or choose a different commit contract.",
                )
        if mode == "commit_preparation":
            if (
                self.scalar("branch_policy") != "commit_preparation_on_existing_branch"
                or do_not != "no"
                or expected != "yes"
            ):
                self.add(
                    "COMMIT002",
                    "commit_contract_inconsistency",
                    "branch_policy,do_not_commit,commit_expected",
                    "Commit preparation requires its dedicated branch and commit contract.",
                    "AGENTS.md sections 7 and 14",
                    "Supply a consistent commit-preparation contract.",
                )

    def validate_mode(self) -> None:
        mode = self.scalar("prompt_mode")
        if mode in {
            "investigation_only",
            "validation_only",
            "pr_preparation",
            "pr_publication",
        }:
            writable = self.raw("allowed_to_modify").lower()
            if re.search(r"\b(?:source|tests?|configs?|agents\.md|cpc\.md)\b", writable):
                self.add(
                    "MODE050",
                    "forbidden_mode_specific_field",
                    "allowed_to_modify",
                    "A read-only mode names a tracked source, test, config, or governance surface as writable.",
                    "AGENTS.md section 6",
                    "Resolve the mode or writable-surface decision explicitly.",
                )
        if mode == "test_alignment_only" and value_is_missing(
            self.fields.get("runtime_intent_evidence")
        ) and value_is_missing(self.fields.get("accepted_prior_evidence")):
            self.add(
                "MODE001",
                "missing_mode_specific_field",
                "runtime_intent_evidence",
                "Test alignment requires explicit evidence that runtime intent is established.",
                "AGENTS.md section 6",
                "Supply the evidence reference without asserting its truth automatically.",
            )

    def validate_contexts(self) -> None:
        continuation = self.schema["conditional_rules"]["continuation_fields"]
        present = [name for name in continuation if name in self.fields]
        if present or self.contexts["continuation"] == "yes":
            self.require_group(
                continuation,
                "CONT001",
                "continuation_contract_inconsistency",
                "CPC.md sections 4 and 9",
            )
        if self.contexts["continuation"] == "unknown":
            self.add(
                "WARN003",
                "warning_only",
                "continuation_context",
                "Continuation context is unknown; completeness is not certified.",
                "CPC.md section 9",
                "Obtain an explicit yes, no, or unknown decision from the author.",
                severity="warning",
            )

        evidence = self.schema["conditional_rules"]["evidence_round_fields"]
        present = [name for name in evidence if name in self.fields]
        if present or self.contexts["evidence_round"] == "yes":
            self.require_group(
                evidence,
                "EVID001",
                "evidence_contract_inconsistency",
                "CPC.md sections 4 and 10",
            )
            if all(name in self.fields for name in evidence):
                joined = " ".join(self.raw(name).lower() for name in evidence)
                positions = [
                    joined.find("collect"),
                    joined.find("serializ"),
                    max(joined.find("reopen"), joined.find("validat")),
                    joined.find("classif"),
                    joined.find("verdict"),
                ]
                if any(position < 0 for position in positions) or positions != sorted(positions):
                    self.add(
                        "EVID001",
                        "evidence_contract_inconsistency",
                        "evidence_requirements",
                        "The evidence plan does not mechanically establish collect, serialize, validate, classify, then verdict order.",
                        "CPC.md section 10",
                        "Supply an explicit ordered evidence method.",
                    )
        if self.contexts["evidence_round"] == "unknown":
            self.add(
                "WARN003",
                "warning_only",
                "evidence_round_context",
                "Evidence-round context is unknown; completeness is not certified.",
                "CPC.md section 10",
                "Obtain an explicit yes, no, or unknown decision from the author.",
                severity="warning",
            )
        if self.contexts["user_run_handoff"] == "unknown":
            self.add(
                "WARN003",
                "warning_only",
                "user_run_handoff_context",
                "User-run-handoff context is unknown; ownership completeness is not certified.",
                "AGENTS.md section 18",
                "Obtain an explicit yes, no, or unknown decision from the author.",
                severity="warning",
            )

    def validate_authorization(self) -> None:
        network = self.permission("network_access")
        for capability in REMOTE_CAPABILITIES:
            values = self.permission_values(capability)
            if len({value for _, value in values}) > 1:
                self.add(
                    "XFLD001",
                    "cross_field_conflict",
                    capability,
                    "Top-level and heavy-command permission values conflict.",
                    "AGENTS.md sections 3 and 11",
                    "Resolve the duplicated permission decision explicitly.",
                )
            if self.permission(capability) == "yes" and network != "yes":
                self.add(
                    "AUTH002",
                    "authorization_inconsistency",
                    capability,
                    "A remote capability is enabled without explicit network authorization.",
                    "AGENTS.md sections 3 and 11",
                    "Supply or deny each independent authorization explicitly.",
                )
        for capability in PRODUCTION_CAPABILITIES:
            if (
                self.permission(capability) == "yes"
                and self.scalar("prompt_mode") != "production_execution"
                and value_is_missing(self.fields.get("user_override_locator"))
            ):
                self.add(
                    "AUTH001",
                    "authorization_inconsistency",
                    capability,
                    "A production capability is enabled outside production mode without an explicit override locator.",
                    "AGENTS.md sections 6 and 11",
                    "Resolve the mode or authorization explicitly.",
                )
        if (
            self.permission("remote_branch_deletion") == "yes"
            and self.scalar("publication_action") != "merge_existing_pr_or_mr"
        ):
            self.add(
                "AUTH003",
                "authorization_inconsistency",
                "remote_branch_deletion",
                "Remote deletion is enabled without a matching explicit merge action.",
                "AGENTS.md sections 3 and 11",
                "State the independent action and permission decisions explicitly.",
            )
        if (
            self.permission("force_push_allowed") == "yes"
            and value_is_missing(self.fields.get("user_override_locator"))
        ):
            self.add(
                "AUTH003",
                "authorization_inconsistency",
                "force_push_allowed",
                "Force push is enabled without an explicit user-override locator.",
                "AGENTS.md sections 3 and 11",
                "Supply the explicit override locator or deny the capability.",
            )

    def validate_publication(self) -> None:
        publication = self.schema["conditional_rules"]["publication_fields"]
        mode = self.scalar("prompt_mode")
        action = self.scalar("publication_action")
        if mode == "pr_publication":
            self.require_group(
                publication,
                "PUB001",
                "publication_contract_inconsistency",
                "CPC.md sections 4 and 12",
            )
            if action == "create_or_reuse_open_pr_or_mr":
                expected = {
                    "network_access": "yes",
                    "remote_git_write": "yes",
                    "pr_or_mr_write": "yes",
                    "pr_or_mr_merge": "no",
                    "remote_branch_deletion": "no",
                    "force_push_allowed": "no",
                    "merge_allowed": "no",
                    "draft_allowed": "no",
                    "duplicate_pr_or_mr_policy": "reuse_exact_open_match_else_create_one",
                }
                conflicts = [
                    field
                    for field, value in expected.items()
                    if self.scalar(field).lower() != value
                ]
                if conflicts:
                    self.add(
                        "PUB003",
                        "publication_contract_inconsistency",
                        ",".join(conflicts),
                        "The create/reuse action conflicts with required independent publication decisions.",
                        "CPC.md section 12",
                        "Resolve every named publication decision explicitly.",
                    )
            elif action == "merge_existing_pr_or_mr":
                self.require_group(
                    self.schema["conditional_rules"]["merge_fields"],
                    "PUB001",
                    "publication_contract_inconsistency",
                    "CPC.md section 12.4",
                )
                if (
                    self.scalar("pr_or_mr_merge").lower() != "yes"
                    or self.scalar("merge_allowed").lower() != "yes"
                    or self.scalar("remote_branch_deletion").lower()
                    not in ("yes", "no")
                    or self.scalar("merge_method") not in ("merge", "squash", "rebase")
                ):
                    self.add(
                        "PUB003",
                        "publication_contract_inconsistency",
                        "publication_action",
                        "The merge action lacks a complete, internally consistent merge authorization.",
                        "CPC.md section 12.4",
                        "Supply each merge and deletion decision independently.",
                    )
            elif action:
                self.add(
                    "PUB002",
                    "publication_contract_inconsistency",
                    "publication_action",
                    "The publication action is not supported by the bound contract.",
                    "CPC.md section 12",
                    "Choose and supply a published action.",
                )
        elif any(name in self.fields for name in publication if name != "network_access"):
            self.add(
                "MODE050",
                "forbidden_mode_specific_field",
                "publication_action",
                "Publication-specific fields appear outside pr_publication mode.",
                "CPC.md sections 4 and 12",
                "Resolve the mode or remove the inapplicable publication contract.",
            )

    def validate_production(self) -> None:
        production = self.schema["conditional_rules"]["production_fields"]
        handoff = self.schema["conditional_rules"]["user_handoff_fields"]
        mode = self.scalar("prompt_mode")
        handoff_context = self.contexts["user_run_handoff"]
        if mode == "production_execution" or handoff_context == "yes":
            self.require_group(
                production,
                "PROD001",
                "production_contract_inconsistency",
                "AGENTS.md section 18; CPC.md section 4",
            )
            policy = self.scalar("overwrite_or_resume_policy").lower()
            retry = self.scalar("interruption_retry_policy").lower()
            vague = ("", "as needed", "unspecified", "implicit", "default")
            if policy in vague:
                self.add(
                    "PROD003",
                    "production_contract_inconsistency",
                    "overwrite_or_resume_policy",
                    "Overwrite or resume behavior is missing or implicit.",
                    "AGENTS.md section 18",
                    "Supply an explicit bounded policy.",
                )
            if retry in vague:
                self.add(
                    "PROD001",
                    "production_contract_inconsistency",
                    "interruption_retry_policy",
                    "Interruption and retry behavior is missing or implicit.",
                    "AGENTS.md section 18",
                    "Supply an explicit bounded policy.",
                )
        if self.scalar("execution_owner").lower() == "user" or handoff_context == "yes":
            self.require_group(
                handoff,
                "PROD002",
                "production_contract_inconsistency",
                "AGENTS.md section 18",
            )

    def validate_cross_fields(self) -> None:
        if (
            not value_is_missing(self.fields.get("workspace_root"))
            and self.scalar("workspace_root")
            != "/users/apiccine/work/correction-lib"
            and value_is_missing(self.fields.get("user_override_locator"))
        ):
            self.add(
                "XFLD001",
                "cross_field_conflict",
                "workspace_root",
                "The workspace root differs from the correction-lib root without an override locator.",
                "AGENTS.md section 2",
                "Resolve the workspace decision explicitly.",
            )
        report = self.scalar("report_path")
        patch = self.scalar("patch_path")
        if (
            not value_is_missing(self.fields.get("report_path"))
            and not report.startswith("/")
        ):
            self.add(
                "XFLD001",
                "cross_field_conflict",
                "report_path",
                "The report path is not absolute.",
                "AGENTS.md section 20",
                "Supply the exact absolute artifact path.",
            )
        if (
            not value_is_missing(self.fields.get("patch_path"))
            and not patch.startswith("/")
        ):
            self.add(
                "XFLD001",
                "cross_field_conflict",
                "patch_path",
                "The patch path is not absolute.",
                "AGENTS.md section 20",
                "Supply the exact absolute artifact path.",
            )
        if (
            not value_is_missing(self.fields.get("report_path"))
            and not value_is_missing(self.fields.get("patch_path"))
            and report == patch
        ):
            self.add(
                "XFLD001",
                "cross_field_conflict",
                "report_path,patch_path",
                "Report and patch paths must be distinct.",
                "AGENTS.md section 20",
                "Supply distinct artifact paths.",
            )
        for field, record in self.fields.items():
            if "expected" in field.lower() and re.search(
                r"(?i)\b(pass(?:ed)?|success|ready|valid|zero failures?)\b",
                record.raw,
            ):
                if field not in {"commit_expected", "expected_local_head"}:
                    self.add(
                        "EVID001",
                        "evidence_contract_inconsistency",
                        field,
                        "A mechanically recognizable desired verdict is encoded as expected evidence.",
                        "CPC.md sections 8 and 10",
                        "Replace the desired conclusion with falsifiable acceptance logic.",
                        line=record.line,
                    )

    def run(self, fields: dict[str, FieldRecord]) -> list[Diagnostic]:
        self.fields = fields
        self.validate_common()
        self.validate_unknown_fields()
        self.validate_mode()
        self.validate_branch()
        self.validate_commit()
        self.validate_contexts()
        self.validate_authorization()
        self.validate_publication()
        self.validate_production()
        self.validate_cross_fields()
        return self.diagnostics


def load_json_resource(path: Path, kind: str) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValidatorDefect(f"Cannot load {kind}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValidatorDefect(f"{kind} must contain a JSON object")
    return data


def discover_workspace(start: Path) -> Path:
    start = start.resolve()
    for candidate in (start, *start.parents):
        if (candidate / "AGENTS.md").is_file() and (candidate / "CPC.md").is_file():
            return candidate
    raise InputFailure("No workspace root containing both AGENTS.md and CPC.md was found.")


def governance_evidence(
    workspace_root: Path,
    binding: dict[str, Any],
) -> tuple[dict[str, Any], list[Diagnostic]]:
    diagnostics: list[Diagnostic] = []
    required = {
        "binding_version",
        "schema_version",
        "agents_path",
        "agents_sha256",
        "cpc_path",
        "cpc_sha256",
    }
    if not required.issubset(binding) or binding.get("schema_version") != SCHEMA_VERSION:
        raise ValidatorDefect("governance binding is missing required versioned fields")
    agents_path = workspace_root / str(binding["agents_path"])
    cpc_path = workspace_root / str(binding["cpc_path"])
    try:
        agents_bytes = agents_path.read_bytes()
        cpc_bytes = cpc_path.read_bytes()
    except OSError as exc:
        raise ValidatorDefect(f"cannot read live governance: {exc}") from exc
    agents_sha = sha256_bytes(agents_bytes)
    cpc_sha = sha256_bytes(cpc_bytes)
    matches = (
        agents_sha == binding["agents_sha256"] and cpc_sha == binding["cpc_sha256"]
    )
    if not matches:
        diagnostics.append(
            Diagnostic(
                "GOV001",
                "error",
                "governance_version_mismatch",
                "governance_binding",
                0,
                "Live AGENTS.md or CPC.md bytes do not match the reviewed binding.",
                "AGENTS.md section 0; CPC.md section 0",
                "Stop and request a separately authorized schema/binding review.",
            )
        )
    return (
        {
            "agents_path": str(agents_path),
            "agents_sha256": agents_sha,
            "cpc_path": str(cpc_path),
            "cpc_sha256": cpc_sha,
            "binding_matches": matches,
        },
        diagnostics,
    )


def result_payload(
    prompt_label: str,
    prompt_bytes: bytes,
    schema: dict[str, Any],
    governance: dict[str, Any],
    contexts: dict[str, str],
    diagnostics: list[Diagnostic],
    defect: bool,
) -> dict[str, Any]:
    severity_rank = {"error": 0, "warning": 1, "info": 2}
    diagnostics = sorted(
        diagnostics,
        key=lambda item: (
            item.line if item.line > 0 else 10**9,
            severity_rank[item.severity],
            item.id,
            item.field,
        ),
    )
    error_count = sum(item.severity == "error" for item in diagnostics)
    warning_count = sum(item.severity == "warning" for item in diagnostics)
    valid = not defect and error_count == 0 and governance.get("binding_matches", False)
    if valid:
        diagnostics.append(
            Diagnostic(
                "OK000",
                "info",
                "valid_schema",
                "<summary>",
                0,
                "The prompt is mechanically schema-valid for the supplied contexts.",
                "AGENTS.md and CPC.md bound contract",
                "Treat schema validity separately from semantic or external-state review.",
            )
        )
    return {
        "validator_version": VALIDATOR_VERSION,
        "schema_version": schema.get("schema_version", "unknown"),
        "input": {"path": prompt_label, "sha256": sha256_bytes(prompt_bytes)},
        "governance": governance,
        "context": contexts,
        "valid_schema": valid,
        "diagnostics": [asdict(item) for item in diagnostics],
        "error_count": error_count,
        "warning_count": warning_count,
    }


def validate_content(
    prompt_label: str,
    prompt_bytes: bytes,
    workspace_root: Path,
    schema_path: Path,
    binding_path: Path,
    contexts: dict[str, str],
    strict_unknown: bool = False,
) -> tuple[dict[str, Any], int]:
    try:
        text = prompt_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InputFailure(f"Prompt is not valid UTF-8: {exc}") from exc
    schema = load_json_resource(schema_path, "prompt schema")
    if (
        schema.get("schema_version") != SCHEMA_VERSION
        or schema.get("validator_version") != VALIDATOR_VERSION
        or schema.get("projection_status")
        != "derived_reviewed_executable_projection_not_normative"
    ):
        raise ValidatorDefect("schema version or derived-projection marker is invalid")
    binding = load_json_resource(binding_path, "governance binding")
    governance, governance_diagnostics = governance_evidence(workspace_root, binding)
    fields, parse_diagnostics = extract_fields(text)
    validator = PromptValidator(schema, contexts, strict_unknown)
    validation_diagnostics = validator.run(fields)
    diagnostics = governance_diagnostics + parse_diagnostics + validation_diagnostics
    defect = bool(governance_diagnostics)
    payload = result_payload(
        prompt_label,
        prompt_bytes,
        schema,
        governance,
        contexts,
        diagnostics,
        defect,
    )
    if defect:
        return payload, 4
    if payload["error_count"]:
        return payload, 3
    return payload, 0


def human_output(payload: dict[str, Any]) -> str:
    lines = [
        f"prompt: {payload['input']['path']}",
        f"input_sha256: {payload['input']['sha256']}",
        f"validator_version: {payload['validator_version']}",
        f"schema_version: {payload['schema_version']}",
        "governance:",
        f"  agents_sha256: {payload['governance'].get('agents_sha256', 'unavailable')}",
        f"  cpc_sha256: {payload['governance'].get('cpc_sha256', 'unavailable')}",
        f"  binding_matches: {str(payload['governance'].get('binding_matches', False)).lower()}",
        "context:",
        f"  continuation: {payload['context']['continuation']}",
        f"  evidence_round: {payload['context']['evidence_round']}",
        f"  user_run_handoff: {payload['context']['user_run_handoff']}",
        "diagnostics:",
    ]
    for item in payload["diagnostics"]:
        location = f"line {item['line']}" if item["line"] else "global"
        lines.append(
            f"  {item['severity']} {item['id']} {item['field']} ({location}): "
            f"{item['message']} [{item['governance_locator']}]"
        )
        lines.append(f"    suggestion: {item['suggestion']}")
    lines.extend(
        [
            "summary:",
            f"  errors: {payload['error_count']}",
            f"  warnings: {payload['warning_count']}",
            f"  valid_schema: {str(payload['valid_schema']).lower()}",
        ]
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a correction-lib Codex prompt without executing it."
    )
    parser.add_argument("--workspace-root", type=Path)
    parser.add_argument("--schema", type=Path)
    parser.add_argument("--governance-binding", type=Path)
    parser.add_argument("--continuation", choices=CONTEXT_VALUES, default="unknown")
    parser.add_argument("--evidence-round", choices=CONTEXT_VALUES, default="unknown")
    parser.add_argument("--user-run-handoff", choices=CONTEXT_VALUES, default="unknown")
    parser.add_argument("--strict-unknown", action="store_true")
    parser.add_argument("--format", choices=("human", "json"), default="human")
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("prompt")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    script_root = Path(__file__).resolve().parents[1]
    schema_path = (args.schema or script_root / "references/prompt_schema.json").resolve()
    binding_path = (
        args.governance_binding
        or script_root / "references/governance_binding.json"
    ).resolve()
    try:
        workspace_root = (
            args.workspace_root.resolve()
            if args.workspace_root
            else discover_workspace(Path.cwd())
        )
        if args.prompt == "-":
            prompt_bytes = sys.stdin.buffer.read()
            prompt_label = "stdin"
        else:
            prompt_path = Path(args.prompt)
            prompt_bytes = prompt_path.read_bytes()
            prompt_label = str(prompt_path)
        contexts = {
            "continuation": args.continuation,
            "evidence_round": args.evidence_round,
            "user_run_handoff": args.user_run_handoff,
        }
        payload, exit_code = validate_content(
            prompt_label,
            prompt_bytes,
            workspace_root,
            schema_path,
            binding_path,
            contexts,
            args.strict_unknown,
        )
        json_text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        if args.json_out:
            args.json_out.write_text(json_text, encoding="utf-8")
        if args.format == "json":
            sys.stdout.write(json_text)
        else:
            sys.stdout.write(human_output(payload) + "\n")
        return exit_code
    except (OSError, InputFailure) as exc:
        print(f"input_error: {exc}", file=sys.stderr)
        return 2
    except ValidatorDefect as exc:
        diagnostic = Diagnostic(
            "GOV002",
            "error",
            "governance_version_mismatch",
            "schema_or_binding",
            0,
            str(exc),
            "AGENTS.md section 0; CPC.md section 0",
            "Stop and repair the reviewed derived resources in an authorized round.",
        )
        payload = result_payload(
            args.prompt,
            b"",
            {"schema_version": SCHEMA_VERSION},
            {"binding_matches": False},
            {
                "continuation": args.continuation,
                "evidence_round": args.evidence_round,
                "user_run_handoff": args.user_run_handoff,
            },
            [diagnostic],
            True,
        )
        if args.format == "json":
            sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        else:
            sys.stdout.write(human_output(payload) + "\n")
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
