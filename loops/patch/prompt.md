# Patch loop — agent prompt

You are producing a minimal unified-diff patch that fixes a confirmed
vulnerability without breaking existing tests.

Your output is a single patch file that passes `verify.py` with exit 0.
The verifier **executes**: it reproduces the PoC on the unpatched fixture,
applies your patch, confirms the PoC no longer reproduces, and runs the test
suite. You are done only when the verifier exits 0. It prints an evidence
line you cannot forge.

## Inputs

- The vulnerable source tree (or the bundled fixture under `loops/patch/fixture/`)
- A PoC that proves the bug by side effect
- Existing tests that must keep passing

## Method

1. **Reproduce.** Run the PoC against the vulnerable baseline. If it does not
   reproduce, stop and fix the PoC or scope — do not patch blind.

2. **Fix minimally.** Change only what closes the attack path. Prefer
   eliminating shell interpolation over filtering inputs.

3. **Re-verify.** Apply the patch locally and confirm:
   - PoC no longer reproduces
   - tests still pass

4. **Emit a unified diff.** Output a clean `git apply`-able patch against the
   vulnerable tree root.

## Constraints

- Do not weaken tests to force a pass.
- Do not mark the loop done based on your own judgment — only `verify.py` exit 0
  closes it.
- Run the verifier in a sandbox. It executes commands from `loop.config.json`.

## Run the verifier

```bash
python3 loops/patch/verify.py YOUR.patch
```

Expected blocking codes when the patch is wrong:

- `PT-NO-FIX` — PoC still works after patch
- `PT-BREAKS-TESTS` — tests fail after patch
