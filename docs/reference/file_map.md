# File map

Choose a destination by what you need to do. Learning pages and how-to guides explain the work; the live authority sources below define the applicable rules. A link or template grants no action.

## Reader entry and learning

| Location | What to use it for |
| --- | --- |
| [README](../../README.md), [manual index](../index.md), [getting started](../getting_started.md) | Enter the manual and choose a short research route. |
| [Tutorial learning path](../tutorials/index.md) | Follow the canonical guided curriculum, with lesson starting points, outcomes, and optional extensions. |
| [Research foundations](../foundations/ai_assisted_research.md), [research workflow](../explanation/research_workflow.md), [roles and authority](../explanation/roles_and_authority.md), [research-oriented writing](../explanation/research_oriented_writing.md) | Understand the method and the responsibilities of people and tools. Explanatory documentation. |
| [Synthetic measurements](../../examples/repeated_measurements/README.md), [companion notebook](../../examples/repeated_measurements/repeated_measurements.ipynb) | Explore invented teaching data and the maintained calculation; the notebook calls its functions and stores no executed output. |
| [First read-only task](../tutorials/03_complete_a_first_read_only_task.md) | Complete one small task without a native analysis checkout; use [Tutorial 1](../tutorials/01_prepare_a_research_project.md) when local execution needs setup. |

## Research task help and tutorials

| Intent | Maintained destination |
| --- | --- |
| Prepare a bounded request | [Ask an assistant to prepare a task](../how_to/ask_an_assistant_to_prepare_a_task.md) |
| Inspect a scientific repository | [TOPEFT repository lesson](../tutorials/02_add_an_analysis_repository.md), an optional bridge to a separately resolved native checkout |
| Make, review or continue a change | [Bounded change](../tutorials/04_make_a_bounded_analysis_change.md), [review and acceptance](../tutorials/05_review_and_accept_returned_evidence.md), [continuation](../tutorials/06_continue_from_existing_evidence.md) |
| Recover or hand off work | [Stopped task](../tutorials/08_recover_from_a_stopped_task.md), [collaborator handoff](../tutorials/09_transfer_work_to_a_collaborator.md) |
| Adapt an installation | [Paths and remote aliases](../how_to/adapt_paths_and_remotes.md), [workspace and checkout names](../how_to/choose_workspace_and_checkout_names.md): map local installation facts without changing repository identity |
| Inspect evidence before proposing a change | [Read-only examination](../how_to/perform_a_read_only_examination.md): bound observations and return their limits |
| Preserve existing work | [Existing local changes](../how_to/handle_existing_local_changes.md), [reuse prior evidence](../how_to/reuse_prior_evidence.md), [prepare a continuation](../how_to/prepare_a_continuation.md): identify ownership, retain valid closure and request only the delta |
| Check setup or a common stop | [Prerequisites](../how_to/check_prerequisites.md), [diagnose common stops](../how_to/diagnose_common_stops.md) |
| Find a teaching aid | [Task request](../../templates/research_task_request.md), [read-only prompt skeleton](../../templates/read_only_prompt.md), [bounded change](../../templates/bounded_change_prompt.md), [continuation](../../templates/continuation_prompt.md), [review](../../templates/review_report.md), [handoff](../../templates/handoff.md) templates; they grant no action |
| Inspect the lifecycle teaching case | [Lifecycle fixture](../../examples/research_workflow_lifecycle/README.md); scratch Git copies are diagnostic only |

These are explanatory task aids. They do not replace native instructions or the applicable live execution contract.

## Coordination and advanced material

| Location | When it helps |
| --- | --- |
| [Multi-repository lesson](../tutorials/07_coordinate_a_multi_repository_change.md), [multi-repository research](../explanation/multi_repository_research.md) | A real dependency crosses repository boundaries; ordinary tasks can remain in one repository. |
| [Advanced route](../advanced/index.md), [advanced tutorials](../tutorials/advanced/01_coordinate_parallel_research_workstreams.md) | Optional coordination learning after the core route; start with the route's decision about whether to enter. |
| [Advanced how-tos](../how_to/advanced/define_workstream_responsibilities.md), [advanced reference](advanced/workstream_record.md), [advanced explanations](../explanation/advanced/coordinating_a_research_programme.md) | Workstream procedures, record shapes and rationale. |
| [Synthetic parallel workstreams](../examples/advanced_parallel_workstreams/README.md) | Four-file teaching case; no live registry or execution. |

These pages explain coordination; they do not authorize agents, parallel writes or cross-repository effects.

## Maintainer and task-author how-to

These guides explain how to prepare or propose an operation. The authority column locates the live sources to consult; it does not duplicate their rules.

