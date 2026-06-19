"""Process SQL, CSV, and JSON into searchable documents."""

import json
import sqlite3
from pathlib import Path

import pandas as pd

from app.models.schemas import DocumentMetadata


def process_sql_tables(db_path: Path) -> list[tuple[str, DocumentMetadata]]:
    """Convert SQL rows to searchable text documents."""
    conn = sqlite3.connect(db_path)
    documents = []

    employees = pd.read_sql("SELECT * FROM employees", conn)
    for _, row in employees.iterrows():
        doc_id = f"employee_{row['employee_id']}"
        text = (
            f"Employee #{row['employee_id']}\n"
            f"Name: {row['name']}\n"
            f"Department: {row['department']}\n"
            f"Salary: {row['salary']}\n"
            f"Manager: {row['manager']}"
        )
        meta = DocumentMetadata(
            document_id=doc_id,
            source="employees.sql",
            department="hr",
            classification="confidential",
            allowed_roles=["HR", "Admin", "Finance"],
            security_level="confidential",
            data_source="sql",
        )
        documents.append((text, meta))

    incidents = pd.read_sql("SELECT * FROM incidents", conn)
    for _, row in incidents.iterrows():
        doc_id = f"incident_{row['incident_id']}"
        text = (
            f"Incident {row['incident_id']}\n"
            f"Service: {row['service']}\n"
            f"Severity: {row['severity']}\n"
            f"Owner: {row['owner']}\n"
            f"Status: {row['status']}"
        )
        meta = DocumentMetadata(
            document_id=doc_id,
            source="incidents.sql",
            department="engineering",
            classification="internal",
            allowed_roles=["Engineering", "Admin", "Compliance"],
            security_level="internal",
            data_source="sql",
        )
        documents.append((text, meta))

    assets = pd.read_sql("SELECT * FROM assets", conn)
    for _, row in assets.iterrows():
        doc_id = f"asset_{row['asset_id']}"
        text = (
            f"Asset {row['asset_id']}\n"
            f"Owner Team: {row['owner_team']}\n"
            f"Criticality: {row['criticality']}"
        )
        meta = DocumentMetadata(
            document_id=doc_id,
            source="assets.sql",
            department="engineering",
            classification="internal",
            allowed_roles=["Engineering", "Admin", "Compliance", "Executive"],
            security_level="internal",
            data_source="sql",
        )
        documents.append((text, meta))

    conn.close()
    return documents


def process_csv_files(csv_dir: Path) -> list[tuple[str, DocumentMetadata]]:
    documents = []
    for csv_file in csv_dir.glob("*.csv"):
        df = pd.read_csv(csv_file)
        for i, row in df.iterrows():
            doc_id = f"{csv_file.stem}_{i}"
            text = f"Financial Record from {csv_file.name}\n" + "\n".join(
                f"{col}: {row[col]}" for col in df.columns
            )
            meta = DocumentMetadata(
                document_id=doc_id,
                source=csv_file.name,
                department="finance",
                classification="confidential",
                allowed_roles=["Finance", "Admin", "Executive"],
                security_level="confidential",
                data_source="csv",
            )
            documents.append((text, meta))
    return documents


def process_json_logs(log_dir: Path) -> list[tuple[str, DocumentMetadata]]:
    documents = []
    for json_file in log_dir.glob("*.json"):
        with open(json_file) as f:
            logs = json.load(f)
        for i, entry in enumerate(logs):
            doc_id = f"{json_file.stem}_{i}"
            text = json.dumps(entry, indent=2)
            dept = "engineering" if "payment" in text.lower() or "api" in text.lower() else "compliance"
            roles = ["Engineering", "Admin", "Compliance"]
            if "audit" in json_file.name:
                roles = ["Compliance", "Admin"]
            meta = DocumentMetadata(
                document_id=doc_id,
                source=json_file.name,
                department=dept,
                classification="internal",
                allowed_roles=roles,
                security_level="internal",
                data_source="json_log",
            )
            documents.append((text, meta))
    return documents
