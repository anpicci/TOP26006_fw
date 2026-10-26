# How to configure your local YAML profile

From your coordination checkout, copy `config/local_profile.example.yml` to the ignored `.top26006/local_profile.yml`:

```sh
checkout=/home/alice/work/TOP26006_fw  # example; replace with your real checkout
cd "$checkout"
mkdir -p .top26006
cp config/local_profile.example.yml .top26006/local_profile.yml
```

Replace `workspace_root` with the absolute checkout path, `tooling.command_wrapper` with your wrapper path, and `tooling.python_interpreter` with your existing Python path. Use YAML only. Keep `TOP26006_fw.path: .` when the workspace root is the checkout. For [Tutorial 2](../tutorials/02_add_an_analysis_repository.md), set the already-governed `topeft.path` to your separate checkout, for example `/home/alice/work/topeft`; that path is an installation example, not a project default. Map other already-governed repository IDs only when needed.

Do not add credentials, branch roles, or permission claims. The [project repository map](../../governance/repositories.md) owns identities and roles; the profile only supplies local paths and aliases. The [schema](../../config/local_profile.schema.yml) and [reference](../reference/local_profile.md) give the closed shape. `provider_procedure: openai_codex` labels this reference procedure and proves no other provider compatibility. Then [inspect the resolved configuration](inspect_the_resolved_configuration.md).
