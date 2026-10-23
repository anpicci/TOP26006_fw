# Validate a prompt before execution

**Problem:** a prepared prompt may be malformed or internally inconsistent.

Run the maintained [prompt-contract validator](../../.agents/skills/correction-lib-prompt-contract/SKILL.md) through the configured wrapper and interpreter on the **filled dispatchable prompt**, following its usage instructions. Inspect its error, warning, and normalized-value output. Then independently compare repository scope, mode, branch role, permissions, evidence, and stop rules against live [CPC.md](../../CPC.md), [AGENTS.md](../../AGENTS.md), registry, and native policy.

A mechanical PASS checks only what the validator implements. It does not establish governance completeness, owner authorization, scientific method, or execution readiness. Do not feed placeholder [templates](../../templates/bounded_change_prompt.md) to it as dispatchable prompts.
