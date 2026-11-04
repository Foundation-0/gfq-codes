# Delsarte upper bound for [31,4] over GF(9)

**Status: claimed research result** — exact Delsarte LP certificate with dual integer
coefficients; **VERIFIED** by both locked checkers in this repository. Human review pending.

## Statement (would lower codetables.de on 2026-10-31)

| Quantity | Value |
|---|---:|
| Field GF(9) | length 31, dimension 4 |
| Displayed lower bound (Grassl) | 25 |
| Displayed upper bound (Grassl) | 26 |
| **Upper bound established here** | **25** |
| Excluded minimum distance | 26 (no linear [31,4,26] code) |

Source entry: [https://www.codetables.de/BKLC/BKLC.php?q=9&n=31&k=4](https://www.codetables.de/BKLC/BKLC.php?q=9&n=31&k=4) (retrieved 2026-10-31 UTC; see sources.json).

## Method

**KNOWN** (Delsarte, 1973): non-negative Krawtchouk combination with nonpositive values on
{d_ex,…,31} and code-size ratio below 9^4 excludes minimum distance ≥ 26.
See [tools/README.md](../../tools/README.md) and [results/gf7-upper-bounds/PROOF.md](../gf7-upper-bounds/PROOF.md).

Discovery on this cell used SciPy HiGHS on the normalized LP in the GF(7) write-up, then
contact-point exactification to integer `krawtchouk_coefficients` in [certificate.json](certificate.json).

## Replay

```sh
sha256sum -c tools/SHA256SUMS
python3 tools/check_bound.py results/gf9-n31-k4-upper-d25/certificate.json
python3 tools/check_bound_independent.py results/gf9-n31-k4-upper-d25/certificate.json
python3 results/gf9-n31-k4-upper-d25/verify.py
```

## Relation to neighbouring entries

**PROVEN** (standard): the other eleven GF(9) entries in this family follow from this one by alternately
puncturing (a [n+1,k,d+1] code gives [n,k,d]) and shortening (a [n+1,k+1,d] code gives [n,k,d]). Each
entry still carries its own certificate.

## Prior art searched (2026-10-31)

- codetables.de entry https://www.codetables.de/BKLC/BKLC.php?q=9&n=31&k=4
- Repository README and notes/scouting.md for per-field bound references

- **Daskalov–Metodieva (2007), Theorem 2.2:** lists GF(7) codes only, so it does not
  apply to this GF(9) entry.
- **Grassl / Brouwer note on GF(9):** **KNOWN** — entry pages state upper bounds are mostly
  from Brouwer’s tables (as of 2007-02-13 on the pages read); stale display vs classical LP
  is possible; no entry-specific proof of bound 25 was found on the page.
- **Grassl entry note:** upper bound provenance as quoted on the entry page; no entry-specific
  citation of an LP bound of 25 on 2026-10-31.
- No claim of priority or exhaustive literature coverage.

## Credit

Markus Grassl's codetables.de supplied comparison data. Certificate found by automated sweep
(`scripts/delsarte_sweep.py`) on branch `axiom/delsarte-sweep`. AI agent for Alkindus; human sign-off pending.
