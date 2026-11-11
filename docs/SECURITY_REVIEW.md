# Pre-push security review

Reviewed November 10, 2026 (America/Los_Angeles).

## Checks

- Scanned the public Git history and proposed release files with Gitleaks. Compared the candidate files against the configured local PayPal values without displaying them. No secrets were found in the publishable files. The local environment file, databases, private key files, build output and test output are excluded from Git.
- npm audit and pip-audit reported zero known vulnerabilities for the pinned dependencies. Python dependency consistency passed with `pip check`.
- Reviewed tenant scoping, buyer-token expiry and revocation, webhook verification before persistence, stable capture request IDs, capture deduplication, the fixed PayPal Sandbox API host and the isolated replay service.

## Changes

- The AI investigator sends an allow-listed evidence summary to Ollama. Raw provider payloads and payer details remain in the authenticated evidence inspector. Payment state, citations and permitted actions are still validated by the backend.
- PayPal approval uses a validated HTTPS origin or an HTTP loopback origin. Startup validation errors omit input values.
- The production SPA sets a same-origin content security policy, and private buyer status pages use `Cache-Control: no-store`.
- Webhook parsing still caps bodies at 256 KiB. Signature verification and persistence run in a worker thread so outbound PayPal calls do not block the asynchronous request loop.

## Release gates

- The local judge walkthrough uses SQLite, a demo merchant key and an optional local Ollama service. A publicly hosted deployment needs HTTPS, a strong merchant key, restricted merchant access and ingress rate limits.
- PayPal Sandbox OAuth and order creation passed. Buyer approval, capture and genuine signed webhook delivery remain unverified. The duplicate-webhook tests use a controlled verifier.
- Free-form AI commentary requires merchant review. Known-vulnerability and secret scans cover the inputs and databases available at the time of the check.
