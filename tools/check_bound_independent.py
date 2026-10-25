#!/usr/bin/env python3
"""Independently check q-ary Delsarte bounds with exact polynomial arithmetic.

No search code or other checker is imported. Krawtchouk values are computed by
multiplying (1-z)^distance (1+(q-1)z)^(n-distance), truncated to the degree used
in the certificate. This differs from the binomial-sum checker.
"""

import argparse
from fractions import Fraction
import json
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


def reject_number(value):
    raise ValueError(f"noninteger JSON number: {value}")


def integer(record, field, minimum, maximum=None):
    value = record.get(field)
    if type(value) is not int or value < minimum or (maximum is not None and value > maximum):
        limit = f"{minimum}..{maximum}" if maximum is not None else f">= {minimum}"
        raise ValueError(f"{field}: expected an integer {limit}")
    return value


def krawtchouk_values(n, q, distance, degree):
    """Return coefficients through degree in the Krawtchouk generating product."""
    polynomial = [1]
    for step in range(n):
        multiplier = -1 if step < distance else q - 1
        product = [0] * min(len(polynomial) + 1, degree + 1)
        for index, coefficient in enumerate(polynomial):
            product[index] += coefficient
            if index + 1 < len(product):
                product[index + 1] += multiplier * coefficient
        polynomial = product
    return polynomial


def verify(record):
    if not isinstance(record, dict):
        raise ValueError("certificate must be an object")
    identifier = record.get("id")
    if not isinstance(identifier, str) or not identifier.strip():
        raise ValueError("id: expected a nonempty string")
    q = integer(record, "q", 2)
    n = integer(record, "n", 1)
    k = integer(record, "k", 1, n)
    distance = integer(record, "excluded_distance", 1, n)
    coefficients = record.get("krawtchouk_coefficients")
    if (not isinstance(coefficients, list) or not 1 <= len(coefficients) <= n + 1
            or any(type(value) is not int or value < 0 for value in coefficients)):
        raise ValueError("krawtchouk_coefficients: expected 1..n+1 nonnegative integers")
    if coefficients[0] <= 0:
        raise ValueError("krawtchouk_coefficients[0]: must be positive")
    declared = record.get("size_bound")
    if not isinstance(declared, str) or re.fullmatch(r"-?[0-9]+(?:/[0-9]+)?", declared) is None:
        raise ValueError("size_bound: expected an integer or NUM/DEN string")
    try:
        declared_bound = Fraction(declared)
    except ZeroDivisionError as error:
        raise ValueError("size_bound: denominator must be nonzero") from error

    degree = len(coefficients) - 1
    at_zero = sum(a * b for a, b in zip(coefficients, krawtchouk_values(n, q, 0, degree)))
    bound = Fraction(at_zero, coefficients[0])
    if bound != declared_bound:
        raise ValueError(f"size_bound: declared {declared}, computed {bound}")
    for index in range(distance, n + 1):
        value = sum(a * b for a, b in zip(coefficients, krawtchouk_values(n, q, index, degree)))
        if value > 0:
            raise ValueError(f"f({index}) = {value} > 0")
    if bound >= q ** k:
        raise ValueError(f"size bound {bound} is not below q^k = {q ** k}")
    return f"{identifier}: q={q}, n={n}, k={k}, d <= {distance - 1}; size bound {bound}"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("certificate", type=Path)
    path = parser.parse_args(argv).certificate
    try:
        with path.open(encoding="utf-8") as source:
            document = json.load(source, object_pairs_hook=object_without_duplicates,
                                 parse_float=reject_number, parse_constant=reject_number)
        if not isinstance(document, dict):
            raise ValueError("document must be an object")
        integer(document, "format_version", 1, 1)
        records = document.get("certificates")
        if not isinstance(records, list) or not records:
            raise ValueError("certificates: expected a nonempty array")
        identifiers = set()
        summaries = []
        for record in records:
            summary = verify(record)
            if record["id"] in identifiers:
                raise ValueError(f"duplicate certificate id: {record['id']}")
            identifiers.add(record["id"])
            summaries.append(summary)
    except (OSError, ValueError, RecursionError) as error:
        print(f"FAIL: {path}: {error}", file=sys.stderr)
        return 1
    for summary in summaries:
        print(summary)
    print(f"PASS: {len(summaries)} certificate(s), independently checked with exact arithmetic")
    return 0


if __name__ == "__main__":
    sys.exit(main())
