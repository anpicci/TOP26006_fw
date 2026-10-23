# Agentic work in TOP26006_fw

> **TOP-26-006 reference-deployment / legacy technical notes.** These pages preserve advanced deployment detail for later migration. First-time readers should use the [research-first manual](../index.md).

Use these notes for advanced TOP-26-006 reference-deployment details after the [research-first manual](../index.md). They explain how to find the right owner and frame a bounded task. They are explanatory: [root `AGENTS.md`](../../AGENTS.md) governs execution, [root `CPC.md`](../../CPC.md) governs prompt construction, and [root `CONTRIBUTING.md`](../../CONTRIBUTING.md) governs reviewer-facing text. Read the live files for exact requirements.

| Read | When you need |
| --- | --- |
| [Architecture and authority](architecture.md) | Project identity, three documentation planes, repository selection, control plane and lanes. |
| [Working with agents](working_with_agents.md) | A decision-focused dispatch, Git lifecycle, evidence, skills, and handoffs. |
| [Scientific documentation](scientific_documentation.md) | ANDOCS consistency audit and human scientific authority. |

## Ten steps from a workspace to a decision

1. Obtain or open the **TOP26006_fw coordination repository** through your project-approved access route. Its existing local checkout is named `correction-lib`; that directory name does not change the repository's identity. This guide asserts no private or public clone URL.
2. Read this index and the [architecture](architecture.md) page. A fresh coordination clone contains its tracked governance and guide files; it does **not** thereby install independent native Git histories, datasets, or an ANDOCS workspace.
3. Pick a `repository_id` from the live [typed registry](../../governance/repositories.md) by the work's owner and role. Resolve its concrete path from the local YAML profile, then check whether that path exists **and** is the intended Git repository. If absent, obtain and set it up through that native owner's official instructions or project contact; do not guess a URL, submodule layout, or installer.
4. Read [root `AGENTS.md`](../../AGENTS.md), the selected registry module when named, every path-applicable nested `AGENTS.md`, and applicable native policy. For a new Codex prompt, read [root `CPC.md`](../../CPC.md); for reviewer text, read [root `CONTRIBUTING.md`](../../CONTRIBUTING.md).
5. State **one decision question** and its exact repository, paths, expected evidence, and stop boundary. Decide whether inspection alone answers it or a tracked mutation is needed.
6. Select a prompt mode and validation ceiling from the live contracts. Declare `allowed_to_modify` and `read_only`; separately grant each needed capability and effect. A tool, credential, checkout, or skill does not grant permission.
7. Before mutation, freshly check the selected repository's branch, HEAD, tree, applicable active feature branches, task-path/index dirt, and output collisions. Stop on an ambiguous branch or foreign change instead of treating the registry or an old report as current Git state.
8. Dispatch the bounded prompt. Ask the agent to collect direct evidence, serialize it, reopen it, and evaluate declared gates before a verdict or later stage. Keep independent repositories' Git operations separate.
9. Review the report, patch, source locators, validation limits, retained foreign state, and unresolved risks. Reuse accepted evidence outside its invalidation boundary; freshly read volatile state when needed.
10. Hand off or advance only through the next separately authorized boundary: further coding, local integration, manual production, publication, and remote merge have distinct contracts. A checkpoint carries context and evidence, not permission.

For example, a useful *conceptual* request is: “In the selected repository, does the documented option match the live CLI behavior? Inspect that option and its maintained documentation, record exact source and command evidence, and report discrepancies. Keep both repositories read-only.” The actual dispatch still needs the live prompt fields, repository identity, and permissions. This example authorizes no command or edit.

## When a task stops

| Observation | Next action |
| --- | --- |
| A gate is `blocked` or indeterminate | Read its exact evidence and failed condition; preserve completed effects. Ask for a new decision if the next action was not already authorized. |
| A command failed technically | Record its exit/output and whether effects may have occurred; read state before a retry. Failure alone does not justify changing target or scope. |
| Feature applicability or task-path ownership is ambiguous | Inspect live refs and dirty state; reconcile or obtain an explicit branch/ownership decision before mutation. |
| The sandbox can run a command, but the prompt lacks permission | Stop at the authorization boundary. Technical capability is not a grant. |
| A snapshot or this guide disagrees with live policy | Follow applicable live governance and report drift; correct this guide in its own authorized round. |
| A scientific statement lacks authoritative evidence | Report the claim and missing binding to its human scientific owner; do not turn plausible prose into a result. |

## Short glossary

| Term | Meaning here |
| --- | --- |
| **Control plane** | The project-level owner of task decisions, authorizations, lane routing, and acceptance; it supplies context, not scientific truth. |
| **Lane / workstream** | A current assignment of work and evidence production. Its roster can change without changing repository ownership. |
| **Authority** | Applicable live governance for actions, or the native scientific/technical owner for content, according to the question. |
| **Source evidence** | An observed file, command result, artifact, or result with provenance; it supports a bounded claim but does not authorize action. |
| **Snapshot / checkpoint** | Recorded evidence and context at a past time. Reuse accepted stable findings; recheck current Git, remote, storage, or process state when material. |
| **Feature / reference / integration branch** | Development surface / baseline / local accumulation target. Exact names and roles depend on selected repository policy. |
| **Blocked / failed** | `Blocked` names an unmet decision gate or permission; technical failure is an observed operation outcome whose effects need assessment. |
| **New decision boundary** | A choice not preauthorized and mechanically determined by current prompt gates; stop before taking it. |
