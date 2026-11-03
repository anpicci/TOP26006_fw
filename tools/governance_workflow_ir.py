"""Immutable decision facts and canonical policy acquisition for D8.

This module describes compilation inputs/results; it never executes a plan.
The selected Git repository is an upstream trust input, not authenticated here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from pathlib import Path
import re
import subprocess
from typing import Any


@dataclass
class Policy_source_binding:
    repository: Path
    master_oid: str = field(init=False)
    blobs: dict[str, str] = field(default_factory=dict, init=False)

    def __post_init__(self):
        self.repository = self.repository.resolve()
        self.master_oid = self._git('rev-parse', '--verify', 'refs/heads/master').decode().strip()

    def _git(self, *args: str) -> bytes:
        return subprocess.check_output(
            ['git', '--no-optional-locks', '-C', str(self.repository), *args],
            stderr=subprocess.PIPE)

    def read(self, path: str) -> bytes:
        if path.startswith('/') or '..' in path.split('/'):
            raise ValueError('policy path must be repository relative')
        blob = self._git('rev-parse', self.master_oid + ':' + path).decode().strip()
        body = self._git('cat-file', 'blob', blob)
        self.blobs[path] = blob
        return body

    def revalidate(self) -> None:
        current = self._git('rev-parse', '--verify', 'refs/heads/master').decode().strip()
        for path, blob in self.blobs.items():
            if self._git('rev-parse', current + ':' + path).decode().strip() != blob:
                raise ValueError('decision-material canonical policy changed: ' + path)

    def receipt(self) -> dict[str, Any]:
        return {'repository': str(self.repository), 'ref': 'refs/heads/master',
                'observed_master_oid': self.master_oid, 'blobs': dict(sorted(self.blobs.items())),
                'trust_boundary': 'upstream-selected repository; observed OID is provenance, not authority'}


def _artifact_path(value: str, *, locator: bool = False) -> str:
    if (not isinstance(value, str) or not value or
            not re.fullmatch(r"/?[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*", value) or
            any(part in {'.', '..'} for part in value.split('/')) or
            (not locator and value.startswith('/'))):
        raise ValueError('unsafe artifact path or locator')
    return value


@dataclass(frozen=True)
class Artifact_spec:
    """Content identity and acquisition evidence, never effect authority.

    Acquired locators are inert paths. Their bytes must be checked by an
    independently authorized materializer; compilation never opens them.
    """
    path: str
    sha256: str
    source_kind: str
    review_evidence: str
    content: str | None = None
    locator: str | None = None

    def __post_init__(self):
        _artifact_path(self.path)
        if not isinstance(self.sha256, str) or not re.fullmatch(r'[0-9a-f]{64}', self.sha256):
            raise ValueError('artifact needs exact SHA-256')
        if not isinstance(self.review_evidence, str) or not self.review_evidence.strip():
            raise ValueError('artifact needs review evidence')
        if self.source_kind == 'synthetic_literal':
            if not isinstance(self.content, str) or self.locator is not None:
                raise ValueError('literal artifact needs exactly one content source')
            body = self.content.encode('utf-8')
            if len(body) > 65536:
                raise ValueError('synthetic literal exceeds bounded fixture size')
            self.verify_bytes(body)
        elif self.source_kind == 'acquired_locator':
            if self.content is not None:
                raise ValueError('acquired artifact cannot also embed literal content')
            _artifact_path(self.locator, locator=True)
        else:
            raise ValueError('artifact lacks supported materialization source')

    @classmethod
    def from_record(cls, path: str, record: dict, review_evidence: str) -> Artifact_spec:
        if not isinstance(record, dict):
            raise ValueError('artifact digest alone lacks materialization source')
        # Existing accepted frozen-postimage input is a compact acquired source.
        if set(record) == {'sha256', 'locator'}:
            return cls(path, record['sha256'], 'acquired_locator', review_evidence,
                       locator=record['locator'])
        if set(record) != {'path', 'sha256', 'source', 'review_evidence'} or record['path'] != path:
            raise ValueError('artifact record path or fields differ')
        if record['review_evidence'] != review_evidence:
            raise ValueError('artifact review binding differs')
        source = record['source']
        if not isinstance(source, dict):
            raise ValueError('artifact source must be a mapping')
        kind = source.get('kind')
        key = 'content' if kind == 'synthetic_literal' else 'locator'
        if set(source) != {'kind', key}:
            raise ValueError('ambiguous artifact source')
        return cls(path, record['sha256'], kind, review_evidence,
                   content=source.get('content'), locator=source.get('locator'))

    def projection(self) -> dict:
        source = {'kind': self.source_kind}
        source.update({'content': self.content} if self.source_kind == 'synthetic_literal'
                      else {'locator': self.locator})
        return {'path': self.path, 'sha256': self.sha256, 'source': source,
                'review_evidence': self.review_evidence}

    def literal_bytes(self) -> bytes:
        if self.source_kind != 'synthetic_literal':
            raise ValueError('acquired locator requires separately authorized materialization')
        return self.content.encode('utf-8')

    def verify_bytes(self, body: bytes) -> None:
        if not isinstance(body, bytes) or hashlib.sha256(body).hexdigest() != self.sha256:
            raise ValueError('artifact postimage digest mismatch')


def artifact_specs(postimages: dict, paths: list[str], review_evidence: str) -> tuple[Artifact_spec, ...]:
    if (not isinstance(postimages, dict) or not postimages or
            len(paths) != len(set(paths)) or set(paths) != set(postimages)):
        raise ValueError('stage paths differ from artifact specification paths')
    return tuple(Artifact_spec.from_record(path, postimages[path], review_evidence)
                 for path in sorted(paths))


def canonical_artifact_relation(values: Any) -> Any:
    """Normalize defined artifact subrelations; retain all surrounding identity.

    Compact acquired records and rich records cross the same Artifact_spec
    boundary. No locator, review, path or non-artifact field is discarded.
    """
    if not isinstance(values, dict):
        return values
    result = dict(values)
    for field, review_field, paths_field in (
            ('frozen_postimages', 'reviewed_evidence', None),
            ('postimages', 'review_evidence', 'paths')):
        if field not in values:
            continue
        records = values[field]
        if not isinstance(records, dict):
            raise ValueError('artifact relation needs a postimage mapping')
        paths = list(records) if paths_field is None else values.get(paths_field)
        if not isinstance(paths, list) or not all(isinstance(path, str) for path in paths):
            raise ValueError('artifact relation needs exact paths')
        artifacts = artifact_specs(records, paths, values.get(review_field))
        result[field] = {artifact.path: artifact.projection() for artifact in artifacts}
    return result


@dataclass(frozen=True, order=True)
class Result_ref:
    stage_id: str
    output: str

    @classmethod
    def parse(cls, value: str) -> Result_ref:
        match = re.fullmatch(r'stage:([A-Za-z0-9_.-]+):([A-Za-z0-9_.-]+)', value)
        if not match:
            raise ValueError('invalid result transport: ' + value)
        return cls(*match.groups())

    def transport(self) -> str:
        return f'stage:{self.stage_id}:{self.output}'


def result_refs(value: Any) -> tuple[Result_ref, ...]:
    """The single decoding boundary for produced-result transport syntax."""
    if isinstance(value, str):
        return (Result_ref.parse(value),) if value.startswith('stage:') else ()
    if isinstance(value, dict):
        # Structured preconditions/evidence contain opaque provenance strings.
        # Only explicit input transports declare result dependencies. Validation
        # operands are separately typed and must be declared as those inputs.
        return ()
    if isinstance(value, (tuple, list)):
        return tuple(ref for item in value for ref in result_refs(item))
    return ()


@dataclass(frozen=True)
class Validation_case:
    provider: Result_ref
    consumer: Result_ref
    expected: str


@dataclass(frozen=True)
class Validation_relation:
    predicate: str
    cases: tuple[Validation_case, ...]

    @classmethod
    def from_contract(cls, contract: dict[str, Any]) -> Validation_relation:
        cases = tuple(Validation_case(Result_ref.parse(row['provider']),
                                      Result_ref.parse(row['consumer']), row['expected'])
                      for row in contract.get('cases', []))
        if not cases or any(row.expected not in {'PASS', 'FAIL_EXPECTED'} for row in cases):
            raise ValueError('validation relation needs exact operands and frozen outcomes')
        if contract.get('matrix') != [row.expected for row in cases]:
            raise ValueError('validation matrix differs from exact relation outcomes')
        if contract.get('predicate') != 'contract equality and protocol membership':
            raise ValueError('unsupported validation predicate')
        return cls(contract['predicate'], cases)

    def projection(self) -> dict[str, Any]:
        return {'predicate': self.predicate, 'cases': [
            {'provider': row.provider.transport(), 'consumer': row.consumer.transport(),
             'expected': row.expected} for row in self.cases],
            'matrix': [row.expected for row in self.cases]}


@dataclass(frozen=True)
class Stage_spec:
    stage_id: str
    outputs: tuple[str, ...]
    inputs: tuple[Result_ref, ...]
    validation: Validation_relation | None = None
    artifacts: tuple[Artifact_spec, ...] = ()


@dataclass(frozen=True)
class Result_graph:
    stages: tuple[Stage_spec, ...]

    @classmethod
    def from_stages(cls, stages: list[dict[str, Any]]) -> Result_graph:
        available: set[Result_ref] = set()
        ids: set[str] = set()
        specs = []
        for stage in stages:
            sid = stage['stage_id']
            outputs = tuple(stage['stage_outputs'])
            if sid in ids or len(outputs) != len(set(outputs)):
                raise ValueError('duplicate stage or output identity')
            inputs = tuple(sorted(set(result_refs(stage['stage_inputs']))))
            if not set(inputs) <= available:
                raise ValueError('unavailable prior-stage result')
            validation = None
            if 'validation_contract' in stage:
                validation = Validation_relation.from_contract(stage['validation_contract'])
                operands = {ref for row in validation.cases for ref in (row.provider, row.consumer)}
                if not operands <= set(inputs):
                    raise ValueError('validation operands are not declared prior-stage inputs')
            artifact_rows = [row['exact_reviewed_postimages'] for row in stage['stage_inputs']
                             if isinstance(row, dict) and 'exact_reviewed_postimages' in row]
            artifacts = ()
            if artifact_rows:
                if len(artifact_rows) != 1:
                    raise ValueError('duplicate artifact declarations')
                reviews = [row['reviewed_result_evidence'] for row in stage['stage_inputs']
                           if isinstance(row, dict) and 'reviewed_result_evidence' in row]
                if len(reviews) != 1:
                    raise ValueError('artifact needs one review binding')
                paths = stage['authorized_commit_scope'][stage['repository_id']]
                artifacts = artifact_specs(artifact_rows[0], paths, reviews[0])
            specs.append(Stage_spec(sid, outputs, inputs, validation, artifacts))
            ids.add(sid)
            available.update(Result_ref(sid, out) for out in outputs)
        return cls(tuple(specs))

    def predecessors(self, stage_id: str) -> set[str]:
        stage = next(stage for stage in self.stages if stage.stage_id == stage_id)
        return {ref.stage_id for ref in stage.inputs}

    def projection(self) -> list[dict[str, Any]]:
        return [{'stage_id': s.stage_id, 'outputs': list(s.outputs),
                 'inputs': [r.transport() for r in s.inputs],
                 'validation': s.validation.projection() if s.validation else None,
                 'artifacts': [a.projection() for a in s.artifacts]}
                for s in self.stages]


def canonical_mapping(value: Any) -> Any:
    """Normalize mapping representation; meaningful sequence order is retained."""
    if isinstance(value, dict):
        return {key: canonical_mapping(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [canonical_mapping(item) for item in value]
    return value
