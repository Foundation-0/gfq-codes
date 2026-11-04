# Delsarte upper bound for [34,7] over GF(9)

**Status: claimed research result** — exact Delsarte LP certificate with dual integer
coefficients; **VERIFIED** by both locked checkers in this repository. Human review pending.

## Statement (would lower codetables.de on 2026-10-31)

| Quantity | Value |
|---|---:|
| Field GF(9) | length 34, dimension 7 |
| Displayed lower bound (Grassl) | 23 |
| Displayed upper bound (Grassl) | 26 |
| **Upper bound established here** | **25** |
| Excluded minimum distance | 26 (no linear [34,7,26] code) |

Source entry: [https://www.codetables.de/BKLC/BKLC.php?q=9&n=34&k=7](https://www.codetables.de/BKLC/BKLC.php?q=9&n=34&k=7) (retrieved 2026-10-31 UTC; see sources.json).

## Method

**KNOWN** (Delsarte, 1973): non-negative Krawtchouk combination with nonpositive values on
{d_ex,…,34} and code-size ratio below 9^7 excludes minimum distance ≥ 26.
See [tools/README.md](../../tools/README.md) and [results/gf7-upper-bounds/PROOF.md](../gf7-upper-bounds/PROOF.md).

Discovery on this cell used SciPy HiGHS on the normalized LP in the GF(7) write-up, then
contact-point exactification to integer `krawtchouk_coefficients` in [certificate.json](certificate.json).

## Replay

```sh
sha256sum -c tools/SHA256SUMS
python3 tools/check_bound.py results/gf9-n34-k7-upper-d25/certificate.json
python3 tools/check_bound_independent.py results/gf9-n34-k7-upper-d25/certificate.json
python3 results/gf9-n34-k7-upper-d25/verify.py
```

## Relation to neighbouring entries

**PROVEN** (standard): this bound also follows from `results/gf9-n31-k4-upper-d25/` (no [31,4,26] code over
GF(9)) by a chain of puncturing and shortening steps. The certificate here is an independent second route.

## Prior art searched (2026-10-31)

- codetables.de entry https://www.codetables.de/BKLC/BKLC.php?q=9&n=34&k=7
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
