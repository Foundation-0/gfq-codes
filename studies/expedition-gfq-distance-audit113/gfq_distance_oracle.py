"""Pure-Z/F_q/Q independent exact linear-code distance certifier (AUDIT-113).

Zero floats, zero NumPy, zero bare asserts, zero shared code with math0#3/#4
or Foundation-0/gfq-codes tools. Implements:
  - Pillar 1: Conway-canonical finite fields GF(q) for q in {2,3,4,5,7,8,9}
    (including GF(9) = F_3[x]/(x^2+2x+2)) and strict Gauss-Jordan RREF.
  - Pillar 2: Full lazy incremental Zimmermann relative-rank minimum-distance
    certification (Checker #2), all 15/15 math0#4 best codes, exact
    MacWilliams duality, and independent pure-Z/Q Delsarte LP verification of
    Foundation-0/gfq-codes's four GF(7) upper-bound certificates.
  - Pillar 3: Law-5 bridge to AUDIT-109's F_{2^5} binary Goppa (24,5,3,9)
    code with exact primal-shortening distance monotonicity, plus an
    unambiguous canonical matrix parser closing all math0#3/#4 parser bugs.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from fractions import Fraction
from itertools import combinations, product
from typing import Any


class GfqCertError(ValueError):
    """Domain error raised on any invalid input, type violation, or check failure."""


SUPPORTED_Q: tuple[int, ...] = (2, 3, 4, 5, 7, 8, 9)
PRIME_Q: frozenset[int] = frozenset({2, 3, 5, 7})
CONWAY_MODULI: dict[int, tuple[int, tuple[int, ...]]] = {
    4: (2, (1, 1, 1)),      # x^2 + x + 1 over GF(2)
    8: (2, (1, 1, 0, 1)),   # x^3 + x + 1 over GF(2)
    9: (3, (2, 2, 1)),      # x^2 + 2x + 2 over GF(3) (Conway / Magma / GAP / Sage / gfq-codes)
}
NON_CONWAY_GF9_MODULUS: tuple[int, ...] = (1, 0, 1)  # x^2 + 1 (math0#3)

_HEX_RE = re.compile(r"^[0-9a-f]+$")
_RATIONAL_RE = re.compile(r"^(0|-?[1-9][0-9]*)(?:/([1-9][0-9]*))?$")
_CANON_UINT_RE = re.compile(r"^(0|[1-9][0-9]*)$")
_UINT_TOK_RE = re.compile(r"^[0-9]+$")
_COMPACT_RE = re.compile(r"^[0-9]{2,}$")
_SEP_RE = re.compile(r"[\s,]+")


# ---------------------------------------------------------------------------
# Strict typing, canonical JSON (str keys only), and rational parsing
# ---------------------------------------------------------------------------

def is_strict_int(value: Any) -> bool:
    return type(value) is int


def require_int(value: Any, name: str, lo: int | None = None, hi: int | None = None) -> int:
    if type(value) is not int:
        raise GfqCertError(f"{name} must be strict int, got {type(value).__name__}")
    if lo is not None and value < lo:
        raise GfqCertError(f"{name}={value} < {lo}")
    if hi is not None and value > hi:
        raise GfqCertError(f"{name}={value} > {hi}")
    return value


def require_hex(value: Any, length: int, name: str) -> str:
    if type(value) is not str:
        raise GfqCertError(f"{name} must be str")
    if len(value) != length or not _HEX_RE.fullmatch(value):
        raise GfqCertError(f"{name} must be {length} lowercase hex chars")
    if value == "0" * length:
        raise GfqCertError(f"{name} must not be all-zero")
    return value


def reject_invalid_json_types(obj: Any, path: str = "$") -> None:
    if obj is None or type(obj) in (bool, int, str):
        return
    if type(obj) is list:
        for idx, item in enumerate(obj):
            reject_invalid_json_types(item, f"{path}[{idx}]")
        return
    if type(obj) is dict:
        for k, v in obj.items():
            if type(k) is not str:
                raise GfqCertError(f"non-str dict key at {path}: {type(k).__name__}")
            reject_invalid_json_types(v, f"{path}.{k}")
        return
    raise GfqCertError(f"disallowed JSON type at {path}: {type(obj).__name__}")


def canonical_json_bytes(obj: Any) -> bytes:
    reject_invalid_json_types(obj)
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def canonical_sha256(obj: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(obj)).hexdigest()


def strict_typed_equal(a: Any, b: Any) -> bool:
    if type(a) is not type(b):
        return False
    if type(a) is dict:
        if a.keys() != b.keys():
            return False
        return all(strict_typed_equal(a[k], b[k]) for k in a)
    if type(a) is list:
        if len(a) != len(b):
            return False
        return all(strict_typed_equal(x, y) for x, y in zip(a, b))
    return a == b


def frac_str(f: Fraction) -> str:
    return f"{f.numerator}/{f.denominator}"


def parse_rational_str(text: Any, name: str) -> Fraction:
    if type(text) is not str:
        raise GfqCertError(f"{name} must be rational string")
    m = _RATIONAL_RE.fullmatch(text)
    if m is None:
        raise GfqCertError(f"{name} invalid rational string: {text!r}")
    num = int(m.group(1))
    den = int(m.group(2)) if m.group(2) is not None else 1
    if math.gcd(abs(num), den) != 1:
        raise GfqCertError(f"{name} not in lowest terms: {text!r}")
    return Fraction(num, den)


# ---------------------------------------------------------------------------
# Pillar 1: Exact Conway-canonical finite fields GF(q) & strict linear algebra
# ---------------------------------------------------------------------------

def _to_digits(code: int, p: int, m: int) -> list[int]:
    out: list[int] = []
    cur = code
    for _ in range(m):
        out.append(cur % p)
        cur //= p
    return out


def _from_digits(digits: list[int], p: int) -> int:
    acc = 0
    for d in reversed(digits):
        acc = acc * p + (d % p)
    return acc


class GaloisField:
    """Finite field GF(q) for q in {2,3,4,5,7,8,9} with strict int enforcement."""

    def __init__(self, q: int, modulus: tuple[int, ...] | list[int] | None = None):
        require_int(q, "q")
        if q in PRIME_Q:
            if modulus is not None:
                raise GfqCertError(f"prime field GF({q}) does not take a modulus")
            self.q = q
            self.p = q
            self.m = 1
            self.modulus: tuple[int, ...] | None = None
        elif q in CONWAY_MODULI:
            p, default_mod = CONWAY_MODULI[q]
            self.q = q
            self.p = p
            self.m = len(default_mod) - 1
            if modulus is None:
                mod_tup = default_mod
            else:
                if not isinstance(modulus, (list, tuple)) or len(modulus) != self.m + 1:
                    raise GfqCertError(f"GF({q}) modulus must have length {self.m + 1}")
                mod_list = [require_int(c, "modulus coeff", 0, p - 1) for c in modulus]
                if mod_list[-1] != 1:
                    raise GfqCertError(f"GF({q}) modulus must be monic")
                for root in range(p):
                    val = 0
                    pwr = 1
                    for c in mod_list:
                        val = (val + c * pwr) % p
                        pwr = (pwr * root) % p
                    if val == 0:
                        raise GfqCertError(f"GF({q}) modulus {mod_list} has root {root} in GF({p})")
                mod_tup = tuple(mod_list)
            self.modulus = mod_tup
        else:
            raise GfqCertError(f"unsupported field order q={q}; supported={SUPPORTED_Q}")

        self._add = tuple(tuple(self._raw_add(a, b) for b in range(q)) for a in range(q))
        self._mul = tuple(tuple(self._raw_mul(a, b) for b in range(q)) for a in range(q))
        self._neg = tuple(next(b for b in range(q) if self._add[a][b] == 0) for a in range(q))
        self._inv = (0,) + tuple(next(b for b in range(q) if self._mul[a][b] == 1) for a in range(1, q))

    def _raw_add(self, a: int, b: int) -> int:
        if self.m == 1:
            return (a + b) % self.p
        da = _to_digits(a, self.p, self.m)
        db = _to_digits(b, self.p, self.m)
        return _from_digits([(x + y) % self.p for x, y in zip(da, db)], self.p)

    def _raw_mul(self, a: int, b: int) -> int:
        if self.m == 1:
            return (a * b) % self.p
        p = self.p
        mod = self.modulus
        da = _to_digits(a, p, self.m)
        db = _to_digits(b, p, self.m)
        prod = [0] * (2 * self.m - 1)
        for i, x in enumerate(da):
            for j, y in enumerate(db):
                prod[i + j] = (prod[i + j] + x * y) % p
        for deg in range(len(prod) - 1, self.m - 1, -1):
            lead = prod[deg] % p
            if lead != 0:
                shift = deg - self.m
                for j in range(self.m + 1):
                    prod[shift + j] = (prod[shift + j] - lead * mod[j]) % p
        return _from_digits(prod[: self.m], p)

    def check(self, a: int) -> int:
        if type(a) is not int or not (0 <= a < self.q):
            raise GfqCertError(f"{a!r} is not a strict element of GF({self.q})")
        return a

    def add(self, a: int, b: int) -> int:
        return self._add[self.check(a)][self.check(b)]

    def sub(self, a: int, b: int) -> int:
        return self._add[self.check(a)][self._neg[self.check(b)]]

    def neg(self, a: int) -> int:
        return self._neg[self.check(a)]

    def mul(self, a: int, b: int) -> int:
        return self._mul[self.check(a)][self.check(b)]

    def inv(self, a: int) -> int:
        self.check(a)
        if a == 0:
            raise GfqCertError("zero has no multiplicative inverse")
        return self._inv[a]

    def div(self, a: int, b: int) -> int:
        return self.mul(a, self.inv(b))

    def pow(self, a: int, exp: int) -> int:
        self.check(a)
        require_int(exp, "exp", lo=0)
        res = 1
        base = a
        e = exp
        while e > 0:
            if e & 1:
                res = self._mul[res][base]
            base = self._mul[base][base]
            e >>= 1
        return res

    def mult_order(self, a: int) -> int:
        self.check(a)
        if a == 0:
            raise GfqCertError("zero has no multiplicative order")
        cur = a
        order = 1
        while cur != 1:
            cur = self._mul[cur][a]
            order += 1
        return order

    def primitive_element(self) -> int:
        for a in range(1, self.q):
            if self.mult_order(a) == self.q - 1:
                return a
        raise GfqCertError(f"no primitive element found in GF({self.q})")


def field_axiom_violations(F: GaloisField) -> list[str]:
    """Exhaustively check all finite-field axioms and return sorted violated axiom tags."""
    q = F.q
    viol: set[str] = set()
    for a in range(q):
        if F.add(a, 0) != a:
            viol.add("add_identity")
        if F.mul(a, 1) != a:
            viol.add("mul_identity")
        if F.add(a, F.neg(a)) != 0:
            viol.add("add_inverse")
        if a != 0 and F.mul(a, F.inv(a)) != 1:
            viol.add("mul_inverse")
        for b in range(q):
            if F.add(a, b) != F.add(b, a):
                viol.add("add_comm")
            if F.mul(a, b) != F.mul(b, a):
                viol.add("mul_comm")
            for c in range(q):
                if F.add(F.add(a, b), c) != F.add(a, F.add(b, c)):
                    viol.add("add_assoc")
                if F.mul(F.mul(a, b), c) != F.mul(a, F.mul(b, c)):
                    viol.add("mul_assoc")
                if F.mul(a, F.add(b, c)) != F.add(F.mul(a, b), F.mul(a, c)):
                    viol.add("distributive")
    F.primitive_element()
    return sorted(viol)


def check_field_axioms(F: GaloisField) -> bool:
    return len(field_axiom_violations(F)) == 0


def validate_matrix(G: list[list[int]], F: GaloisField) -> tuple[int, int]:
    if not isinstance(G, list) or not G or not isinstance(G[0], list) or not G[0]:
        raise GfqCertError("matrix must be a non-empty list of non-empty rows")
    n = len(G[0])
    for row in G:
        if not isinstance(row, list) or len(row) != n:
            raise GfqCertError("matrix rows must have uniform length")
        for x in row:
            F.check(x)
    return len(G), n


def rref(G: list[list[int]], F: GaloisField, col_order: list[int] | None = None) -> tuple[list[list[int]], list[int]]:
    nrows, n = validate_matrix(G, F)
    rows = [list(row) for row in G]
    if col_order is None:
        order = list(range(n))
    else:
        if (
            type(col_order) is not list
            or len(col_order) != n
            or any(type(c) is not int for c in col_order)
            or set(col_order) != set(range(n))
        ):
            raise GfqCertError("col_order must be a permutation of 0..n-1")
        order = list(col_order)
    add, mul, neg, inv = F._add, F._mul, F._neg, F._inv
    pivots: list[int] = []
    r = 0
    for c in order:
        if r >= nrows:
            break
        piv = -1
        for i in range(r, nrows):
            if rows[i][c] != 0:
                piv = i
                break
        if piv < 0:
            continue
        rows[r], rows[piv] = rows[piv], rows[r]
        iv = inv[rows[r][c]]
        rows[r] = [mul[iv][x] for x in rows[r]]
        piv_row = rows[r]
        for i in range(nrows):
            if i != r:
                factor = rows[i][c]
                if factor != 0:
                    ri = rows[i]
                    rows[i] = [add[ri[j]][neg[mul[factor][piv_row[j]]]] for j in range(n)]
        pivots.append(c)
        r += 1
    return rows[:r], pivots


def matrix_rank(G: list[list[int]], F: GaloisField) -> int:
    return len(rref(G, F)[0])


def nullspace_basis(H: list[list[int]], F: GaloisField) -> list[list[int]]:
    _, n = validate_matrix(H, F)
    R, pivots = rref(H, F)
    piv_set = set(pivots)
    free_cols = [c for c in range(n) if c not in piv_set]
    basis: list[list[int]] = []
    for fc in free_cols:
        vec = [0] * n
        vec[fc] = 1
        for i, pc in enumerate(pivots):
            vec[pc] = F._neg[R[i][fc]]
        basis.append(vec)
    return basis


def hamming_weight(vec: list[int]) -> int:
    return sum(1 for x in vec if x != 0)


def row_space_contains(G: list[list[int]], F: GaloisField, vec: list[int]) -> bool:
    _, n = validate_matrix(G, F)
    if not isinstance(vec, list) or len(vec) != n:
        raise GfqCertError("vector length mismatch")
    for x in vec:
        F.check(x)
    R, _ = rref(G, F)
    return matrix_rank(R + [list(vec)], F) == len(R)


def verify_codeword_certificate(G: list[list[int]], F: GaloisField, codeword: list[int], expected_weight: int) -> bool:
    require_int(expected_weight, "expected_weight", lo=0)
    return row_space_contains(G, F, codeword) and hamming_weight(codeword) == expected_weight


def linear_combine(rows: list[list[int]], coeffs: list[int], F: GaloisField) -> list[int]:
    nrows, n = validate_matrix(rows, F)
    if len(coeffs) != nrows:
        raise GfqCertError("coefficient length mismatch")
    out = [0] * n
    add, mul = F._add, F._mul
    for c, row in zip(coeffs, rows):
        F.check(c)
        if c != 0:
            out = [add[out[j]][mul[c][row[j]]] for j in range(n)]
    return out


def shorten_code(G: list[list[int]], F: GaloisField, coords: list[int]) -> list[list[int]]:
    """Primal shortening on coordinate indices `coords`: subcode zero on coords, then drop coords."""
    _, n = validate_matrix(G, F)
    if (
        not coords
        or len(coords) >= n
        or any(type(c) is not int or not (0 <= c < n) for c in coords)
        or len(set(coords)) != len(coords)
    ):
        raise GfqCertError("invalid shortening coordinates")
    basis, _ = rref(G, F)
    k = len(basis)
    if k == 0:
        raise GfqCertError("zero-rank code cannot be shortened")
    H_sel = [[basis[j][s] for j in range(k)] for s in coords]
    msgs = nullspace_basis(H_sel, F)
    if not msgs:
        return []
    drop_set = set(coords)
    keep = [j for j in range(n) if j not in drop_set]
    raw_rows = [[linear_combine(basis, u, F)[j] for j in keep] for u in msgs]
    short_rows, _ = rref(raw_rows, F)
    return short_rows


def certify_pillar1_fields() -> dict[str, Any]:
    """Exhaustively certify all 7 Conway-canonical fields and GF(9) Conway vs x^2+1 contrast."""
    field_records: list[dict[str, Any]] = []
    for q in SUPPORTED_Q:
        F = GaloisField(q)
        field_records.append({
            "q": q,
            "p": F.p,
            "m": F.m,
            "modulus": list(F.modulus) if F.modulus is not None else None,
            "primitive_element": F.primitive_element(),
            "axioms_verified": check_field_axioms(F),
        })

    f9_conway = GaloisField(9)
    f9_math0 = GaloisField(9, modulus=NON_CONWAY_GF9_MODULUS)
    mul_diff_pairs = sum(
        1 for a in range(9) for b in range(9) if f9_conway.mul(a, b) != f9_math0.mul(a, b)
    )
    add_diff_pairs = sum(
        1 for a in range(9) for b in range(9) if f9_conway.add(a, b) != f9_math0.add(a, b)
    )
    return {
        "fields": field_records,
        "gf9_conway_contrast": {
            "conway_modulus": list(CONWAY_MODULI[9][1]),
            "math0_pr3_modulus": list(NON_CONWAY_GF9_MODULUS),
            "conway_x_squared": f9_conway.mul(3, 3),
            "math0_x_squared": f9_math0.mul(3, 3),
            "conway_x_order": f9_conway.mult_order(3),
            "math0_x_order": f9_math0.mult_order(3),
            "conway_primitive_element": f9_conway.primitive_element(),
            "math0_primitive_element": f9_math0.primitive_element(),
            "add_table_mismatches": add_diff_pairs,
            "mul_table_mismatches": mul_diff_pairs,
        },
    }


# ---------------------------------------------------------------------------
# Pillar 2: Zimmermann relative-rank Checker #2, 15 math0#4 codes,
#           exact MacWilliams duality, and GF(7) Delsarte LP verification
# ---------------------------------------------------------------------------

def build_zimmermann_chain(
    G: list[list[int]], F: GaloisField
) -> tuple[int, list[tuple[list[list[int]], list[int], int]]]:
    """Greedily construct systematic matrices with disjoint unused-column relative ranks."""
    _, n = validate_matrix(G, F)
    basis, _ = rref(G, F)
    k = len(basis)
    if k == 0:
        raise GfqCertError("rank-0 generator matrix has undefined minimum distance")
    used: set[int] = set()
    chain: list[tuple[list[list[int]], list[int], int]] = []
    while len(used) < n:
        unused = [c for c in range(n) if c not in used]
        order = unused + sorted(used)
        rows, pivots = rref(basis, F, col_order=order)
        new_pivots = [c for c in pivots if c not in used]
        if not new_pivots:
            break
        chain.append((rows, pivots, len(new_pivots)))
        used.update(new_pivots)
    chain.sort(key=lambda item: -item[2])
    return k, chain


def _combo_count(k: int, s: int, q: int) -> int:
    return math.comb(k, s) * ((q - 1) ** (s - 1))


def zimmermann_min_distance(
    G: list[list[int]], F: GaloisField, max_enum: int = 2_000_000
) -> dict[str, Any]:
    """Exact minimum distance via lazy incremental Zimmermann relative-rank enumeration."""
    require_int(max_enum, "max_enum", lo=0)
    _, n = validate_matrix(G, F)
    k, chain = build_zimmermann_chain(G, F)
    ub = n + 1
    best_cw = list(chain[0][0][0])
    for row in G:
        w = hamming_weight(row)
        if 0 < w < ub:
            ub = w
            best_cw = list(row)

    q = F.q
    add = F._add
    mul = F._mul
    nz = tuple(range(1, q))
    scaled = [
        ([[tuple(mul[c][x] for x in row) for c in range(q)] for row in rows], kj)
        for rows, _, kj in chain
    ]
    done_s = [0] * len(chain)
    enumerated = 0

    def current_lb() -> int:
        raw = sum(max(0, (done_s[j] + 1) - (k - chain[j][2])) for j in range(len(chain)))
        return min(ub, raw)

    lb = current_lb()
    s = 0
    while lb < ub:
        s += 1
        for j, (sm, kj) in enumerate(scaled):
            if lb >= ub:
                break
            if s < k - kj:
                continue
            needed = sum(_combo_count(k, lvl, q) for lvl in range(done_s[j] + 1, s + 1))
            if enumerated + needed > max_enum:
                cert_ok = verify_codeword_certificate(G, F, best_cw, ub)
                return {
                    "q": q,
                    "n": n,
                    "k": k,
                    "d": None,
                    "lower_bound": lb,
                    "upper_bound": ub,
                    "complete": False,
                    "enumerated": enumerated,
                    "relative_ranks": [item[2] for item in chain],
                    "done_s": list(done_s),
                    "codeword": list(best_cw),
                    "certificate_verified": cert_ok,
                }
            for lvl in range(done_s[j] + 1, s + 1):
                for supp in combinations(range(k), lvl):
                    base_row = sm[supp[0]][1]
                    if lvl == 1:
                        enumerated += 1
                        w = sum(1 for x in base_row if x != 0)
                        if 0 < w < ub:
                            ub = w
                            best_cw = list(base_row)
                        continue
                    for rest in product(nz, repeat=lvl - 1):
                        enumerated += 1
                        acc = base_row
                        for pos, val in zip(supp[1:], rest):
                            acc = [add[a][b] for a, b in zip(acc, sm[pos][val])]
                        w = sum(1 for x in acc if x != 0)
                        if 0 < w < ub:
                            ub = w
                            best_cw = acc
            done_s[j] = s
            lb = current_lb()

    cert_ok = verify_codeword_certificate(G, F, best_cw, ub)
    return {
        "q": q,
        "n": n,
        "k": k,
        "d": ub,
        "lower_bound": ub,
        "upper_bound": ub,
        "complete": True,
        "enumerated": enumerated,
        "relative_ranks": [item[2] for item in chain],
        "done_s": list(done_s),
        "codeword": list(best_cw),
        "certificate_verified": cert_ok,
    }


def naive_disjoint_enum_count(relative_ranks: list[int], k: int, q: int, d: int) -> int:
    """Exact combination count required by naive full-rank disjoint-IS BZ (lb = g*(s+1))."""
    require_int(k, "k", lo=1)
    require_int(q, "q", lo=2)
    require_int(d, "d", lo=1)
    if type(relative_ranks) is not list or any(type(r) is not int or r < 0 or r > k for r in relative_ranks):
        raise GfqCertError("relative_ranks must be list of strict ints in 0..k")
    g = sum(1 for r in relative_ranks if r == k)
    if g < 1:
        raise GfqCertError("at least one full-rank information set is required")
    s_naive = min(k, (d - 1) // g)
    return sum(g * _combo_count(k, t, q) for t in range(1, s_naive + 1))


def exact_weight_distribution(G: list[list[int]], F: GaloisField) -> dict[str, int]:
    """Exhaustive exact weight distribution {str(w): count} over GF(q)^k."""
    validate_matrix(G, F)
    basis, _ = rref(G, F)
    k = len(basis)
    q = F.q
    add = F._add
    mul = F._mul
    nz = tuple(range(1, q))
    scaled = [[tuple(mul[c][x] for x in row) for c in range(q)] for row in basis]
    counts: dict[int, int] = {0: 1}
    scale_factor = q - 1
    for lvl in range(1, k + 1):
        for supp in combinations(range(k), lvl):
            base_row = scaled[supp[0]][1]
            if lvl == 1:
                w = sum(1 for x in base_row if x != 0)
                counts[w] = counts.get(w, 0) + scale_factor
                continue
            for rest in product(nz, repeat=lvl - 1):
                acc = base_row
                for pos, val in zip(supp[1:], rest):
                    acc = [add[a][b] for a, b in zip(acc, scaled[pos][val])]
                w = sum(1 for x in acc if x != 0)
                counts[w] = counts.get(w, 0) + scale_factor
    return {str(w): counts[w] for w in sorted(counts)}


def krawtchouk_exact(n: int, q: int, j: int, x: int) -> int:
    """Unnormalized Krawtchouk polynomial K_j^{(n,q)}(x) in exact integers."""
    require_int(n, "n", lo=0)
    require_int(q, "q", lo=2)
    require_int(j, "j", lo=0, hi=n)
    require_int(x, "x", lo=0, hi=n)
    total = 0
    qm1 = q - 1
    for r in range(j + 1):
        term = (qm1 ** (j - r)) * math.comb(x, r) * math.comb(n - x, j - r)
        total = total - term if (r & 1) else total + term
    return total


def _validate_weight_dist(dist: Any, n: int, name: str) -> dict[int, int]:
    if type(dist) is not dict:
        raise GfqCertError(f"{name} must be dict")
    parsed: dict[int, int] = {}
    for k_str, cnt in dist.items():
        if type(k_str) is not str or not _CANON_UINT_RE.fullmatch(k_str):
            raise GfqCertError(f"{name} has invalid weight key: {k_str!r}")
        w = int(k_str)
        if w > n:
            raise GfqCertError(f"{name} weight key {w} exceeds n={n}")
        parsed[w] = require_int(cnt, f"{name}[{k_str}]", lo=0)
    return parsed


def macwilliams_holds(
    primal_dist: dict[str, int], dual_dist: dict[str, int], n: int, q: int, k: int
) -> bool:
    """Exact pure-Q check: B_j == q^{-k} * sum_i A_i * K_j^{(n,q)}(i) for all j = 0..n."""
    require_int(n, "n", lo=1)
    require_int(q, "q", lo=2)
    require_int(k, "k", lo=0, hi=n)
    primal = _validate_weight_dist(primal_dist, n, "primal_dist")
    dual = _validate_weight_dist(dual_dist, n, "dual_dist")
    q_k = q ** k
    for j in range(n + 1):
        rhs_num = sum(cnt * krawtchouk_exact(n, q, j, w) for w, cnt in primal.items())
        if Fraction(rhs_num, q_k) != Fraction(dual.get(j, 0), 1):
            return False
    return True


def verify_macwilliams_identity(G: list[list[int]], F: GaloisField) -> dict[str, Any]:
    _, n = validate_matrix(G, F)
    basis, _ = rref(G, F)
    k = len(basis)
    dual_basis = nullspace_basis(basis, F)
    primal_dist = exact_weight_distribution(basis, F)
    dual_dist = exact_weight_distribution(dual_basis, F)
    primal_d = min(int(w) for w in primal_dist if int(w) > 0)
    dual_d = min(int(w) for w in dual_dist if int(w) > 0)
    return {
        "q": F.q,
        "n": n,
        "k": k,
        "dual_k": len(dual_basis),
        "primal_d": primal_d,
        "dual_d": dual_d,
        "primal_weight_distribution": primal_dist,
        "dual_weight_distribution": dual_dist,
        "macwilliams_all_j_exact": macwilliams_holds(primal_dist, dual_dist, n, F.q, k),
    }


def verify_delsarte_certificate(entry: dict[str, Any]) -> dict[str, Any]:
    """Independent pure-Z/Q verifier for a Foundation-0/gfq-codes Delsarte LP certificate."""
    if type(entry) is not dict:
        raise GfqCertError("Delsarte certificate entry must be dict")
    req_keys = {"id", "q", "n", "k", "excluded_distance", "krawtchouk_coefficients", "size_bound"}
    if entry.keys() != req_keys:
        raise GfqCertError(f"unexpected Delsarte keys: {sorted(entry.keys())}")
    cid = entry["id"]
    if type(cid) is not str or not cid.strip():
        raise GfqCertError("invalid certificate id")
    q = require_int(entry["q"], "q", lo=2)
    n = require_int(entry["n"], "n", lo=1)
    k = require_int(entry["k"], "k", lo=1, hi=n)
    excl_d = require_int(entry["excluded_distance"], "excluded_distance", lo=1, hi=n)
    coeffs = entry["krawtchouk_coefficients"]
    if type(coeffs) is not list or not coeffs or len(coeffs) > n + 1:
        raise GfqCertError("invalid krawtchouk_coefficients list")
    a = [require_int(c, f"a[{j}]", lo=0) for j, c in enumerate(coeffs)]
    if a[0] <= 0:
        raise GfqCertError("a_0 must be strictly positive")
    claimed_bound = parse_rational_str(entry["size_bound"], "size_bound")

    def eval_f(x: int) -> int:
        return sum(aj * krawtchouk_exact(n, q, j, x) for j, aj in enumerate(a))

    f0 = eval_f(0)
    tail_vals = [eval_f(x) for x in range(excl_d, n + 1)]
    max_tail = max(tail_vals)
    if max_tail > 0:
        raise GfqCertError(f"Delsarte nonpositivity violated: max f(x)={max_tail} > 0")
    exact_bound = Fraction(f0, a[0])
    if exact_bound != claimed_bound:
        raise GfqCertError(f"size_bound mismatch: computed {frac_str(exact_bound)} != claimed {frac_str(claimed_bound)}")
    q_k = q ** k
    slack = a[0] * q_k - f0
    if slack <= 0:
        raise GfqCertError(f"Delsarte strict inequality failed: {frac_str(exact_bound)} >= {q_k}")
    return {
        "id": cid,
        "q": q,
        "n": n,
        "k": k,
        "excluded_distance": excl_d,
        "f0": f0,
        "a0": a[0],
        "size_bound": frac_str(exact_bound),
        "q_pow_k": q_k,
        "strict_integer_slack": slack,
        "max_tail_f_value": max_tail,
        "excluded": True,
    }


def ternary_golay_generator(extended: bool = False) -> list[list[int]]:
    if type(extended) is not bool:
        raise GfqCertError("extended must be bool")
    g_poly = [2, 0, 1, 2, 1, 1]
    rows: list[list[int]] = []
    for i in range(6):
        row = [0] * i + g_poly + [0] * (11 - i - len(g_poly))
        if extended:
            row.append((-sum(row)) % 3)
        rows.append(row)
    return rows


def hamming_generator(F: GaloisField, r: int) -> list[list[int]]:
    require_int(r, "r", lo=2)
    cols: list[tuple[int, ...]] = []
    for vec in product(range(F.q), repeat=r):
        first = next((x for x in vec if x != 0), 0)
        if first == 1:
            cols.append(vec)
    H = [[cols[j][i] for j in range(len(cols))] for i in range(r)]
    return nullspace_basis(H, F)


# ---------------------------------------------------------------------------
# Pillar 3: AUDIT-109 F_{2^5} binary Goppa (24,5,3,9) + primal shortening
#           & canonical unambiguous matrix parser closing math0#3/#4 bugs
# ---------------------------------------------------------------------------

def _gf32_mul(a: int, b: int) -> int:
    res = 0
    x = a
    y = b
    while y > 0:
        if y & 1:
            res ^= x
        x <<= 1
        if x & 32:
            x ^= 37
        y >>= 1
    return res


def _gf32_inv(a: int) -> int:
    if a == 0:
        raise GfqCertError("zero has no inverse in GF(32)")
    res = 1
    base = a
    e = 30
    while e > 0:
        if e & 1:
            res = _gf32_mul(res, base)
        base = _gf32_mul(base, base)
        e >>= 1
    return res


def _gf32_eval_g(z: int) -> int:
    z2 = _gf32_mul(z, z)
    z3 = _gf32_mul(z2, z)
    return z3 ^ z2 ^ _gf32_mul(2, z) ^ 1


def _binary_goppa_24_5_3_generator() -> list[list[int]]:
    support = list(range(24))
    H: list[list[int]] = []
    inv_g = [_gf32_inv(_gf32_eval_g(a)) for a in support]
    for j in range(3):
        vals = []
        for idx, a in enumerate(support):
            pwr = 1
            for _ in range(j):
                pwr = _gf32_mul(pwr, a)
            vals.append(_gf32_mul(pwr, inv_g[idx]))
        for bit in range(5):
            H.append([(v >> bit) & 1 for v in vals])
    return nullspace_basis(H, GaloisField(2))


def parse_matrix_canonical(text: str, F: GaloisField) -> list[list[int]]:
    """Canonical unambiguous generator-matrix parser closing all math0#3/#4 defects."""
    if type(text) is not str:
        raise GfqCertError("matrix text must be str")
    entries: list[tuple[int, str, str]] = []
    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        cleaned = raw_line.split("#", 1)[0].strip().rstrip(";")
        if cleaned:
            entries.append((lineno, raw_line, cleaned))
    if not entries:
        raise GfqCertError("no matrix data found")

    rows: list[list[int]] = []
    for idx, (lineno, raw_line, cleaned) in enumerate(entries):
        has_brackets = ("[" in cleaned) or ("]" in cleaned)
        stripped = cleaned.strip().strip("[]").strip()
        if not stripped:
            continue
        if _COMPACT_RE.fullmatch(stripped):
            vals = [int(ch) for ch in stripped]
            for v in vals:
                F.check(v)
            rows.append(vals)
            continue

        toks = [t for t in _SEP_RE.split(stripped) if t != ""]
        if not toks:
            continue

        if idx == 0 and (not has_brackets) and len(entries) > 1:
            second = entries[1][2].strip().strip("[]").strip()
            if _COMPACT_RE.fullmatch(second):
                width2 = len(second)
            else:
                width2 = len([t for t in _SEP_RE.split(second) if t != ""])
            hdr = [int(t) for t in toks] if all(_UINT_TOK_RE.fullmatch(t) for t in toks) else None
            if hdr is not None:
                rem_rows = len(entries) - 1
                is_valid_row_same_width = (len(hdr) == width2) and all(0 <= v < F.q for v in hdr)
                if not is_valid_row_same_width:
                    if len(hdr) == 3 and hdr[1] == rem_rows and hdr[2] == width2:
                        if hdr[0] != F.q:
                            raise GfqCertError(f"header says q={hdr[0]} but field is GF({F.q})")
                        continue
                    if len(hdr) == 2 and hdr[0] == rem_rows and hdr[1] == width2:
                        continue

        if not all(_UINT_TOK_RE.fullmatch(t) for t in toks):
            raise GfqCertError(f"cannot parse matrix line {lineno}: {raw_line!r}")
        vals = [int(t) for t in toks]
        for v in vals:
            F.check(v)
        rows.append(vals)

    validate_matrix(rows, F)
    return rows


