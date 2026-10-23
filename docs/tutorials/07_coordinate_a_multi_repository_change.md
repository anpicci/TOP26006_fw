# Tutorial 7: coordinate a sequential two-repository change

**Learning goal:** carry qualified analysis evidence into a separate methods record without confusing their authority or Git histories.

The [lifecycle fixture](../../examples/research_workflow_lifecycle/README.md) has an analysis seed and a minimal methods seed. The [observed scenario](../../examples/research_workflow_lifecycle/observed_scenario.md) records two diagnostics-local scratch repositories and simulated review/acceptance roles. No real TOP-26-006 child repository was used.

1. In the analysis scratch repository, identify the teaching scenario's qualified commit `c9f7c6b9e090fdc3ae3c29b34171cf3a7cb88ff4`, the CSV SHA-256, observed output, simulated review, and narrow illustrative acceptance. This is the bounded evidence object.
2. Only *after* that review, authorize a distinct task in the methods scratch repository. Its allowed path is `methods_note.md`; its input is the qualified evidence object, not blanket permission to inspect or edit the analysis repository. The methods note records mean `10.060000`, standard error `0.089443`, chi-square `4.300000`, four degrees of freedom, model assumptions, source identity, and the real-data limitation.
3. Observe the separate methods commit `09a97e3ced516e662a8e448f01b9199805c3ea80`. The two scratch repositories have separate `git status`, HEAD, index, and owner decisions. Local-profile paths identify locations; the [typed registry](../../governance/repositories.md) identifies durable roles; fresh Git readback establishes current state. The scratch repositories are teaching copies and are not registry entries.
4. Check the evidence boundary: the methods record consumed only the accepted analysis quantities and provenance it needed. A successful analysis command granted no methods mutation authority; the methods commit granted no analysis authority.

**Checkpoint:** you can explain sequential evidence flow across two research roles. Simultaneous development workstreams and their coordination machinery are a later topic. Continue to [a stopped task](08_recover_from_a_stopped_task.md).
