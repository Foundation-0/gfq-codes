# The Delsarte bound run over the GF(7), GF(8) and GF(9) reference tables

**Status: claimed research result.** Every certificate is accepted by five exact checkers, and the entry lists
pass a bookkeeping check. Two of the checkers are the repository's locked ones, two were written with the scan,
and one was written separately for an earlier review. Human review is pending. No code is constructed and no
lower bound changes.

## What is proved

The method is the classical Delsarte linear programming bound, as in
[results/gf7-upper-bounds/PROOF.md](../gf7-upper-bounds/PROOF.md). A certificate is a list of integers
`a_0,...,a_m` with `a_0>0` and `a_j>=0`. It defines `f(x)=sum_j a_j K_j(x)` with `K_j` the Krawtchouk polynomials of
the repository's format ([tools/README.md](../../tools/README.md)). If `f(i)<=0` for every integer `d<=i<=n` and
`f(0)/a_0<q^k`, then no code of length `n` with `q^k` words over `q` symbols has minimum distance `d` or more.
That holds for every such code, linear or not.

**Base entries.** [certificate.json](certificate.json) holds 1,519 certificates (88 for GF(7), 737 for GF(8), 694 for
GF(9)). For each of the 122 base entries below, its certificate shows that no linear `[n,k,d]` code exists over the
field. So the largest minimum distance of a linear `[n,k]` code is at most `d-1`.

| Field | Base entries | Where listed |
|---|---:|---|
| GF(7), length up to 100 | 12 | below and [base_cells.csv](base_cells.csv) |
| GF(8), length up to 130 | 62 | [base_cells.csv](base_cells.csv) |
| GF(9), length up to 130 | 48 | [base_cells.csv](base_cells.csv) |

The 12 GF(7) base entries, written `[n,k,d]` with `d` the excluded distance:
`[55,10,40]`, `[56,12,39]`, `[66,23,38]`, `[74,10,56]`, `[92,8,73]`, `[93,13,69]`, `[94,16,67]`, `[95,18,66]`,
`[98,8,78]`, `[98,11,75]`, `[99,13,74]`, `[100,16,72]`. The first and fourth are the two base facts already in
`results/gf7-upper-bounds` and `results/gf7-n74-k10-upper-d55`. The other ten are not in the repository's earlier results.

**Improved entries.** Write `u(n,k)` for the largest minimum distance a linear code of that length and dimension can
have. Four standard facts bound it from above in terms of neighbours. Each is a one-line construction on a
hypothetical code:

- `u(n,k) <= u(n-1,k)+1`: delete one coordinate (puncture). Distance drops by at most one and dimension is kept when the distance is 2 or more.
- `u(n,k) <= u(n-1,k-1)`: keep the words that are zero in one coordinate, then delete it (shorten).
- `u(n,k) <= u(n,k-1)`: take a subcode of one dimension less.
- `u(n,k) <= u(n+1,k)`: add a coordinate that is always zero.

The scan starts from the upper bounds displayed in the tables, replaces them by the certified bounds, and applies the
four facts until nothing changes. An entry is *improved* when the result is below the displayed upper bound. It is
counted as improved *beyond the table's own consistency* when it is also below what the same four facts give from
the displayed values alone.

| Field | Open entries tested | Improved entries | Of which base |
|---|---:|---:|---:|
| GF(7), length up to 100 | 4,071 | 94 | 12 |
| GF(8), length up to 130 | 7,202 | 1,408 | 62 |
| GF(9), length up to 130 | 7,265 | 916 | 48 |

An entry is open when the displayed lower and upper bounds differ. [improved_cells.csv](improved_cells.csv) lists
every improved entry with its displayed lower and upper bounds, the new upper bound, and whether it is a base entry.
For GF(9) the file has 1,377 rows. In 461 of them the displayed value is above what the table's own neighbours
imply, so no linear programming is needed. They are listed but not counted above. In all, 531 displayed GF(9) entries
are inconsistent with their neighbours in this way, and 70 of them are also improved beyond that.

**The counts are lower limits.** The floating-point search returned no usable answer for 2,464 (GF(7)), 5,132 (GF(8))
and 5,277 (GF(9)) open entries, and these were not pursued. A further 48, 55 and 58 floating-point candidates failed
the exact check and were dropped. Entries outside the length ranges above were not tested.

**What is not proved.** Nothing here shows that an improved entry has no code at the new upper bound, only at the
excluded distance and above. No lower bound is touched. The theorem is used as published and is not formalised.
The table values are those displayed on the date in [sources.json](sources.json). The tables may change.

## Statistics

From [outputs/codes_stats.out](outputs/codes_stats.out), over the entries improved beyond the table's own consistency:

| Field | Gap before | Gap after | Gap closed |
|---|---:|---:|---:|
| GF(7) | 950 | 856 | 9.9% |
| GF(8) | 23,857 | 22,177 | 7.0% |
| GF(9) | 13,213 | 12,209 | 7.6% |

The gap is the displayed upper bound minus the displayed lower bound, summed over those entries. The upper bound
drops by one in all 94 GF(7) entries, by one, two or three in 1,144, 256 and 8 GF(8) entries, and by one or two in
828 and 88 GF(9) entries.

