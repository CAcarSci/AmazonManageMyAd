# AmazonManageMyAd — Local

Everything runs on your machine: Postgres, FastAPI, Worker jobs, Streamlit, and LLM via Ollama.

## Setup
1. Copy `.env.example` → `.env` and fill your Amazon Ads credentials (kept local).
2. `docker compose up -d`
3. Pull local models:
   ```bash
   make ollama-models
   ```
4. Initialize the database:
   ```bash
   make init
   ```
5. Pull a first batch of data (yesterday's metrics):
   ```bash
   make ingest
   ```
6. (Optional) Load your Brand Analytics / SQP / Ads search term datasets into `keyword_signals`.
7. Build scores & embeddings:
    ```bash
    make scores
    make embed
    ```
8. Open the UI: `http://localhost:8501` (and API docs: `http://localhost:8000/docs`).

## Notes
- Write-backs to Ads (bids/negatives) are off by default — API endpoint returns previews. Wire real calls when ready.
- RAG uses `pgvector` + `nomic-embed-text` (Ollama) and generates with `llama3.1:8b` locally.
- All secrets stay in `.env` and the local DB volume.
