#!/usr/bin/env python3
"""Deterministic, inert evidence-package reviewer (version 1.0.0)."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import struct
import subprocess
import sys
import tempfile
import zipfile
import zlib

REVIEWER_VERSION = "1.0.0"
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
MEDIA_PARSERS = {
    "application/json": {"json"}, "text/csv": {"csv"},
    "text/markdown": {"markdown"}, "text/plain": {"text"},
    "text/x-diff": {"unified_diff", "empty_file"},
}

class ReviewError(Exception):
    def __init__(self, diagnostic_id: str, message: str, *, field: str = "", path: str = ""):
        super().__init__(message); self.diagnostic_id = diagnostic_id; self.message = message; self.field = field; self.path = path

def sha256_bytes(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def read_bytes(path: Path) -> bytes:
    with path.open("rb") as handle: return handle.read()
def strict_text(data: bytes, diagnostic_id: str = "SCHEMA002") -> str:
    if b"\x00" in data: raise ReviewError(diagnostic_id, "NUL or binary content is unsupported")
    try: return data.decode("utf-8", "strict")
    except UnicodeDecodeError as exc: raise ReviewError(diagnostic_id, "content is not strict UTF-8") from exc
def normalize_relative(value: str) -> str:
    if not isinstance(value, str) or not value or value.startswith("/") or "\\" in value or "\x00" in value: raise ReviewError("PATH001", "unsafe relative path", path=str(value))
    parts = value.split("/")
    if any(part in ("", ".", "..") for part in parts): raise ReviewError("PATH001", "unsafe path component", path=value)
    return "/".join(parts)
def key_token(value: str) -> str: return "_".join(value.lower().replace("-", "_").split("_"))
def reject_reserved(value, trail="$"):
    if isinstance(value, dict):
        for key, child in value.items():
            if key_token(str(key)) in RESERVED_FIELDS: raise ReviewError("SCHEMA003", "reserved capability-bearing field", field=f"{trail}.{key}")
            reject_reserved(child, f"{trail}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value): reject_reserved(child, f"{trail}[{index}]")

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
        if value < schema.get("minimum", float("-inf")) or value > schema.get("maximum", float("inf")): raise ReviewError("SCHEMA001", f"{trail} numeric limit invalid")
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

def directory_inventory(carrier: Path, package_root: str):
    if not carrier.is_absolute() or not carrier.is_dir(): raise ReviewError("PACKAGE001", "directory carrier must be an absolute existing directory")
    rows = []
    for root, dirs, files in os.walk(carrier, followlinks=False):
        dirs.sort(); files.sort()
        for name in dirs + files:
            path = Path(root) / name; info = path.lstat()
            if stat.S_ISLNK(info.st_mode) or not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)): raise ReviewError("PATH003", "link or special file encountered", path=str(path))
        for name in files:
            path = Path(root) / name; relative = normalize_relative(path.relative_to(carrier).as_posix())
            if relative.split("/", 1)[0] != package_root: raise ReviewError("PATH002", "member outside declared package root", path=relative)
            flags=os.O_RDONLY|getattr(os,"O_NOFOLLOW",0)
            descriptor=os.open(path,flags)
            try:
                first_stat=os.fstat(descriptor)
                if not stat.S_ISREG(first_stat.st_mode): raise ReviewError("PATH003","descriptor is not regular",path=relative)
                with os.fdopen(descriptor,"rb",closefd=False) as handle: data=handle.read()
            finally: os.close(descriptor)
            reopened=os.open(path,flags)
            try:
                second_stat=os.fstat(reopened)
                with os.fdopen(reopened,"rb",closefd=False) as handle: reopened_data=handle.read()
            finally: os.close(reopened)
            identity=(first_stat.st_dev,first_stat.st_ino,first_stat.st_size,first_stat.st_mtime_ns)
            reopened_identity=(second_stat.st_dev,second_stat.st_ino,second_stat.st_size,second_stat.st_mtime_ns)
            if identity!=reopened_identity or data!=reopened_data: raise ReviewError("HASH003","directory artifact changed during independent reopening",path=relative)
            rows.append({"relative_path": relative, "size_bytes": len(data), "sha256": sha256_bytes(data), "data": data})
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
        try: return json.loads(text)
        except json.JSONDecodeError as exc: raise ReviewError("SCHEMA002", "JSON parse failed") from exc
    if parser=="csv": return list(csv.DictReader(text.splitlines()))
    if parser in ("markdown","text"): return text
    if parser=="unified_diff": return parse_patch(text, None)
    raise ReviewError("SCHEMA003", "unsupported parser")

def parse_patch(text, contract):
    if "GIT binary patch" in text or "Binary files " in text or "Subproject commit " in text: raise ReviewError("PATCH002", "binary or submodule patch")
    records=[]; current=None
    for line in text.splitlines():
        if line.startswith("diff --git "):
            parts=line.split()
            if len(parts)!=4 or not parts[2].startswith("a/") or not parts[3].startswith("b/"): raise ReviewError("PATCH001", "malformed diff header")
            old=normalize_relative(parts[2][2:]); new=normalize_relative(parts[3][2:]); current={"old_path":old,"new_path":new,"hunks":[],"operations":[]}; records.append(current)
        elif line.startswith("@@"):
            if current is None or not line.endswith("@@") and " @@ " not in line: raise ReviewError("PATCH001", "malformed hunk")
            current["hunks"].append(line)
        elif line.startswith(("rename from ","rename to ","copy from ","copy to ","deleted file mode ","old mode ","new mode ")):
            if current is None: raise ReviewError("PATCH001", "patch metadata outside record")
            current["operations"].append(line.split()[0])
    if text and not records: raise ReviewError("PATCH001", "missing diff records")
    paths=[]; seen_paths=set()
    for record in records:
        record_paths={record["old_path"],record["new_path"]}
        if seen_paths.intersection(record_paths): raise ReviewError("SCOPE004", "duplicate normalized patch path")
        seen_paths.update(record_paths); paths.extend(record_paths)
    if contract:
        kind=contract["patch_kind"]
        if len(text.encode())>contract.get("maximum_patch_bytes",16777216) or len(text.splitlines())>contract.get("maximum_patch_lines",200000): raise ReviewError("PATCH001","patch ceiling exceeded")
        if contract["expected_empty"] != (text=="") or (kind=="empty_no_changes" and text!=""): raise ReviewError("PATCH003", "patch empty state disagrees")
        permission={"rename":contract["allow_renames"],"copy":contract["allow_copies"],"deleted":contract["allow_deletions"],"old":contract["allow_mode_changes"],"new":contract["allow_mode_changes"]}
        for record in records:
            if any(not permission.get(operation,False) for operation in record["operations"]): raise ReviewError("PATCH004","patch operation is not authorized")
        allowed=contract["allowed_paths"]; forbidden=contract["forbidden_paths"]
        for path in paths:
            if allowed and not any(path==item or path.startswith(item.rstrip("/")+"/") for item in allowed): raise ReviewError("SCOPE002", "patch path outside allowlist",path=path)
            if any(path==item or path.startswith(item.rstrip("/")+"/") for item in forbidden): raise ReviewError("SCOPE003", "patch path forbidden",path=path)
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
            if row["status"]=="confirmed_preexisting":
                permitted=row["category"] in finding_policy["allowed_nonblocking_preexisting_categories"]
                proven=row.get("reviewer_recomputed_pre_delta") is True and bool(row.get("pre_delta_evidence"))
                if not (permitted and proven): row=dict(row,blocking=True)
            findings.append(row)
    return findings

def check_prompt_traceability(record):
    prompt_path=Path(record["path"]); validation_path=Path(record["prompt_contract_validation_path"])
    if not prompt_path.is_absolute() or not validation_path.is_absolute(): raise ReviewError("PROMPT001","prompt paths must be absolute")
    prompt_data=read_bytes(prompt_path); validation_data=read_bytes(validation_path)
    if sha256_bytes(prompt_data)!=record["sha256"]: raise ReviewError("PROMPT001","authorizing prompt hash mismatch")
    if sha256_bytes(validation_data)!=record["prompt_contract_validation_sha256"]: raise ReviewError("PROMPT002","prompt validation artifact hash mismatch")
    validation=json.loads(strict_text(validation_data,"PROMPT002"))
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

def evaluate_gate(gate,parsed,patch_records,repositories):
    evaluator=gate["evaluator"]; accepted=gate["accepted_values"]
    if evaluator=="text_pattern_absent":
        for locator in gate["evidence_requirements"]:
            value=parsed.get(locator["artifact_id"])
            if not isinstance(value,str) or value.count(locator["locator_value"])!=0: return False
        return bool(gate["evidence_requirements"])
    observations=[locate(item,parsed,patch_records) for item in gate["evidence_requirements"]]
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
    if evaluator=="commit_subject_equals": return any(r.get("expected_commit_subject") in accepted for r in repositories)
    if evaluator=="repository_head_equals": return any(r.get("expected_head_after") in accepted for r in repositories)
    raise ReviewError("GATE001","unsupported gate evaluator")

def validate_origins(parsed):
    for value in parsed.values():
        rows=value.get("results",[]) if isinstance(value,dict) else value if isinstance(value,list) else []
        for row in rows:
            if isinstance(row,dict) and "origin" in row and row["origin"] not in VALIDATION_ORIGINS: raise ReviewError("SCHEMA003","validation origin is unsupported")

def verify_repository(repo, patch_contract):
    mode=repo["verification_mode"]
    if mode=="package_claim_only": return [diagnostics_record(ReviewError("EVIDENCE003","repository values remain package-authored claims",field=repo["repository_id"]))]
    if mode=="not_safely_generic": return [diagnostics_record(ReviewError("VERDICT002","repository state not safely generic",field=repo["repository_id"]))]
    if mode=="reviewer_recomputed_patch_and_baseline":
        if not repo.get("expected_head_before") or patch_contract.get("baseline_head")!=repo.get("expected_head_before"): return [diagnostics_record(ReviewError("BASELINE001","immutable patch baseline is missing or disagrees",field=repo["repository_id"]))]
        return []
    if mode=="reviewer_recomputed_live_read_only":
        path=Path(repo["repository_path"]); head=fixed_git(path,["rev-parse","HEAD"]); branch=fixed_git(path,["branch","--show-current"]); diagnostics=[]
        if head!=repo["expected_head_after"] or branch!=repo["expected_branch_after"]: diagnostics.append(diagnostics_record(ReviewError("BASELINE002","repository branch or HEAD mismatch",field=repo["repository_id"])))
        if repo.get("expected_commit_subject") and fixed_git(path,["log","-1","--format=%s"])!=repo["expected_commit_subject"]: diagnostics.append(diagnostics_record(ReviewError("BASELINE003","commit subject mismatch",field=repo["repository_id"])))
        return diagnostics
    raise ReviewError("SCHEMA003","unsupported repository verification mode")

def diagnostics_record(error):
    severity,blocking=NONBLOCKING_DIAGNOSTICS.get(error.diagnostic_id,("error",True))
    return {"diagnostic_id":error.diagnostic_id,"family":error.diagnostic_id.rstrip("0123456789"),"severity":severity,"blocking":blocking,"artifact_id":"","gate_or_finding_id":"","field":error.field,"safe_path":error.path,"message":error.message,"contract_locator":"SKILLS010_skill_contract.md"}

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
    if findings: return "accepted_with_nonblocking_findings"
    return "accepted"

def review(manifest_path: Path, schema_path: Path, binding_path: Path, output_root: Path|None, validate_only=False):
    manifest=json.loads(strict_text(read_bytes(manifest_path),"SCHEMA001")); schema=json.loads(strict_text(read_bytes(schema_path),"SCHEMA001")); reject_reserved(manifest); schema_validate(manifest,schema,schema); unique_manifest_ids(manifest)
    binding=json.loads(strict_text(read_bytes(binding_path),"GOVERNANCE001")); workspace=Path(__file__).resolve().parents[4]
    for key,name in (("agents_sha256","AGENTS.md"),("cpc_sha256","CPC.md")):
        bound=binding.get(key) or binding.get("governance",{}).get(key)
        if not bound: raise ReviewError("GOVERNANCE001",f"binding missing {key}")
        if sha256_bytes(read_bytes(workspace/name))!=bound: raise ReviewError("GOVERNANCE002",f"live {name} hash differs")
    check_prompt_traceability(manifest["authorizing_prompt"])
    limits={key:min(manifest["limits"][key],value) for key,value in HARD_LIMITS.items()}
    package=manifest["package"]; carrier=Path(package["carrier_path"]); root=normalize_relative(package["package_root"])
    if package["package_format"]=="extracted_directory": rows=directory_inventory(carrier,root)
    elif package["package_format"]=="zip_archive":
        if sha256_bytes(read_bytes(carrier))!=package["carrier_sha256"]: raise ReviewError("HASH001","ZIP carrier hash mismatch")
        rows=zip_inventory(carrier,root,limits)
    else: raise ReviewError("PACKAGE001","unsupported carrier")
    if inventory_hash(rows)!=package["package_inventory_sha256"]: raise ReviewError("HASH001","package inventory hash mismatch")
    by_path={row["relative_path"]:row for row in rows}; parsed={}; diagnostics=[]
    declared_paths={normalize_relative(f"{root}/{record['relative_path']}") for record in manifest["artifacts"]}
    undeclared=sorted(set(by_path)-declared_paths)
    if undeclared: raise ReviewError("PACKAGE004","package contains undeclared artifacts",path=undeclared[0])
    for record in manifest["artifacts"]:
        if record["parser"] not in MEDIA_PARSERS.get(record["media_type"],set()): raise ReviewError("ARTIFACT003","artifact media type and parser disagree",field=record["artifact_id"])
        path=normalize_relative(f"{root}/{record['relative_path']}")
        row=by_path.get(path)
        if row is None:
            if record["required"]: raise ReviewError("ARTIFACT001","required artifact missing",path=path)
            continue
        if row["size_bytes"]!=record["size_bytes"] or row["sha256"]!=record["sha256"]: raise ReviewError("HASH002","artifact identity mismatch",path=path)
        parsed[record["artifact_id"]]=parse_artifact(record,row["data"])
    validate_origins(parsed); findings=collect_findings(parsed,manifest["finding_policy"])
    patch_artifact=next((a for a in manifest["artifacts"] if a["artifact_id"]==manifest["patch_contract"]["artifact_id"]),None)
    if patch_artifact is None or patch_artifact["parser"] not in ("unified_diff","empty_file"): raise ReviewError("ARTIFACT003","patch contract does not select a patch artifact")
    patch_records=[]
    if patch_artifact:
        data=by_path[normalize_relative(f"{root}/{patch_artifact['relative_path']}")]["data"]
        patch_records=parse_patch(strict_text(data),manifest["patch_contract"])
    unresolved_manual=False
    for gate in manifest["declared_gates"]:
        if gate["evaluator"] not in GATE_EVALUATORS: raise ReviewError("GATE001","unknown gate evaluator")
        if gate["evaluator"]=="manual_reviewer_decision_required" and gate.get("manual_resolution") is None: unresolved_manual=True; diagnostics.append(diagnostics_record(ReviewError("GATE003","manual decision unresolved",field=gate["gate_id"])))
        elif gate["required"]:
            try: satisfied=evaluate_gate(gate,parsed,patch_records,manifest["repositories"])
            except ReviewError as exc: diagnostics.append(diagnostics_record(exc)); satisfied=False
            if not satisfied: diagnostics.append(diagnostics_record(ReviewError("GATE002","required gate is not satisfied",field=gate["gate_id"])))
    for repo in manifest["repositories"]:
        diagnostics.extend(verify_repository(repo,manifest["patch_contract"]))
    diagnostics.extend(detect_contradictions(parsed,patch_records)); diagnostics.sort(key=lambda row:(DIAGNOSTIC_IDS.index(row["diagnostic_id"]) if row["diagnostic_id"] in DIAGNOSTIC_IDS else 999,row.get("field","")))
    verdict=derive_verdict(diagnostics,findings,unresolved_manual)
    result={"reviewer_version":REVIEWER_VERSION,"schema_version":SCHEMA_VERSION,"manifest_version":MANIFEST_VERSION,"review_id":manifest["review_id"],"verdict":verdict,"diagnostics":diagnostics,"findings":findings,"package_inventory_sha256":inventory_hash(rows),"patch_paths":[r["new_path"] for r in patch_records]}
    if output_root is not None and not validate_only: publish_outputs(output_root,manifest,rows,result)
    return result

def publish_noreplace(source, target):
    import ctypes
    libc=ctypes.CDLL(None,use_errno=True); renameat2=getattr(libc,"renameat2",None)
    if renameat2 is None: raise ReviewError("RENDER001","no-replace publication primitive unavailable")
    renameat2.argtypes=(ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_uint)
    if renameat2(-100,os.fsencode(source),-100,os.fsencode(target),1)!=0: raise ReviewError("RENDER001","no-replace publication failed")

def write_exclusive_text(path, text):
    flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,"O_NOFOLLOW",0)
    descriptor=os.open(path,flags,0o600)
    with os.fdopen(descriptor,"w",encoding="utf-8",newline="") as handle:
        handle.write(text); handle.flush(); os.fsync(handle.fileno())

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

def publish_outputs(output_root,manifest,rows,result):
    output_root=Path(output_root)
    if output_root.exists(): raise ReviewError("RENDER001","output root exists",path=str(output_root))
    parent=output_root.parent
    if not parent.is_dir(): raise ReviewError("RENDER001","output parent missing")
    staging=Path(tempfile.mkdtemp(prefix=f".{output_root.name}.incomplete-",dir=parent))
    try:
        write_exclusive_text(staging/"review_manifest.resolved.json",json.dumps(manifest,indent=2,sort_keys=True)+"\n")
        with (staging/"package_inventory.csv").open("x",encoding="utf-8",newline="") as h:
            w=csv.DictWriter(h,fieldnames=("relative_path","size_bytes","sha256")); w.writeheader(); w.writerows({k:r[k] for k in w.fieldnames} for r in rows)
            h.flush(); os.fsync(h.fileno())
        with (staging/"review_findings.csv").open("x",encoding="utf-8",newline="") as h:
            fields=("finding_id","category","severity","status","blocking"); w=csv.DictWriter(h,fieldnames=fields); w.writeheader(); w.writerows({k:r.get(k,"") for k in fields} for r in result["findings"])
            h.flush(); os.fsync(h.fileno())
        write_exclusive_text(staging/"review_validation.json",json.dumps(result,indent=2,sort_keys=True)+"\n")
        write_exclusive_text(staging/"review_report.md",f"# Evidence package review\n\nReviewer verdict: `{result['verdict']}`\n")
        plan={"checks":[{"check_id":c["check_id"],"required_evidence":c["required_evidence"],"owner":c["owner"],"state":c["state"]} for c in manifest["independent_checks"]]}
        write_exclusive_text(staging/"review_plan.json",json.dumps(plan,indent=2,sort_keys=True)+"\n")
        validate_generated_outputs(staging,rows,result)
        publish_noreplace(staging,output_root)
    except Exception:
        marker=staging/"INCOMPLETE_REVIEW.json"
        if not marker.exists(): write_exclusive_text(marker,json.dumps({"diagnostic_id":"RENDER002","complete":False})+"\n")
        raise

def parser():
    base=Path(__file__).resolve().parents[1]
    p=argparse.ArgumentParser(); p.add_argument("--schema",type=Path,default=base/"references/review_schema.json"); p.add_argument("--governance-binding",type=Path,default=base/"references/governance_binding.json"); p.add_argument("--format",choices=("human","json"),default="human"); p.add_argument("--json-out",type=Path); p.add_argument("--validate-only",action="store_true"); p.add_argument("--output-root",type=Path); p.add_argument("REVIEW_MANIFEST",type=Path); return p
def main(argv=None):
    args=parser().parse_args(argv)
    try: result=review(args.REVIEW_MANIFEST,args.schema,args.governance_binding,args.output_root,args.validate_only); code=0 if result["verdict"] in ("accepted","accepted_with_nonblocking_findings") else 6
    except ReviewError as exc: result={"reviewer_version":REVIEWER_VERSION,"verdict":"blocked_review","diagnostics":[diagnostics_record(exc)]}; code=4 if exc.diagnostic_id.startswith("GOVERNANCE") else 5 if exc.diagnostic_id.startswith("RENDER") else 2 if exc.diagnostic_id.startswith("SCHEMA") else 3
    rendered=json.dumps(result,indent=2,sort_keys=True)+"\n" if args.format=="json" else "\n".join([f"reviewer_verdict: {result['verdict']}"]+[f"{d['diagnostic_id']}: {d['message']}" for d in result.get("diagnostics",[])])+"\n"
    sys.stdout.write(rendered)
    if args.json_out:
        if args.json_out.exists(): return 5
        try: write_exclusive_text(args.json_out,json.dumps(result,indent=2,sort_keys=True)+"\n")
        except (OSError,ReviewError): return 5
    return code
if __name__=="__main__": raise SystemExit(main())
