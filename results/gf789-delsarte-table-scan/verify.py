#!/usr/bin/env python3
"""Replay every check for this result (standard library only).

Runs the two locked checkers of the repository, the two exact verifiers and the separate checker kept in this
folder on certificate.json, and then the bookkeeping check on the entry lists.
"""

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CERT = HERE / "certificate.json"
COMMANDS = (
    (ROOT / "tools" / "check_bound.py", [CERT]),
    (ROOT / "tools" / "check_bound_independent.py", [CERT]),
    (HERE / "verify_certs.py", [CERT]),
    (HERE / "verify_binomial.py", [CERT]),
    (HERE / "delsarte_independent.py", [CERT]),
    (HERE / "verify_cells.py", []),
)


def main() -> int:
    for program, args in COMMANDS:
        quiet = program.name == "delsarte_independent.py"
        result = subprocess.run(
            [sys.executable, str(program), *map(str, args)],
            capture_output=quiet, text=True, check=False,
        )
        if result.returncode != 0:
            return result.returncode
        if quiet:
            print(result.stdout.splitlines()[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
