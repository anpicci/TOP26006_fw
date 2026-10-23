# Add or update a governance module

**Problem:** a registry repository needs rules beyond common project governance.

First show the concrete repository-specific constraint: for example a native branch role, document validation level, or stricter default. Name the repository ID, native authority, affected paths, and consumers. Propose the minimal module under the [governance registry](../../governance/repositories.md) and register it there through an authorized governance task. Review it against [AGENTS.md](../../AGENTS.md), [CPC.md](../../CPC.md), and native policy.

A module adds constraints; it cannot weaken common safety, create a write grant, or transfer scientific ownership. Keep generic lifecycle rules in the root sources. If no repository-specific delta exists, use the registry's inherited module status.
