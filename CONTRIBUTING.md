# CONTRIBUTING.md

# PR, review, and merge-message style contract

TOP26006_fw uses this common, diff-driven PR and review style across its
project coordination work. The local checkout remains `correction-lib`.

This document governs:

```text
PR titles
PR descriptions
squash-and-merge messages
branch hygiene notes
test-expectation language
reviewer-facing caveats
repository commit subjects
```

For Codex prompt construction and execution policy, see:

```text
AGENTS.md
CPC.md
```

---

## 1. Policy precedence

Policy precedence for this workspace:

1. `AGENTS.md` controls runtime execution, git hygiene, repo permissions, validation, artifact paths, and commit behavior.
2. `CPC.md` controls how ChatGPT should prepare Codex prompts.
3. `CONTRIBUTING.md` controls PR titles, PR descriptions, squash-and-merge messages, branch hygiene notes, test-expectation language, and reviewer-facing text.
4. A user prompt may override these rules only when the override is explicit.
5. If two policies conflict, stop and ask for clarification or report the conflict.

An applicable TOP26006_fw repository module named by
`governance/repositories.md` may add repository- or document-specific reviewer
constraints under this common policy. It may not weaken evidence honesty,
scope, safety, or approval language here. Repository-native scientific and
technical documentation remains with its semantic owner; this reviewer policy
does not transfer its content to project governance. External ANDOCS at its
current path retains its local reviewer policy until the Phase-3 applicability
gate is proved.

---

## 2. Standing PR contract

When preparing a PR description for this repo, use the **house PR template** below by default.

The author may opt out only by explicitly saying:

```text
opt out of the PR template
```

or an equivalent explicit instruction.

PR descriptions must be:

* **diff-driven** — describe what changed, why, and how it was verified;
* **concrete** — prefer file/function-level details over generalities;
* **honest about scope** — distinguish the latest focused change from cumulative branch changes;
* **honest about validation** — distinguish targeted tests, full tests, and production validation;
* **clear about semantics** — avoid changing physics/analysis semantics unless the PR explicitly intends to do so; call out semantics changes clearly.

Reviewer-facing material must use repository-focused language. Do not include:

* prompt IDs;
* Codex references or jargon;
* internal workflow labels;
* local user-specific paths;
* user-specific manager names;
* Codex model names, reasoning levels, delegation modes, token usage, or capacity incidents.

This restriction applies to PR titles, PR descriptions, squash titles, squash messages, reviewer-facing caveats, and commit subjects. Prompt IDs, model/reasoning metadata, delegation details, capacity events, and internal labels may remain in diagnostics paths, reports, patch artifact names, and internal handoff notes, but they must be translated into repository-focused prose before review material is prepared.

Avoid generic summaries.

Prefer concrete details such as:

```text
analysis/analysis_processor.py
topcoffea/modules/<module>.py
tests/test_<surface>.py
input_samples/cfgs/<cfg>.cfg
run_cr.sh
fullR3_run.sh
```

---

## 3. Repository commit, PR, and squash subject style

Use a light Conventional-Commit-style subject:

```text
<type>[optional scope]: <description>
```

Recommended types are `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `build`, `ci`, `chore`, `style`, and `revert`.

Use a concise, action-oriented description of the main diff axis. This form applies to repository commit subjects, PR titles, and squash titles.

Prefer:

```text
fix(topeft): align Run 2 jet JEC levels
fix(topeft): apply Run 3 jet veto maps after JEC/JER
feat(topcoffea): add Run 3 muon momentum corrections
docs(governance): clarify validation ceilings
```

Avoid:

```text
Updates
Fix stuff
Misc changes
Changes
chore: updates
```

If the PR is broader than the title’s main axis, either:

1. choose a broader but still precise title; or
2. keep the focused title and call out the broader cumulative diff in `Review notes`.

---

## 4. House PR template

Use this structure and tone:

```text
### Summary

### Motivation

### Implementation details

### Testing

