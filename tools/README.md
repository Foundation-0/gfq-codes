# Exact upper-bound checkers

These two independent Python 3.10+ programs check certificates for the classical
Delsarte linear-programming bound in q-ary Hamming space. They use only the
standard library and do not run a numerical optimizer.

```sh
python3 tools/check_bound.py path/to/certificate.json
python3 tools/check_bound_independent.py path/to/certificate.json
python3 -m unittest discover -s tests -v
sha256sum -c tools/SHA256SUMS
```

The first computes Krawtchouk values by their binomial sum; the second multiplies
the factors of their generating polynomial. Neither imports the other.
The hashes fix the checker versions for review separately from research results.
Changes to a checker require a separate review and an explicit hash update.

## Certificate format

One file contains a nonempty list of certificates with unique IDs:

```json
{
  "format_version": 1,
  "certificates": [{
    "id": "known-binary-example",
    "q": 2,
    "n": 3,
    "k": 3,
    "excluded_distance": 2,
    "krawtchouk_coefficients": [1, 1],
    "size_bound": "4/1"
  }]
}
```

Here q is the alphabet size (an integer at least 2), n the length, and q^k
the code size to exclude. For a linear code over GF(q), q must be a prime power
and k is its dimension. The generic inequality does not require linearity.
The example excludes eight binary words of length three with mutual distance
at least two; it is a classical control, not a new result.

For j=0,...,n, use the **unnormalized** convention

K_j(x) = sum_l (-1)^l (q-1)^(j-l) binom(x,l) binom(n-x,j-l).

The coefficient list defines f(x)=sum_j a_j K_j(x). It contains at most n+1
nonnegative integers, a_0>0; trailing zeroes may be omitted. Both checkers require
f(x)<=0 at every integer x from excluded_distance to n and verify the exact
ratio f(0)/a_0 against size_bound. That field is an integer or NUM/DEN string,
not a floating-point number. The ratio must be strictly below q^k.
The conclusion is d <= excluded_distance-1 for a code of size q^k.
Duplicate JSON keys, duplicate IDs and malformed records fail with nonzero exit.

## Why the certificate suffices

For a q-ary code C of size M, the Delsarte inequalities say that the sum over
ordered pairs (u,v) in C of K_j(dist(u,v)) is nonnegative. K_0=1, so

M^2 a_0 <= sum_(u,v) f(dist(u,v)) <= M f(0).

The first inequality uses a_j>=0; the second uses f<=0 off the diagonal when
the minimum distance is at least the excluded distance. Thus M<=f(0)/a_0.
This is the classical theorem, not a new method:
[Delsarte bounds in Sage's reference manual](https://doc.sagemath.org/html/en/reference/coding/sage/coding/delsarte_bounds.html).

A successful check verifies exact finite arithmetic under that theorem. It does
not construct a code, establish optimality, prove novelty, or provide a Lean
formalization or human review. Negative controls test the theorem's hypotheses,
strict size inequality and the input boundary.
