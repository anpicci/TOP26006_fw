#!/usr/bin/env python3
"""Deterministic, inert evidence-package reviewer (version 1.0.1)."""

from __future__ import annotations

import argparse
import csv
import datetime
import errno
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import struct
import subprocess
import sys
import tempfile
from typing import NamedTuple
import zipfile
import zlib

REVIEWER_VERSION = "1.0.1"
SCHEMA_VERSION = "1.0.0"
MANIFEST_VERSION = "1.0.0"
HARD_LIMITS = {"maximum_member_count": 512, "maximum_member_uncompressed_bytes": 16777216, "maximum_total_uncompressed_bytes": 67108864, "maximum_compression_ratio": 100}
PATCH_KINDS = ("source_change", "prompt_local", "binding_only", "diagnostics_only", "empty_no_changes", "cumulative_feature", "corrective_follow_up")
LOCATOR_TYPES = ("markdown_section", "csv_row", "json_pointer", "text_pattern", "file_whole", "patch_hunk", "test_name", "probe_name")
GATE_EVALUATORS = ("artifact_present", "hash_equals", "json_pointer_equals", "json_pointer_in_set", "csv_row_count", "csv_value_equals", "text_pattern_present", "text_pattern_absent", "test_summary_equals", "probe_field_equals", "patch_path_subset", "commit_subject_equals", "repository_head_equals", "manual_reviewer_decision_required")
VALIDATION_ORIGINS = ("package_authored_test_transcript", "reviewer_recomputed_builtin_check", "independent_external_test_result", "planned_but_not_run_check", "manual_reviewer_decision")
SEVERITIES = ("info", "warning", "error", "blocker")
FINDING_STATUSES = ("confirmed_new", "confirmed_preexisting", "resolved_by_corrective_delta", "unresolved", "not_reproduced", "package_claim_only", "not_applicable")
VERDICTS = ("accepted", "accepted_with_nonblocking_findings", "corrective_follow_up_required", "blocked_incomplete_package", "blocked_prompt_traceability", "blocked_baseline_mismatch", "blocked_patch_scope", "blocked_validation_evidence", "blocked_declared_gate", "blocked_self_certification", "blocked_review")
RESERVED_FIELDS = frozenset(("execute", "execution", "run", "test_command", "command", "commands", "argv", "shell", "callback", "python", "source_code", "code", "plugin", "template", "activate", "activation", "invoke", "chain", "apply", "patch_apply", "fix", "autofix", "overwrite", "cleanup", "retry", "resume", "submit", "network", "github_action"))
OUTPUT_NAMES = ("review_manifest.resolved.json", "package_inventory.csv", "review_findings.csv", "review_validation.json", "review_report.md", "review_plan.json")
DIAGNOSTIC_IDS = tuple("""PACKAGE001 PACKAGE002 PACKAGE003 PACKAGE004 ARCHIVE001 ARCHIVE002 ARCHIVE003 ARCHIVE004 ARCHIVE005 ARCHIVE006 ARCHIVE007 ARCHIVE008 PATH001 PATH002 PATH003 PATH004 HASH001 HASH002 HASH003 SCHEMA001 SCHEMA002 SCHEMA003 PROMPT001 PROMPT002 PROMPT003 BASELINE001 BASELINE002 BASELINE003 PATCH001 PATCH002 PATCH003 PATCH004 SCOPE001 SCOPE002 SCOPE003 SCOPE004 ARTIFACT001 ARTIFACT002 ARTIFACT003 EVIDENCE001 EVIDENCE002 EVIDENCE003 GATE001 GATE002 GATE003 GATE004 TEST001 TEST002 TEST003 PROBE001 PROBE002 CONTRADICTION001 CONTRADICTION002 CONTRADICTION003 CONTRADICTION004 SELF_CERTIFICATION001 SELF_CERTIFICATION002 SELF_CERTIFICATION003 GOVERNANCE001 GOVERNANCE002 VERDICT001 VERDICT002 VERDICT003 RENDER001 RENDER002""".split())
NONBLOCKING_DIAGNOSTICS = {"EVIDENCE003": ("warning", False), "TEST003": ("warning", False), "VERDICT001": ("info", False)}
SUPPORTED_SCHEMA_KEYWORDS = frozenset({
    "$schema", "$id", "$defs", "$ref", "title", "description", "type",
    "properties", "required", "additionalProperties", "items", "minItems",
    "maxItems", "minLength", "maxLength", "pattern", "minimum", "maximum",
    "exclusiveMinimum", "enum", "const", "oneOf", "allOf", "if", "then",
    "else", "format",
})
MEDIA_PARSERS = {
    "application/json": {"json"}, "text/csv": {"csv"},
    "text/markdown": {"markdown"}, "text/plain": {"text"},
    "text/x-diff": {"unified_diff", "empty_file"},
}

class ReviewError(Exception):
    def __init__(self, diagnostic_id: str, message: str, *, field: str = "", path: str = ""):
        super().__init__(message); self.diagnostic_id = diagnostic_id; self.message = message; self.field = field; self.path = path

