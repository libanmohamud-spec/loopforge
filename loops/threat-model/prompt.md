# Threat-model loop — agent prompt

You are threat-modeling a codebase or system before any security scanning
begins. Use STRIDE per element: work threats from concrete components and
entry points, not from abstract worry lists.

Your output is a single file, `THREAT_MODEL.json`, that conforms to
`schema.json` and passes `verify.py` with zero blocking findings.

This is a loop, not a one-shot. Produce the artifact, run the verifier, read
the findings, fix the model, repeat. You are done only when the verifier exits
0. Do not declare the threat model complete on your own judgment. The verifier
holds the stop condition.

## Inputs

- The source tree, architecture notes, or system description you were given.
- If you were given nothing concrete, ask for the system boundary before
  modeling. Do not invent a system.

## Method

Work in this order. Steps 1–4 are analysis; step 5 is the artifact the
verifier checks.

1. **Assets.** List what an attacker wants or what must not be harmed.
   Classify each: public, internal, confidential, restricted.

2. **Trust boundaries.** Identify where control or trust changes hands
   (user to agent, agent to infrastructure, service to service). Record what
   each boundary separates in `between`.

3. **Data flows and entry points.** Map interactions between components.
   Flag every flow that crosses a trust boundary — each crossing is an entry
   point on the attack surface. Record which boundary it crosses and its
   authentication level (none, user, service, admin).

4. **Questions and assumptions.** Before writing threats, note what you do
   not know and the defaults you are using. Put this in the top-level
   `description` field. State assumptions explicitly rather than smuggling
   them into threats.

5. **Threats and mitigations.** For each entry point, apply STRIDE per
   element:

   - **S** — Spoofing
   - **T** — Tampering
   - **R** — Repudiation
   - **I** — Information disclosure
   - **D** — Denial of service
   - **E** — Elevation of privilege

   For each threat:

   - Tie it to one entry point and the asset(s) at risk.
   - Write a specific `title` — name the component, the attack path, and
     what goes wrong. Avoid generic labels like "SQL injection."
   - Pick one or more STRIDE letters that actually apply.
   - Assign `severity` from realistic likelihood and impact given the
     design — not every theoretical attack deserves critical.

   For each mitigation:

   - Say what it does in `description`.
   - Set `status` to implemented, proposed, or accepted-risk.
   - Every high and critical threat must reference at least one mitigation.

## Realism and prioritization (your judgment — the ceiling)

The verifier guarantees structure, not quality. You must supply the rest:

- Focus on threats that are plausible for this system, not every fantastical
  scenario the input might suggest.
- Prefer threats an attacker could reach through a modeled entry point over
  hypothetical supply-chain catastrophes with no path from the surface.
- When a threat is too unlikely to defend against, either omit it (if no
  credible path) or mark the mitigation `accepted-risk` with a one-line
  reason in the mitigation description.
- Severity should reflect both likelihood and impact. A critical severity
  means credible exploit path plus serious harm — not merely "sounds scary."

Document notable omissions or accepted risks in the top-level `description`
so reviewers know what you deliberately deprioritized.

## Stop condition (the floor — the verifier)

```
python3 verify.py THREAT_MODEL.json   # must exit 0
```

The verifier checks, deterministically:

- the artifact matches the schema and ids are unique;
- every threat points at an entry point and assets that exist;
- every entry point on the surface is modeled by at least one threat
  (an unmodeled entry point is the most common way a threat model lies
  about being finished);
- every high/critical threat has a mitigation;
- STRIDE, severity, classification, and auth values are valid.

It also emits non-blocking warnings, for example an unauthenticated entry
point that reaches a confidential or restricted asset. Warnings do not stop
the loop, but read them.

## Floor vs ceiling

| The verifier proves (floor) | You must judge (ceiling) |
|---|---|
| Every entry point has at least one threat | Whether the threat is the right one |
| References are internally consistent | Whether likelihood and impact are realistic |
| High/critical threats have mitigations | Whether mitigations are sound |
| Required fields and enums are valid | Whether assumptions are stated honestly |

A complete, consistent, shallow model passes. That is intentional. Bring
insight, realism, and prioritization; let the gate hold the floor.

## After the loop closes

Optionally render a human-readable report:

```
python3 render.py THREAT_MODEL.json > THREAT_MODEL.md
```

Render only after `verify.py` passes. The JSON is the source of truth.
