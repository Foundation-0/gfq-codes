"""Corrupted copies of one certificate must be rejected by every checker that tests the broken condition.

Run: python3 -O test_corrupt.py   (also without -O)
"""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CHECKERS = {
    "verify_certs": HERE / "verify_certs.py",
    "verify_binomial": HERE / "verify_binomial.py",
    "delsarte_independent": HERE / "delsarte_independent.py",
    "repository_check_bound": ROOT / "tools" / "check_bound.py",
    "repository_check_bound_independent": ROOT / "tools" / "check_bound_independent.py",
}
ID = "gf7-n55-k10-exclude-d40"


def base_certificate():
    with open(HERE / "certificate.json", encoding="utf-8") as handle:
        for c in json.load(handle)["certificates"]:
            if c["id"] == ID:
                return c
    raise SystemExit("certificate not found")


class CorruptionTests(unittest.TestCase):
    def run_checker(self, name, cert):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "certificate.json"
            path.write_text(json.dumps({"format_version": 1, "certificates": [cert]}), encoding="utf-8")
            return subprocess.run([sys.executable, "-O", str(CHECKERS[name]), str(path)],
                                  capture_output=True, text=True, check=False).returncode

    def rejected_by(self, cert, names):
        for name in names:
            with self.subTest(checker=name):
                self.assertNotEqual(self.run_checker(name, cert), 0)

    def test_original_passes_everywhere(self):
        for name in CHECKERS:
            with self.subTest(checker=name):
                self.assertEqual(self.run_checker(name, base_certificate()), 0)

    def test_negative_coefficient(self):
        c = base_certificate()
        c["krawtchouk_coefficients"][3] = -c["krawtchouk_coefficients"][3]
        self.rejected_by(c, CHECKERS)

    def test_smaller_distance(self):
        c = base_certificate()
        c["excluded_distance"] -= 3
        self.rejected_by(c, CHECKERS)

    def test_smaller_dimension(self):
        c = base_certificate()
        c["k"] = 5
        self.rejected_by(c, CHECKERS)

    def test_halved_coefficient(self):
        c = base_certificate()
        c["krawtchouk_coefficients"][-1] = c["krawtchouk_coefficients"][-1] // 2
        self.rejected_by(c, CHECKERS)

    def test_wrong_declared_bound(self):
        c = copy.deepcopy(base_certificate())
        c["size_bound"] = "1/1"
        # verify_binomial does not compare the declared size_bound; the other four do.
        self.rejected_by(c, [n for n in CHECKERS if n != "verify_binomial"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
