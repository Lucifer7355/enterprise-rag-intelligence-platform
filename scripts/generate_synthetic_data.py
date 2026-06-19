"""Generate synthetic enterprise data for the RAG platform."""

import json
import sqlite3
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "synthetic"


def generate_pdfs_text() -> dict[str, dict]:
    """Generate text content for PDF-like documents."""
    docs = {
        "Compliance_Handbook_2025.pdf": {
            "content": """
            Enterprise Compliance Handbook 2025

            Section 1: Data Protection
            All employees must comply with GDPR and SOC2 requirements.
            Personal data including SSN (format: 123-45-6789) must be encrypted at rest.

            Section 2: Violation Reporting
            Compliance violations must be reported within 24 hours.
            Systems owned by Team Alpha have had 3 compliance violations in Q1 2025
            related to unauthorized data access.

            Section 3: Audit Requirements
            Quarterly audits are mandatory for all financial systems.
            Payment-api service failed compliance checks in January 2025.
            """,
            "department": "compliance",
            "classification": "confidential",
            "allowed_roles": ["Compliance", "Admin", "Executive"],
            "data_source": "compliance",
        },
        "HR_Policies_2025.pdf": {
            "content": """
            Human Resources Policy Manual 2025

            Section 1: Compensation
            Salary information is confidential. Only HR and Finance may access compensation data.
            Annual salary reviews occur in March.

            Section 2: Leave Policy
            Employees receive 20 days PTO annually.
            Manager approval required for leave exceeding 5 consecutive days.

            Section 3: Onboarding
            New hires must complete security training within first week.
            """,
            "department": "hr",
            "classification": "internal",
            "allowed_roles": ["HR", "Admin"],
            "data_source": "hr_policy",
        },
        "Engineering_Runbook_Payment.pdf": {
            "content": """
            Payment API Engineering Runbook

            Service: payment-api
            Owner Team: Team Alpha
            Criticality: HIGH

            Incident Response:
            1. Check service health dashboard
            2. Review JSON logs for ERROR severity events
            3. Escalate to on-call if transaction timeout rate exceeds 5%

            Known Issues:
            Transaction timeout errors occur during peak load.
            Failed payment incidents should be logged with severity ERROR.

            Deployment:
            Blue-green deployment every Tuesday.
            Rollback procedure documented in Section 4.
            """,
            "department": "engineering",
            "classification": "internal",
            "allowed_roles": ["Engineering", "Admin"],
            "data_source": "engineering_runbook",
        },
        "Security_Report_Q1_2025.pdf": {
            "content": """
            Security Assessment Report Q1 2025

            Executive Summary:
            12 security incidents detected in Q1 2025.
            Payment-api experienced 5 authentication failures.
            API key rotation overdue for 3 services.

            Recommendations:
            - Implement MFA for all admin accounts
            - Rotate API keys quarterly
            - Enable WAF on payment-api

            Internal secret detected: api_key=sk-prod-abc123xyz (REDACTED IN PRODUCTION)
            """,
            "department": "engineering",
            "classification": "confidential",
            "allowed_roles": ["Engineering", "Admin", "Compliance"],
            "data_source": "incident_report",
        },
    }
    return docs


