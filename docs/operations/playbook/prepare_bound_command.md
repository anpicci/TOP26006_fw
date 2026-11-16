# Prepare a command from qualified references

This missing cross-source recipe connects the workbook to an existing native
procedure. It produces a reviewable command and its input/output binding in
the existing run report. It does not execute that command or replace a validated
production handoff. Inputs are the task's objective, exact effects, profile,
selected reference and current native procedure; output is a bound proposal or
an explicit unresolved dependent use.

1. Enter through the [membership index](../index.md). Select the collection
   matching the requested scientific use; follow its catalogue source and
   material revisions. Do not select solely by timestamp or path.
2. Resolve the native repository/cwd and original artifact locator with the
   task's preflighted profile. Read the actual native manifest/receipt, preserving
   its identity separately from its path and the qualification being reused.
   If inaccessible, record the exact failed locator and local access limit.
3. Compare scientific stage, selection/normalization, data/blinding, binning,
   WC/other-WC and nuisance treatment with the consumer's request. Same bytes
   do not settle this comparison. Follow [lessons](../workbook/knowledge/operational_lessons.md)
   and any later scope-specific supersession or held handoff.
4. Follow the [goal's single native procedure](index.md). Verify its actual
   maintained parser/entry point; replace historical bindings, not science.
   Resolve all variables and input/plan/output identities before presenting a
   runnable command. Check exact output collision and existing-state semantics.
5. Record cwd, wrapper/interpreter where applicable, exact argv, input/source
   revisions, intended outputs, conditions and permission boundary in the run
   report. A production command remains unexecuted without its own effects and
   mode; a dry-run can itself require a higher ceiling than static preparation.
   Existing output or ambiguous prior outcome calls for authorized readback,
   not automatic overwrite, resume, retry or a fresh-root workaround.

## Worked preparation: BTV plot plan

Goal: prepare the existing qualified BTV plan's no-production preview, without
selecting a new population or launching it. Bind `workspace_root` and TOPEFT
through the profile. Bind the plan to `pkl_btv`'s revision-1 original, whose
digest is in the catalogue; bind the root/tag to `btv_plot_plan`, not an older
reference10 or blocked BTV draft. From the TOPEFT root, the native argument
pattern is:

```bash
./analysis/topeft_run2/run_plotter.sh   --campaign-profile sr_datacard_run2_run3   --campaign-tag top26006-l13-btv-ref-261105-001-261112-001   -o "$topeft_root/histos/TOP26006_BTV_SR_RECO_REFERENCE_261105_001_261112_001"   --plan "$workspace_root/reports/diagnostics/TOP26006_LANE13_BTV_PLAN_AND_MANUAL_HANDOFF_20261114_R1/btv_reference_plan_revision_1.json"   --dry-run --backend condor --resource-observer cgroup_v2   --hard-limit-bytes 245000000000
```

This is a preparation pattern with explicit variables, not a self-contained
dispatch or fresh validation. The consumer must resolve those variables, verify
source identity, maintained flags and actual root collision before recording
its concrete proposal. Use the configured wrapper/interpreter for Python and
wrapper bootstrap. The prior native dry-run and manual handoff are qualified
in `btv_plot_plan`; they are reused evidence, not a new execution here.
Do not remove `--dry-run`, add `--execute`, follow a monitor, or reuse an occupied
root without separately authorized production/lifecycle effects and preflight.
For the old reference10 handoff, step3 instead finds the later 071 hold and
returns the fit-membership boundary; this BTV pattern does not release it.
