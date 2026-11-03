#!/usr/bin/env python3
"""Sweep codetables.de upper bounds for Delsarte LP exclusions.

Writes logs under scripts/output/. SciPy required; verification uses stdlib checkers only.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.delsarte_lp import try_exclude, run_checkers  # noqa: E402

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
FETCH_DATE = datetime.now(timezone.utc).strftime("%Y-%m-%d")
RETRIEVED_AT = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

K_MAX = 12
Q7_N_MAX = 80
OTHER_N_MAX = 60
FIELDS = (3, 4, 5, 7, 8, 9)

BOUND_RE = re.compile(
    r"lower bound:</TD><TD>(\d+)</TD></TR><TR><TD>upper bound:</TD><TD>(\d+)</TD>",
    re.IGNORECASE | re.DOTALL,
)
MODIFIED_RE = re.compile(r"last modified:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", re.IGNORECASE)


def entry_url(q: int, n: int, k: int) -> str:
    return f"https://www.codetables.de/BKLC/BKLC.php?q={q}&n={n}&k={k}"


def skip_cell(q: int, n: int, k: int) -> str | None:
    if k < 1 or k >= n:
        return "invalid_k"
    if q == 7 and 51 <= n <= 60 and k <= K_MAX:
        return "prior_gf7_sweep"
    return None


def fetch_entry(q: int, n: int, k: int) -> dict:
    url = entry_url(q, n, k)
    request = urllib.request.Request(url, headers={"User-Agent": "gfq-codes-delsarte-sweep/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read()
            status = response.status
    except urllib.error.HTTPError as error:
        return {"url": url, "fetch_error": f"HTTP {error.code}"}
    except urllib.error.URLError as error:
        return {"url": url, "fetch_error": str(error.reason)}
    text = body.decode("latin-1", errors="replace")
    match = BOUND_RE.search(text)
    if not match:
        return {
            "url": url,
            "http_status": status,
            "fetch_error": "bounds not found in HTML",
            "response_sha256": hashlib.sha256(body).hexdigest(),
        }
    lower = int(match.group(1))
    upper = int(match.group(2))
    modified = MODIFIED_RE.search(text)
    note_has_daskalov = "daskalov" in text.lower()
    return {
        "url": url,
        "http_status": status,
        "displayed_lower_bound": lower,
        "displayed_upper_bound": upper,
        "entry_last_modified": modified.group(1) if modified else None,
        "note_mentions_daskalov": note_has_daskalov,
        "response_sha256": hashlib.sha256(body).hexdigest(),
        "open_gap": lower < upper,
    }


def prior_art_note(q: int, n: int, k: int, new_upper: int, entry: dict) -> dict:
    """Document what was checked; not exhaustive literature search."""
    searches = [
        f"codetables.de entry {entry.get('url')}",
        "results/gf7-upper-bounds/PROOF.md Daskalov–Metodieva 2007 Thm 2.2 (GF(7) LP list)",
        "Repository README and notes/scouting.md for per-field bound references",
    ]
    if q == 7 and n > 50:
        searches.append("Grassl table note: GF(7) n>50 upper bounds partly from Rumen Daskalov")
    already = new_upper >= entry.get("displayed_upper_bound", new_upper + 1)
    return {
        "searched": searches,
        "displayed_upper_at_fetch": entry.get("displayed_upper_bound"),
        "lp_implied_upper": new_upper,
        "would_lower_displayed_bound": not already and entry.get("open_gap", False),
        "entry_note_mentions_daskalov": entry.get("note_mentions_daskalov"),
    }


def iter_cells():
    for q in FIELDS:
        n_max = Q7_N_MAX if q == 7 else OTHER_N_MAX
        for n in range(1, n_max + 1):
            for k in range(1, min(K_MAX, n - 1) + 1):
                reason = skip_cell(q, n, k)
                if reason:
                    yield q, n, k, reason
                    continue
                yield q, n, k, None


def write_verify_py(result_dir: Path) -> None:
    content = '''#!/usr/bin/env python3
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
    path = result_dir / "verify.py"
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    log_path = OUTPUT_DIR / f"sweep_log_{FETCH_DATE}.jsonl"
    summary_path = OUTPUT_DIR / f"sweep_summary_{FETCH_DATE}.json"
    hits: list[dict] = []
    counts = {"tried": 0, "fetch_fail": 0, "closed": 0, "lp_no": 0, "cert_fail": 0, "checker_fail": 0}

    with log_path.open("w", encoding="utf-8") as log:
        for q, n, k, skip in iter_cells():
            if skip:
                record = {
                    "q": q,
                    "n": n,
                    "k": k,
                    "skipped": skip,
                    "fetch_date_utc": FETCH_DATE,
                }
                log.write(json.dumps(record) + "\n")
                continue

            counts["tried"] += 1
            entry = fetch_entry(q, n, k)
            row = {
                "q": q,
                "n": n,
                "k": k,
                "fetch_date_utc": FETCH_DATE,
                "retrieved_at_utc": RETRIEVED_AT,
                **entry,
            }
            if entry.get("fetch_error"):
                counts["fetch_fail"] += 1
                row["status"] = "fetch_failed"
                log.write(json.dumps(row) + "\n")
                time.sleep(0.05)
                continue

            if not entry.get("open_gap"):
                counts["closed"] += 1
                row["status"] = "closed_entry"
                log.write(json.dumps(row) + "\n")
                time.sleep(0.05)
                continue

            d_u = entry["displayed_upper_bound"]
            status, cert, detail = try_exclude(q, n, k, d_u)
            row["lp_status"] = status
            row["lp_detail"] = detail
            row["tested_excluded_distance"] = d_u

            if status != "certified" or cert is None:
                counts["lp_no"] += 1
                row["status"] = status
                log.write(json.dumps(row) + "\n")
                time.sleep(0.05)
                continue

            new_upper = d_u - 1
            prior = prior_art_note(q, n, k, new_upper, entry)
            row["prior_art"] = prior
            if not prior["would_lower_displayed_bound"]:
                row["status"] = "cert_not_table_improvement"
                log.write(json.dumps(row) + "\n")
                continue

            # Known repo result duplicates
            if q == 7 and (n, k) in {(55, 10), (56, 10), (56, 11), (57, 11)}:
                row["status"] = "already_in_repository"
                log.write(json.dumps(row) + "\n")
                continue

            tmp_cert = OUTPUT_DIR / f"tmp-gf{q}-n{n}-k{k}.json"
            tmp_cert.write_text(
                json.dumps({"format_version": 1, "certificates": [cert]}, indent=2) + "\n",
                encoding="utf-8",
            )
            code, out1, out2 = run_checkers(tmp_cert)
            row["checker_primary"] = out1
            row["checker_independent"] = out2
            if code != 0:
                counts["checker_fail"] += 1
                row["status"] = "checker_failed"
                log.write(json.dumps(row) + "\n")
                continue

            row["status"] = "hit"
            row["old_upper_bound"] = d_u
            row["new_upper_bound"] = new_upper
            row["certificate"] = cert
            hits.append(row)
            log.write(json.dumps(row) + "\n")
            time.sleep(0.05)

    summary = {
        "fetch_date_utc": FETCH_DATE,
        "fields": list(FIELDS),
        "k_range": f"1..{K_MAX} (and k < n)",
        "n_range_q7": f"1..{Q7_N_MAX} excluding n=51..60 with k<={K_MAX}",
        "n_range_other": f"1..{OTHER_N_MAX}",
        "counts": counts,
        "hits": [
            {
                "q": h["q"],
                "n": h["n"],
                "k": h["k"],
                "old_upper_bound": h["old_upper_bound"],
                "new_upper_bound": h["new_upper_bound"],
            }
            for h in hits
        ],
        "log_path": str(log_path.relative_to(ROOT)),
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
