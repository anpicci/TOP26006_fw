# How to configure your local YAML profile

From your coordination checkout, copy `config/local_profile.example.yml` to the ignored `.top26006/local_profile.yml`. Replace `workspace_root` with the absolute checkout path, `tooling.command_wrapper` with your wrapper path, and `tooling.python_interpreter` with your existing Python path. Use YAML only. Keep `TOP26006_fw.path: .` when the workspace root is the checkout; map any additional already-governed repository IDs to their real local paths only when needed.

Do not add credentials or permission claims. The [schema](../../config/local_profile.schema.yml) and [reference](../reference/local_profile.md) give the closed shape. `provider_procedure: openai_codex` labels this reference procedure and proves no other provider compatibility. Then [inspect the resolved configuration](inspect_the_resolved_configuration.md).
