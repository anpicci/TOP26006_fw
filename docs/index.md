# AI-assisted research manual

Use this manual to frame a research question, give an assistant a bounded task, and check the evidence it returns. Start with the research purpose; add execution and project setup when you need them.

## Start here

1. [Get oriented](getting_started.md): understand what you can read now and what needs local tooling.
2. [Read the AI-assisted research foundations](foundations/ai_assisted_research.md): learn how to frame a question, use AI assistance, and check the evidence.
3. [Explore a small synthetic example](../examples/repeated_measurements/README.md): see a question, stated assumptions, and checkable inputs without real analysis data.
4. [Try a first read-only task](tutorials/03_complete_a_first_read_only_task.md): use the existing exercise once your local tooling is prepared. It does not need a TOPEFT checkout.

For the shortest route to one useful reviewed task, follow [Explore one bounded task](getting_started.md#explore-one-bounded-task), then [review the returned evidence](tutorials/05_review_and_accept_returned_evidence.md). Local execution needs the setup linked from that route; reading the example does not.

## Follow the tutorials

The **[tutorial learning path](tutorials/index.md)** guides you through small research exercises, from preparing a workspace and checking a synthetic result to reviewing evidence, continuing work, and handing it over. It gives the recommended ordinary route, each lesson's starting point and outcome, and optional extensions for native analysis and broader coordination.

Use that walkthrough when you want to learn the method by doing; use the task routes below when you already know which kind of help you need.

## Find the route you need

| I want to… | Start with… |
|---|---|
| Understand the research approach | [The research workflow](explanation/research_workflow.md) |
| Understand how people and AI tools contribute | [Roles and authority](explanation/roles_and_authority.md), then [choosing an AI tool for a research task](how_to/choose_an_ai_tool_for_a_research_task.md) |
| Turn a question into a task request | [Asking an assistant to prepare a task](how_to/ask_an_assistant_to_prepare_a_task.md) |
| Prepare local execution | [Prepare a research project](tutorials/01_prepare_a_research_project.md) |
| Inspect or work with a scientific repository | [Add an analysis repository](tutorials/02_add_an_analysis_repository.md), an optional TOPEFT-specific lesson that leads to native documentation and source |
| Look up a term or locate a file | [Glossary](reference/glossary.md) · [File map](reference/file_map.md) |

## Continue after the first task

Choose the next lesson by the task you have now. Ordinary work can stay serial and within one repository.

| I want to… | Start with… |
|---|---|
| Make a bounded change | [A bounded analysis change](tutorials/04_make_a_bounded_analysis_change.md) |
| Review a result and decide what to accept | [Reviewing returned evidence](tutorials/05_review_and_accept_returned_evidence.md) |
| Continue without repeating valid work | [Continuing from existing evidence](tutorials/06_continue_from_existing_evidence.md) |
| Recover after a stop | [Recovering from a stopped task](tutorials/08_recover_from_a_stopped_task.md) |
| Transfer context and evidence to a collaborator | [A collaborator handoff](tutorials/09_transfer_work_to_a_collaborator.md) |
| Handle a dependency that crosses repositories | [A multi-repository change](tutorials/07_coordinate_a_multi_repository_change.md), only when the task needs that dependency |

## Advanced and maintainer routes

These routes are optional after the core learning path. For framework maintenance and governed prompt authoring, use the [maintainer gateway below](#maintain-or-author-top26006_fw-tasks).

- **Coordinate larger work:** the [advanced workstream route](advanced/index.md#decide-whether-to-enter-this-route) helps decide when separable questions justify extra coordination, then explores dependencies and responsibility transfer using a synthetic case. It is not a required next level.
- **Choose or adapt a provider:** [provider compatibility](reference/provider_compatibility.md) distinguishes documented mechanisms from tested support; the [adaptation guide](how_to/adapt_to_another_ai_provider.md) explains what to check.

## Maintain or author TOP26006_fw tasks

Use this gateway when you maintain the framework or translate an authorized task into a governed repository prompt. These technical guides are not prerequisites for the research lessons.

| I need to… | Maintained guide or reference |
|---|---|
| Configure a local installation | [Profile configuration](how_to/configure_your_local_profile.md) |
| Register or update a repository identity | [Repository registration](how_to/register_repositories.md) |
| Add or update repository-specific governance | [Governance modules](how_to/add_or_update_a_governance_module.md) |
| Write a governed prompt manually | [Manual prompt authoring](how_to/write_a_prompt_manually.md) |
| Prepare a prompt for a supported workflow pattern | [Governance workflow compiler](how_to/compile_governance_workflow.md) |
| Mechanically check a completed prompt | [Prompt validation](how_to/validate_a_prompt_before_execution.md) |
| Look up the prompt contract | [Prompt contract reference](reference/prompt_contract.md) |

Manual governed prompt authoring remains a first-class route for any task that can be expressed within the manual contract, whether the author is a person or an authorized assistant. The governance workflow compiler is an optional authoring aid for supported workflow patterns. It produces an inspectable prompt and compilation receipt; it does not create authority, dispatch, execute, review or accept the task. Use manual governed authoring when the required pattern is not supported. The compiler guide is not a prerequisite for the research tutorials.

The guides explain procedures; live [AGENTS.md](../AGENTS.md), [CPC.md](../CPC.md), the [repository registry](../governance/repositories.md) and its applicable modules/contracts remain the authority. Use [governance precedence](reference/governance_precedence.md) and the [file map's authority locators](reference/file_map.md#normative-governance-authority) to find those sources; [CONTRIBUTING.md](../CONTRIBUTING.md) governs contribution and review prose. A prompt-validator PASS establishes supported mechanical checks, not governance completeness, authorization or scientific correctness.

For public visibility and the current licensing status, see the [repository README](../README.md#repository-visibility-and-licensing).
