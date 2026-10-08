# AI assistance with scientific documentation

This page explains the project agent's role around `ANDOCS`, the independent document coordination repository. Its paper `TOP-26-006` and Analysis Note `AN-24-174` are separate native Git histories with their own document owners, scientific review, and applicable CMS/collaboration policy. The live [`ANDOCS` module](../../governance/modules/andocs.md) and [`AGENTS.md`](../../AGENTS.md) govern actions. This page gives no authority to edit a paper, note, or result.

## Prefer a consistency audit

The preferred use of agentic AI on scientific documents is to test a specific claim against the right evidence, then give the responsible human a traceable finding. For each claim:

1. Identify its location and scope in the paper, AN, response, table, or caption. Name the relevant year, category, process, variable, and result stage when material.
2. Find the authoritative implementation, resolved configuration, production-bound or otherwise accepted artifact/result, and provenance for that claim. Current source, a test, a diagnostic aggregate, and an old payload have different evidence ceilings; do not treat them as equal to the consumer's actual result. Check native policy and accepted handoffs.
3. Compare the evidence to the *specific* scientific assertion, using compatible definitions and normalization. Compare paper and AN wording when both documents are in scope, but do not assume one automatically wins every disagreement. Official wording and numerical results may have distinct authorities.
4. Record one of **agreement**, **discrepancy**, **missing evidence**, **ambiguous provenance**, or **unverified claim**, with exact source and claim locators and the reason. Keep absent evidence separate from a proven contradiction.
5. Send discrepancies and unresolved authority questions to the document or scientific owner for resolution. Report proposed correction scope only when separately authorized; do not silently rewrite science to make text appear consistent.

For example, if an AN caption quotes a yield, compare it with the accepted result for the same category, selection, normalization, and stage. If the only available number is an older diagnostic total, report **ambiguous provenance** or **missing evidence**, not agreement. The human owner decides the scientific claim and any document revision. The [working guide](working_with_agents.md) explains how to package this evidence without treating a checkpoint as authorization.

## Human scientific authority

AI is not a scientific authority or an authorizing reviewer. CMS and collaboration processes, the analysis team, document owners, qualified scientific reviewers, and applicable native policy retain their roles. Substantive physics statements, methods, selections, uncertainties, interpretations, numbers, tables, plots and captions, conclusions, citations, and reviewer responses require source grounding and human scientific verification. A generated sentence or plausible citation is not evidence.

Scientific prose generation is discouraged by default. Assistance with substantive drafting requires an **explicit human request**, close supervision by a scientifically qualified human, identified authoritative sources, and claim-level human verification **before adoption**. Pure grammar or formatting that adds no scientific assertion can be handled differently; if wording changes a scientific meaning, apply the substantive review boundary. A cross-document audit normally reads both histories and reports findings; it does not merge them or authorize editing both. Native scientific, developer, and user documentation stays with its own owner. Fix an error in this explanatory page here; route an error in native scientific text to its native owner under a separate authorization.
