#!/usr/bin/env python3
"""Verify exact Delsarte upper-bound certificates using binomial sums."""

import argparse
from fractions import Fraction
import json
from math import comb
from pathlib import Path
import re
import sys


def object_without_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError(f"non-JSON constant: {value}")


def integer(value, name, minimum, maximum=None):
    if type(value) is not int or value < minimum or (maximum is not None and value > maximum):
        raise ValueError(f"invalid {name}: {value!r}")
    return value


def krawtchouk(n, q, degree, distance):
    """Ordinary (unnormalized) q-ary Krawtchouk polynomial at an integer."""
    return sum(
        (-1)**j * (q - 1)**(degree - j) * comb(distance, j) * comb(n - distance, degree - j)
        for j in range(max(0, degree - n + distance), min(degree, distance) + 1)
    )


def verify(record):
    if not isinstance(record, dict):
        raise ValueError("each certificate must be an object")
    name = record["id"]
    if not isinstance(name, str) or not name.strip():
        raise ValueError("id must be a nonempty string")
    q = integer(record["q"], "q", 2)
    n = integer(record["n"], "n", 1)
    k = integer(record["k"], "k", 1, n)
    distance = integer(record["excluded_distance"], "excluded_distance", 1, n)
    coeffs = record["krawtchouk_coefficients"]
    if not isinstance(coeffs, list) or not 1 <= len(coeffs) <= n + 1:
        raise ValueError("coefficient list must contain 1 to n+1 integers")
    for degree, value in enumerate(coeffs):
        integer(value, f"coefficient {degree}", 1 if degree == 0 else 0)

    def evaluate(x):
        return sum(a * krawtchouk(n, q, j, x) for j, a in enumerate(coeffs))

    for x in range(distance, n + 1):
        value = evaluate(x)
        if value > 0:
            raise ValueError(f"{name}: f({x}) = {value} is positive")
    bound = Fraction(evaluate(0), coeffs[0])
    declared = record["size_bound"]
    if not isinstance(declared, str) or not re.fullmatch(r"-?[0-9]+(?:/[0-9]+)?", declared):
        raise ValueError("size_bound must be an integer or NUM/DEN string")
    if Fraction(declared) != bound:
        raise ValueError(f"{name}: declared size_bound does not equal {bound}")
    if bound >= q**k:
        raise ValueError(f"{name}: size bound {bound} does not exclude {q**k} words")
    return f"{name}: q={q}, n={n}, k={k}, d <= {distance - 1}; size <= {bound} < {q**k}"


def check_file(path):
    with path.open(encoding="utf-8") as source:
        data = json.load(source, object_pairs_hook=object_without_duplicates,
                         parse_float=reject_constant, parse_constant=reject_constant)
    if not isinstance(data, dict) or type(data.get("format_version")) is not int or data["format_version"] != 1:
        raise ValueError("expected an object with format_version 1")
    records = data.get("certificates")
    if not isinstance(records, list) or not records:
        raise ValueError("certificates must be a nonempty list")
    reports, names = [], set()
    for record in records:
        report = verify(record)
        if record["id"] in names:
            raise ValueError(f"duplicate certificate id: {record['id']}")
        names.add(record["id"])
        reports.append(report)
    return reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("certificate", type=Path)
    path = parser.parse_args().certificate
    try:
        reports = check_file(path)
    except (OSError, ValueError, TypeError, KeyError, ZeroDivisionError, RecursionError) as error:
        print(f"FAIL: {path}: {error}", file=sys.stderr)
        return 1
    print("\n".join(reports))
    print(f"PASS: {len(reports)} exact upper-bound certificate(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
