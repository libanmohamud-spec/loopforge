#!/usr/bin/env python3
"""
render.py - turn THREAT_MODEL.json into a readable THREAT_MODEL.md.

The JSON is the source of truth and the thing the verifier checks. The
markdown is for humans to read in a PR. Render only after verify.py passes.

Usage:
    python3 render.py THREAT_MODEL.json > THREAT_MODEL.md

Dependencies: Python 3.8+ standard library only.
"""

import json
import sys

STRIDE_NAMES = {
    "S": "Spoofing", "T": "Tampering", "R": "Repudiation",
    "I": "Information disclosure", "D": "Denial of service",
    "E": "Elevation of privilege",
}


def main():
    if len(sys.argv) != 2:
        print("usage: python3 render.py THREAT_MODEL.json", file=sys.stderr)
        sys.exit(2)

    with open(sys.argv[1], encoding="utf-8") as f:
        m = json.load(f)

    asset_name = {a["id"]: a["name"] for a in m["assets"]}
    entry_name = {e["id"]: e["name"] for e in m["entry_points"]}
    out = []

    out.append(f"# Threat model: {m['system']}")
    if m.get("description"):
        out.append("")
        out.append(m["description"])
    out.append("")

    out.append("## Assets")
    out.append("")
    out.append("| ID | Asset | Classification |")
    out.append("|---|---|---|")
    for a in m["assets"]:
        out.append(f"| {a['id']} | {a['name']} | {a['classification']} |")
    out.append("")

    out.append("## Trust boundaries")
    out.append("")
    for b in m["trust_boundaries"]:
        between = " \u2194 ".join(b.get("between", [])) or "-"
        out.append(f"- **{b['id']}** {b['name']}  ({between})")
    out.append("")

    out.append("## Entry points")
    out.append("")
    out.append("| ID | Entry point | Boundary | Auth |")
    out.append("|---|---|---|---|")
    for e in m["entry_points"]:
        out.append(f"| {e['id']} | {e['name']} | {e['boundary']} | {e['auth']} |")
    out.append("")

    out.append("## Threats")
    out.append("")
    for t in sorted(m["threats"], key=lambda x: ["critical", "high", "medium", "low"].index(x["severity"])):
        stride = ", ".join(STRIDE_NAMES.get(s, s) for s in t["stride"])
        out.append(f"### {t['id']} \u2014 {t['title']}")
        out.append("")
        out.append(f"- **Severity:** {t['severity']}")
        out.append(f"- **STRIDE:** {stride}")
        out.append(f"- **Entry point:** {t['entry_point']} ({entry_name.get(t['entry_point'], '?')})")
        assets = ", ".join(f"{a} ({asset_name.get(a, '?')})" for a in t["assets"])
        out.append(f"- **Assets at risk:** {assets}")
        mits = ", ".join(t["mitigations"]) if t["mitigations"] else "_none_"
        out.append(f"- **Mitigations:** {mits}")
        out.append("")

    out.append("## Mitigations")
    out.append("")
    out.append("| ID | Mitigation | Status |")
    out.append("|---|---|---|")
    for mit in m["mitigations"]:
        out.append(f"| {mit['id']} | {mit['description']} | {mit['status']} |")
    out.append("")

    text = "\n".join(out)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    print(text)


if __name__ == "__main__":
    main()
