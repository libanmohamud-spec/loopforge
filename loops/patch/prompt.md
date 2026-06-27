# Patch loop — agent prompt

You are fixing a single verified vulnerability in a project. Your output is a
patch (a unified diff) that the verifier accepts. You are done only when

```
python3 verify.py <your-patch> --project <repo>
```

exits 0. Do not declare the fix complete on your own reading of the diff. The
verifier reproduces the PoC, applies your patch, checks the PoC is gone, and
runs the tests. It holds the stop condition.

## Inputs

- A project containing the vulnerable code, a PoC that demonstrates the finding,
  and a test suite. The project's `loop.config.json` declares the `poc` and
  `tests` commands.
- A description of the finding (what is wrong and why).

If you cannot reproduce the PoC yourself first, stop and say so. A finding you
cannot reproduce is not one you can prove you fixed.

## Method

1. **Reproduce.** Run the PoC. Confirm it reproduces before you change anything.
2. **Understand the sink.** Find the exact line where untrusted input reaches
   the dangerous operation. Fix the cause, not the symptom.
3. **Patch minimally.** Change as little as possible. A small diff is easier to
   review and less likely to break behaviour.
4. **Preserve behaviour.** The existing tests encode what the code must still
   do. Do not change them to make a fix pass. If the fix legitimately changes an
   interface, that is a larger change than this loop is for; flag it.
5. **Verify by running, not reading.** Run the verifier. Read the reason code,
   revise, repeat.

## Stop condition

```
python3 verify.py <your-patch> --project <repo>   # must exit 0
```

The verifier blocks on: `PT-NO-REPRO`, `PT-BASELINE-TESTS`, `PT-APPLY-FAILED`,
`PT-NO-FIX`, `PT-BREAKS-TESTS`. Exit 0 means: reproduced before, gone after,
tests still green.

## Boundaries

A passing verifier proves the named finding is fixed and tests pass. It does
not authorise you to commit, push, open a PR, or deploy. Those are consequential
actions that need a human's approval. Leave a handoff: the patch, the evidence
line the verifier printed, and any sibling variants of the bug you noticed but
did not fix.
