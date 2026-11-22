# Track S16 (`AUDIT-113`): Pure-$\mathbb{Z}/\mathbb{F}_q/\mathbb{Q}$ Conway-Canonical Zimmermann Relative-Rank Minimum-Distance Certifier (`Foundation-0/gfq-codes` & `math0#3/#4`)

- **Audit ID:** `AUDIT-113` (Continuous-Flow Track S16)
- **Arithmetic & Governance Standard:** Aletheia v2.0.0 — 100% pure Python 3 stdlib (`int` & `fractions.Fraction`), **zero floats**, **zero NumPy**, **zero bare `assert`s**, zero shared code with `Foundation-0/math0#3/#4` or `Foundation-0/gfq-codes`, strict `str`-key canonical JSON (exact JSON-roundtrip SHA-256 invariance), and zero external writes.
- **Novelty Classification (Law 4 Honest Default):**
  - **`N0` (Classical Prior Art & Upstream Artifacts):** Conway polynomials over $\mathbb{F}_q$ (Luebeck / Magma / GAP / Sage), Brouwer–Zimmermann relative-rank minimum-distance bounds (Zimmermann 1996; Grassl 2006), MacWilliams identity (MacWilliams 1963), Delsarte linear-programming bound (Delsarte 1973), ternary Golay `[11,6,5]`/`[12,6,6]` and binary Goppa codes (Goppa 1970), plus upstream artifacts from `Foundation-0/gfq-codes @ 9200a06b`, `Foundation-0/math0#3 @ d94ad5d4`, `Foundation-0/math0#4 @ 98bdb872`, and `AUDIT-109` (`MiniMax-AI/Research` `TII-McEliece`).
  - **`N1` (Independent Checker #2 & Cross-Repo Exact Operator Bridge):** Zero-float stdlib lazy incremental Zimmermann relative-rank exact distance certifier that strictly dominates naive disjoint full-rank enumeration across all `15/15` `math0#4` `best/*.txt` matrices (`11` strict wins, `4` ties, `0` losses) and ternary Golay (`72` vs. `236`, `59/18 = 3.278×`), bridges `Foundation-0/gfq-codes`'s Law-1b open PR landscape (`#9` brute force & `#10` coordinate subspaces, neither using Zimmermann relative-rank), independently verifies all `4/4` `gfq-codes` `GF(7)` Delsarte upper-bound certificates via exact Krawtchouk polynomials, certifies exact $\mathbb{F}_{2^5}$ binary Goppa primal-shortening monotonicity (`[24,9,7] -> [21,6,7]`), and proves an unambiguous canonical matrix parser closing all `math0#3/#4` parser defects.

---

## 1. Law-1b Portal Intake (`Foundation-0/gfq-codes` & `Foundation-0/math0#3/#4`)

All `26` pinned primary-source files (`11` from `Foundation-0/gfq-codes @ 9200a06be239d6cc70ec94ed82f681e75b9bc718` + `15` `best/*.txt` generator matrices from `Foundation-0/math0#4 @ 98bdb8727b180f62c0a8e77b8fdcc659e3b0bd38`) are staged read-only in sibling `../intake-gfq-codes/`.

- **Law-1b Open Unmerged-PR Discovery on `Foundation-0/gfq-codes` (`6` open PRs, `5` open issues):**
  - `main @ 9200a06b` currently ships **only** the two independent Delsarte upper-bound checkers (`tools/check_bound.py`, `tools/check_bound_independent.py`; `tools/SHA256SUMS` `2/2 OK`) and `GF(7)`/`GF(9)` upper-bound certificates (`codes/` has only `README.md`).
  - Open PRs **`#9 @ 8123f058`** (brute-force $q^k$ enumeration) and **`#10 @ b1f32e53`** (zero-coordinate subspace enumeration) implement two distance checkers (`APPROVED` by `@orda-aska`, unmerged), alongside `#11 @ 42863db3`, `#13 @ d12113e2`, `#14 @ 492234f3`, and `#19 @ 7310a39e` (unreviewed `GF(7)/GF(8)/GF(9)` Delsarte table scan). **Neither `#9` nor `#10` uses Brouwer–Zimmermann or Zimmermann relative-rank bounds**, leaving a direct high-rate scalability gap (`k > n/2` or large $q^k$) that `AUDIT-113` fills cleanly in pure stdlib Python.
- **Dual-Mode Provenance Boundary (`--live` vs. `--standalone` vs. `--check`):**
  - `--live --intake-dir ../intake-gfq-codes`: fail-closed verifies all `26/26` on-disk files (non-symlink, path-containment, exact byte lengths and SHA-256s, live `tools/SHA256SUMS` verification, live JSON and matrix parsing) and emits `execution_mode = "live_portal_intake"`, `live_portal_verified = true`.
  - `--standalone` (default): recomputes all three pure-$\mathbb{Z}/\mathbb{F}_q/\mathbb{Q}$ pillars live from scratch while replaying the pinned portal manifest (`execution_mode = "standalone_pinned_manifest"`, `live_portal_verified = false`), producing the **exact same `payload_sha256`**.
  - `--check <cert.json>`: fail-closed semantic + canonical-digest validator rejecting floats, non-`str` keys, all-zero SHAs, non-canonical JSON formatting, or any tampered payload even if re-signed.

---

## 2. Three Certified Pure-$\mathbb{Z}/\mathbb{F}_q/\mathbb{Q}$ Pillars

### Pillar 1 — Conway-Canonical Finite Fields $\mathbb{F}_q$ ($q \in \{2,3,4,5,7,8,9\}$)
- Exhaustively verifies all ring/field axioms (identity, commutativity, associativity, distributivity, inverses, and cyclic multiplicative group of order $q - 1$) across all `7` fields with strict `type(x) is int` enforcement (`bool` and `float` rejected).
- **Exact Conway $\mathbb{F}_9$ Contrast (`Foundation-0/gfq-codes/codes/README.md:29-30` vs. `math0#3` `gfq/field.py:21`):**
  - Conway modulus $x^2 + 2x + 2$ (`[2, 2, 1]`): $x^2 = x + 1$ (`mul(3, 3) = 4`), $\mathrm{ord}(x) = 8$ (primitive element `3`).
  - `math0#3` modulus $x^2 + 1$ (`[1, 0, 1]`): $x^2 = 2$ (`mul(3, 3) = 2`), $\mathrm{ord}(x) = 4$ (non-primitive; smallest primitive element `4`).
  - Identical addition tables (`0 / 81` mismatches) but **`36 / 81` multiplication-table mismatches** on the exact same base-3 digit encoding — demonstrating quantitatively why `math0#3` must adopt Conway `[2, 2, 1]` before landing in `gfq-codes`.

### Pillar 2 — Lazy Incremental Zimmermann Relative-Rank Certifier, `15/15` `math0#4` Codes, MacWilliams Duality & `GF(7)` Delsarte Verification
- **Exact Lazy Incremental Zimmermann Bound:** Given systematic forms $(R_1, P_1, k_1), \dots, (R_m, P_m, k_m)$ sorted by descending disjoint unused-column relative rank $k_j = |P_j \cap U_j|$ ($U_j$ pairwise disjoint) and per-matrix completed weight level $s_j \ge 0$, every unseen nonzero codeword $c$ satisfies:
  $$\mathrm{wt}(c) \;\ge\; \sum_{j=1}^{m} \max\!\big(0,\; (s_j + 1) - (k - k_j)\big).$$
  This holds identically at $s_j = 0$ (where full-rank blocks $k_j = k$ contribute $1$ immediately and partial blocks $k_j < k$ contribute $0$) and activates partial blocks only when $s \ge k - k_j$, stopping immediately once $\mathrm{lb} \ge \mathrm{ub}$.
- **Exact Classical Witnesses:**
  - **Ternary Golay `[11, 6, 5]` (`2k = 12 > 11`):** `relative_ranks = [6, 5]`, `done_s = [2, 2]`, **`72` enumerations vs. `236` naive disjoint BZ (`59/18 = 3.278×` reduction)** and `364` brute force (`5.056×`).
  - **Extended Ternary Golay `[12, 6, 6]`:** `relative_ranks = [6, 6]`, `72` enumerations.
  - **Hamming `GF(4)[21, 18, 3]`:** `relative_ranks = [18, 3]`, `477` enumerations (vs. $4^{18} = 68.7\text{B}$ brute force).
- **All `15/15` `math0#4` `best/*.txt` Codes Independently Certified Exact:**
  - **`15/15` exact** (`q=3`: `[22,8,9]`, `[23,8,10]`, `[23,9,9]`, `[24,9,9]`, `[24,10,8]`; `q=4`: `[19,8,8]`, `[20,9,7]`, `[22,6,12]`, `[23,7,11]`, `[24,8,11]`; `q=5`: `[16,5,9]`, `[16,6,8]`, `[17,6,9]`, `[17,7,8]`, `[18,9,7]`).
  - **Strict Dominance Over Naive Disjoint BZ:** **`11` strict wins, `4` ties, `0` losses** — **`14,526` vs. `24,721` total enumerations (`24721/14526 = 1.7018×` aggregate speedup; up to `2692/518 = 1346/259 = 5.197×` on `GF(5)[17,6,9]` and `2994/1650 = 499/275 = 1.815×` on `GF(5)[18,9,7]`)**.
- **Exact MacWilliams Identity (`GF(3)` Golay `[11, 6, 5]` vs. Dual `[11, 5, 6]`):** Verifies $B_j = 3^{-6} \sum_i A_i K_j^{(11,3)}(i)$ identically in $\mathbb{Q}$ for all $j = 0, \dots, 11$ (`A = {0:1, 5:132, 6:132, 8:330, 9:110, 11:24}`, `B = {0:1, 6:132, 9:110}`).
- **Independent Pure-$\mathbb{Z}/\mathbb{Q}$ Verification of All `4/4` `Foundation-0/gfq-codes` `GF(7)` Delsarte LP Certificates:**
  - `[55, 10, 40]` excluded (`317755831120/1357 < 7^{10}`, exact integer slack `173,086,535,880,720 > 0`)
  - `[56, 10, 41]` excluded (`21608924188425/136361 < 7^{10}`, slack `760,935,745,820,880 > 0`)
  - `[56, 11, 40]` excluded (`2224290817840/1357 < 7^{11}`, slack `13,569,984,413,048,448 > 0`)
  - `[57, 11, 41]` excluded (`151262469318975/136361 < 7^{11}`, slack `60,722,672,516,506,224 > 0`)
  - Negative control (testing `excluded_distance = 39` on `[55, 10]` with the same polynomial) fails closed.

### Pillar 3 — Law-5 Bridge (`AUDIT-109` $\mathbb{F}_{2^5}$ Binary Goppa Shortening & Canonical Matrix Parser)
- **Exact Binary Goppa $(24, 5, 3, 9)$ & Primal Shortening (`[24, 9, 7] -> [21, 6, 7]`):** Constructed from scratch over $\mathbb{F}_{2^5} = \mathbb{F}_2[x]/(x^5+x^2+1)$ with $g(X) = X^3 + X^2 + \alpha X + 1$. Zimmermann certifies `[24, 9, 7]` (`relative_ranks = [9, 9, 6]`, `174` enumerations, `13` weight-`7` codewords); primal shortening on coordinates `[21, 22, 23]` produces `[21, 6, 7]` (`relative_ranks = [6, 6, 6, 3]`, `33` enumerations, `6` weight-`7` codewords) with verified distance monotonicity $d_{\text{short}} = 7 \ge d = 7$ and exact parent-subcode containment.
- **Canonical Unambiguous Matrix Parser (`parse_matrix_canonical`):** Closes all `math0#3/#4` parser defects simultaneously — preserving bracketed `[1,2]\n[0,1]\n` (rank `2`), unbracketed `GF(4)` `1 2 3\n0 1 0\n0 0 1\n` (rank `3`), single-row compact `"20121\n"` (len `5`), valid `GF(5)` `k n` header `"2 3\n1 0 1\n0 1 2\n"` (2 rows), valid `GF(3)` `q k n` header `"3 2 3\n1 0 2\n0 1 1\n"` (2 rows), and exact failing-line reporting (`line 1: 'a b c d'`, never the leaked last line).

---

## 3. Reproduction Commands

```bash
# 1. Offline standalone certification (4-mode -I deterministic parity)
python3 -I -B -W error symbiosis/stream/track-s16-gfq-distance-certifier/gfq_distance_audit.py --standalone --json

# 2. Live on-disk intake certification against sibling read-only intake-gfq-codes/
python3 -I -B -W error symbiosis/stream/track-s16-gfq-distance-certifier/gfq_distance_audit.py --live --intake-dir symbiosis/stream/intake-gfq-codes --output symbiosis/stream/track-s16-gfq-distance-certifier/gfq_distance_certificate.json

# 3. Fail-closed semantic & digest check of the frozen certificate
python3 -I -B -W error symbiosis/stream/track-s16-gfq-distance-certifier/gfq_distance_audit.py --check symbiosis/stream/track-s16-gfq-distance-certifier/gfq_distance_certificate.json

# 4. Assertion-free R5 adversarial & mutation-killing test suite
python3 -I -O -B -W error symbiosis/stream/track-s16-gfq-distance-certifier/test_gfq_distance_r5.py
```