### Review notes
```

---

## 5. Summary section

Provide 2–6 bullets describing the main axes of change.

Keep them headline-level and action-oriented.

Good examples:

```text
- Move Run 3 jet-veto-map evaluation after JEC/JER and object-systematic application.
- Align Run 2 regular-jet JEC levels with the Type-1 MET correction convention.
- Add focused tests for Run 3 veto-map input selection and MET collection policy.
```

Avoid vague bullets:

```text
- Update code.
- Fix tests.
- Improve workflow.
```

---

## 6. Motivation section

Explain why the change is needed.

When applicable, describe:

* observed issue;
* failure mode;
* stale test expectation;
* review request;
* maintenance burden;
* physics or object-review motivation;
* workflow/runtime mismatch.

Good examples:

```text
The Run 3 jet veto maps must be evaluated on the same corrected/smeared jet kinematics used by the active JES/JER object variation. The previous ordering evaluated the veto-map inputs before the JEC/JER sequence, which made the veto-map decision inconsistent with the object-systematic loop.
```

```text
The cumulative branch had Run 2 regular-jet corrections using a different JEC level convention from Type-1 MET. This PR aligns the regular-jet and Type-1 MET correction-level handling.
```

---

## 7. Implementation details section

Break down the work into logical sections.

Use concrete notes such as:

* modules/files changed and why;
* behavior or semantics changed;
* behavior explicitly unchanged;
* notable edge cases handled;
* new tooling/scripts and how they are used;
* configuration changes and their rationale;
* whether the description covers the latest focused change or the branch-cumulative diff;
* whether any binary/payload files are included.

When helpful, include short code excerpts or config snippets to anchor key points.

Suggested format:

```text
A. <logical area>

- Changed `<file>` to ...
- Added/updated `<function_or_helper>` to ...
- Preserved ...
- Did not change ...

B. <logical area>