def certify_pillar3_goppa_and_parser() -> dict[str, Any]:
    """Certify AUDIT-109 binary Goppa (24,5,3,9) + primal shortening + canonical parser fixes."""
    F2 = GaloisField(2)
    G24 = _binary_goppa_24_5_3_generator()
    z24 = zimmermann_min_distance(G24, F2)
    dist24 = exact_weight_distribution(G24, F2)

    G21 = shorten_code(G24, F2, [21, 22, 23])
    z21 = zimmermann_min_distance(G21, F2)
    dist21 = exact_weight_distribution(G21, F2)
    all_in_parent = all(row_space_contains(G24, F2, row + [0, 0, 0]) for row in G21)

    F3, F4, F5 = GaloisField(3), GaloisField(4), GaloisField(5)
    p_bracket = parse_matrix_canonical("[1,2]\n[0,1]\n", F3)
    p_gf4_3x3 = parse_matrix_canonical("1 2 3\n0 1 0\n0 0 1\n", F4)
    p_compact_1row = parse_matrix_canonical("20121\n", F3)
    p_gf5_kn_hdr = parse_matrix_canonical("2 3\n1 0 1\n0 1 2\n", F5)
    p_gf3_qkn_hdr = parse_matrix_canonical("3 2 3\n1 0 2\n0 1 1\n", F3)

    bad_err_msg = ""
    try:
        parse_matrix_canonical("a b c d\n1 0 1 2\n0 1 2 0\n", F3)
    except GfqCertError as err:
        bad_err_msg = str(err)

    return {
        "binary_goppa_24_5_3": {
            "n": z24["n"],
            "k": z24["k"],
            "d": z24["d"],
            "relative_ranks": z24["relative_ranks"],
            "zimmermann_enumerated": z24["enumerated"],
            "weight_7_codewords": dist24.get("7", 0),
            "weight_distribution": dist24,
        },
        "primal_shortened_21_6_7": {
            "shortened_coords": [21, 22, 23],
            "n": z21["n"],
            "k": z21["k"],
            "d": z21["d"],
            "relative_ranks": z21["relative_ranks"],
            "zimmermann_enumerated": z21["enumerated"],
            "weight_7_codewords": dist21.get("7", 0),
            "distance_monotone_ge_parent": z21["d"] >= z24["d"],
            "all_shortened_rows_in_parent": all_in_parent,
        },
        "canonical_parser_witnesses": {
            "bracketed_2x2_gf3_rank": matrix_rank(p_bracket, F3),
            "gf4_3x3_rank": matrix_rank(p_gf4_3x3, F4),
            "compact_single_row_len": len(p_compact_1row[0]),
            "gf5_kn_header_rows": len(p_gf5_kn_hdr),
            "gf3_qkn_header_rows": len(p_gf3_qkn_hdr),
            "bad_line_error_message": bad_err_msg,
        },
    }


