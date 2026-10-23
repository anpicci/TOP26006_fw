# Tutorial 5: review and accept returned evidence

**Learning goal:** separate an executor's completion claim from observations, review findings, and a human acceptance decision.

Use the [recorded analysis scenario](../../examples/research_workflow_lifecycle/observed_scenario.md) from Tutorial 4. Its first result commit is `eb40d2703e74350e09e00c459459d706bbc8fa74`. The reviewer and owner entries in this teaching run are simulated roles; a real task needs separate human review and owner decision.

1. Read the executor report as a *claim*: `interpretation.md` reports the weighted mean and model assumptions. The report alone proves neither the calculation nor the adequacy of provenance.
2. Inspect observed evidence: the wrapper output reports mean `10.060000`, standard error `0.089443`, chi-square `4.300000`, four degrees of freedom; the input CSV SHA-256 begins `f6b9311f`; the first result changed only `interpretation.md`. Compare those identities with the source and [example method](../../examples/repeated_measurements/README.md).
3. Record two different review findings in the [review report](../../templates/review_report.md). The arithmetic agrees with the observed run, within the stated model. The first note omits source commit and input hash, a bounded provenance defect. Treat that as **blocking for acceptance of the note**, while preserving the valid arithmetic evidence. A wording preference that does not change traceability or the claim would be nonblocking.
4. Review the provenance repair at analysis commit `c9f7c6b9e090fdc3ae3c29b34171cf3a7cb88ff4`. The repair adds the first result commit, CSV hash, execution route, and limits. In the simulated owner role, record an illustrative acceptance of only the bounded arithmetic record. Acceptance of the model for real data remains unacquired.

**Checkpoint:** your record has four distinct entries: executor report, direct observations, independent finding, and owner acceptance scope. A valid prior result survives a narrow repair. Continue to [continuation](06_continue_from_existing_evidence.md).
