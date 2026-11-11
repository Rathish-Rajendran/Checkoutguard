# Validation evidence

Validated in the managed Linux environment, November 10, 2026 (America/Los_Angeles).

| Check | Result |
| --- | --- |
| `./scripts/setup.sh` with existing dependencies/database | Passed; repeatable install, migrate, seed |
| `./scripts/test.sh` | 31 backend tests passed after the Ollama migration; TypeScript and Vite production build passed |
| PostgreSQL 16 integration run | 17 backend tests passed against a separate PostgreSQL database (before adding the independent sandbox adapter contract test) |
| PostgreSQL initial migration + seed | Passed on a new database |
| PostgreSQL direct evidence deletion | Rejected by append-only database trigger, as expected |
| `cd frontend && npm exec playwright test` | 2 tests passed using system Chromium: incident/reconcile/investigate/evidence/replay; checkout/private status/mobile viewport |
| Four predefined replay scenarios | All assertions passed; isolated fake provider, no payment credentials |
| Live API + separate worker smoke check | Health OK; simulated response loss automatically reconciled to CONFIRMED; repeat capture blocked; status marked no-store; production SPA served |
| Shell syntax / JSON manifests | Passed |
| Real PayPal sandbox purchase and signed delivery | Not run: sandbox client credentials/webhook ID not configured |
| Actual Ollama model inference | Not run: model registry blocked in this cloud environment; native API contract, invalid output, missing model, incomplete generation and outage fallback tested with controlled responses |
| Render deployment | Blueprint included; not deployed |

The sandbox adapter contract test uses HTTPX MockTransport and checks the fixed sandbox host, OAuth, stable request IDs and webhook verification request. It is not a real PayPal integration test.

The updated test suite emits an HTTPX deprecation warning from Starlette. Vite reports a large bundle, primarily AG Grid. Neither failed validation. Fonts are bundled locally rather than fetched by the browser.

The cloud environment draft now requests `api-m.sandbox.paypal.com` and `registry.ollama.ai`; the former Google AI domain has been removed. Review/save those settings before affected external operations and publish to reuse the environment. Saving a draft alone does not apply network access. The actual model download may also require its redirect destinations, which have not yet been observed.

No optional sponsor integrations are represented as complete. The evidence experience is a clickable claim-to-source inspector rather than a visual node graph. Authentication is a demo merchant API key, not a production identity provider. Sandbox approval uses a redirect instead of the PayPal JS SDK. SQLite is the default local store; PostgreSQL was separately validated and is intended for deployment. Automatic retry/recovery of unresolved create-order operations is a documented limitation; capture requests remain protected against duplicates.

See [the pre-push security review](SECURITY_REVIEW.md) for dependency upgrades, additional regression tests and the latest browser run.

Ollama migration: current AI uses the local `/api/chat` adapter and no Google credentials. To run actual inference, follow the root README. Registry access (`registry.ollama.ai` and any actual download redirect destinations) is needed to pull a model here; local inference itself needs no external API access. Historical pre-push security checks are preserved in SECURITY_REVIEW.md.
