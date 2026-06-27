# Loopforge

A library of security agent loops where the verify gate is **executable**, not
prose.

Most prompt catalogs ship the cheap half of a loop: the instruction. The
expensive half is the stop condition. "Looks complete" is not a stop condition.
A loop you can't verify is a loop that lies about being done.

Every loop in Loopforge ships with a runnable verifier. The agent proposes the
work. The verifier authorises the loop to close. Nothing else does.

```
produce / revise  ──►  artifact  ──►  verify.py
                                         │  │
                             exit 1 ─────┘  │ exit 0
                             (keep going)   ▼
                                         loop closes
```

## Loops

| Loop | Use when | Artifact | Stop condition |
|---|---|---|---|
| [threat-model](loops/threat-model/) | Before scanning a new codebase | `THREAT_MODEL.json` | static `verify.py` exits 0 |
| [patch](loops/patch/) | You have a confirmed bug and a candidate fix | unified-diff patch | executing `verify.py` exits 0 |

More to come: vuln-scan, triage, dependency-audit, secret-scan. Each arrives with
its own executable verifier or it does not arrive.

## Try it

```bash
# Threat-model (static artifact)
cd loops/threat-model
python3 verify.py examples/THREAT_MODEL.json       # PASS, exit 0
python3 verify.py examples/THREAT_MODEL.fail.json  # BLOCKED, exit 1

# Patch (executing verifier — run in a sandbox or CI)
cd ../patch
python3 verify.py examples/good.patch              # PASS
python3 verify.py examples/no-fix.patch            # BLOCKED (PT-NO-FIX)
python3 verify.py examples/breaks-tests.patch      # BLOCKED (PT-BREAKS-TESTS)

# Enforce the loop + catalog contract
python3 ci/check.py

# Preview the site locally (repo root is the site root)
npm run dev      # http://localhost:4173
```

**Patch loop sandbox:** the patch verifier executes commands declared in the
fixture's `loop.config.json` (PoC and tests). Run it only against fixtures you
trust, inside a sandbox or CI runner — not on production systems.

Site and catalog are served from repo root — no build step, no copied
artifacts. GitHub Pages: Settings → Pages → Deploy from branch `main`,
folder `/ (root)`. Include `.nojekyll` so Jekyll does not mangle paths.

Browse at `/` and read the guide at `/learn/`. Machine index:
`./catalog.json` (on a project page:
`https://<user>.github.io/loopforge/catalog.json`).

The failing example is half-finished and dressed up to look done: a threat
pointing at an entry point that does not exist, two entry points on the attack
surface with no threat modeling them, a critical threat with no mitigation. The
gate catches all of it.

## Contributing a loop

A loop is accepted when it ships:

1. `LOOP.md` — when to use it, the artifact it emits, the stop condition
2. `prompt.md` — the agent instruction
3. a **runnable verifier** that exits 0 only when the loop is genuinely done
4. a passing example and a failing example
5. `ci.json` — manifest of example cases and expected exit codes (legacy
   `examples/*.fail.json` convention still works for static JSON loops)

No verifier, no loop. The verifier is the point.

The machine index is `catalog.json`. CI asserts it matches disk: every entry
points at a real verifier, every loop under `loops/` is indexed, and every
`works_with` target is a shipped loop or an explicit roadmap entry.

## What a verifier is and isn't

The threat-model verifier proves the model is complete and internally
consistent: every threat hangs off a real entry point and a real asset, every
entry point on the surface is modeled, every high/critical threat is mitigated.
It does not judge whether the threat model is *good*. It guarantees the floor,
not the ceiling. That split is deliberate. Determinism belongs on the floor.

## License

MIT.