Three entries become settled exactly (upper bound equals lower bound), all over GF(9) ([settled_cells.csv](settled_cells.csv)):
`[31,4]` with distance 25, `[32,4]` with distance 26 and `[72,4]` with distance 62. The first two are the subject of
`results/gf9-n31-k4-upper-d25` and `results/gf9-n32-k4-upper-d26`. The third is not in an earlier result.

## Checks

From the repository root, with Python 3.10 or newer, no network and no optimizer:

```sh
sha256sum -c tools/SHA256SUMS
python3 results/gf789-delsarte-table-scan/verify.py
python3 -O results/gf789-delsarte-table-scan/test_corrupt.py
```

`verify.py` runs, on [certificate.json](certificate.json): the repository's two locked checkers, `verify_certs.py`
(Krawtchouk values by the three-term recurrence), `verify_binomial.py` (the binomial sum),
`delsarte_independent.py` (the separate checker, recurrence form, written for an earlier review of this repository),
and `verify_cells.py`, which checks the entry lists. Saved outputs are in [outputs/](outputs/), with the programs run
under `python -I -O` where they allow it. The verifiers raise an error on failure and use no bare `assert`.

- All 1,519 certificates pass all five exact checkers.
- `test_corrupt.py` changes one certificate five ways (a negative coefficient, a smaller distance, a smaller
  dimension, a halved last coefficient, a wrong declared size bound). Every checker that tests the broken
  condition rejects each one. `verify_binomial.py` does not read the declared size bound, so it does not reject the last.
- `verify_cells.py` checks that every base entry's certificate excludes exactly the distance one above its new bound,
  that the counts above come out of the lists, and that all 18 statements of the repository's other results appear in
  the lists with the same bounds. It is a bookkeeping check. It does not recompute the closure, because the list holds
  only the improved entries.
- [outputs/existing_results_separate_checker.out](outputs/existing_results_separate_checker.out): the 18
  certificates of the other results also pass the separate checker.
- [spot_check_live.py](spot_check_live.py) needs a network. It reads nine base entries chosen by a fixed seed and
  compares the displayed bounds. All nine matched on 15 November 2026 ([outputs/spot_check_live.out](outputs/spot_check_live.out)).

The certificates were found with a floating-point solver and turned into exact rationals. The rationals were then
scaled to integers ([scan/to_integer.py](scan/to_integer.py)). A positive scale leaves the signs and the ratio
`f(0)/a_0` unchanged, and the checks above ran on the integer file.

## Rerun the scan

The scan needs NumPy and SciPy. Save the three whole-table pages from the addresses in [sources.json](sources.json)
as `sources/t7.html`, `t8.html` and `t9.html` in a work folder, copy the files of [scan/](scan/) and
`verify_certs.py` into it, and run:

```sh
python3 parse.py
for q in 7 8 9; do python3 scan2.py $q; python3 build_certs.py $q; done
python3 analyze.py
python3 to_integer.py certificate.json certs/gf7_certs.json certs/gf8_certs.json certs/gf9_certs.json
```

The pages are not stored in this repository. The solver output can differ in the last digits, and the certificates
that result need not be identical to these. The published certificates stand on their exact checks.

## Prior work searched, and what was found

The cell pages of the reference tables say that upper bounds come from the tables of Andries Brouwer, except for GF(7)
above length 50, where "the upper bounds are rather weak", and that Rumen Daskalov provided bounds for small
dimension. They do not name the linear programming bound. Brouwer's bound server is discontinued. Maruta's tables
cover these fields only for dimension 4. Three GF(9) base entries have dimension 4 (one, `[31,4]`, is already a result of this repository). That was not
compared with Maruta's tables. A table of Daskalov cited in a 2004 paper covers dimension 7 and below. All 12 GF(7) base
entries have dimension 8 or more, and 98 of the 122 base entries have dimension above 7.

About ten web queries found no earlier report of `[55,10,40]` or `[74,10,56]` over GF(7). The other base entries were
checked only against the tables and papers named above. Two papers could not be read: Daskalov and Metodieva (2007),
which the repository's earlier note says lists 34 exclusions for GF(7), and Daskalov and Gulliver (2001). The earlier
note's statement about the 2007 list was not re-checked. The finding is therefore "no earlier report found". It is not
a claim of priority, and the method is fifty years old.

## Where this meets earlier results

The earlier GF(7) sweep is described as covering `51<=n<=60`, `k<=12`. Entries `[56,12,39]` and `[57,12,40]` are
inside that range and not in its list. See [NOTE-missed-gf7-entries.md](NOTE-missed-gf7-entries.md).

A draft message to the table maintainer is in [DRAFT-note-to-maintainer-NOT-SENT.md](DRAFT-note-to-maintainer-NOT-SENT.md).
It has not been sent. Under [AGENTS.md](../../AGENTS.md) a person signs before anything goes to the maintainer.
The repository's open issues 3 and 5 are the ones this result touches.

## Credit

Markus Grassl's compilation supplied the comparison data. Delsarte supplied the method.