| I need to… | Explanatory destination | Authority to locate |
| --- | --- | --- |
| Register or update repository metadata | [Repository registration](../how_to/register_repositories.md) | [Registry](../../governance/repositories.md), its selected module, applicable [AGENTS.md](../../AGENTS.md) and native policy |
| Add or update a governance module | [Governance module guide](../how_to/add_or_update_a_governance_module.md) | Root/path [AGENTS.md](../../AGENTS.md), [CPC.md](../../CPC.md), relevant [governance contracts](governance_precedence.md) |
| Write a governed prompt manually | [Manual prompt authoring](../how_to/write_a_prompt_manually.md) | [CPC.md](../../CPC.md), applicable governance, [repository module](../../governance/repositories.md) and native policy |
| Prepare a prompt for a supported workflow pattern | [Governance workflow compiler](../how_to/compile_governance_workflow.md) | Current `refs/heads/master` [CPC.md](../../CPC.md), applicable governance, [repository module](../../governance/repositories.md) and native policy |
| Validate a completed prompt mechanically | [Prompt validation](../how_to/validate_a_prompt_before_execution.md) | Maintained [skill instructions](../../.agents/skills/correction-lib-prompt-contract/SKILL.md), [schema](../../.agents/skills/correction-lib-prompt-contract/references/prompt_schema.json) and [validator](../../.agents/skills/correction-lib-prompt-contract/scripts/validate_prompt.py); live governance still controls |
| Inspect prompt fields and semantics | [Prompt contract reference](prompt_contract.md) | [CPC.md](../../CPC.md) and applicable [governance sources](governance_precedence.md) |
| Configure an installation | [Profile configuration](../how_to/configure_your_local_profile.md), [local-profile reference](local_profile.md) | [Example profile](../../config/local_profile.example.yml), [schema](../../config/local_profile.schema.yml), [resolver](../../tools/resolve_local_profile.py) define installation shape/resolution; `.top26006/local_profile.yml` holds ignored local facts, not permissions |

Validator PASS is mechanical evidence only; it does not establish governance completeness, authorization, branch applicability or scientific correctness.

Manual governed prompt authoring remains a first-class route for any task that can be expressed within the manual contract, whether the author is a person or an authorized assistant. The governance workflow compiler is an optional authoring aid for supported workflow patterns. It produces an inspectable prompt and compilation receipt; it does not create authority, dispatch, execute, review or accept the task. Use manual governed authoring when the required pattern is not supported. The compiler guide is not a prerequisite for the research tutorials.

## Reference and navigation

| Location | Primary role |
| --- | --- |
| [Glossary](glossary.md), [file map](file_map.md), [manual index](../index.md) | Terms, document roles and intent-based navigation. |
| [Governance precedence](governance_precedence.md), [prompt contract](prompt_contract.md), [modes](prompt_modes.md), [permissions](permissions.md), [branches](branch_policies.md), [ceilings](validation_ceilings.md), [evidence states](evidence_and_task_states.md), [report contract](report_contract.md) | Lookup aids pointing to live normative sources; not a second policy registry. |
| [Provider adaptation](../how_to/adapt_to_another_ai_provider.md), [OpenAI procedure](../how_to/providers/openai_reference_procedure.md), [Claude adaptation](../how_to/providers/anthropic_adaptation.md) | Existing provider routes; the Claude mapping is documentary. |
| [Compatibility matrix](provider_compatibility.md), [provider limits](../explanation/provider_independence_and_limits.md) | Existing lookup state and explanation of portability limits. |
| [TOP-26-006 worked deployment](../examples/top26006_reference_deployment.md) | Dated project-specific case study, not a universal configuration. |
| [Legacy agentic URLs](../agentic/README.md) | Routing pages to current guidance and the worked deployment. |

## Normative governance authority

| Live source | Authority role |
| --- | --- |
| [AGENTS.md](../../AGENTS.md) and applicable path/native policies | Execution and required-reading router; follow the contracts it selects. |
| [CPC.md](../../CPC.md) | Prompt construction contract. |
| [CONTRIBUTING.md](../../CONTRIBUTING.md) | Contribution and reviewer-writing contract. |
| [Repository registry](../../governance/repositories.md) | Stable repository identities, roles, module selection and native scientific/technical responsibility locators. |
| [Git lifecycle](../../governance/contracts/git_lifecycle.md), [review and evidence](../../governance/contracts/review_and_evidence.md), [orchestration](../../governance/contracts/orchestration.md) | Conditional operating contracts; use the root router to select all applicable sources. |

Consult current live authority when authoring or executing a task. Documentation and mechanical helpers cannot create authorization from the research lead.

## Native repository authority

For an analysis question, move from the [coordination manual](../index.md) to the [repository registry](../../governance/repositories.md), then open the native documentation and source in the separately resolved checkout. TOP26006_fw coordinates and teaches routing; the native repository owns its scientific and technical behavior. Record that checkout's current Git branch, commit and relevant local changes. [Tutorial 2](../tutorials/02_add_an_analysis_repository.md) demonstrates this handoff with one dated TOPEFT source observation; obtain exact current commands from the native manual rather than this file map. Return actual output/provenance and receipts where applicable through the [report contract](report_contract.md) for [human review and acceptance](../explanation/evidence_reproducibility_and_acceptance.md). A located source file or planned command is not an executed result, and the responsible scientific lead decides scientific acceptance.
