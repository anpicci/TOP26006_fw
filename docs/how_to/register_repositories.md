# Register a repository identity

**Problem:** a genuinely new research repository needs a stable role in the project.

First identify its scientific or technical owner, repository class, consumers, path key, and applicable native policy. Propose an exact change to the [typed registry](../../governance/repositories.md), and decide whether a dedicated [module](add_or_update_a_governance_module.md) is needed. The coordinator must obtain an authorized governance-change task on a feature branch and review the registry diff.

A private local-profile edit can map an **existing** ID to one installation path; it cannot register a new ID or grant writes. Resolve live Git identity separately after an authorized checkout exists. Do not create a fake registry entry for the [Tutorial 2 mapping exercise](../tutorials/02_add_an_analysis_repository.md).
