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

## 🔧 Pre-commit Hooks

We rely on [**pre-commit**](https://pre-commit.com/) to auto-run **ruff** (lint) and **black** (format) against **every** change before it is committed.  
If these checks are **not** executed locally, your PR will fail in CI.

> **🚨 Important:** You must have the `pre-commit` package installed **globally**  
> (`pip install --user pre-commit` or via the project’s *dev* extras) **before** making commits.

### Setup (Run once per clone)

```bash
# 1) Install the tool (only needed if it’s not already on your system)
pip install pre-commit          # or: pip install -e '.[dev]'

# 2) Install the Git hooks defined in .pre-commit-config.yaml
pre-commit install
```

This adds a Git hook that formats / lints the staged files automatically at each `git commit`.

Run Checks Manually

To run all checks on all files:

```bash
pre-commit run --all-files
```

### What if the hook rejects my commit?

If `pre-commit` finds issues (usually formatting via **black** or lint via **ruff**),  
the commit will **abort** and the affected files will be *modified in-place* to satisfy the rules.

1. Open **Source Control** (e.g. the Git sidebar in VS Code).  
2. You will see the *updated* (but **unstaged**) files.
3. Click the **➕** (stage) button next to each fixed file *or* `git add <file>`.
4. Re-run `git commit` – it should now succeed.
5. Finally, push your branch to the remote.

> Tip: always run `pre-commit run --all-files` before making a commit to catch issues early.

Notes:
- Hooks are defined in `.pre-commit-config.yaml`.
- You can exclude specific files or directories (e.g., `tutorials/`) by modifying the config file `.pre-commit-config.yaml`.
- CI will re-run the same hooks; commits that bypass them locally will be rejected.
