# Adapt the workflow to Claude Code

> **Documentary adaptation — TOP26006_fw Claude Code runtime: NOT LOCALLY TESTED / NOT QUALIFIED.**

Begin with the [research method and responsibilities](../../explanation/roles_and_authority.md), then the [adaptation worksheet](../adapt_to_another_ai_provider.md). The following maps documented mechanisms to needs a task might have. It does not reproduce the OpenAI product decomposition or establish equivalent project roles.

## Dated official mechanism mapping

Official sources checked **2026-11-02 (America/New_York; 2026-11-03 UTC)**. Recheck the selected product surface/version and the relevant source at use time; this table supplies no installation instructions or local qualification.

| Documented mechanism and official source | Closest project need it could support | What to check before relying on it |
|---|---|---|
| Agentic code reading, editing and commands across terminal, IDE, desktop and browser surfaces — [Overview](https://code.claude.com/docs/en/overview) | Bounded repository inspection or technical work | Actual surface, checkout, allowed actions and returned evidence; no full Chat/Work/Codex role equivalence follows |
| Scoped settings and precedence — [Settings files and precedence](https://code.claude.com/docs/en/settings) | Identify which configuration controls a task | Effective settings and instruction discovery for the actual session, including relevant local/managed sources; a similar instruction filename is insufficient |
| Tool allow/ask/deny controls and permission modes — [Configure permissions](https://code.claude.com/docs/en/permissions) | Control tool actions within an already-authorized task | Actual rules, mode and coverage; do not translate them into CPC permission grants or Codex labels |
| Worker contexts with tool/permission controls and foreground/background patterns — [Create custom subagents](https://code.claude.com/docs/en/sub-agents) | An explicitly authorized bounded assignment or review aid | Inputs, tools, effects, result capture and independence from authorship; separate context or worker agreement does not establish independent review or acceptance |
| Lifecycle/tool-event automation, with event-dependent action decisions — [Hooks reference](https://code.claude.com/docs/en/hooks) | A mechanical check or event response | Actual event, handler, side effects and failure behavior; hooks do not judge scientific adequacy or supply a research lead's authority |
| External tool/data connections through MCP — [Connect Claude Code to tools via MCP](https://code.claude.com/docs/en/mcp) | Reach a specifically authorized source or service | Configuration scope, trust, tool/service identity and permitted effects; connectivity does not authorize access or qualify a result |

## Keep project authority and evidence separate

A documented Claude Code mechanism is not TOP26006 authorization, independent review, scientific acceptance or proof of local compatibility. Permission prompts can control product actions; project grants still come from the research lead under live [AGENTS.md](../../../AGENTS.md), [CPC.md](../../../CPC.md) and applicable [repository/native policy](../../../governance/repositories.md). Neither a hook's decision nor subagent agreement transfers the responsible human's scientific judgment to the product.

Before any separately authorized deployment, record the intended version/surface, effective instruction/settings chain, actual file and network paths, evidence capture and restart behavior. Any local probes need exact authorization and their own receipts. Narrow an unsupported dependent action rather than broadening permissions to imitate another provider. No setting, hook, subagent or MCP server is installed or configured by this guide.

Preserve exact source/input revisions and actual actions/results outside assumptions about product memory. After interruption, obtain bounded process/output/service readback before deciding whether a retry is safe. A conversation resume alone cannot prove execution completed. [Review returned evidence](../../tutorials/05_review_and_accept_returned_evidence.md) and keep human acceptance separate, as in the [accepted method](../../explanation/research_workflow.md).

## Qualification boundary

This page establishes a dated documentary mapping only. No Claude Code runtime, local compatibility, security posture or scientific behavior was tested. See the [compatibility reference](../../reference/provider_compatibility.md) for evidence status, the [provider-limits explanation](../../explanation/provider_independence_and_limits.md) for the enduring boundary, or return to the optional routes in the [manual](../../index.md#advanced-and-maintainer-routes).