def sha256_bytes(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def sha256_file_stream(path: Path) -> str:
    digest=hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk=handle.read(65536)
            if not chunk: break
            digest.update(chunk)
    return digest.hexdigest()
def read_bytes(path: Path) -> bytes:
    with path.open("rb") as handle: return handle.read()
def strict_text(data: bytes, diagnostic_id: str = "SCHEMA002") -> str:
    if b"\x00" in data: raise ReviewError(diagnostic_id, "NUL or binary content is unsupported")
    try: return data.decode("utf-8", "strict")
    except UnicodeDecodeError as exc: raise ReviewError(diagnostic_id, "content is not strict UTF-8") from exc
def strict_json(text: str, diagnostic_id: str = "SCHEMA002"):
    def reject_constant(value):
        raise ReviewError(diagnostic_id, f"non-finite JSON number is unsupported: {value}")
    try: return json.loads(text, parse_constant=reject_constant)
    except ReviewError: raise
    except json.JSONDecodeError as exc: raise ReviewError(diagnostic_id, "JSON parse failed") from exc
def normalize_relative(value: str) -> str:
    if not isinstance(value, str) or not value or value.startswith("/") or "\\" in value or "\x00" in value: raise ReviewError("PATH001", "unsafe relative path", path=str(value))
    parts = value.split("/")
    if any(part in ("", ".", "..") for part in parts): raise ReviewError("PATH001", "unsafe path component", path=value)
    return "/".join(parts)
def key_token(value: str) -> str:
    value=re.sub(r"([a-z0-9])([A-Z])",r"\1_\2",value)
    return "_".join(item for item in re.sub(r"[^A-Za-z0-9]+","_",value).lower().split("_") if item)
def reject_reserved(value, trail="$"):
    if isinstance(value, dict):
        for key, child in value.items():
            token=key_token(str(key))
            if token in RESERVED_FIELDS or token.replace("_","") in {item.replace("_","") for item in RESERVED_FIELDS}: raise ReviewError("SCHEMA003", "reserved capability-bearing field", field=f"{trail}.{key}")
            reject_reserved(child, f"{trail}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value): reject_reserved(child, f"{trail}[{index}]")

def schema_keywords(schema):
    observed=set()
    def visit(node):
        if not isinstance(node,dict): return
        unknown=set(node)-SUPPORTED_SCHEMA_KEYWORDS
        if unknown: raise ReviewError("SCHEMA001",f"schema uses unsupported keywords: {', '.join(sorted(unknown))}")
        observed.update(node)
        for key in ("properties","$defs"):
            for nested in node.get(key,{}).values(): visit(nested)
        for key in ("items","if","then","else"):
            child=node.get(key)
            if isinstance(child,dict): visit(child)
        for key in ("oneOf","allOf"):
            for child in node.get(key,[]): visit(child)
    visit(schema)
    return observed

def schema_validate(value, schema, root, trail="$"):
    if "$ref" in schema:
        node = root
        for part in schema["$ref"][2:].split("/"): node = node[part]
        return schema_validate(value, node, root, trail)
    if "const" in schema and value != schema["const"]: raise ReviewError("SCHEMA001", f"{trail} violates const")
    if "enum" in schema and value not in schema["enum"]: raise ReviewError("SCHEMA001", f"{trail} has unsupported value")
    if "oneOf" in schema:
        matches = 0
        for option in schema["oneOf"]:
            try: schema_validate(value, option, root, trail); matches += 1
            except ReviewError: pass
        if matches != 1: raise ReviewError("SCHEMA001", f"{trail} violates oneOf")
        return
    kind = schema.get("type")
    kinds = kind if isinstance(kind, list) else [kind] if kind else []
    checks = {"object": lambda x: isinstance(x, dict), "array": lambda x: isinstance(x, list), "string": lambda x: isinstance(x, str), "integer": lambda x: isinstance(x, int) and not isinstance(x, bool), "number": lambda x: isinstance(x, (int, float)) and not isinstance(x, bool), "boolean": lambda x: isinstance(x, bool), "null": lambda x: x is None}
    if kinds and not any(checks[item](value) for item in kinds): raise ReviewError("SCHEMA001", f"{trail} has wrong type")
    if isinstance(value, dict):
        required = schema.get("required", [])
        missing = [item for item in required if item not in value]
        if missing: raise ReviewError("SCHEMA001", f"{trail} missing required fields: {', '.join(missing)}")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = sorted(set(value) - set(props))
            if extra: raise ReviewError("SCHEMA003", f"{trail} has additional properties: {', '.join(extra)}")
        for key, child in value.items():
            if key in props: schema_validate(child, props[key], root, f"{trail}/{key}")
    elif isinstance(value, list):
        if len(value) < schema.get("minItems", 0) or len(value) > schema.get("maxItems", 10**9): raise ReviewError("SCHEMA001", f"{trail} array size invalid")
        for index, child in enumerate(value): schema_validate(child, schema.get("items", {}), root, f"{trail}/{index}")
    elif isinstance(value, str):
        if len(value) < schema.get("minLength", 0) or len(value) > schema.get("maxLength", 10**9): raise ReviewError("SCHEMA001", f"{trail} string length invalid")
        pattern = schema.get("pattern")
        if pattern:
            if re.search(pattern, value) is None: raise ReviewError("SCHEMA001", f"{trail} string pattern invalid")
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        if not math.isfinite(value): raise ReviewError("SCHEMA001", f"{trail} must be finite")
        if value < schema.get("minimum", float("-inf")) or value > schema.get("maximum", float("inf")): raise ReviewError("SCHEMA001", f"{trail} numeric limit invalid")
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]: raise ReviewError("SCHEMA001", f"{trail} exclusive minimum invalid")
    if schema.get("format") == "date-time" and value is not None:
        try: datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (AttributeError, ValueError) as exc: raise ReviewError("SCHEMA001", f"{trail} date-time format invalid") from exc
    for branch in schema.get("allOf", []):
        if "if" in branch:
            try: schema_validate(value, branch["if"], root, trail); chosen = branch.get("then", {})
            except ReviewError: chosen = branch.get("else", {})
            schema_validate(value, chosen, root, trail)

def unique_manifest_ids(manifest):
    for section, key in (("repositories", "repository_id"), ("artifacts", "artifact_id"), ("declared_gates", "gate_id"), ("independent_checks", "check_id")):
        values = [row[key] for row in manifest[section]]
        if len(values) != len(set(values)): raise ReviewError("SCHEMA001", f"duplicate {key}")
    paths = [row["relative_path"] for row in manifest["artifacts"]]
    if len(paths) != len(set(paths)): raise ReviewError("ARTIFACT002", "duplicate artifact path")

def validate_carrier_shape(manifest):
    package=manifest.get("package")
    if not isinstance(package,dict): return
    if isinstance(package.get("carrier_path"),(list,dict)) or isinstance(package.get("package_root"),(list,dict)):
        raise ReviewError("PACKAGE003","multiple carriers or package roots are unsupported")

def validate_artifact_set(declared_paths, actual_paths, required_paths):
    undeclared=sorted(set(actual_paths)-set(declared_paths))
    if undeclared: raise ReviewError("PACKAGE004","package contains undeclared artifacts",path=undeclared[0])
    missing=sorted(set(required_paths)-set(actual_paths))
    if missing: raise ReviewError("ARTIFACT001","required artifact missing",path=missing[0])

def validate_identity(observed,expected,artifact=False,path=""):
    if observed!=expected: raise ReviewError("HASH002" if artifact else "HASH001","artifact identity mismatch" if artifact else "package identity mismatch",path=path)

def validate_governance_binding(binding,workspace):
    for key,name in (("agents_sha256","AGENTS.md"),("cpc_sha256","CPC.md")):
        bound=binding.get(key) or binding.get("governance",{}).get(key)
        if not bound: raise ReviewError("GOVERNANCE001",f"binding missing {key}")
        if sha256_bytes(read_bytes(workspace/name))!=bound: raise ReviewError("GOVERNANCE002",f"live {name} hash differs")
    return True

def _descriptor_open(name, flags, parent_fd, diagnostic_id="PATH004"):
    try: return os.open(name, flags | getattr(os, "O_NOFOLLOW", 0), dir_fd=parent_fd)
    except OSError as exc:
        if exc.errno in (errno.ELOOP, errno.ENOTDIR, errno.ENOENT, errno.ESTALE):
            raise ReviewError(diagnostic_id, "descriptor containment changed during traversal", path=str(name)) from exc
        raise

def _read_bounded(descriptor, ceiling, diagnostic_id, path):
    chunks=[]; total=0
    while True:
        chunk=os.read(descriptor, min(65536, ceiling-total+1))
        if not chunk: break
        total += len(chunk)
        if total > ceiling: raise ReviewError(diagnostic_id, "member size limit exceeded", path=path)
        chunks.append(chunk)
    return b"".join(chunks)

def _stat_identity(info):
    return (info.st_dev, info.st_ino, info.st_size, stat.S_IFMT(info.st_mode), info.st_mtime_ns)

def directory_inventory(carrier: Path, package_root: str, limits=None):
    limits=dict(HARD_LIMITS if limits is None else limits)
    if not carrier.is_absolute(): raise ReviewError("PACKAGE001", "directory carrier must be absolute")
    root_flags=os.O_RDONLY|getattr(os,"O_DIRECTORY",0)|getattr(os,"O_NOFOLLOW",0)
    try: root_fd=os.open(carrier,root_flags)
    except OSError as exc: raise ReviewError("PACKAGE001", "directory carrier must be an existing no-follow directory") from exc
    rows=[]; member_count=0; total_bytes=0
    try:
        try: top_names=sorted(os.listdir(root_fd))
        except OSError as exc: raise ReviewError("PATH004", "cannot enumerate held carrier descriptor") from exc
        if top_names != [package_root]: raise ReviewError("PATH002", "carrier must contain exactly one declared package root")
        try: root_info=os.stat(package_root,dir_fd=root_fd,follow_symlinks=False)
        except OSError as exc: raise ReviewError("PATH004", "declared package root changed during traversal",path=package_root) from exc
        if not stat.S_ISDIR(root_info.st_mode): raise ReviewError("PATH003", "declared package root is not a directory",path=package_root)
        package_fd=_descriptor_open(package_root,root_flags,root_fd)
        try:
            opened_info=os.fstat(package_fd)
            if (root_info.st_dev,root_info.st_ino)!=(opened_info.st_dev,opened_info.st_ino): raise ReviewError("PATH004","declared package root identity changed",path=package_root)
            def walk(directory_fd, relative_directory):
                nonlocal member_count,total_bytes
                try: names=sorted(os.listdir(directory_fd))
                except OSError as exc: raise ReviewError("PATH004","directory enumeration failed",path=relative_directory) from exc
                for name in names:
                    normalize_relative(name)
                    relative=f"{relative_directory}/{name}"
                    try: before=os.stat(name,dir_fd=directory_fd,follow_symlinks=False)
                    except OSError as exc: raise ReviewError("PATH004","member changed before descriptor open",path=relative) from exc
                    if stat.S_ISLNK(before.st_mode): raise ReviewError("PATH003","symlink encountered",path=relative)
                    if stat.S_ISDIR(before.st_mode):
                        child_fd=_descriptor_open(name,root_flags,directory_fd)
                        try:
                            opened=os.fstat(child_fd)
                            if (before.st_dev,before.st_ino)!=(opened.st_dev,opened.st_ino): raise ReviewError("PATH004","directory identity changed",path=relative)
                            walk(child_fd,relative)
                        finally: os.close(child_fd)
                        continue
                    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1: raise ReviewError("PATH003","hard-linked or special file encountered",path=relative)
                    member_count += 1
                    if member_count > limits["maximum_member_count"]: raise ReviewError("PACKAGE002","directory member limit exceeded",path=relative)
                    if before.st_size > limits["maximum_member_uncompressed_bytes"]: raise ReviewError("PACKAGE002","directory member size limit exceeded",path=relative)
                    total_bytes += before.st_size
                    if total_bytes > limits["maximum_total_uncompressed_bytes"]: raise ReviewError("PACKAGE002","directory total size limit exceeded",path=relative)
                    first_fd=_descriptor_open(name,os.O_RDONLY,directory_fd)
                    try:
                        first=os.fstat(first_fd)
                        if _stat_identity(before)!=_stat_identity(first) or first.st_nlink!=1: raise ReviewError("PATH004","file identity changed before opening",path=relative)
                        data=_read_bounded(first_fd,limits["maximum_member_uncompressed_bytes"],"PACKAGE002",relative)
                    finally: os.close(first_fd)
                    second_fd=_descriptor_open(name,os.O_RDONLY,directory_fd)
                    try:
                        second=os.fstat(second_fd)
                        if not stat.S_ISREG(second.st_mode) or second.st_nlink!=1: raise ReviewError("PATH003","reopened member is not a unique regular file",path=relative)
                        reopened=_read_bounded(second_fd,limits["maximum_member_uncompressed_bytes"],"PACKAGE002",relative)
                    finally: os.close(second_fd)
                    if _stat_identity(first)!=_stat_identity(second) or data!=reopened: raise ReviewError("HASH003","directory artifact changed during independent reopening",path=relative)
                    rows.append({"relative_path":relative,"size_bytes":len(data),"sha256":sha256_bytes(data),"data":data})
            walk(package_fd,package_root)
        finally: os.close(package_fd)
    finally: os.close(root_fd)
    return rows

def zip_inventory(carrier: Path, package_root: str, limits):
    if not carrier.is_absolute() or not carrier.is_file(): raise ReviewError("PACKAGE001", "ZIP carrier must be an absolute existing file")
    rows=[]; names=set(); folded=set(); offsets=set(); total=0; preflight=[]; roots=set()
    try: archive = zipfile.ZipFile(carrier, "r")
    except (OSError, zipfile.BadZipFile) as exc: raise ReviewError("ARCHIVE001", "malformed ZIP") from exc
    with archive:
        infos=archive.infolist()
        if len(infos)>limits["maximum_member_count"]: raise ReviewError("ARCHIVE002", "member limit exceeded")
        for info in infos:
            name=normalize_relative(info.filename.rstrip("/"))
            if info.is_dir(): raise ReviewError("PATH003", "directory entries are unsupported")
            if name in names: raise ReviewError("ARCHIVE004", "duplicate ZIP member")
            if name.casefold() in folded: raise ReviewError("ARCHIVE005", "case-folded ZIP collision")
            if info.header_offset in offsets: raise ReviewError("ARCHIVE001", "duplicate local-header offset")
            names.add(name); folded.add(name.casefold()); offsets.add(info.header_offset)
            roots.add(name.split("/",1)[0])
            mode=(info.external_attr>>16)&0xffff; mode_type=stat.S_IFMT(mode)
            if mode_type not in (0,stat.S_IFREG): raise ReviewError("PATH003", "non-regular ZIP mode")
            if info.flag_bits & 1: raise ReviewError("ARCHIVE006", "encrypted ZIP member")
            if info.flag_bits & 8: raise ReviewError("ARCHIVE006", "data descriptors are unsupported")
            if info.flag_bits & ~0x800 or info.extract_version>20 or info.extra: raise ReviewError("ARCHIVE006", "unsupported ZIP feature")
            if info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED): raise ReviewError("ARCHIVE006", "unsupported compression")
            total += info.file_size
            if info.file_size>limits["maximum_member_uncompressed_bytes"] or total>limits["maximum_total_uncompressed_bytes"]: raise ReviewError("ARCHIVE002", "ZIP size limit exceeded")
            if info.file_size and not info.compress_size: raise ReviewError("ARCHIVE003", "zero compressed size")
            if info.compress_size and info.file_size/info.compress_size>limits["maximum_compression_ratio"]: raise ReviewError("ARCHIVE003", "compression ratio exceeded")
            if Path(name).suffix.lower() in (".zip", ".tar", ".tgz", ".gz", ".bz2", ".xz", ".7z"): raise ReviewError("ARCHIVE007", "nested archive extension")
            with carrier.open("rb") as raw:
                raw.seek(info.header_offset); header=raw.read(30)
                if len(header)!=30 or header[:4]!=b"PK\x03\x04": raise ReviewError("ARCHIVE001", "malformed local header")
                fields=struct.unpack("<IHHHHHIIIHH",header)
                local_name=raw.read(fields[-2])
                local_extra=raw.read(fields[-1])
                if local_extra or local_name.decode("utf-8" if info.flag_bits&0x800 else "cp437")!=info.filename or fields[3]!=info.compress_type or fields[2]!=info.flag_bits or fields[6]!=info.CRC or fields[7]!=info.compress_size or fields[8]!=info.file_size: raise ReviewError("ARCHIVE008", "central/local header mismatch")
            preflight.append((info,name))
        if roots!={package_root}: raise ReviewError("PATH002", "multiple or wrong package roots")
        for info,name in preflight:
            try:
                chunks=[]; actual=0
                with archive.open(info,"r") as handle:
                    while True:
                        chunk=handle.read(65536)
                        if not chunk: break
                        actual+=len(chunk)
                        if actual>limits["maximum_member_uncompressed_bytes"]: raise ReviewError("ARCHIVE002","stream member limit exceeded")
                        chunks.append(chunk)
                data=b"".join(chunks)
            except ReviewError: raise
            except (RuntimeError, zipfile.BadZipFile, zlib.error,EOFError) as exc: raise ReviewError("ARCHIVE008", "ZIP stream validation failed") from exc
            if len(data)!=info.file_size or (zlib.crc32(data)&0xffffffff)!=info.CRC: raise ReviewError("ARCHIVE008", "ZIP byte count or CRC mismatch")
            if data.startswith((b"PK\x03\x04",b"\x1f\x8b",b"BZh",b"\xfd7zXZ")) or data[257:262]==b"ustar": raise ReviewError("ARCHIVE007", "nested archive signature")
            rows.append({"relative_path":name,"size_bytes":len(data),"sha256":sha256_bytes(data),"data":data})
    return rows

