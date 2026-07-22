from __future__ import annotations

import json
import re

import pandas as pd

from tens_hq import pages


def test_all_required_pages_are_registered():
    assert list(pages.PAGE_RENDERERS) == [
        "Home / Executive Overview",
        "Site Readiness",
        "Resource Network",
        "Outreach Command Center",
        "Pipeline Health",
        "Source Performance",
        "Ratio Forecast",
        "Reports",
        "Privacy & Governance",
    ]


def test_bd_feasibility_is_not_registered():
    assert "BD Feasibility" not in pages.PAGE_RENDERERS
    assert pages.PAGE_RENDERERS["Pipeline Health"] is pages.render_applicant_pipeline


def test_pipeline_health_never_renders_applicant_identifiers_or_names(monkeypatch, demo_data):
    rendered: list[object] = []

    def record(*args, **kwargs):
        rendered.extend(args)
        rendered.extend(kwargs.values())

    class MetricColumn:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def metric(self, *args, **kwargs):
            record(*args, **kwargs)

    monkeypatch.setattr(
        pages.st,
        "columns",
        lambda count, *args, **kwargs: [MetricColumn() for _ in range(count)],
    )
    monkeypatch.setattr(pages.st, "markdown", record)
    monkeypatch.setattr(pages.st, "caption", record)
    monkeypatch.setattr(pages.st, "plotly_chart", record)
    monkeypatch.setattr(pages.st, "dataframe", record)

    pages.render_applicant_pipeline(demo_data, target=0.75, scenario="Base")

    identity_fields = {"applicant_id", "display_label"}
    assert identity_fields.issubset(demo_data.applicants.columns)
    rendered_frames = [value for value in rendered if isinstance(value, pd.DataFrame)]
    assert rendered_frames
    normalized_columns = {
        re.sub(r"[^a-z0-9]", "", str(column).lower())
        for frame in rendered_frames
        for column in frame.columns
    }
    forbidden_columns = {
        "applicantid",
        "applicantname",
        "candidateid",
        "candidatename",
        "displaylabel",
    }
    assert normalized_columns.isdisjoint(forbidden_columns)

    def serializable(value: object) -> object:
        if isinstance(value, pd.DataFrame):
            return {"columns": value.columns.tolist(), "records": value.to_dict("records")}
        if hasattr(value, "to_plotly_json"):
            return value.to_plotly_json()
        return str(value)

    rendered_text = json.dumps(
        [serializable(value) for value in rendered], default=str, ensure_ascii=False
    )
    assert "Pipeline Health" in rendered_text
    assert (
        "applicants are never listed or scored here — aggregate pipeline health only; "
        "synthetic partner-org contacts appear only in the outreach workflow and are never scored."
        in rendered_text
    )
    for field in identity_fields:
        assert field not in rendered_text

    applicant_values = set(demo_data.applicants["applicant_id"].astype(str))
    applicant_values.update(demo_data.applicants["display_label"].astype(str))
    leaked_values = sorted(value for value in applicant_values if value in rendered_text)
    assert leaked_values == []
