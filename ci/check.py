#!/usr/bin/env python3
"""
check.py - the single entrypoint for Loopforge CI.

Runs every check that enforces "nothing here lies about being done":

  1. check_loops.py    - every loop's verifier honours its own examples
  2. check_catalog.py  - the catalog index matches what is on disk

Exit 0 only if both pass. This is what `python3 ci/check.py` runs locally and
what the GitHub Actions job runs on every push and pull request.

Dependencies: Python 3.8+ standard library only.
"""

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKS = ["check_loops.py", "check_catalog.py"]


def main() -> int:
    overall = 0
    for check in CHECKS:
        print(f"\n=== {check} ===")
        result = subprocess.run([sys.executable, str(HERE / check)])
        if result.returncode != 0:
            overall = 1

    print("\n" + "=" * 40)
    if overall:
        print("CI FAILED")
    else:
        print("CI PASSED — loops and catalog are both honest")
    return overall


if __name__ == "__main__":
    sys.exit(main())
