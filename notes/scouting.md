# Scouting record, 18 and 19 October 2026

The research behind this project, from Foundation0's
[scouting of 18–19 October 2026](https://github.com/Foundation-0/f0/tree/main/deep-fields). Each fact is marked by
how far it has been checked.

## The question

Which open entries in the tables of best known linear codes over GF(3) to GF(9) can be improved, with a minimum
distance anyone can recompute?

A linear code adds redundancy to data so errors can be corrected. Its quality is measured by its minimum distance.
Markus Grassl's tables at [codetables.de](https://www.codetables.de/BKLC/index.html) list, for each length and
dimension, the best minimum distance known and the best upper bound. Where the two differ, a better code may exist.
A code is given by its generator matrix, and anyone can recompute its minimum distance.

Hub: [math0](https://github.com/Foundation-0/math0), which holds the
[census of open entries on codetables.de](https://github.com/Foundation-0/math0/tree/main/data/codetables). Related
work in Foundation0:

- f0's [gf2m-circuits](https://fdn0.org/research/gf2m-circuits/) work: exact search plus exhaustive checking;
- the [integer-multiplication race](https://fdn0.org/research/integer-multiplication/story/) format: open pull
  requests, exact checks.

## Checked on 19 Oct 2026

Nothing yet. Every fact below comes from the scouting reports and has not been re-checked for this repository.

## From the scouting reports, not yet re-checked

### f0's scouting of 18 Oct 2026

Source: [deep-fields/README.md](https://github.com/Foundation-0/f0/blob/main/deep-fields/README.md).

- 80,652 open entries on codetables.de outside the binary table (census of 18 Oct 2026 in math0). In a random
  sample, 77% were last changed in 2001–2009. AI work so far targets binary codes.
- Many gaps reflect weak upper bounds, so not every gap hides a better code. Grassl runs his own quasi-cyclic sweep.

### Scouting of 19 Oct 2026

- codetables.de's newest dated update is 24 May 2024, for quantum codes (<https://www.codetables.de/main.html>).
  Grassl's 2025–26 arXiv papers are on other topics.
- One small entrant: genetic-algorithm records over F3 and F4 (GF(3) and GF(4)), 19 Aug 2026
  ([arXiv:2608.18664](https://arxiv.org/abs/2608.18664)). No sweep announced.

## Policy

Build an open minimum-distance checker over GF(q) first. Contact the maintainer, Markus Grassl, before submitting
anything in bulk.

## Status

Not started. Lead: to be named.
