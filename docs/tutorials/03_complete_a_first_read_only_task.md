# Tutorial 3: complete a first read-only task

**Learning goal:** ask a bounded question, reproduce evidence, have a separately tasked reviewer assess it, and leave the acceptance decision with the human researcher or scientific owner. The dataset is deliberately synthetic and does not represent real project science.

1. Read the [example's question, method, and limits](../../examples/repeated_measurements/README.md), then inspect the local CSV:

   ```sh
   cat examples/repeated_measurements/data/measurements.csv
   "$wrap" "$python_env" examples/repeated_measurements/analyze.py
   "$wrap" "$python_env" -m unittest discover -s examples/repeated_measurements -p test_analysis.py
   ```

   The validated reference run reports five measurements, weighted mean `10.060000`, standard error `0.089443`, chi-square `4.300000`, four degrees of freedom, and chi-square/dof `1.075000`. These are computed descriptive quantities under the stated independent Gaussian model, not a goodness-of-fit probability or accepted scientific conclusion.

2. Form a first **read-only** research question: “Do the local CSV, formula, and script support the displayed mean, standard error, and chi-square under the stated assumptions?” Use the [research task request](../../templates/research_task_request.md) to name evidence and stop conditions. The [illustrative read-only skeleton](../../templates/read_only_prompt.md) helps a coordinator prepare a dispatch; live [CPC.md](../../CPC.md) supplies mandatory prompt rules. Filling a template does not authorize execution.

3. Ask the coordinator or authorized agent to inspect only this example, reproduce the computation, cite exact inputs and commands, and return discrepancies or uncertainty. The [task preparation how-to](../how_to/ask_an_assistant_to_prepare_a_task.md) shows the handoff. Request no edits, network use, production job, or publication. An AI tool's ability to run a command is not task authorization.

4. Compare the returned report with the CSV, script, and your own calculation. A test result and executor self-report are evidence to review; an independent reviewer checks provenance, assumptions, arithmetic, omissions, and limits. Use the [review report template](../../templates/review_report.md) to separate observations, claims, findings, and decision. The researcher or scientific owner decides acceptance. [Evidence and acceptance](../explanation/evidence_reproducibility_and_acceptance.md) explains why this boundary matters.

**Checkpoint:** you can frame and review one bounded read-only task. Mutation, a real-data method, production, merge, cleanup, publication, and any new scientific conclusion each require a separate decision and applicable live [AGENTS.md](../../AGENTS.md), [CPC.md](../../CPC.md), and native policy.