# ---------------------------------------------------------------------------
# Pinned primary-source portal data (for --standalone and --live pin check)
# ---------------------------------------------------------------------------

GFQ_CODES_MAIN_SHA = "9200a06be239d6cc70ec94ed82f681e75b9bc718"
MATH0_PR4_HEAD_SHA = "98bdb8727b180f62c0a8e77b8fdcc659e3b0bd38"
MATH0_PR3_HEAD_SHA = "d94ad5d4869abf586d7e97d237c539b504ae5877"

PINNED_GFQ_CODES_FILES: dict[str, tuple[int, str]] = {
    "gfq_codes_head.json": (200, "2a2891a954d69777c3b01ac95935b8bce5e9ddf4a7e2a1073fe72219c39dd84f"),
    "gfq_codes_issues.json": (1560, "1c6af115c3605024008706c710486df0440ce37d0f18284e0068186eb8657a26"),
    "gfq_codes_prs.json": (4577, "8250d3a794063d824c003a22d4514cd1960691c6af058a0218d6bd5da10982ca"),
    "gfq_codes/codes/README.md": (2054, "8f61721e39cd03453e02545127690c260196fabd530a2d5283d4286a875f8900"),
    "gfq_codes/tools/README.md": (2927, "8d4d316df8908ab84520dbfe1ee90c2d1754527fd12721a57fe81d3d714a5eab"),
    "gfq_codes/tools/SHA256SUMS": (186, "abffba1d0aac033de729d1aaa5dac8f1fee109d0e8bc5d04dcc7cbb8d5087799"),
    "gfq_codes/tools/check_bound.py": (4035, "87dfe9991753d8e551aac029d29c9f1e8a7e0124a065f626d284430d6413e450"),
    "gfq_codes/tools/check_bound_independent.py": (4967, "e36196ce6caadebe9c891a1198c9af6e3f33f476ba82ad0e06642e4a0545de18"),
    "gfq_codes/results/gf7-upper-bounds/PROOF.md": (9532, "0c7a998311288f322fa45f3982279b559a825465eb5ed6eb9b428aef3b6e37b6"),
    "gfq_codes/results/gf7-upper-bounds/certificate.json": (1419, "78f6021f200f1e6a508b8598338e801ff1b025c7f818426c2e21ba46da57b603"),
    "gfq_codes/results/gf7-upper-bounds/sources.json": (3530, "3aa52db54847d8de0b09b2c9786f9478052e65092a01e897871b18afe313a4f3"),
}

