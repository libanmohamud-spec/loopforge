#!/usr/bin/env python3
"""
check_loops.py - CI enforcement of the loop contract.

Every loop under loops/ must ship a verifier and examples that prove the gate
both passes good input and rejects bad input. How those examples are run is
declared per loop in ci.json:

    {
      "verifier": "verify.py",
      "cases": [
        { "name": "...", "args": ["examples/good.json"],  "expect": "zero"    },
        { "name": "...", "args": ["examples/bad.json"],   "expect": "nonzero" }
      ]
    }

A manifest lets static-artifact loops (threat-model) and executing loops
(patch) live under one contract: the runner only cares about declared exit
codes. Loops without a ci.json fall back to the convention that examples/*.json
must exit 0 and examples/*.fail.json must exit non-zero.

The contract requires at least one passing case and one rejecting case, so a
verifier that has stopped biting its own failing example fails CI.

Exit 0 if every check matched expectation, else 1.
Dependencies: Python 3.8+ standard library only.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOOPS = ROOT / "loops"


def cases_from_manifest(loop_dir):
    manifest = loop_dir / "ci.json"
    if not manifest.exists():
        return None
    data = json.loads(manifest.read_text(encoding="utf-8"))
    verifier = loop_dir / data.get("verifier", "verify.py")
    cases = []
    for case in data.get("cases", []):
        args = [
            str((loop_dir / arg)) if not arg.startswith("-") else arg
            for arg in case["args"]
        ]
        cases.append((
            case.get("name", " ".join(case["args"])),
            verifier,
            args,
            case.get("expect", "zero"),
        ))
    return cases


def cases_from_convention(loop_dir):
    verifier = loop_dir / "verify.py"
    examples = sorted((loop_dir / "examples").glob("*.json")) if (loop_dir / "examples").is_dir() else []
    cases = []
    for example in examples:
        expect = "nonzero" if ".fail." in example.name else "zero"
        cases.append((example.name, verifier, [str(example)], expect))
    return cases


def matched(code, expectation):
    return (code == 0) if expectation == "zero" else (code != 0)


def main() -> int:
    if not LOOPS.is_dir():
        print(f"no loops/ directory at {LOOPS}", file=sys.stderr)
        return 1

    checks = failures = loops_seen = 0

    for loop_dir in sorted(path for path in LOOPS.iterdir() if path.is_dir()):
        name = loop_dir.name
        if not (loop_dir / "verify.py").exists():
            print(f"FAIL  {name}: no verify.py (loop contract requires a verifier)")
            failures += 1
            continue

        cases = cases_from_manifest(loop_dir)
        if cases is None:
            cases = cases_from_convention(loop_dir)
        if not cases:
            print(f"FAIL  {name}: no ci.json cases and no examples/*.json")
            failures += 1
            continue

        loops_seen += 1
        expectations = {expect for _, _, _, expect in cases}
        if "zero" not in expectations:
            print(f"FAIL  {name}: contract requires at least one passing case")
            failures += 1
        if "nonzero" not in expectations:
            print(f"FAIL  {name}: contract requires a rejecting case the verifier blocks")
            failures += 1

        for label, verifier, args, expect in cases:
            result = subprocess.run(
                [sys.executable, str(verifier), *args],
                capture_output=True,
                text=True,
            )
            checks += 1
            if matched(result.returncode, expect):
                print(f"ok    {name}: {label} -> exit={result.returncode} (expected {expect})")
            else:
                print(f"FAIL  {name}: {label} -> exit={result.returncode} (expected {expect})")
                failures += 1

    print("")
    print(f"loops: {loops_seen}   checks: {checks}   failures: {failures}")
    if failures:
        print("RESULT: CI FAILED — the loop contract is not satisfied")
        return 1
    print("RESULT: CI PASSED — every verifier honours its own examples")
    return 0


if __name__ == "__main__":
    sys.exit(main())
