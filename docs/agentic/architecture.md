# Architecture and authority

## What the coordination repository owns

`TOP26006_fw` is the TOP-26-006 project coordination and agentic-governance repository. Its existing checkout path is `/users/apiccine/work/correction-lib`; `correction-lib` is a local directory name, not a different project identity. The root coordinates implementation, document, dependency, and evidence repositories recorded in the [typed registry](../../governance/repositories.md). It is **not a monorepo**: a nested path can be an independent Git repository with its own index, history, branches, remotes, policy, and semantic owner. Root Git operations must not gather nested histories into a root commit. The coordination root owns its governance and this guide, not native implementation files or scientific conclusions. See [root `AGENTS.md`](../../AGENTS.md) for the exact repository-boundary contract.

## Three planes of documentation

| Plane | Owner and purpose | If content is wrong |
| --- | --- | --- |
| **A. Normative project governance** | Root [`AGENTS.md`](../../AGENTS.md), [`CPC.md`](../../CPC.md), [`CONTRIBUTING.md`](../../CONTRIBUTING.md), the [registry](../../governance/repositories.md) and selected modules, plus applicable repository/upstream-native policy. These control actions, prompts, review text, ownership, and native constraints. | Change the appropriate authority in a separately authorized owner round. |
| **B. TOP26006_fw agentic explanation** | This `docs/agentic/` guide teaches readers how to use plane A. It grants no permission or scientific authority. | Correct this page in TOP26006_fw, after checking live plane A. |
| **C. Native technical and scientific documentation** | Each independent repository owns its implementation guides, developer and user docs, paper or AN text, and scientific interpretation. | Ask the native owner to correct its document under that repository's policy. |

Read **live applicable governance before this explanation** when exact fields, branch roles, or permissions matter. A prior evidence package or old copy of a policy is a snapshot, not current authority. If this guide conflicts with live governance, use the live rule and report this guide as stale. Do not make shadow policy or native-document copies here as substitute authorities. An agentic explanation gap belongs here; a native technical or scientific error belongs to its native owner. Neither is solved by silently editing the other plane. [Working with agents](working_with_agents.md) describes the operational gate that applies these boundaries.

## Selecting a repository

The [registry](../../governance/repositories.md) gives a stable `repository_id`, class, location contract, role, semantic authority, and module binding. Its classes include the coordination root, project implementation and document repositories, external dependencies, pinned evidence, and conditional or out-of-scope surfaces. For example, `topeft` owns analysis implementation, `topcoffea` supplies shared libraries, `EFTFit` owns its fit package, `ANDOCS` coordinates separate paper and AN histories, and `CombinedLimit` is an external dependency. These are ownership roles, not a claim that every path exists in a fresh clone.

To select a target, find its `repository_id` by the question's semantic owner; read its named module, if any (for example, the [`topeft` module](../../governance/modules/topeft.md) or [`ANDOCS` module](../../governance/modules/andocs.md)); verify the path is available and is the intended Git root; then freshly inspect its branch, HEAD, tree, index, and worktree when material. Also read applicable native or upstream policy. The registry records durable relations, **not** current Git state, a remote advertisement, or a grant to write. Membership and technical access never supply task authorization; an exact prompt must grant repository, paths, and effects. The [onboarding path](README.md) explains what to do when the selected native repository is absent.

## Control plane, lanes, and handoffs

The TOP-26-006 control plane decides the work question, task authorization, lane routing, and acceptance boundary. A lane or workstream carries an assigned piece of implementation, document, evidence, or review work. A lane can report a checkpoint with source identity, observations, and unresolved decisions; the next lane can reuse accepted evidence and request new work under its own authority. A checkpoint informs the next task but does not grant a write, publication, production run, or scientific judgment.

Repository ownership is more durable than the current lane roster. A change in who is assigned a task should be handled by the control plane and handoff, not hardcoded as an immutable rule in a repository module. A module records repository-specific project constraints such as branch roles or document review boundaries; it cannot weaken root governance, override native policy, or authorize a new action. This keeps cross-lane movement possible without moving the scientific or technical owner.
