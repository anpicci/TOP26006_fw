# Repository and workspace identity

`TOP26006_fw` is the governed project and coordination repository; its local checkout directory can have any sensible name. The [typed registry](../../governance/repositories.md) assigns stable `repository_id`, role, and profile-key meaning to each governed repository. An ignored [local profile](../reference/local_profile.md) maps those identities to this installation's paths. Neither the directory spelling nor the profile changes the stable identity.

A remote alias is a local Git name, such as `origin`, whose actual target requires separate live inspection when relevant. Branch role describes a governed purpose; `git branch --show-current`, `git rev-parse HEAD`, and status report the current observed ref and tree. Registry and profile text cannot replace that readback. Independent repositories retain separate histories and native policy. Adding a new registry identity is a governed project change, not a local path edit.
