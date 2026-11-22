"""Dual-mode CLI certifier for AUDIT-113 (Foundation-0/gfq-codes & math0#3/#4).

Modes:
  --standalone (default): Recomputes all 3 pure-Z/F_q/Q pillars live from
      scratch and replays the pinned portal manifest (zero disk intake reads).
  --live --intake-dir <dir>: Fail-closed verifies all 26 pinned files on disk
      (byte length, SHA-256, non-symlink containment), parses live JSON/matrix
      inputs from disk, and emits live_portal_verified=true.
  --check <cert.json>: Fail-closed semantic & digest verifier for any saved
      certificate JSON (rejects floats, non-str keys, all-zero SHAs, or forged
      payloads).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

_HERE = str(Path(__file__).resolve().parent)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from gfq_distance_oracle import (
    GFQ_CODES_MAIN_SHA,
    MATH0_PR3_HEAD_SHA,
    MATH0_PR4_HEAD_SHA,
    PINNED_GFQ_CODES_FILES,
    PINNED_GFQ_CODES_OPEN_PRS,
    PINNED_MATH0_PR4_CODES,
    GaloisField,
    GfqCertError,
    assemble_certificate,
    build_payload,
    canonical_json_bytes,
    default_pinned_portal_manifest,
    parse_matrix_canonical,
    require_hex,
    validate_certificate,
)


def _safe_read_pinned_file(intake_root: Path, rel: str, exp_bytes: int, exp_sha: str) -> bytes:
    root_res = intake_root.resolve()
    cur = intake_root
    for part in Path(rel).parts:
        cur = cur / part
        if cur.is_symlink():
            raise GfqCertError(f"refusing symlink intake file: {rel}")
    resolved = cur.resolve()
    if not resolved.is_relative_to(root_res):
        raise GfqCertError(f"path escape outside intake root: {rel}")
    if not resolved.is_file():
        raise GfqCertError(f"missing pinned intake file: {rel}")
    data = resolved.read_bytes()
    if len(data) != exp_bytes:
        raise GfqCertError(f"byte-length mismatch on {rel}: {len(data)} != {exp_bytes}")
    got_sha = hashlib.sha256(data).hexdigest()
    if got_sha != exp_sha:
        raise GfqCertError(f"SHA-256 mismatch on {rel}: {got_sha} != {exp_sha}")
    return data


def _reject_float_parse(val: str) -> Any:
    raise GfqCertError(f"floating-point or special JSON token rejected: {val!r}")


def _load_strict_json_bytes(raw: bytes, label: str) -> Any:
    try:
        return json.loads(
            raw.decode("utf-8"),
            parse_float=_reject_float_parse,
            parse_constant=_reject_float_parse,
        )
    except GfqCertError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as err:
        raise GfqCertError(f"invalid JSON in {label}: {err}") from err


def parse_live_intake_blobs(blobs: dict[str, bytes]) -> tuple[list[tuple[int, str]], int, list[dict[str, Any]]]:
    """Validate and parse pinned gfq-codes metadata, SHA256SUMS, and GF(7) certificates."""
    head_obj = _load_strict_json_bytes(blobs["gfq_codes_head.json"], "gfq_codes_head.json")
    if type(head_obj) is not dict or head_obj.get("sha") != GFQ_CODES_MAIN_SHA:
        raise GfqCertError("live gfq_codes_head.json SHA mismatch")

    prs_obj = _load_strict_json_bytes(blobs["gfq_codes_prs.json"], "gfq_codes_prs.json")
    if type(prs_obj) is not list:
        raise GfqCertError("gfq_codes_prs.json must be list")
    live_open_prs: list[tuple[int, str]] = []
    for p in prs_obj:
        if type(p) is dict and p.get("state") == "OPEN":
            num = p.get("number")
            oid = p.get("headRefOid")
            if type(num) is not int or type(oid) is not str or len(oid) < 8:
                raise GfqCertError(f"malformed open PR record: {p!r}")
            live_open_prs.append((num, oid[:8]))
    live_open_prs.sort()
    exp_open_prs = [(p["number"], p["head_prefix"]) for p in PINNED_GFQ_CODES_OPEN_PRS]
    if live_open_prs != exp_open_prs:
        raise GfqCertError(f"live open PR list mismatch: {live_open_prs} != {exp_open_prs}")

    issues_obj = _load_strict_json_bytes(blobs["gfq_codes_issues.json"], "gfq_codes_issues.json")
    if type(issues_obj) is not list:
        raise GfqCertError("gfq_codes_issues.json must be list")
    open_issue_count = sum(1 for it in issues_obj if type(it) is dict and it.get("state") == "OPEN")
    if open_issue_count != 5:
        raise GfqCertError(f"expected 5 open issues, got {open_issue_count}")

    try:
        sums_text = blobs["gfq_codes/tools/SHA256SUMS"].decode("utf-8")
    except UnicodeDecodeError as err:
        raise GfqCertError(f"invalid UTF-8 in tools/SHA256SUMS: {err}") from err
    sums_lines = [ln.strip() for ln in sums_text.splitlines() if ln.strip()]
    if len(sums_lines) != 2:
        raise GfqCertError("unexpected tools/SHA256SUMS entry count")
    for ln in sums_lines:
        parts = ln.split()
        if len(parts) != 2:
            raise GfqCertError(f"malformed SHA256SUMS line: {ln!r}")
        exp_digest = require_hex(parts[0], 64, "SHA256SUMS digest")
        rel_tool = f"gfq_codes/{parts[1]}"
        if rel_tool not in blobs or hashlib.sha256(blobs[rel_tool]).hexdigest() != exp_digest:
            raise GfqCertError(f"tools/SHA256SUMS verification failed for {parts[1]}")

    cert_doc = _load_strict_json_bytes(
        blobs["gfq_codes/results/gf7-upper-bounds/certificate.json"],
        "gf7-upper-bounds/certificate.json",
    )
    if (
        type(cert_doc) is not dict
        or cert_doc.get("format_version") != 1
        or type(cert_doc.get("certificates")) is not list
    ):
        raise GfqCertError("malformed GF(7) certificate.json")
    return live_open_prs, open_issue_count, cert_doc["certificates"]


def run_live_audit(intake_dir: Path) -> dict[str, Any]:
    """Read, pin-verify, and live-parse all 26 files from intake-gfq-codes/."""
    if not intake_dir.is_dir() or intake_dir.is_symlink():
        raise GfqCertError(f"invalid intake directory: {intake_dir}")

    verified_files: dict[str, dict[str, Any]] = {}
    blobs: dict[str, bytes] = {}
    for rel, (exp_len, exp_sha) in sorted(PINNED_GFQ_CODES_FILES.items()):
        raw = _safe_read_pinned_file(intake_dir, rel, exp_len, exp_sha)
        blobs[rel] = raw
        verified_files[rel] = {"bytes": len(raw), "sha256": exp_sha}

    live_open_prs, open_issue_count, live_gf7_certs = parse_live_intake_blobs(blobs)

    fields_cache = {q: GaloisField(q) for q in (3, 4, 5)}
    live_matrices: list[tuple[int, int, int, int, str, str, list[list[int]]]] = []
    for q, n, k, d_exp, fn, exp_len, exp_sha, _ in PINNED_MATH0_PR4_CODES:
        rel = f"math0_pr4_best/{fn}"
        raw = _safe_read_pinned_file(intake_dir, rel, exp_len, exp_sha)
        verified_files[rel] = {"bytes": len(raw), "sha256": exp_sha}
        G = parse_matrix_canonical(raw.decode("utf-8"), fields_cache[q])
        live_matrices.append((q, n, k, d_exp, fn, exp_sha, G))

    portal_manifest = {
        "gfq_codes_repo": "Foundation-0/gfq-codes",
        "gfq_codes_main_sha": GFQ_CODES_MAIN_SHA,
        "gfq_codes_open_prs": [dict(p) for p in PINNED_GFQ_CODES_OPEN_PRS],
        "gfq_codes_open_pr_count": len(live_open_prs),
        "gfq_codes_open_issue_count": open_issue_count,
        "gfq_codes_tools_sha256sums_ok": True,
        "math0_pr3_head_sha": MATH0_PR3_HEAD_SHA,
        "math0_pr4_head_sha": MATH0_PR4_HEAD_SHA,
        "pinned_file_count": len(verified_files),
        "pinned_files": dict(sorted(verified_files.items())),
    }
    payload = build_payload(math0_matrices=live_matrices, gf7_certs=live_gf7_certs)
    return assemble_certificate(
        execution_mode="live_portal_intake",
        live_portal_verified=True,
        portal_manifest=portal_manifest,
        payload=payload,
    )


def run_standalone_audit() -> dict[str, Any]:
    """Offline standalone audit recomputing all 3 mathematical pillars from scratch."""
    manifest = default_pinned_portal_manifest()
    payload = build_payload()
    return assemble_certificate(
        execution_mode="standalone_pinned_manifest",
        live_portal_verified=False,
        portal_manifest=manifest,
        payload=payload,
    )


def check_certificate_file(cert_path: Path) -> dict[str, Any]:
    if not cert_path.is_file() or cert_path.is_symlink():
        raise GfqCertError(f"invalid certificate path: {cert_path}")
    raw = cert_path.read_bytes()
    parsed = _load_strict_json_bytes(raw, cert_path.name)
    res = validate_certificate(parsed)
    re_encoded = (json.dumps(parsed, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode("utf-8")
    compact = canonical_json_bytes(parsed)
    if raw not in (re_encoded, compact, compact + b"\n"):
        raise GfqCertError("certificate file is not canonically formatted")
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AUDIT-113 pure-Z/F_q/Q linear-code distance certifier")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--standalone", action="store_true", help="Offline standalone verification (default)")
    mode.add_argument("--live", action="store_true", help="Live on-disk intake pin verification")
    mode.add_argument("--check", type=Path, help="Verify an existing certificate JSON file")
    ap.add_argument("--intake-dir", type=Path, help="Read-only intake-gfq-codes/ directory for --live")
    ap.add_argument("--output", type=Path, help="Write canonical indented JSON certificate to path")
    ap.add_argument("--json", action="store_true", help="Emit canonical compact JSON to stdout")
    args = ap.parse_args(argv)

    try:
        if args.check is not None:
            summary = check_certificate_file(args.check)
            if args.json:
                sys.stdout.write(canonical_json_bytes(summary).decode("utf-8") + "\n")
            else:
                print(
                    f"OK AUDIT-113 mode={summary['execution_mode']} "
                    f"payload_sha256={summary['payload_sha256']} "
                    f"certificate_sha256={summary['certificate_sha256']}"
                )
            return 0

        if args.live:
            if args.intake_dir is None:
                raise GfqCertError("--live requires --intake-dir")
            cert = run_live_audit(args.intake_dir)
        else:
            if args.intake_dir is not None:
                raise GfqCertError("--intake-dir is only valid with --live")
            cert = run_standalone_audit()

        if args.output is not None:
            rendered = json.dumps(cert, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
            args.output.write_text(rendered, encoding="utf-8")

        if args.json:
            sys.stdout.write(canonical_json_bytes(cert).decode("utf-8") + "\n")
        else:
            p2 = cert["payload"]["pillar_2_zimmermann_and_duality"]
            m15 = p2["math0_pr4_15_codes"]
            print(
                f"AUDIT-113 PASS mode={cert['execution_mode']} "
                f"math0_15={m15['count']}/15 "
                f"z_enum={m15['total_zimmermann_enumerated']}/{m15['total_naive_disjoint_enumerated']} "
                f"payload_sha256={cert['payload_sha256']} "
                f"certificate_sha256={cert['certificate_sha256']}"
            )
        return 0
    except GfqCertError as err:
        print(f"ERROR: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
