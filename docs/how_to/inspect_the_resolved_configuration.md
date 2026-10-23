# How to inspect resolved configuration

After choosing `wrap` and `python_env` as in [Tutorial 1](../tutorials/01_prepare_a_research_project.md), run the resolver with either explicit `--profile .top26006/local_profile.yml` or without `--profile`. Both should resolve the checkout profile. Use `--format yaml` for structured output or the default human format for a short readback.

`--execution-ready` rejects placeholders and requires an absolute workspace root, then normalizes paths. It checks profile shape/path readiness, not whether each target exists, whether Git state is suitable, whether a provider works, or whether work is authorized or scientifically valid. Compare output with local filesystem facts and fresh Git readback. A missing default profile or recursive YAML alias produces a controlled input error. See the [profile contract](../reference/local_profile.md).
