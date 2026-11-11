# 2:50 demonstration

Use the default **simulated** environment for a repeatable walkthrough. State clearly that no real payment occurs. Use a separately configured sandbox environment if you want to show a real PayPal sandbox transaction.

- 0:00–0:20 — Explain the problem: browser timeout does not prove payment failure.
- 0:20–0:50 — Simulate interrupted checkout. Show UNKNOWN and the recorded capture response-loss fault.
- 0:50–1:20 — Reconcile; show CONFIRMED and the capture reference. Click the timeline source payload.
- 1:20–1:55 — Investigate; inspect source-linked findings, unknown bank-side posting and editable reply. Explain whether this is Gemini or deterministic fallback.
- 1:55–2:25 — Run response-lost Replay Lab scenario. Show one capture, blocked duplicate, recovered truth, and duplicate webhook assertion.
- 2:25–2:50 — Demo checkout and private buyer status page. Explain that the merchant and buyer see the same backend truth.

For deliberately observing UNKNOWN before reconciliation, pause only the worker you started; manual reconcile still works. With a running worker the uncertainty can resolve quickly.
