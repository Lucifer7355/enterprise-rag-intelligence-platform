"""Unit tests for config-driven sensitive data protection."""

from app.security.sensitive_data import detect_sensitive_content, process_sensitive_text


def test_detect_salary():
    assert "salary" in detect_sensitive_content("Employee salary: 150000")


def test_engineering_blocked_from_salary():
    _, denial, action = process_sensitive_text("Salary: 150000", "Engineering")
    assert action == "blocked"
    assert denial and "Insufficient permissions" in denial


def test_hr_can_view_salary():
    _, denial, action = process_sensitive_text("Salary: 150000", "HR")
    assert action == "allowed"
    assert denial is None


def test_secret_skipped_for_engineering():
    _, denial, action = process_sensitive_text("api_key=sk-secret123", "Engineering")
    assert action == "skipped"
    assert denial is None


def test_admin_can_view_secret():
    text, denial, action = process_sensitive_text("api_key=sk-secret123", "Admin")
    assert action == "allowed"
    assert "api_key" in text
