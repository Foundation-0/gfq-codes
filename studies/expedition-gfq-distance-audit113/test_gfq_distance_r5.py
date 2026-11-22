"""Assertion-free R5 adversarial & mutation-killing test suite for AUDIT-113."""
from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from fractions import Fraction
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import gfq_distance_audit as audit
import gfq_distance_oracle as oracle
from gfq_distance_oracle import (
    GFQ_CODES_MAIN_SHA,
    PINNED_GF7_DELSARTE_CERTS,
    PINNED_GFQ_CODES_OPEN_PRS,
    PINNED_MATH0_PR4_CODES,
    GaloisField,
    GfqCertError,
    build_zimmermann_chain,
    canonical_json_bytes,
    canonical_sha256,
    check_field_axioms,
    exact_weight_distribution,
    frac_str,
    hamming_generator,
    hamming_weight,
    is_strict_int,
    krawtchouk_exact,
    linear_combine,
    macwilliams_holds,
    matrix_rank,
    naive_disjoint_enum_count,
    parse_matrix_canonical,
    parse_rational_str,
    reject_invalid_json_types,
    require_hex,
    require_int,
    row_space_contains,
    rref,
    shorten_code,
    strict_typed_equal,
    ternary_golay_generator,
    validate_certificate,
    validate_matrix,
    verify_codeword_certificate,
    verify_delsarte_certificate,
    verify_macwilliams_identity,
    zimmermann_min_distance,
)


def _resign_cert(cert: dict) -> dict:
    c = copy.deepcopy(cert)
    c["payload_sha256"] = canonical_sha256(c["payload"])
    body = {k: v for k, v in c.items() if k != "certificate_sha256"}
    c["certificate_sha256"] = canonical_sha256(body)
    return c


def _make_synthetic_intake_blobs() -> dict[str, bytes]:
    tool1 = b"tool1-body\n"
    tool2 = b"tool2-body\n"
    h1 = hashlib.sha256(tool1).hexdigest()
    h2 = hashlib.sha256(tool2).hexdigest()
    prs = [
        {"number": p["number"], "state": "OPEN", "headRefOid": p["head_prefix"] + "a" * 32}
        for p in PINNED_GFQ_CODES_OPEN_PRS
    ] + [{"number": 8, "state": "MERGED", "headRefOid": "b" * 40}, "non_dict_entry"]
    issues = (
        [{"number": i, "state": "OPEN"} for i in range(1, 6)]
        + [{"number": 6, "state": "CLOSED"}, "non_dict_issue"]
    )
    return {
        "gfq_codes_head.json": json.dumps({"sha": GFQ_CODES_MAIN_SHA}).encode("utf-8"),
        "gfq_codes_prs.json": json.dumps(prs).encode("utf-8"),
        "gfq_codes_issues.json": json.dumps(issues).encode("utf-8"),
        "gfq_codes/tools/check_bound.py": tool1,
        "gfq_codes/tools/check_bound_independent.py": tool2,
        "gfq_codes/tools/SHA256SUMS": (
            f"{h1}  tools/check_bound.py\n{h2}  tools/check_bound_independent.py\n"
        ).encode("utf-8"),
        "gfq_codes/results/gf7-upper-bounds/certificate.json": json.dumps(
            {"format_version": 1, "certificates": PINNED_GF7_DELSARTE_CERTS}
        ).encode("utf-8"),
    }


