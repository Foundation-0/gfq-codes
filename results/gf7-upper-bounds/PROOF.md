# One exact upper bound and four GF(7) table improvements

**Status: claimed research result, with a written argument and exact finite certificates; human review is pending.**
The method is classical Delsarte linear programming. The contribution is a small, replayable certificate
that excludes a linear `[55,10,40]` code over GF(7), together with three consequences for nearby parameters.
It improves four upper bounds displayed by codetables.de on **25 October 2026**. It does not construct a code,
close any of these four gaps, establish a new bounding method, or establish that these numerical consequences
have never appeared elsewhere.

## Statement and table comparison

Write `d_7(n,k)` for the largest minimum distance of a linear length-`n`, dimension-`k` code over GF(7).

| Parameters | Displayed lower bound | Displayed upper bound | Upper bound established here | Source |
|---|---:|---:|---:|---|
| `[55,10]` | 34 | 40 | **39** | [Grassl entry](https://www.codetables.de/BKLC/BKLC.php?q=7&n=55&k=10) |
| `[56,10]` | 35 | 41 | **40** | [Grassl entry](https://www.codetables.de/BKLC/BKLC.php?q=7&n=56&k=10) |
| `[56,11]` | 34 | 40 | **39** | [Grassl entry](https://www.codetables.de/BKLC/BKLC.php?q=7&n=56&k=11) |
| `[57,11]` | 34 | 41 | **40** | [Grassl entry](https://www.codetables.de/BKLC/BKLC.php?q=7&n=57&k=11) |

The lower bounds are quoted from Markus Grassl's compilation, not re-proved here. The four entry pages
were read directly; retrieval times, response hashes and displayed modification dates are in
[sources.json](sources.json). A response hash identifies the bytes read but does not make a mutable URL
an archive. The full tables and source pages are not redistributed.

## The classical bound used

For alphabet size `q=7`, define the unnormalized Krawtchouk polynomials by

\[
K_j^{(n,7)}(x)=\sum_{r=0}^{j}(-1)^r6^{j-r}
\binom{x}{r}\binom{n-x}{j-r}.
\]

For integer `x` outside a binomial coefficient's range, that coefficient is zero. In particular,
`K_0(x)=1` and `K_j(0)=6^j binom(n,j)`.

**Known theorem (Delsarte).** Suppose
`f(x)=sum_j a_j K_j(x)`, with `a_0>0`, all `a_j>=0`, and `f(i)<=0` for every integer `d<=i<=n`.
Then any seven-symbol length-`n` code with minimum distance at least `d` has size at most `f(0)/a_0`.
Consequently, if that ratio is smaller than `7^k`, there is no linear `[n,k,d]` code.

For completeness, the positivity underlying this application can be seen directly. For a nonempty
code `C`, put `A_i=|{(u,v) in C^2: dist(u,v)=i}|/|C|`. Then `A_0=1`, `sum_i A_i=|C|`,
and `A_i=0` for `0<i<d`. Let `omega` be a primitive seventh root of unity. Character orthogonality gives

\[
\sum_i A_i K_j(i)=\frac1{|C|}
\sum_{\substack{z\in\mathbf F_7^n\\\mathrm{wt}(z)=j}}
\left|\sum_{u\in C}\omega^{z\cdot u}\right|^2\ge0.
\]

Indeed, expanding the square gives a sum over ordered pairs; each nonzero coordinate of `u-v`
contributes `-1` when the corresponding character is summed, and each zero coordinate contributes `6`.
Collecting weight-`j` characters yields the displayed Krawtchouk polynomial. Therefore
`a_0 |C| <= sum_i A_i f(i) <= f(0)`, which proves the bound used here. This argument does not require
the code to be linear; linearity is used only for the size `7^k`.

The original source is P. Delsarte, *An algebraic approach to the association schemes of coding theory*,
Philips Research Reports Supplements, No. 10 (1973): theorem 3.8 and the bound in section 3.3.2,
printed page 31, with Hamming schemes treated in section 4.1
([primary text, PDF page 20](https://users.wpi.edu/~martin/RESEARCH/philips.pdf#page=20)).

## Explicit certificate for the base bound

Set `n=55`. Take these coefficients in the **unnormalized** Krawtchouk basis, starting at degree zero:

```text
[3582480, 2011428, 438976, 87849, 13572, 1770, 160, 10]
```

Every coefficient is positive. Exact polynomial expansion gives

\[
f(x)=\frac{117649}{72}(40-x)
(44-x)(45-x)(48-x)(49-x)(52-x)(53-x).
\]

For every integer `x>=40`, the first factor is nonpositive. Each other consecutive pair is nonnegative
at every integer, so `f(x)<=0` throughout the required range `40,...,55`. Further,

\[
\frac{f(0)}{a_0}
=\frac{838875394156800}{3582480}
=\frac{317755831120}{1357}
< 7^{10}=282475249.
\]

The strict inequality is an integer comparison:
`3582480 * 282475249 - 838875394156800 = 173086535880720 > 0`.
Thus a linear length-55, dimension-10 code cannot have minimum distance 40 or greater, proving
`d_7(55,10)<=39`.

## The other three parameter pairs

These are consequences of the base bound, not three independent advances.

1. If a linear `[56,10]` code had distance at least 41, puncturing one coordinate would preserve its
   dimension (no weight-one word can exist) and leave distance at least 40. That contradicts the base bound.
2. A linear `[56,11]` code has a coordinate on which projection is nonzero. Restricting that coordinate
   to zero gives a dimension-10 subcode. Deleting that zero coordinate leaves length 55 and does not lower
   distance. Thus distance at least 40 would again contradict the base bound.
3. Puncturing a hypothetical `[57,11]` code of distance at least 41 gives a `[56,11]` code of distance
   at least 40, excluded by the preceding step.

For replay without relying on those transformations, [certificate.json](certificate.json) also includes
direct polynomial certificates for all four entries:

| Length | Dimension excluded | Minimum distance excluded | Exact upper bound on code size |
|---:|---:|---:|---|
| 55 | 10 | 40 | `317755831120/1357` |
| 56 | 10 | 41 | `21608924188425/136361` |
| 56 | 11 | 40 | `2224290817840/1357` |
| 57 | 11 | 41 | `151262469318975/136361` |

All four ratios are strictly smaller than `7^k`. The length-56, dimension-10 direct polynomial has
the seven base roots each increased by one. The two dimension-11 certificates have degree eight.
The checkers evaluate every required integer argument exactly, so the written factorization is not
a substitute for machine verification.

## Replay and what was searched

From the repository root, with Python 3.10 or newer:

```sh
sha256sum -c tools/SHA256SUMS
python3 tools/check_bound.py results/gf7-upper-bounds/certificate.json
python3 tools/check_bound_independent.py results/gf7-upper-bounds/certificate.json
python3 -m unittest discover -s tests -v
```

Verification needs only the Python standard library and does not fetch tables or invoke an optimizer.
The coefficient integers are the certificate; no floating-point solver outcome is trusted.

Discovery used a bounded exploratory sweep of the live GF(7) table for `51<=n<=60`, `k<=12`:
81 open entries were tested at their displayed upper distance, yielding four candidate exclusions.
The other 77 attempts produced no such candidate; that does not establish their bounds or feasibility.
The LP minimized `1+sum_j g_j` subject to
`1+sum_j g_j K_j(i)/K_j(0)<=0` for every `i>=d` and `g_j>=0`.
The exploratory environment used NumPy 2.3.5 and SciPy 1.17.0 with `linprog(method="highs")`.
Initial rounded rational candidates passed an exact sign check; contact points were then used to solve
for exact coefficients, clear denominators and remove a common factor, producing the small integers
committed here. Exploratory solver files are not necessary to reproduce the asserted bounds.

This differs from [math0 PR #4](https://github.com/Foundation-0/math0/pull/4), which searched for
better lower-bound constructions over GF(3), GF(4) and GF(5) and explicitly did no upper-bound work.

## Prior art and limits

- **Known method:** Delsarte's theorem above. [SageMath's documented implementation](https://doc.sagemath.org/html/en/reference/coding/sage/coding/delsarte_bounds.html)
  already computes general Delsarte bounds and gives the same Krawtchouk convention. SageMath was consulted
  as a reference, not executed here.
- **Earlier seven-ary work:** R. Daskalov and E. Metodieva, *Minimum distance bounds for 7-ary linear codes*,
  Fifth International Workshop on Optimal Codes and Related Topics (2007), pp. 62–67,
  [author-uploaded primary text](https://www.researchgate.net/publication/264553328_Minimum_distance_bounds_for_7-ary_linear_codes),
  DOI `10.13140/2.1.3975.4883`. Theorem 2.2 lists 34 LP exclusions in the same length range;
  none is one of these four parameter triples. That absence is not an exhaustive novelty result.
- **Search scope:** exact-parameter web searches, the live Grassl entries, the 2007 paper and Foundation0's
  existing code work were checked on 25 October 2026. No claim of priority or exhaustive literature coverage
  is made. A stronger or equivalent bound may exist elsewhere; the displayed table comparison is the
  limited, directly checked improvement.
- **Status:** exact arithmetic checks are finite verifications of the certificates; the theorem application
  is the written argument above. This is not a Lean formalization or a peer-reviewed result. A shared
  conceptual mistake could survive two implementations, so independent mathematical review remains useful.
- **Outstanding:** the known lower bounds remain below the new upper bounds. No optimum is established,
  no code has been constructed, and nobody has contacted Grassl or submitted a table change.

## Credit

Markus Grassl's compilation supplied the comparison data; Delsarte supplied the method. OpenAI Codex
(GPT-6), working for Ahraz Arifuddin (@ahrazzle), performed the exploration, exact certificate construction,
writing and independent AI checks. Human review and sign-off are pending.
