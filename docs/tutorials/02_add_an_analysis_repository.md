# Tutorial 2: map an analysis repository

**Learning goal:** distinguish the stable research role of a repository from a path chosen in one installation. No child repository is needed for this exercise.

1. Find the `repository_id` for the analysis work in the [typed registry](../../governance/repositories.md). The registry records identity, role, and profile keys. For example, a profile key already named there can point to a separate analysis checkout. It does not assert that the checkout exists on your machine.

2. In `.top26006/local_profile.yml`, add or change that existing repository key's `path` to the actual local directory once it is available. A workspace-relative value resolves against `workspace_root`; an absolute value keeps its absolute location. For a first exercise, leave the example's `TOP26006_fw.path: .` intact and inspect it:

   ```sh
   "$wrap" "$python_env" tools/resolve_local_profile.py --execution-ready --format yaml
   ```

3. Practice fresh Git readback on the coordination checkout:

   ```sh
   git -C "$checkout" rev-parse --show-toplevel
   git -C "$checkout" branch --show-current
   git -C "$checkout" rev-parse HEAD
   ```

   Here `$checkout` names only TOP26006_fw. Once a separate checkout is available and its native owner has supplied the setup route, perform the same readback in **that repository** under its own policy. A [remote alias](../reference/glossary.md) is a local Git name such as `origin`; the profile does not supply or verify the remote URL. The registry does not report a live branch or HEAD.

A **brand-new** project repository requires a separate governed registry change. Editing a private profile can only map an already-known identity to local installation facts. Read [repository and workspace identity](../explanation/repository_and_workspace_identity.md) and [roles and authority](../explanation/roles_and_authority.md) before assigning work there. Continue to [Tutorial 3](03_complete_a_first_read_only_task.md) in this coordination checkout.
