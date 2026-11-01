# Delsarte upper bound for [75,11] over GF(7)

**Status: claimed research result** — exact Delsarte LP certificate with dual integer
coefficients; **VERIFIED** by both locked checkers in this repository. Human review pending.

## Statement (would lower codetables.de on 2026-10-31)

| Quantity | Value |
|---|---:|
| Field GF(7) | length 75, dimension 11 |
| Displayed lower bound (Grassl) | 48 |
| Displayed upper bound (Grassl) | 56 |
| **Upper bound established here** | **55** |
| Excluded minimum distance | 56 (no linear [75,11,56] code) |

Source entry: [https://www.codetables.de/BKLC/BKLC.php?q=7&n=75&k=11](https://www.codetables.de/BKLC/BKLC.php?q=7&n=75&k=11) (retrieved 2026-10-31 UTC; see sources.json).

## Method

**KNOWN** (Delsarte, 1973): non-negative Krawtchouk combination with nonpositive values on
{d_ex,…,75} and code-size ratio below 7^11 excludes minimum distance ≥ 56.
See [tools/README.md](../../tools/README.md) and [results/gf7-upper-bounds/PROOF.md](../gf7-upper-bounds/PROOF.md).

Discovery on this cell used SciPy HiGHS on the normalized LP in the GF(7) write-up, then
contact-point exactification to integer `krawtchouk_coefficients` in [certificate.json](certificate.json).

## Replay

```sh
sha256sum -c tools/SHA256SUMS
python3 tools/check_bound.py results/gf7-n75-k11-upper-d55/certificate.json
python3 tools/check_bound_independent.py results/gf7-n75-k11-upper-d55/certificate.json
python3 results/gf7-n75-k11-upper-d55/verify.py
```

## Prior art searched (2026-10-31)

- codetables.de entry https://www.codetables.de/BKLC/BKLC.php?q=7&n=75&k=11
- results/gf7-upper-bounds/PROOF.md Daskalov–Metodieva 2007 Thm 2.2 (GF(7) LP list)
- Repository README and notes/scouting.md for per-field bound references
- Grassl table note: GF(7) n>50 upper bounds partly from Rumen Daskalov

- **Daskalov–Metodieva (2007), Theorem 2.2 (GF(7) LP list):** **VERIFIED** against the
  author PDF preview on 2026-10-31 — `[75,11,56]_7` is **not** among the 34 listed
  nonexistent codes when q=7; for q≠7 this theorem does not apply directly.
- **Grassl / Brouwer note on GF(9):** **KNOWN** — entry pages state upper bounds are mostly
  from Brouwer’s tables (as of 2007-02-13 on the pages read); stale display vs classical LP
  is possible; no entry-specific proof of bound 55 was found on the page.
- **Grassl entry note:** upper bound provenance as quoted on the entry page; no entry-specific
  citation of an LP bound of 55 on 2026-10-31.
- No claim of priority or exhaustive literature coverage.

## Credit

Markus Grassl's codetables.de supplied comparison data. Certificate found by automated sweep
(`scripts/delsarte_sweep.py`) on branch `axiom/delsarte-sweep`. AI agent for Alkindus; human sign-off pending.
