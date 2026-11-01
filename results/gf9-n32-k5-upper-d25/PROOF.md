# Delsarte upper bound for [32,5] over GF(9)

**Status: claimed research result** — exact Delsarte LP certificate with dual integer
coefficients; **VERIFIED** by both locked checkers in this repository. Human review pending.

## Statement (would lower codetables.de on 2026-10-31)

| Quantity | Value |
|---|---:|
| Field GF(9) | length 32, dimension 5 |
| Displayed lower bound (Grassl) | 24 |
| Displayed upper bound (Grassl) | 26 |
| **Upper bound established here** | **25** |
| Excluded minimum distance | 26 (no linear [32,5,26] code) |

Source entry: [https://www.codetables.de/BKLC/BKLC.php?q=9&n=32&k=5](https://www.codetables.de/BKLC/BKLC.php?q=9&n=32&k=5) (retrieved 2026-10-31 UTC; see sources.json).

## Method

**KNOWN** (Delsarte, 1973): non-negative Krawtchouk combination with nonpositive values on
{d_ex,…,32} and code-size ratio below 9^5 excludes minimum distance ≥ 26.
See [tools/README.md](../../tools/README.md) and [results/gf7-upper-bounds/PROOF.md](../gf7-upper-bounds/PROOF.md).

Discovery on this cell used SciPy HiGHS on the normalized LP in the GF(7) write-up, then
contact-point exactification to integer `krawtchouk_coefficients` in [certificate.json](certificate.json).

## Replay

```sh
sha256sum -c tools/SHA256SUMS
python3 tools/check_bound.py results/gf9-n32-k5-upper-d25/certificate.json
python3 tools/check_bound_independent.py results/gf9-n32-k5-upper-d25/certificate.json
python3 results/gf9-n32-k5-upper-d25/verify.py
```

## Prior art searched (2026-10-31)

- codetables.de entry https://www.codetables.de/BKLC/BKLC.php?q=9&n=32&k=5
- results/gf7-upper-bounds/PROOF.md Daskalov–Metodieva 2007 Thm 2.2 (GF(7) LP list)
- Repository README and notes/scouting.md for per-field bound references

- **Daskalov–Metodieva (2007), Theorem 2.2 (GF(7) LP list):** **VERIFIED** against the
  author PDF preview on 2026-10-31 — `[32,5,26]_9` is **not** among the 34 listed
  nonexistent codes when q=7; for q≠7 this theorem does not apply directly.
- **Grassl / Brouwer note on GF(9):** **KNOWN** — entry pages state upper bounds are mostly
  from Brouwer’s tables (as of 2007-02-13 on the pages read); stale display vs classical LP
  is possible; no entry-specific proof of bound 25 was found on the page.
- **Grassl entry note:** upper bound provenance as quoted on the entry page; no entry-specific
  citation of an LP bound of 25 on 2026-10-31.
- No claim of priority or exhaustive literature coverage.

## Credit

Markus Grassl's codetables.de supplied comparison data. Certificate found by automated sweep
(`scripts/delsarte_sweep.py`) on branch `axiom/delsarte-sweep`. AI agent for Alkindus; human sign-off pending.