- Updated `<test_file>` to cover ...
- Added regression coverage for ...
```

Use `snake_case` for new code identifiers and coding examples.

---

## 8. Testing section

List what was run and what it covers.

Prefer explicit commands.

Examples:

```text
- `python -m compileall analysis tests`
- `python -m pytest -q tests/test_run3_veto_map_input_selection.py`
- `python -m pytest -q tests/test_met_collection_policy.py`
```

If commands were run through a wrapper or controlled environment, mention that.

Disclose material warnings and skips. State what emitted them, whether they
affect the reviewed behavior, and whether they are resolved, accepted with
evidence, or remain an explicit limitation. Do not hide them behind an overall
pass statement.

Do not mention which Codex model, reasoning level, or delegation mode executed the tests. Reviewer-facing validation should describe commands, inputs, outputs, and results. A model-capacity interruption belongs in the internal report unless it caused missing or incomplete validation evidence; in that case, describe only the resulting validation limitation.

If tests are intentionally scoped, say so.

Do not write:

```text
Tests passed.
```

unless the relevant requested test scope actually passed.

Use precise testing language:

```text
Targeted tests passed; full pytest was not run.
Targeted tests passed; full pytest still has unrelated/pre-existing failures.
Compile/import checks passed; production campaign validation was not run.
Production validation is pending and must not be inferred from unit tests.
Full pytest passed.
Full pytest was not run because this PR only prepares reviewer-facing text and does not change source code.
```

If full pytest fails in unrelated or pre-existing areas, say:

```text
Targeted tests for the changed surface passed. Full pytest was attempted but still fails in broader/pre-existing areas unrelated to this PR.
```

Do not imply production validation from unit tests, compile checks, or synthetic tests.

---

## 9. Review notes section

Use `Review notes` to focus reviewer attention.

Call out, when applicable:

* physics or analysis semantics changed;
* behavior intentionally unchanged;
* cumulative diff broader than the central change;
* generated or binary artifacts;
* payload files;
* config naming conventions;
* backwards-compatibility concerns;
* no-shims decisions;
* targeted vs full-test limitations;
* production validation not performed;
* dirty-branch or branch-cumulative context;
* follow-up items intentionally left out of scope.
* migration or deletion successor, ownership, and affected-consumer status, or
  evidence-backed intentional retirement;
* which closure claims are actually established and which remain separate.

Do not use `Review notes` to expose internal model-selection, token-consumption, reasoning-level, delegation, or capacity details. Translate any resulting limitation into evidence-focused language, such as which validation step did not complete.

Examples:

```text
- Reviewers should check the ordering of Run 3 jet-veto-map evaluation relative to JEC/JER and object-systematic application.
- The cumulative branch includes workflow/script changes in addition to the JME correction changes; reviewers should decide whether those should remain in this PR or be split.
- This PR is validated by targeted tests only. It does not include production-scale yield validation.
- The Run 2 JES Case-II regrouping is intentionally not addressed here and remains a follow-up with JME.
```

If there are no special notes, write:

```text
No special review notes beyond the changed files listed above.
```

Do not write “No concerns” if testing or production validation was intentionally scoped.

---

## 10. Scope breadth and split-PR notes

PR material must explicitly identify whether it describes the latest focused change or the full branch-cumulative diff. If the branch includes earlier commits or broader scope, call that out in `Review notes` using repository-focused language.

If the PR includes changes outside the main behavioral axis, the PR description must call this out in `Review notes`.

Examples of broader scope:

* workflow/script changes included with analysis-code changes;
* sample cfg changes included with object-correction changes;
* test-only alignment included with runtime behavior changes;
* vendored payloads or binary files included with code changes;
* PR-preparation-only changes mixed with source changes;
* unrelated dirty work included in the cumulative branch diff.

Recommend splitting the PR when independent behavior, documentation, configuration, generated artifacts, or repository-boundary changes can be validated and reverted independently. Cross-repository changes should normally be reviewed in their respective repositories even when coordinated by one workspace task.

For an integration or reconciliation PR, describe the complete
reviewer-visible delta, including surviving upstream behavior and removed or
superseded surfaces. Do not describe only the latest reconciliation commit.

When the broader diff could reasonably be split, say so explicitly.

Suggested wording:

```text
The cumulative diff is broader than the central change. It also includes `<file_or_area>`. Reviewers should decide whether those changes should remain in this PR or be split into a separate PR.
```

---

## 11. Physics and analysis semantics

Avoid changing physics/analysis semantics unless the PR explicitly intends to do so.

If semantics change, call out:

```text
what changed
why it changed
which samples/years/categories are affected
whether the change affects nominal behavior, systematics, or both
which validation was run
what remains unvalidated
```

If semantics did not change but the diff is near sensitive code, say so explicitly:

```text
This PR changes ordering/test coverage only and does not intentionally change the configured JES source schema.
```

```text
This PR adds the correction interface and tests, but does not wire the new object variation into the analysis processor.
```

---

## 12. Focused vs cumulative diff

When a PR is based on a branch that contains earlier commits or existing dirty work, distinguish:

```text
latest focused change
branch-cumulative change
pre-existing dirty work
```

Use explicit language:

```text
The latest focused commit changes `<files>`.
The branch-cumulative diff also includes `<files>`.
The PR description below covers the full cumulative diff intended for review.
```

Do not describe a cumulative branch diff as if it were created entirely by the latest focused change. Internal terms such as prompt IDs or prompt-local labels must be translated into the repository-focused wording above.

---

## 13. Binary files and generated artifacts

If binary files, payloads, generated figures, large pkls, or other non-text artifacts are included, the PR description must list:

```text
path
why it is included
how it was produced or sourced
whether it is required at runtime
whether it was regenerated in this PR
```

Do not inline binary content.

If artifacts are generated but not committed, say so:

```text
Generated diagnostic artifacts were written under `<path>` and are not committed.
```

---

## 14. Branch hygiene notes

When preparing branch hygiene notes, state:

```text
base/reference branch
feature branch or existing target branch
whether the branch was created from the reference branch
whether the checked-out branch is the current integrated baseline
whether the branch contains earlier commits
whether focused and cumulative diffs were distinguished
whether unrelated dirty work remains
```

Translate internal branch-policy fields into repository-focused prose. For example:

```text
This feature branch was created from `run3_test_mmerged_anpicci`.
This work continues on the existing integration branch.
The repository was inspected without changing its checked-out branch.
```

Keep keys such as `branch_policy` and `integrated_baseline_mode` in internal reports; do not copy them into reviewer-facing branch notes.

Do not hide branch ambiguity.

If branch origin is uncertain, say:

```text
Branch origin was not verified and should be checked before opening the PR.
```

---

## 15. Squash-and-merge message style

The squash title must use:

```text
<type>[optional scope]: <description>
```

The squash message should preserve the same structure as the PR description when the PR contains nontrivial analysis logic, workflow changes, or validation caveats.

At minimum, include:

* main behavior change;
* important files or modules changed;
* validation performed;
* known limitations or intentionally scoped tests;
* follow-up items that should not be lost.

Suggested structure for nontrivial PRs:

```text
<type>[optional scope]: <description>

Summary:
- ...
- ...

Validation:
- ...

