"""Independent CLI controls for the exact Delsarte certificate checkers.

The tiny examples here are known bounds, not proposed code-table improvements.
No implementation modules, numerical solvers, or result certificates are used.
"""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CHECKERS = (ROOT / "tools" / "check_bound.py", ROOT / "tools" / "check_bound_independent.py")
TOY = {
    "format_version": 1,
    "certificates": [{
        "id": "known-binary-toy",
        "q": 2,
        "n": 3,
        "k": 3,
        "excluded_distance": 2,
        "krawtchouk_coefficients": [1, 1],
        "size_bound": "4/1",
    }],
}


class BoundCheckerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "certificate.json"

    def run_both(self, expected):
        for checker in CHECKERS:
            with self.subTest(checker=checker.name):
                result = subprocess.run(
                    [sys.executable, str(checker), str(self.path)],
                    capture_output=True, text=True, check=False,
                )
                self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def check(self, document, expected=1):
        self.path.write_text(json.dumps(document), encoding="utf-8")
        self.run_both(expected)

    def changed_record(self, **changes):
        document = copy.deepcopy(TOY)
        document["certificates"][0].update(changes)
        return document

    def test_known_binary_bound(self):
        # K_1(x) = 3 - 2x, so f = 4 - 2x <= 0 for x = 2, 3.
        # The bound 4 < 2^3 excludes dimension 3 and distance >= 2.
        self.check(TOY, 0)

    def test_nonbinary_bound_uses_q_minus_one(self):
        # For q=3 and n=2, f=1+K_1=5-3x, hence A_3(2,2)<=5<9.
        self.check(self.changed_record(q=3, n=2, k=2, size_bound="5/1"), 0)

    def test_equivalent_exact_bound_strings(self):
        for bound in ("4", "8/2"):
            with self.subTest(bound=bound):
                self.check(self.changed_record(size_bound=bound), 0)

    def test_full_degree_and_fractional_bound(self):
        # For binary n=3, f=3+3K_1+K_2+K_3 has f(2)=0, f(3)=-4,
        # f(0)=16 and f_0=3. The exact size bound is 16/3 < 8.
        self.check(self.changed_record(krawtchouk_coefficients=[3, 3, 1, 1], size_bound="16/3"), 0)

    def test_large_integer_scaling_preserves_exact_bound(self):
        scale = 10 ** 30 + 1
        self.check(self.changed_record(
            krawtchouk_coefficients=[3 * scale, 3 * scale, scale, scale],
            size_bound="16/3",
        ), 0)

    def test_constant_polynomial_is_not_a_bound(self):
        self.check(self.changed_record(krawtchouk_coefficients=[1], size_bound="1/1"))

    def test_positive_value_at_first_allowed_distance_is_rejected(self):
        self.check(self.changed_record(excluded_distance=1))

    def test_later_allowed_distances_are_also_checked(self):
        # f=1+K_2 vanishes at x=1,2 but equals 4 at x=3.
        self.check(self.changed_record(excluded_distance=1, krawtchouk_coefficients=[1, 0, 1]))

    def test_equality_does_not_exclude_a_code(self):
        # A binary [3,2,2] parity code exists: a bound of 4 is not < 2^2.
        self.check(self.changed_record(k=2))

    def test_declared_bound_must_equal_computed_bound(self):
        for bound in ("3/1", "5/1", "40000000000000001/10000000000000000"):
            with self.subTest(bound=bound):
                self.check(self.changed_record(size_bound=bound))

    def test_malformed_rationals_are_rejected(self):
        for bound in (None, 4, 4.0, True, "4/0", "four", "-4/1", "4/-1", "NaN", "4.0", " 4", "4e0"):
            with self.subTest(bound=bound):
                self.check(self.changed_record(size_bound=bound))

    def test_coefficients_must_be_nonnegative_integers_with_positive_constant(self):
        for coefficients in ([0, 1], [-1, 1], [1, -1], [True, 1], [1, False], [1, 1.0], [1, "1"]):
            with self.subTest(coefficients=coefficients):
                self.check(self.changed_record(krawtchouk_coefficients=coefficients))

    def test_coefficient_shape_and_degree(self):
        for coefficients in (None, {}, "1,1", [], [1, 1, 0, 0, 0]):
            with self.subTest(coefficients=coefficients):
                self.check(self.changed_record(krawtchouk_coefficients=coefficients))

    def test_all_record_fields_are_required(self):
        for field in TOY["certificates"][0]:
            with self.subTest(field=field):
                document = copy.deepcopy(TOY)
                del document["certificates"][0][field]
                self.check(document)

    def test_parameter_ranges_and_integer_types(self):
        bad_values = {
            "q": (0, 1, -2, True, 2.0, "2", None),
            "n": (0, -1, True, 3.0, "3", None),
            "k": (0, -1, 4, True, 3.0, "3", None),
            "excluded_distance": (0, -1, 4, True, 2.0, "2", None),
        }
        for field, values in bad_values.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    self.check(self.changed_record(**{field: value}))

    def test_identifier_must_be_nonempty_string(self):
        for identifier in (None, "", "  ", 1, True, []):
            with self.subTest(identifier=identifier):
                self.check(self.changed_record(id=identifier))

    def test_invalid_document_shapes_and_versions(self):
        documents = (
            None, [], "text", {},
            {"format_version": 1},
            {"certificates": TOY["certificates"]},
            dict(TOY, certificates=None), dict(TOY, certificates={}),
            dict(TOY, certificates=[]), dict(TOY, certificates=[None]),
            dict(TOY, certificates=[[]]),
        )
        for document in documents:
            with self.subTest(document=document):
                self.check(document)
        for version in (0, 2, True, 1.0, "1", None):
            with self.subTest(version=version):
                self.check(dict(TOY, format_version=version))

    def test_duplicate_identifiers_are_rejected(self):
        self.check(dict(TOY, certificates=TOY["certificates"] * 2))

    def test_every_certificate_is_checked(self):
        second = copy.deepcopy(TOY["certificates"][0])
        second["id"] = "another-known-toy"
        document = dict(TOY, certificates=[TOY["certificates"][0], second])
        self.check(document, 0)
        second["k"] = 2
        self.check(document)

    def test_malformed_json_and_duplicate_keys(self):
        examples = (
            '{"format_version":',
            json.dumps(TOY)[:-1] + ', "format_version": 1}',
            json.dumps(TOY).replace('"q": 2', '"q": 3, "q": 2'),
        )
        for text in examples:
            with self.subTest(text=text):
                self.path.write_text(text, encoding="utf-8")
                self.run_both(1)

    def test_nonstandard_json_numbers_are_rejected(self):
        for constant in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(constant=constant):
                self.path.write_text(json.dumps(TOY)[:-1] + ', "extra": ' + constant + '}', encoding="utf-8")
                self.run_both(1)

    def test_invalid_utf8_and_file_errors(self):
        self.run_both(1)  # File does not exist yet.
        self.path.write_bytes(b'\xff')
        self.run_both(1)
        self.path.unlink()
        self.path.mkdir()
        self.run_both(1)


if __name__ == "__main__":
    unittest.main()
