# How to inspect resolved configuration

After choosing `wrap` and `python_env` as in [Tutorial 1](../tutorials/01_prepare_a_research_project.md), run the resolver from the coordination checkout:

```sh
cd "$checkout"
"$wrap" "$python_env" tools/resolve_local_profile.py \
  --profile .top26006/local_profile.yml --execution-ready --format yaml
```

Omitting `--profile` also selects the checkout profile. In the example installation, a representative YAML checkpoint has `workspace_root: /home/alice/work/TOP26006_fw`, `repositories.TOP26006_fw.path: /home/alice/work/TOP26006_fw`, and `repositories.topeft.path: /home/alice/work/topeft`. The displayed paths vary with your installation. The default human format provides a shorter readback.

`--execution-ready` rejects placeholders and requires an absolute workspace root, then normalizes paths. It checks profile shape/path readiness, not whether each target exists, whether Git state is suitable, whether a provider works, or whether work is authorized or scientifically valid. Compare the resolved `topeft.path` with `git -C /home/alice/work/topeft rev-parse --show-toplevel` after substituting your real path. A missing default profile or recursive YAML alias produces a controlled input error. See the [profile contract](../reference/local_profile.md).
