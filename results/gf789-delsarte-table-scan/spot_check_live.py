"""Optional live check (needs a network): look up nine base entries, chosen by a fixed random seed, on the
reference tables and compare the displayed lower and upper bounds with the values in improved_cells.csv.
The pages are read and discarded. Nothing is saved or redistributed.

Usage: python3 -I spot_check_live.py
"""
import csv
import random
import re
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    with open(HERE / "improved_cells.csv", newline="", encoding="utf-8") as handle:
        base = [r for r in csv.DictReader(handle) if r["kind"] == "base"]
    random.seed(20261115)
    bad = 0
    for r in random.sample(base, 9):
        url = f"http://www.codetables.de/BKLC/BKLC.php?q={r['q']}&n={r['n']}&k={r['k']}"
        request = urllib.request.Request(url, headers={"User-Agent": "research-script"})
        html = urllib.request.urlopen(request, timeout=40).read().decode("latin-1")
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
        m = re.search(r"lower bound:\s*(\d+)\s*upper bound:\s*(\d+)", text)
        live = m.groups() if m else None
        same = live == (r["lower"], r["table_upper"])
        bad += not same
        print(f"q={r['q']} n={r['n']} k={r['k']}: listed {r['lower']}/{r['table_upper']}, live {live}, {'match' if same else 'DIFFERENT'}")
        time.sleep(1.2)
    if bad:
        raise SystemExit(f"{bad} of 9 entries differ")
    print("9 of 9 match")


if __name__ == "__main__":
    main()
