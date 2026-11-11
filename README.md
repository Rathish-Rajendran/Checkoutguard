# CheckoutGuard

An evidence-based payment incident workspace. When checkout stops responding, reconstruct the payment outcome, inspect the source records, and test recovery without making another payment.

**Implemented:** FastAPI, SQLAlchemy/Alembic, PostgreSQL support, a zero-key SQLite local mode, React/TypeScript/Vite, AG Grid Community incident table, private buyer status, append-only Flight Recorder, durable capture idempotency, verified sandbox webhook inbox, outbox worker, source-linked investigator, and four isolated replay scenarios.

**Local simulation is not a PayPal transaction.** Sandbox integration code is implemented but requires your credentials and a real sandbox approval/capture to validate. AI now runs through local Ollama; unavailable AI falls back to a labeled deterministic report. No AI API key is required. There is no live-money mode.

## Project status

The local development workflow is implemented and tested. **The project still needs deployed sandbox integration testing and a final demo before it is hackathon-ready.** Credentials are one prerequisite; hosting, webhook registration, network access, and end-to-end validation also remain.

### What has been implemented

| Area | Implementation | Validation status |
| --- | --- | --- |
| Application foundation | FastAPI API, health endpoint, environment validation, correlation IDs and structured logs | Local health and startup verified |
| Database | SQLAlchemy models, initial Alembic migration, demo merchant seed, SQLite local mode and PostgreSQL support | Migration/seed verified; PostgreSQL integration tests passed |
| Payment integration | Separate simulated and PayPal sandbox clients; server-side OAuth, create, approval redirect, capture and lookup | Simulated flows and mocked sandbox request contract tested; actual sandbox calls still pending |
| Capture protection | Durable operation/request keys and a database uniqueness constraint prevent repeated or concurrent capture calls | Concurrent and repeated capture tests passed |
| Payment Truth | Backend-derived CONFIRMED, PENDING, UNKNOWN and FAILED states, matching resource checks and protection against confirmed-state regression | Automated state and reconciliation tests passed |
| Flight Recorder | Append-only timeline with stable evidence IDs, timestamps and inspectable source payloads | Application immutability tested; PostgreSQL database trigger verified |
| Webhooks and worker | Sandbox signature-verification adapter, durable inbox, event deduplication, outbox and bounded reconciliation retries | Verification failure, injected verification success, duplicates and worker behavior tested; PayPal-signed deliveries pending |
| Buyer experience | Demo checkout and private polling status page; hashed, expiring and revocable status tokens | Browser flow, mobile viewport and token/access tests passed |
| Merchant workspace | API-key authentication, tenant-scoped incident list/detail, AG Grid table, timeline and manual reconciliation | Browser investigation flow and tenant isolation tested |
| Investigation | Local Ollama adapter, structured output, evidence-ID/action validation, deterministic confirmed-fact wording and reply drafts, outage fallback | Local report, fabricated-citation rejection and provider-outage fallback tested; actual local-model inference pending in this cloud environment |
| Evidence inspection | Clickable findings and timeline records open their underlying JSON; editable support reply | Browser interaction tested; implemented as a source inspector rather than a node graph |
| Replay Lab | Four isolated scenarios: lost response, repeated capture, duplicate/out-of-order notifications and unresolved payment; saved assertions and traces | All four simulations passed; no PayPal credentials used |
| Delivery tooling | Setup/start/test scripts, dependency locks, environment template, PostgreSQL Compose file, Postman collection, Render blueprint and demo guide | Setup repeatability and production frontend build verified; hosting and Postman execution still pending |

### What has been verified

These are the recorded results from the implementation session, not a claim that external integrations or deployment have been validated:

- **31 backend tests passed** using the local test database.
- **17 backend tests passed against PostgreSQL 16**, before the independent mocked sandbox adapter contract test was added.
- **2 browser tests passed**, covering merchant investigation/evidence/replay and buyer checkout/private status, including a mobile viewport.
- **TypeScript checking and the Vite production build passed.**
- A running API and separate worker automatically recovered a simulated lost capture response, confirmed payment truth, and blocked a duplicate capture.
- PostgreSQL migrations, seeding and the append-only evidence trigger were verified.

See [the pre-push security review](docs/SECURITY_REVIEW.md) for dependency fixes and security checks.