class TestAudit113StrictTypesAndFields(unittest.TestCase):
    def test_strict_types_hex_json_rational_and_equality(self) -> None:
        self.assertTrue(is_strict_int(0))
        self.assertFalse(is_strict_int(True))
        self.assertFalse(is_strict_int(1.0))

        self.assertEqual(require_int(5, "x", lo=5, hi=5), 5)
        for bad in (True, False, 1.5, "5"):
            with self.assertRaises(GfqCertError):
                require_int(bad, "x")
        with self.assertRaises(GfqCertError):
            require_int(4, "x", lo=5)
        with self.assertRaises(GfqCertError):
            require_int(6, "x", hi=5)

        good_hex = "a" * 40
        self.assertEqual(require_hex(good_hex, 40, "h"), good_hex)
        for bad_hex in (123, "a" * 39, "A" * 40, "g" * 40, "0" * 40, "0" * 64):
            with self.assertRaises(GfqCertError):
                require_hex(bad_hex, 40, "h")

        reject_invalid_json_types({"a": [1, True, None, "ok", {"b": 0}]})
        for bad_obj in (1.5, 1j, (1, 2), {1, 2}, b"abc", {1: "a"}, [{"k": 2.0}]):
            with self.assertRaises(GfqCertError):
                canonical_json_bytes(bad_obj)

        sample = {"13": 16, "8": 16, "nested": [True, 1, "x"]}
        rt = json.loads(canonical_json_bytes(sample).decode("utf-8"))
        self.assertEqual(canonical_sha256(sample), canonical_sha256(rt))

        self.assertTrue(strict_typed_equal({"a": [1, True]}, {"a": [1, True]}))
        self.assertFalse(strict_typed_equal(True, 1))
        self.assertFalse(strict_typed_equal({"a": 1}, {"b": 1}))
        self.assertFalse(strict_typed_equal([1, 2], [1]))
        self.assertFalse(strict_typed_equal([1, 2], [1, 3]))

        self.assertEqual(parse_rational_str("0", "r"), Fraction(0, 1))
        self.assertEqual(parse_rational_str("-7", "r"), Fraction(-7, 1))
        self.assertEqual(parse_rational_str("317755831120/1357", "r"), Fraction(317755831120, 1357))
        self.assertEqual(frac_str(Fraction(10, 4)), "5/2")
        for bad_r in (123, "01", "2/4", "3/0", "1.5", "-0", "1/-2", ""):
            with self.assertRaises(GfqCertError):
                parse_rational_str(bad_r, "r")

    def test_galois_fields_conway_axioms_and_errors(self) -> None:
        p1 = oracle.certify_pillar1_fields()
        self.assertEqual(len(p1["fields"]), 7)
        for rec in p1["fields"]:
            self.assertTrue(rec["axioms_verified"])
        c = p1["gf9_conway_contrast"]
        self.assertEqual(c["conway_modulus"], [2, 2, 1])
        self.assertEqual(c["conway_x_squared"], 4)
        self.assertEqual(c["math0_x_squared"], 2)
        self.assertEqual(c["conway_x_order"], 8)
        self.assertEqual(c["math0_x_order"], 4)
        self.assertEqual(c["add_table_mismatches"], 0)
        self.assertEqual(c["mul_table_mismatches"], 36)

        F9 = GaloisField(9)
        self.assertEqual(F9.sub(4, 3), 1)
        self.assertEqual(F9.div(4, 3), 3)
        self.assertEqual(F9.pow(3, 0), 1)
        self.assertEqual(F9.pow(3, 8), 1)
        self.assertEqual(F9.pow(3, 3), F9.mul(F9.mul(3, 3), 3))

        # Test every branch of check_field_axioms with targeted broken tables on GF(3).
        def broken_gf3(patch_fn) -> GaloisField:
            f = GaloisField(3)
            patch_fn(f)
            return f

        def _set_cell(tbl, r, col, val):
            rows = [list(x) for x in tbl]
            rows[r][col] = val
            return tuple(tuple(x) for x in rows)

        self.assertTrue(check_field_axioms(GaloisField(3)))
        # 1. add(a,0) != a
        self.assertIn("add_identity", oracle.field_axiom_violations(broken_gf3(lambda f: setattr(f, "_add", _set_cell(f._add, 1, 0, 2)))))
        # 2. mul(a,1) != a
        self.assertIn("mul_identity", oracle.field_axiom_violations(broken_gf3(lambda f: setattr(f, "_mul", _set_cell(f._mul, 2, 1, 1)))))
        # 3. add(a, neg(a)) != 0
        self.assertIn("add_inverse", oracle.field_axiom_violations(broken_gf3(lambda f: setattr(f, "_neg", (0, 1, 2)))))
        # 4. mul(a, inv(a)) != 1
        self.assertIn("mul_inverse", oracle.field_axiom_violations(broken_gf3(lambda f: setattr(f, "_inv", (0, 1, 1)))))
        # 5. non-commutative add
        self.assertIn("add_comm", oracle.field_axiom_violations(broken_gf3(lambda f: setattr(f, "_add", _set_cell(f._add, 1, 2, 1)))))
        # 6. non-commutative mul
        f5_nc = GaloisField(5)
        f5_nc._mul = _set_cell(f5_nc._mul, 2, 4, 1)
        self.assertIn("mul_comm", oracle.field_axiom_violations(f5_nc))
        # 7. non-associative commutative add
        f3_na = GaloisField(3)
        f3_na._add = _set_cell(f3_na._add, 1, 1, 0)
        self.assertIn("add_assoc", oracle.field_axiom_violations(f3_na))
        # 8. non-associative commutative mul
        f5_nm = GaloisField(5)
        f5_nm._mul = _set_cell(f5_nm._mul, 2, 2, 3)
        self.assertIn("mul_assoc", oracle.field_axiom_violations(f5_nm))
        # 9. non-distributive (swap 2 <-> 4 in GF(5)*: isomorphic comm/assoc group, breaks a*(b+c)!)
        perm = {0: 0, 1: 1, 2: 4, 3: 3, 4: 2}
        f5_nd = GaloisField(5)
        f5_nd._mul = tuple(
            tuple(perm[f5_nd._mul[perm[a]][perm[b]]] for b in range(5)) for a in range(5)
        )
        f5_nd._inv = (0,) + tuple(next(b for b in range(5) if f5_nd._mul[a][b] == 1) for a in range(1, 5))
        self.assertEqual(oracle.field_axiom_violations(f5_nd), ["distributive"])
        self.assertFalse(check_field_axioms(f5_nd))

        for bad_q in (0, 1, 6, 10, 11, True):
            with self.assertRaises(GfqCertError):
                GaloisField(bad_q)
        with self.assertRaises(GfqCertError):
            GaloisField(3, modulus=(1, 1))
        for bad_mod in ([1, 1], "bad"):
            with self.assertRaisesRegex(GfqCertError, "modulus must have length"):
                GaloisField(9, modulus=bad_mod)
        # [2, 0, 2] has NO root in GF(3) (vals: 2, 1, 1), so ONLY the monic check catches it!
        with self.assertRaisesRegex(GfqCertError, "must be monic"):
            GaloisField(9, modulus=[2, 0, 2])
        for bad_mod in ([0, 0, 1], [1, 2, 1]):
            with self.assertRaisesRegex(GfqCertError, "has root"):
                GaloisField(9, modulus=bad_mod)
        with self.assertRaises(GfqCertError):
            GaloisField(9, modulus=[True, 1, 1])
        for bad_el in (True, False, -1, 9, 1.0):
            with self.assertRaises(GfqCertError):
                F9.add(bad_el, 1)
        with self.assertRaises(GfqCertError):
            F9.inv(0)
        with self.assertRaises(GfqCertError):
            F9.mult_order(0)
        with self.assertRaises(GfqCertError):
            F9.pow(3, -1)

    def test_linear_algebra_edges(self) -> None:
        F3 = GaloisField(3)
        self.assertEqual(validate_matrix([[1, 2], [0, 1]], F3), (2, 2))
        for bad_m in ([], [[]], ([1, 2],), ["bad_row"]):
            with self.assertRaisesRegex(GfqCertError, "non-empty list of non-empty rows"):
                validate_matrix(bad_m, F3)
        for bad_m in ([[1, 2], [1]], [[1, 2], "ab"]):
            with self.assertRaisesRegex(GfqCertError, "uniform length"):
                validate_matrix(bad_m, F3)
        for bad_m in ([[1, 3]], [[True, 0]]):
            with self.assertRaises(GfqCertError):
                validate_matrix(bad_m, F3)

        for bad_ord in ((0, 1), [False, True], [0, 0], [0, 1, 0]):
            with self.assertRaisesRegex(GfqCertError, "col_order must be a permutation"):
                rref([[1, 0], [0, 1]], F3, col_order=bad_ord)

        with self.assertRaisesRegex(GfqCertError, "vector length mismatch"):
            row_space_contains([[1, 0]], F3, [1, 0, 0])
        with self.assertRaisesRegex(GfqCertError, "vector length mismatch"):
            row_space_contains([[1, 0]], F3, "10")

        self.assertTrue(verify_codeword_certificate([[1, 1, 0]], F3, [2, 2, 0], 2))
        self.assertTrue(verify_codeword_certificate([[1, 0]], F3, [0, 0], 0))
        self.assertFalse(verify_codeword_certificate([[1, 1, 0]], F3, [1, 0, 1], 2))
        self.assertFalse(verify_codeword_certificate([[1, 1, 0]], F3, [2, 2, 0], 1))
        for bad_w in (True, False, -1, 1.0):
            with self.assertRaises(GfqCertError):
                verify_codeword_certificate([[1, 0]], F3, [1, 0], expected_weight=bad_w)

        with self.assertRaises(GfqCertError):
            linear_combine([[1, 0]], [1, 2], F3)
        self.assertEqual(linear_combine([[1, 2], [0, 1]], [2, 0], F3), [2, 1])
        self.assertEqual(hamming_weight([0, 2, 0, 1]), 2)

        for bad_coords in ([], [3], [-1], [0, 0], [True], [0, 1, 2]):
            with self.assertRaisesRegex(GfqCertError, "invalid shortening coordinates"):
                shorten_code([[1, 0, 1]], F3, bad_coords)
        with self.assertRaisesRegex(GfqCertError, "zero-rank"):
            shorten_code([[0, 0]], F3, [0])
        self.assertEqual(shorten_code([[1, 0]], F3, [0]), [])


