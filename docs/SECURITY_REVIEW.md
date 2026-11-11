# Pre-push security review

Reviewed November 10, 2026 (America/Los_Angeles). This is a scoped development review, not a penetration test or a production security certification.

## Checks and fixes

- Reviewed the publication file list and scanned for common private-key, AWS, GitHub, Google API-key and payment-secret patterns. No unexpected credential patterns were detected. The documented local merchant key and test-only values are intentional demo placeholders.
- Verified `.env`, the local payment database, virtual environment, node_modules, frontend build output and browser test artifacts are excluded from Git. Expanded exclusions for environment variants, private-key/certificate files and alternate SQLite files; `.env.example` remains included with placeholders only.
- `npm audit`: found advisories affecting the original Vite version. Upgraded Vite from 6.3.5 to 6.4.6. The final audit reports zero known vulnerabilities.
- `pip-audit` against every pinned package in `backend/requirements.lock`: found advisories affecting Starlette and pytest. Upgraded FastAPI to 0.162.4, Starlette to 1.10.0 and pytest to 9.2.0. The final audit reports zero known vulnerabilities. `pip check` also passes.
- Preserved TLS verification and pinned the tested dependency set. Deployment and Docker install from the lock file.
- Sandbox configuration now rejects merchant API keys shorter than 32 characters, including the published local demo key. The Render worker inherits the API service's merchant key because both use the same settings validation.
- Webhook request bodies are limited to 256 KiB during streaming, before the full body is buffered or signature verification is attempted.
- API responses use `Cache-Control: no-store`; responses also include no-referrer, nosniff and frame-denial headers.
- Reviewed merchant query scoping, buyer-token hashing/expiry/revocation, webhook verification before persistence, database capture deduplication, fixed sandbox destinations, structured AI validation and credential-free isolated replays. No `eval`, shell execution, disabled TLS verification or raw HTML injection is used in the application paths reviewed.

## Validation after fixes

- Backend suite: **21 tests passed**, including concurrent capture, tenant/token boundaries, invalid webhook signatures, duplicate webhook processing, fabricated AI citations, outage fallback and the new security regression tests.
- TypeScript check and production frontend build: passed.
- Browser suite: **2 tests passed** against a separate SQLite database and API/frontend ports, without changing the user's running application data. Merchant investigation/evidence/replay and buyer status/mobile viewport were exercised.
- Existing PostgreSQL validation is recorded separately in `VALIDATION.md`; it was not repeated for this dependency update.

## Remaining limits

- Actual PayPal sandbox credentials, PayPal-signed deliveries, live Gemini and a public deployment still need end-to-end validation.
- Keep the local default merchant key confined to simulation. Use a generated random sandbox key, HTTPS, restricted merchant access and ingress rate limits for a hosted demo. The API-key flow is not a production identity/session system.
- Free-form AI commentary requires merchant review; deterministic payment facts and support replies remain protected separately.
- Vulnerability scanners only report issues known to their databases at scan time. Pattern scanning cannot guarantee that every possible secret format has been recognized.
- Starlette's test client emits an HTTPX deprecation warning; the frontend build emits a bundle-size warning. Neither failed validation.
