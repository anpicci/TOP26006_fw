# Adapt the research workflow to another AI provider

Start with the research question and the [accepted research method](../explanation/research_workflow.md): a bounded task, authority and permissions, evidence, review, and human interpretation or acceptance. The [responsibilities of people and tools](../explanation/roles_and_authority.md) remain in place when a provider changes. A provider need not divide its products into the same roles or use the same names.

Use this guide for a selected task and surface. The [OpenAI reference procedure](providers/openai_reference_procedure.md) is the project's concrete example; the [Claude Code adaptation](providers/anthropic_adaptation.md) is documentary and not locally qualified. Read the [compatibility status](../reference/provider_compatibility.md) for the evidence limits, and [provider independence and limits](../explanation/provider_independence_and_limits.md) for the reasoning.

## Map the task before choosing mechanisms

1. **Bound the work.** Name the research purpose, responsible human, exact sources, permitted effects and useful finish. Use the [task-preparation guide](ask_an_assistant_to_prepare_a_task.md). Keep scientific choices with the responsible researchers.
2. **List only the needs this task has.** Use the worksheet below. Discussion may be enough; a repository task or external data access introduces different mechanisms. Delegation is optional and separately authorized, not a required adaptation step.
3. **Acquire the provider's current official description.** Identify product, surface, version where observable, local or hosted execution, and the specific mechanism. Record the source title, URL, access date and conditions. Distinguish provider documentation, project reference use and direct local observations.
4. **Check the actual controls.** Under the task's authorization, inspect instruction discovery, effective settings and their precedence, permission/approval behavior, filesystem reach and every network/tool path the task needs. Record requested settings separately from observed controls. A shell restriction alone does not establish another tool's coverage. Do not translate permission labels by name.
5. **Preserve the authority and evidence boundaries.** Follow live [AGENTS.md](../../AGENTS.md), [CPC.md](../../CPC.md), the selected [repository/native authority](../../governance/repositories.md), and the owner's grant. An action approval, instruction file or connected service cannot enlarge that grant. Context retained by a product is not authoritative current project state.
6. **Record the mapping and its limits.** Preserve source/input revisions, commands and outputs actually obtained, a patch when changed, and unresolved observations. Identify evidence capture, restart/readback and the reviewer before relying on the result. Resume from durable evidence and fresh material state, not remembered completion.
7. **Stop only the unsupported dependent effect.** If a needed mechanism is unverified, report the missing observation and propose a narrower task. A narrower task still needs authorization. Any local qualification probes require their own bounded grant; reading this guide does not authorize installation, configuration, execution or deployment. Claim support only for the exact surface and checks actually exercised.

## Adaptation worksheet

Record each applicable row in the task's existing evidence record. Label its evidence as **documented mapping**, **locally observed within stated scope**, **not verified**, or **not applicable**. These describe support for a need, not a universal compatibility score or equivalent product role.

| Task need | What to map and preserve |
|---|---|
| Conversational or research assistance | Which surface supports discussion, source comparison or a finished deliverable; who checks the claims |
| Repository/code execution | Exact checkout, instructions, working paths, execution controls and allowed validation |
| External tools and data | Each service/tool path, permitted reads or mutations, connectivity, data scope and actual reach |
| Permissions and approval mechanics | Effective settings, approval/enforcement behavior and limits, separately from project grants |
| Persistent or project context | What context is available, its source revision and how current material state is refreshed |
| Delegated or parallel workers | Authorized responsibilities, write boundaries and review independence; separate contexts alone establish none of these |
| Evidence capture and restartability | Source identities, actual actions/results, artifacts, preserved unknown outcomes and safe readback before retry |
| Human review and acceptance | Responsible owner, reviewer evidence, accepted claim and residual limits; provider agreement cannot accept it |

For each row add the official locator/date, exact target surface/version, local observation or missing check, and claim ceiling. Recheck any decision-material mechanism at use time, especially after a product, configuration or surface change. A mechanism rename reopens that mapping, not the research method or unrelated accepted work.
