# Use the OpenAI/Codex reference procedure

Use this concrete project reference after framing a [bounded research task](../ask_an_assistant_to_prepare_a_task.md). The common [research method](../../explanation/research_workflow.md) and [roles](../../explanation/roles_and_authority.md) come first. Product descriptions, the project operating model and local execution facts answer different questions.

## Product mechanisms observed from official documentation

Official sources checked **2026-11-02 (America/New_York; 2026-11-03 UTC)**: [ChatGPT Work and Codex](https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex) describes Chat for conversational help, Work for longer research and deliverables, and Codex for software/repository work. Availability and controls vary with surface, account and workspace; check the current documentation and actual access before relying on a feature.

[Projects in ChatGPT](https://help.openai.com/en/articles/10169521-projects-in-chatgpt) describes grouping related chats, files and instructions. Work can use project context where supported. Treat that context as supplied material: check its revision and completeness against current sources before a decision. Product memory is not canonical project state.

These are dated mechanism observations. Recheck relevant behavior at use time; no plan entitlements, model roster, quota, price or menu sequence is part of this procedure.

## TOP26006's project-local role mapping

The accepted project model assigns these responsibilities; OpenAI documentation does not grant scientific or project authority:

| Project role | Responsibility in this project |
|---|---|
| Chat | Continuity, governance-aware framing and interpretation |
| Work | Bounded research, source comparison, audit and finished deliverables |
| Codex | Repository/code work, tests and bounded technical execution when authorized |

The human defines scientific purpose, assumptions, permissions and acceptance. Chat can help apply governance but cannot grant effects or decide the science. A researcher can use only the roles the question needs; product handoffs are not automatic and do not transfer authority or source access. Git records source history; reviewer findings and human acceptance remain separate from execution.

## Follow the reference on the actual installation

1. **Prepare the task.** Identify the question, owner, repository/path scope, permitted effects, validation ceiling, expected evidence and stop boundary. The prompt author follows current [AGENTS.md](../../../AGENTS.md), [CPC.md](../../../CPC.md), applicable modules/native policy and [mechanical prompt validation](../validate_a_prompt_before_execution.md). Validator PASS is not authorization or scientific correctness.
2. **Check local facts.** Use the maintained [local-profile procedure](../configure_your_local_profile.md) to resolve paths, wrapper and interpreter. Freshly observe branch, HEAD and relevant changes. A profile describes an installation; it grants no action.
3. **Inspect effective controls.** Read applicable instructions and observe the chosen session's sandbox, approvals, file/network reach and tool paths. Consult current official documentation for the selected surface. Record unavailable or unobserved facts honestly; instructions and requested settings do not prove enforcement.
4. **Execute only the authorized task.** Product access or an approval prompt cannot enlarge its scope. A shell, hosted web tool and connected service require separate access/effect checks; permission for a documentation read does not authorize remote Git or publication.
5. **Return reviewable evidence.** Record exact sources, actual commands/results, relevant local state, patch/report and limits. Distinguish requested from observable runtime identity when material. Reopen durable evidence before claiming completion; an interrupted action needs readback before any retry.
6. **Review and decide.** Use the [review lesson](../../tutorials/05_review_and_accept_returned_evidence.md). A separate context or product code review alone does not establish independent project review. The responsible human accepts a bounded claim, asks for repair or leaves it unresolved. [Continuation](../../tutorials/06_continue_from_existing_evidence.md) reuses still-valid evidence.

## Evidence status and next route

OpenAI/Codex is the project reference procedure. This guide supplies no per-feature runtime qualification for Chat, Work, Codex, local, cloud or connected-app surfaces. Existing project use is not evidence for an unobserved feature or another installation. Check the [compatibility reference](../../reference/provider_compatibility.md) for the distinction; use the [adaptation guide](../adapt_to_another_ai_provider.md) for another provider and the [manual](../../index.md) to return to research tasks.
