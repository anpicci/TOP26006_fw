# Provider compatibility status

Start with the [common research method](../explanation/research_workflow.md), then map the mechanisms a task needs. This is an evidence-status reference, not a provider ranking or a universal PASS/FAIL score. OpenAI/Codex is the project reference route; Claude Code is a documentary adaptation, **NOT LOCALLY TESTED / NOT QUALIFIED** for TOP26006_fw.

## Read the evidence columns separately

**Documented mechanism** means an official source describes it. **Project reference use/mapping** describes this manual's assignment of responsibilities. **Local evidence** requires direct observations tied to an exact installation, surface and task. A documented feature or familiar product name cannot substitute for that evidence. The ignored profile's `provider_procedure` selects a local procedure, not a compatibility certificate.

Official mechanism sources linked below were checked **2026-11-02 (America/New_York; 2026-11-03 UTC)**. Recheck decision-material behavior at use time after a provider, version, configuration or surface change. Freshness of the source does not prove runtime compatibility.

| Research/task need | Provider-documented mechanism | TOP26006 reference use or mapping | Local evidence status | Check at use time | Claim ceiling |
|---|---|---|---|---|---|
| Discussion, research, technical work | OpenAI [Chat / Work / Codex](https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex) | [Project-local role mapping](../how_to/providers/openai_reference_procedure.md#top26006s-project-local-role-mapping) | Project reference; no per-feature qualification asserted here | Actual surface/access and required controls | No blanket qualification of all OpenAI features |
| Context organization | OpenAI [Projects](https://help.openai.com/en/articles/10169521-projects-in-chatgpt) | Carry identified sources/context into a task | Documentary feature description; no memory/continuity test | Available context, revisions and freshness | Product memory is not canonical project state |
| Repository work | Claude Code [coding surface](https://code.claude.com/docs/en/overview) | Possible bounded executor mechanism | Documentary; NOT LOCALLY TESTED / NOT QUALIFIED | Surface/version, checkout and effects | No equivalent Chat/Work/Codex decomposition |
| Configuration | Claude [settings and precedence](https://code.claude.com/docs/en/settings) | Locate effective controls | Documentary; NOT LOCALLY TESTED / NOT QUALIFIED | Actual instruction/settings sources and scope | Files or names do not prove loading/enforcement |
| Tool action controls | Claude [permissions](https://code.claude.com/docs/en/permissions) | Controls within a task authorized by the research lead | Documentary; NOT LOCALLY TESTED / NOT QUALIFIED | Effective rules/mode and tool coverage | No CPC grant or label equivalence |
| Delegated work | Claude [subagents](https://code.claude.com/docs/en/sub-agents) | Optional authorized assignment/review aid | Documentary; NOT LOCALLY TESTED / NOT QUALIFIED | Inputs, tool/effect boundaries and result evidence | Context separation is not independent review/acceptance |
| Event automation | Claude [hooks](https://code.claude.com/docs/en/hooks) | Possible mechanical action check | Documentary; NOT LOCALLY TESTED / NOT QUALIFIED | Event, handler, side effects and failures | No scientific gate or authority from a research lead |
| External tools/data | Claude [MCP](https://code.claude.com/docs/en/mcp) | Possible authorized service access path | Documentary; NOT LOCALLY TESTED / NOT QUALIFIED | Tool/service identity, scope, trust and grants | Connectivity is not service authorization |
| Exact local execution | Provider availability alone is insufficient | [OpenAI reference procedure](../how_to/providers/openai_reference_procedure.md); [Claude mapping](../how_to/providers/anthropic_adaptation.md) | No runtime qualification established by this reference | Installation, actual controls, evidence and restart behavior under separate authorization | Support is limited to actual observed checks; no cross-provider equivalence |
| Scientific acceptance | No provider mechanism supplies this responsibility | [Human review and acceptance](../explanation/evidence_reproducibility_and_acceptance.md) | Human decision evidence is required separately | Responsible scientific lead, accepted claim, assumptions and limits | Technical compatibility is not scientific compatibility |

Use the [adaptation worksheet](../how_to/adapt_to_another_ai_provider.md) to record task-specific evidence and unresolved needs. Project permissions and scientific acceptance do not transfer with a provider change. Return to the [manual](../index.md#advanced-and-maintainer-routes) when these optional details are no longer needed.
