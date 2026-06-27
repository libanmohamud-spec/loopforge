# Changelog

## v0.2.0

- Add **patch** loop with executing verifier (reproduce PoC → apply patch → re-verify → tests)
- Bundled CWE-78 command-injection fixture with `good`, `no-fix`, and `breaks-tests` examples
- Introduce per-loop `ci.json` manifest; `check_loops.py` is manifest-driven with legacy fallback
- Promote `patch` out of roadmap; catalog version `0.2.0`

## v0.1.0

- Initial release: threat-model loop, catalog honesty CI, GitHub Pages site
