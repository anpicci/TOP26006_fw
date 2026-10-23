# TOP-26-006 reference deployment

> **Worked reference deployment / case study — not a universal configuration.**
>
> **Dated snapshot:** 2026-10-23. Live branch, paths, settings, and assignments must be checked again before use. This page describes TOP-26-006 choices; it grants no repository action or scientific acceptance.

The [generic manual](../index.md) starts with a research question and bounded evidence. This case study shows where one project places the corresponding authority and installation facts. It draws on the live [registry](../../governance/repositories.md), [root governance](../../AGENTS.md), the ignored local profile observed at this snapshot, the existing legacy pages, and a fresh coordination-repository preflight. No child repository was inspected for this page.

| Generic concept | TOP-26-006 choice | Evidence state |
| --- | --- | --- |
| Project identity | `TOP26006_fw`, the TOP-26-006 coordination project | **Stable project convention** in root governance and registry |
| Coordination repository | `TOP26006_fw` is a `COORDINATION_META_REPOSITORY`; independent repositories keep their own Git histories | **Stable project convention** in registry |
| Installation path | This observed checkout is `/users/apiccine/work/correction-lib`; directory name is not project identity | **Current live observation**, 2026-10-23; other installations differ |
| Local profile | Ignored `.top26006/local_profile.yml` records workspace, evidence root, wrapper/interpreter paths, repository paths, and `provider_procedure: openai_codex` | **Current local observation**; private installation fact, not permission or compatibility proof |
| Root governance | `AGENTS.md` controls execution; `CPC.md` prompt construction; `CONTRIBUTING.md` reviewer prose | **Stable project convention**; use live files for exact rules |
| Typed registry and modules | `governance/repositories.md` assigns repository identity, class, role and module; TOP26006_fw inherits root policy, with no dedicated TOP26006_fw module | **Stable project convention** at this snapshot |
| Research workstream | A task or historical “lane” carries assigned evidence work; roster can change without moving repository ownership | **Historical terminology** in legacy pages; current assignment requires an owner decision |
| Human owner | Sets the scientific question, authorizes effects within authority, and decides acceptance after review | **Stable responsibility**; current individual assignment **not asserted** here |
| Coordinating Chat or prompt author | Translates the owner's mandate into a bounded prompt and records gates and accepted prior evidence | **Stable responsibility**; product surface or current assignee **not asserted** |
| Work research role | May compare provider/source evidence and return a dated finding for prompt construction | **Programme role example**, not an automatic project authority or current roster |
| Codex execution role | The current local provider procedure is OpenAI/Codex; the executor checks live state, performs authorized work and returns report/patch | **Current project convention** in root governance and local profile; exact runtime identity requires session observation |
| Review and acceptance | A separate reviewer challenges evidence; the human owner accepts a bounded result. Executor self-review is not independent review | **Stable project convention** in [roles and authority](../explanation/roles_and_authority.md) |
| Feature-line example | `docs/research-first-manual` at `4585756510f2b7d516c94bd49e3e08ee1b17c554` before this documentation change, compared with local `master` | **Observed at snapshot preflight; historical after this change**, not a future HEAD or universal branch role |
| Diagnostics | Local profile names `reports/diagnostics` as its evidence root | **Current local observation**; reports are evidence, not committed governance |
| Publication and license | The repository remains private. Apache-2.0 is an intended future repository-wide license, with no present effective grant or public-release claim | **Current owner/project boundary** in [README](../../README.md) |

The historical legacy guide called the project coordinator a “Control Plane” and task assignments “lanes.” Those terms explain earlier handoffs; they do not replace current [roles and authority](../explanation/roles_and_authority.md). Historical examples in another repository used `run3_test_mmerged`, `run3_test_mmerged_anpicci`, and `te/*` branch names. They are **not** TOP26006_fw branch rules or live child-repository observations. Check the selected repository's live native policy and Git state before a task.

Scientific writing in the separate `ANDOCS` document coordination repository, including its paper and Analysis Note histories, remains native-owned. For a document consistency audit, identify the exact claim, matching implementation or accepted result, provenance, and discrepancy or evidence gap; route substantive corrections to the document and scientific owner. The [scientific responsibility](../explanation/scientific_responsibility.md), [evidence and acceptance](../explanation/evidence_reproducibility_and_acceptance.md), and live [ANDOCS module](../../governance/modules/andocs.md) govern that boundary. This case study does not assert the current state of those child histories.

For provider choices, use the [OpenAI reference procedure](../how_to/providers/openai_reference_procedure.md), [documentary Claude adaptation](../how_to/providers/anthropic_adaptation.md), and [compatibility matrix](../reference/provider_compatibility.md). Claude Code has **not** been locally qualified for this deployment.