def inventory_hash(rows):
    payload="".join(f"{row['relative_path']}\0{row['size_bytes']}\0{row['sha256']}\n" for row in sorted(rows,key=lambda x:x["relative_path"])).encode()
    return sha256_bytes(payload)

def parse_artifact(record, data):
    parser=record["parser"]
    if parser not in MEDIA_PARSERS.get(record["media_type"], set()): raise ReviewError("ARTIFACT003", "media type and parser disagree")
    if parser=="empty_file":
        if data: raise ReviewError("SCHEMA002", "expected exact zero-byte artifact")
        return None
    text=strict_text(data)
    if parser=="json":
        return strict_json(text)
    if parser=="csv": return list(csv.DictReader(text.splitlines()))
    if parser in ("markdown","text"): return text
    if parser=="unified_diff": return parse_patch(text, None)
    raise ReviewError("SCHEMA003", "unsupported parser")

def _patch_path(value, prefix=None, allow_dev_null=False):
    if allow_dev_null and value=="/dev/null": return value
    if prefix is not None:
        expected=prefix+"/"
        if not value.startswith(expected): raise ReviewError("SCOPE001","patch path lacks its grammatical prefix",path=value)
        value=value[len(expected):]
    try: return normalize_relative(value)
    except ReviewError as exc: raise ReviewError("SCOPE001","unsafe patch path",path=str(value)) from exc

def _path_in_scope(path, roots):
    return any(path==root.rstrip("/") or path.startswith(root.rstrip("/")+"/") for root in roots)

def _parse_hunk(lines,index,record):
    match=re.fullmatch(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?: .*)?",lines[index])
    if not match: raise ReviewError("PATCH001","malformed hunk header")
    old_expected=int(match.group(2) if match.group(2) is not None else 1)
    new_expected=int(match.group(4) if match.group(4) is not None else 1)
    header=lines[index]; index+=1; old_count=0; new_count=0; previous_content=False
    while index<len(lines) and not lines[index].startswith(("@@ ","diff --git ")):
        line=lines[index]
        if line==r"\ No newline at end of file":
            if not previous_content: raise ReviewError("PATCH001","misplaced no-newline marker")
            previous_content=False; index+=1; continue
        if not line or line[0] not in (" ","+","-"): raise ReviewError("PATCH001","unknown hunk body line")
        if line[0] in (" ","-"): old_count+=1
        if line[0] in (" ","+"): new_count+=1
        previous_content=True; index+=1
    if old_count!=old_expected or new_count!=new_expected: raise ReviewError("PATCH001","hunk line counts disagree with header")
    record["hunks"].append(header)
    return index

