# CheckoutGuard

When a checkout response is lost, CheckoutGuard checks the existing payment, shows the buyer a private status page, and gives the merchant an evidence-backed investigation. Replay Lab reproduces checkout failures and checks that repeated requests cannot capture the same payment twice.

## Quick start

Use Bash on macOS or Linux with **Git, Python 3.12+, and Node.js 22+ with npm**. The default demo uses a local SQLite database and simulated payments. You can run it without Docker, hosting, or **PayPal or AI API keys**.

```bash
git clone https://github.com/Rathish-Rajendran/Checkoutguard.git
cd Checkoutguard
cp -n .env.example backend/.env
./scripts/setup.sh
AI_PROVIDER=deterministic ./scripts/dev.sh
```

Setup installs locked dependencies, creates the database, and seeds the demo merchant. If `python3` points to an older version, run `PYTHON=python3.13 ./scripts/setup.sh` with the executable for a supported version you have installed.

Keep the terminal running and open [CheckoutGuard](http://127.0.0.1:5173). Enter **`local-demo-key-change-me`** and click **Open workspace**. This is the app's local demo key. The API and reconciliation worker start with the frontend. To check the API, run `curl -fsS http://127.0.0.1:8000/health` in a second terminal. Expect `"status":"ok"` and `"payment_mode":"simulated"`. Stop the app with **Ctrl+C**.

## Try the whole story (no API keys required)

**Scenario — a $49 capture succeeds, but the checkout response is lost.**

1. In **Incidents**, click **Simulate interrupted checkout**. The incident opens with a response-loss event in the **Flight Recorder**. Payment Truth may briefly show **UNKNOWN**.
2. Click **Reconcile now**. Expect **CONFIRMED** and a capture reference. The background worker may confirm the payment before you click.
3. Click **Investigate incident**, then click a source-linked finding. Check that the source record shows a completed capture and the customer reply draft says the payment is confirmed. The quick-start command shows **DETERMINISTIC**. With Ollama enabled, look for **OLLAMA · LOCAL**.
4. Click **Open private payment status**. The buyer page should show **Your payment is confirmed** and **$49.00 USD** for the same order. The link also works in a private browser window without the merchant key.
5. Open **Replay Lab**, select **Response lost**, and click **Run simulation**. Expect **All assertions passed**, including **At most one provider capture** and **Duplicate attempt blocked**.

For a normal checkout, open **Demo checkout** → **Start simulated checkout** → **Capture approved order** → **Open private payment status**. Expect a confirmed payment.

## Local AI with Ollama

To test the model-backed investigator, install and start Ollama, then download the model. Local inference requires no API key. [Ollama download](https://ollama.com/download)

```bash
ollama pull qwen2.5:3b
```

If Ollama is installed but the service is down, open the desktop app or run `ollama serve` in a separate terminal. Stop CheckoutGuard with **Ctrl+C**, then restart it from the repo root:

```bash
AI_PROVIDER=ollama ./scripts/dev.sh
```

Repeat the investigation and look for **OLLAMA · LOCAL**. If the service is unreachable or the model output fails validation, expect **OLLAMA UNAVAILABLE · FALLBACK** and a deterministic report. Payment Truth remains available in either case.

## Keys and sandbox setup

Use this section to test **PayPal Sandbox checkout**. The simulated judge walkthrough above uses only the included demo merchant key. Store Sandbox credentials in `backend/.env` and keep that file out of Git.

| Setting | Where to get it |
| --- | --- |
| `PAYPAL_CLIENT_ID` and `PAYPAL_CLIENT_SECRET` | In PayPal Developer Dashboard, switch to **Sandbox** → **Apps & Credentials**. Open the default app or create one and copy its client ID and secret. [PayPal REST setup](https://developer.paypal.com/api/get-started/) |
| `PAYPAL_WEBHOOK_ID` | In that same app, add a webhook at a public HTTPS URL ending in `/api/paypal/webhooks` and copy the resulting ID. For a local test, forward just that route to the API on port 8000. Subscribe to `CHECKOUT.ORDER.APPROVED`, `PAYMENT.CAPTURE.COMPLETED`, `PAYMENT.CAPTURE.PENDING`, and `PAYMENT.CAPTURE.DENIED`. [PayPal webhook setup](https://developer.paypal.com/api/rest/webhooks/rest/) |
| `MERCHANT_API_KEY` | Generate a private key with `openssl rand -hex 32`. Use it to unlock CheckoutGuard after setup seeds the Sandbox database. |

Stop the app, add the values above, and update these settings in `backend/.env`. The separate database keeps your simulated history intact.

```dotenv
PAYMENT_MODE=sandbox
DATABASE_URL=sqlite:///./checkoutguard-sandbox.db
PUBLIC_URL=http://127.0.0.1:5173
DEMO_FAULTS_ENABLED=false
```

Run `./scripts/setup.sh` and `./scripts/dev.sh` again. Use the exact origin in `PUBLIC_URL` when opening the app so the PayPal redirect returns to the same browser session.

1. In the PayPal Developer Dashboard, open **Testing Tools → Sandbox Accounts** and select **View/Edit Account** for a **Personal** buyer to find its login. Use that login on PayPal's approval page. [PayPal Sandbox accounts](https://developer.paypal.com/sandbox-testing/accounts)
2. In CheckoutGuard, open **Demo checkout** → **Approve with PayPal**. Sign in as the Sandbox buyer and approve the order. On return, click **Capture approved order**, then **Open private payment status**.
3. Expect **CONFIRMED** for **$49.00 USD**. In the Sandbox app's webhook history, look for a successful `PAYMENT.CAPTURE.COMPLETED` delivery. If the status is still uncertain, use **Report checkout problem** and **Reconcile now** for that order.

## Automated testing

From the repo root, run `./scripts/test.sh` for the backend tests and the frontend production build. For the browser tests, keep the **simulated** app running with the default demo key and `AI_PROVIDER=deterministic`:

```bash
cd frontend
npm exec -- playwright install chromium
npm exec -- playwright test
```

If setup succeeds but the workspace returns 401, check the merchant key and rerun setup to seed it. If either port is busy, stop the other process or start with `API_PORT=8001 WEB_PORT=5174 ./scripts/dev.sh`. For browser tests on a different frontend port, set `PLAYWRIGHT_BASE_URL`. For Sandbox, update `PUBLIC_URL`.

[Validation results](docs/VALIDATION.md) · [Security review](docs/SECURITY_REVIEW.md) · [Demo script](docs/DEMO.md) · [Postman collection](postman/CheckoutGuard.postman_collection.json) · [Render deployment blueprint](render.yaml) · [MIT license](LICENSE)
