# Patch loop

> Fix a verified finding, and refuse to call it fixed until execution proves
> the vulnerability is gone and the tests still pass.

| | |
|---|---|
| **Use when** | You have a reproducible finding (ideally from the triage loop) and a candidate fix |
| **Input** | A project with a PoC and a test suite, plus a candidate patch |
| **Artifact** | A patch (unified diff). The verifier emits the evidence record. |
| **Stop condition** | `python3 verify.py <patch>` exits `0` |
| **Works with** | Consumes a finding handed down by the triage loop |

## What makes this loop different

The threat-model loop verifies a static artifact. This one cannot. A patch is
only "done" if it actually fixes the bug without breaking anything, and the
only honest way to know that is to run it. So the verifier executes the proof
itself rather than trusting a result the agent wrote down:

1. the PoC reproduces on the unpatched project (the finding is real)
2. the patch applies cleanly
3. the PoC no longer reproduces after the patch (it is actually fixed)
4. the project's tests still pass (nothing was broken)

The agent cannot fake evidence it did not produce.

## Files

- `prompt.md` — the agent instruction that drives the loop
- `verify.py` — the executing verifier (Python 3.8+ stdlib, plus `git`)
- `examples/project/` — a small project with a real CWE-78 command injection,
  a PoC (`poc/poc.py`) and tests (`tests/`)
- `examples/good.patch` — a fix that passes
- `examples/bad-no-fix.patch` — a cosmetic change that does not fix the bug
- `examples/bad-breaks-tests.patch` — a fix that breaks behaviour

## The loop

```
        ┌──────────────────────────────────────────────────┐
        │                                                  │
        ▼                                                  │
  revise patch  ──►  patch  ──►  verify.py (runs PoC + tests)
                                       │   │
                           exit 1 ─────┘   │ exit 0
                           (keep going)    ▼
                                        loop closes
```

## Running it

```
# against the bundled example
python3 verify.py examples/good.patch

# against your own project
python3 verify.py my-fix.diff --project /path/to/repo
```

The project must carry a `loop.config.json` declaring its `poc` and `tests`
commands, or you can pass `--poc` and `--tests` directly. The verifier runs
those commands, so run it in a container or sandbox, not blindly on a
workstation. It never runs anything the project config did not declare.

## Reason codes

| Code | Blocking | Meaning |
|---|---|---|
| `PT-NO-REPRO` | yes | PoC does not reproduce on the unpatched project; nothing to verify |
| `PT-BASELINE-TESTS` | yes | tests already fail before the patch; fix the baseline first |
| `PT-APPLY-FAILED` | yes | patch does not apply cleanly |
| `PT-NO-FIX` | yes | PoC still reproduces after the patch |
| `PT-BREAKS-TESTS` | yes | tests fail after the patch |

This namespace (`PT-*`) is local to Loopforge and unrelated to any product
reason codes.

## What the verifier cannot do

It proves the named finding is fixed and the existing tests still pass. It does
not prove the fix is idiomatic, that it closes sibling variants of the bug, or
that the test suite is adequate. Floor, not ceiling.
