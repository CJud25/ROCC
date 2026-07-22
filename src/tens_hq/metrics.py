"""Versioned, testable metric logic shared by every ROCC page."""

from __future__ import annotations

from datetime import timedelta
from math import ceil

import numpy as np
import pandas as pd

from .constants import (
    DATA_AS_OF_DATE,
    DEFAULT_TARGET,
    PLANNING_BUFFER,
    STAGE_START_PROBABILITY,
)
from .synthetic import DemoData

FORECAST_VERSION = "SYN-FORECAST-1.1"
PARTNER_SCORE_VERSION = "SYN-PARTNER-1.1"

FORECAST_HORIZONS = (30, 60, 90, 120, 150, 180)
_SCENARIO_SETTINGS = {
    "Conservative": {"conversion": 0.78, "attrition": 1.25, "ramp": 0.82},
    "Base": {"conversion": 1.00, "attrition": 1.00, "ramp": 1.00},
    "Optimistic": {"conversion": 1.16, "attrition": 0.78, "ramp": 1.08},
}

_PIPELINE_FUNNEL_STAGES = (
    "Referred",
    "Applied",
    "Interviewed",
    "Offered",
    "Hired",
    "Eligibility Cleared",
)


def safe_ratio(numerator: float, denominator: float) -> float:
    """Return a ratio or NaN when the denominator cannot support one."""

    if denominator <= 0:
        return float("nan")
    return float(numerator / denominator)


def site_pipeline_stage_counts(data: DemoData, site_id: str) -> pd.DataFrame:
    """Aggregate the current synthetic pipeline by stage for one site."""

    counts = (
        data.applicants.loc[
            data.applicants["target_site_id"] == site_id,
            "current_stage",
        ]
        .value_counts()
        .rename_axis("stage")
        .reset_index(name="candidates")
    )
    return counts


