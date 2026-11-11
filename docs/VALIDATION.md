# Validation evidence

Validated in the managed Linux environment, November 10, 2026 (America/Los_Angeles).

| Check | Result |
| --- | --- |
| `./scripts/setup.sh` with existing dependencies/database | Passed; repeatable install, migrate, seed |
| `./scripts/test.sh` | 21 backend tests passed after the pre-push security updates; TypeScript and Vite production build passed |
| PostgreSQL 16 integration run | 17 backend tests passed against a separate PostgreSQL database (before adding the independent sandbox adapter contract test) |
| PostgreSQL initial migration + seed | Passed on a new database |
| PostgreSQL direct evidence deletion | Rejected by append-only database trigger, as expected |
| `cd frontend && npm exec playwright test` | 2 tests passed using system Chromium: incident/reconcile/investigate/evidence/replay; checkout/private status/mobile viewport |
| Four predefined replay scenarios | All assertions passed; isolated fake provider, no payment credentials |
| Live API + separate worker smoke check | Health OK; simulated response loss automatically reconciled to CONFIRMED; repeat capture blocked; status marked no-store; production SPA served |
| Shell syntax / JSON manifests | Passed |
| Real PayPal sandbox purchase and signed delivery | Not run: sandbox client credentials/webhook ID not configured |
| Live Gemini model | Not run: optional Gemini API key not configured; deterministic and outage fallback tested |
| Render deployment | Blueprint included; not deployed |

The sandbox adapter contract test uses HTTPX MockTransport and checks the fixed sandbox host, OAuth, stable request IDs and webhook verification request. It is not a real PayPal integration test.

The updated test suite emits an HTTPX deprecation warning from Starlette. Vite reports a large bundle, primarily AG Grid. Neither failed validation. Fonts are bundled locally rather than fetched by the browser.

PayPal sandbox's host is blocked by the current cloud network policy. A draft adds `api-m.sandbox.paypal.com` and optional `generativelanguage.googleapis.com`, alongside install/start instructions. Review and save these settings before external integration tests, then publish if you want the prepared environment reused. Saving the draft alone does not apply network access or deploy the app.

No optional sponsor integrations are represented as complete. The evidence experience is a clickable claim-to-source inspector rather than a visual node graph. Authentication is a demo merchant API key, not a production identity provider. Sandbox approval uses a redirect instead of the PayPal JS SDK. SQLite is the default local store; PostgreSQL was separately validated and is intended for deployment. Automatic retry/recovery of unresolved create-order operations is a documented limitation; capture requests remain protected against duplicates.

See [the pre-push security review](SECURITY_REVIEW.md) for dependency upgrades, additional regression tests and the latest browser run.
