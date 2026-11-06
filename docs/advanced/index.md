# Advanced workstream coordination

Complete the [core learning route](../tutorials/index.md) first. Its serial task, review, acceptance, continuation, and handoff method is sufficient for ordinary work. Concurrent workstreams are useful when questions and dependencies can be bounded; adding workers is not a measure of maturity or quality.

## Decide whether to enter this route

Start with an ordinary bounded research question and the [serial lifecycle](../explanation/task_lifecycle.md), using one repository when sufficient. Use the [multi-repository lesson](../tutorials/07_coordinate_a_multi_repository_change.md) only when a real dependency crosses repositories. Its [handoff method](../tutorials/09_transfer_work_to_a_collaborator.md) carries evidence without transferring permissions, authority, validation, or acceptance. Parallel work is a separate, conditional choice; it need not involve several repositories.

Enter this route when two bounded questions can produce useful evidence without waiting for each other's unfinished result, or when a second method can challenge a conclusion along a stated independence dimension. Stay serial when the next question needs an accepted upstream answer, inputs are still changing, shared files or services would contend, or coordination and review cost exceed the useful work available. Parallelism is not an achievement level.

## Follow the paper exercise

Start with the [synthetic three-workstream case](../examples/advanced_parallel_workstreams/README.md). It is a paper exercise, not an active project registry. Then follow the tutorials in order:

1. [Coordinate parallel research workstreams](../tutorials/advanced/01_coordinate_parallel_research_workstreams.md).
2. [Reconcile a shared dependency change](../tutorials/advanced/02_reconcile_a_shared_dependency_change.md).

Use the guides to [define responsibilities](../how_to/advanced/define_workstream_responsibilities.md), [coordinate shared files and dependencies](../how_to/advanced/coordinate_shared_files_and_dependencies.md), [reconcile results](../how_to/advanced/reconcile_workstream_results.md), and [stop or resume one workstream](../how_to/advanced/stop_or_resume_one_workstream.md). Look up the [workstream](../reference/advanced/workstream_record.md), [coordination](../reference/advanced/coordination_record.md), and [handoff](../reference/advanced/handoff_record.md) record shapes.

The explanations cover [programme coordination](../explanation/advanced/coordinating_a_research_programme.md), [dependency patterns](../explanation/advanced/parallel_work_and_dependency_management.md), and [authority and continuity](../explanation/advanced/authority_context_and_continuity.md). These responsibilities and evidence checks also work sequentially, without an AI tool.

## Optional implementation aids

A Git worktree supplies a separate checkout and index, which can reduce accidental edit overlap. It does not provide security isolation, separate scientific authority, automatic safe concurrent writes, compatibility, or acceptance. Shared caches, data locations, services, and external jobs still need explicit boundaries.

For TOP-26-006 work in TOP26006_fw, TOPEFT, and TOPCOFFEA, the current operating rule prefers at most one persistent active development worktree per repository/workstream, with the canonical checkout kept separate. Short-lived fixture/test worktrees may exist only temporarily under their own authorization. This is a project operating rule, not universal Git or provider behavior. Dividing responsibilities does not require creating more development worktrees.

Agents or parallel sessions may be optional executors or reviewers inside an authorized, bounded assignment. Separate contexts alone establish neither scientific independence nor permission, repository authority, safe concurrent writes, acceptance, complete provenance, or guaranteed delivery and recovery. A paused conversation does not prove that external work stopped.

Read the [automation and OpenClaw outlook](../explanation/advanced/automation_harnesses_and_openclaw_outlook.md) last, as dated background. Generically, a harness can route tasks, connect approved tools, record activity, or apply mechanical checks. Discussing it does not qualify, adopt, or deploy a TOP-26-006 harness. It supplies no scientific authority or acceptance, complete capture of effective permissions, guaranteed side-effect replay or recovery, or provider equivalence. Provider-specific operating guides and capability qualification require separate work. This route activates no agents, teams, worktrees, harness, scheduler, or provider configuration.
