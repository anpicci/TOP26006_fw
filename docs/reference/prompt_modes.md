# Prompt modes

[AGENTS.md section 6](../../AGENTS.md) and [CPC.md section 6](../../CPC.md) are authoritative. The current literal vocabulary is:

| Value | Primary activity |
| --- | --- |
| investigation_only | Evidence without tracked mutation. |
| coding | Bounded implementation/configuration change. |
| validation_only | Validation without tracked source edits. |
| test_alignment_only | Test correction after runtime intent is proven. |
| documentation_only | Tracked documentation after behavior is established. |
| commit_preparation | Exact-path staging and local commit. |
| pr_preparation | Reviewer text from established evidence. |
| integration_only | Exact local integration decision. |
| branch_maintenance_only | Exact local ref lifecycle decision. |
| orchestrated_workflow | Ordered preauthorized stages. |
| pr_publication | Exact remote publication action. |
| production_execution | Explicit production capability only. |

A mode names an activity contract, not a permission grant. Read the live mode section before dispatch; this table does not replace its conditions.
