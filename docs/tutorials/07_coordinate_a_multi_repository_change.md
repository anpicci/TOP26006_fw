# Tutorial 7: coordinate a sequential two-repository change

**Learning goal:** transfer evidence across a genuine repository dependency while keeping each repository's authority, validation, and acceptance separate.

Use this lesson only when the task genuinely crosses two maintained repository boundaries. If one repository is sufficient, stay in one repository. This is an intermediate route after the everyday lifecycle, not a requirement for a newcomer. A second repository may remain read-only when it supplies an interface contract; both repositories need not change.

## Follow the dependency serially

Start with the question you can answer in one repository. Add a second repository only when that answer depends on its maintained result or interface. Call the repository supplying that result the **provider** and the repository using it the **consumer**. These roles belong to this dependency, not permanently to a project.

First identify each repository, its exact commit, relevant local changes, and its own policy and responsible human. State the precise claim to transfer. Attach the minimum evidence supporting it: source and input identities, relevant interface contract, check method and result, limitations, and provider review/acceptance status with its exact scope. A recorded PASS covers only the checks actually performed.

Then continue in the consumer under its own authorization. Reuse accepted provider checks while their sources, inputs, assumptions, and methods remain valid. The consumer still needs evidence that its selected provider revision works at the affected interface with its own configuration and downstream use. Agree the relevant local checks with the consumer's responsible human; provider PASS cannot replace them. Review and accept the consumer result separately. Recording two commits establishes identity, not compatibility or scientific validity.

| Item | Provider side | Consumer side |
| --- | --- | --- |
| Repository identity | Exact repository and commit; relevant local changes | Its own repository and commit; selected provider revision |
| Claim/evidence | State precisely what each artifact supports | State which claim is relied upon and its limits |
| Validation | Provider-local checks and observed results | Consumer-local compatibility and impact checks still required |
| Acceptance | Record responsible human, decision and claim ceiling | Separate responsible-human decision; acceptance does not migrate |
| Permissions | Handoff grants none | Obtain consumer-side authorization for the proposed action |
| Invalidation | Relevant source, input, assumption or method change; missing or contradictory evidence | Consumer configuration, dependency or interface drift may require a fresh local check |
| Repetition | Preserve accepted checks while evidence remains valid | Repeat only invalidated or directly coupled checks |

Provider then consumer is a sufficient normal sequence. If the consumer stops or a compatibility check fails, preserve valid provider evidence and report the unresolved consumer state. Separate histories have no global transaction and imply no automatic rollback. Neither write permission, repository authority, scientific acceptance nor automatic validation crosses with the evidence.

## Dated example: a shared correction interface

Suppose you need to understand what correction evidence to carry from TOPCOFFEA before changing or accepting its use in TOPEFT. The maintained documentation observed locally on **2026-11-02** describes TOPCOFFEA as providing reusable correction mechanisms and packaged shared payload interfaces, while TOPEFT selects their era/tag/payload, working point, enabled variations and analysis application. This is one correction-interface family example, not a choice of calibration or scientific policy.

The observation is bound to these separate local identities:

- Provider TOPCOFFEA: `7363c89a16c8e08632e2eac23040eb09324beb5a`.
- Consumer TOPEFT: `22f1ff174c10eb5cd4900ba08b1943b85e24b8a4`.

Read the native files at those revisions: TOPCOFFEA's `docs/correction_interfaces.md` (mechanism/policy boundary) and `docs/topeft_integration.md` (interface responsibilities and ref selection); TOPEFT's `docs/reference/shared_topcoffea_interfaces.md` (corrections and calibrated objects) and `docs/how_to/corrections_weights_and_systematics.md` (shared-mechanism route). Locate the checkouts through the [native-repository bridge](02_add_an_analysis_repository.md). Operational instructions remain in those native manuals.

Those docs say the consuming workflow selects an exact compatible TOPCOFFEA ref and both commits must be recorded. Similar branch names are not compatibility evidence. These observed commits identify the documentation read; they are **not a qualified compatible pair** or a timeless dependency prescription. No native execution or compatibility check supports this example.

