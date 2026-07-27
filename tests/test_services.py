from __future__ import annotations

from dataclasses import replace
import inspect

import tens_hq.services as services
from tens_hq.metrics import forecast_sites, source_performance
from tens_hq.services import (
    build_outreach_queue,
    leadership_summary_markdown,
    outreach_email_draft,
    site_report_markdown,
)


def test_do_not_contact_orgs_are_excluded_from_outreach_queue(demo_data):
    do_not_contact = demo_data.organizations["relationship_status"].eq("Do Not Contact")
    assert do_not_contact.sum() > 0

    forecasts = forecast_sites(demo_data)
    scores = source_performance(demo_data)
    queue = build_outreach_queue(demo_data, scores, forecasts)

    assert not queue["relationship_status"].eq("Do Not Contact").any()


def test_do_not_contact_partner_priority_score_is_zero(demo_data):
    scored = source_performance(demo_data)
    organization_id = scored.iloc[0]["organization_id"]
    organizations = demo_data.organizations.copy()
    organizations.loc[
        organizations["organization_id"].eq(organization_id), "relationship_status"
    ] = "Do Not Contact"

    scores = source_performance(replace(demo_data, organizations=organizations))
    do_not_contact = scores.loc[scores["organization_id"].eq(organization_id)]

    assert len(do_not_contact) == 1
    assert do_not_contact.iloc[0]["partner_priority_score"] == 0


def test_outreach_drafts_are_synthetic_and_carry_no_delivery_capability():
    warm_subject, warm_body = outreach_email_draft(
        "Synthetic Partner",
        "Taylor Example",
        "Synthetic Site",
        "Administrative Support",
        "Warm",
    )
    cold_subject, cold_body = outreach_email_draft(
        "Synthetic Partner",
        "Taylor Example",
        "Synthetic Site",
        "Administrative Support",
        "Cold",
    )

    assert warm_subject
    assert cold_subject
    assert "ROCC Demo User (Synthetic)" in warm_body
    assert "ROCC Demo User (Synthetic)" in cold_body
    assert "has not been sent" in cold_body

    source = inspect.getsource(services)
    assert "smtplib" not in source
    assert "requests" not in source
    assert ".send(" not in source
    assert "sendmail" not in source


def test_reports_carry_decision_boundary_banners(demo_data):
    forecasts = forecast_sites(demo_data)
    scores = source_performance(demo_data)
    queue = build_outreach_queue(demo_data, scores, forecasts)

    site_report = site_report_markdown(forecasts.iloc[0])
    leadership_summary = leadership_summary_markdown(forecasts, queue)

    assert "NOT AN OFFICIAL ODLH COMPLIANCE DETERMINATION" in site_report
    assert "SYNTHETIC DEMO DATA — NOT FOR EMPLOYMENT OR COMPLIANCE DECISIONS" in leadership_summary
