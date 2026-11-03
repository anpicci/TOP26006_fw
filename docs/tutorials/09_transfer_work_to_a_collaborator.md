# Tutorial 9: transfer work to a collaborator

**Learning goal:** give a collaborator enough durable evidence and residual context to continue without reopening valid accepted work.

A handoff can stay inside one repository or span several. Use only the repositories the task actually needs. Start with the [handoff template](../../templates/handoff.md): state the purpose, exact repository identities, artifact locations and what each artifact establishes. Distinguish reviewed/accepted claims and their limits from last-observed state and unresolved work. A last-observed HEAD or clean status must be refreshed when continuation depends on it; it is not a permanent guarantee.

Describe what would invalidate reused evidence and which checks should not be repeated while that boundary holds. Reopen only the invalidated or directly coupled delta, rather than rerunning everything for confidence. Include relevant uncommitted changes as identified evidence, without adopting them or granting permission to change them.

The recipient first locates and reads the evidence, then checks decision-material current identities and local state. They confirm what is established, what is pending, and the next responsible-human decision. A handoff transfers context and evidence; it grants no write permission, repository authority, scientific acceptance or authorization to rerun closed work. Any residual action needs its own applicable authorization. Executor completion, repository-local validation and human acceptance are separate statuses.

For a provider-to-consumer handoff, record both commits and the claim relied upon using [Tutorial 7's transfer map](07_coordinate_a_multi_repository_change.md#follow-the-dependency-serially). Provider checks remain provider-local. The consumer must still verify its selected dependency and affected use and obtain separate acceptance. Preserve valid provider work if consumer work remains pending or fails; there is no global rollback.

**Recipient checkpoint:** without oral context, identify the accepted claim and evidence, last observation to refresh, unresolved delta, invalidation triggers, checks not to repeat, authorization still needed and next human decision. Confirm acquisition and understanding separately from sending the handoff.

## Optional documentary practice: prepare a successor handoff

You are the researcher preparing a successor to assess a stopped local task without oral project history. You will write a **personal handoff draft** using the [observed scenario](../../examples/research_workflow_lifecycle/observed_scenario.md) and the existing [handoff template](../../templates/handoff.md), both read-only. You need read access and somewhere to save your draft. No previous tutorial execution, scratch repositories, shell variables, historical Git objects or contact with another person is required. A saved [Tutorial 8](08_recover_from_a_stopped_task.md) assessment is optional supporting work.

### Enter at the documented intentional stop

Use the scenario's “Intentional stop” row and qualification paragraph. At this later stage the scenario reports that expected and observed analysis HEAD were both the provenance-repair HEAD, status was ` M interpretation.md`, and the diff added `unexpected local edit after accepted commit`. The earlier repaired record remains prior closure; the later working tree was dirty. Do not describe that stopped state as a clean accepted result or as your current checkout.

Record the scenario and template paths, their available version or file hash, and this exact stage in your draft. If version information is unavailable from your reading source, mark it unresolved. The scenario describes an added line; it does **not** provide a complete original stopped-state patch. Do not generate a patch from a nonexistent repository or present a reconstructed line as that original artifact.

### Prepare a handoff someone else could assess

Use the template fields to make the following evidence-based selections. For every established claim, cite the scenario row or paragraph that supports it; for every unknown, explain what next action depends on it.

1. **Purpose, roles and established claims.** State the successor's decision: how to obtain current evidence and have the responsible human classify the stopped edit before continuation. Identify the analysis and methods histories separately using their recorded commits and CSV hash. Carry the reported synthetic arithmetic, assumption and provenance repair with their qualifications. Identify the owner, executor and reviewer as simulated teaching roles; real ownership and authorization remain unresolved.
2. **Superseded wording and evidence limits.** Record that the first note omitted source commit and CSV hash and that the scenario reports a later provenance repair. The original wording and complete notes/receipts are unavailable here. Locate the reported finding and repair without inventing their full contents. Preserve the distinction between the reported stopped diff and possession of its original patch; request the full task-scope evidence before any real recovery decision.
3. **Last observations and unresolved state.** Quote the stop row's equal expected/observed HEAD, modified-note status and added line as historical observations. Explain why HEAD equality does not imply cleanliness. Current paths, branch/HEAD, index, working tree, edit ownership and any interrupted-command effects need fresh authorized readback; the scenario cannot settle them. Treat the methods record as separate prior evidence, not proof of current consumer compatibility.
4. **Reuse and invalidation.** Choose which reported checks should not be repeated while their inputs, source, method and assumptions remain valid: the numerical run and closed provenance repair. Name which relevant changes or missing/contradictory evidence would reopen each claim. A dirty note line alone does not invalidate the earlier arithmetic; its ownership still blocks adopting or overwriting it.
5. **Next human decision and permissions.** Propose bounded read-only acquisition of actual HEAD, task-scope staged/unstaged status and full diff, note contents and any command receipt. Preserve the edit while the responsible human classifies it and authorizes an exact continuation. Mark real write, retry, cleanup and acceptance permissions unresolved; this handoff grants none.
6. **Recipient readback.** Mark acquisition and comprehension **pending** until a real successor locates, reads and confirms the evidence. Preparing or sending a handoff is not that confirmation. This optional exercise ends with your own draft check and requires no contact; a real later handoff needs its own context and authorization.

Save your personal draft with exact input locators, the last completed entry and unresolved evidence requests. It must let a reader find the compact source and see both what it supports and which originals remain missing. Writing the draft does not modify the scenario, template or stopped evidence.

### Restart and check your output

Reopen your saved draft and its named scenario/template after interruption. Compare recorded versions or hashes when available, retaining any unresolved identity limit. Resume at the first unanswered field without recreating the stop, querying historical refs or replaying arithmetic. If a source changed, preserve the earlier assessment and revisit only affected claims. To start directly or afresh, use the same intentional-stop stage and a new personal draft.

**Draft checkpoint:** compare your handoff with every template field and the scenario. Can a reader locate prior closure, superseded provenance, last observations, the reported stopped edit, missing full patch, invalidation triggers, protected checks and next human decision without oral history? Have you kept simulated acceptance separate from real acceptance and your self-check separate from recipient confirmation? Record gaps instead of claiming completeness unsupported by the summary. Completion demonstrates a documentary handoff draft, not recovery execution or recipient comprehension. Return to the [manual index](../index.md); for a real continuation, first resolve the identified evidence and owner decisions under its separately authorized task.
