# Adapt paths and remotes

**Problem:** the same research repository has a different location or remote name on your machine.

Use the ignored [YAML local profile](../reference/local_profile.md) for the checkout's filesystem path. Compare the resolved path with a fresh Git top-level query. The [registry](../../governance/repositories.md) owns stable identity; changing a path does not create a repository.

A Git remote alias such as origin is a local name; its URL and advertised branch are separate live facts. Inspect them only when the task authorizes that observation. Credentials belong to the local authentication system, never the profile or documentation. A path, alias, URL, and credential answer four different questions and none authorizes network access or a push. See [provider status](../reference/provider_compatibility.md).
