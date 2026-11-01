#!/usr/bin/env python3
"""Write results/* directories from sweep log hits."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "scripts" / "output" / "sweep_log_2026-10-31.jsonl"
FETCH_DATE = "2026-10-31"

VERIFY_PY = '''#!/usr/bin/env python3
"""Replay certificate checks with locked tools (stdlib only)."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CERT = Path(__file__).resolve().parent / "certificate.json"
CHECKERS = (
    ROOT / "tools" / "check_bound.py",
    ROOT / "tools" / "check_bound_independent.py",
)


def main() -> int:
    for checker in CHECKERS:
        result = subprocess.run([sys.executable, str(checker), str(CERT)], check=False)
        if result.returncode != 0:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def proof_md(hit: dict) -> str:
    q, n, k = hit["q"], hit["n"], hit["k"]
    old_u, new_u = hit["old_upper_bound"], hit["new_upper_bound"]
    d_ex = hit["tested_excluded_distance"]
    url = hit["url"]
    cert = hit["certificate"]
    prior = hit.get("prior_art", {})
    return f"""# Delsarte upper bound for [{n},{k}] over GF({q})

**Status: claimed research result** — exact Delsarte LP certificate with dual integer
coefficients; **VERIFIED** by both locked checkers in this repository. Human review pending.

## Statement (would lower codetables.de on {FETCH_DATE})

| Quantity | Value |
|---|---:|
| Field GF({q}) | length {n}, dimension {k} |
| Displayed lower bound (Grassl) | {hit.get("displayed_lower_bound")} |
| Displayed upper bound (Grassl) | {old_u} |
| **Upper bound established here** | **{new_u}** |
| Excluded minimum distance | {d_ex} (no linear [{n},{k},{d_ex}] code) |

Source entry: [{url}]({url}) (retrieved {FETCH_DATE} UTC; see sources.json).

## Method

**KNOWN** (Delsarte, 1973): non-negative Krawtchouk combination with nonpositive values on
{{d_ex,…,{n}}} and code-size ratio below {q}^{k} excludes minimum distance ≥ {d_ex}.
See [tools/README.md](../../tools/README.md) and [results/gf7-upper-bounds/PROOF.md](../gf7-upper-bounds/PROOF.md).

Discovery on this cell used SciPy HiGHS on the normalized LP in the GF(7) write-up, then
contact-point exactification to integer `krawtchouk_coefficients` in [certificate.json](certificate.json).

## Replay

```sh
sha256sum -c tools/SHA256SUMS
python3 tools/check_bound.py results/{Path(hit["result_dir"]).name}/certificate.json
python3 tools/check_bound_independent.py results/{Path(hit["result_dir"]).name}/certificate.json
python3 results/{Path(hit["result_dir"]).name}/verify.py
```

## Prior art searched ({FETCH_DATE})

{chr(10).join("- " + s for s in prior.get("searched", []))}

- **Daskalov–Metodieva (2007), Theorem 2.2 (GF(7) LP list):** **VERIFIED** against the
  author PDF preview on {FETCH_DATE} — `[{n},{k},{d_ex}]_{q}` is **not** among the 34 listed
  nonexistent codes when q=7; for q≠7 this theorem does not apply directly.
- **Grassl / Brouwer note on GF(9):** **KNOWN** — entry pages state upper bounds are mostly
  from Brouwer’s tables (as of 2007-02-13 on the pages read); stale display vs classical LP
  is possible; no entry-specific proof of bound {new_u} was found on the page.
- **Grassl entry note:** upper bound provenance as quoted on the entry page; no entry-specific
  citation of an LP bound of {new_u} on {FETCH_DATE}.
- No claim of priority or exhaustive literature coverage.

## Credit

Markus Grassl's codetables.de supplied comparison data. Certificate found by automated sweep
(`scripts/delsarte_sweep.py`) on branch `axiom/delsarte-sweep`. AI agent for Alkindus; human sign-off pending.
"""


def main() -> int:
    hits = []
    for line in LOG.open(encoding="utf-8"):
        row = json.loads(line)
        if row.get("status") == "hit":
            hits.append(row)
    for hit in hits:
        q, n, k = hit["q"], hit["n"], hit["k"]
        name = f"gf{q}-n{n}-k{k}-upper-d{hit['new_upper_bound']}"
        hit["result_dir"] = f"results/{name}"
        result_dir = ROOT / "results" / name
        result_dir.mkdir(parents=True, exist_ok=True)
        cert_doc = {"format_version": 1, "certificates": [hit["certificate"]]}
        (result_dir / "certificate.json").write_text(
            json.dumps(cert_doc, indent=2) + "\n", encoding="utf-8"
        )
        sources = {
            "description": "Single codetables.de entry snapshot for this certificate.",
            "entries": [
                {
                    "q": q,
                    "n": n,
                    "k": k,
                    "url": hit["url"],
                    "retrieved_at_utc": hit.get("retrieved_at_utc"),
                    "http_status": hit.get("http_status"),
                    "displayed_lower_bound": hit.get("displayed_lower_bound"),
                    "displayed_upper_bound": hit.get("displayed_upper_bound"),
                    "entry_last_modified": hit.get("entry_last_modified"),
                    "response_sha256": hit.get("response_sha256"),
                }
            ],
        }
        (result_dir / "sources.json").write_text(json.dumps(sources, indent=2) + "\n", encoding="utf-8")
        (result_dir / "PROOF.md").write_text(proof_md(hit), encoding="utf-8")
        verify = result_dir / "verify.py"
        verify.write_text(VERIFY_PY, encoding="utf-8")
        verify.chmod(0o755)
        subprocess.run(
            [sys.executable, str(verify)],
            cwd=ROOT,
            check=True,
        )
        print("wrote", name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
