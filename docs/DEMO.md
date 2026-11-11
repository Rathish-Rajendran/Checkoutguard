# CheckoutGuard demo script

Use a fresh SQLite database and Ollama with `qwen2.5:3b`. Open the merchant workspace at `http://localhost:5173` and unlock it with the documented demo key. Use simulated payments for this walkthrough.

| Time | On screen | Narration |
| --- | --- | --- |
| 0:00–0:20 | Merchant incident list | When checkout freezes, the buyer wonders whether they paid. CheckoutGuard helps the merchant answer that question from payment evidence. |
| 0:20–0:45 | Simulate interrupted checkout | The simulator completed a capture and dropped the response. Payment Truth shows UNKNOWN while the outcome is being verified. |
| 0:45–1:10 | Reconcile and open a Flight Recorder event | CheckoutGuard looks up the existing order and confirms the matching capture. Open the provider record to see what supports the result. |
| 1:10–1:45 | Investigate incident, inspect a cited finding and show the reply | Ollama returns a structured investigation. The merchant can inspect the citation, review uncertainty about bank-side posting and edit the reply. |
| 1:45–2:10 | Open the private buyer status from the incident | The buyer sees the same confirmed outcome for this checkout, using a private link. |
| 2:10–2:50 | Replay Lab, response lost | Replay Lab runs the same failure in isolation and checks that repeating the request cannot capture twice. The local setup instructions are in the repository. |

For a recording that visibly shows UNKNOWN before confirmation, run the API and frontend while the worker is paused. Resume the worker for normal use. A separate PayPal Sandbox walkthrough requires a sandbox buyer and a reachable webhook. Show the PayPal approval and the returned capture only after verifying both in the Sandbox.
