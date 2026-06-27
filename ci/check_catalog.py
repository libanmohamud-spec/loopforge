#!/usr/bin/env python3
"""
check_catalog.py - enforce that catalog.json does not lie about what is on disk.

The loops can't lie about being done; the index that advertises them still can.
This closes that seam. It asserts:

  CAT-VERIFIER   every catalog entry's verifier path exists on disk
  CAT-LOOPDIR    every catalog entry has a directory under loops/
  CAT-UNINDEXED  every directory under loops/ appears in the catalog
  CAT-WORKSWITH  every works_with target is a shipped loop or a declared roadmap entry
  CAT-DUP-ID     no duplicate loop ids in the catalog

Exit 0 if the index is honest, else 1.
Dependencies: Python 3.8+ standard library only.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "catalog.json"
LOOPS = ROOT / "loops"


def fail(code, message, refs=None):
    ref = f"  [{', '.join(refs)}]" if refs else ""
    print(f"  FAIL  {code:14} {message}{ref}")


def main() -> int:
    if not CATALOG.exists():
        print(f"no catalog.json at {CATALOG}", file=sys.stderr)
        return 1

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    entries = catalog.get("loops", [])
    roadmap = set(catalog.get("roadmap", []))
    catalog_ids = [entry.get("id") for entry in entries]
    shipped = set(catalog_ids)

    failures = 0

    seen, dupes = set(), set()
    for loop_id in catalog_ids:
        if loop_id in seen:
            dupes.add(loop_id)
        seen.add(loop_id)
    for duplicate in sorted(map(str, dupes)):
        fail("CAT-DUP-ID", f"duplicate loop id in catalog: {duplicate}")
        failures += 1

    for entry in entries:
        loop_id = entry.get("id")
        verifier = entry.get("verifier")
        if not verifier or not (ROOT / verifier).exists():
            fail("CAT-VERIFIER", f"loop {loop_id}: verifier path missing on disk: {verifier}", [str(loop_id)])
            failures += 1
        if not (LOOPS / str(loop_id)).is_dir():
            fail("CAT-LOOPDIR", f"loop {loop_id}: no directory at loops/{loop_id}", [str(loop_id)])
            failures += 1

    if LOOPS.is_dir():
        on_disk = sorted(path.name for path in LOOPS.iterdir() if path.is_dir())
        for name in on_disk:
            if name not in shipped:
                fail("CAT-UNINDEXED", f"loops/{name} exists on disk but is not in the catalog", [name])
                failures += 1

    for entry in entries:
        loop_id = entry.get("id")
        for target in entry.get("works_with", []):
            if target not in shipped and target not in roadmap:
                fail(
                    "CAT-WORKSWITH",
                    f"loop {loop_id}: works_with target '{target}' is neither a shipped loop nor a roadmap entry",
                    [str(loop_id)],
                )
                failures += 1

    print("")
    print(
        f"catalog: {len(entries)} loop(s), {len(roadmap)} roadmap entry(ies), "
        f"{failures} failure(s)"
    )
    if failures:
        print("RESULT: CATALOG DISHONEST — the index does not match disk")
        return 1
    print("RESULT: CATALOG HONEST — the index matches disk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
