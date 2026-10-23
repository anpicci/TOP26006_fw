# Adapt the research workflow to another AI provider

**How-to.** Use this sequence when a researcher wants to carry a bounded project workflow to a selected provider, version, and execution surface. The [research responsibilities](../explanation/roles_and_authority.md) can be assigned without assuming that two products load instructions or restrict actions alike. Start with the [compatibility status](../reference/provider_compatibility.md) and the [provider limits](../explanation/provider_independence_and_limits.md).

1. **Name the research purpose and responsibilities.** Record the question, scientific owner, prompt author or coordinator, source-comparison researcher, executor, independent reviewer, and person who can accept the result. A single person may hold several responsibilities, but an executor's self-review is not independent review.
2. **List the mechanisms the current task actually uses.** Read live project governance and the prompt. Identify instruction files, validator, permission and sandbox controls, network and tool paths, continuity records, returned evidence, and review route. The [OpenAI reference procedure](providers/openai_reference_procedure.md) is a worked provider procedure, not a universal template.
3. **Choose an exact target.** Record provider, product surface, installed version, local or hosted environment, operating system, settings sources, and working directory. Consult the provider's current official documentation for that combination. Record access dates and URLs.
4. **Trace instruction discovery.** Determine which root, ancestor, nested, private, imported, and path-scoped instructions load, in what order, and when. Confirm the *observed* instruction chain in the target session. Similar file names do not prove equivalent loading.
5. **Map action controls.** Determine permission modes, allow/ask/deny rules, settings precedence, sandbox scope, escalation behavior, and any hooks. Separate behavioral guidance from technical enforcement and from the owner's authorization.
6. **Map each access path.** Check shell commands, built-in file tools, hosted search or web fetch, connectors, MCP servers, and delegated agents separately. Record filesystem and network coverage for each path. A shell network restriction says nothing by itself about hosted search or a connector.
7. **Map continuity and evidence.** Identify how a session resumes or loses context; how the operator records source versions, commands, outputs, artifacts, and limits; and where a separate reviewer can inspect them. A product's action approval or code review does not accept a scientific claim.
8. **Classify every required mechanism.** Use the worksheet below. For any missing control, narrow the task to what the provider can actually enforce. For example, use read-only analysis or a smaller file scope until an independently enforced boundary is available. Do not broaden permissions to simulate equivalence.
9. **Qualify locally before deployment claims.** In the intended installation, verify the version, instruction chain, effective settings, allowed/denied actions, all relevant file and network paths, evidence capture, and stop behavior with bounded, harmless probes. Record failures and the exact environment. Only then claim support for that qualified surface and scope. The [Anthropic adaptation](providers/anthropic_adaptation.md) is documentary guidance; it has no TOP26006_fw local Claude Code qualification.

## Adaptation worksheet

Copy the table into the task's evidence record. For each row choose **documented close equivalent**, **documented partial equivalent**, **concept only**, **not verified**, or **not applicable**. A documented mapping is still **not locally tested** until the intended installation is checked.

| Research need or mechanism | Current project use | Target provider, version, surface | Official URL and date | Classification | Local observation and limit |
| --- | --- | --- | --- | --- | --- |
| Human authority and scientific acceptance | Owner decision after review | | | | |
| Instruction discovery and nested guidance | Applicable `AGENTS.md` plus project governance | | | | |
| Prompt validation | Project validator around the provider | | | | |
| Permission and sandbox enforcement | Prompt grant plus effective runtime controls | | | | |
| File, network, web and connector paths | Separate grants and observations | | | | |
| Context/session continuity | Evidence and handoff record | | | | |
| Returned evidence and independent review | Report, patch, source locators, reviewer | | | | |

If a row is **concept only** or **not verified** and matters to the proposed effect, stop at that narrower boundary. Treat an official feature description as documentation evidence, not as a local test result.
