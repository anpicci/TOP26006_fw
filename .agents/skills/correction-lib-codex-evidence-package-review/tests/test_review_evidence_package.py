import csv
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import struct
import tempfile
import unittest
from unittest import mock
import zipfile
import subprocess

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "review_evidence_package.py"
SPEC = importlib.util.spec_from_file_location("evidence_reviewer", SCRIPT)
reviewer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reviewer)


class ContractTests(unittest.TestCase):
    def test_closed_counts(self):
        self.assertEqual(reviewer.REVIEWER_VERSION, "1.1.1")
        self.assertEqual(len(reviewer.DIAGNOSTIC_IDS), 63)
        self.assertEqual(len({item.rstrip("0123456789") for item in reviewer.DIAGNOSTIC_IDS}), 18)
        self.assertEqual(len(reviewer.PATCH_KINDS), 4)
        self.assertEqual(len(reviewer.LOCATOR_TYPES), 8)
        self.assertEqual(len(reviewer.GATE_EVALUATORS), 14)
        self.assertEqual(len(reviewer.VALIDATION_ORIGINS), 5)
        self.assertEqual(len(reviewer.SEVERITIES), 4)
        self.assertEqual(len(reviewer.FINDING_STATUSES), 7)
        self.assertEqual(len(reviewer.VERDICTS), 11)

    def test_schema_accepts_template(self):
        schema = json.loads((SKILL_ROOT / "references" / "review_schema.json").read_text())
        manifest = json.loads((SKILL_ROOT / "assets" / "review_manifest_template.json").read_text())
        reviewer.reject_reserved(manifest)
        reviewer.schema_validate(manifest, schema, schema)

    def test_prompt_semantics_are_not_closed_governance_vocabularies(self):
        schema = json.loads((SKILL_ROOT / "references" / "review_schema.json").read_text())
        prompt_mode = schema["$defs"]["authorizing_prompt"]["properties"]["expected_prompt_mode"]
        validation_ceiling = schema["$defs"]["authorizing_prompt"]["properties"]["expected_validation_ceiling"]
        self.assertEqual(prompt_mode["type"], "string")
        self.assertNotIn("enum", prompt_mode)
        self.assertEqual(validation_ceiling["type"], "string")
        self.assertNotIn("enum", validation_ceiling)
        self.assertEqual(
            set(schema["$defs"]["patch_kind"]["enum"]),
            {"prompt_local", "cumulative", "touched_file_cumulative", "empty_no_changes"},
        )
        self.assertEqual(set(reviewer.PATCH_KINDS), set(schema["$defs"]["patch_kind"]["enum"]))

    def test_recursive_additional_property(self):
        schema = json.loads((SKILL_ROOT / "references" / "review_schema.json").read_text())
        manifest = json.loads((SKILL_ROOT / "assets" / "review_manifest_template.json").read_text())
        manifest["package"]["surprise"] = True
        with self.assertRaisesRegex(reviewer.ReviewError, "additional"):
            reviewer.schema_validate(manifest, schema, schema)

    def test_every_reserved_capability(self):
        for key in reviewer.RESERVED_FIELDS:
            with self.subTest(key=key), self.assertRaises(reviewer.ReviewError) as caught:
                reviewer.reject_reserved({"nested": [{key: "inert"}]})
            self.assertEqual(caught.exception.diagnostic_id, "SCHEMA003")
        for key in ("testCommand","source-code","patchApply","githubAction","AUTO_FIX"):
            with self.subTest(variant=key), self.assertRaises(reviewer.ReviewError): reviewer.reject_reserved({key:"inert"})

    def test_cli_shape(self):
        actions = {action.dest for action in reviewer.parser()._actions}
        self.assertEqual(actions, {"help", "schema", "format", "json_out", "validate_only", "output_root", "REVIEW_MANIFEST"})
        self.assertTrue(actions.isdisjoint({"execute", "apply", "fix", "chain", "command", "shell", "argv"}))

    def test_human_json_diagnostic_equivalence(self):
        error = reviewer.ReviewError("PATH001", "unsafe")
        record = reviewer.diagnostics_record(error)
        human = f"{record['diagnostic_id']}: {record['message']}"
        parsed = json.loads(json.dumps(record))
        self.assertIn(parsed["diagnostic_id"], human)
        self.assertIn(parsed["message"], human)