def parse_patch(text, contract):
    if "GIT binary patch" in text or "Binary files " in text or "Subproject commit " in text: raise ReviewError("PATCH002", "binary or submodule patch")
    encoded=text.encode("utf-8")
    maximum_bytes=(contract or {}).get("maximum_patch_bytes",16777216)
    maximum_lines=(contract or {}).get("maximum_patch_lines",200000)
    lines=text.splitlines()
    if len(encoded)>maximum_bytes or len(lines)>maximum_lines: raise ReviewError("PATCH001","patch ceiling exceeded")
    if contract:
        kind=contract["patch_kind"]
        if contract["expected_empty"] != (len(encoded)==0) or (kind=="empty_no_changes" and encoded): raise ReviewError("PATCH003","patch empty state disagrees")
    if not text: return []
    records=[]; index=0; seen=set()
    while index<len(lines):
        match=re.fullmatch(r"diff --git a/(\S+) b/(\S+)",lines[index])
        if not match: raise ReviewError("PATCH001","expected diff --git record boundary")
        old_path=_patch_path("a/"+match.group(1),"a"); new_path=_patch_path("b/"+match.group(2),"b")
        record={"old_path":old_path,"new_path":new_path,"hunks":[],"operations":[],"semantic_paths":[old_path,new_path]}
        if old_path in seen or new_path in seen: raise ReviewError("SCOPE004","duplicate normalized patch path")
        seen.update((old_path,new_path)); index+=1
        metadata={}; content_old=None; content_new=None
        while index<len(lines) and not lines[index].startswith(("diff --git ","--- ","@@ ")):
            line=lines[index]
            if re.fullmatch(r"index [0-9a-f]+\.\.[0-9a-f]+(?: [0-7]{6})?",line):
                if "index" in metadata: raise ReviewError("PATCH001","duplicate index metadata")
                metadata["index"]=line
            elif re.fullmatch(r"(?:old mode|new mode|new file mode|deleted file mode) [0-7]{6}",line):
                key=line.rsplit(" ",1)[0]
                if key in metadata: raise ReviewError("PATCH001","duplicate mode metadata")
                metadata[key]=line.rsplit(" ",1)[1]
            elif re.fullmatch(r"similarity index (?:100|[0-9]{1,2})%",line):
                if "similarity" in metadata: raise ReviewError("PATCH001","duplicate similarity metadata")
                metadata["similarity"]=line
            elif line.startswith(("rename from ","rename to ","copy from ","copy to ")):
                key,value=line.split(" ",2)[0]+" "+line.split(" ",2)[1],line.split(" ",2)[2]
                if key in metadata: raise ReviewError("PATCH001","duplicate operation metadata")
                normalized=_patch_path(value)
                metadata[key]=normalized; record["semantic_paths"].append(normalized); record["operations"].append(key.split()[0])
            else: raise ReviewError("PATCH001","unknown patch metadata or text")
            index+=1
        if index<len(lines) and lines[index].startswith("--- "):
            content_old=_patch_path(lines[index][4:],"a",allow_dev_null=True); index+=1
            if index>=len(lines) or not lines[index].startswith("+++ "): raise ReviewError("PATCH001","missing paired +++ header")
            content_new=_patch_path(lines[index][4:],"b",allow_dev_null=True); index+=1
            for path in (content_old,content_new):
                if path!="/dev/null": record["semantic_paths"].append(path)
            if content_old=="/dev/null":
                if content_new!=new_path or "new file mode" not in metadata: raise ReviewError("PATCH001","invalid creation headers")
            elif content_new=="/dev/null":
                if content_old!=old_path or "deleted file mode" not in metadata: raise ReviewError("PATCH001","invalid deletion headers")
            elif content_old!=old_path or content_new!=new_path: raise ReviewError("PATCH001","content paths disagree with diff header")
            if index>=len(lines) or not lines[index].startswith("@@ "): raise ReviewError("PATCH001","content patch has no hunk")
            while index<len(lines) and lines[index].startswith("@@ "): index=_parse_hunk(lines,index,record)
        elif index<len(lines) and lines[index].startswith("@@ "):
            raise ReviewError("PATCH001","hunk lacks ---/+++ headers")
        rename=("rename from" in metadata or "rename to" in metadata)
        copy=("copy from" in metadata or "copy to" in metadata)
        if rename:
            if set(("rename from","rename to"))-set(metadata) or metadata["rename from"]!=old_path or metadata["rename to"]!=new_path: raise ReviewError("PATCH001","rename metadata is incomplete or inconsistent")
        if copy:
            if set(("copy from","copy to"))-set(metadata) or metadata["copy from"]!=old_path or metadata["copy to"]!=new_path: raise ReviewError("PATCH001","copy metadata is incomplete or inconsistent")
        if rename and copy: raise ReviewError("PATCH001","record cannot be both rename and copy")
        if ("old mode" in metadata)!=("new mode" in metadata): raise ReviewError("PATCH001","mode metadata must be paired")
        if not record["hunks"] and not rename and not copy and not any(key in metadata for key in ("old mode","new mode","new file mode","deleted file mode")):
            raise ReviewError("PATCH001","diff record has no complete operation")
        record["metadata"]=metadata; records.append(record)
    if contract:
        for record in records:
            operations=set(record["operations"])
            if "rename" in operations and not contract["allow_renames"]: raise ReviewError("PATCH004","rename is not authorized")
            if "copy" in operations and not contract["allow_copies"]: raise ReviewError("PATCH004","copy is not authorized")
            if "deleted file mode" in record["metadata"] and not contract["allow_deletions"]: raise ReviewError("PATCH004","deletion is not authorized")
            if any(key in record["metadata"] for key in ("old mode","new mode")) and not contract["allow_mode_changes"]: raise ReviewError("PATCH004","mode change is not authorized")
            for path in record["semantic_paths"]:
                if contract["allowed_paths"] and not _path_in_scope(path,contract["allowed_paths"]): raise ReviewError("SCOPE002","patch path outside allowlist",path=path)
                if _path_in_scope(path,contract["forbidden_paths"]): raise ReviewError("SCOPE003","patch path forbidden",path=path)
    return records

def fixed_git(repo: Path, args):
    if not repo.is_absolute() or not (repo/".git").exists(): raise ReviewError("BASELINE001", "invalid repository path")
    allowed=(args==["rev-parse","HEAD"] or args==["branch","--show-current"] or args==["log","-1","--format=%s"])
    if not allowed: raise ReviewError("BASELINE001","Git operation is outside the closed read-only set")
    completed=subprocess.run(["git",*args],cwd=repo,text=True,capture_output=True,shell=False,check=False)
    if completed.returncode: raise ReviewError("BASELINE002", "bounded Git read failed")
    return completed.stdout.strip()

def json_pointer(value, pointer):
    if pointer=="": return value
    if not pointer.startswith("/"): raise ReviewError("EVIDENCE001", "invalid JSON pointer")
    node=value
    for token in pointer[1:].split("/"):
        token=token.replace("~1","/").replace("~0","~")
        try: node=node[int(token)] if isinstance(node,list) else node[token]
        except (KeyError,IndexError,ValueError,TypeError) as exc: raise ReviewError("EVIDENCE001", "JSON pointer absent") from exc
    return node

def locate(locator, parsed, patch_records):
    artifact_id=locator["artifact_id"]
    if artifact_id not in parsed: raise ReviewError("EVIDENCE001","locator artifact absent",field=artifact_id)
    value=parsed[artifact_id]; kind=locator["locator_type"]; token=locator["locator_value"]
    if kind=="json_pointer": observed=json_pointer(value,token)
    elif kind=="file_whole": observed=sha256_bytes((json.dumps(value,sort_keys=True) if not isinstance(value,str) else value).encode())
    elif kind=="text_pattern":
        if not isinstance(value,str) or value.count(token)!=1: raise ReviewError("EVIDENCE001","literal pattern absent or ambiguous")
        observed=token
    elif kind=="markdown_section":
        if not isinstance(value,str): raise ReviewError("EVIDENCE001","Markdown locator targets non-text")
        heading=" ".join(token.strip().lower().split()); matches=[line for line in value.splitlines() if line.startswith("#") and " ".join(line.lstrip("#").strip().lower().split())==heading]
        if len(matches)!=1: raise ReviewError("EVIDENCE001","Markdown heading absent or ambiguous")
        observed=matches[0]
    elif kind=="csv_row":
        if not isinstance(value,list): raise ReviewError("EVIDENCE001","CSV locator targets non-CSV")
        key,value_token=token.split("=",1); matches=[row for row in value if row.get(key)==value_token]
        if len(matches)!=1: raise ReviewError("EVIDENCE001","CSV row absent or ambiguous")
        observed=matches[0]
    elif kind=="patch_hunk":
        matches=[h for row in patch_records for h in row["hunks"] if token in f"{row['old_path']}->{row['new_path']}:{h}"]
        if len(matches)!=1: raise ReviewError("EVIDENCE001","patch hunk absent or ambiguous")
        observed=matches[0]
    elif kind in ("test_name","probe_name"):
        if not isinstance(value,(list,dict)): raise ReviewError("EVIDENCE001","named result targets unsupported data")
        rows=value if isinstance(value,list) else value.get("results",[]); matches=[row for row in rows if row.get("name")==token]
        if len(matches)!=1: raise ReviewError("EVIDENCE001","named result absent or ambiguous")
        observed=matches[0]
    else: raise ReviewError("EVIDENCE001","unsupported locator")
    expected=locator.get("expected_hash_or_value")
    if expected is not None and observed!=expected: raise ReviewError("EVIDENCE002","locator value mismatch")
    declared_observed=locator.get("observed_hash_or_value")
    if declared_observed is not None and observed!=declared_observed: raise ReviewError("EVIDENCE002","declared observed locator value mismatch")
    return observed

