# Prepare a governance workflow prompt with the D8 compiler

The non-normative D8 compiler prepares an inspectable CPC prompt candidate and
a YAML compilation receipt. It does not dispatch a prompt, perform an effect,
evaluate execution evidence, or accept a result. D8 remains non-normative
during D8-E and D8-F.

Use the Python wrapper and interpreter resolved from the local YAML profile:

```bash
"$wrapper" "$python_interpreter" tools/governance_workflow_compiler.py \
  --feature task.feature --bindings task_bindings.yml \
  --prompt-out generated_prompt.md --receipt-out compilation_receipt.yml
```

Standard Gherkin is the human semantic contract: the feature and scenarios
describe premises, requested actions, observable results, and negative
boundaries. This implementation supports `Feature`, `Scenario`, `Given`,
`When`, `Then`, `And`, `But`, comments, blank lines, and feature/scenario tags.
`And` and `But` inherit the preceding step's role. Unsupported standard
constructs, including `Rule`, `Background`, `Scenario Outline`, and `Examples`,
fail explicitly with a line-referenced diagnostic. This is a bounded subset,
not a full Gherkin implementation. Tags remain visible as classification and
routing hints; they never grant authority or select production by themselves.

The separate binding YAML supplies acquired authority and evidence facts,
repository identities, exact scopes, a CPC context, and, where needed,
requested effects and exact workflow identity facts. Each material binding
names its source identity, acquisition state, validity scope, and exact effect and target if it
authorizes an effect. Gherkin premises are not proof. A positive effect needs
an acquired owner binding plus the exact current CPC permission and
path/ref/action scope. The compiler selects the minimum supported execution
shape and mode from the behavior and bound context. For the bounded two-writer
and two-repository provider/consumer patterns, it constructs stage roles,
ordering, bodies, gates, commit closure, local grants and provenance. Any
supplied `stages` are an inert historical reference; their goals, modes, grants,
gates and ordering do not become the executable plan. Supply exact worker
branch/worktree/base identities in `worker_contract`, repository base and branch
identities in `repositories`, and exact deletion/preservation identities in
`retirement`. The planner binds later stages to prior observed outputs rather
than assuming requested candidate heads are observed facts. An independent
review stage requires compatible delegation. A supported tracked writer needs
an exact owner-bound local ref effect and index/ref scope for commit closure.
Tracked paths are relative to their selected repository, including when two
repositories contain the same relative path.
The bounded provider/consumer planner starts from `NOT_STARTED`; an observed
partial or completed state yields a diagnostic that preserves the supplied
partial-effect record and requires a separately bound continuation or recovery
plan. It does not replay the initial stages.
Other dependent or unfamiliar action patterns fail closed as compiler
limitations. The author must inspect the generated Markdown and receipt
against live governance before any separately
authorized dispatch.

`dispatch_gate` may name three acquired binding IDs: `owner_authorization_binding`,
`manual_governance_review_binding`, and `live_applicability_binding`. Without
them, the receipt marks the candidate prepared while leaving conformance,
owner authorization, and dispatchability unestablished. A failed compile writes
only a diagnostic receipt; it never writes a valid prompt.

The compiler resolves each selected repository module from the live typed
registry. TOPEFT and TOPCOFFEA prompts carry all four native branch-role fields;
an out-of-role development branch or feature namespace fails closed. A matching
feature namespace never grants branch creation. The generated prompt also names
the applicable repository-native policy requirement. Conditional Git,
orchestration, evidence, recovery, model, production and reviewer-prose rule
families are recorded in the receipt with their live source hashes.

The compiler checks the current serialized closed fields against live sources:
typed repository IDs and their prompt scopes, prompt/stage mode, branch policy,
validation ceiling, model, reasoning, delegation, dirty-worktree and preflight
policy, patch kind, foreign-work and staging policy, workflow stop policy,
integration method, publication action and duplicate policy, and production
execution owner. When the applicable source cannot establish an allowed value,
compilation fails closed.
The receipt evaluates traceability across semantic steps, authority/effect
bindings, emitted stages and mechanics, and post-execution evidence paths;
missing material edges prevent a conforming prompt. It emits the evidence and
evaluation contract, but does not ingest execution evidence or evaluate
acceptance. `patch_kind_expected` is checked against the whole plan:
read-only plans use `empty_no_changes`, and supported tracked mutation plans
use `prompt_local`. Other patch kinds are unsupported until exact provenance
semantics are implemented. The maintained prompt validator checks mechanical
validity and internal consistency only; governance completeness remains unassessed. A
generated prompt, receipt, or validator PASS is neither execution nor
acceptance nor normative D8 adoption. Historical H1-H6 comparison belongs to
D8-F.

If the compiler cannot express a manually valid task, use the existing
[manual prompt guide](write_a_prompt_manually.md) and
[prompt validation guide](validate_a_prompt_before_execution.md). A compiler
limitation does not revoke an independently valid manual workflow.
