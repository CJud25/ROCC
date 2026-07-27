from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_freshness  # noqa: E402


def test_fresh_on_2026_07_27():
    assert check_freshness.stale_facts(date(2026, 7, 27)) == []


def test_stale_after_365_days():
    findings = check_freshness.stale_facts(date(2027, 7, 1))
    assert len(findings) == 1
    assert "DATA_AS_OF_DATE" in findings[0]
    assert "deadline 2027-06-30" in findings[0]


def test_deadline_day_is_fresh():
    assert check_freshness.stale_facts(date(2027, 6, 30)) == []


def test_registry_is_not_empty():
    assert check_freshness.fact_registry()