def collect_findings(parsed, finding_policy):
    findings=[]; seen=set()
    for value in parsed.values():
        candidates=value.get("findings",[]) if isinstance(value,dict) else []
        if not isinstance(candidates,list): continue
        for row in candidates:
            required={"finding_id","category","severity","status","blocking"}
            if not isinstance(row,dict) or not required.issubset(row): raise ReviewError("SCHEMA002","finding record is incomplete")
            if row["finding_id"] in seen: raise ReviewError("ARTIFACT002","duplicate finding ID")
            if row["severity"] not in SEVERITIES or row["status"] not in FINDING_STATUSES: raise ReviewError("SCHEMA003","finding enum is unsupported")
            seen.add(row["finding_id"])
            row=dict(row); status=row["status"]; severity=row["severity"]
            permitted=row["category"] in finding_policy["allowed_nonblocking_preexisting_categories"]
            preexisting_proven=row.get("reviewer_recomputed_pre_delta") is True and bool(row.get("pre_delta_evidence"))
            corrective_proven=row.get("reviewer_recomputed_corrective") is True and bool(row.get("corrective_evidence") or row.get("evidence_locators"))
            derived_blocking = (
                (status=="confirmed_preexisting" and not (permitted and preexisting_proven)) or
                (status=="resolved_by_corrective_delta" and not corrective_proven) or
                status=="unresolved" or
                (status=="package_claim_only" and finding_policy.get("package_claim_only_blocks_acceptance") is True) or
                (status=="confirmed_new" and severity in ("error","blocker"))
            )
            row["blocking"]=bool(row.get("blocking")) or derived_blocking
            row["reviewer_normalized"]=True
            findings.append(row)
    return findings

def check_prompt_traceability(record):
    prompt_path=Path(record["path"]); validation_path=Path(record["prompt_contract_validation_path"])
    if not prompt_path.is_absolute() or not validation_path.is_absolute(): raise ReviewError("PROMPT001","prompt paths must be absolute")
    prompt_data=read_bytes(prompt_path); validation_data=read_bytes(validation_path)
    if sha256_bytes(prompt_data)!=record["sha256"]: raise ReviewError("PROMPT001","authorizing prompt hash mismatch")
    if sha256_bytes(validation_data)!=record["prompt_contract_validation_sha256"]: raise ReviewError("PROMPT002","prompt validation artifact hash mismatch")
    validation=strict_json(strict_text(validation_data,"PROMPT002"),"PROMPT002")
    if validation.get("input",{}).get("sha256")!=record["sha256"] or validation.get("error_count")!=0 or validation.get("valid_schema") is not True: raise ReviewError("PROMPT002","prompt-contract result is invalid or mismatched")
    required_context={"continuation","evidence_round","user_run_handoff"}
    if set(validation.get("context",{}))!=required_context or validation.get("validator_version")!="1.0.0" or validation.get("schema_version")!="1.0.0": raise ReviewError("PROMPT002","prompt-contract context or version mismatch")
    governance=validation.get("governance",{})
    if governance.get("binding_matches") is not True: raise ReviewError("PROMPT002","prompt-contract governance binding was stale")
    workspace=Path(__file__).resolve().parents[4]
    if governance.get("agents_sha256")!=sha256_bytes(read_bytes(workspace/"AGENTS.md")) or governance.get("cpc_sha256")!=sha256_bytes(read_bytes(workspace/"CPC.md")): raise ReviewError("PROMPT002","prompt-contract governance hashes disagree with live bytes")
    text=strict_text(prompt_data,"PROMPT001")
    exact_scalars={"prompt_id":record["expected_prompt_id"],"prompt_mode":record["expected_prompt_mode"],"validation_ceiling":record["expected_validation_ceiling"],"patch_kind_expected":record["expected_patch_kind"]}
    for key,expected in exact_scalars.items():
        if re.search(rf"(?m)^{re.escape(key)}:\s*{re.escape(str(expected))}\s*$",text) is None: raise ReviewError("PROMPT003",f"expected prompt metadata disagrees: {key}")
    policy=record["expected_commit_policy"]
    for key in ("commit_expected","do_not_commit"):
        expected="yes" if policy[key] else "no"
        if re.search(rf"(?m)^{key}:\s*{expected}\s*$",text) is None: raise ReviewError("PROMPT003",f"expected commit policy disagrees: {key}")
    subject=policy.get("expected_subject")
    if subject is not None and subject not in text: raise ReviewError("PROMPT003","expected commit subject disagrees")
    for expected in record["expected_allowed_paths"]:
        if expected not in text: raise ReviewError("PROMPT003","expected allowed path absent")
    for expected in record["expected_forbidden_actions"]:
        if re.search(rf"(?m)^\s*{re.escape(expected)}:\s*no\s*$",text) is None and expected not in text: raise ReviewError("PROMPT003","expected forbidden action absent")
    return validation

class RepositoryObservation(NamedTuple):
    repository_id: str
    mode: str
    authoritative: bool
    observed_branch: str|None = None
    observed_head: str|None = None
    observed_subject: str|None = None
    observed_patch_baseline: str|None = None
    diagnostics: tuple = ()

def _authoritative_locator(locator, observed, evaluator, source_of_authority=""):
    source=observed.get("origin") if isinstance(observed,dict) else None
    needs_independent=evaluator in ("test_summary_equals","probe_field_equals")
    authority=source_of_authority.lower()
    if locator.get("reviewer_recomputed") is not True and (needs_independent or "reviewer" in authority or "independent" in authority):
        raise ReviewError("SELF_CERTIFICATION002","required reviewer recomputation is absent")
    if needs_independent and source in ("package_authored_test_transcript","planned_but_not_run_check",None):
        raise ReviewError("SELF_CERTIFICATION002","package-authored result cannot satisfy an independent gate")

def evaluate_gate(gate,parsed,patch_records,repositories):
    evaluator=gate["evaluator"]; accepted=gate["accepted_values"]
    if evaluator=="text_pattern_absent":
        for locator in gate["evidence_requirements"]:
            value=parsed.get(locator["artifact_id"])
            if not isinstance(value,str) or value.count(locator["locator_value"])!=0: return False
        return bool(gate["evidence_requirements"])
    observations=[]
    for item in gate["evidence_requirements"]:
        observed=locate(item,parsed,patch_records); _authoritative_locator(item,observed,evaluator,gate.get("source_of_authority","")); observations.append(observed)
    if evaluator=="manual_reviewer_decision_required":
        resolution=gate.get("manual_resolution")
        if resolution is None or resolution.get("decision") not in accepted: return False
        locate(resolution["evidence_locator"],parsed,patch_records)
        return True
    if evaluator=="artifact_present": return bool(observations)
    if evaluator in ("hash_equals","json_pointer_equals","csv_value_equals","test_summary_equals","probe_field_equals"): return bool(observations) and observations[-1] in accepted
    if evaluator=="json_pointer_in_set": return bool(observations) and observations[-1] in accepted
    if evaluator=="csv_row_count":
        if not gate["evidence_requirements"]: return False
        artifact=parsed.get(gate["evidence_requirements"][-1]["artifact_id"])
        return isinstance(artifact,list) and len(artifact)==gate["expected_count"]
    if evaluator=="text_pattern_present": return bool(observations)
    if evaluator=="text_pattern_absent": return not observations
    if evaluator=="patch_path_subset": return set(r["new_path"] for r in patch_records).issubset(set(accepted))
    if evaluator in ("commit_subject_equals","repository_head_equals"):
        authoritative=[item for item in repositories if item.authoritative]
        if not authoritative: raise ReviewError("SELF_CERTIFICATION002","required repository observation is not authoritative")
        field="observed_subject" if evaluator=="commit_subject_equals" else "observed_head"
        return any(getattr(item,field) in accepted for item in authoritative)
    raise ReviewError("GATE001","unsupported gate evaluator")

def evaluate_declared_gate(gate,parsed,patch_records,repositories):
    if gate["evaluator"] not in GATE_EVALUATORS: raise ReviewError("GATE001","unknown gate evaluator")
    if gate["evaluator"]=="manual_reviewer_decision_required" and gate.get("manual_resolution") is None:
        return [diagnostics_record(ReviewError("GATE003","manual decision unresolved",field=gate.get("gate_id","")))],True
    if not gate.get("required",False): return [],False
    try: satisfied=evaluate_gate(gate,parsed,patch_records,repositories)
    except ReviewError as exc: return [diagnostics_record(exc),diagnostics_record(ReviewError("GATE002","required gate is not satisfied",field=gate.get("gate_id","")))],False
    if not satisfied: return [diagnostics_record(ReviewError("GATE002","required gate is not satisfied",field=gate.get("gate_id","")))],False
    return [],False

def validate_origins(parsed):
    for value in parsed.values():
        rows=value.get("results",[]) if isinstance(value,dict) else value if isinstance(value,list) else []
        for row in rows:
            if isinstance(row,dict) and "origin" in row and row["origin"] not in VALIDATION_ORIGINS: raise ReviewError("SCHEMA003","validation origin is unsupported")

