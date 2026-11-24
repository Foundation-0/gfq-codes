"""Turn the rational certificates written by build_certs.py into the repository's integer format.

A positive scalar multiple of the coefficient list gives the same signs and the same ratio f(0)/a_0, so the
conclusion is unchanged. Each certificate is multiplied by the least common multiple of its denominators and
divided by the greatest common divisor of the results.

Usage: python3 to_integer.py out.json certs/gf7_certs.json certs/gf8_certs.json certs/gf9_certs.json
"""
import json
import sys
from fractions import Fraction
from math import gcd, lcm


def to_integer(cert):
    a = [Fraction(v) for v in cert["krawtchouk_coefficients"]]
    scale = lcm(*(v.denominator for v in a))
    ints = [int(v * scale) for v in a]
    g = 0
    for v in ints:
        g = gcd(g, v)
    ints = [v // g for v in ints]
    out = dict(cert)
    out["krawtchouk_coefficients"] = ints
    return out


def main(argv):
    if len(argv) < 3:
        raise SystemExit(__doc__)
    certs = []
    for path in argv[2:]:
        with open(path, encoding="utf-8") as handle:
            certs.extend(to_integer(c) for c in json.load(handle)["certificates"])
    with open(argv[1], "w", encoding="utf-8") as handle:
        json.dump({"format_version": 1, "certificates": certs}, handle, indent=0, separators=(",", ":"))
        handle.write("\n")
    print(len(certs), "certificates written")


if __name__ == "__main__":
    main(sys.argv)
