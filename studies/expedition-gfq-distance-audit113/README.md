# Pure-$\mathbb{Z}/\mathbb{F}_q/\mathbb{Q}$ Conway-Canonical Lazy Incremental Zimmermann Relative-Rank Distance Certifier (`AUDIT-113`)

An add-only, zero-dependency, zero-float Python 3 stdlib exact minimum-distance certifier and cross-repo verification suite for linear codes over $\mathbb{F}_q$ ($q \in \{2, 3, 4, 5, 7, 8, 9\}$), designed to complement `Foundation-0/gfq-codes` PRs `#9` and `#10` without modifying existing tools or hashes.

## Why This Complements Open PRs `#9` and `#10`

Open PRs `#9` (`8123f058`, brute-force $q^k$ word enumeration) and `#10` (`b1f32e53`, zero-coordinate subspace rank checks over descending $|S|$) provide two genuinely independent exact checkers for small codes, each bounded by a default `1,000,000` budget. Neither uses Brouwer–Zimmermann relative-rank bounds.

Against the `15` best-known codes in `Foundation-0/math0#4` (`best/*.txt`):

| Checker | Algorithm | Default Budget | `math0#4` Codes Certified Within Default Budget | Notes |
|---|---|---:|---:|---|
| PR `#9` (`8123f058`) | Exhaustive $q^k$ words | `1,000,000` words | `14 / 15` | Overflows on `GF(5)[18,9,7]` (`5^9 = 1,953,125` words) |
| PR `#10` (`b1f32e53`) | Zero-coordinate subsets `rank(G[:,S]) < k` | `1,000,000` subsets | `10 / 15` (`5 / 15` strictly `> 1M` before $|S|=n-d$) | Overflows on `GF(3)[23,8,10]`, `[24,9,9]`, `GF(4)[22,6,12]`, `[23,7,11]`, `[24,8,11]` (`>1.27M`–`>4.54M`) |
| `#9` + `#10` pair | Two-checker intersection | `1,000,000` each | `9 / 15` | `6 / 15` exceed at least one checker's default cap |
| **This study (`AUDIT-113`)** | **Lazy incremental Zimmermann relative-rank** | Exact (no float) | **`15 / 15`** | **`14,526` total enumerations** across all `15` codes (`11` strict wins, `4` ties, `0` losses vs. `24,721` naive disjoint BZ; up to `5.197×` fewer enumerations on `GF(5)[17,6,9]`) |

## What Is Included

All files are strictly add-only under `studies/expedition-gfq-distance-audit113/` (zero modifications to `tools/`, `tests/`, `codes/`, `results/`, or `.github/`):

- `gfq_distance_oracle.py` — Pure-$\mathbb{Z}/\mathbb{F}_q/\mathbb{Q}$ Conway-canonical finite fields (`GF(2)` through `GF(9)` matching `codes/README.md:29-30`), lazy incremental Zimmermann relative-rank exact distance certifier, MacWilliams identity verifier in $\mathbb{Q}$, independent exact Krawtchouk Delsarte LP checker, $\mathbb{F}_{2^5}$ binary Goppa primal-shortening checker (`[24,9,7] -> [21,6,7]`), and unambiguous canonical matrix parser.
- `gfq_distance_audit.py` — Reproducible CLI supporting `--standalone` (self-contained offline certification), `--live --intake-dir <dir>` (fail-closed verification against on-disk intake), and `--check <cert.json>` (fail-closed semantic + canonical-digest validator).
- `test_gfq_distance_r5.py` — Assertion-free (`-O`-safe) adversarial & negative-control test suite (`9` tests; `157/157` `100.0%` mutation kill rate on `aletheia v2.0.0 mutate` and `84/84` `100.0%` AST `BoolOp` kill rate).
- `gfq_distance_certificate.json` — Frozen canonical JSON certificate (strict `str`-key canonical formatting, zero floats).
- `GFQ_DISTANCE_AUDIT_REPORT.md` — Detailed mathematical audit report covering all three pillars, Conway vs. non-Conway `GF(9)` `36/81` multiplication-table contrast, all `4/4` `GF(7)` Delsarte upper-bound certificates (`[55,10,40]`, `[56,10,41]`, `[56,11,40]`, `[57,11,41]`), and all `15/15` `math0#4` exact distance certifications.

## Exact Offline Replay (Python 3.10+ Stdlib Only)

```bash
# 1. Self-contained offline certification (deterministic across -I -B, -I -O -B, -I -B -W error)
python3 -I -B -W error studies/expedition-gfq-distance-audit113/gfq_distance_audit.py --standalone --json

# 2. Fail-closed semantic & digest verification of the committed certificate
python3 -I -B -W error studies/expedition-gfq-distance-audit113/gfq_distance_audit.py --check studies/expedition-gfq-distance-audit113/gfq_distance_certificate.json

# 3. Assertion-free adversarial & negative-control suite (9/9 OK under -I -O -B -W error)
python3 -I -O -B -W error studies/expedition-gfq-distance-audit113/test_gfq_distance_r5.py
```

## Scope & Governance

- **Add-only research study:** Does not alter `tools/SHA256SUMS`, `tools/check_bound*.py`, or `codes/`.
- **Honest novelty classification:** Classical mathematical prior art (`N0`: Conway polynomials, Brouwer–Zimmermann 1996 / Grassl 2006, MacWilliams 1963, Delsarte 1973, Goppa 1970) packaged as an independent zero-float stdlib Checker #2 bridge (`N1`) with full negative-control and mutation coverage.
