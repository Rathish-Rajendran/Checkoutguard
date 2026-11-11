# Validation evidence

Release checks were run on macOS on November 10, 2026.

| Check | Result |
| --- | --- |
| Fresh judge setup | Installed locked dependencies, applied migrations, seeded a fresh SQLite database and started the API, worker and frontend with Bash 3.2 and no PayPal credentials. Health returned OK. |
| `./scripts/test.sh` | 34 backend tests passed after the security review. TypeScript and the Vite production build passed. |
| Playwright with Chrome | 2 tests passed against the FastAPI-served production bundle with its content security policy. The tests exercise incident recovery, investigation, evidence inspection, replay, manual incident reporting and private buyer status at desktop and mobile widths. |
| Postman via Newman | 11 requests and 17 assertions passed against a fresh simulated service, including confirmation, buyer data minimization, replay and rejection of an unsigned webhook. |
| Replay Lab | Automated checks passed for all four predefined scenarios. |
| Ollama with `qwen2.5:3b` | A live browser investigation displayed OLLAMA · LOCAL and linked to a provider record. Adapter tests cover invalid citations, malformed output, incomplete output and provider failure. |
| PayPal Sandbox | OAuth succeeded and CheckoutGuard's adapter created a Sandbox order with a buyer approval link. Buyer approval, capture and genuine signed webhook delivery remain to be verified. |
| PostgreSQL 16 | An earlier Linux run passed 17 backend integration tests, fresh migration and seed, and direct evidence deletion rejection. The current release suite ran against SQLite. |
| Hosting | The built SPA was served by FastAPI and the Render blueprint is included. The judge walkthrough was verified locally. |

The suite emits a Starlette HTTPX deprecation warning and a Vite bundle size warning. The Postman webhook request checks unsigned rejection. Automated tests for verified webhook persistence and deduplication use a controlled verifier.

For a complete PayPal Sandbox validation, register a reachable HTTPS webhook, approve a checkout with a sandbox buyer, verify one capture and the matching buyer status, then check PayPal's signed delivery history. See [sandbox setup](../README.md#keys-and-sandbox-setup) and [the demo script](DEMO.md).
