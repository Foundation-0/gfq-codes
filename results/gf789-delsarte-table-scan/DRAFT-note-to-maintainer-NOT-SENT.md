# DRAFT. NOT SENT.

This is a draft for the owners of the repository. It has not been sent to anyone. Under [AGENTS.md](../../AGENTS.md),
a person signs before anything goes to the table maintainer, and the repository's open issue 5 tracks the contact.
The sender line is left empty on purpose. The link near the end works only after this result is merged.

---

Subject: Delsarte LP upper bounds that tighten some entries for q = 7, 8, 9

Dear Dr. Grassl,

I checked the upper bounds in your tables for GF(7) (n up to 100), GF(8) and GF(9) (n up to 130) against the plain Delsarte linear programming bound. Your pages were read on 15 November 2026. For some entries the bound excludes the displayed upper distance, so the upper bound can drop by one or more.

What I found, as a lower limit (my search missed entries where the floating-point solver gave no usable answer):

- GF(7): 12 entries where the bound is new at that entry, and 82 more that follow by puncturing, shortening and taking subcodes. Examples: no linear [55,10,40], [56,12,39], [66,23,38], [74,10,56] and [92,8,73] code over GF(7).
- GF(8): 62 such entries and 1,346 that follow.
- GF(9): 48 such entries and 1,329 that follow. In 461 of the 1,377 GF(9) entries, the displayed value is already above what your own neighbouring values imply. After applying those rules to your values, 916 entries still improve.

Each base entry has an exact certificate: a polynomial in the Krawtchouk basis with a_0 > 0, a_j >= 0, f(i) <= 0 for d <= i <= n, and f(0)/a_0 < q^k. The certificate files hold the coefficients as exact integers.

Three short Python programs that use only the standard library check every condition with exact arithmetic. They compute the Krawtchouk polynomials by different formulas. To check one entry by hand, evaluate f at the integers d to n.

The method is Delsarte's from 1973. I am not claiming a new method, and I have not searched the literature exhaustively, so some of these bounds may already be known to you or appear in papers I did not find. The base entries are listed in base_cells.csv and all improved entries in improved_cells.csv.

The files and the programs are at https://github.com/Foundation-0/gfq-codes/tree/main/results/gf789-delsarte-table-scan

[sender line to be filled in by the person who sends it]
