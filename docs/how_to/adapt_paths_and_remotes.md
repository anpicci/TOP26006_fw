# Adapt paths and remotes

Use this guide when an already governed research repository lives at a different local path or uses a different remote alias. This preserves provenance across installations; it does not change repository identity.

## Before you start

Know the stable `repository_id` from the [typed registry](../../governance/repositories.md), the actual checkout path, and the ignored `.top26006/local_profile.yml`. Have the locally configured wrapper and interpreter available. The [profile reference](../reference/local_profile.md) defines the accepted fields.

## Procedure

1. Read the local profile as data. Distinguish `repositories.<repository_id>.path` (installation location), `remote_aliases` (local names), a Git remote URL (configured destination), and credentials (outside the profile). For example, `repositories.sample_analysis.path: /home/researcher/work/analysis` is a local path, not a new registry identity.
2. Edit only the local path or alias for an **existing** registry ID. Keep branch role, permissions, scientific meaning, remote URL, and credentials out of the profile. Use the [schema](../../config/local_profile.schema.yml) to check field names.
3. Resolve the edited profile with the existing wrapper/interpreter; replace the placeholders with paths already verified on this installation:

   ```sh
   "$wrap" /bin/bash --noprofile --norc -c \
     'cd "$1" && "$2" tools/resolve_local_profile.py --profile .top26006/local_profile.yml --execution-ready --format yaml' \
     profile_check "$checkout" "$python_env"
   git -C "$repo" rev-parse --show-toplevel
   git -C "$repo" remote -v
   ```

4. Compare the resolved repository path with Git's top level, allowing only intentional canonical-path normalization. Inspect remote alias and URL without fetching. Record any mismatch before preparing a task.

## Verify the result

The resolved path identifies the intended checkout, the Git top level agrees, and the configured remote aliases are understood. A remote listing is local configuration evidence, not proof of a reachable server or authorization to contact it.

## Stop instead of proceeding if...

The path resolves to another Git root, the ID is absent from the registry, the profile contains a permission/branch/science claim, or the remote identity is decision-material but unverified. Do not infer access or publication authority from a path or URL. See [AGENTS.md](../../AGENTS.md) for live execution permissions.

## Generic example

A researcher moves `sample_analysis` to `/home/researcher/work/analysis` and changes the ignored profile path. The resolved path and Git top level agree before the next task is drafted.

## What this does not establish

Path agreement does not prove current branch, remote reachability, credentials, or permission.
