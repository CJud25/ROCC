"""Scheduled freshness runbook.
Reads: DATA_AS_OF_DATE from src/tens_hq/constants.py.
Red: the synthetic demo date is more than 365 days old or the fact registry is empty.
Remediation: review the demo facts, regenerate them, and advance DATA_AS_OF_DATE.
Notification: GitHub emails the scheduled-run actor; 60 days of inactivity may auto-disable the schedule with warning.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tens_hq.constants import DATA_AS_OF_DATE  # noqa: E402


MAX_FACT_AGE_DAYS = 365


@dataclass(frozen=True)
class Fact:
    name: str
    as_of: date
    remediation: str

    @property
    def deadline(self) -> date:
        return self.as_of + timedelta(days=MAX_FACT_AGE_DAYS)


def fact_registry() -> tuple[Fact, ...]:
    return (
        Fact(
            name="DATA_AS_OF_DATE",
            as_of=DATA_AS_OF_DATE,
            remediation="review the demo facts, regenerate them, and advance DATA_AS_OF_DATE",
        ),
    )


def stale_facts(today: date) -> list[str]:
    facts = fact_registry()
    if not facts:
        return ["fact registry is empty; restore at least one machine-readable dated fact"]
    return [
        f"{fact.name}: deadline {fact.deadline.isoformat()}; {fact.remediation}"
        for fact in facts
        if today > fact.deadline
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Check ROCC's dated demo facts for staleness.")
    parser.add_argument("--today", type=date.fromisoformat, help="override today with YYYY-MM-DD")
    args = parser.parse_args()
    today = args.today or date.today()

    facts = fact_registry()
    findings = stale_facts(today)
    if not facts:
        for finding in findings:
            print(f"STALE: {finding}")
        return 1

    for fact in facts:
        status = "STALE" if today > fact.deadline else "FRESH"
        print(
            f"{status}: {fact.name} as of {fact.as_of.isoformat()} "
            f"(deadline {fact.deadline.isoformat()})"
        )
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
