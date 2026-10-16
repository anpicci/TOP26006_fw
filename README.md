# TOP26006_fw

`TOP26006_fw` is the TOP-26-006 coordination and project-governance
meta-repository, privately published as `anpicci/TOP26006_fw`. It connects the
project's implementation, scientific-document, dependency, and evidence work
without combining those repositories into one Git history.

The managed Glados checkout is `/users/apiccine/work/correction-lib`. The
directory name `correction-lib` is a local path, not the repository identity.
Independent repositories in that workspace keep their own branches, policies,
histories, and technical or scientific owners. This repository owns project
governance and coordination; it does not own their implementation or scientific
content.

## Start here

Read [Getting started](docs/getting_started.md) for a safe first inspection and
a task-to-repository guide. A fresh clone of `TOP26006_fw` contains its tracked
files; it does not automatically include the independent repositories present
in the managed workspace. Check that a needed repository is available before
following its native documentation.

For common work, start in `topeft` for analysis, plotting, datacard workflow,
or production; `EFTFit` for statistical fitting; and the separately maintained
document repositories coordinated locally under `ANDOCS` for the paper or
analysis note. `topcoffea` supplies shared framework mechanisms. The
[getting-started routes](docs/getting_started.md#where-to-go-for-common-tasks)
identify the native entry pages and ownership boundaries.

## Governance and contributions

The [repository registry](governance/repositories.md) records stable roles and
ownership. [AGENTS.md](AGENTS.md) governs agent execution,
[CPC.md](CPC.md) governs prompt construction, and
[CONTRIBUTING.md](CONTRIBUTING.md) governs reviewer-facing prose. The
[agentic guide](docs/agentic/README.md) explains how to use those contracts;
these links, rather than this README, provide the detailed rules.

Reports and historical reading material preserve evidence from earlier work.
Use the current governance and native repository documentation as the normal
entry path; consult historical evidence when a specific question needs its
provenance.