PINNED_GFQ_CODES_OPEN_PRS: list[dict[str, Any]] = [
    {"number": 9, "head_prefix": "8123f058", "role": "brute_force_distance_checker"},
    {"number": 10, "head_prefix": "b1f32e53", "role": "coordinate_subspace_distance_checker"},
    {"number": 11, "head_prefix": "42863db3", "role": "gap_one_target_selector"},
    {"number": 13, "head_prefix": "d12113e2", "role": "maintainer_contact_packet"},
    {"number": 14, "head_prefix": "492234f3", "role": "systematic_quasicyclic_pilot"},
    {"number": 19, "head_prefix": "7310a39e", "role": "gf789_delsarte_table_scan"},
]

PINNED_GF7_DELSARTE_CERTS: list[dict[str, Any]] = [
    {
        "id": "gf7-n55-k10-exclude-d40",
        "q": 7, "n": 55, "k": 10, "excluded_distance": 40,
        "krawtchouk_coefficients": [3582480, 2011428, 438976, 87849, 13572, 1770, 160, 10],
        "size_bound": "317755831120/1357",
    },
    {
        "id": "gf7-n56-k10-exclude-d41",
        "q": 7, "n": 56, "k": 10, "excluded_distance": 41,
        "krawtchouk_coefficients": [6136245, 2553765, 542337, 103361, 15512, 1940, 170, 10],
        "size_bound": "21608924188425/136361",
    },
    {
        "id": "gf7-n56-k11-exclude-d40",
        "q": 7, "n": 56, "k": 11, "excluded_distance": 40,
        "krawtchouk_coefficients": [40123776, 22842204, 5545512, 1194585, 211428, 31626, 3724, 322, 16],
        "size_bound": "2224290817840/1357",
    },
    {
        "id": "gf7-n57-k11-exclude-d41",
        "q": 7, "n": 57, "k": 11, "excluded_distance": 41,
        "krawtchouk_coefficients": [69953193, 29829417, 6987213, 1441701, 247116, 35688, 4062, 338, 16],
        "size_bound": "151262469318975/136361",
    },
]

