# TOP26006_fw coordination meta-repository

`TOP26006_fw` is the TOP-26-006 project-governance and coordination repository.
Its local checkout remains `/users/apiccine/work/correction-lib`; no physical
rename is part of this governance change.

The [typed repository registry](governance/repositories.md) identifies project
roles, stable paths and ownership. Root `AGENTS.md`, `CPC.md`, and
`CONTRIBUTING.md` hold common policy; the four files under
[`governance/modules/`](governance/modules/) add repository-specific project
rules for topeft, topcoffea, EFTFit and ANDOCS. The nested implementation,
document, dependency and evidence repositories retain independent Git
histories and their own native policies.

ANDOCS is an independent local-only Git meta-repository at
`/users/apiccine/work/correction-lib/ANDOCS`. The root `/ANDOCS/` ignore rule
keeps its contents out of the TOP26006_fw index. Root governance applies by
ancestry, with the ANDOCS module and retained local compatibility governance;
the paper and AN retain separate Git histories and scientific ownership. The
coordination checkout is local-only for now; any private remote or publication
is a separate future authorization boundary.

## Working with project agents

Start with the [agentic architecture and user guide](docs/agentic/README.md)
for onboarding, repository and authority boundaries, governed agent workflows,
and scientific-documentation review. The guide explains the live policies
linked above; it does not replace them.
