# Evidence, reproducibility, and acceptance

Evidence should identify inputs, source versions, commands, outputs, assumptions, and known limits. Reproducibility lets another person obtain the same calculation; it does not establish that a scientific model is appropriate. Validation checks a specified claim. An independent reviewer compares sources and outputs and records blocking and nonblocking findings before a human owner accepts or rejects a result.

For the [synthetic example](../../examples/repeated_measurements/README.md), the CSV, formula, script, tests, and observed numerical output support a narrow arithmetic claim. They provide no real-data provenance, correlated uncertainty treatment, or scientific acceptance. The [review template](../../templates/review_report.md) keeps executor claims apart from review evidence. Tracked mutation, production, publication, merge, and cleanup each have separate live authorization boundaries in [AGENTS.md](../../AGENTS.md).
