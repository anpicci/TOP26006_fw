# Tutorial 7: coordinate a sequential two-repository change

**Learning goal:** transfer evidence across a genuine repository dependency while keeping each repository's authority, validation, and acceptance separate.

Use this lesson only when the task genuinely crosses two maintained repository boundaries. If one repository is sufficient, stay in one repository. This is an intermediate route after the everyday lifecycle, not a requirement for a newcomer. A second repository may remain read-only when it supplies an interface contract; both repositories need not change.

## Follow the dependency serially

Start with the question you can answer in one repository. Add a second repository only when that answer depends on its maintained result or interface. Call the repository supplying that result the **provider** and the repository using it the **consumer**. These roles belong to this dependency, not permanently to a project.

First identify each repository, its exact commit, relevant local changes, and its own policy and responsible human. State the precise claim to transfer. Attach the minimum evidence supporting it: source and input identities, relevant interface contract, check method and result, limitations, and provider review/acceptance status with its exact scope. A recorded PASS covers only the checks actually performed.

Then continue in the consumer under its own authorization. Reuse accepted provider checks while their sources, inputs, assumptions, and methods remain valid. The consumer still needs evidence that its selected provider revision works at the affected interface with its own configuration and downstream use. Agree the relevant local checks with the consumer's responsible human; provider PASS cannot replace them. Review and accept the consumer result separately. Recording two commits establishes identity, not compatibility or scientific validity.

| Item | Provider side | Consumer side |
| --- | --- | --- |
| Repository identity | Exact repository and commit; relevant local changes | Its own repository and commit; selected provider revision |
| Claim/evidence | State precisely what each artifact supports | State which claim is relied upon and its limits |
| Validation | Provider-local checks and observed results | Consumer-local compatibility and impact checks still required |
| Acceptance | Record responsible human, decision and claim ceiling | Separate responsible-human decision; acceptance does not migrate |
| Permissions | Handoff grants none | Obtain consumer-side authorization for the proposed action |
| Invalidation | Relevant source, input, assumption or method change; missing or contradictory evidence | Consumer configuration, dependency or interface drift may require a fresh local check |
| Repetition | Preserve accepted checks while evidence remains valid | Repeat only invalidated or directly coupled checks |

Provider then consumer is a sufficient normal sequence. If the consumer stops or a compatibility check fails, preserve valid provider evidence and report the unresolved consumer state. Separate histories have no global transaction and imply no automatic rollback. Neither write permission, repository authority, scientific acceptance nor automatic validation crosses with the evidence.

## Dated example: a shared correction interface

Suppose you need to understand what correction evidence to carry from TOPCOFFEA before changing or accepting its use in TOPEFT. The maintained documentation observed locally on **2026-11-02** describes TOPCOFFEA as providing reusable correction mechanisms and packaged shared payload interfaces, while TOPEFT selects their era/tag/payload, working point, enabled variations and analysis application. This is one correction-interface family example, not a choice of calibration or scientific policy.

The observation is bound to these separate local identities:

- Provider TOPCOFFEA: `7363c89a16c8e08632e2eac23040eb09324beb5a`.
- Consumer TOPEFT: `22f1ff174c10eb5cd4900ba08b1943b85e24b8a4`.

Read the native files at those revisions: TOPCOFFEA's `docs/correction_interfaces.md` (mechanism/policy boundary) and `docs/topeft_integration.md` (interface responsibilities and ref selection); TOPEFT's `docs/reference/shared_topcoffea_interfaces.md` (corrections and calibrated objects) and `docs/how_to/corrections_weights_and_systematics.md` (shared-mechanism route). Locate the checkouts through the [native-repository bridge](02_add_an_analysis_repository.md). Operational instructions remain in those native manuals.

Those docs say the consuming workflow selects an exact compatible TOPCOFFEA ref and both commits must be recorded. Similar branch names are not compatibility evidence. These observed commits identify the documentation read; they are **not a qualified compatible pair** or a timeless dependency prescription. No native execution or compatibility check supports this example.

For a future authorized correction change, hand over the exact provider revision, affected interface contract, provider check artifacts and their limits, plus actual review/acceptance status. If checks have not run or acceptance is pending, say so. TOPEFT can reuse still-valid provider evidence, but must verify its own selected dependency, dispatch and affected downstream use under native authority before accepting its result. That consumer check is pending in this reading example. A relevant provider interface or consumer configuration change invalidates the corresponding part of the handoff; simply introducing a second repository does not invalidate unrelated accepted work.