class TestAudit113ZimmermannDualityGoppaAndParser(unittest.TestCase):
    def test_zimmermann_controls_budget_and_dominance(self) -> None:
        F3 = GaloisField(3)
        golay = ternary_golay_generator(False)
        zg = zimmermann_min_distance(golay, F3, max_enum=72)
        self.assertTrue(zg["complete"])
        self.assertEqual(zg["d"], 5)
        self.assertEqual(zg["relative_ranks"], [6, 5])
        self.assertEqual(zg["done_s"], [2, 2])
        self.assertEqual(zg["enumerated"], 72)
        self.assertEqual(naive_disjoint_enum_count(zg["relative_ranks"], 6, 3, 5), 236)

        # Exact boundary max_enum=71 must return incomplete!
        z_b71 = zimmermann_min_distance(golay, F3, max_enum=71)
        self.assertFalse(z_b71["complete"])
        self.assertIsNone(z_b71["d"])
        self.assertLess(z_b71["lower_bound"], z_b71["upper_bound"])
        self.assertTrue(z_b71["certificate_verified"])

        # Zero-column code exercises `if not new_pivots: break`.
        G_zcol = [[1, 0, 0], [0, 1, 0]]
        k_z, ch_z = build_zimmermann_chain(G_zcol, F3)
        self.assertEqual(k_z, 2)
        self.assertEqual([item[2] for item in ch_z], [2])
        self.assertEqual(zimmermann_min_distance(G_zcol, F3)["d"], 1)

        # 3 disjoint info sets and weight-3 row -> 0 enumerations!
        zr = zimmermann_min_distance([[1, 1, 1]], F3)
        self.assertEqual(zr["d"], 3)
        self.assertEqual(zr["enumerated"], 0)

        with self.assertRaisesRegex(GfqCertError, "rank-0"):
            zimmermann_min_distance([[0, 0, 0]], F3)
        with self.assertRaises(GfqCertError):
            zimmermann_min_distance(golay, F3, max_enum=-1)
        with self.assertRaises(GfqCertError):
            naive_disjoint_enum_count([3, 2], 4, 3, 3)
        self.assertEqual(naive_disjoint_enum_count([0, 1], 1, 2, 1), 0)
        for bad_nargs in (
            ((1,), 1, 3, 1),
            ([True], 1, 3, 1),
            ([-1, 1], 1, 3, 1),
            ([2, 1], 1, 3, 1),
            ([1], True, 3, 1),
            ([1], 0, 3, 1),
            ([1], 1, True, 1),
            ([1], 1, 1, 1),
            ([1], 1, 3, True),
            ([1], 1, 3, 0),
        ):
            with self.assertRaises(GfqCertError):
                naive_disjoint_enum_count(*bad_nargs)
        with self.assertRaises(GfqCertError):
            hamming_generator(F3, 1)

        F4 = GaloisField(4)
        h4_2 = hamming_generator(F4, 2)
        zh = zimmermann_min_distance(h4_2, F4)
        dh = exact_weight_distribution(h4_2, F4)
        self.assertEqual(zh["d"], 3)
        self.assertEqual(min(int(w) for w in dh if int(w) > 0), 3)

    def test_macwilliams_and_delsarte_edge_rejections(self) -> None:
        F3 = GaloisField(3)
        mw = verify_macwilliams_identity(ternary_golay_generator(False), F3)
        self.assertTrue(mw["macwilliams_all_j_exact"])
        self.assertEqual(mw["primal_d"], 5)
        self.assertEqual(mw["dual_d"], 6)
        tampered_dual = dict(mw["dual_weight_distribution"])
        tampered_dual["6"] = 131
        self.assertFalse(macwilliams_holds(mw["primal_weight_distribution"], tampered_dual, 11, 3, 6))
        self.assertEqual(krawtchouk_exact(5, 3, 0, 2), 1)
        self.assertEqual(krawtchouk_exact(5, 3, 1, 0), 10)
        self.assertEqual(krawtchouk_exact(5, 3, 5, 5), -1)
        for bad_kargs in (
            (True, 3, 0, 0),
            (5, 1, 0, 0),
            (5, 3, -1, 0),
            (5, 3, 0, -1),
            (5, 3, 6, 0),
            (5, 3, 0, 6),
        ):
            with self.assertRaises(GfqCertError):
                krawtchouk_exact(*bad_kargs)
        self.assertTrue(macwilliams_holds({"0": 1, "1": 0, "2": 1}, {"0": 1, "2": 1}, 2, 2, 1))
        for bad_mw in (
            ({"0": 1}, {"0": 1}, 0, 3, 0),
            ("not_dict", {"0": 1}, 2, 2, 1),
            ({"0": 1}, [], 2, 2, 1),
            ({0: 1}, {"0": 1}, 2, 2, 1),
            ({"01": 1}, {"0": 1}, 2, 2, 1),
            ({"0": 1, "2": 1}, {"0": 1, "2": 1, "99": 1000, "garbage": -5}, 2, 2, 1),
            ({"0": True, "2": True}, {"0": True, "2": True}, 2, 2, 1),
            ({"0": 1, "3": 1}, {"0": 1}, 2, 2, 1),
            ({"0": 1, "2": 1}, {"0": 1, "3": 0}, 2, 2, 1),
            ({"0": -1}, {"0": 1}, 2, 2, 1),
        ):
            with self.assertRaises(GfqCertError):
                macwilliams_holds(*bad_mw)
        with self.assertRaises(GfqCertError):
            ternary_golay_generator(extended=1)

        base = copy.deepcopy(PINNED_GF7_DELSARTE_CERTS[0])
        res = verify_delsarte_certificate(base)
        self.assertEqual(res["strict_integer_slack"], 173086535880720)

        # Exact slack == 0 boundary (f(0)/a_0 == 4 == 2^2): must be rejected!
        eq_slack_cert = {
            "id": "exact-tie",
            "q": 2, "n": 3, "k": 2, "excluded_distance": 2,
            "krawtchouk_coefficients": [1, 1], "size_bound": "4/1",
        }
        with self.assertRaisesRegex(GfqCertError, "strict inequality failed"):
            verify_delsarte_certificate(eq_slack_cert)

        # Zero a_0 with zero tail (so ONLY a[0] <= 0 catches it!)
        with self.assertRaisesRegex(GfqCertError, "a_0 must be strictly positive"):
            verify_delsarte_certificate({
                "id": "zero-a0", "q": 2, "n": 3, "k": 2, "excluded_distance": 2,
                "krawtchouk_coefficients": [0], "size_bound": "0",
            })
        for bad_cid in (123, "   "):
            with self.assertRaisesRegex(GfqCertError, "invalid certificate id"):
                verify_delsarte_certificate({**base, "id": bad_cid})
        for bad_c in ("not_list", [], [1] * 57):
            with self.assertRaisesRegex(GfqCertError, "invalid krawtchouk_coefficients"):
                verify_delsarte_certificate({**base, "krawtchouk_coefficients": bad_c})
        for bad in (
            "not_dict",
            {k: v for k, v in base.items() if k != "id"},
            {**base, "q": 1},
            {**base, "n": 0},
            {**base, "k": 56},
            {**base, "excluded_distance": 0},
            {**base, "krawtchouk_coefficients": [1, -1]},
            {**base, "excluded_distance": 39},
            {**base, "size_bound": "1/1"},
            {**base, "k": 1},
        ):
            with self.assertRaises(GfqCertError):
                verify_delsarte_certificate(bad)

    def test_goppa_shortening_and_canonical_parser_edges(self) -> None:
        p3 = oracle.certify_pillar3_goppa_and_parser()
        self.assertEqual(p3["binary_goppa_24_5_3"]["d"], 7)
        self.assertEqual(p3["binary_goppa_24_5_3"]["weight_7_codewords"], 13)
        self.assertEqual(p3["primal_shortened_21_6_7"]["k"], 6)
        self.assertEqual(p3["primal_shortened_21_6_7"]["d"], 7)
        self.assertEqual(p3["primal_shortened_21_6_7"]["weight_7_codewords"], 6)
        self.assertTrue(p3["primal_shortened_21_6_7"]["distance_monotone_ge_parent"])
        self.assertTrue(p3["primal_shortened_21_6_7"]["all_shortened_rows_in_parent"])
        pw = p3["canonical_parser_witnesses"]
        self.assertEqual(pw["bracketed_2x2_gf3_rank"], 2)
        self.assertEqual(pw["gf4_3x3_rank"], 3)
        self.assertEqual(pw["compact_single_row_len"], 5)
        self.assertEqual(pw["gf5_kn_header_rows"], 2)
        self.assertEqual(pw["gf3_qkn_header_rows"], 2)
        self.assertIn("line 1", pw["bad_line_error_message"])
        self.assertIn("a b c d", pw["bad_line_error_message"])
        self.assertNotIn("0 1 2 0", pw["bad_line_error_message"])

        with self.assertRaises(GfqCertError):
            oracle._gf32_inv(0)

        F3 = GaloisField(3)
        F5 = GaloisField(5)
        # Bracket on left ONLY (kills Or 0) and right ONLY (kills Or 1),
        # with entries outside GF(3)? No: in GF(5), "[2 3\n1 0 1\n0 1 2\n" has 2 toks != width2=3
        # so ONLY has_brackets stops it from being skipped as a k,n header!
        with self.assertRaisesRegex(GfqCertError, "uniform length"):
            parse_matrix_canonical("[2 3\n1 0 1\n0 1 2\n", F5)
        with self.assertRaisesRegex(GfqCertError, "uniform length"):
            parse_matrix_canonical("2 3]\n1 0 1\n0 1 2\n", F5)

        # idx == 0 guard: header-like line on row 2 (rem_rows=2, width2=3) MUST NOT be skipped!
        with self.assertRaisesRegex(GfqCertError, "strict element"):
            parse_matrix_canonical("1 0 2\n3 2 3\n0 1 1\n", F3)
        # len(toks) == 4 must not be treated as header; wrong rem_rows or wrong width2 must not be header!
        with self.assertRaisesRegex(GfqCertError, "strict element"):
            parse_matrix_canonical("3 9 3\n1 0 2\n0 1 1\n", F3)
        with self.assertRaisesRegex(GfqCertError, "strict element"):
            parse_matrix_canonical("3 2 9\n1 0 2\n0 1 1\n", F3)
        with self.assertRaisesRegex(GfqCertError, "strict element"):
            parse_matrix_canonical("9 3\n1 0 2\n0 1 1\n", F5)
        with self.assertRaisesRegex(GfqCertError, "strict element"):
            parse_matrix_canonical("2 9\n1 0 2\n0 1 1\n", F5)
        with self.assertRaisesRegex(GfqCertError, "uniform length"):
            parse_matrix_canonical("1 2 3 4\n1 0 2\n0 1 1\n", F5)
        with self.assertRaisesRegex(GfqCertError, "uniform length"):
            parse_matrix_canonical("2 3 0 0\n1 0 2\n0 1 1\n", F5)
        # Single-line 2-token non-row (len(entries)==1) must not trigger header branch:
        with self.assertRaisesRegex(GfqCertError, "strict element"):
            parse_matrix_canonical("3 2 3\n", F3)

        self.assertEqual(parse_matrix_canonical("[]\n, ,\n# comment\n1 0 2;\n", F3), [[1, 0, 2]])
        self.assertEqual(parse_matrix_canonical("3 2 3\n102\n011\n", F3), [[1, 0, 2], [0, 1, 1]])
        with self.assertRaisesRegex(GfqCertError, "no matrix data found"):
            parse_matrix_canonical("   \n# only comments\n", F3)
        for bad_txt in (
            123,
            "4 2 3\n1 0 2\n0 1 1\n",
            "a b\n1 0\n",
            "1 0\n1 0 2\n",
            "105\n",
            "1 5\n",
            "[1,2],[0,1]\n",
            "[1,2],0,1\n",
            "1,2,[0,1]\n",
            "1_0 2\n",
            "+1 2\n",
            "\uff11 2\n",
            "2_0 3\n1 0 1\n0 1 2\n",
        ):
            with self.assertRaises(GfqCertError):
                parse_matrix_canonical(bad_txt, F3)


