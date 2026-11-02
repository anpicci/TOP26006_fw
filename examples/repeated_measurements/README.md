# Synthetic repeated measurements

This small teaching example asks: what common calibration quantity summarizes
five repeated synthetic measurements, given their stated statistical uncertainties?
The numbers are deliberately invented; no instrument or institution produced them.
They are not TOP-26-006 scientific data or an accepted result.

## Inputs and maintained calculation

[data/measurements.csv](data/measurements.csv) contains five identifiers, values,
and one-standard-deviation uncertainties. Treat it as read-only input.
[analyze.py](analyze.py) owns CSV parsing and validation in `read_measurements`,
and the calculation in `summarize`. It also provides the command-line summary.
The notebook calls these functions rather than maintaining another parser or
estimator. The existing `test_analysis.py` supplies focused checks of the script.

The model assumes independent Gaussian statistical errors and one common value.
Values are weighted by inverse variance. The script returns the count, weighted
mean, model-based standard error, chi-square and degrees of freedom; its display
also reports chi-square per degree of freedom. These are descriptive calculations,
not a goodness-of-fit probability or scientific acceptance.

## Run the ordinary script

Use the project's prepared Python environment for the tutorial. With your
already-configured `wrap` and `python_env`, run from the repository root:

```sh
"$wrap" "$python_env" examples/repeated_measurements/analyze.py examples/repeated_measurements/data/measurements.csv
"$wrap" "$python_env" -m unittest discover -s examples/repeated_measurements -p test_analysis.py
```

From this example directory, the equivalent analysis command is:

```sh
"$wrap" "$python_env" analyze.py data/measurements.csv
```

If those environment variables are unfamiliar, follow the prerequisites in
[Tutorial 3](../../docs/tutorials/03_complete_a_first_read_only_task.md).
For this input, the script prints mean `10.060000`, standard error `0.089443`,
chi-square `4.300000`, four degrees of freedom and chi-square/dof `1.075000`.
A missing file or `measurement error` calls for checking the directory and input,
without changing them to match the reference.

## Use the interactive companion

The existing [repeated_measurements.ipynb](repeated_measurements.ipynb) adds a
guided input inspection, visible source binding, interpretation, a checkpoint
and an in-memory reflection exercise. The pattern is one tutorial task, a nearby
README, and a companion notebook when interactivity helps; ordinary maintained
source continues to own the calculation.

Open the notebook in an already-prepared Jupyter tool, selecting the project's
prepared Python environment for the tutorial. The supported kernel working
directories are the repository root and `examples/repeated_measurements/`.
Setup checks these two contexts and displays the exact source and data paths.
Other directories produce a message telling you where to launch it.

Start with a clean kernel: restart it and run all cells from the beginning.
Read each explanation before its code and check the displayed paths. If a name
is undefined, restart and run all in order; if setup reports a directory error,
reopen from a supported directory. Ask your installation maintainer about a
missing prepared kernel instead of installing software during this task.

Tracked notebook outputs and execution counts are intentionally cleared, so
opening the file is not evidence that it ran. Execution displays local outputs;
close without saving them into the repository. Normal execution reads the
maintained files and keeps the exercise in memory. Restarting discards those
variables. The notebook and script should agree at the script's six-decimal
precision; a mismatch is a reason to stop and record the evidence.

## Interpret the result and continue

Successful execution validates the tutorial example and its source reuse. It
does not validate a broader scientific analysis. Correlated systematics, model
choice, outlier treatment and real experimental provenance remain outside this
example. Real work needs its own data authority, uncertainty model, validation
and independent scientific review.

Return to [Tutorial 3](../../docs/tutorials/03_complete_a_first_read_only_task.md)
to turn your observations into a checkable account, or browse the
[manual](../../docs/index.md).