See [validation evidence and limitations](docs/VALIDATION.md) for the full record. Commands to repeat the checks appear under [Automated testing](#automated-testing).

### What needs to be done for the hackathon

Complete these in order. External test results may reveal issues that need fixes; having adapter code is not proof that the integration works.

- [ ] **Configure PayPal sandbox access.** Create a sandbox app, obtain its Client ID/Secret, and prepare a sandbox personal buyer account. Store credentials securely as described under [Keys and sandbox setup](#keys-and-sandbox-setup).
- [ ] **Deploy the application and database.** Provision a public HTTPS application, PostgreSQL and the background worker; review the supplied [Render blueprint](render.yaml) and hosting costs. Migrate/seed the deployment and confirm API/worker startup.
- [ ] **Register the sandbox webhook.** Add the public `/api/paypal/webhooks` endpoint to the PayPal sandbox app, subscribe to the documented events, and configure its Webhook ID on the API and worker. Set `PUBLIC_URL` to the deployed application origin and enable `PAYMENT_MODE=sandbox` once all three PayPal values exist.
- [ ] **Verify outbound network access.** In this managed cloud environment, review/save the proposed access to `api-m.sandbox.paypal.com` and, for model downloads in this cloud environment, `registry.ollama.ai`, then test a fresh connection. A saved draft alone does not apply network changes. Ensure the chosen host also permits the required destinations.
- [ ] **Complete an actual PayPal sandbox purchase.** Approve with the sandbox buyer, capture once, and verify the capture ID and matching amount/currency through backend lookup and buyer status. No real money should move.
- [ ] **Verify signed webhook delivery and deduplication.** Confirm PayPal deliveries are accepted only after verification and persistence; resend a delivery and confirm no duplicate business effect. Check worker reconciliation.
- [ ] **Demonstrate sandbox response-loss recovery.** In a controlled sandbox demo, enable the response-loss fault, prove reconciliation confirms one capture, and prove a repeated request cannot capture again. Disable faults afterward.
- [ ] **Run and validate local Ollama.** Install Ollama, pull `qwen2.5:3b`, and follow [Local AI with Ollama](#local-ai-with-ollama). Verify a source-linked investigation on the sandbox incident and check invalid-output/outage fallback. No AI API key is needed.
- [ ] **Run the deployed acceptance checks.** Exercise merchant access, private buyer status, source inspection, all four replays, and the Postman collection. Record results and fix failures.
- [ ] **Prepare the submission.** Confirm hackathon-required integrations, rehearse [the demo](docs/DEMO.md), record it, and add the deployed URL and judge access instructions without publishing secrets.

### Known limitations and optional follow-up

- Authentication is a demo merchant API key, not a production identity/session system. The checkout screen is merchant-operated; a public storefront needs a server-side merchant integration so buyers never receive that key.
- Automatic recovery of unresolved **create-order** operations is not implemented. These require investigation; capture operations have separate duplicate protection and reconciliation.
- The Evidence Graph requirement is represented by the interactive claim-to-source inspector. A visual node graph is optional follow-up.
- PayPal approval uses a redirect instead of embedded JS SDK buttons.
- Elastic, AG Studio, APIMatic, Zapier and KERNEL are not integrated. AG Grid Community is implemented. Confirm judging requirements before deciding whether any additional integration is necessary.
- Production identity, ingress rate limits, operational monitoring and further bundle-size optimization are follow-up work beyond the current development demo.

## Local AI with Ollama

The investigator uses **Ollama instead of Gemini**. It needs no AI API key. Install Ollama from [the official download page](https://ollama.com/download) on the same machine as the API, then download the starter model:

```bash
ollama pull qwen2.5:3b
```

Ollama's desktop app normally runs the service for you. On Linux, if it is not already running, start `ollama serve` in a separate terminal. The model is roughly 2 GB to download; allow several GB of available RAM and more time on a CPU. First inference may be slower while loading the model. The model tag is configurable; larger models need more resources.

In `backend/.env`, replace the former Gemini configuration with:

```dotenv
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:3b
OLLAMA_TIMEOUT_SECONDS=120
```

Restart the API. No application dependency changes or Gemini key are needed. Confirm the service and downloaded model:

```bash
curl --noproxy localhost,127.0.0.1 -fsS http://127.0.0.1:11434/api/tags
```

In CheckoutGuard, create/open an incident and click **Investigate incident**. A successful model response shows **OLLAMA · LOCAL**. If the service is stopped, the model is missing, inference times out or its JSON/citations are rejected, the workspace shows **OLLAMA UNAVAILABLE · FALLBACK** and a source-linked deterministic report. Payment truth remains backend-derived in both cases. Test failure handling by stopping Ollama and investigating again. Set `AI_PROVIDER=deterministic` to skip model calls entirely for a repeatable non-AI demo or automated UI checks.

The backend uses Ollama's native `/api/chat` endpoint, structured JSON-schema output, a separate system instruction and untrusted user-data message, temperature zero and no tools. It still validates citations, restricts next-step actions and generates confirmed facts/support replies deterministically. Prior investigations keep their historical provider metadata; create a new investigation to use Ollama.

**Deployment:** `127.0.0.1` is relative to the API process. An API hosted on Render cannot reach Ollama running on your laptop via that address. For a local hackathon demo, run the API and Ollama together. For a hosted demo, provision a model server reachable over a protected private network, configure `OLLAMA_BASE_URL` there, and switch `AI_PROVIDER=ollama`. Do not expose Ollama's unauthenticated port directly to the public internet. The Render blueprint defaults to `deterministic` until that model service is configured. If containers are used, configure a reachable service hostname rather than assuming container loopback reaches the host.

This managed cloud environment currently blocks `registry.ollama.ai`. Adapter tests use controlled HTTP responses; an actual model download/inference here remains unverified until registry access and any download destinations are allowed. Model setup is separate from `scripts/setup.sh`, so normal dependency installation does not silently download a large model.

## Quick start

Prerequisites: Python 3.12+, Node 22+ and npm. From the repository root:

```bash
cp -n .env.example backend/.env  # Preserve an existing local configuration
./scripts/setup.sh
./scripts/dev.sh
```

Open `http://localhost:5173` on your own machine. API docs: `http://localhost:8000/docs`. Health: `curl http://localhost:8000/health`.

Enter `local-demo-key-change-me` at the workspace login (or your configured `MERCHANT_API_KEY`). This is development API-key authentication, not a production identity/session system. Keys are hashed in the database and held in browser session storage while unlocked. Never put the PayPal secret into the browser key field.

`setup.sh` installs dependencies, migrates the database, and creates/updates the demo merchant key. It is repeatable and does not reset payment records. `dev.sh` starts the API, worker, and Vite and stops its processes on exit. Processes must be restarted in a new environment; existing isolated checkouts do not need a Git worktree.

## Try the whole story (no API keys required)

1. Unlock the merchant workspace.
2. Click **Simulate interrupted checkout**. A $49 simulated capture completes but the browser response is deliberately dropped. An incident appears; until reconciliation, truth is UNKNOWN.
3. Click **Reconcile now**. Lookup confirms exactly one capture; status becomes CONFIRMED. The background worker also does this automatically, so UNKNOWN may already have resolved.
4. Click **Investigate incident**. Inspect the findings, unknowns and editable customer reply. Click a cited finding or timeline event to see its source JSON.
5. Open **Replay Lab**, choose **response lost**, then **Run simulation**. Inspect expected/actual assertions, duplicate protection, and trace. Run the other three scenarios too.
6. Open **Demo checkout**, start a simulated checkout, capture it, then open the private payment status link. That page works without a merchant key and polls every three seconds. Demo faults are available only when enabled on the server.

The checkout screen is a merchant-operated demo. A production public storefront should create orders through a server-side merchant integration rather than distributing a merchant API key to buyers. The private status page is buyer-facing.

## Automated testing

```bash
./scripts/test.sh                 # Python service/API tests + TypeScript/production build
cd frontend
npm exec playwright install chromium  # only if Chromium is not installed
CHROMIUM_PATH=/path/to/chromium npm exec playwright test
```

The browser suite expects API port 8000 and frontend port 5173 running in **simulated** mode, using the default demo merchant key. On this cloud machine Chromium is `/usr/bin/chromium`; elsewhere provide the installed browser executable. Run in a disposable development database: browser tests create demo payment records. API tests use their own SQLite database under `/tmp` and reset it before each test.

Tests cover simultaneous capture requests, lost-response recovery, deterministic truth, no state regression, token secrecy/expiry/revocation, tenant isolation, webhook verification failure and deduplication, worker reconciliation, fabricated AI citations, AI outage fallback, immutable evidence, and all replay scenarios. Browser tests exercise merchant investigation/evidence/replay plus buyer checkout/status on desktop and mobile. API/OpenAPI examples are also available in `postman/CheckoutGuard.postman_collection.json`.

## Keys and sandbox setup

Put values in `backend/.env` locally, or your hosting provider's secure environment settings. **Never commit them or paste secrets into chat.** No external keys are needed to use the simulator.

| Variable | Required for | Where it comes from |
| --- | --- | --- |
| `MERCHANT_API_KEY` | Merchant API | Generate a random value of at least 32 characters for sandbox (API and worker); rerun `python -m app.seed` after changing it |
| `PAYPAL_CLIENT_ID` | Sandbox | PayPal Developer dashboard → Apps & Credentials → Sandbox app |
| `PAYPAL_CLIENT_SECRET` | Sandbox | Same sandbox app, server-side secret |
| `PAYPAL_WEBHOOK_ID` | Sandbox verified webhooks | Create a webhook in that sandbox app |
| `AI_PROVIDER` | Investigation mode | `ollama` (default), or `deterministic` to skip model calls |
| `OLLAMA_BASE_URL` | Local model service | Default `http://127.0.0.1:11434`; set on the API server only |
| `OLLAMA_MODEL` | Local model name | Default `qwen2.5:3b`; pull it with Ollama first |
| `OLLAMA_TIMEOUT_SECONDS` | Inference timeout | Default `120`; increase up to `600` for slower hardware |
| `DATABASE_URL` | PostgreSQL deployment | Provider connection string; `postgresql+psycopg://...` supported |
| `PUBLIC_URL` | Sandbox approval redirect | Your public HTTPS application origin, without trailing slash |

For a sandbox test:

1. Create a PayPal developer sandbox app and use its sandbox business and personal buyer accounts. Never use a real account to pay.
2. Deploy to a public HTTPS origin (or use a tunnel you control). Register `https://YOUR_ORIGIN/api/paypal/webhooks` in the sandbox app. Subscribe to `PAYMENT.CAPTURE.COMPLETED`, `PAYMENT.CAPTURE.DENIED`, `PAYMENT.CAPTURE.PENDING`, and `CHECKOUT.ORDER.APPROVED`.
3. Configure all three PayPal variables, `PAYMENT_MODE=sandbox`, and `PUBLIC_URL`. Keep `DEMO_FAULTS_ENABLED=false` except in a controlled sandbox demonstration. Restart both API and worker; rerun the seed if the merchant key changed.
4. Open Demo checkout → **Approve with PayPal**, sign in as the sandbox personal buyer and approve. After returning, click **Capture approved order**. This uses a server-side capture and durable PayPal-Request-Id. The frontend uses PayPal's approval redirect rather than embedding its JS SDK.
5. Check the buyer status and authenticated `GET /api/orders/{id}` for CONFIRMED and a capture ID. If unresolved, reconcile; do not start another payment. Use **Report problem** through the API if you need a manual incident.
6. Inspect PayPal's webhook delivery history. A verified delivery must persist and return 200; duplicate deliveries must return `duplicate: true`. The worker must be running for reconciliation.
7. For a response-loss demo only, enable demo faults, start a separate sandbox order, check the fault checkbox before capture, and observe recovery. Disable the fault flag afterward.

Only `api-m.sandbox.paypal.com` is used for server payment calls. Ollama inference goes to your configured model server; downloading models requires access to Ollama’s registry and any download redirect hosts. No Google API access is needed. Browser approval goes to PayPal sandbox domains on the buyer's network. No Elastic, AG Studio, APIMatic, Zapier, or KERNEL integration is claimed; AG Grid Community is implemented.

## PostgreSQL

SQLite makes local evaluation possible without Docker. Use PostgreSQL for a deployed API/worker:

```bash
export POSTGRES_PASSWORD='choose-a-local-development-password'
docker compose up -d postgres
# In backend/.env, set DATABASE_URL to:
# postgresql+psycopg://checkoutguard:YOUR_PASSWORD@localhost:5432/checkoutguard
cd backend
../.venv/bin/alembic upgrade head
../.venv/bin/python -m app.seed
```

Migrations install database triggers rejecting updates/deletes to Flight Recorder records. Keep a separate database per environment. The migration currently represents the initial schema; future schema changes need new explicit Alembic revisions.

## Production build / deployment

```bash
npm --prefix frontend ci
npm --prefix frontend run build
cd backend
../.venv/bin/python -m uvicorn app.main:app --no-access-log --host 0.0.0.0 --port 8000
# Separate process, same database and payment mode:
../.venv/bin/python -m app.worker
```

The API serves the built SPA on the same origin, so no CORS configuration is needed. Start/restart the API **after** building the frontend. `render.yaml` describes an API+SPA service, worker, and PostgreSQL database; review plans and set all secrets before deploying. It is a deployment blueprint, not an already deployed service. Migrate and seed on the API service before starting the worker. Render must provide Python 3.12+ and Node 22+. The backend-only Dockerfile is an alternative API image; build the frontend separately or use Render's combined build.

Change the default merchant key, disable demo faults, use TLS, restrict access to merchant tooling, and configure rate limits and log redaction at the ingress before public use. Do not log buyer token paths; app startup commands disable Uvicorn access logging. Treat private status links like secrets; hashes only are stored, expiry is 48 hours, and the merchant can revoke all order links through `DELETE /api/orders/{id}/buyer-tokens`.

## Architecture and payment rules

- **Backend authority:** only a matching, authenticated provider resource with a completed capture can confirm money movement. Resource IDs, internal reference, amount and currency are checked. Timeouts produce UNKNOWN; CONFIRMED cannot regress due to stale events. FAILED requires explicit declined/failed capture evidence. Retrying the same capture is always blocked; a failed order requires merchant review and a new checkout.
- **Durable operations:** a unique `(order_id, kind)` operation with a stable request key prevents concurrent duplicate capture calls. An outbox row is persisted with capture intent so crashes can be recovered by lookup. The app never automatically issues a second capture.
- **Webhook inbox:** parses the raw request, calls PayPal signature verification using its transmission headers and configured webhook ID, persists once before acknowledging, then queues lookup. Webhook text never directly overwrites payment truth. The simulator rejects public webhook signatures; verification-success tests inject an explicit test verifier.
- **Worker:** bounded exponential backoff (six attempts); exhausted jobs remain inspectable, with manual reconcile available. One worker is the supported local topology. Confirmed order evidence survives simulator process restarts via recorder restoration. Creation timeouts can leave an unresolved internal intent; investigate rather than creating another order blindly. Automatic create-operation recovery is not implemented.
- **Investigation:** facts are tenant-scoped, and no payment credentials or execution tools are sent to Ollama. Model data has a structured schema; IDs and actions are validated. Confirmed-fact prose and the support reply are generated deterministically, preventing model financial claims from entering those channels. Model summary/unknowns remain labeled commentary requiring merchant review. Invalid citations or provider outage yields deterministic fallback. This is not a semantic truth guarantee for free-form AI commentary.
- **Replay:** each run creates a separate in-memory database and credential-free fake client, invokes the actual payment/reconciliation/webhook persistence services, and saves only the trace/assertions in the merchant database. Only four predefined IDs are accepted. Out-of-order replay sends stale resources through the real state derivation path.

## Reset and troubleshooting

To reset **local simulated SQLite data only**, stop the app, archive `backend/checkoutguard.db` (and its `-wal`/`-shm` files if present), then rerun `./scripts/setup.sh`. This removes local history from the active database; never use it against sandbox/production data. Simulation buttons always create fresh independent orders; they do not reset existing orders.

- 401: check your configured merchant key and rerun the seed after changing it; lock/unlock the browser workspace.
- 504 with `Demo:`: expected response-loss fault, not failed payment. Reconcile or inspect private status.
- UNKNOWN: provider evidence is unavailable or did not match. Check worker/database/provider configuration. Never assume failed payment.
- Replays always pass locally but sandbox fails: replay verifies your safety logic, not PayPal credentials, network access, or real approval. Complete the sandbox steps above.
- npm cache permission error: use `npm --cache /tmp/checkoutguard-npm ...` as the setup script does.
- Frontend build reports a large chunk: AG Grid Community accounts for most of it; functionally valid but further lazy-loading is possible.

See `docs/DEMO.md` for the short demonstration and `docs/VALIDATION.md` for current evidence and limitations.
