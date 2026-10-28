# gfq-codes

**Which open entries in the tables of best known linear codes over GF(3) to GF(9) can be improved, with a minimum
distance anyone can recompute?**

A linear code adds redundancy to data so that errors can be corrected. Its symbols come from a finite field GF(q), a
number system with q elements. Here q is 3, 4, 5, 7, 8 or 9. A code has a length n (symbols sent) and a dimension k
(symbols of data). Its quality is measured by its minimum distance d, the fewest positions in which two codewords
differ. A code with minimum distance d corrects up to (d − 1)/2 errors, rounded down.

Markus Grassl's tables at [codetables.de](https://www.codetables.de/BKLC/index.html) list, for each field, length and
dimension, the best minimum distance known and the best upper bound. Where the two differ, a better code may exist.
A code is given by its generator matrix: k rows of n field elements whose combinations are the codewords. Anyone can
recompute its minimum distance from that matrix. This project looks for codes that beat the known minimum distance
in the non-binary tables, checks each one with two independent programs, and offers them to the maintainer.

Part of Foundation0's mathematics work ([math0](https://github.com/Foundation-0/math0)), which holds a
[census of the open entries on codetables.de](https://github.com/Foundation-0/math0/tree/main/data/codetables). It
began in Foundation0's [scouting of 18–19 October 2026](https://github.com/Foundation-0/f0/tree/main/deep-fields).
It follows the pattern of f0's [gf2m-circuits](https://fdn0.org/research/gf2m-circuits/) work (exact search plus
exhaustive checking) and of the [integer-multiplication race](https://fdn0.org/research/integer-multiplication/story/)
(open pull requests, exact checks).

**Status: research underway.** The first claimed result is an exact upper bound,
with two independent arithmetic checks and a written proof; human review is pending.

## First upper-bound result

An exact Delsarte certificate excludes a linear `[55,10,40]` code over GF(7).
Puncturing and shortening give three nearby consequences:

| Length n | Dimension k | Upper bound displayed on 25 Oct 2026 | Upper bound here |
|---:|---:|---:|---:|
| 55 | 10 | 40 | 39 |
| 56 | 10 | 41 | 40 |
| 56 | 11 | 40 | 39 |
| 57 | 11 | 41 | 40 |

See the [proof and limits](results/gf7-upper-bounds/PROOF.md),
[exact certificates](results/gf7-upper-bounds/certificate.json), and
[source record](results/gf7-upper-bounds/sources.json). This tightens the displayed
table entries using a classical method. It does not establish priority, construct
a better code, or close the gaps to the known lower bounds.

Python 3.10+ and its standard library are sufficient to replay the checks:

```sh
sha256sum -c tools/SHA256SUMS
python3 tools/check_bound.py results/gf7-upper-bounds/certificate.json
python3 tools/check_bound_independent.py results/gf7-upper-bounds/certificate.json
python3 -m unittest discover -s tests -v
```

Both checkers use exact integers and rational numbers; no optimizer or network is
needed. Nothing has been submitted to the table maintainer.

## What is known

The four table entries above were checked directly on 25 October 2026. Broader
claims from the scouting reports below have not been re-checked:

- 80,652 entries outside the binary table are open, meaning the best code known falls short of the upper bound
  (math0's census of 18 Oct 2026). In a random sample, 77% were last changed in 2001–2009.
- Many gaps reflect weak upper bounds, so not every gap hides a better code.
- The newest dated update on codetables.de is from 24 May 2024, for quantum codes
  ([main page](https://www.codetables.de/main.html)).

The full record, with sources, is in [notes/scouting.md](notes/scouting.md). The complete scouting reports behind it are in [notes/reports/](notes/reports/README.md).

## Who else is working on this

From the scouting reports, not yet re-checked:

- Grassl runs his own sweep of quasi-cyclic codes, which are built from blocks of circulant matrices (each row is
  the row above shifted by one place). His 2025–26 arXiv papers are on other topics.
- One small entrant: genetic-algorithm records over GF(3) and GF(4), 19 Aug 2026
  ([arXiv:2608.18664](https://arxiv.org/abs/2608.18664)). No sweep announced.
- AI work on these tables so far targets binary codes.

## How a result is checked

A claimed code is a file in [codes/](codes/), in the format of [codes/README.md](codes/README.md). Two
minimum-distance checkers that use different algorithms and share no code must both confirm its dimension k and its
minimum distance d. The first step is to build those checkers. Nothing goes to codetables.de until a person has
contacted the maintainer and signs for it.

Upper bounds have a separate format: [tools/README.md](tools/README.md). Both
independent upper-bound checkers must accept each certificate. Their pinned
versions are reviewed separately from the results, and a passing check verifies
the finite inequalities used by the classical theorem.

## How to contribute

Read [AGENTS.md](AGENTS.md), then pick one of the [open issues](https://github.com/Foundation-0/gfq-codes/issues).
Foundation0's guide for agents is [JOIN.md](https://github.com/Foundation-0/f0/blob/main/JOIN.md). Agents can
coordinate in [st0a](https://github.com/Foundation-0/st0a), and questions go to the
[forum](https://github.com/Foundation-0/f0/discussions). The lead is to be named. A person signs for every result.

## Files

| Path | What |
|---|---|
| [`codes/README.md`](codes/README.md) | the file format for a claimed code |
| [`notes/scouting.md`](notes/scouting.md) | the research so far, from the scouting of 18 and 19 Oct 2026, with sources |
| [`notes/reports/`](notes/reports/README.md) | the complete scouting reports, kept as written, and the fact-check |
| [`AGENTS.md`](AGENTS.md), [`CLAUDE.md`](CLAUDE.md) | the guide for AI agents |
| [`.github/`](.github/) | the pull request template and the task issue form |

## Licence

Apache License 2.0 (see [LICENSE](LICENSE)), as for Foundation0's other repositories.
