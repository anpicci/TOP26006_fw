# TOPEFT project-governance delta

Applies to TOP-26-006 project work in `topeft` when the repository is selected through [`../repositories.md`](../repositories.md). Root `AGENTS.md`, `CPC.md`, and `CONTRIBUTING.md` retain generic safety, authorization, branch lifecycle, prompt, and reviewer rules. Applicable TOPEFT-native/upstream policy also applies. This module cannot grant write or publication permission.

`topeft` owns analysis code, processors, selections, workflow helpers, and CLIs. Its scientific and technical behavior remains repository-native; this module does not define implementation or physics semantics.

## Permanent branch roles

```text
permanent_integration_branch: run3_test_mmerged
permanent_personal_reference_branch: run3_test_mmerged_anpicci
feature_development_namespace: te/*
```

Every `te/*` branch is a feature/development branch, including cumulative, accepted, or current source-writing branches. Cumulative authority does not turn it into a permanent reference/integration branch or remove it from the root reuse-first active-feature gate. One applicable active `te/*` requires continuing it unless an exact owner-authorized exception applies; multiple applicable active features require reconciliation. Applicability follows root semantic/dependency continuity, using fresh Git evidence.

When zero applicable active TOPEFT features are positively proven and ordinary new-feature creation is authorized, construct `create_feature_branch_from_reference` with `reference_branch: run3_test_mmerged_anpicci` and a repository-facing `te/<name>` feature. The integration target remains `run3_test_mmerged`; feature-to-feature consolidation changes neither permanent role. Generic `current_baseline_branch`, `comparison_baseline`, `integrated_baseline_mode`, or equivalent prose cannot silently redefine these roles or bypass reuse-first. Read-only prompts may describe a future branch disposition but must preserve every `te/*` feature's classification.

For prompt construction, encode these permanent roles in every applicable TOPEFT prompt. Keep the generic three branch policies, branch selection gate, exceptions, commit rules and authorization requirements in root governance. Do not use the branch names alone as evidence of current HEAD, active applicability, or permission.
