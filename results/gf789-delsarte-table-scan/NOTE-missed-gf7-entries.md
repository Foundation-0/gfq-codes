# Two GF(7) entries inside the earlier sweep range

[results/gf7-upper-bounds/PROOF.md](../gf7-upper-bounds/PROOF.md) says the first GF(7) sweep covered `51<=n<=60`
and `k<=12`. It tested 81 open entries at their displayed upper distance and found four exclusions, listed there.

Two entries inside that range are not in its list:

| Entry | Displayed lower bound | Displayed upper bound | Distance excluded here | Certificate id |
|---|---:|---:|---:|---|
| `[56,12]` | 33 | 39 | 39 | `gf7-n56-k12-exclude-d39` |
| `[57,12]` | 34 | 40 | 40 | `gf7-n57-k12-exclude-d40` |

Both entries were read again on 15 November 2026 and show the values above ([sources.json](sources.json)). Both have
exact certificates in [certificate.json](certificate.json) that pass every checker in this folder. The ratio
`f(0)/(a_0 q^k)` is 0.957 for `[56,12]` and 0.691 for `[57,12]`, both below 1. So there is no linear `[56,12,39]` code
and no linear `[57,12,40]` code over GF(7), and the displayed upper bounds fall to 38 and 39.

The reason the earlier sweep did not list them is not known. Possible causes are a solver that did not return a usable
answer for these two entries, or a different range than the one written. Nothing in the repository settles which.
The earlier text is not changed. This note records the difference.

Check: `python3 results/gf789-delsarte-table-scan/verify_cells.py` prints that both certificates are present, and
`python3 results/gf789-delsarte-table-scan/verify.py` checks them.
