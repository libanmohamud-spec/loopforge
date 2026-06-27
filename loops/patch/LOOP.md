# Patch loop

> Reproduce a vulnerability, apply a candidate fix, and refuse to call it done
> until the PoC no longer works and tests still pass.

| | |
|---|---|
| **Use when** | You have a confirmed vulnerability and a candidate patch to review |
| **Input** | PoC, vulnerable codebase, unified-diff patch |
| **Artifact** | `PATCH_FILE` (unified diff against the vulnerable tree) |
| **Stop condition** | `python3 verify.py PATCH_FILE` exits `0` |
| **Works with** | Runs after threat-model or vuln-scan scopes the surface |

## Files

- `prompt.md` — the agent instruction that drives the loop
- `verify.py` — executing stop condition (reproduces, applies, re-verifies, tests)
- `fixture/` — bundled CWE-78 command-injection lab (`loop.config.json` declares commands)
- `examples/good.patch` — fixes the bug, tests pass
- `examples/no-fix.patch` — cosmetic change only; gate rejects
- `examples/breaks-tests.patch` — fixes the bug but breaks tests; gate rejects
- `ci.json` — CI manifest for example cases

## The loop

```
        ┌─────────────────────────────────────────────┐
        │                                             │
        ▼                                             │
  produce / revise  ──►  PATCH_FILE  ──►  verify.py (executes)
                                              │   │
                                  exit 1 ─────┘   │ exit 0
                                  (keep going)    ▼
                                               loop closes
```

Unlike static-artifact loops, the patch verifier **runs commands** declared in
the fixture's `loop.config.json`. It generates an evidence line such as
`poc_before_exit=0 poc_after_exit=1 tests_after_exit=0`. The agent cannot
forge that record.

## Reason codes

| Code | Blocking | Meaning |
|---|---|---|
| `PT-POC-BEFORE` | yes | PoC did not reproduce on the vulnerable baseline |
| `PT-APPLY-FAIL` | yes | patch did not apply cleanly |
| `PT-NO-FIX` | yes | PoC still reproduces after patch |
| `PT-BREAKS-TESTS` | yes | tests fail after patch |

This namespace (`PT-*`) is local to Loopforge.

## Sandbox

The verifier executes project-declared commands from `loop.config.json`. Run it
only against fixtures you trust, inside a sandbox or CI runner, not on
production systems.
