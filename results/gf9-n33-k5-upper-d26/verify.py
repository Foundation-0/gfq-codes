#!/usr/bin/env python3
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
