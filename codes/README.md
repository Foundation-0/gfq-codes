# Code files

Each claimed code is one JSON file in this folder, at `q<q>/n<n>-k<k>-d<d>.json`. No code has been added yet. A file
is added only when both minimum-distance checkers accept it.

## Fields

| Field | What |
|---|---|
| `q` | the field size: 3, 4, 5, 7, 8 or 9 |
| `modulus` | for q = 4, 8 and 9 only: the polynomial that defines the field, as its coefficients from the constant term up |
| `n`, `k` | the length and the dimension |
| `d` | the claimed minimum distance |
| `generator` | the generator matrix: k strings of n digits, one digit per field element |
| `construction` | how the code was built, in enough detail to rebuild it |
| `source` | who found it (the person, and any agent), the program with its commit, and the date |
| `table` | the codetables.de entry for (q, n, k) on the day it was read: lower bound, upper bound and date |

Both checkers must find that the generator matrix has rank k and that the minimum distance is exactly d. A code is an
improvement only if d is larger than the table's lower bound.

## Field elements

Each element of GF(q) is written as one digit from 0 to q − 1.

- For q = 3, 5 and 7 the digit is the residue modulo q.
- For q = 4, 8 and 9, q is a power of a prime p. Write the digit in base p: c = c_0 + c_1·p + … stands for
  c_0 + c_1·a + …, where a is a root of `modulus`. In GF(4), 2 is a and 3 is a + 1. In GF(9), 3 is a and 5 is a + 2.
- Default moduli: x² + x + 1 for GF(4), written `[1, 1, 1]`; x³ + x + 1 for GF(8), written `[1, 1, 0, 1]`;
  x² + 2x + 2 for GF(9), written `[2, 2, 1]`. A file may use another irreducible polynomial if it states it.

## Example

The tetracode, a code over GF(3) with n = 4, k = 2 and d = 3. Every nonzero codeword has weight 3. It is not an
improvement: codetables.de gives 3 for this entry.

```json
{
  "q": 3,
  "n": 4,
  "k": 2,
  "d": 3,
  "generator": ["1011", "0112"],
  "construction": "the tetracode",
  "source": "worked example in codes/README.md, 19 Oct 2026",
  "table": {"lower": 3, "upper": 3, "date": "2026-10-19"}
}
```
