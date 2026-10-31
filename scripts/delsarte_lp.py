"""Delsarte LP discovery and exact integer certificate construction (exploratory).

SciPy HiGHS is used only from sweep scripts. Replay uses stdlib checkers in tools/.
"""

from __future__ import annotations

from fractions import Fraction
from functools import reduce
import sys
from math import gcd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.check_bound import krawtchouk  # noqa: E402


def krawtchouk_at_zero(n: int, q: int, degree: int) -> int:
    return krawtchouk(n, q, degree, 0)


def evaluate_polynomial(n: int, q: int, coeffs: list[int], x: int) -> int:
    return sum(a * krawtchouk(n, q, j, x) for j, a in enumerate(coeffs))


def gauss_rational(matrix: list[list[Fraction]], rhs: list[Fraction]) -> list[Fraction] | None:
    size = len(matrix)
    m = [row[:] for row in matrix]
    b = rhs[:]
    for col in range(size):
        pivot = next((row for row in range(col, size) if m[row][col] != 0), None)
        if pivot is None:
            return None
        m[col], m[pivot] = m[pivot], m[col]
        b[col], b[pivot] = b[pivot], b[col]
        pv = m[col][col]
        m[col] = [value / pv for value in m[col]]
        b[col] /= pv
        for row in range(size):
            if row == col:
                continue
            factor = m[row][col]
            if factor == 0:
                continue
            m[row] = [m[row][index] - factor * m[col][index] for index in range(size)]
            b[row] -= factor * b[col]
    return b


def trim_trailing_zeros(coeffs: list[int]) -> list[int]:
    while len(coeffs) > 1 and coeffs[-1] == 0:
        coeffs.pop()
    return coeffs


def fractions_to_positive_ints(values: list[Fraction]) -> list[int] | None:
    scale = 1
    for value in values:
        scale = scale * value.denominator // gcd(scale, value.denominator)
    ints = [int(value * scale) for value in values]
    common = reduce(gcd, (abs(value) for value in ints if value), 0) or 1
    ints = [value // common for value in ints]
    if ints[0] <= 0 or any(value < 0 for value in ints):
        return None
    return ints


def normalized_lp(n: int, q: int, excluded_distance: int):
    """Minimize 1+sum g_j subject to 1+sum g_j K_j(i)/K_j(0) <= 0 for i>=d."""
    from scipy.optimize import linprog
    import numpy as np

    k0 = [krawtchouk_at_zero(n, q, j) for j in range(n + 1)]
    rows = []
    for i in range(excluded_distance, n + 1):
        rows.append([krawtchouk(n, q, j, i) / k0[j] for j in range(n + 1)])
    if not rows:
        return False, None, None, "no constraints"
    result = linprog(
        np.ones(n + 1),
        A_ub=np.array(rows, dtype=float),
        b_ub=-np.ones(len(rows)),
        bounds=[(0.0, None)] * (n + 1),
        method="highs",
    )
    if not result.success:
        return False, None, None, result.message
    objective = 1.0 + float(result.x.sum())
    return True, objective, result.x, result.message


def exact_coefficients_from_lp(
    n: int,
    q: int,
    excluded_distance: int,
    g,
    tolerance: float = 1e-3,
) -> list[int] | None:
    """Build integer Krawtchouk coefficients from a normalized LP optimum."""
    k0 = [krawtchouk_at_zero(n, q, j) for j in range(n + 1)]
    active = [j for j, value in enumerate(g) if value > 1e-5]
    if not active:
        return None
    max_degree = max(active)
    contacts = []
    for i in range(excluded_distance, n + 1):
        slack = 1.0 + sum(g[j] * krawtchouk(n, q, j, i) / k0[j] for j in range(n + 1))
        if abs(slack) <= tolerance:
            contacts.append(i)
    if len(contacts) < max_degree:
        return None
    contacts = contacts[:max_degree]
    unknowns = list(range(max_degree + 1))
    equations = [
        [Fraction(krawtchouk(n, q, j, i)) for j in unknowns]
        for i in contacts
    ]
    anchor = [[Fraction(1 if j == max_degree else 0) for j in unknowns]]
    rhs = [Fraction(0)] * len(contacts) + [Fraction(1)]
    solution = gauss_rational(equations + anchor, rhs)
    if solution is None:
        return None
    ints = fractions_to_positive_ints(solution)
    if ints is None:
        return None
    ints = trim_trailing_zeros(ints)
    for x in range(excluded_distance, n + 1):
        if evaluate_polynomial(n, q, ints, x) > 0:
            return None
    return ints


def build_certificate_record(
    q: int,
    n: int,
    k: int,
    excluded_distance: int,
    coeffs: list[int],
    cert_id: str,
) -> dict:
    bound = Fraction(evaluate_polynomial(n, q, coeffs, 0), coeffs[0])
    return {
        "id": cert_id,
        "q": q,
        "n": n,
        "k": k,
        "excluded_distance": excluded_distance,
        "krawtchouk_coefficients": coeffs,
        "size_bound": f"{bound.numerator}/{bound.denominator}",
    }


def try_exclude(q: int, n: int, k: int, excluded_distance: int) -> tuple[str, dict | None, str]:
    code_size = q**k
    ok, objective, g, message = normalized_lp(n, q, excluded_distance)
    if not ok or g is None or objective is None:
        return "lp_failed", None, message or "solver failed"
    if objective >= code_size:
        return "lp_feasible_code", None, f"objective {objective} >= {code_size}"

    coeffs = exact_coefficients_from_lp(n, q, excluded_distance, g)
    if coeffs is None:
        return "lp_hit_no_exact_cert", None, f"objective {objective} but exact cert failed"

    record = build_certificate_record(
        q,
        n,
        k,
        excluded_distance,
        coeffs,
        f"gf{q}-n{n}-k{k}-exclude-d{excluded_distance}",
    )
    declared = Fraction(record["size_bound"])
    if declared >= code_size:
        return "cert_too_weak", None, f"exact bound {declared} >= {code_size}"
    return "certified", record, f"LP objective {objective}; size_bound {record['size_bound']}"


def run_checkers(certificate_path: Path) -> tuple[int, str, str]:
    import subprocess

    cmd1 = [sys.executable, str(ROOT / "tools" / "check_bound.py"), str(certificate_path)]
    cmd2 = [sys.executable, str(ROOT / "tools" / "check_bound_independent.py"), str(certificate_path)]
    first = subprocess.run(cmd1, capture_output=True, text=True, check=False)
    second = subprocess.run(cmd2, capture_output=True, text=True, check=False)
    output = first.stdout + first.stderr + second.stdout + second.stderr
    code = 0 if first.returncode == 0 and second.returncode == 0 else 1
    return code, first.stdout.strip(), second.stdout.strip()


if __name__ == "__main__":
    status, record, detail = try_exclude(7, 55, 10, 40)
    print(status, detail)
    if record:
        print(record["krawtchouk_coefficients"])
