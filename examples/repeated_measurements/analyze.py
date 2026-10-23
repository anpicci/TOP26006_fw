#!/usr/bin/env python3
"""Summarize synthetic repeated measurements under independent Gaussian errors."""

import argparse
import csv
import math
from pathlib import Path


HEADERS = ["measurement_id", "value", "uncertainty"]


def read_measurements(path):
    with Path(path).open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != HEADERS:
            raise ValueError("expected CSV headers: " + ",".join(HEADERS))
        rows = []
        for line_number, row in enumerate(reader, start=2):
            if None in row or not row["measurement_id"] or any(row[key] is None for key in HEADERS):
                raise ValueError(f"incomplete measurement on line {line_number}")
            try:
                value = float(row["value"])
                uncertainty = float(row["uncertainty"])
            except ValueError as exc:
                raise ValueError(f"non-numeric measurement on line {line_number}") from exc
            if not math.isfinite(value) or not math.isfinite(uncertainty) or uncertainty <= 0:
                raise ValueError(f"value must be finite and uncertainty positive on line {line_number}")
            rows.append((value, uncertainty))
    if len(rows) < 2:
        raise ValueError("at least two measurements are required for chi-square per degree of freedom")
    return rows


def summarize(rows):
    if len(rows) < 2 or any(not math.isfinite(v) or not math.isfinite(s) or s <= 0 for v, s in rows):
        raise ValueError("at least two finite measurements with positive uncertainties are required")
    weights = [1.0 / (uncertainty * uncertainty) for _, uncertainty in rows]
    total_weight = math.fsum(weights)
    mean = math.fsum(value * weight for (value, _), weight in zip(rows, weights)) / total_weight
    standard_error = math.sqrt(1.0 / total_weight)
    chi_square = math.fsum(((value - mean) / uncertainty) ** 2 for value, uncertainty in rows)
    degrees_of_freedom = len(rows) - 1
    return len(rows), mean, standard_error, chi_square, degrees_of_freedom


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", nargs="?", default=Path(__file__).resolve().parent / "data" / "measurements.csv")
    args = parser.parse_args(argv)
    try:
        count, mean, standard_error, chi_square, dof = summarize(read_measurements(args.csv_path))
    except (OSError, ValueError) as exc:
        parser.exit(2, f"measurement error: {exc}\n")
    print("Synthetic repeated measurements")
    print(f"measurements: {count}")
    print(f"weighted mean: {mean:.6f}")
    print(f"standard error: {standard_error:.6f}")
    print(f"chi-square: {chi_square:.6f}")
    print(f"degrees of freedom: {dof}")
    print(f"chi-square / dof: {chi_square / dof:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