class PathAndArchiveTests(unittest.TestCase):
    def test_path_rejections(self):
        for value in ("/abs", "../escape", "a/../b", "a/./b", "a//b", "a\\b", "a\x00b"):
            with self.subTest(value=value), self.assertRaises(reviewer.ReviewError) as caught:
                reviewer.normalize_relative(value)
            self.assertEqual(caught.exception.diagnostic_id, "PATH001")

    def test_directory_inventory_and_symlink(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); package = root / "pkg"; package.mkdir(); (package / "a.txt").write_text("safe")
            rows = reviewer.directory_inventory(root, "pkg")
            self.assertEqual(rows[0]["relative_path"], "pkg/a.txt")
            link = package / "link"; link.symlink_to(package / "a.txt")
            with self.assertRaises(reviewer.ReviewError) as caught: reviewer.directory_inventory(root, "pkg")
            self.assertEqual(caught.exception.diagnostic_id, "PATH003")

    def make_zip(self, path, members):
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, data in members: archive.writestr(name, data)

    def test_safe_zip(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "safe.zip"; self.make_zip(path, [("pkg/a.txt", b"safe")])
            rows = reviewer.zip_inventory(path, "pkg", reviewer.HARD_LIMITS)
            self.assertEqual(rows[0]["data"], b"safe")

    def test_safe_directory_zip_logical_equivalence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)/"directory"; package=root/"pkg"; package.mkdir(parents=True); (package/"a.txt").write_bytes(b"safe")
            archive=Path(temporary)/"safe.zip"; self.make_zip(archive,[("pkg/a.txt",b"safe")])
            directory_rows=reviewer.directory_inventory(root,"pkg"); zip_rows=reviewer.zip_inventory(archive,"pkg",reviewer.HARD_LIMITS)
            self.assertEqual(reviewer.inventory_hash(directory_rows),reviewer.inventory_hash(zip_rows))

    def test_zip_duplicate_and_casefold(self):
        with tempfile.TemporaryDirectory() as temporary:
            duplicate = Path(temporary) / "duplicate.zip"
            with zipfile.ZipFile(duplicate, "w") as archive:
                with self.assertWarns(UserWarning):
                    archive.writestr("pkg/a", b"1"); archive.writestr("pkg/a", b"2")
            with self.assertRaises(reviewer.ReviewError) as caught: reviewer.zip_inventory(duplicate, "pkg", reviewer.HARD_LIMITS)
            self.assertEqual(caught.exception.diagnostic_id, "ARCHIVE004")
            folded = Path(temporary) / "folded.zip"; self.make_zip(folded, [("pkg/A", b"1"), ("pkg/a", b"2")])
            with self.assertRaises(reviewer.ReviewError) as caught: reviewer.zip_inventory(folded, "pkg", reviewer.HARD_LIMITS)
            self.assertEqual(caught.exception.diagnostic_id, "ARCHIVE005")

    def test_zip_multiple_root_nested_and_backslash(self):
        cases = [([("one/a", b"1"), ("two/b", b"2")], "PATH002"), ([("pkg/a.zip", b"x")], "ARCHIVE007"), ([("pkg\\a", b"x")], "PATH001")]
        with tempfile.TemporaryDirectory() as temporary:
            for index, (members, expected) in enumerate(cases):
                path = Path(temporary) / f"case{index}.zip"; self.make_zip(path, members)
                with self.subTest(expected=expected), self.assertRaises(reviewer.ReviewError) as caught: reviewer.zip_inventory(path, "pkg", reviewer.HARD_LIMITS)
                self.assertEqual(caught.exception.diagnostic_id, expected)

    def test_zip_symlink(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "link.zip"
            info = zipfile.ZipInfo("pkg/link"); info.create_system = 3; info.external_attr = (stat.S_IFLNK | 0o777) << 16
            with zipfile.ZipFile(path, "w") as archive: archive.writestr(info, "target")
            with self.assertRaises(reviewer.ReviewError) as caught: reviewer.zip_inventory(path, "pkg", reviewer.HARD_LIMITS)
            self.assertEqual(caught.exception.diagnostic_id, "PATH003")

    def test_zip_limits_and_tightening(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "limit.zip"; self.make_zip(path, [("pkg/a", b"1234")])
            limits = dict(reviewer.HARD_LIMITS); limits["maximum_member_uncompressed_bytes"] = 3
            with self.assertRaises(reviewer.ReviewError) as caught: reviewer.zip_inventory(path, "pkg", limits)
            self.assertEqual(caught.exception.diagnostic_id, "ARCHIVE002")

    def test_local_header_mismatch(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "header.zip"; self.make_zip(path, [("pkg/a", b"safe")])
            data = bytearray(path.read_bytes()); data[30] = ord("q"); path.write_bytes(data)
            with self.assertRaises(reviewer.ReviewError) as caught: reviewer.zip_inventory(path, "pkg", reviewer.HARD_LIMITS)
            self.assertEqual(caught.exception.diagnostic_id, "ARCHIVE008")


class PatchLocatorGateTests(unittest.TestCase):
    PATCH = "diff --git a/src/a.py b/src/a.py\n--- a/src/a.py\n+++ b/src/a.py\n@@ -1 +1 @@\n-old\n+new\n"

    def contract(self, kind="prompt_local"):
        return {"patch_kind": kind, "allowed_paths": ["src"], "forbidden_paths": ["secret"], "expected_empty": kind == "empty_no_changes", "allow_renames": False, "allow_copies": False, "allow_mode_changes": False, "allow_deletions": False}

    def test_all_patch_kinds(self):
        for kind in reviewer.PATCH_KINDS:
            text = "" if kind == "empty_no_changes" else self.PATCH
            records = reviewer.parse_patch(text, self.contract(kind))
            self.assertEqual(bool(records), bool(text))

    def test_patch_rejections(self):
        cases = [("GIT binary patch\n", "PATCH002"), ("diff --git /x /y\n", "PATCH001"), (self.PATCH.replace("src/a.py", "outside/a.py"), "SCOPE002"), (self.PATCH.replace("src/a.py", "secret/a.py"), "SCOPE002")]
        for text, expected in cases:
            with self.subTest(expected=expected), self.assertRaises(reviewer.ReviewError): reviewer.parse_patch(text, self.contract())

    def test_patch_operations_require_permission(self):
        text = "diff --git a/src/a b/src/b\nrename from src/a\nrename to src/b\n"
        with self.assertRaises(reviewer.ReviewError) as caught: reviewer.parse_patch(text, self.contract())
        self.assertEqual(caught.exception.diagnostic_id, "PATCH004")

    def test_all_locator_types(self):
        patch = reviewer.parse_patch(self.PATCH, None)
        parsed = {"md": "# Title\nbody", "csv": [{"id":"one","value":"ok"}], "json": {"a": 1}, "text": "literal", "patch": patch, "tests": [{"name":"named","status":"pass"}], "probes": [{"name":"probe","value":1}]}
        locators = [("markdown_section","md","title"),("csv_row","csv","id=one"),("json_pointer","json","/a"),("text_pattern","text","literal"),("file_whole","text","whole"),("patch_hunk","patch","src/a.py->src/a.py:@@ -1 +1 @@"),("test_name","tests","named"),("probe_name","probes","probe")]
        for kind, artifact, token in locators:
            locator = {"artifact_id":artifact,"locator_type":kind,"locator_value":token,"expected_hash_or_value":None}
            with self.subTest(kind=kind): self.assertIsNotNone(reviewer.locate(locator, parsed, patch))

    def test_all_gate_evaluators_are_closed(self):
        self.assertEqual(set(reviewer.GATE_EVALUATORS), {"artifact_present","hash_equals","json_pointer_equals","json_pointer_in_set","csv_row_count","csv_value_equals","text_pattern_present","text_pattern_absent","test_summary_equals","probe_field_equals","patch_path_subset","commit_subject_equals","repository_head_equals","manual_reviewer_decision_required"})

    def test_manual_gate(self):
        gate = {"evaluator":"manual_reviewer_decision_required","manual_resolution":None,"evidence_requirements":[],"accepted_values":[True]}
        self.assertFalse(reviewer.evaluate_gate(gate, {}, [], []))
        locator={"artifact_id":"decision","locator_type":"text_pattern","locator_value":"approved","expected_hash_or_value":"approved","observed_hash_or_value":"approved","reviewer_recomputed":True}
        gate["manual_resolution"] = {"decision": True,"reviewer":"reviewer","evidence_locator":locator}
        self.assertTrue(reviewer.evaluate_gate(gate, {"decision":"approved"}, [], []))


class VerdictRenderSafetyTests(unittest.TestCase):
    def test_all_verdicts_reachable_by_closed_derivation(self):
        observed = {reviewer.derive_verdict([], []), reviewer.derive_verdict([], [{"status":"confirmed_preexisting"}]), reviewer.derive_verdict([], [{"status":"confirmed_new","severity":"error"}])}
        for diagnostic in ("PACKAGE001","PROMPT001","BASELINE001","PATCH001","TEST001","GATE001","SELF_CERTIFICATION001","SCHEMA001"):
            observed.add(reviewer.derive_verdict([{"diagnostic_id":diagnostic}], []))
        self.assertEqual(observed, set(reviewer.VERDICTS))

    def test_contradiction_patterns(self):
        parsed = {"one":{"report_status":"pass","failed":1},"two":{"summary_count":2,"details":[1]},"three":{"no_changes":True},"four":{"noninterference":True,"current_production_artifact":"x"},"five":{"package_authored_verdict":"accepted"}}
        ids = {row["diagnostic_id"] for row in reviewer.detect_contradictions(parsed,[{"new_path":"x"}])}
        self.assertEqual(ids,{"CONTRADICTION001","CONTRADICTION002","CONTRADICTION003","CONTRADICTION004","VERDICT001"})

    def test_no_replace_publication(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "output"; target.mkdir()
            with self.assertRaises(reviewer.ReviewError) as caught: reviewer.publish_outputs(target, {}, [], {"findings":[],"verdict":"accepted"})
            self.assertEqual(caught.exception.diagnostic_id,"RENDER001")

    def test_incomplete_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "output"
            result={"review_id":"review","findings":[],"verdict":"accepted","diagnostics":[],"package_inventory_sha256":reviewer.inventory_hash([]),"patch_paths":[]}
            with mock.patch.object(reviewer, "publish_noreplace_at", side_effect=OSError):
                with self.assertRaises(Exception): reviewer.publish_outputs(target, {"review_id":"review","independent_checks":[]}, [], result)
            incomplete = list(Path(temporary).glob(".output.incomplete-*/INCOMPLETE_REVIEW.json"))
            self.assertEqual(len(incomplete), 1)

    def test_no_package_execution_boundaries(self):
        source = SCRIPT.read_text()
        forbidden = ("eval(", "exec(", "os.system", "shell=True", "git apply", "subprocess.call", "subprocess.Popen", "importlib.import_module")
        for token in forbidden: self.assertNotIn(token, source)
        with mock.patch("subprocess.Popen", side_effect=AssertionError("execution attempted")), mock.patch("subprocess.call", side_effect=AssertionError("execution attempted")):
            reviewer.reject_reserved({"safe": "data"})

    def test_plan_has_no_runnable_fields(self):
        checks = [{"check_id":"check","required_evidence":["evidence"],"owner":"user","state":"planned_but_not_run_check"}]
        plan = {"checks":[{key:item[key] for key in ("check_id","required_evidence","owner","state")} for item in checks]}
        self.assertTrue(set(plan["checks"][0]).isdisjoint({"command","argv","shell","script","activation"}))


class ExtendedContractTests(unittest.TestCase):
    PATCH = PatchLocatorGateTests.PATCH

    def locator(self, artifact, kind, token, expected=None):
        return {"artifact_id":artifact,"locator_type":kind,"locator_value":token,"expected_hash_or_value":expected,"observed_hash_or_value":expected,"reviewer_recomputed":True}

    def test_all_artifact_parsers_and_media_pairs(self):
        records=[
            ({"parser":"json","media_type":"application/json"},b'{"a":1}\n'),
            ({"parser":"csv","media_type":"text/csv"},b'id,value\none,ok\n'),
            ({"parser":"markdown","media_type":"text/markdown"},b'# Heading\n'),
            ({"parser":"text","media_type":"text/plain"},b'plain\n'),
            ({"parser":"unified_diff","media_type":"text/x-diff"},self.PATCH.encode()),
            ({"parser":"empty_file","media_type":"text/x-diff"},b''),
        ]
        for record,data in records:
            with self.subTest(parser=record["parser"]): reviewer.parse_artifact(record,data)
        with self.assertRaisesRegex(reviewer.ReviewError,"media type"):
            reviewer.parse_artifact({"parser":"json","media_type":"text/plain"},b'{}')
        for data in (b'\xff',b'abc\x00def'):
            with self.assertRaises(reviewer.ReviewError): reviewer.parse_artifact({"parser":"text","media_type":"text/plain"},data)

    def test_unique_manifest_ids_and_paths(self):
        manifest={"repositories":[{"repository_id":"same"},{"repository_id":"same"}],"artifacts":[],"declared_gates":[],"independent_checks":[]}
        with self.assertRaises(reviewer.ReviewError): reviewer.unique_manifest_ids(manifest)
        manifest={"repositories":[{"repository_id":"one"}],"artifacts":[{"artifact_id":"a","relative_path":"x"},{"artifact_id":"b","relative_path":"x"}],"declared_gates":[],"independent_checks":[]}
        with self.assertRaises(reviewer.ReviewError): reviewer.unique_manifest_ids(manifest)

    def test_directory_independent_reopen_change(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); package=root/"pkg"; package.mkdir(); target=package/"a.txt"; target.write_text("first")
            real_open=reviewer._descriptor_open; calls=0
            def changed(path, flags, parent_fd, diagnostic_id="PATH004"):
                nonlocal calls
                if path=="a.txt":
                    calls+=1
                    if calls==2: target.write_text("second")
                return real_open(path,flags,parent_fd,diagnostic_id)
            with mock.patch.object(reviewer,"_descriptor_open",side_effect=changed), self.assertRaises(reviewer.ReviewError) as caught:
                reviewer.directory_inventory(root,"pkg")
            self.assertEqual(caught.exception.diagnostic_id,"HASH003")

    def test_zip_encryption_and_unsupported_feature(self):
        with tempfile.TemporaryDirectory() as temporary:
            encrypted=Path(temporary)/"encrypted.zip"
            with zipfile.ZipFile(encrypted,"w") as archive: archive.writestr("pkg/a",b"x")
            data=bytearray(encrypted.read_bytes()); central=data.index(b"PK\x01\x02")
            for offset in (6,central+8): data[offset]|=1
            encrypted.write_bytes(data)
            with self.assertRaises(reviewer.ReviewError) as caught: reviewer.zip_inventory(encrypted,"pkg",reviewer.HARD_LIMITS)
            self.assertEqual(caught.exception.diagnostic_id,"ARCHIVE006")
            feature=Path(temporary)/"feature.zip"; info=zipfile.ZipInfo("pkg/a"); info.extra=b"\x99\x99\x00\x00"
            with zipfile.ZipFile(feature,"w") as archive: archive.writestr(info,b"x")
            with self.assertRaises(reviewer.ReviewError) as caught: reviewer.zip_inventory(feature,"pkg",reviewer.HARD_LIMITS)
            self.assertEqual(caught.exception.diagnostic_id,"ARCHIVE006")

    def test_zip_stream_corruption(self):
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/"corrupt.zip"
            with zipfile.ZipFile(path,"w",zipfile.ZIP_DEFLATED) as archive: archive.writestr("pkg/a",b"stream bytes")
            data=bytearray(path.read_bytes()); name_length=struct.unpack_from("<H",data,26)[0]; extra_length=struct.unpack_from("<H",data,28)[0]
            payload=30+name_length+extra_length; data[payload]^=0xff; path.write_bytes(data)
            with self.assertRaises(reviewer.ReviewError) as caught: reviewer.zip_inventory(path,"pkg",reviewer.HARD_LIMITS)
            self.assertEqual(caught.exception.diagnostic_id,"ARCHIVE008")

    def test_patch_all_operations_allowed_and_duplicate_records(self):
        samples={
            "allow_renames":"diff --git a/src/a b/src/b\nrename from src/a\nrename to src/b\n",
            "allow_copies":"diff --git a/src/a b/src/b\ncopy from src/a\ncopy to src/b\n",
            "allow_deletions":"diff --git a/src/a b/src/a\ndeleted file mode 100644\n",
            "allow_mode_changes":"diff --git a/src/a b/src/a\nold mode 100644\nnew mode 100755\n",
        }
        base={"patch_kind":"prompt_local","allowed_paths":["src"],"forbidden_paths":[],"expected_empty":False,"allow_renames":False,"allow_copies":False,"allow_deletions":False,"allow_mode_changes":False}
        for permission,text in samples.items():
            contract=dict(base); contract[permission]=True
            with self.subTest(permission=permission): self.assertTrue(reviewer.parse_patch(text,contract))
        duplicate=self.PATCH+self.PATCH
        with self.assertRaises(reviewer.ReviewError) as caught: reviewer.parse_patch(duplicate,base)
        self.assertEqual(caught.exception.diagnostic_id,"SCOPE004")

    def test_locator_failures_and_literal_pattern(self):
        parsed={"text":"a.c a-c","json":{"a":1}}
        with self.assertRaises(reviewer.ReviewError): reviewer.locate(self.locator("text","text_pattern","a.*c"),parsed,[])
        with self.assertRaises(reviewer.ReviewError): reviewer.locate(self.locator("text","text_pattern","a.c","wrong"),parsed,[])
        with self.assertRaises(reviewer.ReviewError): reviewer.locate(self.locator("missing","file_whole","whole"),parsed,[])

    def test_all_gate_evaluators_positive_and_negative(self):
        test_row={"name":"suite","status":"pass","origin":"independent_external_test_result"}; probe_row={"name":"probe","value":1,"origin":"reviewer_recomputed_builtin_check"}
        parsed={"text":"present","json":{"value":"ok"},"csv":[{"id":"one","value":"ok"}],"tests":[test_row],"probes":[probe_row]}
        patch=reviewer.parse_patch(self.PATCH,None); repos=[reviewer.RepositoryObservation("repo","reviewer_recomputed_live_read_only",True,observed_head="head",observed_subject="subject")]
        cases=[
            ("artifact_present",[self.locator("text","text_pattern","present","present")],["present"],None),
            ("hash_equals",[self.locator("json","json_pointer","/value","ok")],["ok"],None),
            ("json_pointer_equals",[self.locator("json","json_pointer","/value","ok")],["ok"],None),
            ("json_pointer_in_set",[self.locator("json","json_pointer","/value","ok")],["ok","other"],None),
            ("csv_row_count",[self.locator("csv","csv_row","id=one",{"id":"one","value":"ok"})],[1],1),
            ("csv_value_equals",[self.locator("csv","csv_row","id=one",{"id":"one","value":"ok"})],[{"id":"one","value":"ok"}],None),
            ("text_pattern_present",[self.locator("text","text_pattern","present","present")],[True],None),
            ("text_pattern_absent",[{**self.locator("text","text_pattern","absent"),"observed_hash_or_value":None}],[True],None),
            ("test_summary_equals",[self.locator("tests","test_name","suite",test_row)],[test_row],None),
            ("probe_field_equals",[self.locator("probes","probe_name","probe",probe_row)],[probe_row],None),
            ("patch_path_subset",[],["src/a.py"],None),
            ("commit_subject_equals",[],["subject"],None),
            ("repository_head_equals",[],["head"],None),
        ]
        for evaluator,evidence,accepted,count in cases:
            gate={"evaluator":evaluator,"evidence_requirements":evidence,"accepted_values":accepted,"expected_count":count}
            with self.subTest(evaluator=evaluator): self.assertTrue(reviewer.evaluate_gate(gate,parsed,patch,repos))
        bad={"evaluator":"hash_equals","evidence_requirements":[self.locator("json","json_pointer","/value","ok")],"accepted_values":["bad"],"expected_count":None}
        self.assertFalse(reviewer.evaluate_gate(bad,parsed,patch,repos))

    def test_validation_origins_closed(self):
        reviewer.validate_origins({"results":[{"origin":value} for value in reviewer.VALIDATION_ORIGINS]})
        with self.assertRaises(reviewer.ReviewError): reviewer.validate_origins({"results":[{"origin":"package_command"}]})

    def test_finding_statuses_severities_and_preexisting_proof(self):
        rows=[]
        for index,status in enumerate(reviewer.FINDING_STATUSES):
            rows.append({"finding_id":f"finding_{index}","category":"known","severity":reviewer.SEVERITIES[index%4],"status":status,"blocking":False,"reviewer_recomputed_pre_delta":status=="confirmed_preexisting","pre_delta_evidence":["evidence"] if status=="confirmed_preexisting" else []})
        findings=reviewer.collect_findings({"evidence":{"findings":rows}},{"allowed_nonblocking_preexisting_categories":["known"]})
        self.assertEqual({row["status"] for row in findings},set(reviewer.FINDING_STATUSES))
        unproven=dict(rows[1],finding_id="unproven",reviewer_recomputed_pre_delta=False,pre_delta_evidence=[])
        result=reviewer.collect_findings({"evidence":{"findings":[unproven]}},{"allowed_nonblocking_preexisting_categories":["known"]})
        self.assertTrue(result[0]["blocking"])

    def test_all_contradiction_patterns_and_secondary_visibility(self):
        parsed={
            "report":{"report_status":"pass","failed":1,"package_authored_verdict":"accepted"},
            "summary":{"summary_count":2,"details":[1],"blocking_diagnostics":["GATE002"],"summary_diagnostics":[]},
            "hash":{"declared_hash":"a","actual_hash":"b"},
            "commit":{"commit_claim":"a","recomputed_commit":"b"},
            "change":{"no_changes":True,"claimed_fix_path":"missing"},
            "production":{"noninterference":True,"current_production_artifact":"declared"},
        }
        diagnostics=reviewer.detect_contradictions(parsed,reviewer.parse_patch(self.PATCH,None))
        ids=[row["diagnostic_id"] for row in diagnostics]
        for expected in ("CONTRADICTION001","CONTRADICTION002","CONTRADICTION003","CONTRADICTION004","SELF_CERTIFICATION003","VERDICT001"): self.assertIn(expected,ids)
        self.assertEqual(reviewer.derive_verdict(diagnostics,[]),"blocked_self_certification")
        self.assertGreaterEqual(ids.count("CONTRADICTION003"),4)

    def test_generated_outputs_reopened_and_no_replace(self):
        with tempfile.TemporaryDirectory() as temporary:
            target=Path(temporary)/"review"
            manifest={"review_id":"review","independent_checks":[{"check_id":"check","required_evidence":["evidence"],"owner":"user","state":"planned_but_not_run_check"}]}
            rows=[{"relative_path":"pkg/a","size_bytes":1,"sha256":reviewer.sha256_bytes(b"x"),"data":b"x"}]
            result={"review_id":"review","findings":[],"verdict":"accepted","diagnostics":[],"package_inventory_sha256":reviewer.inventory_hash(rows),"patch_paths":[]}
            reviewer.publish_outputs(target,manifest,rows,result)
            self.assertEqual({item.name for item in target.iterdir()},set(reviewer.OUTPUT_NAMES))
            reviewer.validate_generated_outputs(target,rows,result)
            with self.assertRaises(reviewer.ReviewError): reviewer.publish_outputs(target,manifest,rows,result)

    def test_prompt_traceability_optional_helper_and_semantic_compatibility(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); prompt=root/"prompt.md"; validation=root/"validation.json"
            prompt.write_text("prompt_id: TEST\nprompt_mode: validation_only\nvalidation_ceiling: static_inspection_only\npatch_kind_expected: empty_no_changes\ncommit_expected: no\ndo_not_commit: yes\nallowed/path\nreviewed_code_execution: no\n")
            prompt_hash=reviewer.sha256_bytes(prompt.read_bytes())
            payload={"input":{"sha256":prompt_hash},"producer":{"name":"compatible-helper","version":"9.7.3"},"capabilities":{"mechanical_validity":True,"internal_consistency":True},"unknown_future_field":{"accepted":True}}
            validation.write_text(json.dumps(payload))
            record={"path":str(prompt),"sha256":prompt_hash,"expected_prompt_id":"TEST","expected_prompt_mode":"validation_only","expected_commit_policy":{"commit_expected":False,"do_not_commit":True,"expected_subject":None},"expected_allowed_paths":["allowed/path"],"expected_forbidden_actions":["reviewed_code_execution"],"expected_validation_ceiling":"static_inspection_only","expected_patch_kind":"empty_no_changes"}
            with mock.patch("subprocess.run",side_effect=AssertionError("prompt validator invoked")):
                self.assertFalse(reviewer.check_prompt_traceability(record)["helper_result_supplied"])
            record.update({"prompt_helper_result_path":str(validation),"prompt_helper_result_sha256":reviewer.sha256_bytes(validation.read_bytes()),"required_helper_capabilities":["mechanical_validity","internal_consistency"]})
            self.assertEqual(reviewer.check_prompt_traceability(record)["producer"]["version"],"9.7.3")
            payload["input"]["sha256"]="0"*64; validation.write_text(json.dumps(payload)); record["prompt_helper_result_sha256"]=reviewer.sha256_bytes(validation.read_bytes())
            with self.assertRaises(reviewer.ReviewError): reviewer.check_prompt_traceability(record)
            payload["input"]["sha256"]=prompt_hash; payload["capabilities"].pop("internal_consistency"); validation.write_text(json.dumps(payload)); record["prompt_helper_result_sha256"]=reviewer.sha256_bytes(validation.read_bytes())
            with self.assertRaises(reviewer.ReviewError): reviewer.check_prompt_traceability(record)

    def test_end_to_end_directory_review_and_generated_artifacts(self):
        workspace=SCRIPT.resolve().parents[4]
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); carrier=root/"carrier"; package=carrier/"package_root"; package.mkdir(parents=True); (package/"empty.patch").write_bytes(b"")
            prompt=root/"prompt.md"; manifest_path=root/"manifest.json"; output=root/"output"
            prompt.write_text("prompt_id: TEST\nprompt_mode: validation_only\nvalidation_ceiling: static_inspection_only\npatch_kind_expected: empty_no_changes\ncommit_expected: no\ndo_not_commit: yes\nallowed/path\nreviewed_code_execution: no\n")
            prompt_hash=reviewer.sha256_bytes(prompt.read_bytes())
            manifest=json.loads((SKILL_ROOT/"assets/review_manifest_template.json").read_text())
            manifest["review_id"]="review"; manifest["authorizing_prompt"].update({"path":str(prompt),"sha256":prompt_hash,"expected_prompt_id":"TEST","expected_allowed_paths":["allowed/path"],"expected_forbidden_actions":["reviewed_code_execution"]})
            manifest["repositories"][0]["repository_path"]=str(workspace)
            baseline="1"*64
            manifest["repositories"][0].update({"verification_mode":"reviewer_recomputed_patch_and_baseline","expected_head_before":baseline})
            manifest["patch_contract"]["baseline_head"]=baseline
            manifest["package"].update({"carrier_path":str(carrier),"package_inventory_sha256":reviewer.inventory_hash(reviewer.directory_inventory(carrier,"package_root"))})
            manifest_path.write_text(json.dumps(manifest))
            result=reviewer.review(manifest_path,SKILL_ROOT/"references/review_schema.json",output)
            self.assertEqual(result["verdict"],"accepted")
            self.assertEqual(result["diagnostics"],[])
            reviewer.validate_generated_outputs(output,reviewer.directory_inventory(carrier,"package_root"),result)

    def test_fixed_git_read_only_and_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo=Path(temporary)/"repo"; repo.mkdir()
            subprocess.run(["git","init","-b","main"],cwd=repo,check=True,capture_output=True)
            (repo/"file.txt").write_text("data")
            subprocess.run(["git","add","file.txt"],cwd=repo,check=True,capture_output=True)
            subprocess.run(["git","-c","user.name=Test","-c","user.email=test@example.invalid","commit","-m","subject"],cwd=repo,check=True,capture_output=True)
            before=(subprocess.run(["git","rev-parse","HEAD"],cwd=repo,text=True,capture_output=True,check=True).stdout,subprocess.run(["git","status","--porcelain"],cwd=repo,text=True,capture_output=True,check=True).stdout,(repo/".git/index").read_bytes())
            self.assertEqual(reviewer.fixed_git(repo,["branch","--show-current"]),"main")
            self.assertEqual(reviewer.fixed_git(repo,["log","-1","--format=%s"]),"subject")
            with self.assertRaises(reviewer.ReviewError): reviewer.fixed_git(repo,["checkout","other"])
            head=reviewer.fixed_git(repo,["rev-parse","HEAD"])
            base={"repository_id":"repo","repository_path":str(repo),"expected_head_before":head,"expected_head_after":head,"expected_branch_after":"main","expected_commit_subject":"subject"}
            modes={
                "package_claim_only":"EVIDENCE003",
                "reviewer_recomputed_live_read_only":None,
                "reviewer_recomputed_patch_and_baseline":None,
                "not_safely_generic":"VERDICT002",
            }
            for mode,expected in modes.items():
                observation=reviewer.verify_repository(dict(base,verification_mode=mode),{"baseline_head":head})
                with self.subTest(mode=mode): self.assertEqual(observation.diagnostics[0]["diagnostic_id"] if observation.diagnostics else None,expected)
            after=(subprocess.run(["git","rev-parse","HEAD"],cwd=repo,text=True,capture_output=True,check=True).stdout,subprocess.run(["git","status","--porcelain"],cwd=repo,text=True,capture_output=True,check=True).stdout,(repo/".git/index").read_bytes())
            self.assertEqual(before,after)


class FixtureInventoryTests(unittest.TestCase):
    def test_fixture_counts(self):
        self.assertEqual(len(list((SKILL_ROOT/"tests/fixtures/valid").glob("*.json"))),7)
        self.assertEqual(len(list((SKILL_ROOT/"tests/fixtures/invalid").glob("*.json"))),29)


PATCH_TEXT = "diff --git a/src/a.py b/src/a.py\n--- a/src/a.py\n+++ b/src/a.py\n@@ -1 +1 @@\n-old\n+new\n"

def _capture_error(operation):
    try: operation()
    except reviewer.ReviewError as error: return [reviewer.diagnostics_record(error)]
    return []

def _patch_contract(**updates):
    value={"patch_kind":"prompt_local","allowed_paths":["src"],"forbidden_paths":[],"expected_empty":False,"allow_renames":False,"allow_copies":False,"allow_mode_changes":False,"allow_deletions":False}
    value.update(updates); return value

def _zip(path,members,compression=zipfile.ZIP_DEFLATED):
    with zipfile.ZipFile(path,"w",compression) as archive:
        for name,data in members: archive.writestr(name,data)

def _prompt_case(root):
    prompt=root/"prompt.md"; validation=root/"validation.json"
    prompt.write_text("prompt_id: TEST\nprompt_mode: validation_only\nvalidation_ceiling: static_inspection_only\npatch_kind_expected: empty_no_changes\ncommit_expected: no\ndo_not_commit: yes\nallowed/path\nreviewed_code_execution: no\n")
    digest=reviewer.sha256_bytes(prompt.read_bytes())
    payload={"input":{"sha256":digest},"producer":{"name":"prompt-helper","version":"newer"},"capabilities":{"mechanical_validity":True}}
    validation.write_text(json.dumps(payload))
    record={"path":str(prompt),"sha256":digest,"prompt_helper_result_path":str(validation),"prompt_helper_result_sha256":reviewer.sha256_bytes(validation.read_bytes()),"required_helper_capabilities":["mechanical_validity"],"expected_prompt_id":"TEST","expected_prompt_mode":"validation_only","expected_commit_policy":{"commit_expected":False,"do_not_commit":True,"expected_subject":None},"expected_allowed_paths":["allowed/path"],"expected_forbidden_actions":["reviewed_code_execution"],"expected_validation_ceiling":"static_inspection_only","expected_patch_kind":"empty_no_changes"}
    return prompt,validation,payload,record

def _consistent_manifest():
    manifest=json.loads((SKILL_ROOT/"assets/review_manifest_template.json").read_text())
    baseline="1"*64
    manifest["repositories"][0].update({"verification_mode":"reviewer_recomputed_patch_and_baseline","expected_head_before":baseline})
    manifest["patch_contract"]["baseline_head"]=baseline
    return manifest

def _run_fixture(record):
    kind=record["scenario_kind"]; diagnostics=[]; findings=[]; success=False
    with tempfile.TemporaryDirectory() as temporary:
        root=Path(temporary)
        if kind=="valid_corrective_follow_up_required":
            findings=reviewer.collect_findings({"x":{"findings":[{"finding_id":"new_defect","category":"defect","severity":"error","status":"confirmed_new","blocking":False}]}},{"allowed_nonblocking_preexisting_categories":[],"package_claim_only_blocks_acceptance":True}); success=True
        elif kind=="valid_declared_manual_gate_resolved":
            locator={"artifact_id":"decision","locator_type":"text_pattern","locator_value":"approved","expected_hash_or_value":"approved","observed_hash_or_value":"approved","reviewer_recomputed":True}
            gate={"gate_id":"manual","evaluator":"manual_reviewer_decision_required","manual_resolution":{"decision":True,"reviewer":"human","evidence_locator":locator},"evidence_requirements":[],"accepted_values":[True],"required":True}
            success=reviewer.evaluate_gate(gate,{"decision":"approved"},[],[])
        elif kind=="valid_empty_no_changes_patch": success=reviewer.parse_patch("",_patch_contract(patch_kind="empty_no_changes",expected_empty=True))==[]
        elif kind=="valid_extracted_package_accepted":
            package=root/"carrier"/"pkg"; package.mkdir(parents=True); (package/"a.txt").write_text("safe"); success=reviewer.directory_inventory(package.parent.resolve(),"pkg")[0]["data"]==b"safe"
        elif kind=="valid_final_integration_acceptance": success=reviewer.validate_cross_records(_consistent_manifest())
        elif kind=="valid_preexisting_nonblocking_finding":
            row={"finding_id":"known","category":"known","severity":"error","status":"confirmed_preexisting","blocking":False,"reviewer_recomputed_pre_delta":True,"pre_delta_evidence":["before"]}
            findings=reviewer.collect_findings({"x":{"findings":[row]}},{"allowed_nonblocking_preexisting_categories":["known"],"package_claim_only_blocks_acceptance":True}); success=not findings[0]["blocking"]
        elif kind=="valid_zip_package_accepted":
            path=root/"safe.zip"; _zip(path,[("pkg/a.txt",b"safe")]); success=reviewer.zip_inventory(path.resolve(),"pkg",reviewer.HARD_LIMITS)[0]["data"]==b"safe"
        elif kind=="invalid_artifact_hash": diagnostics+=_capture_error(lambda: reviewer.validate_identity("a","b",True,"pkg/a"))
        elif kind=="invalid_binary_patch": diagnostics+=_capture_error(lambda: reviewer.parse_patch("GIT binary patch\n",_patch_contract()))
        elif kind=="invalid_current_production_artifact": diagnostics+=reviewer.detect_contradictions({"x":{"noninterference":True,"current_production_artifact":"declared"}},[])
        elif kind=="invalid_duplicate_normalized_patch_path": diagnostics+=_capture_error(lambda: reviewer.parse_patch(PATCH_TEXT+PATCH_TEXT,_patch_contract()))
        elif kind=="invalid_empty_patch_nonempty": diagnostics+=_capture_error(lambda: reviewer.parse_patch("x",_patch_contract(patch_kind="empty_no_changes",expected_empty=True)))
        elif kind=="invalid_encrypted_archive":
            path=root/"encrypted.zip"; _zip(path,[("pkg/a",b"x")]); data=bytearray(path.read_bytes()); central=data.index(b"PK\x01\x02"); data[6]|=1; data[central+8]|=1; path.write_bytes(data); diagnostics+=_capture_error(lambda: reviewer.zip_inventory(path.resolve(),"pkg",reviewer.HARD_LIMITS))
        elif kind=="invalid_execution_field": diagnostics+=_capture_error(lambda: reviewer.reject_reserved({"nested":{"execute":True}}))
        elif kind=="invalid_missing_required_artifact": diagnostics+=_capture_error(lambda: reviewer.validate_artifact_set({"pkg/a"},set(),{"pkg/a"}))
        elif kind=="invalid_multiple_roots":
            path=root/"roots.zip"; _zip(path,[("one/a",b"1"),("two/b",b"2")]); diagnostics+=_capture_error(lambda: reviewer.zip_inventory(path.resolve(),"one",reviewer.HARD_LIMITS))
        elif kind=="invalid_nested_archive":
            path=root/"nested.zip"; _zip(path,[("pkg/a.zip",b"x")]); diagnostics+=_capture_error(lambda: reviewer.zip_inventory(path.resolve(),"pkg",reviewer.HARD_LIMITS))
        elif kind=="invalid_package_self_verdict_only":
            diagnostics+=reviewer.detect_contradictions({"x":{"authoritative_package_verdict":True}},[])
            gate={"evaluator":"repository_head_equals","accepted_values":["claim"],"evidence_requirements":[]}
            observation=reviewer.RepositoryObservation("repo","package_claim_only",False)
            diagnostics+=_capture_error(lambda: reviewer.evaluate_gate(gate,{},[],[observation]))
        elif kind=="invalid_package_supplied_command":
            diagnostics+=_capture_error(lambda: reviewer.reject_reserved({"command":"unsafe"}))
            diagnostics+=_capture_error(lambda: reviewer.evaluate_gate({"evaluator":"package_expression","accepted_values":[],"evidence_requirements":[]},{},[],[]))
        elif kind=="invalid_patch_path_escape": diagnostics+=_capture_error(lambda: reviewer.parse_patch("diff --git a/src/a b/src/b\nrename from ../../outside\nrename to src/b\n",_patch_contract(allow_renames=True)))
        elif kind=="invalid_patch_scope": diagnostics+=_capture_error(lambda: reviewer.parse_patch(PATCH_TEXT.replace("src/","outside/"),_patch_contract()))
        elif kind=="invalid_prompt_contract_mismatch":
            prompt,validation,payload,prompt_record=_prompt_case(root); payload["input"]["sha256"]="0"*64; validation.write_text(json.dumps(payload)); prompt_record["prompt_helper_result_sha256"]=reviewer.sha256_bytes(validation.read_bytes()); diagnostics+=_capture_error(lambda: reviewer.check_prompt_traceability(prompt_record))
            prompt,validation,payload,prompt_record=_prompt_case(root); prompt_record["expected_prompt_id"]="OTHER"; diagnostics+=_capture_error(lambda: reviewer.check_prompt_traceability(prompt_record))
        elif kind=="invalid_prompt_hash":
            prompt,validation,payload,prompt_record=_prompt_case(root); prompt_record["sha256"]="0"*64; diagnostics+=_capture_error(lambda: reviewer.check_prompt_traceability(prompt_record))
        elif kind=="invalid_report_test_contradiction": diagnostics+=reviewer.detect_contradictions({"x":{"report_status":"pass","failed":1}},[])
        elif kind=="invalid_repository_baseline":
            repo=root/"repo"; (repo/".git").mkdir(parents=True); values=iter(["observed_head","main","subject"])
            with mock.patch.object(reviewer,"fixed_git",side_effect=lambda *args:next(values)):
                observation=reviewer.verify_repository({"repository_id":"repo","verification_mode":"reviewer_recomputed_live_read_only","repository_path":str(repo.resolve()),"expected_head_after":"expected_head","expected_branch_after":"main","expected_commit_subject":"subject"},{})
            diagnostics+=list(observation.diagnostics)
        elif kind=="invalid_summary_csv_contradiction": diagnostics+=reviewer.detect_contradictions({"x":{"summary_count":2,"details":[1]}},[])
        elif kind=="invalid_undeclared_domain_gate": diagnostics+=reviewer.validate_result_artifacts({"artifacts":[],"independent_checks":[],"declared_gates":[]},{"report":{"domain_gate_ids":["missing"]}})
        elif kind=="invalid_undeclared_mode_change": diagnostics+=_capture_error(lambda: reviewer.parse_patch("diff --git a/src/a b/src/a\nold mode 100644\nnew mode 100755\n",_patch_contract()))
        elif kind=="invalid_unresolved_manual_gate":
            gate={"gate_id":"manual","evaluator":"manual_reviewer_decision_required","manual_resolution":None,"evidence_requirements":[],"accepted_values":[True],"required":True}; found,_=reviewer.evaluate_declared_gate(gate,{},[],[]); diagnostics+=found
        elif kind=="invalid_zip_backslash_name":
            path=root/"backslash.zip"; _zip(path,[("pkg\\a",b"x")]); diagnostics+=_capture_error(lambda: reviewer.zip_inventory(path.resolve(),"pkg",reviewer.HARD_LIMITS))
        elif kind=="invalid_zip_bomb_limit":
            path=root/"limit.zip"; _zip(path,[("pkg/a",b"x"*100)]); limits=dict(reviewer.HARD_LIMITS,maximum_member_uncompressed_bytes=10); diagnostics+=_capture_error(lambda: reviewer.zip_inventory(path.resolve(),"pkg",limits)); limits=dict(reviewer.HARD_LIMITS,maximum_compression_ratio=1); diagnostics+=_capture_error(lambda: reviewer.zip_inventory(path.resolve(),"pkg",limits))
        elif kind=="invalid_zip_casefold_collision":
            path=root/"case.zip"; _zip(path,[("pkg/A",b"1"),("pkg/a",b"2")]); diagnostics+=_capture_error(lambda: reviewer.zip_inventory(path.resolve(),"pkg",reviewer.HARD_LIMITS))
        elif kind=="invalid_zip_duplicate_name":
            path=root/"duplicate.zip"
            with zipfile.ZipFile(path,"w") as archive:
                with self_warns_user_warning(): archive.writestr("pkg/a",b"1"); archive.writestr("pkg/a",b"2")
            diagnostics+=_capture_error(lambda: reviewer.zip_inventory(path.resolve(),"pkg",reviewer.HARD_LIMITS))
        elif kind=="invalid_zip_local_header_mismatch":
            path=root/"header.zip"; _zip(path,[("pkg/a",b"safe")]); data=bytearray(path.read_bytes()); data[30]=ord("q"); path.write_bytes(data); diagnostics+=_capture_error(lambda: reviewer.zip_inventory(path.resolve(),"pkg",reviewer.HARD_LIMITS))
        elif kind=="invalid_zip_path_traversal":
            path=root/"traversal.zip"; _zip(path,[("pkg/../escape",b"x")]); diagnostics+=_capture_error(lambda: reviewer.zip_inventory(path.resolve(),"pkg",reviewer.HARD_LIMITS))
        elif kind=="invalid_zip_symlink":
            path=root/"link.zip"; info=zipfile.ZipInfo("pkg/link"); info.create_system=3; info.external_attr=(stat.S_IFLNK|0o777)<<16
            with zipfile.ZipFile(path,"w") as archive: archive.writestr(info,b"target")
            diagnostics+=_capture_error(lambda: reviewer.zip_inventory(path.resolve(),"pkg",reviewer.HARD_LIMITS))
        else: raise AssertionError(f"unknown fixture scenario: {kind}")
    verdict=reviewer.derive_verdict(diagnostics,findings)
    return {"diagnostics":diagnostics,"verdict":verdict,"success":success}

def self_warns_user_warning():
    return mock.patch("warnings.showwarning")

def _fixture_test(path):
    def test(self):
        record=json.loads(path.read_text()); self.assertEqual(record["fixture_id"],path.stem); self.assertEqual(record["scenario_kind"],path.stem)
        with mock.patch("subprocess.Popen",side_effect=AssertionError("reviewed execution attempted")), mock.patch("os.system",side_effect=AssertionError("reviewed shell attempted")):
            observed=_run_fixture(record)
        expected={item for item in record["expected_diagnostics"].split(";") if item and item!="none"}
        self.assertEqual({item["diagnostic_id"] for item in observed["diagnostics"]},expected)
        self.assertEqual(observed["verdict"],record["expected_verdict"])
        self.assertEqual(observed["success"],record["validity"]=="valid")
    return test


for _path in sorted((SKILL_ROOT/"tests/fixtures").glob("*/*.json")):
    setattr(FixtureInventoryTests, f"test_fixture_{_path.stem}", _fixture_test(_path))

_FIXTURE_BY_DIAGNOSTIC={}
for _fixture_path in sorted((SKILL_ROOT/"tests/fixtures").glob("*/*.json")):
    _fixture_record=json.loads(_fixture_path.read_text())
    for _diagnostic_id in _fixture_record["expected_diagnostics"].split(";"):
        if _diagnostic_id and _diagnostic_id!="none": _FIXTURE_BY_DIAGNOSTIC.setdefault(_diagnostic_id,_fixture_record)

def _error_record(operation):
    records=_capture_error(operation)
    if not records: raise AssertionError("behavior did not emit a diagnostic")
    return records[0]

def _trigger_diagnostic(diagnostic_id):
    if diagnostic_id in _FIXTURE_BY_DIAGNOSTIC:
        records=_run_fixture(_FIXTURE_BY_DIAGNOSTIC[diagnostic_id])["diagnostics"]
        return next(item for item in records if item["diagnostic_id"]==diagnostic_id)
    with tempfile.TemporaryDirectory() as temporary:
        root=Path(temporary)
        if diagnostic_id=="PACKAGE001": return _error_record(lambda: reviewer.directory_inventory(Path("relative"),"pkg"))
        if diagnostic_id=="PACKAGE002":
            package=root/"carrier"/"pkg"; package.mkdir(parents=True); (package/"a").write_text("x"); limits=dict(reviewer.HARD_LIMITS,maximum_member_count=0); return _error_record(lambda: reviewer.directory_inventory(package.parent.resolve(),"pkg",limits))
        if diagnostic_id=="PACKAGE003": return _error_record(lambda: reviewer.validate_carrier_shape({"package":{"carrier_path":["a","b"],"package_root":"pkg"}}))
        if diagnostic_id=="PACKAGE004": return _error_record(lambda: reviewer.validate_artifact_set({"pkg/a"},{"pkg/a","pkg/b"},{"pkg/a"}))
        if diagnostic_id=="ARCHIVE001":
            path=root/"bad.zip"; path.write_bytes(b"not a zip"); return _error_record(lambda: reviewer.zip_inventory(path.resolve(),"pkg",reviewer.HARD_LIMITS))
        if diagnostic_id=="PATH004":
            descriptor=os.open(root,os.O_RDONLY|getattr(os,"O_DIRECTORY",0))
            try: return _error_record(lambda: reviewer._descriptor_open("missing",os.O_RDONLY,descriptor))
            finally: os.close(descriptor)
        if diagnostic_id=="HASH001": return _error_record(lambda: reviewer.validate_identity("observed","expected"))
        if diagnostic_id=="HASH003":
            package=root/"carrier"/"pkg"; package.mkdir(parents=True); target=package/"a"; target.write_text("one"); real=reviewer._descriptor_open; calls=0
            def change(name,flags,parent_fd,diag="PATH004"):
                nonlocal calls
                if name=="a":
                    calls+=1
                    if calls==2: target.write_text("two")
                return real(name,flags,parent_fd,diag)
            with mock.patch.object(reviewer,"_descriptor_open",side_effect=change): return _error_record(lambda: reviewer.directory_inventory(package.parent.resolve(),"pkg"))
        if diagnostic_id=="SCHEMA001": return _error_record(lambda: reviewer.schema_validate(-1,{"type":"number","exclusiveMinimum":0},{"type":"number","exclusiveMinimum":0}))
        if diagnostic_id=="SCHEMA002": return _error_record(lambda: reviewer.parse_artifact({"parser":"json","media_type":"application/json"},b"{"))
        if diagnostic_id=="BASELINE001":
            manifest=_consistent_manifest(); manifest["patch_contract"]["baseline_repository_id"]="missing"; return _error_record(lambda: reviewer.validate_cross_records(manifest))
        if diagnostic_id=="BASELINE003":
            manifest=_consistent_manifest(); manifest["patch_contract"]["baseline_head"]="2"*64; return _error_record(lambda: reviewer.validate_cross_records(manifest))
        if diagnostic_id=="PATCH001": return _error_record(lambda: reviewer.parse_patch("diff --git a/src/a b/src/a\nunknown\n",_patch_contract()))
        if diagnostic_id=="SCOPE003": return _error_record(lambda: reviewer.parse_patch(PATCH_TEXT,_patch_contract(forbidden_paths=["src"])))
        if diagnostic_id=="ARTIFACT002":
            manifest={"repositories":[{"repository_id":"r"}],"artifacts":[{"artifact_id":"a","relative_path":"same"},{"artifact_id":"b","relative_path":"same"}],"declared_gates":[],"independent_checks":[]}; return _error_record(lambda: reviewer.unique_manifest_ids(manifest))
        if diagnostic_id=="ARTIFACT003": return _error_record(lambda: reviewer.parse_artifact({"parser":"json","media_type":"text/plain"},b"{}"))
        if diagnostic_id=="EVIDENCE001": return _error_record(lambda: reviewer.locate({"artifact_id":"missing","locator_type":"file_whole","locator_value":"whole"},{},[]))
        if diagnostic_id=="EVIDENCE002": return _error_record(lambda: reviewer.locate({"artifact_id":"x","locator_type":"text_pattern","locator_value":"value","expected_hash_or_value":"other"},{"x":"value"},[]))
        if diagnostic_id=="EVIDENCE003": return reviewer.verify_repository({"repository_id":"r","verification_mode":"package_claim_only"},{}).diagnostics[0]
        if diagnostic_id=="GATE002":
            locator={"artifact_id":"x","locator_type":"json_pointer","locator_value":"/value","expected_hash_or_value":"observed","observed_hash_or_value":"observed","reviewer_recomputed":True}; gate={"gate_id":"g","evaluator":"json_pointer_equals","evidence_requirements":[locator],"accepted_values":["required"],"required":True}; records,_=reviewer.evaluate_declared_gate(gate,{"x":{"value":"observed"}},[],[]); return records[0]
        if diagnostic_id=="TEST001":
            manifest=_consistent_manifest(); manifest["independent_checks"]=[{"check_id":"check","state":"independent_external_test_result","result_artifact_id":"missing"}]; return _error_record(lambda: reviewer.validate_cross_records(manifest))
        if diagnostic_id=="TEST002":
            manifest={"artifacts":[{"artifact_id":"tests","semantic_role":"test_results"}],"independent_checks":[],"declared_gates":[]}; records=reviewer.validate_result_artifacts(manifest,{"tests":{"total":2,"failed":0,"results":[{"name":"one","status":"pass"}]}}); return records[0]
        if diagnostic_id=="TEST003":
            records=reviewer.validate_result_artifacts({"artifacts":[],"independent_checks":[{"check_id":"planned","state":"planned_but_not_run_check"}],"declared_gates":[]},{}); return records[0]
        if diagnostic_id=="PROBE001":
            manifest={"artifacts":[{"artifact_id":"probes","semantic_role":"probe_results"}],"independent_checks":[],"declared_gates":[]}; return reviewer.validate_result_artifacts(manifest,{"probes":{"results":"bad"}})[0]
        if diagnostic_id=="PROBE002":
            manifest={"artifacts":[{"artifact_id":"probes","semantic_role":"probe_results"}],"independent_checks":[],"declared_gates":[]}; return reviewer.validate_result_artifacts(manifest,{"probes":{"results":[{"name":"probe","expected":1,"observed":0}]}})[0]
        if diagnostic_id=="CONTRADICTION003": return reviewer.detect_contradictions({"x":{"no_changes":True}},[{"new_path":"src/a"}])[0]
        if diagnostic_id=="SELF_CERTIFICATION003": return reviewer.detect_contradictions({"x":{"blocking_diagnostics":["GATE002"],"summary_diagnostics":[]}},[])[0]
        if diagnostic_id=="VERDICT001": return reviewer.detect_contradictions({"x":{"package_authored_verdict":"accepted"}},[])[0]
        if diagnostic_id=="VERDICT002": return reviewer.verify_repository({"repository_id":"r","verification_mode":"not_safely_generic"},{}).diagnostics[0]
        if diagnostic_id=="VERDICT003": return reviewer.validate_verdict_precedence("accepted","blocked_review")
        if diagnostic_id=="RENDER001":
            target=root/"output"; target.mkdir(); return _error_record(lambda: reviewer.publish_outputs(target,{"review_id":"r","independent_checks":[]},[],{"review_id":"r","verdict":"accepted","diagnostics":[],"findings":[],"package_inventory_sha256":reviewer.inventory_hash([]),"patch_paths":[]}))
        if diagnostic_id=="RENDER002": return _error_record(lambda: reviewer.validate_generated_outputs(root,[],{"verdict":"accepted","findings":[]}))
    raise AssertionError(f"no behavioral trigger for {diagnostic_id}")

class DiagnosticReachabilityTests(unittest.TestCase):
    def test_reachability_table_complete(self):
        observed={diagnostic_id:_trigger_diagnostic(diagnostic_id)["diagnostic_id"] for diagnostic_id in reviewer.DIAGNOSTIC_IDS}
        self.assertEqual(observed,{diagnostic_id:diagnostic_id for diagnostic_id in reviewer.DIAGNOSTIC_IDS})

def _diagnostic_test(diagnostic_id):
    def test(self):
        with mock.patch("subprocess.Popen",side_effect=AssertionError("reviewed execution attempted")), mock.patch("os.system",side_effect=AssertionError("reviewed shell attempted")):
            observed=_trigger_diagnostic(diagnostic_id)
        self.assertEqual(observed["diagnostic_id"],diagnostic_id)
        expected=reviewer.NONBLOCKING_DIAGNOSTICS.get(diagnostic_id,("error",True))
        self.assertEqual((observed["severity"],observed["blocking"]),expected)
        self.assertEqual(reviewer.derive_verdict([observed],[]),reviewer.verdict_for_error(reviewer.ReviewError(diagnostic_id,"behavioral trigger")))
    return test

for _diagnostic_id in reviewer.DIAGNOSTIC_IDS:
    setattr(DiagnosticReachabilityTests,f"test_diagnostic_{_diagnostic_id.lower()}",_diagnostic_test(_diagnostic_id))

class CorrectiveHardeningTests(unittest.TestCase):
    def _directory(self,root,relative="pkg/a",data=b"inside"):
        target=root/relative; target.parent.mkdir(parents=True); target.write_bytes(data); return target

    def test_descriptor_root_and_parent_component_races(self):
        with tempfile.TemporaryDirectory() as temporary:
            base=Path(temporary); carrier=base/"carrier"; target=self._directory(carrier); outside=self._directory(base/"outside",data=b"outside")
            real_open=os.open
            def replace_carrier(path,flags,*args,**kwargs):
                descriptor=real_open(path,flags,*args,**kwargs)
                if Path(path)==carrier:
                    carrier.rename(base/"carrier_original"); carrier.symlink_to(base/"outside",target_is_directory=True)
                return descriptor
            with mock.patch.object(os,"open",side_effect=replace_carrier): rows=reviewer.directory_inventory(carrier.resolve(),"pkg")
            self.assertEqual(rows[0]["data"],b"inside")
        for component in ("pkg","middle","a"):
            with self.subTest(component=component), tempfile.TemporaryDirectory() as temporary:
                base=Path(temporary); carrier=base/"carrier"; target=self._directory(carrier,"pkg/middle/a"); outside=self._directory(base/"outside","middle/a",b"outside")
                real=reviewer._descriptor_open; replaced=False
                def replace(name,flags,parent_fd,diag="PATH004"):
                    nonlocal replaced
                    if not replaced and name==component:
                        replaced=True
                        victim={"pkg":carrier/"pkg","middle":carrier/"pkg/middle","a":target}[component]
                        victim.rename(victim.with_name(victim.name+"_original")); victim.symlink_to((base/"outside") if component=="pkg" else (base/"outside/middle") if component=="middle" else (base/"outside/middle/a"),target_is_directory=component!="a")
                    return real(name,flags,parent_fd,diag)
                with mock.patch.object(reviewer,"_descriptor_open",side_effect=replace), self.assertRaises(reviewer.ReviewError) as caught: reviewer.directory_inventory(carrier.resolve(),"pkg")
                self.assertEqual(caught.exception.diagnostic_id,"PATH004")

    def test_directory_resource_bounds_and_hardlink(self):
        cases=[("maximum_member_count",1,{"a":b"1","b":b"2"}), ("maximum_member_uncompressed_bytes",1,{"a":b"12"}), ("maximum_total_uncompressed_bytes",2,{"a":b"12","b":b"3"})]
        for key,limit,files in cases:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as temporary:
                carrier=Path(temporary)/"carrier"; package=carrier/"pkg"; package.mkdir(parents=True)
                for name,data in files.items(): (package/name).write_bytes(data)
                limits=dict(reviewer.HARD_LIMITS); limits[key]=limit
                with self.assertRaises(reviewer.ReviewError) as caught: reviewer.directory_inventory(carrier.resolve(),"pkg",limits)
                self.assertEqual(caught.exception.diagnostic_id,"PACKAGE002")
        with tempfile.TemporaryDirectory() as temporary:
            carrier=Path(temporary)/"carrier"; original=self._directory(carrier); os.link(original,original.with_name("hardlink"))
            with self.assertRaises(reviewer.ReviewError) as caught: reviewer.directory_inventory(carrier.resolve(),"pkg")
            self.assertEqual(caught.exception.diagnostic_id,"PATH003")

    def test_output_parent_and_target_races(self):
        result={"review_id":"r","verdict":"accepted","diagnostics":[],"findings":[],"package_inventory_sha256":reviewer.inventory_hash([]),"patch_paths":[]}; manifest={"review_id":"r","independent_checks":[]}
        with tempfile.TemporaryDirectory() as temporary:
            base=Path(temporary); parent=base/"parent"; outside=base/"outside"; parent.mkdir(); outside.mkdir(); real=reviewer._open_absolute_directory
            def replace(path):
                descriptor=real(path); parent.rename(base/"parent_original"); parent.symlink_to(outside,target_is_directory=True); return descriptor
            with mock.patch.object(reviewer,"_open_absolute_directory",side_effect=replace): reviewer.publish_outputs(parent/"output",manifest,[],result)
            self.assertTrue((base/"parent_original/output/review_validation.json").is_file()); self.assertEqual(list(outside.iterdir()),[])
        with tempfile.TemporaryDirectory() as temporary:
            parent=Path(temporary); target=parent/"output"; outside=parent/"outside"; outside.mkdir(); real=reviewer.publish_noreplace_at
            def race(parent_fd,source,target_name):
                os.symlink("outside",target_name,dir_fd=parent_fd); return real(parent_fd,source,target_name)
            with mock.patch.object(reviewer,"publish_noreplace_at",side_effect=race), self.assertRaises(reviewer.ReviewError) as caught: reviewer.publish_outputs(target,manifest,[],result)
            self.assertEqual(caught.exception.diagnostic_id,"RENDER001"); self.assertEqual(list(outside.iterdir()),[]); self.assertEqual(len(list(parent.glob(".output.incomplete-*/INCOMPLETE_REVIEW.json"))),1)

    def test_strict_patch_valid_forms(self):
        forms={
            "modify":(PATCH_TEXT,_patch_contract()),
            "create":("diff --git a/src/new b/src/new\nnew file mode 100644\n--- /dev/null\n+++ b/src/new\n@@ -0,0 +1 @@\n+new\n",_patch_contract()),
            "delete":("diff --git a/src/a b/src/a\ndeleted file mode 100644\n--- a/src/a\n+++ /dev/null\n@@ -1 +0,0 @@\n-old\n",_patch_contract(allow_deletions=True)),
            "rename":("diff --git a/src/a b/src/b\nsimilarity index 100%\nrename from src/a\nrename to src/b\n",_patch_contract(allow_renames=True)),
            "copy":("diff --git a/src/a b/src/b\nsimilarity index 100%\ncopy from src/a\ncopy to src/b\n",_patch_contract(allow_copies=True)),
            "mode":("diff --git a/src/a b/src/a\nold mode 100644\nnew mode 100755\n",_patch_contract(allow_mode_changes=True)),
        }
        for name,(text,contract) in forms.items():
            with self.subTest(name=name): self.assertEqual(len(reviewer.parse_patch(text,contract)),1)

    def test_strict_patch_malformed_forms(self):
        cases=[
            ("diff --git a/src/a b/src/a\narbitrary\n","PATCH001"),
            ("diff --git a/src/a b/src/b\nrename from ../../outside\nrename to src/b\n","SCOPE001"),
            (PATCH_TEXT.replace("--- a/src/a.py","--- a/src/other.py"),"PATCH001"),
            (PATCH_TEXT.replace("@@ -1 +1 @@","@@ -1,2 +1 @@"),"PATCH001"),
            (PATCH_TEXT.replace("--- a/src/a.py","unknown metadata\n--- a/src/a.py"),"PATCH001"),
        ]
        for text,expected in cases:
            with self.subTest(expected=expected), self.assertRaises(reviewer.ReviewError) as caught: reviewer.parse_patch(text,_patch_contract(allow_renames=True))
            self.assertEqual(caught.exception.diagnostic_id,expected)

    def test_reviewer_authority_and_finding_policy(self):
        repo_gate={"evaluator":"repository_head_equals","accepted_values":["claim"],"evidence_requirements":[]}
        with self.assertRaises(reviewer.ReviewError) as caught: reviewer.evaluate_gate(repo_gate,{},[],[reviewer.RepositoryObservation("r","package_claim_only",False)])
        self.assertEqual(caught.exception.diagnostic_id,"SELF_CERTIFICATION002")
        row={"name":"suite","status":"pass","origin":"package_authored_test_transcript"}; locator={"artifact_id":"tests","locator_type":"test_name","locator_value":"suite","expected_hash_or_value":row,"observed_hash_or_value":row,"reviewer_recomputed":False}
        with self.assertRaises(reviewer.ReviewError) as caught: reviewer.evaluate_gate({"evaluator":"test_summary_equals","accepted_values":[row],"evidence_requirements":[locator]},{"tests":[row]},[],[])
        self.assertEqual(caught.exception.diagnostic_id,"SELF_CERTIFICATION002")
        finding={"finding_id":"claim","category":"claim","severity":"warning","status":"package_claim_only","blocking":False}; normalized=reviewer.collect_findings({"x":{"findings":[finding]}},{"allowed_nonblocking_preexisting_categories":[],"package_claim_only_blocks_acceptance":True})
        self.assertTrue(normalized[0]["blocking"]); self.assertEqual(reviewer.derive_verdict([],normalized),"blocked_self_certification")

    def test_schema_keyword_inventory_finite_and_exclusive(self):
        schema=json.loads((SKILL_ROOT/"references/review_schema.json").read_text()); used=reviewer.schema_keywords(schema)
        self.assertIn("exclusiveMinimum",used); self.assertTrue(used.issubset(reviewer.SUPPORTED_SCHEMA_KEYWORDS))
        for value in (-1,0,float("nan"),float("inf")):
            with self.subTest(value=value), self.assertRaises(reviewer.ReviewError): reviewer.schema_validate(value,{"type":"number","exclusiveMinimum":0},{"type":"number","exclusiveMinimum":0})
        with self.assertRaises(reviewer.ReviewError): reviewer.strict_json('{"number": NaN}')

    def test_cross_record_rules(self):
        cases=[]
        manifest=_consistent_manifest(); manifest["package"]["reviewed_repository_ids"]=["missing"]; cases.append(manifest)
        manifest=_consistent_manifest(); manifest["patch_contract"]["baseline_repository_id"]="missing"; cases.append(manifest)
        manifest=_consistent_manifest(); manifest["patch_contract"]["baseline_head"]="2"*64; cases.append(manifest)
        manifest=_consistent_manifest(); manifest["repositories"][0]["allowed_changed_paths"]=["safe"]; manifest["patch_contract"]["allowed_paths"]=["outside"]; cases.append(manifest)
        manifest=_consistent_manifest(); manifest["repositories"][0]["mutation_expected"]=True; cases.append(manifest)
        manifest=_consistent_manifest(); manifest["repositories"][0]["commit_expected"]=True; cases.append(manifest)
        manifest=_consistent_manifest(); manifest["authorizing_prompt"]["expected_commit_policy"]["commit_expected"]=True; cases.append(manifest)
        manifest=_consistent_manifest(); manifest["independent_checks"]=[{"check_id":"c","state":"independent_external_test_result","result_artifact_id":"missing"}]; cases.append(manifest)
        manifest=_consistent_manifest(); manifest["independent_checks"]=[{"check_id":"c","state":"planned_but_not_run_check","result_artifact_id":"empty_patch"}]; cases.append(manifest)
        locator={"artifact_id":"missing","locator_type":"file_whole","locator_value":"whole","expected_hash_or_value":None,"observed_hash_or_value":None,"reviewer_recomputed":True}
        manifest=_consistent_manifest(); manifest["declared_gates"]=[{"gate_id":"g","evidence_requirements":[locator],"manual_resolution":None}]; cases.append(manifest)
        manifest=_consistent_manifest(); manifest["declared_gates"]=[{"gate_id":"g","evidence_requirements":[],"manual_resolution":{"evidence_locator":locator}}]; cases.append(manifest)
        for index,value in enumerate(cases):
            with self.subTest(index=index), self.assertRaises(reviewer.ReviewError): reviewer.validate_cross_records(value)

    def test_early_failure_verdict_mapping(self):
        expected={"PACKAGE001":"blocked_incomplete_package","PROMPT001":"blocked_prompt_traceability","BASELINE001":"blocked_baseline_mismatch","PATCH001":"blocked_patch_scope","TEST001":"blocked_validation_evidence","GATE001":"blocked_declared_gate","SELF_CERTIFICATION001":"blocked_self_certification","SCHEMA001":"blocked_review"}
        for diagnostic,verdict in expected.items(): self.assertEqual(reviewer.verdict_for_error(reviewer.ReviewError(diagnostic,"failure")),verdict)

    def test_complete_review_never_reaches_execution_boundaries(self):
        workspace=SCRIPT.resolve().parents[4]
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); carrier=root/"carrier"; package=carrier/"package_root"; package.mkdir(parents=True); (package/"empty.patch").write_bytes(b"")
            prompt=root/"prompt.md"; manifest_path=root/"manifest.json"; output=root/"output"
            prompt.write_text("prompt_id: TEST\nprompt_mode: validation_only\nvalidation_ceiling: static_inspection_only\npatch_kind_expected: empty_no_changes\ncommit_expected: no\ndo_not_commit: yes\nallowed/path\nreviewed_code_execution: no\n")
            prompt_hash=reviewer.sha256_bytes(prompt.read_bytes())
            manifest=_consistent_manifest(); manifest["review_id"]="execution_boundary_review"; manifest["authorizing_prompt"].update({"path":str(prompt),"sha256":prompt_hash,"expected_prompt_id":"TEST","expected_allowed_paths":["allowed/path"],"expected_forbidden_actions":["reviewed_code_execution"]}); manifest["repositories"][0]["repository_path"]=str(workspace); manifest["package"].update({"carrier_path":str(carrier),"package_inventory_sha256":reviewer.inventory_hash(reviewer.directory_inventory(carrier.resolve(),"package_root"))}); manifest_path.write_text(json.dumps(manifest))
            blocked=[]
            def forbidden(*args,**kwargs): blocked.append((args,kwargs)); raise AssertionError("execution boundary reached")
            targets=["subprocess.run","subprocess.Popen","os.system","os.popen","importlib.import_module","builtins.compile","builtins.eval","builtins.exec"]
            targets += [f"os.{name}" for name in ("execl","execle","execlp","execlpe","execv","execve","execvp","execvpe") if hasattr(os,name)]
            with contextlib.ExitStack() as stack:
                for target_name in targets: stack.enter_context(mock.patch(target_name,side_effect=forbidden))
                result=reviewer.review(manifest_path,SKILL_ROOT/"references/review_schema.json",output)
            self.assertEqual(result["verdict"],"accepted"); self.assertEqual(blocked,[]); reviewer.validate_generated_outputs(output,reviewer.directory_inventory(carrier.resolve(),"package_root"),result)


if __name__ == "__main__":
    unittest.main()
