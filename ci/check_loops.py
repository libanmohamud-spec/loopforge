#!/usr/bin/env python3
"""
check_loops.py - CI enforcement of the loop contract.

Walks every loop under loops/, runs its verifier against every example, and
asserts the exit code by naming convention:

    examples/*.fail.json   ->  verifier MUST exit non-zero (the gate must bite)
    examples/*.json        ->  verifier MUST exit 0        (the loop may close)

This is what makes the loop contract self-policing. A new loop that ships a
verify.py plus a passing and a failing example is picked up automatically. A
verifier that has stopped biting its own failing example fails CI.

Exit 0 if every check matched expectation, else 1.
Dependencies: Python 3.8+ standard library only.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOOPS = ROOT / "loops"


def expected_exit(example: Path) -> str:
    return "nonzero" if ".fail." in example.name else "zero"


def matched(code: int, expectation: str) -> bool:
    return (code == 0) if expectation == "zero" else (code != 0)


def main() -> int:
    if not LOOPS.is_dir():
        print(f"no loops/ directory at {LOOPS}", file=sys.stderr)
        return 1

    checks = 0
    failures = 0
    loops_seen = 0

    for loop_dir in sorted(p for p in LOOPS.iterdir() if p.is_dir()):
        verifier = loop_dir / "verify.py"
        examples_dir = loop_dir / "examples"
        if not verifier.exists():
            print(f"FAIL  {loop_dir.name}: no verify.py (loop contract requires a verifier)")
            failures += 1
            continue
        if not examples_dir.is_dir():
            print(f"FAIL  {loop_dir.name}: no examples/ (contract requires a passing and a failing example)")
            failures += 1
            continue

        examples = sorted(examples_dir.glob("*.json"))
        if not examples:
            print(f"FAIL  {loop_dir.name}: examples/ has no .json artifacts")
            failures += 1
            continue

        has_pass = any(".fail." not in e.name for e in examples)
        has_fail = any(".fail." in e.name for e in examples)
        loops_seen += 1
        if not has_pass:
            print(f"FAIL  {loop_dir.name}: contract requires at least one passing example")
            failures += 1
        if not has_fail:
            print(f"FAIL  {loop_dir.name}: contract requires a failing example the verifier rejects")
            failures += 1

        for example in examples:
            expectation = expected_exit(example)
            result = subprocess.run(
                [sys.executable, str(verifier), str(example)],
                capture_output=True, text=True,
            )
            checks += 1
            ok = matched(result.returncode, expectation)
            rel = example.relative_to(ROOT)
            if ok:
                print(f"ok    {loop_dir.name}: {rel.name} exit={result.returncode} (expected {expectation})")
            else:
                print(f"FAIL  {loop_dir.name}: {rel.name} exit={result.returncode} (expected {expectation})")
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
