# Tutorial 3: complete a first read-only task

**You are** a researcher trying a small, checkable task, with optional AI assistance.
**You want** to understand how five invented measurements are summarized and
what the result can tell you under a stated model.
**You will use** a local CSV, the maintained Python script, and optionally its
interactive notebook companion. A terminal runs commands; a notebook lets you
inspect the same task one step at a time. Chat can help explain what you see;
Codex can inspect or run the example when you explicitly ask and authorize it.
**You will change** no project files. Your observations can stay in your own
notes outside the repository.
**You will not change** the data, calculation, notebook, environment, or Git state.
**You should finish with** the input and command you used, the calculated values,
the assumptions they depend on, and a short explanation of what remains unproven.

## Prerequisites

Read the [research foundations](../foundations/ai_assisted_research.md) and
[tool-choice guide](../how_to/choose_an_ai_tool_for_a_research_task.md) first if
these roles are unfamiliar. You need a local checkout and the project's prepared
Python environment for this tutorial. For terminal commands, `wrap` and
`python_env` must already identify your command wrapper and Python interpreter;
[Tutorial 1](01_prepare_a_research_project.md) explains that setup. You do not
need a TOPEFT checkout. For the interactive route, use a Jupyter application
configured to use that environment as its Python kernel. If the environment is
unavailable, ask whoever maintains your local setup before continuing.

## 1. Identify the question and inspect the input

Start with: “What common value summarizes these five synthetic measurements,
and what assumptions does that summary require?” Read the
[example README](../../examples/repeated_measurements/README.md), which explains
the method and its limits. In a file viewer, open
[measurements.csv](../../examples/repeated_measurements/data/measurements.csv).
You can also inspect it in a terminal from the repository root:

```sh
cat examples/repeated_measurements/data/measurements.csv
```

Expect a header and five rows, each with an identifier, value and positive
one-standard-deviation uncertainty. Inspecting them first connects the answer
to its input. These numbers were invented for teaching; they are not experimental
evidence. If the file is absent or different, check the checkout and directory
before running anything. Do not replace the input to force an expected answer.

## 2. Reproduce the calculation using either route

Both routes use the same calculation and CSV. The terminal runs `analyze.py` as
a script; the notebook loads that file and calls its functions. Choose the
terminal for one complete summary, or the notebook for a guided inspection.
You may use both to compare their results.

### Terminal route

From the repository root, run this command using that environment:

```sh
"$wrap" "$python_env" examples/repeated_measurements/analyze.py examples/repeated_measurements/data/measurements.csv
```

The script reads and checks the input, then prints the summary. Read
[analyze.py](../../examples/repeated_measurements/analyze.py) alongside the
README to see how it parses the CSV and calculates the summary. To run the
existing focused test as well, use:

```sh
"$wrap" "$python_env" -m unittest discover -s examples/repeated_measurements -p test_analysis.py
```

A `measurement error` means the input could not be read or did not satisfy the
script's checks. A missing command or interpreter means local setup is not ready.
Check the path or ask whoever maintains your local setup; keep the source and
input unchanged. Passing this test provides evidence about the script's behavior
in the tested cases. It does not establish that a broader analysis is correct.

### Interactive route

Open the existing [companion notebook](../../examples/repeated_measurements/repeated_measurements.ipynb)
in your configured Jupyter application and select that Python environment.
Start the application from the repository root or
`examples/repeated_measurements/`; both working directories are supported.
The application may set the working directory to the example directory when
opening the notebook, which is supported too.

Restart the kernel, then run all cells from the beginning. Read the prose before
each code cell: it explains setup, input inspection, the calculation,
and a reflection exercise. The setup displays the paths of the `analyze.py`
and CSV files the notebook uses. Check that these belong to your checkout.
A launch-directory error tells you where to reopen the notebook. An undefined
name usually means a cell was skipped: restart and run all in order. If an import
fails, check the selected environment. Do not repair the script or install
packages as part of this exercise.

The notebook is stored in the repository without outputs. Your application will
display local results during execution; close without saving those outputs into
the repository. The notebook adds teaching steps and questions; both routes use
the calculation in `analyze.py`, without duplicating it in the notebook.

## 3. Interpret and challenge the observation

For the supplied CSV, the script prints:

| Quantity | Value |
|---|---:|
| Measurements | 5 |
| Weighted mean | 10.060000 |
| Standard error | 0.089443 |
| Chi-square | 4.300000 |
| Degrees of freedom | 4 |
| Chi-square / dof | 1.075000 |

The notebook displays the same quantities, possibly with more decimal places.
Compare at the script's six-decimal precision. Agreement shows that the two
routes reproduce this tutorial example. If they disagree, record the input file
path, the command or notebook used, and any error message or differing values in
your notes. Stop before using the result. First check the working directory,
selected kernel and displayed source and data paths.

The five measurements are assumed to estimate a single common value, with
independent Gaussian statistical errors. The weighted mean summarizes them
under those assumptions. The standard error follows from the stated uncertainty
model. Chi-square measures residual variation relative to the stated
uncertainties. The printed ratio is neither a goodness-of-fit probability nor
a scientific acceptance decision. Correlations, outliers and the origin of real
experimental data would require additional scientific choices and evidence.

**Checkpoint:** Can you point to the input and the function that calculates the
mean? Why does matching the reference output leave the suitability of the
uncertainty model unanswered?

**Try it:** predict whether simply reversing the order of the same measurements
should change their summary. The notebook checks that prediction using an
in-memory copy and the same function. Leave the CSV untouched. Explain
what this checks and what it cannot establish about real measurements.

## 4. Use AI assistance and return a checkable account

You can do this task yourself. If you use Codex, give it the question,
these exact example files and permission to inspect them and run only this
small calculation. Ask it to leave files unchanged, avoid network access and
job submission, cite the input and command, and separate observations from
interpretation. The [task-preparation guide](../how_to/ask_an_assistant_to_prepare_a_task.md)
shows how to make that request concrete. Chat can help frame or explain the
question; Codex can inspect and run repository material within the limits you
authorize. Neither tool is required for this task.

Compare the returned account with your observations. Ask a reviewer or colleague
who did not produce the original account to challenge the source, assumptions,
comparison and omissions. An execution report and a review are evidence for your
judgment. You remain responsible for deciding whether the account answers this
synthetic question. A successful run does not establish that the method is
appropriate for real data or that a real scientific analysis is correct.

Finish with a short note naming the CSV and the repository version you used
(for example, the commit, if available), the route and command or notebook you
used, the values observed, and the limits above. Record any discrepancy rather
than guessing its cause. For more on assessing that account, read
[evidence and acceptance](../explanation/evidence_reproducibility_and_acceptance.md),
or return to the [manual](../index.md) to choose your next task.
