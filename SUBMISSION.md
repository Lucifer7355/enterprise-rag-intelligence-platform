# HackerEarth Submission Guide

## Project: Enterprise RAG Intelligence Platform

**One-liner:** Config-driven, plug-and-play enterprise RAG with RBAC-enforced hybrid retrieval, knowledge graph reasoning, and full audit trail.

---

## Evaluator Quick Start (5 minutes)

```bash
cd enterprise-rag
docker-compose up --build
```

| Service | URL |
|---------|-----|
| API Docs | http://localhost:8000/docs |
| Streamlit UI | http://localhost:8501 |
| Health | http://localhost:8000/health |

**First run takes ~2-3 min** (downloads embedding model). `USE_MOCK_LLM=true` is set in Docker — no API key needed.

### Without Docker

```bash
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
set USE_MOCK_LLM=true
uvicorn app.main:app --port 8000
# New terminal:
streamlit run streamlit_app/app.py
```

---

## Demo Script (copy-paste for judges)

### 1. RBAC — Engineering blocked from salary
```bash
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" ^
  -d "{\"query\": \"Show employee salary data\", \"role\": \"Engineering\"}"
```
Expected: Access denied or no salary data returned.

### 2. Incident query — Admin gets citations
```bash
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" ^
  -d "{\"query\": \"Show failed payment incidents\", \"role\": \"Admin\"}"
```
Expected: Answer + sources (runbook, incidents.sql) + retrieval trace.

### 3. Multi-hop compliance
```bash
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" ^
  -d "{\"query\": \"Which compliance violations were caused by systems owned by Team Alpha?\", \"role\": \"Compliance\"}"
```
Expected: Cross-source retrieval (compliance PDF + assets + incidents).

### 4. Plug-and-play — add document at runtime
```bash
curl -X POST http://localhost:8000/documents -H "Content-Type: application/json" ^
  -d "{\"document_id\": \"demo_policy\", \"source\": \"WFH_Policy.pdf\", \"text\": \"Employees may work from home 3 days per week.\", \"metadata\": {\"allowed_roles\": [\"HR\", \"Admin\"]}}"
```

### 5. Run tests
```bash
pytest tests/ -q
```
Expected: 33 passed.

---

## Deliverables Checklist (vs. challenge requirements)

| # | Requirement | Status | Location |
|---|-------------|--------|----------|
| 1 | Architecture | ✅ | `docs/architecture.md` |
| 2 | Folder structure | ✅ | Modular `app/` layout |
| 3 | Infrastructure diagram | ✅ | Mermaid in `docs/architecture.md` |
| 4 | FastAPI backend | ✅ | `app/main.py`, `app/api/routes.py` |
| 5 | Streamlit frontend | ✅ | `streamlit_app/app.py` |
| 6 | Vector DB (Qdrant) | ✅ | `app/storage/qdrant_store.py` |
| 7 | Elasticsearch (BM25) | ✅ | `app/storage/elasticsearch_store.py` |
| 8 | Knowledge Graph | ✅ | `app/knowledge_graph/graph.py` + `config/graph.yaml` |
| 9 | RBAC middleware | ✅ | `app/security/rbac.py` (retrieval-time filter) |
| 10 | Retrieval pipeline | ✅ | `app/retrieval/pipeline.py` |
| 11 | Evaluation framework | ✅ | `app/evaluation/metrics.py` |
| 12 | Docker | ✅ | `Dockerfile` |
| 13 | Docker Compose | ✅ | `docker-compose.yml` |
| 14 | Unit tests | ✅ | `tests/unit/` |
| 15 | Integration tests | ✅ | `tests/integration/` |
| 16 | Synthetic data generator | ✅ | `scripts/generate_synthetic_data.py` |
| 17 | README | ✅ | `README.md` |

### Bonus (beyond requirements)

| Feature | Location |
|---------|----------|
| Plug-and-play connectors | `config/connectors.yaml`, `app/connectors/` |
| Config hot-reload | `POST /config/reload` |
| Runtime document ingest | `POST /documents` |
| Custom connector plugins | `plugins/connectors/` |

---

## Demo Login Credentials

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Admin |
| engineer | eng123 | Engineering |
| finance | fin123 | Finance |
| hr_user | hr123 | HR |
| compliance | comp123 | Compliance |

## Observability URLs

| Service | URL | How to start (local) |
|---------|-----|----------------------|
| Phoenix (traces) | http://localhost:6006 | `.\venv\Scripts\phoenix serve` |
| Langfuse | http://localhost:3000 | `docker-compose up langfuse` |

**Important:** `phoenix_enabled: true` in the API only means trace export is configured. You must **separately start Phoenix** for the UI to open.

## Production Features Added

| Feature | Status |
|---------|--------|
| JWT Auth + Login | ✅ `POST /auth/login` |
| OIDC SSO | ✅ `GET /auth/sso/login` (configure SSO_* env vars) |
| Streamlit Login | ✅ Required before dashboard access |
| Langfuse | ✅ Integrated (set LANGFUSE keys) |
| Phoenix | ✅ OTLP traces to port 4317 |
| Live RAGAS | ✅ Real pipeline evaluation (heuristic or LLM) |

---

## What Makes This Stand Out

1. **Retrieval-time RBAC** — unauthorized chunks never retrieved (not filter-after-retrieve)
2. **Plug-and-play** — add data sources via YAML or API, no code changes
3. **Hybrid search** — 0.6 semantic + 0.4 BM25 with cross-encoder reranking
4. **Full explainability** — citations, confidence, retrieval trace on every answer
5. **33 automated tests** — judges can verify with one command

---

## How to Submit on HackerEarth

### Step 1 — Prepare the zip/repo

Submit only the `enterprise-rag/` folder. **Do NOT include:**
- `venv/` folder
- `.pytest_cache/`
- `__pycache__/`
- `.env` (secrets)

```powershell
cd c:\Users\ankit\OneDrive\Desktop\Hackerearth
git init
git add enterprise-rag
git commit -m "Enterprise RAG Intelligence Platform submission"
```

Push to GitHub (recommended) or zip `enterprise-rag` without `venv`.

### Step 2 — Verify before submit

```powershell
cd enterprise-rag
.\scripts\start_local.ps1
# Wait 2-3 min, then:
.\venv\Scripts\pytest tests\ -q
```

### Step 3 — HackerEarth submission form

| Field | What to enter |
|-------|---------------|
| **Project title** | Enterprise RAG Intelligence Platform |
| **GitHub URL** | Your public repo link (preferred) |
| **Description** | Copy the text below |
| **Demo video** | Optional 2-min screen recording (highly recommended) |

**Description to paste:**

```
Enterprise-grade RAG platform with RBAC-enforced hybrid retrieval.

Highlights:
• Retrieval-time RBAC — unauthorized data never retrieved
• Hybrid search: BGE embeddings (Qdrant) + BM25 (Elasticsearch)
• Plug-and-play connectors via YAML or API
• Knowledge graph multi-hop reasoning
• JWT auth + OIDC SSO + Streamlit login
• Live RAGAS evaluation + Phoenix/Langfuse observability
• 33 automated tests

Quick start: .\scripts\start_local.ps1
Login: admin / admin123
UI: http://localhost:8501 | API: http://localhost:8000/docs

Full judge guide: SUBMISSION.md in repo root.
```

### Step 4 — Optional demo video (2 min)

1. Run `start_local.ps1`
2. Login as admin
3. Query: "Show failed payment incidents" → show sources + trace
4. Switch role / show RBAC in Audit tab
5. Run `pytest tests/ -q` → 33 passed