def generate_sql_database(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            employee_id INTEGER PRIMARY KEY,
            name TEXT,
            department TEXT,
            salary INTEGER,
            manager TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            incident_id TEXT PRIMARY KEY,
            service TEXT,
            severity TEXT,
            owner TEXT,
            status TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            asset_id TEXT PRIMARY KEY,
            owner_team TEXT,
            criticality TEXT
        )
    """)

    employees = [
        (101, "Alice Chen", "Finance", 150000, "Bob Smith"),
        (102, "Bob Smith", "Finance", 180000, "Carol Davis"),
        (103, "Carol Davis", "HR", 165000, "David Lee"),
        (104, "David Lee", "Engineering", 175000, "Eve Wilson"),
        (105, "Eve Wilson", "Engineering", 160000, "Frank Brown"),
        (106, "Frank Brown", "Compliance", 155000, "Alice Chen"),
    ]
    cursor.executemany(
        "INSERT OR REPLACE INTO employees VALUES (?,?,?,?,?)", employees
    )

    incidents = [
        ("INC-001", "payment-api", "ERROR", "Team Alpha", "open"),
        ("INC-002", "payment-api", "CRITICAL", "Team Alpha", "resolved"),
        ("INC-003", "auth-service", "WARNING", "Team Beta", "open"),
        ("INC-004", "payment-api", "ERROR", "Team Alpha", "investigating"),
        ("INC-005", "data-pipeline", "INFO", "Team Gamma", "closed"),
    ]
    cursor.executemany(
        "INSERT OR REPLACE INTO incidents VALUES (?,?,?,?,?)", incidents
    )

    assets = [
        ("AST-001", "Team Alpha", "HIGH"),
        ("AST-002", "Team Alpha", "MEDIUM"),
        ("AST-003", "Team Beta", "HIGH"),
        ("AST-004", "Team Gamma", "LOW"),
        ("AST-005", "Team Alpha", "CRITICAL"),
    ]
    cursor.executemany(
        "INSERT OR REPLACE INTO assets VALUES (?,?,?)", assets
    )

    conn.commit()
    conn.close()


def generate_csv_files(csv_dir: Path) -> None:
    csv_dir.mkdir(parents=True, exist_ok=True)

    expenses = pd.DataFrame({
        "month": ["2025-01", "2025-01", "2025-02", "2025-02"],
        "category": ["Infrastructure", "Marketing", "Infrastructure", "HR"],
        "amount": [45000, 12000, 48000, 8500],
        "department": ["Engineering", "Marketing", "Engineering", "HR"],
    })
    expenses.to_csv(csv_dir / "monthly_expenses.csv", index=False)

    revenue = pd.DataFrame({
        "month": ["2025-01", "2025-02", "2025-03"],
        "product": ["Enterprise", "SMB", "Enterprise"],
        "revenue": [250000, 85000, 275000],
        "region": ["NA", "EU", "NA"],
    })
    revenue.to_csv(csv_dir / "revenue_reports.csv", index=False)


def generate_json_logs(log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)

    auth_events = [
        {"timestamp": "2025-01-05T10:00:00Z", "service": "auth-service", "severity": "INFO", "message": "User login successful", "user": "alice@corp.com"},
        {"timestamp": "2025-01-06T14:30:00Z", "service": "auth-service", "severity": "WARNING", "message": "Failed login attempt", "user": "unknown"},
        {"timestamp": "2025-01-07T09:15:00Z", "service": "payment-api", "severity": "ERROR", "message": "Authentication token expired"},
    ]
    with open(log_dir / "authentication_events.json", "w") as f:
        json.dump(auth_events, f, indent=2)

    api_failures = [
        {"timestamp": "2025-01-08T11:00:00Z", "service": "payment-api", "severity": "ERROR", "message": "Transaction timeout", "transaction_id": "TXN-991"},
        {"timestamp": "2025-01-09T16:45:00Z", "service": "payment-api", "severity": "ERROR", "message": "Transaction timeout", "transaction_id": "TXN-992"},
        {"timestamp": "2025-01-10T08:20:00Z", "service": "payment-api", "severity": "CRITICAL", "message": "Payment gateway unreachable"},
        {"timestamp": "2025-01-11T13:00:00Z", "service": "data-pipeline", "severity": "ERROR", "message": "ETL job failed"},
    ]
    with open(log_dir / "api_failures.json", "w") as f:
        json.dump(api_failures, f, indent=2)

    audit_logs = [
        {"timestamp": "2025-01-12T10:00:00Z", "action": "data_access", "user": "compliance_officer", "resource": "Compliance_Handbook_2025.pdf", "result": "allowed"},
        {"timestamp": "2025-01-13T11:30:00Z", "action": "data_access", "user": "engineer1", "resource": "salary_data", "result": "denied"},
        {"timestamp": "2025-01-14T09:00:00Z", "action": "compliance_check", "service": "payment-api", "result": "failed", "team": "Team Alpha"},
    ]
    with open(log_dir / "audit_logs.json", "w") as f:
        json.dump(audit_logs, f, indent=2)


def save_pdf_text_files(pdf_dir: Path) -> None:
    pdf_dir.mkdir(parents=True, exist_ok=True)
    docs = generate_pdfs_text()
    for filename, meta in docs.items():
        txt_path = pdf_dir / filename.replace(".pdf", ".txt")
        txt_path.write_text(meta["content"].strip(), encoding="utf-8")
        meta_path = pdf_dir / filename.replace(".pdf", "_meta.json")
        meta_path.write_text(
            json.dumps({
                "department": meta["department"],
                "classification": meta["classification"],
                "allowed_roles": meta["allowed_roles"],
                "data_source": meta["data_source"],
            }, indent=2),
            encoding="utf-8",
        )


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    save_pdf_text_files(DATA_DIR / "pdfs")
    generate_sql_database(DATA_DIR / "enterprise.db")
    generate_csv_files(DATA_DIR / "csv")
    generate_json_logs(DATA_DIR / "json_logs")
    print(f"Synthetic data generated in {DATA_DIR}")


if __name__ == "__main__":
    main()
