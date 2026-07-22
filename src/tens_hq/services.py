"""Action queues, safe outreach drafts, and manager-ready narrative outputs."""

from __future__ import annotations

import pandas as pd

from .constants import DATA_AS_OF_DATE
from .metrics import portfolio_summary
from .synthetic import DemoData


def build_outreach_queue(
    data: DemoData,
    source_scores: pd.DataFrame,
    forecasts: pd.DataFrame,
) -> pd.DataFrame:
    """Prioritize sources against site need while honoring Do Not Contact."""

    coverage_sites = data.coverage.merge(
        data.sites[["site_id", "site_name", "county_id"]], on="county_id", how="inner"
    ).merge(
        forecasts[["site_id", "risk_status", "qualified_hiring_need"]], on="site_id", how="inner"
    )
    risk_boost = {"Healthy": 0.0, "Watch": 7.0, "At Risk": 16.0, "Critical": 24.0}
    coverage_sites["risk_boost"] = coverage_sites["risk_status"].map(risk_boost).fillna(0.0)
    best_need = coverage_sites.sort_values("risk_boost", ascending=False).drop_duplicates("organization_id")
    queue = data.organizations.merge(
        source_scores[["organization_id", "partner_priority_score", "reliability_score", "confidence_level"]],
        on="organization_id",
        how="left",
    ).merge(
        best_need[
            ["organization_id", "site_id", "site_name", "risk_status", "qualified_hiring_need", "risk_boost"]
        ],
        on="organization_id",
        how="left",
    )
    as_of = pd.Timestamp(DATA_AS_OF_DATE)
    queue["days_overdue"] = (as_of - pd.to_datetime(queue["next_follow_up_date"])).dt.days.fillna(0).clip(lower=0)
    queue["partner_priority_score"] = queue["partner_priority_score"].fillna(35.0)
    queue["risk_boost"] = queue["risk_boost"].fillna(0.0)
    queue["queue_priority"] = (
        queue["partner_priority_score"] + queue["risk_boost"] + queue["days_overdue"].clip(upper=30) * 0.35
    ).clip(0, 120)
    queue = queue.loc[queue["relationship_status"] != "Do Not Contact"].copy()
    queue["suggested_next_action"] = queue.apply(
        lambda row: "Schedule role briefing"
        if row["relationship_status"] in {"Warm", "Active Partner", "Strategic Partner"}
        else "Send reviewed introduction draft"
        if row["relationship_status"] in {"Unknown", "Cold"}
        else "Complete scheduled follow-up",
        axis=1,
    )
    return queue.sort_values(["queue_priority", "days_overdue"], ascending=False).reset_index(drop=True)


def outreach_email_draft(
    organization_name: str,
    contact_name: str,
    site_name: str,
    job_family_name: str,
    relationship_status: str,
) -> tuple[str, str]:
    """Generate a non-sensitive draft only; no delivery capability exists."""

    first_name = contact_name.split()[0] if contact_name else "there"
    if relationship_status in {"Warm", "Active Partner", "Strategic Partner"}:
        subject = f"Follow-up: {site_name} role outlook and referral cadence"
        body = f"""Hello {first_name},

Thank you for the ongoing relationship with {organization_name}. Our current synthetic planning scenario shows a need to strengthen the {job_family_name.lower()} pipeline supporting {site_name}. I would like to confirm the best format for sharing role summaries and discuss whether a recurring referral check-in would be useful.

Could we schedule a 20-minute conversation next week? I can bring a short, non-sensitive overview of job families, expected timing, and referral steps.

Best,
ROCC Demo User (Synthetic)
"""
    else:
        subject = f"Exploring a local employment referral partnership for {site_name}"
        body = f"""Hello {first_name},

I support workforce outreach for {site_name}, a synthetic demonstration site used to show how a disability-inclusive federal-contracting employer might coordinate with community partners. We are mapping organizations that support candidates interested in {job_family_name.lower()} roles and would value a brief conversation about your referral process, service area, and preferred way to receive role information.

Would you be open to a 20-minute introductory call during the next two weeks? This is a demonstration draft and has not been sent.

Thank you,
ROCC Demo User (Synthetic)
"""
    return subject, body


def site_report_markdown(site_row: pd.Series) -> str:
    need = site_row["qualified_hiring_need"]
    need_text = "Assumptions cannot reach target" if pd.isna(need) else str(int(need))
    return f"""# {site_row['site_name']} — Synthetic Site Readiness Report

**PLANNING INDICATOR — NOT AN OFFICIAL ODLH COMPLIANCE DETERMINATION**

**Status:** {site_row['risk_status']}  
**Current planning ratio:** {site_row['current_ratio']:.1%}  
**Projected {int(site_row['horizon_days'])}-day ratio:** {site_row['projected_ratio']:.1%}  
**Qualified hiring need:** {need_text}  
**Pipeline candidates:** {int(site_row['pipeline_candidates'])}  
**Expected ready hires:** {site_row['expected_ready_hires']:.1f}

## Plain-English explanation

{site_row['explanation']}

## Required action

Assign an owner, confirm the forecast assumptions, and complete the recommended outreach action within 14 days when the site is At Risk or Critical.

## Decision boundary

This report uses synthetic facts and probability-weighted planning assumptions. It is not an official ODLH determination, employment decision, or compliance certification. Formula version: `{site_row['formula_version']}`.
"""


def leadership_summary_markdown(forecasts: pd.DataFrame, queue: pd.DataFrame) -> str:
    summary = portfolio_summary(forecasts)
    risk_sites = forecasts.loc[forecasts["risk_status"].isin(["At Risk", "Critical"])].nlargest(
        3, "qualified_hiring_need"
    )
    risks = "\n".join(
        f"- {row.site_name}: {row.risk_status}, projected {row.projected_ratio:.1%}, need {int(row.qualified_hiring_need or 0)}"
        for row in risk_sites.itertuples(index=False)
    ) or "- No At Risk or Critical sites in the selected scenario."
    actions = "\n".join(
        f"- {row.organization_name} → {row.site_name}: {row.suggested_next_action}"
        for row in queue.head(3).itertuples(index=False)
    )
    return f"""# ROCC Monthly Leadership Summary — Synthetic

**SYNTHETIC DEMO DATA — NOT FOR EMPLOYMENT OR COMPLIANCE DECISIONS**

The selected scenario projects an organization-wide planning ratio of **{summary['projected_ratio']:.1%}**. **{summary['at_risk_sites']}** sites are At Risk or Critical, with an estimated **{summary['qualified_hires_needed']}** additional ready hires across those planning scenarios.

## Priority site risks

{risks}

## Next three partner actions

{actions}

## Decision boundary

This is a synthetic manager summary. Site indicators are operational planning aids; official ODLH treatment requires authoritative records and approved compliance review.
"""
