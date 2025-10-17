.PHONY: up down init ingest optimize scores embed ui api ollama-models

up:
	docker compose up -d

down:
	docker compose down

init:
	docker compose exec db bash -lc "psql -U ads -d amazon_ads -f /sql/01_schema.sql"
	docker compose exec db bash -lc "psql -U ads -d amazon_ads -f /sql/02_pgvector.sql"

ingest:
	docker compose exec worker python ingest_reports.py

scores:
	docker compose exec worker python score_keywords.py

embed:
	docker compose exec worker python build_embeddings.py

optimize:
	docker compose exec worker python optimize.py

ollama-models:
	docker compose exec ollama ollama pull llama3.1:8b
	docker compose exec ollama ollama pull nomic-embed-text

ui:
	open http://localhost:8501 || xdg-open http://localhost:8501

api:
	open http://localhost:8000/docs || xdg-open http://localhost:8000/docs
