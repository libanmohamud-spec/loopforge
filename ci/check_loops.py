#!/usr/bin/env python3
"""
check_loops.py - CI enforcement of the loop contract.

Each loop may declare a ci.json manifest listing example artifacts and expected
verifier exit codes. When no manifest exists, falls back to the legacy
convention:

    examples/*.fail.json   ->  verifier MUST exit non-zero
    examples/*.json        ->  verifier MUST exit 0

Exit 0 if every check matched expectation, else 1.
Dependencies: Python 3.8+ standard library only.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOOPS = ROOT / "loops"


def matched(code: int, expectation: str) -> bool:
    return (code == 0) if expectation == "zero" else (code != 0)


def load_manifest(loop_dir: Path):
    manifest = loop_dir / "ci.json"
    if not manifest.is_file():
        return None
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        print(f"FAIL  {loop_dir.name}: invalid ci.json: {error}")
        return "invalid"

    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        print(f"FAIL  {loop_dir.name}: ci.json must include a non-empty cases array")
        return "invalid"

    parsed = []
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            print(f"FAIL  {loop_dir.name}: ci.json cases[{index}] must be an object")
            return "invalid"
        example = case.get("example")
        expect = case.get("expect")
        if not isinstance(example, str) or not example:
            print(f"FAIL  {loop_dir.name}: ci.json cases[{index}] missing example path")
            return "invalid"
        if expect not in (0, "zero", "nonzero"):
            print(f"FAIL  {loop_dir.name}: ci.json cases[{index}] expect must be 0, zero, or nonzero")
            return "invalid"
        normalized = "zero" if expect in (0, "zero") else "nonzero"
        parsed.append((loop_dir / example, normalized))
    return parsed


def legacy_cases(examples_dir: Path):
    if not examples_dir.is_dir():
        return []
    cases = []
    for example in sorted(examples_dir.glob("*.json")):
        expectation = "nonzero" if ".fail." in example.name else "zero"
        cases.append((example, expectation))
    return cases


def main() -> int:
    if not LOOPS.is_dir():
        print(f"no loops/ directory at {LOOPS}", file=sys.stderr)
        return 1

    checks = 0
    failures = 0
    loops_seen = 0

    for loop_dir in sorted(path for path in LOOPS.iterdir() if path.is_dir()):
        verifier = loop_dir / "verify.py"
        if not verifier.exists():
            print(f"FAIL  {loop_dir.name}: no verify.py (loop contract requires a verifier)")
            failures += 1
            continue

        manifest = load_manifest(loop_dir)
        if manifest == "invalid":
            failures += 1
            continue

        cases = manifest if manifest is not None else legacy_cases(loop_dir / "examples")
        if not cases:
            print(f"FAIL  {loop_dir.name}: no ci.json cases and no legacy examples/*.json")
            failures += 1
            continue

        has_pass = any(expectation == "zero" for _, expectation in cases)
        has_fail = any(expectation == "nonzero" for _, expectation in cases)
        loops_seen += 1
        if not has_pass:
            print(f"FAIL  {loop_dir.name}: contract requires at least one passing example")
            failures += 1
        if not has_fail:
            print(f"FAIL  {loop_dir.name}: contract requires a failing example the verifier rejects")
            failures += 1

        for example, expectation in cases:
            if not example.is_file():
                print(f"FAIL  {loop_dir.name}: example missing on disk: {example.relative_to(ROOT)}")
                failures += 1
                continue

            result = subprocess.run(
                [sys.executable, str(verifier), str(example)],
                capture_output=True,
                text=True,
            )
            checks += 1
            rel = example.relative_to(ROOT)
            if matched(result.returncode, expectation):
                print(
                    f"ok    {loop_dir.name}: {rel.name} exit={result.returncode} "
                    f"(expected {expectation})"
                )
            else:
                print(
                    f"FAIL  {loop_dir.name}: {rel.name} exit={result.returncode} "
                    f"(expected {expectation})"
                )
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
