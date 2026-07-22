from __future__ import annotations

import math

import pandas as pd
import pytest

from tens_hq.metrics import (
    FORECAST_HORIZONS,
    FORECAST_VERSION,
    apply_hiring_plan,
    forecast_sites,
    portfolio_summary,
    qualified_hiring_need,
    safe_ratio,
    source_performance,
    trajectory,
)


def test_ratio_edge_cases():
    assert safe_ratio(75, 100) == 0.75
    assert math.isnan(safe_ratio(0, 0))


def test_qualified_hiring_need_uses_both_numerator_and_denominator():
    # (7,000 + 4*520) / (10,000 + 4*520) exceeds 75%; three hires do not.
    assert qualified_hiring_need(7000, 10000, 0.75, 520, 520) == 4
    assert qualified_hiring_need(7600, 10000, 0.75, 520, 520) == 0
    assert qualified_hiring_need(7000, 10000, 0.75, 300, 500) is None


def test_forecast_has_meaningful_story_mix(demo_data):
    forecasts = forecast_sites(demo_data)
    counts = forecasts["risk_status"].value_counts().to_dict()
    assert counts.get("Healthy", 0) >= 3
    assert counts.get("At Risk", 0) + counts.get("Critical", 0) >= 2
    assert forecasts["qualified_hiring_need"].fillna(0).sum() > 0


def test_portfolio_rollup_uses_hours(demo_data):
    forecasts = forecast_sites(demo_data)
    summary = portfolio_summary(forecasts)
    expected = forecasts["projected_qdlh"].sum() / forecasts["projected_total_dlh"].sum()
    assert summary["projected_ratio"] == expected
    assert summary["hours_gap"] == pytest.approx(
        summary["planning_target"] * forecasts["projected_total_dlh"].sum()
        - forecasts["projected_qdlh"].sum()
    )
    assert summary["ratio_gap"] == pytest.approx(
        summary["planning_target"] - summary["projected_ratio"]
    )
    assert summary["ratio_gap_points"] == pytest.approx(summary["ratio_gap"] * 100.0)
    assert summary["formula_version"] == FORECAST_VERSION


def test_started_people_are_not_double_counted_as_pipeline(demo_data):
    forecasts = forecast_sites(demo_data)
    expected_candidates = demo_data.applicants.loc[
        demo_data.applicants["start_date"].isna()
        & ~demo_data.applicants["current_stage"].isin(["Not Selected", "Withdrawn", "Separated"])
    ].shape[0]
    assert forecasts["pipeline_candidates"].sum() == expected_candidates


def test_source_scores_are_bounded_and_confidence_is_visible(demo_data):
    scores = source_performance(demo_data)
    assert scores["reliability_score"].between(0, 100).all()
    assert scores["partner_priority_score"].between(0, 100).all()
    assert {"High", "Medium", "Low"}.issubset(set(scores["confidence_level"]))


def test_apply_hiring_plan_uses_the_qualified_hire_contribution_vector():
    forecasts = pd.DataFrame(
        [
            {
                "site_id": "SYN-SITE-A",
                "current_ratio": 0.70,
                "projected_ratio": 0.70,
                "projected_qdlh": 700.0,
                "projected_total_dlh": 1000.0,
                "current_qdlh": 700.0,
                "current_total_dlh": 1000.0,
                "ready_hire_hours": 100.0,
                "qualified_hiring_need": 2,
                "expected_ready_hires": 1.0,
                "pipeline_candidates": 4,
                "risk_status": "At Risk",
                "scenario": "Base",
                "horizon_days": 90,
                "planning_target": 0.75,
                "formula_version": FORECAST_VERSION,
            },
            {
                "site_id": "SYN-SITE-B",
                "current_ratio": 0.60,
                "projected_ratio": 0.60,
                "projected_qdlh": 600.0,
                "projected_total_dlh": 1000.0,
                "current_qdlh": 600.0,
                "current_total_dlh": 1000.0,
                "ready_hire_hours": 100.0,
                "qualified_hiring_need": 6,
                "expected_ready_hires": 1.5,
                "pipeline_candidates": 5,
                "risk_status": "Critical",
                "scenario": "Base",
                "horizon_days": 90,
                "planning_target": 0.75,
                "formula_version": FORECAST_VERSION,
            },
        ]
    )

    planned = apply_hiring_plan(forecasts, 3, 0.75, 90, "Base")
    site_a = planned.loc[planned["site_id"] == "SYN-SITE-A"].iloc[0]
    site_b = planned.loc[planned["site_id"] == "SYN-SITE-B"].iloc[0]

    assert site_a["committed_ready_hires"] == 0
    assert site_a["projected_ratio"] == 0.70
    assert site_b["committed_ready_hires"] == 3
    assert site_b["projected_ratio"] == pytest.approx((600.0 + 3 * 100.0) / (1000.0 + 3 * 100.0))
    assert site_b["qualified_hiring_need"] == 3
    assert site_b["formula_version"] == "SYN-FORECAST-1.1"
    assert forecasts.loc[1, "projected_qdlh"] == 600.0


def test_trajectory_is_pure_forecast_composition(demo_data):
    result = trajectory(demo_data, target=0.75, scenario="Base")

    assert tuple(sorted(result["horizon_days"].unique())) == FORECAST_HORIZONS
    assert len(result) == len(demo_data.sites) * len(FORECAST_HORIZONS)
    assert result["formula_version"].eq("SYN-FORECAST-1.1").all()
    for horizon in FORECAST_HORIZONS:
        expected = forecast_sites(demo_data, target=0.75, horizon_days=horizon, scenario="Base")
        actual = result.loc[result["horizon_days"] == horizon]
        assert actual["projected_ratio"].tolist() == expected["projected_ratio"].tolist()
        assert actual["portfolio_projected_ratio"].nunique() == 1

    higher_target = trajectory(demo_data, target=0.78, scenario="Base")
    assert higher_target["target_crossing_day"].iloc[0] == 30.0
