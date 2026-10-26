# Synthetic repeated measurements

**Purpose:** a small teaching example, not TOP-26-006 scientific data or an accepted result.

**Research question:** What single calibration quantity summarizes five repeated synthetic measurements, given their stated statistical uncertainties?

**Provenance:** `data/measurements.csv` is a local, deliberately synthetic CSV fixed for this tutorial. Each row has an ID, value, and one-standard-deviation uncertainty. No instrument or institution produced these numbers.

**Method:** assume independent Gaussian statistical errors and one common quantity. For uncertainty σᵢ, weight each value by 1/σᵢ². Divide the weighted sum by total weight. The standard error is √(1/Σwᵢ). Sum ((value − fitted mean)/σᵢ)² for chi-square; fitting one mean leaves N−1 degrees of freedom.

From the coordination checkout, use the Python interpreter selected for your local wrapper:

```sh
"$wrap" "$python_env" examples/repeated_measurements/analyze.py
"$wrap" "$python_env" -m unittest discover -s examples/repeated_measurements -p test_analysis.py
```

The output gives a weighted mean, its model-based standard error, chi-square, degrees of freedom, and chi-square per degree of freedom. These are descriptive calculations. They establish no goodness-of-fit probability or scientific acceptance.

The companion [repeated-measurements notebook](repeated_measurements.ipynb) imports `read_measurements` and `summarize` from the maintained `analyze.py`; it does not implement another estimator. Open it from this directory with an already-prepared notebook tool so `analyze` and `data/measurements.csv` resolve. The notebook stores no executed outputs and has not been execution- or render-qualified by this documentation example. The script and its focused test remain the checkable calculation authority.

**Limitations:** correlated systematics, model choice, outlier treatment, and real experimental provenance are outside this teaching example. A real analysis needs its own data authority, uncertainty model, validation, and independent scientific review.
