import csv
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
        self.assertEqual(len(reviewer.DIAGNOSTIC_IDS), 65)
        self.assertEqual(len({item.rstrip("0123456789") for item in reviewer.DIAGNOSTIC_IDS}), 19)
        self.assertEqual(len(reviewer.PATCH_KINDS), 7)
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

    def test_cli_shape(self):
        actions = {action.dest for action in reviewer.parser()._actions}
        self.assertEqual(actions, {"help", "schema", "governance_binding", "format", "json_out", "validate_only", "output_root", "REVIEW_MANIFEST"})
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

    def contract(self, kind="source_change"):
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
            with mock.patch.object(reviewer, "publish_noreplace", side_effect=OSError):
                with self.assertRaises(Exception): reviewer.publish_outputs(target, {"independent_checks":[]}, [], {"findings":[],"verdict":"accepted","diagnostics":[]})
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
            real_open=os.open; calls=0
            def changed(path, flags, *args):
                nonlocal calls
                calls+=1
                if calls==2: target.write_text("second")
                return real_open(path,flags,*args)
            with mock.patch.object(os,"open",side_effect=changed), self.assertRaises(reviewer.ReviewError) as caught:
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
        base={"patch_kind":"source_change","allowed_paths":["src"],"forbidden_paths":[],"expected_empty":False,"allow_renames":False,"allow_copies":False,"allow_deletions":False,"allow_mode_changes":False}
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
        parsed={"text":"present","json":{"value":"ok"},"csv":[{"id":"one","value":"ok"}],"tests":[{"name":"suite","status":"pass"}],"probes":[{"name":"probe","value":1}]}
        patch=reviewer.parse_patch(self.PATCH,None); repos=[{"expected_commit_subject":"subject","expected_head_after":"head"}]
        cases=[
            ("artifact_present",[self.locator("text","text_pattern","present","present")],["present"],None),
            ("hash_equals",[self.locator("json","json_pointer","/value","ok")],["ok"],None),
            ("json_pointer_equals",[self.locator("json","json_pointer","/value","ok")],["ok"],None),
            ("json_pointer_in_set",[self.locator("json","json_pointer","/value","ok")],["ok","other"],None),
            ("csv_row_count",[self.locator("csv","csv_row","id=one",{"id":"one","value":"ok"})],[1],1),
            ("csv_value_equals",[self.locator("csv","csv_row","id=one",{"id":"one","value":"ok"})],[{"id":"one","value":"ok"}],None),
            ("text_pattern_present",[self.locator("text","text_pattern","present","present")],[True],None),
            ("text_pattern_absent",[{**self.locator("text","text_pattern","absent"),"observed_hash_or_value":None}],[True],None),
            ("test_summary_equals",[self.locator("tests","test_name","suite",{"name":"suite","status":"pass"})],[{"name":"suite","status":"pass"}],None),
            ("probe_field_equals",[self.locator("probes","probe_name","probe",{"name":"probe","value":1})],[{"name":"probe","value":1}],None),
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
            result={"review_id":"review","findings":[],"verdict":"accepted","diagnostics":[]}
            reviewer.publish_outputs(target,manifest,rows,result)
            self.assertEqual({item.name for item in target.iterdir()},set(reviewer.OUTPUT_NAMES))
            reviewer.validate_generated_outputs(target,rows,result)
            with self.assertRaises(reviewer.ReviewError): reviewer.publish_outputs(target,manifest,rows,result)

    def test_prompt_traceability_exact_fields_without_invocation(self):
        workspace=SCRIPT.resolve().parents[4]
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); prompt=root/"prompt.md"; validation=root/"validation.json"
            prompt.write_text("prompt_id: TEST\nprompt_mode: validation_only\nvalidation_ceiling: static_inspection_only\npatch_kind_expected: empty_no_changes\ncommit_expected: no\ndo_not_commit: yes\nallowed/path\nreviewed_code_execution: no\n")
            prompt_hash=reviewer.sha256_bytes(prompt.read_bytes())
            payload={"input":{"sha256":prompt_hash},"error_count":0,"valid_schema":True,"validator_version":"1.0.0","schema_version":"1.0.0","context":{"continuation":"no","evidence_round":"yes","user_run_handoff":"no"},"governance":{"binding_matches":True,"agents_sha256":reviewer.sha256_bytes((workspace/"AGENTS.md").read_bytes()),"cpc_sha256":reviewer.sha256_bytes((workspace/"CPC.md").read_bytes())}}
            validation.write_text(json.dumps(payload))
            record={"path":str(prompt),"sha256":prompt_hash,"prompt_contract_validation_path":str(validation),"prompt_contract_validation_sha256":reviewer.sha256_bytes(validation.read_bytes()),"expected_prompt_id":"TEST","expected_prompt_mode":"validation_only","expected_commit_policy":{"commit_expected":False,"do_not_commit":True,"expected_subject":None},"expected_allowed_paths":["allowed/path"],"expected_forbidden_actions":["reviewed_code_execution"],"expected_validation_ceiling":"static_inspection_only","expected_patch_kind":"empty_no_changes"}
            with mock.patch("subprocess.run",side_effect=AssertionError("prompt validator invoked")):
                self.assertEqual(reviewer.check_prompt_traceability(record)["error_count"],0)
            payload["error_count"]=1; validation.write_text(json.dumps(payload)); record["prompt_contract_validation_sha256"]=reviewer.sha256_bytes(validation.read_bytes())
            with self.assertRaises(reviewer.ReviewError): reviewer.check_prompt_traceability(record)

    def test_end_to_end_directory_review_and_generated_artifacts(self):
        workspace=SCRIPT.resolve().parents[4]
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); carrier=root/"carrier"; package=carrier/"package_root"; package.mkdir(parents=True); (package/"empty.patch").write_bytes(b"")
            prompt=root/"prompt.md"; validation=root/"validation.json"; manifest_path=root/"manifest.json"; output=root/"output"
            prompt.write_text("prompt_id: TEST\nprompt_mode: validation_only\nvalidation_ceiling: static_inspection_only\npatch_kind_expected: empty_no_changes\ncommit_expected: no\ndo_not_commit: yes\nallowed/path\nreviewed_code_execution: no\n")
            prompt_hash=reviewer.sha256_bytes(prompt.read_bytes())
            validation_payload={"input":{"sha256":prompt_hash},"error_count":0,"valid_schema":True,"validator_version":"1.0.0","schema_version":"1.0.0","context":{"continuation":"no","evidence_round":"yes","user_run_handoff":"no"},"governance":{"binding_matches":True,"agents_sha256":reviewer.sha256_bytes((workspace/"AGENTS.md").read_bytes()),"cpc_sha256":reviewer.sha256_bytes((workspace/"CPC.md").read_bytes())}}
            validation.write_text(json.dumps(validation_payload))
            manifest=json.loads((SKILL_ROOT/"assets/review_manifest_template.json").read_text())
            manifest["review_id"]="review"; manifest["authorizing_prompt"].update({"path":str(prompt),"sha256":prompt_hash,"prompt_contract_validation_path":str(validation),"prompt_contract_validation_sha256":reviewer.sha256_bytes(validation.read_bytes()),"expected_prompt_id":"TEST","expected_allowed_paths":["allowed/path"],"expected_forbidden_actions":["reviewed_code_execution"]})
            manifest["repositories"][0]["repository_path"]=str(workspace)
            manifest["package"].update({"carrier_path":str(carrier),"package_inventory_sha256":reviewer.inventory_hash(reviewer.directory_inventory(carrier,"package_root"))})
            manifest_path.write_text(json.dumps(manifest))
            result=reviewer.review(manifest_path,SKILL_ROOT/"references/review_schema.json",SKILL_ROOT/"references/governance_binding.json",output)
            self.assertEqual(result["verdict"],"accepted")
            self.assertEqual(result["diagnostics"][0]["diagnostic_id"],"EVIDENCE003")
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
                diagnostics=reviewer.verify_repository(dict(base,verification_mode=mode),{"baseline_head":head})
                with self.subTest(mode=mode): self.assertEqual(diagnostics[0]["diagnostic_id"] if diagnostics else None,expected)
            after=(subprocess.run(["git","rev-parse","HEAD"],cwd=repo,text=True,capture_output=True,check=True).stdout,subprocess.run(["git","status","--porcelain"],cwd=repo,text=True,capture_output=True,check=True).stdout,(repo/".git/index").read_bytes())
            self.assertEqual(before,after)


class FixtureInventoryTests(unittest.TestCase):
    def test_fixture_counts(self):
        self.assertEqual(len(list((SKILL_ROOT/"tests/fixtures/valid").glob("*.json"))),7)
        self.assertEqual(len(list((SKILL_ROOT/"tests/fixtures/invalid").glob("*.json"))),29)


def _fixture_test(path):
    def test(self):
        record = json.loads(path.read_text())
        self.assertEqual(record["fixture_id"], path.stem)
        self.assertIn(record["validity"], ("valid","invalid"))
        expected = [item for item in record["expected_diagnostics"].split(";") if item and item != "none"]
        self.assertTrue(set(expected).issubset(set(reviewer.DIAGNOSTIC_IDS)))
    return test


for _path in sorted((SKILL_ROOT/"tests/fixtures").glob("*/*.json")):
    setattr(FixtureInventoryTests, f"test_fixture_{_path.stem}", _fixture_test(_path))


if __name__ == "__main__":
    unittest.main()
