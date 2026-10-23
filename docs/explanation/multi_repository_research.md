# Multi-repository research

Different repositories may own analysis, methods, documentation, or evidence. Each has its own Git history, native policy, and responsible authority. The [typed registry](../../governance/repositories.md) records durable roles; a local profile maps those IDs to paths in one installation. Neither describes the current branch or grants cross-repository mutation.

Sequential coordination moves a *qualified evidence object* from one role to another. The analysis side produces an identified result with inputs, assumptions, observations, and review. The methods side receives only the parts needed for its note and obtains a separate authorized task. In the [synthetic scenario](../tutorials/07_coordinate_a_multi_repository_change.md), two scratch repositories demonstrate this flow without inspecting project child repositories.

Simultaneous development workstreams require additional coordination decisions. They are outside this core route.