PINNED_MATH0_PR4_CODES: tuple[tuple[int, int, int, int, str, int, str, tuple[str, ...]], ...] = (
    (3, 22, 8, 9, "q3_n22_k8_d9.txt", 352, "210b2cee876507ff869b64dd5a0bc8696eb28ec8ce589038b4d21a9c808732bc",
     ("0111010111100111110111", "1210021110210220201120", "1112111110221002121100", "0101000001120002111021",
      "0222021211002020210000", "0011000210011002200212", "0111101022210210122212", "2021001101211212210122")),
    (3, 23, 8, 10, "q3_n23_k8_d10.txt", 368, "6c11dab5b06342a3c40ae88c8d1b60f7eb8989ffefddaa6476cb89bcba6550ab",
     ("00010110010101010111100", "10101021101010110000011", "00020112100020101002100", "21002202001111112222110",
      "12110200221222010010120", "10011002011210221012111", "11011002021001101100000", "00110012121021020210221")),
    (3, 23, 9, 9, "q3_n23_k9_d9.txt", 414, "00ee51d291c13919f2c23440fd8b3ec31fc862b6dcffef1a991e22e7b64ad7db",
     ("01011110111110110001111", "00102221212001200100101", "12000222010110211001200", "02021102111222122210121",
      "20112022010211111220022", "11120111020100121201202", "20112121112011022122200", "12200220022000100222010",
      "11112222220220111121212")),
    (3, 24, 10, 8, "q3_n24_k10_d8.txt", 480, "944b087a4bc5a3e8b3407c580ad7928b55ceca2c4883941f23dd2866b6bf708e",
     ("110111111010111110011101", "100221011121202000120211", "111012110122112010012121", "121220111002000111000012",
      "121202112211012100000222", "121122201001012021221011", "020020001111120111021110", "002212200002010102222211",
      "222020121111100001110121", "211112111010222021020202")),
    (3, 24, 9, 9, "q3_n24_k9_d9.txt", 432, "58ba192e00f815914a4488775710acbfcfa10b38bda8d21f11bcee279e6e3367",
     ("011111100001111010110111", "121211201102002100101021", "202210211010020210022001", "002211022222111200002222",
      "202212022222102021101211", "210002202212110021011102", "222221201112211120001202", "001220110102121201220221",
      "221121101200100220211210")),
    (4, 19, 8, 8, "q4_n19_k8_d8.txt", 304, "41db9ccf9fbda57b1b7fcb6fabe854b795641c5ee533e4f398220301c922f119",
     ("1011111111001111110", "1012100032113022221", "3133312033312311132", "3223233320303320323",
      "3202213122132010300", "1023203330133033033", "1013020231123121103", "1131121101032020011")),
    (4, 20, 9, 7, "q4_n20_k9_d7.txt", 360, "550b51e2e198cd63094bf7d3a82f412d99853e16f0fd128b9f5d98aac554a61a",
     ("01101111110000011111", "10211230111111132202", "30213230222333203020", "02031132011002211200",
      "23011020301303111113", "10220013313320210113", "23300110123031322210", "01131001030122121011",
      "30102113333322313331")),
    (4, 22, 6, 12, "q4_n22_k6_d12.txt", 264, "9ce106e63ace6c8d5fda930472ecbb9028dcf7bdec0f45d8e377f6dd5004f9fb",
     ("0110011110110111101110", "1201102101221013012130", "0022210200313002133220", "2213123131222201011220",
      "2132311213222121011030", "1121121323333002202111")),
    (4, 23, 7, 11, "q4_n23_k7_d11.txt", 322, "2cdd3a878eaee94ec98de29bc44d633d02693f61ff94c9c7942de84e16d0583e",
     ("10010101011010011111110", "21101311131101130132031", "30322112123012311300012", "00120322121020223222031",
      "20123230001012131200332", "22333000112032130131211", "22322233302133202010103")),
    (4, 24, 8, 11, "q4_n24_k8_d11.txt", 384, "a9fa69edd0a5efc86f2e39c43e32c799d35282bd937e2bee8c0efedee5632f62",
     ("010010111011110111111111", "101011030030021331331123", "131133000112032002211222", "310120010301331200100121",
      "320122300232000303303110", "203211303002332211102133", "021010201103030100331130", "010013120210220310113301")),
    (5, 16, 5, 9, "q5_n16_k5_d9.txt", 160, "28d7a2636c31d18007c9aab96126363a2a1981a1597729e12b990aa84f7f11bb",
     ("0111111111111011", "1144421232142140", "4413322324424402", "2223203021122334", "2304122432311431")),
    (5, 16, 6, 8, "q5_n16_k6_d8.txt", 192, "c7f1e86455614f01933b27f395338ea0f5364b1cabc5c725a927667c96908894",
     ("1111101011000111", "0143212132110411", "2103231140000210", "2403412101301232", "1121311234442333", "4442044004201213")),
    (5, 17, 6, 9, "q5_n17_k6_d9.txt", 204, "65668670f4cb381e070c5372e8deaf1c7f1feecf2daab6d20ae40c67f841d96c",
     ("11111101111111001", "02402110424024114", "22440013120023103", "03434024433244422", "02241342200210012", "42131333223110040")),
    (5, 17, 7, 8, "q5_n17_k7_d8.txt", 238, "76c6c960fee790bdcc5fd773bf4d0f646cf92570116be37537bac190cc3cfbbe",
     ("11111111001110111", "03011232113231024", "01001313041110044", "41114411340314010", "12433301222201302", "23322133132142340",
      "01322323042101304")),
    (5, 18, 9, 7, "q5_n18_k9_d7.txt", 324, "5920051718719e2d05a0e351b4f1ec4b08d5476443da6f5143a00334b52da344",
     ("100000000333040104", "010000000433304010", "001000000043330401", "000100000104333040", "000010000010433304",
      "000001000401043330", "000000100040104333", "000000010304010433", "000000001330401043")),
)