**Checkpoint:** explain why this question needs two authorities, which evidence can be reused, which consumer check remains, and who may authorize and accept that consumer action. Use the [handoff template](../../templates/handoff.md) to record the unresolved boundary.

## Optional documentary practice: prepare an evidence transfer

You are the researcher preparing evidence for a receiving methods responsibility. Your purpose is to decide which analysis claim can be carried across and what the recipient must still establish. You will produce a **personal evidence-transfer draft**, using the existing [handoff template](../../templates/handoff.md) as a read-only guide. You need only read access to that template and the [observed scenario](../../examples/research_workflow_lifecycle/observed_scenario.md), plus a place for your own draft. No previous tutorial execution, scratch repository, shell variables, or historical Git objects are required. A saved [Tutorial 6](06_continue_from_existing_evidence.md) draft may help, but is optional.

### Select the documented transfer stage

Use the scenario's analysis-to-methods stage: **after provenance repair, at the methods evidence record, before the later intentional stop**. Locate the rows “Review finding”, “Provenance repair HEAD”, and “Methods evidence HEAD”, and read the qualification paragraph below the table. Do not import the later dirty analysis state into this earlier transfer.

Record the scenario and template paths, the version or file hash available from your reading source, and the selected stage in your personal draft. If source version information is unavailable, record that limit rather than inventing it. Historical commits in the scenario identify its separate teaching histories; you need not possess or interrogate them. They do not identify your present checkout.

### Write and justify the transfer

Fill the relevant handoff fields in your own words. Make these selections explicit:

| Entry in your draft | Selection and explanation to produce |
| --- | --- |
| Claim and two roles | Choose the bounded synthetic arithmetic claim the methods record relies on. Explain why analysis supplies evidence and methods receives it for this dependency, and why their responsibilities remain separate. Quote the reported quantities and independent Gaussian assumption with their synthetic limits. |
| Source and input identities | Extract the analysis seed, first bounded note, provenance repair, methods evidence and CSV identifiers from their named scenario rows. Label each stage separately: a repaired note's commit is not proof that its contents cite that same final commit. Identify what the summary actually reports and what underlying contents you have not inspected. |
| Review and acceptance | Explain the initial provenance omission and the reported repair without a repeated numerical run. Attribute bounded task/evidence acceptance of the repaired arithmetic record to the scenario's simulated research coordinator after review; no independent human scientific acceptance or real-data qualification is established. |
| Evidence to reuse | Select the reported arithmetic and repaired provenance record, while keeping source, input, assumption and review limits attached. Explain why unchanged accepted checks need not be replayed simply because methods receives the evidence. |
| Receiving-side checks | Identify what methods must still establish: the actual selected analysis revision, readable full evidence, suitability for its intended use, affected interface/configuration checks where relevant, and its own review and responsible-human acceptance. The historical methods commit alone proves none of these for a new task. |
| Missing information and decision | List unavailable original notes, full command receipts or attachments, actual repository paths/branch/HEAD/status, current permissions and responsible humans. Explain which proposed action each gap prevents. Propose the smallest authorized evidence-acquisition step for a real transfer and name the human decision needed before it can proceed. |

The compact scenario does not supply the full original notes, compatibility results or current repository states. Mark an item unavailable when it is absent; do not reconstruct it as original evidence. Writing this draft changes neither maintained inputs nor a methods repository and grants no permission for the real task it describes. Evidence crosses the boundary; write authority and acceptance do not.

### Reopen, check and continue

Save your draft with its input locators, selected stage, completed entries and unresolved items. To restart, reopen that draft and the named scenario/template. Compare the recorded source version or hash if available; otherwise retain the unresolved identity limit. Resume at the first incomplete entry. A changed source requires reviewing only the affected claim. To enter directly or start afresh, use the same documented stage and a new personal draft; no prior shell or repository state is needed.

**Checkpoint:** compare every entry with the scenario rows and template. Can you explain why two responsibilities matter, which evidence travels, which authority does not, and which checks and human decision remain with the recipient? Have you kept the later stop separate and identified missing originals rather than inventing them? The output is an assessable documentary draft; it demonstrates no executed Git operation or newly accepted consumer result. For the separate documented stop, continue to [Tutorial 8](08_recover_from_a_stopped_task.md); for a successor handoff, use [Tutorial 9](09_transfer_work_to_a_collaborator.md).
