# Getting started

This guide helps a newcomer locate the right repository and its maintained
instructions before making a change. Start with the [root README](../README.md)
for the project overview.

## What you have

`TOP26006_fw` is the TOP-26-006 coordination and project-governance
meta-repository. It owns the project-level [repository registry](../governance/repositories.md)
and governance files. Analysis software, shared libraries, fit software, and
scientific documents have independent repository and semantic owners. The
coordination checkout is not a monorepo.

The managed Glados checkout is `/users/apiccine/work/correction-lib`. Its
directory name is a local path, not the `TOP26006_fw` repository identity.

## Fresh clone vs managed workspace

A fresh `TOP26006_fw` clone gives you its tracked coordination files. The
managed workspace may also have separately checked-out repositories beneath
it, including `topeft`, `topcoffea`, `EFTFit`, and `ANDOCS`. Those independent
Git histories and their data are not installed by cloning this repository.
Treat a workspace path as a location to verify, not proof that a repository is
available or that you may change it.

## First safe read-only checks

1. From the directory you received, run `git rev-parse --show-toplevel` to
   identify its Git root. Confirm that you are in the `TOP26006_fw` checkout,
   rather than an independent repository inside the managed workspace.
2. Run `git branch --show-current` and `git status --short` to inspect the
   current branch and working state without changing them.
3. Read the [README](../README.md) and this guide, then choose a native
   repository from the table below.
4. Before entering that repository, check that its directory exists and that
   `git rev-parse --show-toplevel` from inside it identifies the intended
   independent Git root. Read its native README, applicable instructions, and
   policy before acting.

These checks establish where you are; they do not validate an analysis or
authorize a write.

## Where to go for common tasks

The paths in this table are **inside the named independent repository**, not
files tracked by `TOP26006_fw`. In the managed workspace, locate the repository
using the [registry](../governance/repositories.md), then verify its Git root.

| Task | Repository and native starting point |
| --- | --- |
| Analysis | `topeft`: `docs/README.md`, then `docs/tutorials/analysis_workflow.md`. |
| Plotting | `topeft`: `docs/how_to/plotting.md`; `docs/reference/plotting.md` has interface details. |
| Datacard workflow | `topeft`: `docs/how_to/datacards_and_scalings.md` and `docs/how_to/datacard_packages.md` for analysis-side creation, scalings, and package handoff. Resolve the owner of a particular card, model, or schema for that task before changing it. |
| Statistical fitting | `EFTFit`: `README.md` for the native fit package and its local documentation route. |
| Production | `topeft`: `docs/how_to/production.md`. |
| Scientific documents | `ANDOCS` coordinates local document work. `ANDOCS/TOP-26-006` is the independent paper repository and `ANDOCS/AN-24-174` the independent analysis-note repository; start at each available repository's `README.md`. |
| Shared framework mechanisms | `topcoffea`: `docs/README.md` and `docs/topeft_integration.md` for shared interfaces and the handoff with `topeft`. Task-specific analysis workflows remain in `topeft`. |

The `EFTFit` route names its repository and README because deeper local docs
are not established as available through its public default branch. The
document repositories are likewise separate checkouts, not contents promised
by a fresh `TOP26006_fw` clone.

## Working with independent repositories

Choose the repository whose native owner can answer the task, then inspect its
own Git root, state, README, and applicable policy. A root-level Git command
acts on `TOP26006_fw`; it does not report the state of the repositories nested
in the managed workspace. Keep changes, commits, and review evidence tied to
the selected repository. If a task spans repositories, establish each owner's
scope and handle its Git history separately.

## Governance, changes, and evidence

For exact execution and permission rules, use [AGENTS.md](../AGENTS.md).
[CPC.md](../CPC.md) controls Codex prompt construction, and
[CONTRIBUTING.md](../CONTRIBUTING.md) controls reviewer-facing writing. The
[agentic guide](agentic/README.md) explains repository selection and evidence
handoffs. The [registry](../governance/repositories.md) records stable roles;
it is not a record of current branches or task assignments.

Reports and reading-room material are useful provenance for specific earlier
decisions. They are not substitutes for current policy, native documentation,
or a fresh check of the repository involved in a new task.

## When something is missing or ambiguous

If an independent checkout is absent, find its owner and approved access or
setup route before proceeding. Do not infer a clone URL or directory layout.
If a repository is present but the owner of a particular artifact or decision
is unclear, resolve that owner for the concrete task before editing. If local
instructions conflict, use the applicable policy files and raise the specific
conflict to the responsible owner.

## Next references

- [Repository roles and paths](../governance/repositories.md)
- [Agentic architecture and workflow guide](agentic/README.md)
- [Contribution and review writing](../CONTRIBUTING.md)
