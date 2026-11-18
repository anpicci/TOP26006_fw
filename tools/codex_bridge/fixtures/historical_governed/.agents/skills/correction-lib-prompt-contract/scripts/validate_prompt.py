#!/usr/bin/env python3
"""Mechanically lint a bounded prompt without certifying workspace policy."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


VALIDATOR_VERSION = "2.1.0"
SCHEMA_VERSION = "2.1.0"
MAX_INPUT_BYTES = 2 * 1024 * 1024
FIELD_RE = re.compile(r"^([a-z][a-z0-9_]*):(?:[ \t]*(.*))?$")
MAPPING_FENCE_LABELS = frozenset(("", "text", "yaml", "yml"))
PLACEHOLDER_PATTERNS = (
    re.compile(r"<[^>\n]+>"),
    re.compile(r"\{\{[^}\n]+\}\}"),
    re.compile(r"\$\{[^}\n]+\}"),
    re.compile(r"(?i)\b(?:TODO|TBD|FIXME)\b"),
)
TRUE_VALUES = {"yes", "true"}
FALSE_VALUES = {"no", "false"}
NONE_VALUES = {"none", "null", "n/a", "not_applicable"}
SUPPORTED_CAPABILITIES = {
    "bounded_prompt_parsing": True,
    "duplicate_field_detection": True,
    "placeholder_detection": True,
    "block_scoped_mapping_parsing": True,
    "mapping_and_fence_structure_checks": True,
    "supplied_value_normalization": True,
    "internal_consistency_check": True,
    "mechanical_validity_check": True,
}


@dataclass(frozen=True)
class FieldRecord:
    name: str
    value: str
    line: int


@dataclass(frozen=True)
class MappingBlock:
    block_index: int
    fence_label: str
    start_line: int
    end_line: int | None
    fields: dict[str, FieldRecord]


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def diagnostic(
    diagnostic_id: str,
    message: str,
    *,
    line: int | None = None,
    field: str | None = None,
    severity: str = "error",
) -> dict[str, Any]:
    return {
        "diagnostic_id": diagnostic_id,
        "severity": severity,
        "line": line,
        "field": field,
        "message": message,
    }


def normalize_scalar(value: str) -> Any:
    normalized = " ".join(value.strip().split())
    lowered = normalized.lower()
    if lowered in TRUE_VALUES:
        return True
    if lowered in FALSE_VALUES:
        return False
    if lowered in NONE_VALUES:
        return None
    return normalized


def parse_prompt(text: str) -> tuple[list[MappingBlock], list[dict[str, Any]]]:
    blocks: list[MappingBlock] = []
    diagnostics: list[dict[str, Any]] = []
    in_fence = False
    fence_start = 0
    fence_label = ""
    fence_lines: list[tuple[int, str]] = []

    def finish_fence(end_line: int | None) -> None:
        nonlocal fence_lines
        if fence_label not in MAPPING_FENCE_LABELS:
            fence_lines = []
            return
        fields: dict[str, FieldRecord] = {}
        active: FieldRecord | None = None
        continuation: list[str] = []

        def finish_active() -> None:
            nonlocal active, continuation
            if active is None:
                return
            value = "\n".join([active.value, *continuation])
            record = FieldRecord(active.name, value, active.line)
            if record.name in fields:
                diagnostics.append(
                    diagnostic(
                        "PARSE002",
                        f"duplicate field in mapping block; first supplied on line {fields[record.name].line}",
                        line=record.line,
                        field=record.name,
                    )
                )
            else:
                fields[record.name] = record
            active = None
            continuation = []

        for line_number, line in fence_lines:
            match = FIELD_RE.fullmatch(line)
            if match:
                finish_active()
                active = FieldRecord(match.group(1), match.group(2) or "", line_number)
            elif active is not None:
                continuation.append(line.rstrip())
        finish_active()
        if fields:
            blocks.append(
                MappingBlock(
                    block_index=len(blocks) + 1,
                    fence_label=fence_label,
                    start_line=fence_start,
                    end_line=end_line,
                    fields=fields,
                )
            )
        fence_lines = []

    for line_number, line in enumerate(text.splitlines(), 1):
        if line.startswith("```"):
            if in_fence:
                finish_fence(line_number)
                in_fence = False
            else:
                in_fence = True
                fence_start = line_number
                fence_label = line[3:].strip().lower()
                fence_lines = []
            continue
        if in_fence:
            fence_lines.append((line_number, line))

    if in_fence:
        finish_fence(None)
        diagnostics.append(
            diagnostic(
                "PARSE001",
                "unclosed fenced block",
                line=fence_start,
            )
        )
    return blocks, diagnostics


def placeholder_diagnostics(blocks: list[MappingBlock]) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    seen: set[tuple[int, str]] = set()
    for block in blocks:
        for field in block.fields.values():
            for offset, line in enumerate(field.value.splitlines() or [""]):
                line_number = field.line + offset
                for pattern in PLACEHOLDER_PATTERNS:
                    for match in pattern.finditer(line):
                        key = (line_number, match.group(0))
                        if key in seen:
                            continue
                        seen.add(key)
                        diagnostics.append(
                            diagnostic(
                                "PLACEHOLDER001",
                                f"unresolved token: {match.group(0)}",
                                line=line_number,
                                field=field.name,
                            )
                        )
    return diagnostics


def internal_consistency_diagnostics(
    fields: dict[str, FieldRecord],
) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    normalized = {name: normalize_scalar(record.value) for name, record in fields.items()}

    commit_expected = normalized.get("commit_expected")
    do_not_commit = normalized.get("do_not_commit")
    if isinstance(commit_expected, bool) and isinstance(do_not_commit, bool):
        if commit_expected == do_not_commit:
            diagnostics.append(
                diagnostic(
                    "CONSISTENCY001",
                    "commit_expected and do_not_commit must express opposite states",
                    line=fields["commit_expected"].line,
                    field="commit_expected",
                )
            )

    if normalized.get("execution_not_authorized") is True:
        for field in ("execute", "execution_requested", "task_execution_requested"):
            if normalized.get(field) is True:
                diagnostics.append(
                    diagnostic(
                        "CONSISTENCY002",
                        f"{field} conflicts with execution_not_authorized",
                        line=fields[field].line,
                        field=field,
                    )
                )

    if (
        normalized.get("materialization_requested") is False
        and normalized.get("materialization_completed") is True
    ):
        diagnostics.append(
            diagnostic(
                "CONSISTENCY003",
                "materialization_completed conflicts with materialization_requested",
                line=fields["materialization_completed"].line,
                field="materialization_completed",
            )
        )
    return diagnostics


def load_schema(path: Path) -> dict[str, Any]:
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"schema is not readable strict-UTF-8 JSON: {exc}") from exc
    if not isinstance(schema, dict):
        raise ValueError("schema resource must be an object")
    if schema.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("schema resource version is incompatible with this linter")
    if schema.get("validator_version") != VALIDATOR_VERSION:
        raise ValueError("schema resource validator version is incompatible with this linter")
    return schema


def validate_content(content: bytes, input_path: Path) -> dict[str, Any]:
    if len(content) > MAX_INPUT_BYTES:
        raise ValueError(f"prompt exceeds {MAX_INPUT_BYTES} bytes")
    try:
        text = content.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError(f"prompt is not strict UTF-8: {exc}") from exc

    blocks, parse_diagnostics = parse_prompt(text)
    unresolved = placeholder_diagnostics(blocks)
    contradictions = [
        item
        for block in blocks
        for item in internal_consistency_diagnostics(block.fields)
    ]
    diagnostics = sorted(
        [*parse_diagnostics, *unresolved, *contradictions],
        key=lambda item: (
            item["line"] if item["line"] is not None else -1,
            item["diagnostic_id"],
            item["field"] or "",
            item["message"],
        ),
    )
    mechanical_errors = [
        item
        for item in diagnostics
        if item["diagnostic_id"].startswith(("PARSE", "PLACEHOLDER"))
        and item["severity"] == "error"
    ]
    consistency_errors = [
        item
        for item in diagnostics
        if item["diagnostic_id"].startswith("CONSISTENCY")
        and item["severity"] == "error"
    ]
    mechanical_validity = not mechanical_errors
    internal_consistency = not consistency_errors
    return {
        "producer": {
            "name": "correction-lib-prompt-contract",
            "version": VALIDATOR_VERSION,
            "schema_version": SCHEMA_VERSION,
        },
        "input": {
            "path": str(input_path.resolve()),
            "sha256": sha256_bytes(content),
            "size_bytes": len(content),
        },
        "capabilities": dict(SUPPORTED_CAPABILITIES),
        "results": {
            "mechanical_validity": mechanical_validity,
            "internal_consistency": internal_consistency,
        },
        "governance_completeness": "not_assessed",
        "governance_completeness_not_assessed": True,
        "mapping_block_count": len(blocks),
        "field_count": sum(len(block.fields) for block in blocks),
        "mapping_blocks": [
            {
                "block_index": block.block_index,
                "fence_label": block.fence_label,
                "start_line": block.start_line,
                "end_line": block.end_line,
                "normalized_fields": {
                    name: normalize_scalar(record.value)
                    for name, record in sorted(block.fields.items())
                },
            }
            for block in blocks
        ],
        "error_count": sum(item["severity"] == "error" for item in diagnostics),
        "warning_count": sum(item["severity"] == "warning" for item in diagnostics),
        "diagnostics": diagnostics,
    }


def human_output(result: dict[str, Any]) -> str:
    lines = [
        f"input_sha256: {result['input']['sha256']}",
        f"mechanical_validity: {str(result['results']['mechanical_validity']).lower()}",
        f"internal_consistency: {str(result['results']['internal_consistency']).lower()}",
        "governance_completeness: not_assessed",
        f"errors: {result['error_count']}",
        f"warnings: {result['warning_count']}",
        "diagnostics:",
    ]
    for item in result["diagnostics"]:
        location = f"line {item['line']}" if item["line"] is not None else "input"
        field = f" {item['field']}" if item["field"] else ""
        lines.append(
            f"  {item['severity']} {item['diagnostic_id']} {location}{field}: {item['message']}"
        )
    return "\n".join(lines)


def write_exclusive(path: Path, content: str) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(content)


def build_parser() -> argparse.ArgumentParser:
    skill_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Mechanically lint a prompt without assessing governance completeness."
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=skill_root / "references" / "prompt_schema.json",
    )
    parser.add_argument("--format", choices=("human", "json"), default="human")
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("prompt", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        load_schema(args.schema)
        content = args.prompt.read_bytes()
        result = validate_content(content, args.prompt)
        exit_code = 0 if result["error_count"] == 0 else 3
    except (OSError, ValueError) as exc:
        result = {
            "producer": {"name": "correction-lib-prompt-contract", "version": VALIDATOR_VERSION},
            "input": {"path": str(args.prompt), "sha256": None, "size_bytes": None},
            "capabilities": dict(SUPPORTED_CAPABILITIES),
            "results": {"mechanical_validity": False, "internal_consistency": False},
            "governance_completeness": "not_assessed",
            "governance_completeness_not_assessed": True,
            "error_count": 1,
            "warning_count": 0,
            "diagnostics": [diagnostic("INPUT001", str(exc))],
        }
        exit_code = 2

    serialized = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        try:
            write_exclusive(args.json_out, serialized)
        except OSError as exc:
            print(f"output_error: {exc}", file=sys.stderr)
            return 4
    if args.format == "json":
        sys.stdout.write(serialized)
    else:
        sys.stdout.write(human_output(result) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