def verify_repository(repo, patch_contract):
    mode=repo["verification_mode"]
    repository_id=repo["repository_id"]
    if mode=="package_claim_only": return RepositoryObservation(repository_id,mode,False,diagnostics=(diagnostics_record(ReviewError("EVIDENCE003","repository values remain package-authored claims",field=repository_id)),))
    if mode=="not_safely_generic": return RepositoryObservation(repository_id,mode,False,diagnostics=(diagnostics_record(ReviewError("VERDICT002","repository state not safely generic",field=repository_id)),))
    if mode=="reviewer_recomputed_patch_and_baseline":
        baseline=patch_contract.get("baseline_head")
        if not repo.get("expected_head_before") or baseline!=repo.get("expected_head_before"): return RepositoryObservation(repository_id,mode,False,observed_patch_baseline=baseline,diagnostics=(diagnostics_record(ReviewError("BASELINE001","immutable patch baseline is missing or disagrees",field=repository_id)),))
        return RepositoryObservation(repository_id,mode,True,observed_patch_baseline=baseline)
    if mode=="reviewer_recomputed_live_read_only":
        path=Path(repo["repository_path"]); head=fixed_git(path,["rev-parse","HEAD"]); branch=fixed_git(path,["branch","--show-current"]); diagnostics=[]
        subject=fixed_git(path,["log","-1","--format=%s"])
        if head!=repo["expected_head_after"] or branch!=repo["expected_branch_after"]: diagnostics.append(diagnostics_record(ReviewError("BASELINE002","repository branch or HEAD mismatch",field=repository_id)))
        if repo.get("expected_commit_subject") and subject!=repo["expected_commit_subject"]: diagnostics.append(diagnostics_record(ReviewError("BASELINE003","commit subject mismatch",field=repository_id)))
        return RepositoryObservation(repository_id,mode,not any(item["blocking"] for item in diagnostics),branch,head,subject,diagnostics=tuple(diagnostics))
    raise ReviewError("SCHEMA003","unsupported repository verification mode")

def diagnostics_record(error):
    severity,blocking=NONBLOCKING_DIAGNOSTICS.get(error.diagnostic_id,("error",True))
    return {"diagnostic_id":error.diagnostic_id,"family":error.diagnostic_id.rstrip("0123456789"),"severity":severity,"blocking":blocking,"artifact_id":"","gate_or_finding_id":"","field":error.field,"safe_path":error.path,"message":error.message,"contract_locator":"SKILLS010_skill_contract.md"}

def validate_cross_records(manifest):
    repositories={row["repository_id"]:row for row in manifest["repositories"]}
    artifacts={row["artifact_id"]:row for row in manifest["artifacts"]}
    gates={row["gate_id"]:row for row in manifest["declared_gates"]}
    reviewed=manifest["package"]["reviewed_repository_ids"]
    if any(item not in repositories for item in reviewed): raise ReviewError("BASELINE001","package references an unknown reviewed repository")
    patch=manifest["patch_contract"]; repository=repositories.get(patch["baseline_repository_id"])
    if repository is None: raise ReviewError("BASELINE001","patch baseline repository is absent")
    if patch["artifact_id"] not in artifacts: raise ReviewError("ARTIFACT001","patch artifact reference is absent")
    expected_before=repository.get("expected_head_before")
    if expected_before is not None and patch.get("baseline_head")!=expected_before: raise ReviewError("BASELINE003","patch baseline disagrees with immutable expected-before HEAD")
    repo_allowed=repository.get("allowed_changed_paths",[])
    for allowed in patch["allowed_paths"]:
        if repo_allowed and not _path_in_scope(allowed,repo_allowed): raise ReviewError("SCOPE002","patch allowlist exceeds repository allowlist",path=allowed)
    empty=patch["expected_empty"] or patch["patch_kind"]=="empty_no_changes"
    if empty and (repository["mutation_expected"] or repository["commit_expected"] or patch["commit_requirement"]=="required"):
        raise ReviewError("BASELINE003","empty patch conflicts with mutation or commit expectation")
    if repository["commit_expected"] != (patch["commit_requirement"]=="required") and patch["commit_requirement"]!="not_applicable":
        raise ReviewError("BASELINE003","repository and patch commit requirements disagree")
    prompt_commit=manifest["authorizing_prompt"]["expected_commit_policy"]["commit_expected"]
    if prompt_commit != repository["commit_expected"]: raise ReviewError("BASELINE003","prompt and repository commit policies disagree")
    for check in manifest["independent_checks"]:
        result=check["result_artifact_id"]
        if check["state"]=="planned_but_not_run_check":
            if result is not None: raise ReviewError("TEST001","planned check cannot claim a result artifact")
        elif result is None or result not in artifacts: raise ReviewError("TEST001","completed check result artifact is absent")
    for gate in gates.values():
        for locator in gate["evidence_requirements"]:
            if locator["artifact_id"] not in artifacts: raise ReviewError("EVIDENCE001","gate locator references absent artifact",field=gate["gate_id"])
        resolution=gate.get("manual_resolution")
        if resolution and resolution["evidence_locator"]["artifact_id"] not in artifacts: raise ReviewError("GATE003","manual resolution references absent evidence",field=gate["gate_id"])
    return True

def validate_result_artifacts(manifest, parsed):
    diagnostics=[]
    for artifact in manifest["artifacts"]:
        role=artifact["semantic_role"]
        if role not in ("test_results","probe_results") or artifact["artifact_id"] not in parsed: continue
        value=parsed[artifact["artifact_id"]]; diagnostic="TEST001" if role=="test_results" else "PROBE001"
        rows=value.get("results") if isinstance(value,dict) else value
        if not isinstance(rows,list) or any(not isinstance(row,dict) or not isinstance(row.get("name"),str) for row in rows):
            diagnostics.append(diagnostics_record(ReviewError(diagnostic,"result rows are malformed",field=artifact["artifact_id"]))); continue
        if role=="test_results" and isinstance(value,dict):
            failed=sum(1 for row in rows if row.get("status") not in ("pass","passed","ok"))
            if ("total" in value and value["total"]!=len(rows)) or ("failed" in value and value["failed"]!=failed): diagnostics.append(diagnostics_record(ReviewError("TEST002","test summary disagrees with detailed results",field=artifact["artifact_id"])))
        if role=="probe_results":
            for row in rows:
                if "expected" in row and row.get("observed")!=row["expected"]: diagnostics.append(diagnostics_record(ReviewError("PROBE002","probe result disagrees with required value",field=row["name"])))
    for check in manifest["independent_checks"]:
        if check["state"]=="planned_but_not_run_check": diagnostics.append(diagnostics_record(ReviewError("TEST003","independent test is planned but not supplied",field=check["check_id"])))
    declared_gate_ids={gate["gate_id"] for gate in manifest["declared_gates"]}
    for value in parsed.values():
        if not isinstance(value,dict): continue
        claimed=value.get("domain_gate_ids",[])
        if isinstance(claimed,list) and any(item not in declared_gate_ids for item in claimed): diagnostics.append(diagnostics_record(ReviewError("GATE004","package relies on an undeclared domain gate")))
    return diagnostics

def detect_contradictions(parsed,patch_records):
    diagnostics=[]
    objects=[item for item in parsed.values() if isinstance(item,dict)]
    for item in objects:
        if item.get("report_status") in ("pass","passed") and item.get("failed",0): diagnostics.append(diagnostics_record(ReviewError("CONTRADICTION001","report pass conflicts with failure")))
        if "summary_count" in item and "details" in item and item["summary_count"]!=len(item["details"]): diagnostics.append(diagnostics_record(ReviewError("CONTRADICTION002","summary count conflicts with details")))
        if item.get("no_changes") is True and patch_records: diagnostics.append(diagnostics_record(ReviewError("CONTRADICTION003","no-change claim conflicts with patch")))
        if item.get("declared_hash") and item.get("actual_hash") and item["declared_hash"]!=item["actual_hash"]: diagnostics.append(diagnostics_record(ReviewError("CONTRADICTION003","declared hash conflicts with recomputed hash")))
        if item.get("commit_claim") and item.get("recomputed_commit") and item["commit_claim"]!=item["recomputed_commit"]: diagnostics.append(diagnostics_record(ReviewError("CONTRADICTION003","commit claim conflicts with recomputed state")))
        if item.get("claimed_fix_path") and item["claimed_fix_path"] not in {row["new_path"] for row in patch_records}: diagnostics.append(diagnostics_record(ReviewError("CONTRADICTION003","claimed fix path is absent from patch")))
        if item.get("noninterference") is True and item.get("current_production_artifact"): diagnostics.append(diagnostics_record(ReviewError("CONTRADICTION004","noninterference conflicts with current production artifact")))
        if item.get("blocking_diagnostics") and item.get("summary_diagnostics") is not None and not set(item["blocking_diagnostics"]).issubset(set(item["summary_diagnostics"])): diagnostics.append(diagnostics_record(ReviewError("SELF_CERTIFICATION003","package summary omits a blocking diagnostic")))
        if item.get("authoritative_package_verdict") is True: diagnostics.append(diagnostics_record(ReviewError("SELF_CERTIFICATION001","package verdict was asserted as authoritative")))
        if item.get("package_authored_verdict"): diagnostics.append(diagnostics_record(ReviewError("VERDICT001","package-authored verdict retained as nonauthoritative",field="package_authored_verdict")))
    return diagnostics

