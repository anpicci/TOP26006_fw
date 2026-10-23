# Tutorial 1: prepare a research project

**Learning goal:** set up the coordination checkout so a later research task can name its evidence and execution environment. This is an OpenAI/Codex reference procedure; [other providers need adaptation](../reference/provider_compatibility.md).

Start with a research question you might later investigate, such as whether five synthetic calibration measurements are consistent with one common value. Keep scientific interpretation separate from installing the tools.

1. Obtain the private TOP26006_fw coordination repository through an approved project access route. Place it in any sensible workspace and checkout directory. In the shell below, set `checkout` to **your actual TOP26006_fw checkout**, whatever its directory name:

   ```sh
   checkout=/path/to/your/research-coordination
   cd "$checkout"
   git rev-parse --show-toplevel
   git branch --show-current
   git rev-parse HEAD
   git status --short
   ```

   These observations identify the current local Git state; they grant no task permission. [Names and identity](../explanation/repository_and_workspace_identity.md) explains why the directory name is not the project name.

2. Set `python_env` to an already-prepared interpreter's absolute path. For this learning exercise, create a minimal **local installation choice**: a command wrapper that forwards its arguments. It is not maintained project infrastructure and does not activate or install an environment. Put it in your ignored `.top26006` directory, then use it to check that Python can import PyYAML:

   ```sh
   python_env=/path/to/prepared/python
   mkdir -p .top26006
   cat > .top26006/python_wrapper.sh <<'WRAPPER'
   #!/bin/sh
   set -eu
   exec "$@"
   WRAPPER
   chmod 700 .top26006/python_wrapper.sh
   wrap="$checkout/.top26006/python_wrapper.sh"
   "$wrap" "$python_env" -c 'import yaml; print(yaml.__version__)'
   ```

   The interface is `"$wrap" COMMAND [ARG ...]`: it runs the supplied command and returns its status. Your site can supply another local wrapper that prepares an existing environment. The current deployment's `codex-run.sh` has site-specific activation paths and is not a portable tracked dependency. [Prerequisites](../how_to/check_prerequisites.md) and [profile setup](../how_to/configure_your_local_profile.md) give task-oriented detail.

3. Copy the tracked YAML example and replace only installation facts. Set `workspace_root` to your absolute checkout path, `tooling.command_wrapper` to `.top26006/python_wrapper.sh`, and `tooling.python_interpreter` to your prepared Python path. Keep `provider_procedure: openai_codex` for this reference procedure; do not infer another provider from the label.

   ```sh
   cp config/local_profile.example.yml .top26006/local_profile.yml
   ```

   Use your editor for the three values. Do not put credentials or task permissions in this file. The [local profile reference](../reference/local_profile.md) lists the allowed keys.

4. Check the profile through the chosen wrapper and interpreter:

   ```sh
   "$wrap" "$python_env" tools/resolve_local_profile.py --profile .top26006/local_profile.yml --execution-ready --format yaml
   "$wrap" "$python_env" tools/resolve_local_profile.py --execution-ready --format yaml
   ```

   The second command selects the checkout's `.top26006/local_profile.yml` even if the caller later works from another directory. The resolver validates profile shape, path normalization, and placeholder rejection. `--execution-ready` is only profile shape/path readiness; it does **not** qualify a provider, repository, branch, scientific method, task permission, or accepted result. Compare the resolved paths with local evidence before use. [Inspect resolution](../how_to/inspect_the_resolved_configuration.md) explains the fields.

**Checkpoint:** you have a local execution route and can identify the coordination Git root. Continue to [Tutorial 2](02_add_an_analysis_repository.md), where a stable repository ID meets a local path. The [research workflow](../explanation/research_workflow.md) keeps the scientific question visible.
