# Threat-model loop

> Build a structured threat model for a system before you scan it, and refuse
> to call it done until it is complete and internally consistent.

| | |
|---|---|
| **Use when** | Starting on a new or unfamiliar codebase, before vuln scanning or triage |
| **Input** | Source tree, architecture notes, or a system description |
| **Artifact** | `THREAT_MODEL.json` (machine-checkable), optionally rendered to `THREAT_MODEL.md` |
| **Stop condition** | `python3 verify.py THREAT_MODEL.json` exits `0` |
| **Works with** | Hands a scoped attack surface to the vuln-scan and triage loops downstream |

## Files

- `prompt.md` — the agent instruction that drives the loop
- `schema.json` — the contract for the artifact
- `verify.py` — the executable stop condition (Python 3.8+, stdlib only)
- `render.py` — optional, turns the JSON into a readable `THREAT_MODEL.md`
- `examples/THREAT_MODEL.json` — a passing model
- `examples/THREAT_MODEL.fail.json` — a broken model that the gate rejects

## The loop

```
        ┌─────────────────────────────────────────────┐
        │                                             │
        ▼                                             │
  produce / revise  ──►  THREAT_MODEL.json  ──►  verify.py
                                                   │   │
                                       exit 1 ─────┘   │ exit 0
                                       (keep going)    ▼
                                                    loop closes
```

The model proposes the threat model. The verifier authorises the loop to
close. Nothing else does.

## Reason codes

The verifier emits named codes so a failure is actionable, not a vibe.

| Code | Blocking | Meaning |
|---|---|---|
| `TM-SCHEMA` | yes | missing section or malformed shape |
| `TM-ID-DUP` | yes | duplicate id within a collection |
| `TM-REF-ENTRY-BOUNDARY` | yes | entry point references a boundary that does not exist |
| `TM-REF-THREAT-ENTRY` | yes | threat references an entry point that does not exist |
| `TM-REF-THREAT-ASSET` | yes | threat references an asset that does not exist |
| `TM-REF-MITIGATION` | yes | threat references a mitigation that does not exist |
| `TM-COV-ENTRY` | yes | an entry point on the surface has no threat |
| `TM-COV-BOUNDARY` | no | a trust boundary has no entry points crossing it |
| `TM-ASSET-CLASS` | yes | invalid asset classification |
| `TM-ENTRY-AUTH` | yes | invalid entry-point auth level |
| `TM-STRIDE-INVALID` | yes | threat has empty or invalid STRIDE |
| `TM-SEV-INVALID` | yes | invalid severity |
| `TM-SEV-UNMITIGATED` | yes | high/critical threat with no mitigation |
| `TM-WARN-NOAUTH-SENSITIVE` | no | unauthenticated entry point reaches a confidential/restricted asset |

This namespace (`TM-*`) is local to Loopforge and unrelated to any product
reason codes.
