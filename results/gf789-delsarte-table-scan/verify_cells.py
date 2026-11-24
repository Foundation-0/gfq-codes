"""Offline bookkeeping check for the table scan (standard library only; failures raise SystemExit).

Reads certificate.json, improved_cells.csv, base_cells.csv and summary.json from this folder and checks:
 1. every improved entry lies strictly below the displayed upper bound and not below the displayed lower bound;
 2. every base entry names a certificate that exists, has the same q, n, k, and excludes exactly new_upper + 1;
 3. the counts per field: improved entries beyond the table's own consistency (94, 1,408, 916), base entries
    (12, 62, 48) and the matching figures in summary.json;
 4. the two GF(7) entries [56,12,39] and [57,12,40] have certificates that exclude distance 39 and 40;
 5. every statement already in the other results of this repository (18 certificates) appears in the entry list
    with a new upper bound at least as small.
Whether each certificate is valid is checked by the other programs in this folder, not here.

Usage: python3 -I -O verify_cells.py
"""
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPECT_IMPROVED = {7: 94, 8: 1408, 9: 916}
EXPECT_BASE = {7: 12, 8: 62, 9: 48}


def fail(message):
    raise SystemExit("FAIL: " + message)


def main():
    with open(HERE / "certificate.json", encoding="utf-8") as handle:
        certs = {c["id"]: c for c in json.load(handle)["certificates"]}
    with open(HERE / "improved_cells.csv", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    with open(HERE / "base_cells.csv", newline="", encoding="utf-8") as handle:
        base_file = list(csv.DictReader(handle))
    with open(HERE / "summary.json", encoding="utf-8") as handle:
        summary = json.load(handle)

    for r in rows:
        q, n, k = int(r["q"]), int(r["n"]), int(r["k"])
        lower, table_up, new_up = int(r["lower"]), int(r["table_upper"]), int(r["new_upper"])
        if not lower <= new_up < table_up:
            fail(f"q={q} n={n} k={k}: new upper bound outside [lower, table upper)")
        if r["kind"] not in ("base", "derived"):
            fail(f"q={q} n={n} k={k}: unknown kind")
        if r["kind"] == "base":
            name = r["cert"].split("#", 1)[1]
            c = certs.get(name)
            if c is None:
                fail(f"missing certificate {name}")
            if (c["q"], c["n"], c["k"]) != (q, n, k):
                fail(f"{name}: parameters do not match the entry")
            if c["excluded_distance"] != new_up + 1:
                fail(f"{name}: excludes d={c['excluded_distance']}, entry needs {new_up + 1}")

    if [tuple(sorted(r.items())) for r in base_file] != [tuple(sorted(r.items())) for r in rows if r["kind"] == "base"]:
        fail("base_cells.csv differs from the base rows of improved_cells.csv")

    for q in (7, 8, 9):
        mine = [r for r in rows if int(r["q"]) == q]
        beyond = [r for r in mine if int(r["new_upper"]) < int(r["table_self_closure_upper"])]
        base = [r for r in mine if r["kind"] == "base"]
        if len(beyond) != EXPECT_IMPROVED[q] or len(base) != EXPECT_BASE[q]:
            fail(f"GF({q}): counts {len(beyond)} improved, {len(base)} base")
        if any(int(r["new_upper"]) >= int(r["table_self_closure_upper"]) for r in base):
            fail(f"GF({q}): a base entry lies within the table's own closure")
        s = summary[str(q)]
        if (s["improved_beyond_table_own_closure"], s["base"], s["improved"]) != (len(beyond), len(base), len(mine)):
            fail(f"GF({q}): summary.json disagrees with the entry list")
        print(f"GF({q}): {len(mine)} listed, {len(beyond)} improved beyond the table's own consistency, {len(base)} base")

    for n, d in ((56, 39), (57, 40)):
        c = certs.get(f"gf7-n{n}-k12-exclude-d{d}")
        if c is None or c["excluded_distance"] != d or (c["q"], c["n"], c["k"]) != (7, n, 12):
            fail(f"no certificate for GF(7) [{n},12,{d}]")
    print("GF(7) [56,12,39] and [57,12,40]: certificates present")

    listed = {(int(r["q"]), int(r["n"]), int(r["k"])): int(r["new_upper"]) for r in rows}
    count = 0
    for path in sorted(HERE.parent.glob("*/certificate.json")):
        if path.parent == HERE:
            continue
        with open(path, encoding="utf-8") as handle:
            for c in json.load(handle)["certificates"]:
                key = (c["q"], c["n"], c["k"])
                if key not in listed or listed[key] > c["excluded_distance"] - 1:
                    fail(f"{path.parent.name}: {c['id']} is not in the entry list with the same bound")
                count += 1
    print(f"{count} statements of the other results appear in the entry list with the same or a smaller bound")
    print("bookkeeping passes")


if __name__ == "__main__":
    main()
