#!/usr/bin/env python3
"""
verify.py - the stop condition for the threat-model loop.

A threat model is "done" when it is a complete, internally consistent graph:
every threat hangs off an entry point and an asset that actually exist, every
entry point on the attack surface is modeled by at least one threat, and every
high/critical threat carries a mitigation. This verifier proves those
properties deterministically. It cannot tell you the threat model is smart.
It can tell you it is not lying about being finished.

Usage:
    python3 verify.py THREAT_MODEL.json

Exit code:
    0  no blocking findings - the loop may close
    1  one or more blocking findings - keep iterating
    2  the file could not be read or parsed

Dependencies: Python 3.8+ standard library only.
"""

import json
import sys

STRIDE = {"S", "T", "R", "I", "D", "E"}
CLASSIFICATIONS = {"public", "internal", "confidential", "restricted"}
SEVERITIES = {"low", "medium", "high", "critical"}
BLOCKING_SEVERITY = {"high", "critical"}
AUTH_LEVELS = {"none", "user", "service", "admin"}
SENSITIVE = {"confidential", "restricted"}


class Finding:
    def __init__(self, code, blocking, message, refs=None):
        self.code = code
        self.blocking = blocking
        self.message = message
        self.refs = refs or []

    def line(self):
        tag = "BLOCK" if self.blocking else " WARN"
        ref = f"  [{', '.join(self.refs)}]" if self.refs else ""
        return f"  {tag}  {self.code:24} {self.message}{ref}"


