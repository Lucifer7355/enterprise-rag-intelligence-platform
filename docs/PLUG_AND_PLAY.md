# Plug & Play Guide

This platform is **fully config-driven**. No code changes needed for most customizations.

## Quick Start (3 steps)

### 1. Add your data

**Option A — Edit config** (`config/connectors.yaml`):

```yaml
connectors:
  - name: my_company_docs
    type: folder
    enabled: true
    path: /path/to/your/documents
    file_patterns: ["*.pdf", "*.txt"]
    metadata:
      department: legal
      classification: confidential
      allowed_roles: [Legal, Admin]
      data_source: legal_docs
```

**Option B — Runtime API**:

```bash
curl -X POST http://localhost:8000/connectors \
  -H "Content-Type: application/json" \
  -d '{
    "name": "sales_csv",
    "type": "csv",
    "path": "data/sales",
    "metadata": {
      "department": "sales",
      "allowed_roles": ["Sales", "Admin"],
      "data_source": "csv"
    }
  }'
```

**Option C — Index a single document**:

```bash
curl -X POST http://localhost:8000/documents \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "policy_001",
    "source": "Remote_Work_Policy.pdf",
    "text": "All employees may work remotely 2 days per week...",
    "metadata": {
      "department": "hr",
      "allowed_roles": ["HR", "Admin"]
    }
  }'
```

### 2. Ingest

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"force_reindex": true}'
```

### 3. Query

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the remote work policy?", "role": "HR"}'
```

---

## Customize Without Code

| What | Config File | Example |
|------|-------------|---------|
| Add roles | `config/rbac.yaml` | Add `Legal` role with inherits |
| Route queries | `config/routing.yaml` | Add "Legal Query" with keywords |
| Protect PII | `config/sensitive_data.yaml` | Add regex + allowed roles |
| Knowledge graph | `config/graph.yaml` | Map SQL tables to entities |
| Auto-tag files | `config/connectors.yaml` | Add `auto_tag_patterns` |

After editing, reload:

```bash
curl -X POST http://localhost:8000/config/reload
```

---

## Custom Connector Plugin

1. Create `plugins/connectors/sharepoint_connector.py`:

```python
from app.connectors.base import BaseConnector
from app.models.schemas import DocumentMetadata

class SharePointConnector(BaseConnector):
    connector_type = "sharepoint"

    def fetch(self):
        # Your SharePoint API logic here
        ...
```

2. Register in `config/connectors.yaml`:

```yaml
- name: sharepoint_hr
  type: sharepoint
  enabled: true
  site_url: https://company.sharepoint.com/hr
  metadata:
    department: hr
    allowed_roles: [HR, Admin]
```

3. `POST /ingest` — done.

---

## Built-in Connector Types

| Type | Description |
|------|-------------|
| `folder` | Directory of PDF/TXT with optional `*_meta.json` sidecars |
| `pdf` | PDF directory (uses PyMuPDF) |
| `csv` | All CSV files in a directory |
| `json` | JSON log files (array or object per file) |
| `sql` | SQLite with per-table templates |
| `inline` | Documents added via `POST /documents` |

---

## API Reference (Plug & Play)

| Endpoint | Purpose |
|----------|---------|
| `GET /roles` | List configured roles |
| `GET /connectors` | List connector types & configs |
| `POST /connectors` | Add connector at runtime |
| `DELETE /connectors/{name}` | Remove connector |
| `POST /documents` | Index single document |
| `POST /config/reload` | Hot-reload YAML configs |
| `GET /config` | View active configuration |
| `POST /ingest` | Run ingestion pipeline |
| `POST /chat` | Query with RBAC |
