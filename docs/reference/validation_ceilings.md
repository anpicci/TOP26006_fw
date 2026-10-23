# Validation ceilings

[AGENTS.md section 17](../../AGENTS.md) is authoritative. The current literal ceilings are:

| Value | Maximum class |
| --- | --- |
| static_inspection_only | Files, Git readback, static diff. |
| lightweight_import_or_cli_probe | Bounded import, help/version, compilation probe. |
| targeted_unit_test | Named focused tests. |
| workflow_dry_run_or_config_validation | Bounded no-submit workflow/configuration probe. |
| production_execution | Explicit production action only. |

A ceiling never requires every check below it and does not grant side effects. Record actual commands, inputs, outputs, and limits. A synthetic dry run establishes only its bounded claim, not a real-data method or production result.
