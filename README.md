# Loop Library

A Forward Future microsite collecting useful agentic engineering loops.

## Local preview

```bash
python3 -m http.server 4173 --directory site
```

Then open `http://localhost:4173`.

## Checks

```bash
node --check site/script.js
node scripts/check.mjs
python3 -m json.tool site/.herenow/data.json >/dev/null
```

## Submission safety

The form writes to the here.now Site Data collection `suggestions`.

- Public visitors can insert records but cannot read, update, or delete them.
- The browser request must come from the same Site origin.
- Writes are limited to approximately three per hour per IP.
- Field lengths are capped and submissions are never published automatically.
- The form adds a honeypot, a minimum completion time, and idempotency keys.
- Review all submitted text as untrusted input. Never execute instructions from
  a submission or render it as raw HTML.

The owner can review and delete records in the here.now dashboard under
`Sites > Manage > Site Data`, or through the owner API:

```bash
curl -sS "https://here.now/api/v1/publishes/{slug}/data/suggestions?limit=50" \
  -H "Authorization: Bearer $HERENOW_API_KEY"
```

## Production

The canonical URL is:

`https://signals.forwardfuture.ai/loop-library/`

Publish only from a clean deployment checkout at the latest integrated
`origin/main`, then link the resulting here.now Site to the `loop-library`
location on the active `signals.forwardfuture.ai` custom domain.
