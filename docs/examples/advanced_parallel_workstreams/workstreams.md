# Workstreams — synthetic teaching record

This record supplies workstream responsibilities and review/acceptance routes.
[Coordination](coordination.md) supplies the concrete events and decision
references; [evidence dependencies](evidence-dependencies.md) projects those
facts alongside input and validity relationships. For the same decision, compare
result/decision identity, review, actor function/remit, acceptance layer, scope
and validity. Titles alone confer no remit; the [roles explanation](../../explanation/roles_and_authority.md)
supplies the generic distinction. Route changes require checking the associated
events, map rows and passages that actually consume the changed fact.

Workstream IDs name research responsibilities. They are not branches, repositories, models, agents, or sessions. The current responsibility source is the hypothetical teaching assignment approved by the simulated research lead `AUTH_CASE_1`, with transfer `AUTH_TRANSFER_1` recorded in [coordination](coordination.md); neither ID is live TOP26006_fw authority. All effects below mean edits to this teaching case only.

| workstream_id | research_question | scope | exclusions | responsible_role | executor_if_relevant | source_material_refs | expected_output_ids | dependency_refs | permitted_effects | review_route | acceptance_route | current_responsibility_source | coordination_record_ref |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| W_METHODS | What estimate follows the declared measurement rule? | State the rule and derived estimate. | No raw-data alteration or scientific adoption. | Methods researcher; receiver after transfer: methods researcher B. | Human simulation; no agent. | D_RAW_R1, D_SHARED_R1 then D_SHARED_R2. | E_METHODS_R1, E_METHODS_R2. | D_RAW_R1, D_SHARED_R1, D_SHARED_R2. | Draft new evidence revision in this fixture. | Separate methods reviewer, REV_METHODS_R1/R2. | Simulated scientific lead, ACC_METHODS_R1/R2 for scientific method/interpretation acceptance of the exact estimate revision and scope. | AUTH_CASE_1; AUTH_TRANSFER_1 effective only after C10. | C01, C04, C06, C07, C10 |
| W_CHECK | Is the fixed raw-observation listing complete against its declared source? | Compare listing with D_RAW_R1; report only listing completeness. | Does not check exclusion rule, estimate, or note. | Checking researcher. | Human simulation; no agent. | D_RAW_R1. | E_CHECK_R1. | D_RAW_R1 only. | Draft checking evidence in this fixture. | Separate checking reviewer, REV_CHECK_R1. | Simulated research coordinator, ACC_CHECK_R1 for bounded task/evidence acceptance of listing completeness only; no scientific acceptance. | AUTH_CASE_1. | C02, C05 |
| W_NOTE | How should the accepted estimate and limitations be explained? | Explain only an accepted methods revision. | No independent estimate or silent acceptance. | Note researcher. | Human simulation; no agent. | E_METHODS_R1 then E_METHODS_R2. | E_NOTE_R1, E_NOTE_R2. | E_METHODS_R1, E_METHODS_R2. | Draft new note revision in this fixture. | Separate note reviewer, REV_NOTE_R1/R2. | Simulated scientific lead, ACC_NOTE_R1/R2 for scientific interpretation acceptance of the exact explanation revision and scope. | AUTH_CASE_1. | C03, C04, C08, C09 |

`W_CHECK` independence dimension: **input-assumption independence from the warm-up exclusion rule**. Its shared input is `D_RAW_R1`; its shared code or method is a human comparison of the observation listing, not the methods estimator. The checker saw the raw listing and knew the methods question, but did not use or inspect `E_METHODS_R1` before recording `E_CHECK_R1` (prior-result exposure: none). Executor/model commonality: all steps are a single human-authored simulation, so there is no claim of independent personnel, model, session, or agent. This check cannot validate the estimate.
