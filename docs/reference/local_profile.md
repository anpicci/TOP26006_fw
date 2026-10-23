# Local profile reference

The TOP26006_fw local profile is YAML at `.top26006/local_profile.yml` by default. An explicit `--profile PATH` overrides it. The maintained [schema](../../config/local_profile.schema.yml) is the exact shape authority; [the example](../../config/local_profile.example.yml) shows placeholders to replace. No JSON profile or fallback exists.

| Key | Meaning |
| --- | --- |
| `profile_version` | Must be `1`. |
| `profile_name` | Local descriptive name. |
| `workspace_root` | Absolute base path in execution-ready mode. |
| `evidence_root` | Evidence path; relative values resolve inside workspace root. |
| `provider_procedure` | Label for the selected procedure; `openai_codex` is the current reference, not a compatibility certificate. |
| `tooling.command_wrapper` | Local command-forwarding wrapper path. |
| `tooling.python_interpreter` | Existing Python interpreter path. |
| `repositories.<repository_id>.path` | Concrete checkout path for a registry-known identity. |
| `repositories.<repository_id>.remote_aliases` | Optional local Git alias names, not URLs or observed remotes. |

Absolute paths retain their location. Relative paths are normalized against `workspace_root` and cannot escape it. Unknown keys, duplicate keys, credential-like keys, recursive YAML aliases, malformed values, and relative path escapes fail. `--execution-ready` rejects placeholders and requires an absolute workspace root; it does not check path existence, provider behavior, Git state, scientific validity, or authorization. Use [inspection guidance](../how_to/inspect_the_resolved_configuration.md) before any task.