For a future authorized correction change, hand over the exact provider revision, affected interface contract, provider check artifacts and their limits, plus actual review/acceptance status. If checks have not run or acceptance is pending, say so. TOPEFT can reuse still-valid provider evidence, but must verify its own selected dependency, dispatch and affected downstream use under native authority before accepting its result. That consumer check is pending in this reading example. A relevant provider interface or consumer configuration change invalidates the corresponding part of the handoff; simply introducing a second repository does not invalidate unrelated accepted work.

**Checkpoint:** explain why this question needs two authorities, which evidence can be reused, which consumer check remains, and who may authorize and accept that consumer action. Use the [handoff template](../../templates/handoff.md) to record the unresolved boundary.

## Optional scratch practice: analysis to methods

The following continues the synthetic serial exercise. It does not authorize work in either native repository.

Continue from [Tutorial 6](06_continue_from_existing_evidence.md) with your `analysis`, `accepted_analysis_head`, `csv_sha256`, and `practice_root`. The [lifecycle fixture](../../examples/research_workflow_lifecycle/README.md) provides a methods seed. Both repositories here are diagnostics-local teaching copies, not real governed project repositories.

1. Verify the source before transfer:

   ```sh
   test "$(git -C "$analysis" rev-parse HEAD)" = "$accepted_analysis_head"
   test "$(sha256sum "$analysis/data/measurements.csv" | cut -d ' ' -f1)" = "$csv_sha256"
   git -C "$analysis" status --porcelain=v1 -- interpretation.md data/measurements.csv analyze.py
   cat "$analysis/interpretation.md"
   ```

   If a test fails or task paths are dirty, stop. The bounded evidence object is the calculation, input hash, source commit, repaired note, review finding, and **simulated teaching acceptance** of synthetic arithmetic.
2. Create your own separate methods repository only after the analysis record is qualified:

   ```sh
   cp -R "$checkout/examples/research_workflow_lifecycle/methods_seed" "$practice_root/methods_repository"
   methods="$practice_root/methods_repository"
   git -C "$methods" init -q -b main
   git -C "$methods" config user.name 'Synthetic Researcher'
   git -C "$methods" config user.email 'synthetic@example.invalid'
   git -C "$methods" add -- README.md
   git -C "$methods" commit -m 'docs: establish synthetic methods seed'
   ```

3. Under this teaching authorization, write only `methods_note.md`. Carry the qualified quantities and their limits; use your own source identity:

   ```sh
   cat > "$methods/methods_note.md" <<EOF
   # Synthetic methods evidence
   Analysis source commit: $accepted_analysis_head
   Input CSV SHA-256: $csv_sha256
   Observed local-wrapper result: five rows; weighted mean 10.060000;
   standard error 0.089443; chi-square 4.300000; four degrees of freedom.
   Assumption: independent Gaussian uncertainties and one common mean.
   Review: bounded provenance finding repaired in the analysis note.
   Acceptance: simulated teaching owner acceptance of synthetic arithmetic only.
   Limit: no real-data method, interpretation, production, or publication claim.
   EOF
   git -C "$methods" status --porcelain=v1
   git -C "$methods" add -- methods_note.md
   git -C "$methods" diff --cached -- methods_note.md
   git -C "$methods" commit -m 'docs: record qualified synthetic methods evidence'
   methods_evidence_head="$(git -C "$methods" rev-parse HEAD)"
   ```

4. Check `git -C "$methods" status --porcelain=v1` and `git -C "$analysis" rev-parse HEAD`. The methods commit must cite `accepted_analysis_head` while the analysis repository stays at its own head. Neither commit authorizes edits in the other repository.

**Verified reference run:** the [observed scenario](../../examples/research_workflow_lifecycle/observed_scenario.md) records different analysis and methods commit IDs for one prior run.

**Checkpoint:** your methods note cites your own analysis source and its qualified evidence. Continue to [the stopped task](08_recover_from_a_stopped_task.md).
