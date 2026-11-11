# Local AI migration

Gemini has been replaced by Ollama. Delete any unused Gemini API key from your secure deployment settings; the application no longer reads it. No data is sent to Google by the current investigator.

- Default provider: `AI_PROVIDER=ollama`.
- Default origin: `OLLAMA_BASE_URL=http://127.0.0.1:11434`.
- Default model: `OLLAMA_MODEL=qwen2.5:3b`.
- Timeout: `OLLAMA_TIMEOUT_SECONDS=120` (valid range greater than zero, up to 600 seconds).
- Alternate mode: `AI_PROVIDER=deterministic`, with no model requests.

Install Ollama using its official distribution, run the service and `ollama pull qwen2.5:3b`. See the root README for local, hosted and container networking guidance. Model downloads are explicit; application setup never downloads them automatically.

The read-only investigator requests non-streaming JSON-schema output. Payment truth, amount, currency, confirmed-fact wording and support replies remain controlled by backend validation. Model summary and unknowns remain commentary for merchant review. Ollama errors, missing models, incomplete output and rejected evidence IDs return an explicit deterministic fallback.

Tests exercise the native request contract using HTTPX MockTransport, not an actual LLM. This machine has sufficient memory/disk for a small model but the model registry is blocked, so actual inference is not claimed as verified. No Gemini API key is required going forward.
