# Prompt contract

The authoritative field contract is [CPC.md section 4](../../CPC.md) with execution constraints in [AGENTS.md](../../AGENTS.md). A dispatchable prompt states one **decision_question**; prompt ID, title, mode, model/reasoning/delegation choice; repository locations and allowed/read-only surfaces; branch policy and validation ceiling; effect permissions; evidence, stop, patch, and final-report contract as applicable.

A continuation identifies accepted prior evidence, delta, invalidation boundary, and checks not to repeat when those carry real state. An orchestrated workflow declares ordered stages and a stop policy. Field presence and mechanical validation do not prove owner authorization or scientific adequacy. [Manual writing](../how_to/write_a_prompt_manually.md) is for an author who can check the live contract; [validator use](../how_to/validate_a_prompt_before_execution.md) is a separate mechanical check.
