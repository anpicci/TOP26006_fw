# Evidence, reproducibility, and acceptance

This page explains the distinction between execution evidence, independent
review, bounded task/evidence acceptance and scientific acceptance. Procedures
and lookup pages project these decision layers rather than redefine them.
The [responsibilities explanation](roles_and_authority.md) supplies the role
boundaries; the person making each decision needs actual remit for that layer
and scope under live governance, regardless of title.

Evidence should identify inputs, source versions, commands, outputs, assumptions, and known limits. Reproducibility lets another person obtain the same calculation; it does not establish that a scientific model is appropriate. Validation checks a specified claim. An independent reviewer compares sources and outputs and records blocking and nonblocking findings before the research coordinator records acceptance or rejection of a bounded task or evidence layer for a stated scope. That acceptance does not authorize new effects or choose scientific method. Separately, the responsible scientific lead decides whether evidence supports a scientific claim or interpretation; task/evidence acceptance does not confer scientific acceptance.

For the [synthetic example](../../examples/repeated_measurements/README.md), the CSV, formula, script, tests, and observed numerical output support a narrow arithmetic claim. They provide no real-data provenance, correlated uncertainty treatment, or scientific acceptance. The [review template](../../templates/review_report.md) keeps executor claims apart from review evidence. Tracked mutation, production, publication, merge, and cleanup each have separate live authorization boundaries in [AGENTS.md](../../AGENTS.md).

The [lifecycle scenario](../tutorials/05_review_and_accept_returned_evidence.md) adds an instructive partial finding: the arithmetic was valid, while the first interpretation note lacked provenance. The note was repaired without repeating the calculation. In the simulated research coordinator role, task/evidence acceptance then covered the bounded arithmetic record only; it did not adopt a scientific model. This is why continuation must name closure and an invalidation boundary rather than assuming all prior live state persists.