Notes:
- ...
```

For very small PRs, a concise squash message is acceptable if it still preserves the important context.

Avoid squash messages like:

```text
fix
updates
misc
```

Do not copy diagnostics identifiers, Codex terminology, model/reasoning/delegation metadata, token or capacity commentary, internal workflow labels, local user-specific paths, or user-specific manager names into the squash title or body.

---

## 16. Review-material honesty rules

Reviewer-facing text must distinguish:

```text
confirmed by the diff
confirmed by tests
plausible but not proven
not tested
out of scope
follow-up item
```

Use closure language literally. Test completion, remote publication, upstream
merge, and repository-history normalization are distinct claims; none should
be implied by another. For a migration, deletion, or deprecation, disclose the
successor and owner for affected consumers, or state the evidence-backed
intentional retirement.

Do not claim:

```text
full pytest passed
production validation completed
final datacards were verified
no regression
physics semantics unchanged
```

unless the evidence actually supports it.

Do not describe a diagnostic aggregate as the fitted or otherwise consumed
object unless direct consumer-side evidence supports that wording. Describe a
ratio to a stored statistical scale as descriptive, not a formal pull or
significance, unless the stated covariance and statistical model support the
formal claim. When a historical/current comparison excludes incompatible
binning or other non-like-for-like objects, say so rather than implying a
forced remapping or broader comparison.

Prefer:

```text
Targeted tests passed; full pytest was not run.
Targeted tests passed; full pytest still has unrelated/pre-existing failures.
Implementation validation passed; production campaign validation was not run.
No intentional physics semantic change is introduced by this PR.
```

---

## 17. Example PR description

```text
### Summary

- Move Run 3 jet-veto-map evaluation after the JEC/JER and object-systematic sequence.
- Apply the veto-map input selection to lepton/tau-cleaned AK4 PUPPI jets with corrected/smeared pT.
- Add focused regression coverage for the veto-map input helper and MET collection policy.

### Motivation

Run 3 jet veto maps should be evaluated using the same corrected/smeared jet kinematics used by the active JES/JER object variation. The previous ordering evaluated the veto-map decision before the correction/systematic sequence, making the veto-map input inconsistent with the object-systematic loop.

### Implementation details

A. Run 3 jet-veto-map ordering

- Updated `analysis/analysis_processor.py` so the Run 3 jet-veto-map input selection is evaluated after `ApplyJetCorrections(...)` and `ApplyJetSystematics(...)`.
- Kept the veto-map input jets lepton/tau-cleaned.
- Preserved the intended veto-map input requirements: corrected/smeared pT > 15 GeV, tightLepVeto-equivalent AK4 PUPPI ID, and `chEmEF + neEmEF < 0.9`.

B. Tests

- Added/updated `tests/test_run3_veto_map_input_selection.py` to cover the helper-level input selection.
- Updated `tests/test_met_collection_policy.py` to preserve the Run 2/Run 3 MET collection expectations.

### Testing

- `python -m compileall analysis tests`
- `python -m pytest -q tests/test_run3_veto_map_input_selection.py`
- `python -m pytest -q tests/test_met_collection_policy.py`

Targeted tests passed. Full pytest was attempted but still has broader/pre-existing failures outside the edited surface.

### Review notes

- Reviewers should focus on the ordering of Run 3 jet-veto-map evaluation relative to JEC/JER and object-systematic application.
- This PR is validated by targeted source-order/helper tests, not by production-scale yield validation.
- The cumulative branch should be checked for workflow/sample-config changes that may be better split into a separate PR.
```

---

## 18. Final checklist for PR material

Before finalizing PR material, check:

```text
PR title is specific and action-oriented
PR description uses the house template unless explicitly opted out
Summary has 2–6 action-oriented bullets
Motivation explains the issue or need
Implementation details are file/function-level where possible
Testing includes explicit commands and honest scope
Review notes call out risky or broad areas
Latest focused vs branch-cumulative diff is clear
Physics/analysis semantics are explicit
Production validation is not overclaimed
Full pytest status is not overclaimed
Broader diff/split-PR question is called out when relevant
Squash message preserves important context
Commit, PR, and squash subjects use `<type>[optional scope]: <description>`
Reviewer-facing text contains no prompt IDs, Codex references, model/reasoning/delegation metadata, token or capacity commentary, internal workflow labels, local user-specific paths, or user-specific manager names
Independent behavior, documentation, config, generated-artifact, or repository-boundary changes are split or explicitly justified
```
