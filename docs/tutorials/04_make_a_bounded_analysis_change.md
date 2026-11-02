# Tutorial 4: make a bounded analysis change

**Learning goal:** make one controlled change to a synthetic analysis record and return evidence for review.

- **You are:** a researcher preparing a small local documentation change.
- **You want:** an interpretation note whose claims have identifiable sources.
- **You will use:** the maintained repeated-measurements files, the recorded synthetic result, Git, and the bounded-change template.
- **You will change:** only a new `interpretation.md` in your own scratch analysis repository, after preparing its seed.
- **You will not change:** the coordination checkout's tracked files, data, method, script, tests, environment, or another repository.
- **You should finish with:** one local note commit, its parent, a patch, source identities, and a pending review decision.
- **Prerequisites:** a local TOP26006_fw checkout, a shell, Git, and permission to create the named private practice directory and scratch history. No earlier tutorial run or assistant conversation is required.

## Establish the entry state

Read the [synthetic example's question and limits](../../examples/repeated_measurements/README.md) and the [observed scenario](../../examples/research_workflow_lifecycle/observed_scenario.md). The latter reports five measurements, weighted mean `10.060000`, model-based standard error `0.089443`, chi-square `4.300000`, and four degrees of freedom under independent Gaussian uncertainties. Here you will quote that historical result, not execute a new calculation. This lesson does not establish fresh arithmetic reproduction or a real-data inference.

Start a new shell if needed. Replace `/absolute/path/to/TOP26006_fw` below with your actual coordination checkout. This block declares all its paths locally; it needs no variables from Tutorial 3. The practice directory must be absent. If it exists, inspect it using the restart instructions rather than rerunning setup.

```sh
(
set -eu
cd /absolute/path/to/TOP26006_fw
test -f examples/repeated_measurements/data/measurements.csv
test -f examples/research_workflow_lifecycle/observed_scenario.md
test ! -e reports/diagnostics/tutorial04_practice
mkdir -p reports/diagnostics
mkdir -m 700 reports/diagnostics/tutorial04_practice
mkdir -m 700 reports/diagnostics/tutorial04_practice/analysis_repository
mkdir -m 700 reports/diagnostics/tutorial04_practice/analysis_repository/data
cp examples/repeated_measurements/README.md examples/repeated_measurements/analyze.py examples/repeated_measurements/test_analysis.py reports/diagnostics/tutorial04_practice/analysis_repository/
cp examples/repeated_measurements/data/measurements.csv reports/diagnostics/tutorial04_practice/analysis_repository/data/
cp examples/research_workflow_lifecycle/observed_scenario.md reports/diagnostics/tutorial04_practice/source_scenario.md
cd reports/diagnostics/tutorial04_practice/analysis_repository
git init -q -b main
git config user.name 'Synthetic Researcher'
git config user.email 'synthetic@example.invalid'
git add -- README.md analyze.py test_analysis.py data/measurements.csv
git commit -m 'test: establish synthetic analysis seed'
git rev-parse HEAD
git status --porcelain=v1
sha256sum README.md analyze.py test_analysis.py data/measurements.csv ../source_scenario.md
)
```

The four copied files form the clean seed; `interpretation.md` is absent. Preserve the displayed seed HEAD and hashes in your own lesson record outside the scratch repository. The scenario copy is a fixed documentary input, not a second repository. Compare its CSV hash (`f6b9311f0ce6e675999c5ef31a14d82589179a9f8e82be917df6695c6893c294`) with your copied input. If they differ, stop: the recorded result is not bound to this input.

The [bounded-change template](../../templates/bounded_change_prompt.md) helps state the task: the researcher owns interpretation and acceptance; the prompt author bounds effects; the executor returns evidence. Fill it against live governance before an assistant dispatch. It grants no effects on its own. For this practice, the sole post-seed write is the scratch note plus its exact local commit and evidence outside that repository; no runtime, network, production, or publication is needed.

## Make the bounded change

Open a text editor at the explicit path `/absolute/path/to/TOP26006_fw/reports/diagnostics/tutorial04_practice/analysis_repository/interpretation.md`. Write a short note containing:

1. The five recorded quantities above, attributed to `../source_scenario.md` as historical observations.
2. The independent Gaussian assumption and synthetic, descriptive scope; no real-data interpretation or new execution claim.
3. Your observed seed commit, copied CSV SHA-256, and scenario SHA-256.
4. A statement that review and human acceptance are pending.

Read the complete note. Do not claim that your seed commit is the historical scenario's first-result commit: your scratch history has its own identity.

## Return evidence and stop before acceptance

In a fresh shell, replace the checkout path again:

```sh
cd /absolute/path/to/TOP26006_fw/reports/diagnostics/tutorial04_practice/analysis_repository
git rev-parse HEAD
git status --porcelain=v1
cat interpretation.md
sha256sum README.md analyze.py test_analysis.py data/measurements.csv ../source_scenario.md
```

The expected task delta is only `?? interpretation.md`. An untracked file does not appear in ordinary `git diff`; direct reading is necessary. Compare all fixed-file hashes with the saved seed evidence. Any other change stops staging.

Stage only the note, inspect the full staged diff, then make the local practice commit:

```sh
git add -- interpretation.md
git diff --cached --name-status
git diff --cached --check
git diff --cached
git commit -m 'docs: record synthetic interpretation with provenance'
git rev-parse HEAD HEAD^
git diff HEAD^ HEAD -- interpretation.md
if test -e ../tutorial04_change.patch; then
  printf '%s\n' 'tutorial04_change.patch already exists; inspect it instead of overwriting it' >&2
  exit 1
fi
git diff HEAD^ HEAD -- interpretation.md > ../tutorial04_change.patch
git status --porcelain=v1
```

Run these commands in order, stopping on any failure or unexpected path before committing. Write the patch only if its destination is absent; if it already exists, read and compare it rather than overwriting it. Keep the patch, note, seed/result identities, hash comparisons, and command observations in your lesson record. A clean result and a local commit prove neither pedagogical nor scientific acceptance. An independent reviewer advises; the human owner decides whether this bounded record is acceptable.

## Restart or continue

After interruption, enter the explicit scratch path and inspect HEAD, status, the note, and the saved evidence first. No note and the recorded clean seed means resume at writing. An untracked note means read it and resume review before staging. A staged note means inspect the complete staged diff before any commit. A committed note means verify its parent and contents and resume evidence review; do not commit it again. Missing seed evidence, unexpected history, or changed fixed inputs leaves the state unresolved.

To start the lesson from its initial state, choose a new absent practice directory and replace every `tutorial04_practice` occurrence consistently. Preserve the earlier directory; do not reset, clean, overwrite, or infer ownership of its changes. The seed setup is the only preparation to repeat in the new directory; no Tutorial 3 calculation is required.

Continue to [review returned evidence](05_review_and_accept_returned_evidence.md), which has its own fixed input and does not require this scratch history.
