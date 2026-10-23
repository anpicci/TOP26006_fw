# Observed synthetic lifecycle (one local diagnostic run)

This is a compact, human-readable record of one diagnostics-local run. New
scratch Git histories will have different commit IDs. The full command and
output receipt is in the local Prompt-003 diagnostics package, not required for
using this teaching fixture.

| Observation | Recorded value |
| --- | --- |
| Analysis seed HEAD | `803b07b22f32fb813257adbe9f74890fb31c7e3c` |
| Methods seed HEAD | `1a1dd41611f4e475570017081e505b20dd4849db` |
| CSV SHA-256 | `f6b9311f0ce6e675999c5ef31a14d82589179a9f8e82be917df6695c6893c294` |
| Analysis command | configured wrapper and Python interpreter running `analyze.py` |
| Output | five measurements; weighted mean `10.060000`; model-based standard error `0.089443`; chi-square `4.300000`; four degrees of freedom; chi-square/dof `1.075000` |
| First bounded note HEAD | `eb40d2703e74350e09e00c459459d706bbc8fa74`; changed path `interpretation.md` only |
| Review finding | arithmetic agrees with observed output; note omitted source commit and CSV hash, blocking note acceptance but preserving arithmetic evidence |
| Provenance repair HEAD | `c9f7c6b9e090fdc3ae3c29b34171cf3a7cb88ff4`; numerical run was not repeated |
| Methods evidence HEAD | `09a97e3ced516e662a8e448f01b9199805c3ea80`; separate scratch Git history, `methods_note.md` only |
| Intentional stop | expected and observed analysis HEAD were the provenance repair HEAD; status was ` M interpretation.md`; diff added `unexpected local edit after accepted commit`; no retry or cleanup |

The review and owner roles were simulated within this one-executor diagnostic
run. The review exercise qualified only the synthetic arithmetic under the
stated independent Gaussian model; its illustrative owner decision accepted
that bounded record after provenance repair. No separate human scientific
review or acceptance was performed. This is a teaching decision in scratch
repositories; it establishes no real-data result or project child-repository
authority. A successor would need the source identity, input hash, assumptions,
review, acceptance scope, residual dirty-state decision, and checks not to
repeat. See the [fixture README](README.md).
