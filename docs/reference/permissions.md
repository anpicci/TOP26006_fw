# Permissions and effects

[AGENTS.md sections 2–5 and 11](../../AGENTS.md) control repository and capability permissions. A prompt must identify the exact writable repository, paths, and effects; all other repositories remain read-only by default. A local profile path, registry entry, working credential, or executable creates no permission.

Separate grants govern network use, remote Git write, PR/MR write, merge, remote branch deletion, production, environment change, storage output, and cleanup. An allowed local commit is distinct from a remote push. Current [provider compatibility](provider_compatibility.md) limits concrete tool assumptions. See [bounded authorization](../how_to/authorise_a_bounded_change.md) for the task-oriented route.
