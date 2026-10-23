"""Independent arithmetic and input checks for the synthetic teaching example."""

import importlib.util
import math
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("repeated_measurements", ROOT / "analyze.py")
ANALYSIS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ANALYSIS)


class AnalysisTests(unittest.TestCase):
    def test_fixed_dataset_against_independent_equal_weight_arithmetic(self):
        rows = ANALYSIS.read_measurements(ROOT / "data" / "measurements.csv")
        count, mean, standard_error, chi_square, dof = ANALYSIS.summarize(rows)
        values = [10.1, 9.9, 10.3, 9.8, 10.2]
        expected_mean = sum(values) / len(values)
        expected_chi_square = sum((value - expected_mean) ** 2 for value in values) / 0.2 ** 2
        self.assertEqual((count, dof), (5, 4))
        self.assertTrue(math.isclose(mean, expected_mean, abs_tol=1e-12))
        self.assertTrue(math.isclose(standard_error, 0.2 / math.sqrt(5), abs_tol=1e-12))
        self.assertTrue(math.isclose(chi_square, expected_chi_square, abs_tol=1e-12))
        self.assertTrue(math.isclose(chi_square / dof, 1.075, abs_tol=1e-12))

    def test_invalid_headers_and_uncertainties(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.csv"
            path.write_text("id,value,uncertainty\nm1,1,0.2\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "headers"):
                ANALYSIS.read_measurements(path)
            path.write_text("measurement_id,value,uncertainty\nm1,1,0\nm2,2,0.2\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "positive"):
                ANALYSIS.read_measurements(path)


if __name__ == "__main__":
    unittest.main()
