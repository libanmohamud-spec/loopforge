#!/usr/bin/env python3
"""
check_catalog.py - enforce that catalog.json does not lie about what is on disk.

The loops can't lie about being done; the index that advertises them still can.
This closes that seam.

Reason codes:
  CAT-VERIFIER      verifier path missing on disk
  CAT-VERIFIER-PATH verifier path not loops/{id}/verify.py
  CAT-LOOPDIR       catalog entry has no loops/{id}/ directory
  CAT-UNINDEXED     directory under loops/ not listed in catalog
  CAT-WORKSWITH     works_with target neither shipped nor on roadmap
  CAT-DUP-ID        duplicate loop id in catalog
  CAT-SCHEMA        missing required catalog field

Exit 0 if the index is honest, else 1.
Dependencies: Python 3.8+ standard library only.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "catalog.json"
LOOPS = ROOT / "loops"

REQUIRED_TOP = ("name", "description", "version", "loops")
REQUIRED_LOOP = (
    "id",
    "title",
    "summary",
    "use_when",
    "artifact",
    "verifier",
    "stop_condition",
    "category",
    "works_with",
)


def fail(code, message, refs=None):
    ref = f"  [{', '.join(refs)}]" if refs else ""
    print(f"  FAIL  {code:18} {message}{ref}")


def main() -> int:
    if not CATALOG.exists():
        print(f"no catalog.json at {CATALOG}", file=sys.stderr)
        return 1

    try:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        fail("CAT-SCHEMA", f"invalid JSON: {error}")
        print("\nRESULT: CATALOG DISHONEST — the index does not match disk")
        return 1

    failures = 0

    for field in REQUIRED_TOP:
        if field not in catalog:
            fail("CAT-SCHEMA", f"missing top-level field: {field}")
            failures += 1

    entries = catalog.get("loops", [])
    if not isinstance(entries, list):
        fail("CAT-SCHEMA", "loops must be an array")
        failures += 1
        entries = []

    roadmap_raw = catalog.get("roadmap", [])
    if not isinstance(roadmap_raw, list):
        fail("CAT-SCHEMA", "roadmap must be an array when present")
        failures += 1
        roadmap_raw = []

    roadmap = {entry for entry in roadmap_raw if isinstance(entry, str)}
    catalog_ids = []
    shipped = {entry.get("id") for entry in entries if isinstance(entry, dict) and isinstance(entry.get("id"), str)}

    for index, entry in enumerate(entries):
        prefix = f"loops[{index}]"
        if not isinstance(entry, dict):
            fail("CAT-SCHEMA", f"{prefix} must be an object")
            failures += 1
            continue

        for field in REQUIRED_LOOP:
            if field not in entry:
                fail("CAT-SCHEMA", f"{prefix} missing field: {field}")
                failures += 1

        loop_id = entry.get("id")
        if not isinstance(loop_id, str) or not loop_id:
            fail("CAT-SCHEMA", f"{prefix} has invalid id")
            failures += 1
            continue

        catalog_ids.append(loop_id)

        expected_verifier = f"loops/{loop_id}/verify.py"
        verifier = entry.get("verifier")
        if verifier != expected_verifier:
            fail(
                "CAT-VERIFIER-PATH",
                f"loop {loop_id}: verifier must be {expected_verifier}, got {verifier!r}",
                [loop_id],
            )
            failures += 1

        if not verifier or not (ROOT / str(verifier)).is_file():
            fail("CAT-VERIFIER", f"loop {loop_id}: verifier path missing on disk: {verifier}", [loop_id])
            failures += 1

        if not (LOOPS / loop_id).is_dir():
            fail("CAT-LOOPDIR", f"loop {loop_id}: no directory at loops/{loop_id}", [loop_id])
            failures += 1

        works_with = entry.get("works_with", [])
        if not isinstance(works_with, list):
            fail("CAT-SCHEMA", f"loop {loop_id}: works_with must be an array", [loop_id])
            failures += 1
            continue

        for target in works_with:
            if not isinstance(target, str):
                fail("CAT-WORKSWITH", f"loop {loop_id}: works_with entries must be strings", [loop_id])
                failures += 1
                continue
            if target not in shipped and target not in roadmap:
                fail(
                    "CAT-WORKSWITH",
                    f"loop {loop_id}: works_with target {target!r} is neither a shipped loop nor a roadmap entry",
                    [loop_id],
                )
                failures += 1

    seen, dupes = set(), set()
    for loop_id in catalog_ids:
        if loop_id in seen:
            dupes.add(loop_id)
        seen.add(loop_id)
    for loop_id in sorted(dupes):
        fail("CAT-DUP-ID", f"duplicate loop id in catalog: {loop_id}", [loop_id])
        failures += 1

    if LOOPS.is_dir():
        on_disk = sorted(path.name for path in LOOPS.iterdir() if path.is_dir())
        for name in on_disk:
            if name not in shipped:
                fail("CAT-UNINDEXED", f"loops/{name} exists on disk but is not in the catalog", [name])
                failures += 1

    print("")
    print(
        f"catalog: {len(shipped)} loop(s), {len(roadmap)} roadmap entry(ies), "
        f"{failures} failure(s)"
    )
    if failures:
        print("RESULT: CATALOG DISHONEST — the index does not match disk")
        return 1
    print("RESULT: CATALOG HONEST — the index matches disk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