def pipeline_health(data: DemoData) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Build the aggregate-only applicant pipeline output contract.

    Person-like records are consumed only inside this metric layer. The three
    returned frames contain funnel measures, stage-age summaries, and
    referral-source shares; none can identify or score an applicant.
    """

    reached_by_stage = data.stage_history.groupby("to_stage")["applicant_id"].nunique()
    reached = [int(reached_by_stage.get(stage, 0)) for stage in _PIPELINE_FUNNEL_STAGES]
    conversion = [np.nan]
    conversion.extend(
        current / previous if previous else np.nan
        for current, previous in zip(reached[1:], reached[:-1])
    )
    funnel = pd.DataFrame(
        {
            "Stage": _PIPELINE_FUNNEL_STAGES,
            "Reached stage": reached,
            "Conversion from prior stage": conversion,
        }
    )

    current = data.applicants[["current_stage", "stage_date"]].copy()
    current["Days in stage"] = (
        pd.Timestamp(DATA_AS_OF_DATE) - pd.to_datetime(current["stage_date"])
    ).dt.days.clip(lower=0)
    stage_age = (
        current.dropna(subset=["stage_date"])
        .groupby("current_stage", as_index=False)
        .agg(Records=("Days in stage", "size"), median_days=("Days in stage", "median"))
        .rename(
            columns={
                "current_stage": "Current stage",
                "median_days": "Median days in stage",
            }
        )
    )
    stage_age["Median days in stage"] = stage_age["Median days in stage"].round(1)
    stage_age = stage_age.sort_values(
        ["Records", "Current stage"], ascending=[False, True]
    ).reset_index(drop=True)

    source_mix = (
        data.applicants.groupby("source_organization_id", as_index=False)
        .size()
        .rename(columns={"size": "Referrals"})
        .merge(
            data.organizations[["organization_id", "organization_name"]],
            left_on="source_organization_id",
            right_on="organization_id",
            how="left",
        )
    )
    total = int(source_mix["Referrals"].sum())
    source_mix["Portfolio share"] = source_mix["Referrals"] / total if total else np.nan
    source_mix = (
        source_mix.rename(columns={"organization_name": "Referral source"})
        [["Referral source", "Referrals", "Portfolio share"]]
        .sort_values(["Referrals", "Referral source"], ascending=[False, True])
        .reset_index(drop=True)
    )
    return funnel, stage_age, source_mix


def qualified_hiring_need(
    projected_qdlh: float,
    projected_total_dlh: float,
    target: float,
    qdlh_per_hire: float,
    total_dlh_per_hire: float,
) -> int | None:
    """Calculate additional ready hires using numerator/denominator contribution margin."""

    hours_gap = max(0.0, target * projected_total_dlh - projected_qdlh)
    if hours_gap == 0:
        return 0
    contribution = qdlh_per_hire - target * total_dlh_per_hire
    if contribution <= 0:
        return None
    return int(ceil(hours_gap / contribution))


def _risk_status(
    projected_ratio: float,
    target: float,
    pipeline_coverage: float | None,
    direction: float,
) -> str:
    if np.isnan(projected_ratio):
        return "Critical"
    if projected_ratio < target - 0.10 or (pipeline_coverage is not None and pipeline_coverage < 0.50):
        return "Critical"
    if projected_ratio < target or (pipeline_coverage is not None and pipeline_coverage < 0.90):
        return "At Risk"
    if (
        projected_ratio < target + PLANNING_BUFFER
        or direction < -0.01
        or (pipeline_coverage is not None and pipeline_coverage < 1.25)
    ):
        return "Watch"
    return "Healthy"


def forecast_sites(
    data: DemoData,
    target: float = DEFAULT_TARGET,
    horizon_days: int = 90,
    scenario: str = "Base",
) -> pd.DataFrame:
    """Forecast site readiness using aggregate stage probabilities, never person scores."""

    if scenario not in _SCENARIO_SETTINGS:
        raise ValueError(f"Unknown scenario: {scenario}")
    settings = _SCENARIO_SETTINGS[scenario]
    as_of = pd.Timestamp(DATA_AS_OF_DATE)
    weeks = horizon_days / 7.0
    months = horizon_days / 30.4375

    latest_month = data.labor_hours["month_start"].max()
    latest = data.labor_hours.loc[data.labor_hours["month_start"] == latest_month].copy()
    latest = latest.merge(
        data.sites[
            [
                "site_id",
                "site_name",
                "county_name",
                "state_code",
                "contract_type",
                "default_weekly_dlh_per_hire",
                "expected_attrition_fte",
                "open_roles_count",
            ]
        ],
        on="site_id",
        suffixes=("", "_site"),
    )

    # Started records are represented in the closed labor-hour baseline. Excluding
    # them prevents double counting. The remaining records are grouped before any
    # probability is applied so ROCC measures pipeline strata, never individuals.
    active = data.applicants.loc[
        data.applicants["start_date"].isna()
        & ~data.applicants["current_stage"].isin(["Not Selected", "Withdrawn", "Separated"])
    ]
    pipeline_strata = (
        active.groupby(["target_site_id", "current_stage", "qdl_count_status"], as_index=False)
        .agg(
            pipeline_candidates=("applicant_id", "nunique"),
            expected_weekly_dlh=("expected_weekly_dlh", "sum"),
        )
    )
    pipeline_strata["start_probability"] = (
        pipeline_strata["current_stage"].map(STAGE_START_PROBABILITY).fillna(0.0)
    )
    pipeline_strata["start_probability"] = np.minimum(
        1.0, pipeline_strata["start_probability"] * settings["conversion"]
    )
    qdl_probability_map = {
        "Mock Countable": 1.0,
        "Pending": 0.82,
        "Mock Not Countable": 0.0,
        "Not Applicable": 0.0,
    }
    pipeline_strata["qdl_probability"] = (
        pipeline_strata["qdl_count_status"].map(qdl_probability_map).fillna(0.72)
    )
    pipeline_strata["expected_total_hours"] = (
        pipeline_strata["expected_weekly_dlh"]
        * weeks
        * pipeline_strata["start_probability"]
        * settings["ramp"]
    )
    pipeline_strata["expected_qdl_hours"] = (
        pipeline_strata["expected_total_hours"] * pipeline_strata["qdl_probability"]
    )
    pipeline_strata["expected_ready_hires"] = (
        pipeline_strata["pipeline_candidates"]
        * pipeline_strata["start_probability"]
        * pipeline_strata["qdl_probability"]
    )
    pipeline = (
        pipeline_strata.groupby("target_site_id", as_index=False)
        .agg(
            pipeline_candidates=("pipeline_candidates", "sum"),
            expected_total_hours=("expected_total_hours", "sum"),
            expected_qdl_hours=("expected_qdl_hours", "sum"),
            expected_ready_hires=("expected_ready_hires", "sum"),
        )
        .rename(columns={"target_site_id": "site_id"})
    )
    result = latest.merge(pipeline, on="site_id", how="left")
    for column in [
        "pipeline_candidates",
        "expected_total_hours",
        "expected_qdl_hours",
        "expected_ready_hires",
    ]:
        result[column] = result[column].fillna(0.0)

    result["baseline_total_dlh"] = result["total_direct_labor_hours"] * months
    result["baseline_qdlh"] = result["mock_qdl_hours"] * months
    result["attrition_total_hours"] = (
        result["expected_attrition_fte_site"]
        * result["default_weekly_dlh_per_hire"]
        * weeks
        * settings["attrition"]
    )
    # The synthetic story assumes attrition is somewhat concentrated in QDL hours.
    result["attrition_qdl_hours"] = result["attrition_total_hours"] * np.minimum(
        0.96, result["current_ratio_pct"] / 100.0 + 0.10
    )
    result["projected_total_dlh"] = (
        result["baseline_total_dlh"] - result["attrition_total_hours"] + result["expected_total_hours"]
    )
    result["projected_qdlh"] = (
        result["baseline_qdlh"] - result["attrition_qdl_hours"] + result["expected_qdl_hours"]
    )
    result["current_total_dlh"] = result["total_direct_labor_hours"]
    result["current_qdlh"] = result["mock_qdl_hours"]
    result["projected_ratio"] = result.apply(
        lambda row: safe_ratio(row["projected_qdlh"], row["projected_total_dlh"]), axis=1
    )
    result["current_ratio"] = result["current_ratio_pct"] / 100.0
    result["direction"] = result["projected_ratio"] - result["current_ratio"]

    needs: list[int | None] = []
    coverage_values: list[float | None] = []
    statuses: list[str] = []
    explanations: list[str] = []
    for row in result.itertuples(index=False):
        hours_per_hire = row.default_weekly_dlh_per_hire * weeks * settings["ramp"]
        need = qualified_hiring_need(
            row.projected_qdlh,
            row.projected_total_dlh,
            target,
            hours_per_hire,
            hours_per_hire,
        )
        needs.append(need)
        coverage = None if need in {None, 0} else float(row.expected_ready_hires / need)
        coverage_values.append(coverage)
        status = _risk_status(row.projected_ratio, target, coverage, row.direction)
        statuses.append(status)
        if row.attrition_qdl_hours > row.expected_qdl_hours:
            driver = "expected QDL-hour attrition exceeds probability-weighted pipeline replacement"
        elif row.projected_ratio < target:
            driver = "the projected planning ratio remains below the configurable target"
        elif coverage is not None and coverage < 1.25:
            driver = "pipeline coverage does not yet provide a comfortable operating buffer"
        else:
            driver = "pipeline contribution and current hours support the planning buffer"
        action = (
            "prioritize a 14-day partner outreach sprint"
            if status in {"Critical", "At Risk"}
            else "monitor assumptions and maintain partner cadence"
        )
        explanations.append(f"{row.site_name} is {status} because {driver}. Recommended action: {action}.")

    result["qualified_hiring_need"] = needs
    result["pipeline_coverage"] = coverage_values
    result["risk_status"] = statuses
    result["explanation"] = explanations
    result["scenario"] = scenario
    result["horizon_days"] = horizon_days
    result["planning_target"] = target
    result["ready_hire_hours"] = (
        result["default_weekly_dlh_per_hire"] * weeks * settings["ramp"]
    )
    result["formula_version"] = FORECAST_VERSION
    return result[
        [
            "site_id",
            "site_name",
            "county_name",
            "state_code",
            "contract_type",
            "current_ratio",
            "projected_ratio",
            "direction",
            "open_roles_count",
            "pipeline_candidates",
            "expected_ready_hires",
            "expected_attrition_fte_site",
            "attrition_qdl_hours",
            "expected_qdl_hours",
            "current_total_dlh",
            "current_qdlh",
            "projected_total_dlh",
            "projected_qdlh",
            "ready_hire_hours",
            "qualified_hiring_need",
            "pipeline_coverage",
            "risk_status",
            "explanation",
            "scenario",
            "horizon_days",
            "planning_target",
            "formula_version",
        ]
    ].rename(
        columns={"expected_attrition_fte_site": "expected_attrition_fte"}
    )


def portfolio_summary(forecasts: pd.DataFrame) -> dict[str, float | int | str]:
    """Roll up ratios correctly by summing hours, never averaging percentages."""

    total = float(forecasts["projected_total_dlh"].sum())
    qdl = float(forecasts["projected_qdlh"].sum())
    current_total = float(forecasts["current_total_dlh"].sum())
    current_qdl = float(forecasts["current_qdlh"].sum())
    targets = pd.to_numeric(forecasts["planning_target"], errors="coerce").dropna().unique()
    if len(targets) != 1:
        raise ValueError("Forecast rows must share one planning target")
    target = float(targets[0])
    projected_ratio = safe_ratio(qdl, total)
    return {
        "current_ratio": safe_ratio(current_qdl, current_total),
        "projected_ratio": projected_ratio,
        "planning_target": target,
        "ratio_gap": target - projected_ratio,
        "ratio_gap_points": (target - projected_ratio) * 100.0,
        "hours_gap": target * total - qdl,
        "projected_qdlh": qdl,
        "projected_total_dlh": total,
        "at_risk_sites": int(forecasts["risk_status"].isin(["At Risk", "Critical"]).sum()),
        "qualified_hires_needed": int(pd.to_numeric(forecasts["qualified_hiring_need"], errors="coerce").fillna(0).sum()),
        "pipeline_candidates": int(forecasts["pipeline_candidates"].sum()),
        "formula_version": FORECAST_VERSION,
    }


def apply_hiring_plan(
    forecasts: pd.DataFrame,
    ready_hires: int,
    target: float,
    horizon: int,
    scenario: str,
) -> pd.DataFrame:
    """Apply committed ready hires to the highest remaining site needs.

    Each assigned hire contributes the same versioned QDLH and total-DLH amount
    used by :func:`qualified_hiring_need`; the input frame is never mutated.
    """

    if isinstance(ready_hires, bool) or int(ready_hires) != ready_hires or ready_hires < 0:
        raise ValueError("ready_hires must be a non-negative integer")
    if horizon <= 0:
        raise ValueError("horizon must be positive")
    if scenario not in _SCENARIO_SETTINGS:
        raise ValueError(f"Unknown scenario: {scenario}")
    if not 0 < target < 1:
        raise ValueError("target must be between zero and one")
    required = {
        "site_id",
        "current_ratio",
        "projected_qdlh",
        "projected_total_dlh",
        "ready_hire_hours",
        "qualified_hiring_need",
        "expected_ready_hires",
        "scenario",
        "horizon_days",
        "planning_target",
    }
    missing = required - set(forecasts.columns)
    if missing:
        raise ValueError(f"Forecast frame is missing columns: {sorted(missing)}")
    if forecasts.empty:
        result = forecasts.copy(deep=True)
        result["committed_ready_hires"] = pd.Series(dtype="int64")
        return result
    if not forecasts["scenario"].eq(scenario).all():
        raise ValueError("scenario does not match the forecast frame")
    if not pd.to_numeric(forecasts["horizon_days"], errors="coerce").eq(horizon).all():
        raise ValueError("horizon does not match the forecast frame")
    if not np.isclose(
        pd.to_numeric(forecasts["planning_target"], errors="coerce").to_numpy(dtype=float),
        target,
    ).all():
        raise ValueError("target does not match the forecast frame")

    result = forecasts.copy(deep=True)
    result["committed_ready_hires"] = 0
    remaining = int(ready_hires)
    needs = pd.to_numeric(result["qualified_hiring_need"], errors="coerce").fillna(0).clip(lower=0)
    priority = (
        result.assign(_need=needs)
        .sort_values(["_need", "projected_ratio", "site_id"], ascending=[False, True, True])
        .index
    )
    for index in priority:
        if remaining <= 0:
            break
        site_need = int(needs.loc[index])
        if site_need <= 0:
            continue
        assigned = min(site_need, remaining)
        result.at[index, "committed_ready_hires"] = assigned
        remaining -= assigned

    contribution = (
        pd.to_numeric(result["committed_ready_hires"], errors="coerce").fillna(0)
        * pd.to_numeric(result["ready_hire_hours"], errors="coerce").fillna(0.0)
    )
    result["projected_qdlh"] = result["projected_qdlh"] + contribution
    result["projected_total_dlh"] = result["projected_total_dlh"] + contribution
    result["projected_ratio"] = result.apply(
        lambda row: safe_ratio(row["projected_qdlh"], row["projected_total_dlh"]), axis=1
    )
    result["direction"] = result["projected_ratio"] - result["current_ratio"]

    updated_needs: list[int | None] = []
    updated_coverage: list[float | None] = []
    updated_statuses: list[str] = []
    for row in result.itertuples(index=False):
        need = qualified_hiring_need(
            row.projected_qdlh,
            row.projected_total_dlh,
            target,
            row.ready_hire_hours,
            row.ready_hire_hours,
        )
        updated_needs.append(need)
        coverage = None if need in {None, 0} else float(row.expected_ready_hires / need)
        updated_coverage.append(coverage)
        updated_statuses.append(_risk_status(row.projected_ratio, target, coverage, row.direction))
    result["qualified_hiring_need"] = updated_needs
    result["pipeline_coverage"] = updated_coverage
    result["risk_status"] = updated_statuses
    result["planning_simulation"] = True
    result["formula_version"] = FORECAST_VERSION
    return result


def _target_crossing_day(points: pd.DataFrame, target: float) -> float:
    """Estimate the first day the versioned portfolio course is below target."""

    ordered = points[["horizon_days", "portfolio_projected_ratio"]].drop_duplicates().sort_values("horizon_days")
    previous_day: float | None = None
    previous_ratio: float | None = None
    for row in ordered.itertuples(index=False):
        day = float(row.horizon_days)
        ratio = float(row.portfolio_projected_ratio)
        if ratio < target:
            if previous_day is None or previous_ratio is None or previous_ratio < target:
                return day
            change = previous_ratio - ratio
            if change <= 0:
                return day
            fraction = (previous_ratio - target) / change
            return previous_day + fraction * (day - previous_day)
        previous_day = day
        previous_ratio = ratio
    return float("nan")


def trajectory(data: DemoData, target: float, scenario: str) -> pd.DataFrame:
    """Compose site forecasts at the six executive-demo planning horizons."""

    frames: list[pd.DataFrame] = []
    for horizon in FORECAST_HORIZONS:
        frame = forecast_sites(data, target=target, horizon_days=horizon, scenario=scenario)
        frame["portfolio_projected_ratio"] = portfolio_summary(frame)["projected_ratio"]
        frames.append(frame)
    result = pd.concat(frames, ignore_index=True)
    result["target_crossing_day"] = _target_crossing_day(result, target)
    result["formula_version"] = FORECAST_VERSION
    return result


def _shrunk_rate(observed: float, n: int, prior: float, k: int = 20) -> float:
    if n <= 0 or np.isnan(observed):
        return prior
    return (n / (n + k)) * observed + (k / (n + k)) * prior


def source_performance(data: DemoData) -> pd.DataFrame:
    """Create mature-cohort partner metrics with small-sample shrinkage."""

    as_of = pd.Timestamp(DATA_AS_OF_DATE)
    maturity_cutoff = as_of - timedelta(days=90)
    cohort = data.applicants.loc[data.applicants["referral_date"] <= maturity_cutoff].copy()
    history_flags = (
        data.stage_history.assign(value=1)
        .pivot_table(index="applicant_id", columns="to_stage", values="value", aggfunc="max", fill_value=0)
        .reset_index()
    )
    for column in ["Applied", "Interviewed", "Hired"]:
        if column not in history_flags:
            history_flags[column] = 0
    cohort = cohort.merge(history_flags[["applicant_id", "Applied", "Interviewed", "Hired"]], on="applicant_id", how="left")
    cohort[["Applied", "Interviewed", "Hired"]] = cohort[["Applied", "Interviewed", "Hired"]].fillna(0)
    cohort["cleared"] = (cohort["eligibility_review_status"] == "Cleared").astype(int)
    cohort["docs_complete"] = cohort["documentation_status"].isin(["Complete", "Cleared"]).astype(int)
    cohort["mature_90"] = cohort["start_date"].notna() & (cohort["start_date"] <= maturity_cutoff)
    cohort["retained_90"] = ((cohort["retention_status"] == "Active-90+") & cohort["mature_90"]).astype(int)
    cohort["actual_expected_qdl_hours"] = np.where(
        cohort["qdl_count_status"] == "Mock Countable",
        cohort["expected_weekly_dlh"] * 13,
        0.0,
    )

    rows: list[dict] = []
    for organization_id, group in cohort.groupby("source_organization_id"):
        referrals = len(group)
        applied = int(group["Applied"].sum())
        interviewed = int(group["Interviewed"].sum())
        hired = int(group["Hired"].sum())
        started_group = group.loc[group["start_date"].notna()]
        mature_90_group = group.loc[group["mature_90"]]
        rows.append(
            {
                "organization_id": organization_id,
                "referral_volume": referrals,
                "application_conversion": safe_ratio(applied, referrals),
                "interview_conversion": safe_ratio(interviewed, applied),
                "hire_yield": safe_ratio(hired, referrals),
                "eligibility_clearance_yield": safe_ratio(float(started_group["cleared"].sum()), len(started_group)),
                "documentation_completion": safe_ratio(float(started_group["docs_complete"].sum()), len(started_group)),
                "median_days_to_clear": float(started_group["days_to_clear"].median()) if started_group["days_to_clear"].notna().any() else np.nan,
                "retention_90": safe_ratio(float(mature_90_group["retained_90"].sum()), len(mature_90_group)),
                "mature_90_count": len(mature_90_group),
                "expected_qdl_hours_produced": float(group["actual_expected_qdl_hours"].sum()),
            }
        )
    scores = pd.DataFrame(rows)
    if scores.empty:
        return scores

    rate_columns = [
        "hire_yield",
        "eligibility_clearance_yield",
        "documentation_completion",
        "retention_90",
    ]
    priors = {column: float(scores[column].dropna().mean()) for column in rate_columns}
    for column in rate_columns:
        count_column = "mature_90_count" if column == "retention_90" else "referral_volume"
        scores[f"adjusted_{column}"] = scores.apply(
            lambda row: _shrunk_rate(row[column], int(row[count_column]), priors[column]), axis=1
        )
    scores["referral_volume_score"] = np.log1p(scores["referral_volume"]).rank(pct=True) * 100.0
    target_days = 14.0
    scores["days_penalty"] = np.minimum(
        10.0,
        np.maximum(0.0, scores["median_days_to_clear"].fillna(target_days) - target_days) / target_days * 5.0,
    )
    scores["reliability_score"] = np.clip(
        0.35 * scores["adjusted_eligibility_clearance_yield"] * 100.0
        + 0.20 * scores["adjusted_hire_yield"] * 100.0
        + 0.20 * scores["adjusted_retention_90"] * 100.0
        + 0.15 * scores["adjusted_documentation_completion"] * 100.0
        + 0.10 * scores["referral_volume_score"]
        - scores["days_penalty"],
        0,
        100,
    )

    latest = data.labor_hours.loc[data.labor_hours["month_start"] == data.labor_hours["month_start"].max()]
    site_need = data.sites[["site_id", "county_id"]].merge(
        latest[["site_id", "current_ratio_pct"]], on="site_id", how="left"
    )
    site_need["site_need_score"] = np.clip((0.80 - site_need["current_ratio_pct"] / 100.0) / 0.15 * 100.0, 10, 100)
    coverage_need = data.coverage.merge(site_need[["county_id", "site_need_score"]], on="county_id", how="left")
    coverage_need = coverage_need.groupby("organization_id", as_index=False)["site_need_score"].max()
    job_fit = (
        data.org_job_families.assign(
            job_family_fit=lambda frame: frame["capability_level"].map(
                {"Potential": 45.0, "Claimed": 68.0, "Demonstrated": 90.0}
            )
        )
        .groupby("organization_id", as_index=False)["job_family_fit"]
        .mean()
    )
    scores = scores.merge(
        data.organizations[["organization_id", "organization_name", "organization_type", "relationship_status", "state_code"]],
        on="organization_id",
        how="left",
    ).merge(coverage_need, on="organization_id", how="left").merge(job_fit, on="organization_id", how="left")
    relationship_score = {
        "Unknown": 20,
        "Cold": 35,
        "Contacted": 55,
        "Warm": 72,
        "Active Partner": 88,
        "Strategic Partner": 100,
        "Dormant": 30,
        "Do Not Contact": 0,
    }
    scores["relationship_readiness"] = scores["relationship_status"].map(relationship_score).fillna(20.0)
    scores["site_need_score"] = scores["site_need_score"].fillna(35.0)
    scores["job_family_fit"] = scores["job_family_fit"].fillna(40.0)
    scores["partner_priority_score"] = np.clip(
        0.55 * scores["reliability_score"]
        + 0.20 * scores["site_need_score"]
        + 0.15 * scores["job_family_fit"]
        + 0.10 * scores["relationship_readiness"],
        0,
        100,
    )
    scores.loc[scores["relationship_status"] == "Do Not Contact", "partner_priority_score"] = 0.0
    scores["confidence_level"] = np.select(
        [scores["referral_volume"] >= 50, scores["referral_volume"] >= 20],
        ["High", "Medium"],
        default="Low",
    )
    scores["formula_version"] = PARTNER_SCORE_VERSION
    percentage_columns = [
        "application_conversion",
        "interview_conversion",
        "hire_yield",
        "eligibility_clearance_yield",
        "documentation_completion",
        "retention_90",
    ]
    for column in percentage_columns:
        scores[column] = scores[column] * 100.0
    return scores.sort_values("partner_priority_score", ascending=False).reset_index(drop=True)