def derive_verdict(diagnostics, findings, unresolved_manual=False):
    ids={row["diagnostic_id"] for row in diagnostics if row.get("blocking",True)}
    if ids & {"PACKAGE001","PACKAGE002","PACKAGE003","PACKAGE004","ARTIFACT001"}: return "blocked_incomplete_package"
    if any(item.startswith("PROMPT") or item.startswith("GOVERNANCE") for item in ids): return "blocked_prompt_traceability"
    if any(item.startswith("BASELINE") for item in ids): return "blocked_baseline_mismatch"
    if any(item.startswith("PATCH") or item.startswith("SCOPE") for item in ids): return "blocked_patch_scope"
    if any(item.startswith(("TEST","PROBE","EVIDENCE")) for item in ids): return "blocked_validation_evidence"
    if unresolved_manual or any(item.startswith("GATE") for item in ids): return "blocked_declared_gate"
    if any(item.startswith(("CONTRADICTION","SELF_CERTIFICATION")) for item in ids): return "blocked_self_certification"
    if ids: return "blocked_review"
    if any(row.get("status")=="confirmed_new" and row.get("severity") in ("error","blocker") for row in findings): return "corrective_follow_up_required"
    if any(row.get("blocking") for row in findings):
        if any(row.get("status")=="package_claim_only" for row in findings): return "blocked_self_certification"
        return "blocked_review"
    if findings: return "accepted_with_nonblocking_findings"
    return "accepted"

def validate_verdict_precedence(claimed, derived):
    if claimed is not None and claimed!=derived: return diagnostics_record(ReviewError("VERDICT003","serialized verdict conflicts with reviewer derivation"))
    return None

def verdict_for_error(error):
    return derive_verdict([diagnostics_record(error)],[])

def review(manifest_path: Path, schema_path: Path, binding_path: Path, output_root: Path|None, validate_only=False):
    manifest=strict_json(strict_text(read_bytes(manifest_path),"SCHEMA001"),"SCHEMA001"); schema=strict_json(strict_text(read_bytes(schema_path),"SCHEMA001"),"SCHEMA001"); schema_keywords(schema); reject_reserved(manifest); validate_carrier_shape(manifest); schema_validate(manifest,schema,schema); unique_manifest_ids(manifest); validate_cross_records(manifest)
    binding=strict_json(strict_text(read_bytes(binding_path),"GOVERNANCE001"),"GOVERNANCE001"); workspace=Path(__file__).resolve().parents[4]
    validate_governance_binding(binding,workspace)
    check_prompt_traceability(manifest["authorizing_prompt"])
    limits={key:min(manifest["limits"][key],value) for key,value in HARD_LIMITS.items()}
    package=manifest["package"]; carrier=Path(package["carrier_path"]); root=normalize_relative(package["package_root"])
    if package["package_format"]=="extracted_directory": rows=directory_inventory(carrier,root,limits)
    elif package["package_format"]=="zip_archive":
        validate_identity(sha256_file_stream(carrier),package["carrier_sha256"])
        rows=zip_inventory(carrier,root,limits)
    else: raise ReviewError("PACKAGE001","unsupported carrier")
    validate_identity(inventory_hash(rows),package["package_inventory_sha256"])
    by_path={row["relative_path"]:row for row in rows}; parsed={}; diagnostics=[]
    declared_paths={normalize_relative(f"{root}/{record['relative_path']}") for record in manifest["artifacts"]}
    required_paths={normalize_relative(f"{root}/{record['relative_path']}") for record in manifest["artifacts"] if record["required"]}
    validate_artifact_set(declared_paths,set(by_path),required_paths)
    for record in manifest["artifacts"]:
        if record["parser"] not in MEDIA_PARSERS.get(record["media_type"],set()): raise ReviewError("ARTIFACT003","artifact media type and parser disagree",field=record["artifact_id"])
        path=normalize_relative(f"{root}/{record['relative_path']}")
        row=by_path.get(path)
        if row is None: continue
        validate_identity((row["size_bytes"],row["sha256"]),(record["size_bytes"],record["sha256"]),True,path)
        parsed[record["artifact_id"]]=parse_artifact(record,row["data"])
    validate_origins(parsed); findings=collect_findings(parsed,manifest["finding_policy"])
    patch_artifact=next((a for a in manifest["artifacts"] if a["artifact_id"]==manifest["patch_contract"]["artifact_id"]),None)
    if patch_artifact is None or patch_artifact["parser"] not in ("unified_diff","empty_file"): raise ReviewError("ARTIFACT003","patch contract does not select a patch artifact")
    patch_records=[]
    if patch_artifact:
        data=by_path[normalize_relative(f"{root}/{patch_artifact['relative_path']}")]["data"]
        patch_records=parse_patch(strict_text(data),manifest["patch_contract"])
    diagnostics.extend(validate_result_artifacts(manifest,parsed))
    observations=[verify_repository(repo,manifest["patch_contract"]) for repo in manifest["repositories"]]
    for observation in observations: diagnostics.extend(observation.diagnostics)
    if manifest["finding_policy"].get("package_claim_only_blocks_acceptance") and any(item.mode=="package_claim_only" for item in observations):
        diagnostics.append(diagnostics_record(ReviewError("SELF_CERTIFICATION002","package-only repository evidence cannot support acceptance")))
    unresolved_manual=False
    for gate in manifest["declared_gates"]:
        gate_diagnostics,gate_unresolved=evaluate_declared_gate(gate,parsed,patch_records,observations); diagnostics.extend(gate_diagnostics); unresolved_manual=unresolved_manual or gate_unresolved
    diagnostics.extend(detect_contradictions(parsed,patch_records)); diagnostics.sort(key=lambda row:(DIAGNOSTIC_IDS.index(row["diagnostic_id"]) if row["diagnostic_id"] in DIAGNOSTIC_IDS else 999,row.get("field","")))
    verdict=derive_verdict(diagnostics,findings,unresolved_manual)
    for value in parsed.values():
        if isinstance(value,dict) and "reviewer_verdict" in value:
            conflict=validate_verdict_precedence(value["reviewer_verdict"],verdict)
            if conflict: diagnostics.append(conflict); verdict=derive_verdict(diagnostics,findings,unresolved_manual)
    result={"reviewer_version":REVIEWER_VERSION,"schema_version":SCHEMA_VERSION,"manifest_version":MANIFEST_VERSION,"review_id":manifest["review_id"],"verdict":verdict,"diagnostics":diagnostics,"findings":findings,"package_inventory_sha256":inventory_hash(rows),"patch_paths":[r["new_path"] for r in patch_records]}
    if output_root is not None and not validate_only: publish_outputs(output_root,manifest,rows,result)
    return result

def publish_noreplace(source, target):
    import ctypes
    libc=ctypes.CDLL(None,use_errno=True); renameat2=getattr(libc,"renameat2",None)
    if renameat2 is None: raise ReviewError("RENDER001","no-replace publication primitive unavailable")
    renameat2.argtypes=(ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_uint)
    if renameat2(-100,os.fsencode(source),-100,os.fsencode(target),1)!=0: raise ReviewError("RENDER001","no-replace publication failed")

def publish_noreplace_at(parent_fd, source_name, target_name):
    import ctypes
    libc=ctypes.CDLL(None,use_errno=True); renameat2=getattr(libc,"renameat2",None)
    if renameat2 is None: raise ReviewError("RENDER001","no-replace publication primitive unavailable")
    renameat2.argtypes=(ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_uint)
    if renameat2(parent_fd,os.fsencode(source_name),parent_fd,os.fsencode(target_name),1)!=0: raise ReviewError("RENDER001","no-replace publication failed")

def write_exclusive_text(path, text):
    flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,"O_NOFOLLOW",0)
    descriptor=os.open(path,flags,0o600)
    with os.fdopen(descriptor,"w",encoding="utf-8",newline="") as handle:
        handle.write(text); handle.flush(); os.fsync(handle.fileno())

def _open_absolute_directory(path):
    if not path.is_absolute(): raise ReviewError("RENDER001","output parent must be absolute")
    descriptor=os.open("/",os.O_RDONLY|getattr(os,"O_DIRECTORY",0))
    try:
        for component in path.parts[1:]:
            child=_descriptor_open(component,os.O_RDONLY|getattr(os,"O_DIRECTORY",0),descriptor,"PATH004")
            os.close(descriptor); descriptor=child
        return descriptor
    except Exception:
        os.close(descriptor); raise

