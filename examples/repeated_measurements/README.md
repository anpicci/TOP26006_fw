# Synthetic repeated measurements

This small teaching example asks: what common value summarizes five repeated
synthetic measurements, given their stated statistical uncertainties?
The numbers are deliberately invented; no instrument or institution produced them.
They are not TOP-26-006 scientific data or an accepted result.

## Inputs and maintained calculation

[data/measurements.csv](data/measurements.csv) contains five rows, each with an
identifier, value and one-standard-deviation uncertainty. Treat it as read-only
input. [analyze.py](analyze.py) contains the maintained parser and calculation:
`read_measurements` reads and checks the CSV, and `summarize` calculates the
summary. The script also prints the command-line summary. The notebook calls
these functions rather than duplicating the parser or estimator.
The existing `test_analysis.py` provides focused tests of the script.

The five measurements are assumed to estimate a single common value, with
independent Gaussian statistical errors. Values are weighted by inverse
variance. The script returns the count, weighted mean, standard error,
chi-square and degrees of freedom; it also displays chi-square per degree of
freedom. The standard error follows from the stated uncertainty model, and
chi-square measures residual variation relative to the stated uncertainties.
The ratio is not a goodness-of-fit probability or a scientific acceptance decision.

## Run the script

Use the project's prepared Python environment for the tutorial. With `wrap` and
`python_env` already configured, run from the repository root:

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
If a file is missing or you see a `measurement error`, check the working
directory and input. Do not change the data to match the reference values.

## Use the interactive companion

The existing [repeated_measurements.ipynb](repeated_measurements.ipynb) guides you
through input inspection, checking which source and data files it uses,
interpretation, a checkpoint and an in-memory reflection exercise. This example
pairs a tutorial task with a nearby README and a companion notebook for
interactive exploration. The calculation remains in the script.

Open the notebook in a Jupyter application configured to use that environment
as its Python kernel. The supported working directories are the repository root
and `examples/repeated_measurements/`. The setup checks these two contexts and
displays the exact source and data paths. If you launch it elsewhere, a message
explains where to reopen it.

Restart the kernel, then run all cells from the beginning.
Read each explanation before its code and check the displayed paths. If a name
is undefined, restart and run all in order; if setup reports a directory error,
reopen from a supported directory. If that environment is unavailable as a
kernel, ask whoever maintains your local setup. Do not install software during
this task.

The notebook is stored in the repository with empty outputs and null execution
counts, so opening the file is not evidence that it ran. Execution displays local
outputs; close without saving them into the repository. The notebook reads the
source and data files and keeps the exercise in memory. Restarting the kernel
discards those variables. The notebook and script should agree at the script's
six-decimal precision; if they differ, stop and record the file paths and results.

## Interpret the result and continue

Matching the reference values reproduces the tutorial example. Reading the
notebook code shows that it uses the script's functions. A successful run does
not establish that the method is appropriate for real data or that a real
scientific analysis is correct. Correlated systematics, model choice, outlier
treatment and the origin of real experimental data remain outside this example.
Real work needs an identified, trustworthy data source, an appropriate uncertainty
model, validation and independent scientific review.

Return to [Tutorial 3](../../docs/tutorials/03_complete_a_first_read_only_task.md)
to turn your observations into a checkable account, or browse the
[manual](../../docs/index.md).
