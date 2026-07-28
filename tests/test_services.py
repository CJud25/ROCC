from __future__ import annotations

from dataclasses import replace
import inspect

import pytest

from tens_hq import pages
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
    assert scored.iloc[0]["partner_priority_score"] != 0

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


@pytest.mark.parametrize("missing_need", [None, float("nan")], ids=["none", "nan"])
def test_missing_qualified_hiring_need_is_zero_in_frame_consumers(
    monkeypatch, demo_data, missing_need
):
    forecasts90 = forecast_sites(demo_data)
    needs = forecasts90["qualified_hiring_need"].astype(float).tolist()
    needs[0] = missing_need
    forecasts90 = forecasts90.assign(qualified_hiring_need=needs)
    forecasts180 = forecast_sites(demo_data, horizon_days=180)

    assert str(forecasts90["qualified_hiring_need"].dtype) == "float64"

    scores = source_performance(demo_data)
    queue = build_outreach_queue(demo_data, scores, forecasts90)
    leadership_summary = leadership_summary_markdown(forecasts90, queue)

    assert "North Harbor Services: At Risk" in leadership_summary
    assert "need 0" in leadership_summary

    rendered_metrics = {}

    class MetricColumn:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def metric(self, label, value, *_args, **_kwargs):
            rendered_metrics[label] = value

    monkeypatch.setattr(
        pages,
        "_cached_forecast_sites",
        lambda _data, _seed, _target, _scenario, horizon: (
            forecasts90 if horizon == 90 else forecasts180
        ),
    )
    monkeypatch.setattr(pages, "_cached_source_performance", lambda *_args: scores)
    monkeypatch.setattr(
        pages.st,
        "columns",
        lambda spec, *_args, **_kwargs: [
            MetricColumn() for _ in range(spec if isinstance(spec, int) else len(spec))
        ],
    )
    monkeypatch.setattr(pages.st, "selectbox", lambda _label, options: options[0])
    monkeypatch.setattr(pages.st, "markdown", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(pages.st, "caption", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(pages.st, "plotly_chart", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(pages.st, "dataframe", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(pages.st, "info", lambda *_args, **_kwargs: None)

    pages.render_site_readiness(demo_data, target=0.75, scenario="Base")

    assert rendered_metrics["Ready hires still needed"] == 0
