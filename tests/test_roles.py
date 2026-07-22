from __future__ import annotations

from tens_hq import roles


EXPECTED_PAGES = (
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


def test_public_demo_exposes_the_complete_ordered_page_set():
    assert roles.ALL_PAGES == EXPECTED_PAGES
    assert roles.allowed_pages() == EXPECTED_PAGES


def test_collapsed_roles_module_has_no_visibility_or_pilot_concepts():
    removed_names = {
        "ROLES",
        "ROLE_PAGES",
        "DEFAULT_ROLE",
        "current_role",
        "pilot_mode_enabled",
        "PILOT_MODE_ENV",
        "PILOT_PAGES",
        "can",
    }
    assert removed_names.isdisjoint(vars(roles))
