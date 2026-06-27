# Changelog

## v0.2.1

Align patch loop and CI contract with the reference implementation:

- `examples/project/` fixture layout (`poc/`, `tests/`, `loop.config.json`)
- Executing verifier with baseline checks (`PT-NO-REPRO`, `PT-BASELINE-TESTS`)
- `ci.json` manifest uses `{ verifier, cases: [{ name, args, expect }] }`

## v0.2.0

Added the **patch loop** — the first executing verifier in the catalog.

- `loops/patch/` fixes a verified finding and proves by execution that the PoC
  reproduces before the patch, no longer reproduces after it, and the project's
  tests still pass. Reason codes: `PT-NO-REPRO`, `PT-BASELINE-TESTS`,
  `PT-APPLY-FAILED`, `PT-NO-FIX`, `PT-BREAKS-TESTS`.
- Per-loop `ci.json` manifests for static and executing loops.

Requires `git` on PATH for the patch verifier.

## v0.1.0

Initial release: threat-model loop, catalog honesty CI, GitHub Pages site.