def certify_pillar2_zimmermann_and_duality(
    math0_matrices: list[tuple[int, int, int, int, str, str, list[list[int]]]] | None = None,
    gf7_certs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Certify Zimmermann relative-rank vs naive BZ, all 15 math0#4 codes, MacWilliams, & GF(7) Delsarte."""
    F3 = GaloisField(3)
    F4 = GaloisField(4)
    golay11 = ternary_golay_generator(extended=False)
    golay12 = ternary_golay_generator(extended=True)
    ham_gf4_r3 = hamming_generator(F4, 3)

    z_g11 = zimmermann_min_distance(golay11, F3)
    naive_g11 = naive_disjoint_enum_count(z_g11["relative_ranks"], 6, 3, 5)
    z_g12 = zimmermann_min_distance(golay12, F3)
    z_h4 = zimmermann_min_distance(ham_gf4_r3, F4)
    macwilliams_g11 = verify_macwilliams_identity(golay11, F3)

    if math0_matrices is None:
        code_items = [
            (q, n, k, d, fn, sha, [[int(ch) for ch in row] for row in rows])
            for q, n, k, d, fn, _, sha, rows in PINNED_MATH0_PR4_CODES
        ]
    else:
        code_items = math0_matrices

    if len(code_items) != 15:
        raise GfqCertError(f"expected 15 math0#4 codes, got {len(code_items)}")

    fields_cache = {q: GaloisField(q) for q in (3, 4, 5)}
    math0_records: list[dict[str, Any]] = []
    tot_z = 0
    tot_naive = 0
    wins = 0
    ties = 0
    losses = 0
    for q, n, k, d_exp, fn, sha, G in code_items:
        F = fields_cache[q]
        z = zimmermann_min_distance(G, F)
        if z["n"] != n or z["k"] != k or z["d"] != d_exp:
            raise GfqCertError(f"math0#4 code {fn} verification mismatch: {z}")
        naive_cnt = naive_disjoint_enum_count(z["relative_ranks"], k, q, d_exp)
        z_cnt = z["enumerated"]
        if z_cnt < naive_cnt:
            wins += 1
        elif z_cnt == naive_cnt:
            ties += 1
        else:
            losses += 1
        tot_z += z_cnt
        tot_naive += naive_cnt
        math0_records.append({
            "file": fn,
            "sha256": require_hex(sha, 64, f"{fn}.sha256"),
            "q": q,
            "n": n,
            "k": k,
            "d": d_exp,
            "relative_ranks": z["relative_ranks"],
            "done_s": z["done_s"],
            "zimmermann_enumerated": z_cnt,
            "naive_disjoint_enumerated": naive_cnt,
            "certificate_verified": z["certificate_verified"],
        })

    certs_in = PINNED_GF7_DELSARTE_CERTS if gf7_certs is None else gf7_certs
    if len(certs_in) != 4:
        raise GfqCertError(f"expected 4 GF(7) Delsarte certificates, got {len(certs_in)}")
    delsarte_verified = [verify_delsarte_certificate(c) for c in certs_in]

    bad_cert = dict(certs_in[0])
    bad_cert["excluded_distance"] = 39
    neg_rejected = False
    try:
        verify_delsarte_certificate(bad_cert)
    except GfqCertError:
        neg_rejected = True

    return {
        "classical_controls": {
            "ternary_golay_11_6_5": {
                "d": z_g11["d"],
                "relative_ranks": z_g11["relative_ranks"],
                "done_s": z_g11["done_s"],
                "zimmermann_enumerated": z_g11["enumerated"],
                "naive_disjoint_enumerated": naive_g11,
                "speedup_ratio": frac_str(Fraction(naive_g11, z_g11["enumerated"])),
            },
            "ternary_golay_ext_12_6_6": {
                "d": z_g12["d"],
                "relative_ranks": z_g12["relative_ranks"],
                "zimmermann_enumerated": z_g12["enumerated"],
            },
            "hamming_gf4_21_18_3": {
                "d": z_h4["d"],
                "relative_ranks": z_h4["relative_ranks"],
                "zimmermann_enumerated": z_h4["enumerated"],
            },
        },
        "macwilliams_ternary_golay": macwilliams_g11,
        "math0_pr4_15_codes": {
            "count": len(math0_records),
            "all_exact": True,
            "strict_wins_over_naive": wins,
            "ties_with_naive": ties,
            "losses_vs_naive": losses,
            "total_zimmermann_enumerated": tot_z,
            "total_naive_disjoint_enumerated": tot_naive,
            "aggregate_speedup_ratio": frac_str(Fraction(tot_naive, tot_z)),
            "records": math0_records,
        },
        "gfq_codes_gf7_delsarte": {
            "count": len(delsarte_verified),
            "all_excluded": True,
            "negative_control_rejected": neg_rejected,
            "certificates": delsarte_verified,
        },
    }


# ---------------------------------------------------------------------------
# Certificate assembly & fail-closed semantic validation
# ---------------------------------------------------------------------------

def build_payload(
    math0_matrices: list[tuple[int, int, int, int, str, str, list[list[int]]]] | None = None,
    gf7_certs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "audit_id": "AUDIT-113",
        "track": "track-s16-gfq-distance-certifier",
        "novelty_tier": "N1",
        "prior_art_tier": "N0",
        "pillar_1_conway_fields": certify_pillar1_fields(),
        "pillar_2_zimmermann_and_duality": certify_pillar2_zimmermann_and_duality(
            math0_matrices=math0_matrices, gf7_certs=gf7_certs
        ),
        "pillar_3_goppa_and_parser": certify_pillar3_goppa_and_parser(),
    }


def assemble_certificate(
    execution_mode: str,
    live_portal_verified: bool,
    portal_manifest: dict[str, Any],
    payload: dict[str, Any],
) -> dict[str, Any]:
    if execution_mode not in ("live_portal_intake", "standalone_pinned_manifest"):
        raise GfqCertError(f"invalid execution_mode: {execution_mode!r}")
    if type(live_portal_verified) is not bool:
        raise GfqCertError("live_portal_verified must be bool")
    if live_portal_verified != (execution_mode == "live_portal_intake"):
        raise GfqCertError("execution_mode / live_portal_verified mismatch")
    payload_sha = canonical_sha256(payload)
    body = {
        "schema": "aletheia-gfq-distance-cert/1",
        "execution_mode": execution_mode,
        "live_portal_verified": live_portal_verified,
        "portal_manifest": portal_manifest,
        "payload_sha256": payload_sha,
        "payload": payload,
    }
    cert_sha = canonical_sha256(body)
    out = dict(body)
    out["certificate_sha256"] = cert_sha
    return out


def default_pinned_portal_manifest() -> dict[str, Any]:
    files = {
        rel: {"bytes": blen, "sha256": sha}
        for rel, (blen, sha) in sorted(PINNED_GFQ_CODES_FILES.items())
    }
    for _, _, _, _, fn, blen, sha, _ in PINNED_MATH0_PR4_CODES:
        files[f"math0_pr4_best/{fn}"] = {"bytes": blen, "sha256": sha}
    return {
        "gfq_codes_repo": "Foundation-0/gfq-codes",
        "gfq_codes_main_sha": GFQ_CODES_MAIN_SHA,
        "gfq_codes_open_prs": [dict(p) for p in PINNED_GFQ_CODES_OPEN_PRS],
        "gfq_codes_open_pr_count": len(PINNED_GFQ_CODES_OPEN_PRS),
        "gfq_codes_open_issue_count": 5,
        "gfq_codes_tools_sha256sums_ok": True,
        "math0_pr3_head_sha": MATH0_PR3_HEAD_SHA,
        "math0_pr4_head_sha": MATH0_PR4_HEAD_SHA,
        "pinned_file_count": len(files),
        "pinned_files": files,
    }


def validate_certificate(cert: Any, expected_manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    """Fail-closed semantic validator rejecting any structural, hash, or math forgery."""
    reject_invalid_json_types(cert)
    if type(cert) is not dict:
        raise GfqCertError("certificate must be dict")
    expected_top = {
        "schema", "execution_mode", "live_portal_verified",
        "portal_manifest", "payload_sha256", "payload", "certificate_sha256",
    }
    if cert.keys() != expected_top:
        raise GfqCertError(f"certificate top-level key mismatch: {sorted(cert.keys())}")
    if cert["schema"] != "aletheia-gfq-distance-cert/1":
        raise GfqCertError(f"unknown schema: {cert['schema']!r}")
    mode = cert["execution_mode"]
    live_flag = cert["live_portal_verified"]
    if mode not in ("live_portal_intake", "standalone_pinned_manifest") or type(live_flag) is not bool:
        raise GfqCertError("invalid execution_mode or live_portal_verified")
    if live_flag != (mode == "live_portal_intake"):
        raise GfqCertError("execution_mode and live_portal_verified disagree")

    p_sha = require_hex(cert["payload_sha256"], 64, "payload_sha256")
    c_sha = require_hex(cert["certificate_sha256"], 64, "certificate_sha256")
    if canonical_sha256(cert["payload"]) != p_sha:
        raise GfqCertError("payload_sha256 mismatch")
    body = {k: v for k, v in cert.items() if k != "certificate_sha256"}
    if canonical_sha256(body) != c_sha:
        raise GfqCertError("certificate_sha256 mismatch")

    manifest = cert["portal_manifest"]
    if type(manifest) is not dict:
        raise GfqCertError("portal_manifest must be dict")
    req_m_keys = {
        "gfq_codes_repo", "gfq_codes_main_sha", "gfq_codes_open_prs",
        "gfq_codes_open_pr_count", "gfq_codes_open_issue_count",
        "gfq_codes_tools_sha256sums_ok", "math0_pr3_head_sha",
        "math0_pr4_head_sha", "pinned_file_count", "pinned_files",
    }
    if manifest.keys() != req_m_keys:
        raise GfqCertError("portal_manifest key mismatch")
    require_hex(manifest["gfq_codes_main_sha"], 40, "gfq_codes_main_sha")
    require_hex(manifest["math0_pr3_head_sha"], 40, "math0_pr3_head_sha")
    require_hex(manifest["math0_pr4_head_sha"], 40, "math0_pr4_head_sha")
    if type(manifest["pinned_files"]) is not dict:
        raise GfqCertError("pinned_files must be dict")
    for rel, meta in manifest["pinned_files"].items():
        if type(meta) is not dict or meta.keys() != {"bytes", "sha256"}:
            raise GfqCertError(f"invalid pinned_files entry for {rel}")
        require_int(meta["bytes"], f"{rel}.bytes", lo=1)
        require_hex(meta["sha256"], 64, f"{rel}.sha256")
    ref_manifest = default_pinned_portal_manifest() if expected_manifest is None else expected_manifest
    if not strict_typed_equal(manifest, ref_manifest):
        raise GfqCertError("portal_manifest does not match pinned provenance")

    fresh_payload = build_payload()
    if not strict_typed_equal(cert["payload"], fresh_payload):
        raise GfqCertError("payload semantic mismatch against fresh recomputation")

    return {
        "ok": True,
        "execution_mode": mode,
        "live_portal_verified": live_flag,
        "payload_sha256": p_sha,
        "certificate_sha256": c_sha,
    }