def _write_exclusive_at(directory_fd,name,text):
    descriptor=_descriptor_open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL,directory_fd,"RENDER001")
    with os.fdopen(descriptor,"w",encoding="utf-8",newline="") as handle:
        handle.write(text); handle.flush(); os.fsync(handle.fileno())

def _read_at(directory_fd,name):
    descriptor=_descriptor_open(name,os.O_RDONLY,directory_fd,"RENDER002")
    try: return _read_bounded(descriptor,HARD_LIMITS["maximum_member_uncompressed_bytes"],"RENDER002",name)
    finally: os.close(descriptor)

def _csv_text(fieldnames,rows):
    import io
    stream=io.StringIO(newline=""); writer=csv.DictWriter(stream,fieldnames=fieldnames); writer.writeheader(); writer.writerows(rows); return stream.getvalue()

def validate_generated_outputs(staging, rows, result):
    names={item.name for item in staging.iterdir()}
    if names!=set(OUTPUT_NAMES): raise ReviewError("RENDER002","generated artifact set is incomplete")
    resolved=json.loads(strict_text(read_bytes(staging/"review_manifest.resolved.json"),"RENDER002"))
    validation=json.loads(strict_text(read_bytes(staging/"review_validation.json"),"RENDER002"))
    plan=json.loads(strict_text(read_bytes(staging/"review_plan.json"),"RENDER002"))
    with (staging/"package_inventory.csv").open(encoding="utf-8",newline="") as handle: inventory=list(csv.DictReader(handle))
    with (staging/"review_findings.csv").open(encoding="utf-8",newline="") as handle: findings=list(csv.DictReader(handle))
    strict_text(read_bytes(staging/"review_report.md"),"RENDER002")
    if validation.get("verdict")!=result["verdict"] or validation.get("review_id")!=resolved.get("review_id"): raise ReviewError("RENDER002","generated verdict or review identity disagrees")
    if len(inventory)!=len(rows) or len(findings)!=len(result["findings"]): raise ReviewError("RENDER002","generated row count disagrees")
    if any(set(check).intersection(RESERVED_FIELDS) for check in plan.get("checks",[])): raise ReviewError("RENDER002","review plan contains a reserved runnable field")

def validate_generated_outputs_fd(staging_fd,rows,result):
    if set(os.listdir(staging_fd))!=set(OUTPUT_NAMES): raise ReviewError("RENDER002","generated artifact set is incomplete")
    resolved=strict_json(strict_text(_read_at(staging_fd,"review_manifest.resolved.json"),"RENDER002"),"RENDER002")
    validation=strict_json(strict_text(_read_at(staging_fd,"review_validation.json"),"RENDER002"),"RENDER002")
    plan=strict_json(strict_text(_read_at(staging_fd,"review_plan.json"),"RENDER002"),"RENDER002")
    inventory=list(csv.DictReader(strict_text(_read_at(staging_fd,"package_inventory.csv"),"RENDER002").splitlines()))
    findings=list(csv.DictReader(strict_text(_read_at(staging_fd,"review_findings.csv"),"RENDER002").splitlines()))
    report=strict_text(_read_at(staging_fd,"review_report.md"),"RENDER002")
    if validation.get("verdict")!=result["verdict"] or validation.get("review_id")!=resolved.get("review_id"): raise ReviewError("RENDER002","generated verdict or review identity disagrees")
    if len(inventory)!=len(rows) or len(findings)!=len(result["findings"]): raise ReviewError("RENDER002","generated row count disagrees")
    required=(result.get("review_id",resolved.get("review_id","")),result["verdict"],result.get("package_inventory_sha256",inventory_hash(rows)))
    if any(str(item) not in report for item in required): raise ReviewError("RENDER002","human report omits review identity")
    if any(set(check).intersection(RESERVED_FIELDS) for check in plan.get("checks",[])): raise ReviewError("RENDER002","review plan contains a reserved runnable field")

def publish_outputs(output_root,manifest,rows,result):
    output_root=Path(output_root)
    parent_fd=_open_absolute_directory(output_root.parent)
    staging_name=None; staging_fd=None
    try:
        if output_root.name in os.listdir(parent_fd): raise ReviewError("RENDER001","output root exists",path=str(output_root))
        for candidate in tempfile._get_candidate_names():
            staging_name=f".{output_root.name}.incomplete-{candidate}"
            try: os.mkdir(staging_name,0o700,dir_fd=parent_fd); break
            except FileExistsError: continue
        else: raise ReviewError("RENDER001","cannot allocate exclusive staging root")
        staging_fd=_descriptor_open(staging_name,os.O_RDONLY|getattr(os,"O_DIRECTORY",0),parent_fd,"PATH004")
        _write_exclusive_at(staging_fd,"review_manifest.resolved.json",json.dumps(manifest,indent=2,sort_keys=True)+"\n")
        inventory_fields=("relative_path","size_bytes","sha256")
        _write_exclusive_at(staging_fd,"package_inventory.csv",_csv_text(inventory_fields,({k:r[k] for k in inventory_fields} for r in rows)))
        finding_fields=("finding_id","category","severity","status","blocking")
        _write_exclusive_at(staging_fd,"review_findings.csv",_csv_text(finding_fields,({k:r.get(k,"") for k in finding_fields} for r in result["findings"])))
        _write_exclusive_at(staging_fd,"review_validation.json",json.dumps(result,indent=2,sort_keys=True)+"\n")
        diagnostic_ids=",".join(item["diagnostic_id"] for item in result.get("diagnostics",[]))
        finding_ids=",".join(item["finding_id"] for item in result.get("findings",[]))
        patch_paths=",".join(result.get("patch_paths",[]))
        report=(f"# Evidence package review\n\nReview ID: `{result.get('review_id',manifest.get('review_id',''))}`\n\nReviewer verdict: `{result['verdict']}`\n\nPackage inventory SHA-256: `{result.get('package_inventory_sha256',inventory_hash(rows))}`\n\nDiagnostics: `{diagnostic_ids}`\n\nFindings: `{finding_ids}`\n\nPatch paths: `{patch_paths}`\n")
        _write_exclusive_at(staging_fd,"review_report.md",report)
        plan={"checks":[{"check_id":c["check_id"],"required_evidence":c["required_evidence"],"owner":c["owner"],"state":c["state"]} for c in manifest["independent_checks"]]}
        _write_exclusive_at(staging_fd,"review_plan.json",json.dumps(plan,indent=2,sort_keys=True)+"\n")
        validate_generated_outputs_fd(staging_fd,rows,result)
        os.fsync(staging_fd); publish_noreplace_at(parent_fd,staging_name,output_root.name); staging_name=None
    except Exception:
        if staging_fd is not None and "INCOMPLETE_REVIEW.json" not in os.listdir(staging_fd): _write_exclusive_at(staging_fd,"INCOMPLETE_REVIEW.json",json.dumps({"diagnostic_id":"RENDER002","complete":False})+"\n")
        raise
    finally:
        if staging_fd is not None: os.close(staging_fd)
        os.close(parent_fd)

def parser():
    base=Path(__file__).resolve().parents[1]
    p=argparse.ArgumentParser(); p.add_argument("--schema",type=Path,default=base/"references/review_schema.json"); p.add_argument("--governance-binding",type=Path,default=base/"references/governance_binding.json"); p.add_argument("--format",choices=("human","json"),default="human"); p.add_argument("--json-out",type=Path); p.add_argument("--validate-only",action="store_true"); p.add_argument("--output-root",type=Path); p.add_argument("REVIEW_MANIFEST",type=Path); return p
def main(argv=None):
    args=parser().parse_args(argv)
    try: result=review(args.REVIEW_MANIFEST,args.schema,args.governance_binding,args.output_root,args.validate_only); code=0 if result["verdict"] in ("accepted","accepted_with_nonblocking_findings") else 6
    except ReviewError as exc: result={"reviewer_version":REVIEWER_VERSION,"verdict":verdict_for_error(exc),"diagnostics":[diagnostics_record(exc)]}; code=4 if exc.diagnostic_id.startswith("GOVERNANCE") else 5 if exc.diagnostic_id.startswith("RENDER") else 2 if exc.diagnostic_id.startswith("SCHEMA") else 3
    rendered=json.dumps(result,indent=2,sort_keys=True)+"\n" if args.format=="json" else "\n".join([f"reviewer_verdict: {result['verdict']}"]+[f"{d['diagnostic_id']}: {d['message']}" for d in result.get("diagnostics",[])])+"\n"
    sys.stdout.write(rendered)
    if args.json_out:
        if args.json_out.exists(): return 5
        try: write_exclusive_text(args.json_out,json.dumps(result,indent=2,sort_keys=True)+"\n")
        except (OSError,ReviewError): return 5
    return code
if __name__=="__main__": raise SystemExit(main())
