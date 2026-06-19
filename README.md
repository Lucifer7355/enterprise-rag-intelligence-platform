# Enterprise RAG Intelligence Platform

**Plug-and-play** enterprise AI assistant with config-driven RBAC, connector plugins, hybrid retrieval, and knowledge graph reasoning.

> **HackerEarth judges:** See **[SUBMISSION.md](SUBMISSION.md)** for 5-minute setup, demo script, and login credentials.

## Fastest Start (Windows — one command)

```powershell
cd enterprise-rag
.\scripts\start_local.ps1
```

Then open http://localhost:8501 and login: **admin** / **admin123**

> Add data sources, roles, routing rules, and security policies via YAML or API — **no code changes required**.
> See [docs/PLUG_AND_PLAY.md](docs/PLUG_AND_PLAY.md) for the full guide.

## Plug & Play in 3 Steps

```bash
# 1. Add a connector in config/connectors.yaml (or POST /connectors)
# 2. Ingest
curl -X POST http://localhost:8000/ingest -d '{"force_reindex": true}'

# 3. Query
curl -X POST http://localhost:8000/chat \
  -d '{"query": "Show failed payment incidents", "role": "Engineering"}'
```

**Customize via YAML** (hot-reload with `POST /config/reload`):
- `config/rbac.yaml` — roles & permissions
- `config/routing.yaml` — query types & source routing
- `config/connectors.yaml` — data source plugins
- `config/sensitive_data.yaml` — PII/secret handling
- `config/graph.yaml` — knowledge graph entity mappings

**Custom connectors**: drop a Python file in `plugins/connectors/` — auto-discovered at startup.

## Features

- **Plug & Play Connectors** — folder, csv, json, sql, pdf, inline + custom plugins
- **Config-Driven RBAC** — add roles in YAML, no code changes
- **Query Classification** — LLM + config-driven keyword routing
- **Hybrid Retrieval** — Dense (BGE embeddings + Qdrant) + Sparse (BM25 + Elasticsearch)
- **RBAC Security** — Retrieval-time role filtering; never retrieve-then-filter
- **Sensitive Data Protection** — Blocks salary, SSN, secrets for unauthorized roles
- **Knowledge Graph** — NetworkX multi-hop reasoning across employees, teams, assets, incidents
- **Reranking** — BGE Cross-Encoder (top 5 contexts)
- **Explainability** — Source citations, confidence scores, retrieval trace
- **Evaluation** — Recall@K, Precision@K, MRR, NDCG + security metrics
- **JWT Auth + OIDC SSO** — Login API, Streamlit auth, enterprise SSO ready
- **Langfuse + Phoenix** — LLM tracing and OpenTelemetry export
- **Live RAGAS** — Real-time faithfulness, relevance, context precision
- **Observability** — Structured logging, OpenTelemetry, audit logs

## Quick Start

### Option 1: Local (recommended for judges)

```powershell
cd enterprise-rag
.\scripts\start_local.ps1
```

| URL | Purpose |
|-----|---------|
| http://localhost:8501 | Streamlit UI (login required) |
| http://localhost:8000/docs | API Swagger |
| http://localhost:6006 | Phoenix trace UI |

**Login:** `admin` / `admin123` — more accounts in [SUBMISSION.md](SUBMISSION.md)

Manual start (3 terminals):
```powershell
# Terminal 1
$env:USE_MOCK_LLM="true"; $env:PYTHONPATH="."; .\venv\Scripts\uvicorn app.main:app --port 8000
# Terminal 2
.\venv\Scripts\streamlit run streamlit_app/app.py --server.headless true
# Terminal 3
.\venv\Scripts\phoenix serve
```

### Option 2: Docker Compose

```bash
docker-compose up --build
```

## API Endpoints

| Method | Endpoint    | Description                    |
|--------|-------------|--------------------------------|
| POST   | `/chat`     | Ask a question with RBAC       |
| POST   | `/ingest`   | Ingest/regenerate data         |
| GET    | `/sources`  | List indexed data sources      |
| GET    | `/audit`    | View audit logs                |
| POST   | `/evaluate` | Run retrieval/security metrics |
| GET    | `/roles`    | List configured roles          |
| GET    | `/connectors` | List connector plugins       |
| POST   | `/connectors` | Add connector at runtime     |
| POST   | `/documents`  | Index single document        |
| POST   | `/config/reload` | Hot-reload YAML configs   |
| GET    | `/config`   | View active configuration      |
| POST   | `/auth/login` | JWT login (demo: admin/admin123) |
| GET    | `/auth/sso/login` | OIDC SSO redirect          |
| GET    | `/observability` | Langfuse/Phoenix status     |
| GET    | `/health`   | Health check                   |

### Example Chat Request

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Show failed payment incidents", "role": "Engineering"}'
```

## Configuration

Copy `.env.example` to `.env`:

```env
OPENAI_API_KEY=your-key          # Optional; uses mock LLM if empty
USE_MOCK_LLM=true                # Set false when using OpenAI
QDRANT_HOST=localhost
ELASTICSEARCH_URL=http://localhost:9200
```

## Sample Queries

| Role         | Query                                                      |
|--------------|------------------------------------------------------------|
| Engineering  | Show failed payment incidents from last week               |
| Compliance   | Which compliance violations were caused by Team Alpha?     |
| Finance      | What are the monthly infrastructure expenses?              |
| HR           | List employee salary information                           |
| Engineering  | (blocked) Access salary data → "Access Denied"             |

## Testing

```bash
pytest tests/ -v
```

## Project Structure

See [docs/architecture.md](docs/architecture.md) for full architecture diagram and design decisions.

## Tech Stack

- **Backend**: FastAPI, Python 3.11
- **UI**: Streamlit
- **Vector DB**: Qdrant (with in-memory fallback)
- **Search**: Elasticsearch + rank_bm25 fallback
- **Embeddings**: BGE-large-en-v1.5 (sentence-transformers)
- **Reranker**: BGE-reranker-base
- **Knowledge Graph**: NetworkX
- **LLM**: OpenAI GPT-4o-mini (mock fallback)
- **Observability**: structlog, OpenTelemetry

## License

MIT