class TestAudit113CLIAndCertificateForgeries(unittest.TestCase):
    def test_pillar2_mismatch_and_live_blob_parser_guards(self) -> None:
        # Exercise Pillar 2 validation errors on bad math0_matrices (wrong count, n, k, d) & gf7_certs.
        with self.assertRaises(GfqCertError):
            oracle.certify_pillar2_zimmermann_and_duality(math0_matrices=[])
        with self.assertRaises(GfqCertError):
            oracle.certify_pillar2_zimmermann_and_duality(gf7_certs=[])

        good_15 = [
            (q, n, k, d, fn, sha, [[int(ch) for ch in row] for row in rows])
            for q, n, k, d, fn, _, sha, rows in PINNED_MATH0_PR4_CODES
        ]
        # Replace item 0 with wrong expected n, k, and d (small 1x1 matrix is instant!)
        for bad_tuple in (
            (3, 99, 1, 1, "q3_bad.txt", "a" * 64, [[1]]),
            (3, 1, 99, 1, "q3_bad.txt", "a" * 64, [[1]]),
            (3, 1, 1, 99, "q3_bad.txt", "a" * 64, [[1]]),
        ):
            bad_15 = [bad_tuple] + good_15[1:]
            with self.assertRaisesRegex(GfqCertError, "verification mismatch"):
                oracle.certify_pillar2_zimmermann_and_duality(math0_matrices=bad_15)

        # Synthetic self-contained live blob parser tests (works in isolated mutate tempdirs!)
        blobs = _make_synthetic_intake_blobs()
        open_prs, open_issues, certs = audit.parse_live_intake_blobs(blobs)
        self.assertEqual(len(open_prs), 6)
        self.assertEqual(open_issues, 5)
        self.assertEqual(len(certs), 4)

        def _mut_blobs(key: str, val: bytes) -> dict[str, bytes]:
            b = dict(blobs)
            b[key] = val
            return b

        # Exact 8-char headRefOid boundary must be accepted!
        prs_exact8 = [
            {"number": p["number"], "state": "OPEN", "headRefOid": p["head_prefix"]}
            for p in PINNED_GFQ_CODES_OPEN_PRS
        ]
        self.assertEqual(len(audit.parse_live_intake_blobs(_mut_blobs("gfq_codes_prs.json", json.dumps(prs_exact8).encode()))[0]), 6)

        # Exercise every single guard and BoolOp clause in parse_live_intake_blobs!
        for key, val, pat in (
            ("gfq_codes_head.json", b"[]", "SHA mismatch"),
            ("gfq_codes_head.json", json.dumps({"sha": "f" * 40}).encode(), "SHA mismatch"),
            ("gfq_codes_prs.json", b"{}", "must be list"),
            ("gfq_codes_prs.json", json.dumps([{"state": "OPEN"}]).encode(), "malformed open PR"),
            ("gfq_codes_prs.json", json.dumps([{"number": True, "state": "OPEN", "headRefOid": "a" * 40}]).encode(), "malformed open PR"),
            ("gfq_codes_prs.json", json.dumps([{"number": 9, "state": "OPEN", "headRefOid": None}]).encode(), "malformed open PR"),
            ("gfq_codes_prs.json", json.dumps([{"number": 9, "state": "OPEN", "headRefOid": "1234567"}]).encode(), "malformed open PR"),
            ("gfq_codes_prs.json", json.dumps([{"number": 9, "state": "OPEN", "headRefOid": "a" * 40}]).encode(), "open PR list mismatch"),
            ("gfq_codes_issues.json", b"{}", "must be list"),
            ("gfq_codes_issues.json", json.dumps([{"number": 1, "state": "OPEN"}]).encode(), "expected 5 open issues"),
            ("gfq_codes/tools/SHA256SUMS", b"\xff\xfe", "invalid UTF-8"),
            ("gfq_codes/tools/SHA256SUMS", b"only_one_line\n", "entry count"),
            ("gfq_codes/tools/SHA256SUMS", b"bad line with three tokens\nsecond line\n", "malformed SHA256SUMS"),
            ("gfq_codes/tools/SHA256SUMS", f"{'a'*64}  tools/missing.py\n{'a'*64}  tools/missing2.py\n".encode(), "verification failed"),
            ("gfq_codes/tools/SHA256SUMS", f"{'a'*64}  tools/check_bound.py\n{'a'*64}  tools/check_bound_independent.py\n".encode(), "verification failed"),
            ("gfq_codes/results/gf7-upper-bounds/certificate.json", b"[]", "malformed GF\\(7\\)"),
            ("gfq_codes/results/gf7-upper-bounds/certificate.json", json.dumps({"format_version": 2, "certificates": []}).encode(), "malformed GF\\(7\\)"),
            ("gfq_codes/results/gf7-upper-bounds/certificate.json", json.dumps({"format_version": 1, "certificates": {}}).encode(), "malformed GF\\(7\\)"),
        ):
            with self.assertRaisesRegex(GfqCertError, pat):
                audit.parse_live_intake_blobs(_mut_blobs(key, val))

    def test_standalone_live_check_and_forged_certificates(self) -> None:
        cert_s = audit.run_standalone_audit()
        self.assertEqual(cert_s["execution_mode"], "standalone_pinned_manifest")
        self.assertFalse(cert_s["live_portal_verified"])
        rt_s = json.loads(canonical_json_bytes(cert_s).decode("utf-8"))
        self.assertEqual(validate_certificate(rt_s)["certificate_sha256"], cert_s["certificate_sha256"])

        p2 = cert_s["payload"]["pillar_2_zimmermann_and_duality"]
        self.assertEqual(p2["classical_controls"]["ternary_golay_11_6_5"]["d"], 5)
        self.assertEqual(p2["classical_controls"]["ternary_golay_ext_12_6_6"]["d"], 6)
        self.assertEqual(p2["classical_controls"]["hamming_gf4_21_18_3"]["d"], 3)
        self.assertEqual(p2["math0_pr4_15_codes"]["losses_vs_naive"], 0)
        self.assertTrue(p2["gfq_codes_gf7_delsarte"]["negative_control_rejected"])

        intake_dir = _HERE.parent / "intake-gfq-codes"
        cert_file = _HERE / "gfq_distance_certificate.json"
        if intake_dir.is_dir() and cert_file.is_file():
            cert_l = audit.run_live_audit(intake_dir)
            self.assertEqual(cert_l["payload_sha256"], cert_s["payload_sha256"])
            self.assertTrue(cert_l["live_portal_verified"])
            chk = audit.check_certificate_file(cert_file)
            self.assertEqual(chk["certificate_sha256"], cert_l["certificate_sha256"])

        with self.assertRaises(GfqCertError):
            oracle.assemble_certificate("bad_mode", False, cert_s["portal_manifest"], cert_s["payload"])
        with self.assertRaises(GfqCertError):
            oracle.assemble_certificate("standalone_pinned_manifest", 0, cert_s["portal_manifest"], cert_s["payload"])
        with self.assertRaises(GfqCertError):
            oracle.assemble_certificate("standalone_pinned_manifest", True, cert_s["portal_manifest"], cert_s["payload"])

        with self.assertRaisesRegex(GfqCertError, "top-level key mismatch"):
            validate_certificate({**cert_s, "extra": 1})
        with self.assertRaisesRegex(GfqCertError, "payload_sha256 mismatch"):
            validate_certificate({**cert_s, "payload_sha256": "a" * 64})
        with self.assertRaisesRegex(GfqCertError, "invalid execution_mode or live_portal_verified"):
            validate_certificate(_resign_cert({**cert_s, "live_portal_verified": 0}))

        forged_probes = [
            "not_dict",
            _resign_cert({**cert_s, "schema": "wrong/1"}),
            _resign_cert({**cert_s, "execution_mode": "unknown"}),
            _resign_cert({**cert_s, "live_portal_verified": True}),
            {**cert_s, "certificate_sha256": "b" * 64},
            _resign_cert({**cert_s, "portal_manifest": "not_dict"}),
            _resign_cert({**cert_s, "portal_manifest": {"bad": 1}}),
        ]
        tampered_payload = copy.deepcopy(cert_s)
        tampered_payload["payload"]["pillar_2_zimmermann_and_duality"]["classical_controls"]["ternary_golay_11_6_5"]["d"] = 6
        forged_probes.append(_resign_cert(tampered_payload))

        for mutate_fn in (
            lambda m: m.__setitem__("gfq_codes_main_sha", "0" * 40),
            lambda m: m.__setitem__("gfq_codes_main_sha", "f" * 40),
            lambda m: m.__setitem__("pinned_files", "bad"),
            lambda m: m["pinned_files"].__setitem__(next(iter(m["pinned_files"])), "not_dict"),
            lambda m: m["pinned_files"].__setitem__(next(iter(m["pinned_files"])), {"bytes": 1}),
        ):
            tc = copy.deepcopy(cert_s)
            mutate_fn(tc["portal_manifest"])
            forged_probes.append(_resign_cert(tc))

        for probe in forged_probes:
            with self.assertRaises(GfqCertError):
                validate_certificate(probe)

    def test_cli_flags_and_safe_file_guards(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tpath = Path(tmp)
            sub_root = tpath / "intake"
            sub_root.mkdir()
            out_cert = tpath / "standalone_cert.json"

            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = audit.main(["--standalone", "--output", str(out_cert), "--json"])
            self.assertEqual(rc, 0)
            self.assertEqual(json.loads(buf.getvalue())["execution_mode"], "standalone_pinned_manifest")

            # Verify compact canonical JSON (with and without trailing newline) is accepted!
            compact_bytes = canonical_json_bytes(json.loads(out_cert.read_text(encoding="utf-8")))
            compact_cert = tpath / "compact_cert.json"
            compact_cert.write_bytes(compact_bytes)
            self.assertTrue(audit.check_certificate_file(compact_cert)["ok"])
            compact_nl_cert = tpath / "compact_nl_cert.json"
            compact_nl_cert.write_bytes(compact_bytes + b"\n")
            self.assertTrue(audit.check_certificate_file(compact_nl_cert)["ok"])

            buf2 = io.StringIO()
            with redirect_stdout(buf2):
                rc2 = audit.main(["--check", str(out_cert)])
            self.assertEqual(rc2, 0)
            self.assertIn("OK AUDIT-113", buf2.getvalue())

            buf3 = io.StringIO()
            with redirect_stdout(buf3):
                rc3 = audit.main(["--check", str(out_cert), "--json"])
            self.assertEqual(rc3, 0)
            self.assertTrue(json.loads(buf3.getvalue())["ok"])

            non_canon = tpath / "non_canon.json"
            non_canon.write_text(out_cert.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            with self.assertRaisesRegex(GfqCertError, "not canonically formatted"):
                audit.check_certificate_file(non_canon)

            float_json = tpath / "float.json"
            float_json.write_text('{"x": 1.5}', encoding="utf-8")
            with self.assertRaises(GfqCertError):
                audit.check_certificate_file(float_json)

            bad_json = tpath / "bad.json"
            bad_json.write_text("{not json", encoding="utf-8")
            with self.assertRaises(GfqCertError):
                audit.check_certificate_file(bad_json)

            # Missing cert file (kills Or 0) and symlink cert file (kills Or 1)
            with self.assertRaisesRegex(GfqCertError, "invalid certificate path"):
                audit.check_certificate_file(tpath / "missing_cert.json")
            sym_cert = tpath / "sym.json"
            os.symlink(out_cert, sym_cert)
            with self.assertRaisesRegex(GfqCertError, "invalid certificate path"):
                audit.check_certificate_file(sym_cert)

            err_buf = io.StringIO()
            with redirect_stderr(err_buf):
                self.assertEqual(audit.main(["--live"]), 1)
                self.assertEqual(audit.main(["--standalone", "--intake-dir", str(sub_root)]), 1)
            self.assertIn("ERROR:", err_buf.getvalue())

            # Test _safe_read_pinned_file valid read + every unshadowed failure guard!
            payload_b = b"hello"
            payload_h = hashlib.sha256(payload_b).hexdigest()
            real_f = sub_root / "a.txt"
            real_f.write_bytes(payload_b)
            self.assertEqual(audit._safe_read_pinned_file(sub_root, "a.txt", 5, payload_h), payload_b)

            # Symlink pointing to valid file with exact length & hash (ONLY is_symlink catches it!)
            sym_f = sub_root / "link.txt"
            os.symlink(real_f, sym_f)
            with self.assertRaisesRegex(GfqCertError, "refusing symlink"):
                audit._safe_read_pinned_file(sub_root, "link.txt", 5, payload_h)

            # Intermediate symlinked parent directory (catches component-wise traversal!)
            real_sub = sub_root / "real_sub"
            real_sub.mkdir()
            (real_sub / "a.txt").write_bytes(payload_b)
            sym_sub = sub_root / "sym_sub"
            os.symlink(real_sub, sym_sub)
            with self.assertRaisesRegex(GfqCertError, "refusing symlink"):
                audit._safe_read_pinned_file(sub_root, "sym_sub/a.txt", 5, payload_h)

            # Outside file with exact length & hash (ONLY is_relative_to catches it!)
            outside_f = tpath / "outside.txt"
            outside_f.write_bytes(payload_b)
            with self.assertRaisesRegex(GfqCertError, "path escape"):
                audit._safe_read_pinned_file(sub_root, "../outside.txt", 5, payload_h)

            with self.assertRaisesRegex(GfqCertError, "missing pinned"):
                audit._safe_read_pinned_file(sub_root, "missing.txt", 5, payload_h)
            with self.assertRaisesRegex(GfqCertError, "byte-length mismatch"):
                audit._safe_read_pinned_file(sub_root, "a.txt", 4, payload_h)
            with self.assertRaisesRegex(GfqCertError, "SHA-256 mismatch"):
                audit._safe_read_pinned_file(sub_root, "a.txt", 5, "a" * 64)

            # run_live_audit non-dir (kills Or 0) and symlink-to-dir (kills Or 1)
            with self.assertRaisesRegex(GfqCertError, "invalid intake directory"):
                audit.run_live_audit(tpath / "no_such_dir")
            sym_dir = tpath / "sym_intake"
            os.symlink(sub_root, sym_dir)
            with self.assertRaisesRegex(GfqCertError, "invalid intake directory"):
                audit.run_live_audit(sym_dir)


if __name__ == "__main__":
    unittest.main()
