"""Ordered page visibility for the public ROCC demonstration.

Visibility roles and pilot gating belonged to the combined private demo. ROCC
publishes one aggregate-safe surface, so every page is visible to every viewer.
"""

from __future__ import annotations


ALL_PAGES = (
    "Home / Executive Overview",
    "Site Readiness",
    "Resource Network",
    "Outreach Command Center",
    "Pipeline Health",
    "Source Performance",
    "Ratio Forecast",
    "Reports",
    "Privacy & Governance",
)


def allowed_pages() -> tuple[str, ...]:
    """Return the complete ordered public page set."""

    return ALL_PAGES
