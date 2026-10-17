# Getting started

Use this guide to find the repository and documentation for your TOP-26-006
task. The [root README](../README.md) gives a short project overview.

## Project repositories

`TOP26006_fw` coordinates project structure and repository roles. Analysis
software, shared libraries, fit software, and scientific documents are kept in
independent repositories, each with its own Git history and technical
responsibilities. The local checkout path is
`/users/apiccine/work/correction-lib`; `correction-lib` is a directory name,
not the repository identity.

### Fresh clone and managed workspace

A fresh clone of `TOP26006_fw` contains its tracked coordination files. It
does not install the independent repositories that may be checked out in the
managed workspace, such as `topeft`, `topcoffea`, `EFTFit`, or `ANDOCS`. Check
that the repository you need is present and identify its Git root before
using its documentation.

### First read-only checks

From the directory you received:

1. Run `git rev-parse --show-toplevel` and confirm that it identifies the
   intended repository.
2. Run `git branch --show-current` and `git status --short` to see the current
   branch and working-tree state without changing them.
3. Read the root [README](../README.md), then use the task table below to find
   the native repository and starting page.
4. In that repository, confirm its Git root and read its README and applicable
   local instructions before making changes.

These checks identify the repository and its current state. They do not
validate an analysis or grant permission to change project files.

## Where to go for common tasks

The paths below are inside the named independent repository; they are not
tracked by `TOP26006_fw`. In the managed workspace, use the
[repository registry](../governance/repositories.md) to locate a checkout,
then confirm its Git root.

| Task | Repository and native starting point |
| --- | --- |
| Analysis | `topeft`: `docs/README.md`, then `docs/tutorials/analysis_workflow.md`. |
| Plotting | `topeft`: `docs/how_to/plotting.md`; `docs/reference/plotting.md` describes interfaces. |
| Datacard workflow | `topeft`: `docs/how_to/datacards_and_scalings.md` and `docs/how_to/datacard_packages.md` for analysis-side card creation, scalings, and package handoff. Resolve responsibility for a particular card, model, or schema for that task. |
| Statistical fitting | `EFTFit`: `README.md` for the fit package and its local documentation route. |
| Production | `topeft`: `docs/how_to/production.md`. |
| Paper and Analysis Note | `ANDOCS` coordinates local document work. `ANDOCS/TOP-26-006` is the independent paper repository; `ANDOCS/AN-24-174` is the independent Analysis Note repository. Start with the available repository's `README.md`. |
| Shared framework mechanisms | `topcoffea`: `docs/README.md` and `docs/topeft_integration.md` for shared interfaces and their use with `topeft`. Task-specific analysis workflows are documented in `topeft`. |

The `EFTFit` route points to its README because deeper local documentation is
not established as available through its public default branch. The paper and
Analysis Note repositories are separate checkouts; a fresh `TOP26006_fw` clone
does not include them.

## Contributing across repositories

Work in the repository that maintains the software, configuration, or
document relevant to your task. Check its branch and working-tree state, read
its local guidance, and keep its changes and commits in that repository. For a
particular card, model, or schema, confirm responsibility for that artifact
before editing it. The [registry](../governance/repositories.md) records
stable repository roles, not current branches or task assignments.

For project instructions, see [AGENTS.md](../AGENTS.md); for contribution and
review writing, see [CONTRIBUTING.md](../CONTRIBUTING.md). Follow the native
repository's applicable instructions as well.

If a needed checkout is missing, contact its maintainer for the approved
access or setup route. If responsibility for a particular artifact or
decision is unclear, resolve it for that task before making a change.
