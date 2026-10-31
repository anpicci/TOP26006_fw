# AI-assisted research manual

Use this manual to frame a research question, give an assistant a bounded task, and check the evidence it returns. Start with the research purpose; add execution and project setup when you need them.

## Start here

1. [Get oriented](getting_started.md): understand what you can read now and what needs local tooling.
2. [Read the AI-assisted research foundations](foundations/ai_assisted_research.md): learn how to frame a question, use AI assistance, and check the evidence.
3. [Explore a small synthetic example](../examples/repeated_measurements/README.md): see a question, stated assumptions, and checkable inputs without real analysis data.
4. [Try a first read-only task](tutorials/03_complete_a_first_read_only_task.md): use the existing exercise once your local tooling is prepared. It does not need a TOPEFT checkout.

## Find the route you need

| I want to… | Start with… |
|---|---|
| Understand the research approach | [The research workflow](explanation/research_workflow.md) |
| Understand how people and AI tools contribute | [Choosing an AI tool for a research task](how_to/choose_an_ai_tool_for_a_research_task.md) |
| Turn a question into a task request | [Asking an assistant to prepare a task](how_to/ask_an_assistant_to_prepare_a_task.md) |
| Prepare local execution | [Prepare a research project](tutorials/01_prepare_a_research_project.md) |
| Work with an existing analysis repository | [Add an analysis repository](tutorials/02_add_an_analysis_repository.md), an optional TOPEFT-specific lesson |
| Look up a term or locate a file | [Glossary](reference/glossary.md) · [File map](reference/file_map.md) |

## Continue after the first task

The later tutorials cover [a bounded change](tutorials/04_make_a_bounded_analysis_change.md), [reviewing returned evidence](tutorials/05_review_and_accept_returned_evidence.md), [continuing from existing evidence](tutorials/06_continue_from_existing_evidence.md), [a two-repository change](tutorials/07_coordinate_a_multi_repository_change.md), [recovering from a stop](tutorials/08_recover_from_a_stopped_task.md), and [a collaborator handoff](tutorials/09_transfer_work_to_a_collaborator.md). Use these when the corresponding need arises.

## Advanced and maintainer routes

These routes are optional for the introduction:

- **Coordinate larger work:** the [advanced workstream route](advanced/index.md) explores dependencies and responsibility transfer using a synthetic case.
- **Choose or adapt a provider:** [provider compatibility](reference/provider_compatibility.md) distinguishes documented mechanisms from tested support; the [adaptation guide](how_to/adapt_to_another_ai_provider.md) explains what to check.
- **Maintain a project installation:** [profile configuration](how_to/configure_your_local_profile.md) and [repository registration](how_to/register_repositories.md) cover installation and repository mapping.
- **Maintain operating rules:** [guide to operating rules](reference/governance_precedence.md) points to the binding contracts; [CONTRIBUTING.md](../CONTRIBUTING.md) covers contribution and review prose.

For public visibility and the current licensing status, see the [repository README](../README.md#repository-visibility-and-licensing).