def load(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"error: file not found: {path}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"error: {path} is not valid JSON: {e}", file=sys.stderr)
        sys.exit(2)


def require_lists(model, findings):
    """Structural gate. If the shape is wrong, deeper checks are meaningless."""
    ok = True
    for key in ("assets", "trust_boundaries", "entry_points", "threats", "mitigations"):
        if not isinstance(model.get(key), list):
            findings.append(Finding("TM-SCHEMA", True,
                                    f"missing or non-list section: {key}"))
            ok = False
    if not isinstance(model.get("system"), str) or not model.get("system"):
        findings.append(Finding("TM-SCHEMA", True, "missing system name"))
        ok = False
    return ok


def ids_of(items):
    return [it.get("id") for it in items if isinstance(it, dict)]


def check_unique_ids(model, findings):
    for key in ("assets", "trust_boundaries", "entry_points", "threats", "mitigations"):
        seen, dupes = set(), set()
        for _id in ids_of(model[key]):
            if _id in seen:
                dupes.add(_id)
            seen.add(_id)
        if dupes:
            findings.append(Finding("TM-ID-DUP", True,
                                    f"duplicate ids in {key}", sorted(map(str, dupes))))


def check_referential_integrity(model, findings):
    asset_ids = set(ids_of(model["assets"]))
    boundary_ids = set(ids_of(model["trust_boundaries"]))
    entry_ids = set(ids_of(model["entry_points"]))
    mitig_ids = set(ids_of(model["mitigations"]))

    for e in model["entry_points"]:
        b = e.get("boundary")
        if b not in boundary_ids:
            findings.append(Finding("TM-REF-ENTRY-BOUNDARY", True,
                                    f"entry point {e.get('id')} references unknown boundary {b}",
                                    [str(e.get("id"))]))

    for t in model["threats"]:
        if t.get("entry_point") not in entry_ids:
            findings.append(Finding("TM-REF-THREAT-ENTRY", True,
                                    f"threat {t.get('id')} references unknown entry point {t.get('entry_point')}",
                                    [str(t.get("id"))]))
        for a in t.get("assets", []):
            if a not in asset_ids:
                findings.append(Finding("TM-REF-THREAT-ASSET", True,
                                        f"threat {t.get('id')} references unknown asset {a}",
                                        [str(t.get("id"))]))
        for m in t.get("mitigations", []):
            if m not in mitig_ids:
                findings.append(Finding("TM-REF-MITIGATION", True,
                                        f"threat {t.get('id')} references unknown mitigation {m}",
                                        [str(t.get("id"))]))


def check_coverage(model, findings):
    """The checks that catch a half-finished model dressed up to look done."""
    referenced_entries = {t.get("entry_point") for t in model["threats"]}
    for e in model["entry_points"]:
        if e.get("id") not in referenced_entries:
            findings.append(Finding("TM-COV-ENTRY", True,
                                    f"entry point {e.get('id')} is on the attack surface but no threat models it",
                                    [str(e.get("id"))]))

    boundaries_with_entries = {e.get("boundary") for e in model["entry_points"]}
    for b in model["trust_boundaries"]:
        if b.get("id") not in boundaries_with_entries:
            findings.append(Finding("TM-COV-BOUNDARY", False,
                                    f"trust boundary {b.get('id')} has no entry points crossing it",
                                    [str(b.get("id"))]))


def check_fields(model, findings):
    for a in model["assets"]:
        if a.get("classification") not in CLASSIFICATIONS:
            findings.append(Finding("TM-ASSET-CLASS", True,
                                    f"asset {a.get('id')} has invalid classification {a.get('classification')}",
                                    [str(a.get("id"))]))
    for e in model["entry_points"]:
        if e.get("auth") not in AUTH_LEVELS:
            findings.append(Finding("TM-ENTRY-AUTH", True,
                                    f"entry point {e.get('id')} has invalid auth {e.get('auth')}",
                                    [str(e.get("id"))]))
    for t in model["threats"]:
        stride = set(t.get("stride", []))
        if not stride or not stride.issubset(STRIDE):
            findings.append(Finding("TM-STRIDE-INVALID", True,
                                    f"threat {t.get('id')} has empty or invalid STRIDE {sorted(stride)}",
                                    [str(t.get("id"))]))
        if t.get("severity") not in SEVERITIES:
            findings.append(Finding("TM-SEV-INVALID", True,
                                    f"threat {t.get('id')} has invalid severity {t.get('severity')}",
                                    [str(t.get("id"))]))


def check_severity_mitigated(model, findings):
    for t in model["threats"]:
        if t.get("severity") in BLOCKING_SEVERITY and not t.get("mitigations"):
            findings.append(Finding("TM-SEV-UNMITIGATED", True,
                                    f"{t.get('severity')} threat {t.get('id')} has no mitigation",
                                    [str(t.get("id"))]))


def check_warnings(model, findings):
    """Non-blocking signal. An unauthenticated path to sensitive data is worth a look."""
    asset_class = {a.get("id"): a.get("classification") for a in model["assets"]}
    entry_auth = {e.get("id"): e.get("auth") for e in model["entry_points"]}
    for t in model["threats"]:
        auth = entry_auth.get(t.get("entry_point"))
        if auth == "none":
            for a in t.get("assets", []):
                if asset_class.get(a) in SENSITIVE:
                    findings.append(Finding("TM-WARN-NOAUTH-SENSITIVE", False,
                                            f"threat {t.get('id')}: unauthenticated entry point reaches {asset_class.get(a)} asset {a}",
                                            [str(t.get("id"))]))


def main():
    if len(sys.argv) != 2:
        print("usage: python3 verify.py THREAT_MODEL.json", file=sys.stderr)
        sys.exit(2)

    path = sys.argv[1]
    model = load(path)
    findings = []

    if not require_lists(model, findings):
        report(path, model, findings)
        sys.exit(1)

    check_unique_ids(model, findings)
    check_referential_integrity(model, findings)
    check_coverage(model, findings)
    check_fields(model, findings)
    check_severity_mitigated(model, findings)
    check_warnings(model, findings)

    blocking = [f for f in findings if f.blocking]
    report(path, model, findings)
    sys.exit(1 if blocking else 0)


def report(path, model, findings):
    name = model.get("system", "?") if isinstance(model, dict) else "?"
    counts = {}
    if isinstance(model, dict):
        for k in ("assets", "trust_boundaries", "entry_points", "threats", "mitigations"):
            v = model.get(k)
            counts[k] = len(v) if isinstance(v, list) else 0

    print(f"\nthreat-model verify  ::  {path}")
    if counts:
        print("  system: {}   assets:{assets} boundaries:{trust_boundaries} "
              "entries:{entry_points} threats:{threats} mitigations:{mitigations}"
              .format(name, **counts))
    print("")

    if not findings:
        print("  no findings.")
    else:
        for f in findings:
            print(f.line())

    blocking = [f for f in findings if f.blocking]
    warns = [f for f in findings if not f.blocking]
    print("")
    if blocking:
        print(f"  RESULT: BLOCKED  ({len(blocking)} blocking, {len(warns)} warning) "
              f"-- loop stays open")
    else:
        print(f"  RESULT: PASS  (0 blocking, {len(warns)} warning) -- loop may close")
    print("")


if __name__ == "__main__":
    main()
