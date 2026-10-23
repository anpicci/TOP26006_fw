# How to check prerequisites

For the OpenAI/Codex reference procedure, obtain an authorized private TOP26006_fw checkout and an already-prepared Python interpreter with PyYAML. Identify its absolute path and test `import yaml`; do not install packages as part of this route. Confirm you can read [AGENTS.md](../../AGENTS.md), [CPC.md](../../CPC.md), and the [registry](../../governance/repositories.md). A shell that can run `git` suffices for local readback.

The local command wrapper must accept a command and arguments, prepare any site-specific existing environment if needed, execute the command, and propagate its exit status. [Tutorial 1](../tutorials/01_prepare_a_research_project.md) provides a forwarding-only example for an already-prepared interpreter. If your interpreter cannot import PyYAML, obtain a project-approved prepared environment; do not silently change the software environment. For other providers, use [compatibility status](../reference/provider_compatibility.md).
