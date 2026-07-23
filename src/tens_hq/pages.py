"""Streamlit page renderers for the ROCC manager workflow."""

from __future__ import annotations

from datetime import date, timedelta
import html

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from .constants import (
    COLUMN_LABELS,
    DATA_AS_OF_DATE,
    DEFAULT_SEED,
    DRAFT_BANNER,
    JOB_FAMILIES,
    PLANNING_BANNER,
    POLICY_FLOOR,
    RISK_COLORS,
    RISK_ORDER,
    SYNTHETIC_BANNER,
)
from .metrics import (
    FORECAST_HORIZONS,
    apply_hiring_plan,
    forecast_sites,
    pipeline_health,
    portfolio_summary,
    site_pipeline_stage_counts,
    source_performance,
    trajectory,
)
from .services import (
    build_outreach_queue,
    leadership_summary_markdown,
    outreach_email_draft,
    site_report_markdown,
)
from .synthetic import DemoData
from .validation import validate_demo_data


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root { --navy:#15324B; --teal:#167D7F; --slate:#52606D; --paper:#F4F6F8; }
        .stApp { background: #F4F6F8; }
        [data-testid="stSidebar"] { background: #15324B; color: white; }
        [data-testid="stSidebar"] * { color: #F7FAFC; }
        [data-testid="stSidebar"] div[role="radiogroup"] label {
            padding: .42rem .55rem; border-radius: .45rem; margin: .08rem 0;
        }
        [data-testid="stSidebar"] div[role="radiogroup"] label:hover { background:#234A68; }
        .sidebar-banner { font-size:.72rem; line-height:1.25; padding:.65rem; border:1px solid #4F718B;
            border-radius:.5rem; background:#1D405B; margin:.8rem 0 1rem; }
        .page-kicker { color:#167D7F; text-transform:uppercase; letter-spacing:.08em;
            font-size:.76rem; font-weight:700; margin-bottom:.2rem; }
        .page-title { color:#15324B; font-size:2.15rem; line-height:1.12; font-weight:750; margin:0; }
        .page-subtitle { color:#52606D; font-size:1rem; margin:.35rem 0 1rem; }
        .demo-banner, .planning-banner, .draft-banner { padding:.62rem .82rem; border-radius:.45rem;
            font-size:.78rem; font-weight:700; margin:.35rem 0 1rem; }
        .demo-banner { background:#E6F4F1; color:#115E59; border-left:4px solid #167D7F; }
        .planning-banner { background:#FFF7E6; color:#8A5A13; border-left:4px solid #B7791F; }
        .draft-banner { background:#EDF2F7; color:#334E68; border-left:4px solid #52606D; }
        .insight-box { background:white; border:1px solid #D9E2EC; border-left:5px solid #167D7F;
            padding:1rem 1.1rem; border-radius:.55rem; margin:.6rem 0 1rem; color:#243B53; }
        .risk-badge { display:inline-block; color:white; font-size:.78rem; font-weight:750;
            padding:.28rem .6rem; border-radius:1rem; }
        div[data-testid="stMetric"] { background:white; border:1px solid #D9E2EC;
            padding:.8rem .9rem; border-radius:.6rem; min-height:112px; }
        div[data-testid="stMetricLabel"] { color:#52606D; }
        div[data-testid="stDataFrame"] { border:1px solid #D9E2EC; border-radius:.5rem; }
        .small-note { color:#627D98; font-size:.82rem; }
        h2, h3 { color:#15324B; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _page_header(title: str, subtitle: str, kicker: str) -> None:
    st.markdown(f'<div class="page-kicker">{html.escape(kicker)}</div>', unsafe_allow_html=True)
    st.markdown(f'<h1 class="page-title">{html.escape(title)}</h1>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-subtitle">{html.escape(subtitle)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="demo-banner">{SYNTHETIC_BANNER}</div>', unsafe_allow_html=True)


def _planning_banner() -> None:
    st.markdown(f'<div class="planning-banner">{PLANNING_BANNER}</div>', unsafe_allow_html=True)


def _risk_badge(status: str) -> str:
    color = RISK_COLORS.get(status, RISK_COLORS["Unknown"])
    return f'<span class="risk-badge" style="background:{color}">{html.escape(status)}</span>'


def _plot_layout(fig: go.Figure, height: int = 430) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#243B53"),
        legend_title_text="",
    )
    fig.update_xaxes(gridcolor="#E8EDF2")
    fig.update_yaxes(gridcolor="#E8EDF2")
    return fig


def _format_percent_frame(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    result = frame.copy()
    for column in columns:
        result[column] = result[column].map(lambda value: "—" if pd.isna(value) else f"{value:.1%}")
    return result


def _label_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Rename raw metric-layer columns to friendly headers for display only."""
    return frame.rename(columns=COLUMN_LABELS)


@st.cache_data(show_spinner=False, hash_funcs={DemoData: lambda _: "synthetic-demo-data"})
def _cached_forecast_sites(
    data: DemoData,
    seed: int,
    target: float,
    scenario: str,
    horizon: int,
) -> pd.DataFrame:
    """Cache the metric-layer forecast by its complete deterministic inputs."""

    del seed
    return forecast_sites(data, target=target, horizon_days=horizon, scenario=scenario)


@st.cache_data(show_spinner=False, hash_funcs={DemoData: lambda _: "synthetic-demo-data"})
def _cached_source_performance(data: DemoData, seed: int) -> pd.DataFrame:
    """Cache source metrics by the deterministic demo-data seed."""

    del seed
    return source_performance(data)


@st.cache_data(show_spinner=False, hash_funcs={DemoData: lambda _: "synthetic-demo-data"})
def _cached_trajectory(
    data: DemoData,
    seed: int,
    target: float,
    scenario: str,
) -> pd.DataFrame:
    """Cache the six-horizon SYN-FORECAST-1.1 trajectory."""

    del seed
    return trajectory(data, target=target, scenario=scenario)


def render_home(data: DemoData, target: float, scenario: str) -> None:
    _page_header(
        "Executive Command Brief",
        "The current synthetic portfolio course, the quantified target gap, and the action leadership can test now.",
        "Home / Executive",
    )
    _planning_banner()
    forecasts = _cached_forecast_sites(data, DEFAULT_SEED, target, scenario, 90)
    summary = portfolio_summary(forecasts)
    scores = _cached_source_performance(data, DEFAULT_SEED)

    impact = st.columns(4)
    impact[0].metric(
        "90-day planning indicator",
        f"{summary['projected_ratio']:.1%}",
        delta=f"Target {summary['planning_target']:.1%}",
        help="SYN-FORECAST-1.1: sum of projected QDLH divided by sum of projected total DLH.",
    )
    above_target = summary["ratio_gap_points"] < 0  # ratio_gap_points>0 means BELOW target
    gap_direction = "above" if above_target else "below"
    surplus_or_shortfall = "surplus" if summary["hours_gap"] < 0 else "shortfall"
    impact[1].metric(
        "Gap to target",
        f"{abs(summary['ratio_gap_points']):.1f} pts {gap_direction}",
        delta=f"{abs(summary['hours_gap']):,.0f} hrs {surplus_or_shortfall}",
        delta_color="off",
        help="SYN-FORECAST-1.1: target × summed projected DLH − summed projected QDLH. Positive = shortfall (need more qualifying hours); negative = surplus.",
    )
    impact[2].metric(
        "Ready hires needed",
        summary["qualified_hires_needed"],
        help="Additional fully-qualifying ready hires to reach the planning target across at-risk sites.",
    )
    impact[3].metric("At Risk / Critical sites", summary["at_risk_sites"])

    st.markdown("### Test a leadership commitment")
    ready_hires = st.slider(
        "Ready hires we can commit",
        min_value=0,
        max_value=max(1, summary["qualified_hires_needed"]),
        value=0,
        help="Allocates ready hires to the highest-need sites using the same numerator/denominator contribution as qualified hiring need.",
    )
    st.caption("Planning simulation — SYN-FORECAST-1.1 (synthetic)")
    simulated = apply_hiring_plan(forecasts, ready_hires, target, 90, scenario)
    simulated_summary = portfolio_summary(simulated)
    simulated_queue = build_outreach_queue(data, scores, simulated)

    simulation_badges = st.columns(3)
    simulation_badges[0].metric(
        "Simulated 90-day portfolio",
        f"{simulated_summary['projected_ratio']:.1%}",
    )
    simulation_badges[1].metric("Remaining ready hires needed", simulated_summary["qualified_hires_needed"])
    simulation_badges[2].metric("Simulated At Risk / Critical", simulated_summary["at_risk_sites"])

    selected_course = _cached_trajectory(data, DEFAULT_SEED, target, scenario)
    conservative_course = _cached_trajectory(data, DEFAULT_SEED, target, "Conservative")
    optimistic_course = _cached_trajectory(data, DEFAULT_SEED, target, "Optimistic")
    selected_points = selected_course.drop_duplicates("horizon_days").sort_values("horizon_days")
    conservative_points = conservative_course.drop_duplicates("horizon_days").sort_values("horizon_days")
    optimistic_points = optimistic_course.drop_duplicates("horizon_days").sort_values("horizon_days")
    simulated_points: list[dict[str, float | int]] = []
    for horizon in FORECAST_HORIZONS:
        horizon_forecast = selected_course.loc[selected_course["horizon_days"] == horizon]
        horizon_plan = apply_hiring_plan(horizon_forecast, ready_hires, target, horizon, scenario)
        horizon_summary = portfolio_summary(horizon_plan)
        simulated_points.append(
            {"horizon_days": horizon, "projected_ratio": horizon_summary["projected_ratio"]}
        )
    simulated_course = pd.DataFrame(simulated_points)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=optimistic_points["horizon_days"],
            y=optimistic_points["portfolio_projected_ratio"],
            mode="lines",
            line={"width": 0},
            hoverinfo="skip",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=conservative_points["horizon_days"],
            y=conservative_points["portfolio_projected_ratio"],
            mode="lines",
            fill="tonexty",
            fillcolor="rgba(22,125,127,0.16)",
            line={"width": 0},
            name="Conservative–optimistic fan",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=selected_points["horizon_days"],
            y=selected_points["portfolio_projected_ratio"],
            mode="lines+markers",
            line={"color": "#15324B", "width": 3},
            name=f"{scenario} current course",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=simulated_course["horizon_days"],
            y=simulated_course["projected_ratio"],
            mode="lines+markers",
            line={"color": "#167D7F", "width": 3, "dash": "dash"},
            name=f"With {ready_hires} committed ready hires",
        )
    )
    fig.add_hline(y=target, line_dash="dot", line_color="#9B2C2C", annotation_text=f"Target {target:.1%}")
    crossing_day = selected_points["target_crossing_day"].iloc[0]
    if pd.notna(crossing_day):
        fig.add_annotation(
            x=float(crossing_day),
            y=target,
            text=f"~Day {crossing_day:.0f}: current course below target",
            showarrow=True,
            arrowcolor="#9B2C2C",
        )
    else:
        fig.add_annotation(
            x=180,
            y=target,
            text="Current course does not cross below target through day 180",
            showarrow=False,
            yshift=28,
        )
    fig.update_layout(title="Portfolio trajectory and live commitment simulation", hovermode="x unified")
    fig.update_xaxes(title="Planning horizon (days)", tickvals=list(FORECAST_HORIZONS))
    fig.update_yaxes(title="Portfolio planning indicator", tickformat=".1%")
    st.plotly_chart(_plot_layout(fig, 470), use_container_width=True)

    badge_table = simulated[
        ["site_name", "committed_ready_hires", "projected_ratio", "risk_status"]
    ].copy()
    badge_table["projected_ratio"] = badge_table["projected_ratio"].map(lambda value: f"{value:.1%}")
    st.dataframe(
        badge_table.rename(
            columns={
                "site_name": "Synthetic site",
                "committed_ready_hires": "Committed ready hires",
                "projected_ratio": "Projected planning indicator",
                "risk_status": "Simulated risk",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

    briefing = leadership_summary_markdown(simulated, simulated_queue)
    briefing_blocks = [block for block in briefing.split("\n\n") if block.strip()]
    briefing_paragraph = next(
        (block for block in briefing_blocks if block.startswith("The selected scenario")),
        briefing_blocks[0],
    )
    st.markdown("### Auto-briefing")
    st.markdown(briefing_paragraph)
    st.download_button(
        "Download leadership brief as Markdown",
        data=briefing,
        file_name="ROCC_Synthetic_Executive_Command_Brief.md",
        mime="text/markdown",
    )


def render_site_readiness(data: DemoData, target: float, scenario: str) -> None:
    _page_header(
        "Site Readiness",
        "Trace a site-level planning risk to labor hours, attrition assumptions, pipeline coverage, and partner actions.",
        "Operations / Site",
    )
    _planning_banner()
    forecasts90 = _cached_forecast_sites(data, DEFAULT_SEED, target, scenario, 90)
    forecasts180 = _cached_forecast_sites(data, DEFAULT_SEED, target, scenario, 180)
    selected_name = st.selectbox("Select synthetic site", forecasts90["site_name"].tolist())
    row90 = forecasts90.loc[forecasts90["site_name"] == selected_name].iloc[0]
    row180 = forecasts180.loc[forecasts180["site_name"] == selected_name].iloc[0]
    site_id = row90["site_id"]

    st.markdown(f"### {selected_name} &nbsp; {_risk_badge(row90['risk_status'])}", unsafe_allow_html=True)
    cols = st.columns(6)
    cols[0].metric("Current indicator", f"{row90['current_ratio']:.1%}")
    cols[1].metric("90-day", f"{row90['projected_ratio']:.1%}", f"{row90['direction']:+.1%}")
    cols[2].metric("180-day", f"{row180['projected_ratio']:.1%}")
    cols[3].metric("Open roles", int(row90["open_roles_count"]))
    cols[4].metric("Ready hires still needed", int(row90["qualified_hiring_need"] or 0))
    cols[5].metric("Projected pipeline arrivals", f"{row90['expected_ready_hires']:.1f}")
    st.markdown(f'<div class="insight-box">{html.escape(row90["explanation"])}</div>', unsafe_allow_html=True)
    _cov = row90["pipeline_coverage"]
    _cov_txt = "n/a" if pd.isna(_cov) else f"{_cov:.2f}x"
    st.caption(
        f"Coverage = projected arrivals / ready hires still needed = {_cov_txt}. "
        "A site can project more arrivals than it still needs and remain At Risk: "
        "projected arrivals are already inside the projected indicator, while "
        "'still needed' is the residual gap after them."
    )

    left, right = st.columns([1.35, 1])
    with left:
        history = data.labor_hours.loc[data.labor_hours["site_id"] == site_id].copy()
        fig = px.line(
            history,
            x="month_start",
            y="current_ratio_pct",
            markers=True,
            title="24-month synthetic site ratio history",
        )
        fig.update_traces(line_color="#167D7F")
        fig.add_hline(y=target * 100, line_dash="dash", line_color="#9B2C2C", annotation_text=f"Target {target:.0%}")
        fig.update_yaxes(ticksuffix="%")
        st.plotly_chart(_plot_layout(fig, 390), use_container_width=True)
    with right:
        bridge = pd.DataFrame(
            {
                "driver": ["Baseline QDLH", "Pipeline QDLH", "Attrition QDLH", "Projected QDLH"],
                "value": [
                    row90["projected_qdlh"] - row90["expected_qdl_hours"] + row90["attrition_qdl_hours"],
                    row90["expected_qdl_hours"],
                    -row90["attrition_qdl_hours"],
                    row90["projected_qdlh"],
                ],
                "measure": ["absolute", "relative", "relative", "total"],
            }
        )
        fig = go.Figure(
            go.Waterfall(
                x=bridge["driver"],
                y=bridge["value"],
                measure=bridge["measure"],
                connector={"line": {"color": "#9FB3C8"}},
                increasing={"marker": {"color": "#167D7F"}},
                decreasing={"marker": {"color": "#C05640"}},
                totals={"marker": {"color": "#15324B"}},
            )
        )
        fig.update_layout(title="90-day QDL-hour bridge")
        st.plotly_chart(_plot_layout(fig, 390), use_container_width=True)

    left, right = st.columns(2)
    with left:
        pipeline = site_pipeline_stage_counts(data, site_id)
        fig = px.bar(pipeline, x="candidates", y="stage", orientation="h", title="Synthetic pipeline by stage")
        fig.update_traces(marker_color="#167D7F")
        st.plotly_chart(_plot_layout(fig, 420), use_container_width=True)
    with right:
        scores = _cached_source_performance(data, DEFAULT_SEED)
        county_id = data.sites.loc[data.sites["site_id"] == site_id, "county_id"].iloc[0]
        covering = data.coverage.loc[data.coverage["county_id"] == county_id, "organization_id"]
        recommended = scores.loc[scores["organization_id"].isin(covering)].nlargest(5, "partner_priority_score")
        st.markdown("#### Recommended partner actions")
        if recommended.empty:
            st.info("No scored source covers this fictional county; validate the resource inventory.")
        else:
            st.dataframe(
                _label_columns(
                    recommended[
                        ["organization_name", "relationship_status", "partner_priority_score", "confidence_level"]
                    ].round({"partner_priority_score": 1})
                ),
                hide_index=True,
                use_container_width=True,
            )
        st.markdown("#### Manager action plan")
        st.markdown(
            "1. Confirm the assumption set and latest labor close.\n"
            "2. Assign the top three partner contacts to an owner.\n"
            "3. Complete a 14-day outreach sprint for At Risk/Critical sites.\n"
            "4. Re-run the forecast after the next pipeline review."
        )


def render_resource_network(data: DemoData, target: float, scenario: str) -> None:
    del target, scenario
    _page_header(
        "Resource Network",
        "Explore the fictional community organizations that cover each geography, job family, and relationship stage.",
        "Recruiting / Ecosystem",
    )
    filters = st.columns(3)
    state = filters[0].selectbox("State", ["All"] + sorted(data.organizations["state_code"].unique().tolist()))
    org_type = filters[1].selectbox("Organization type", ["All"] + sorted(data.organizations["organization_type"].unique().tolist()))
    relationship = filters[2].selectbox("Relationship", ["All"] + data.organizations["relationship_status"].drop_duplicates().tolist())
    filtered = data.organizations.copy()
    if state != "All":
        filtered = filtered.loc[filtered["state_code"] == state]
    if org_type != "All":
        filtered = filtered.loc[filtered["organization_type"] == org_type]
    if relationship != "All":
        filtered = filtered.loc[filtered["relationship_status"] == relationship]

    cols = st.columns(4)
    cols[0].metric("Organizations", len(filtered))
    cols[1].metric("Warm or stronger", int(filtered["relationship_status"].isin(["Warm", "Active Partner", "Strategic Partner"]).sum()))
    covered = data.coverage.loc[data.coverage["organization_id"].isin(filtered["organization_id"]), "county_id"].nunique()
    cols[2].metric("Counties covered", covered)
    due = int((pd.to_datetime(filtered["next_follow_up_date"]) <= pd.Timestamp(DATA_AS_OF_DATE)).sum())
    cols[3].metric("Follow-ups due", due)

    if filtered.empty:
        st.info("No organizations match these filters. Adjust the State, Organization type, or Relationship filter to see the network.")
        return

    left, right = st.columns([1.25, 1])
    with left:
        counts = filtered.groupby(["organization_type", "relationship_status"], as_index=False).size()
        fig = px.bar(
            counts,
            x="size",
            y="organization_type",
            color="relationship_status",
            orientation="h",
            title="Resource network by type and relationship",
        )
        st.plotly_chart(_plot_layout(fig, 460), use_container_width=True)
    with right:
        st.markdown("#### Filtered directory")
        st.dataframe(
            _label_columns(
                filtered[
                    ["organization_name", "organization_type", "county_name", "state_code", "relationship_status", "next_follow_up_date"]
                ]
            ),
            hide_index=True,
            use_container_width=True,
            height=410,
        )

    if not filtered.empty:
        selected_org = st.selectbox("Open organization detail", filtered["organization_name"].tolist())
        organization = filtered.loc[filtered["organization_name"] == selected_org].iloc[0]
        org_id = organization["organization_id"]
        detail_cols = st.columns(3)
        detail_cols[0].markdown(f"**Type**  \n{organization['organization_type']}")
        detail_cols[1].markdown(f"**Relationship**  \n{organization['relationship_status']}")
        detail_cols[2].markdown(f"**Next follow-up**  \n{organization['next_follow_up_date']:%Y-%m-%d}" if pd.notna(organization['next_follow_up_date']) else "**Next follow-up**  \nNot scheduled")
        coverage_detail = data.coverage.loc[data.coverage["organization_id"] == org_id].merge(
            data.counties[["county_id", "county_name", "state_code"]], on="county_id"
        )
        capabilities = data.org_job_families.loc[data.org_job_families["organization_id"] == org_id].copy()
        capabilities["job_family"] = capabilities["job_family_code"].map(lambda code: JOB_FAMILIES[code][0])
        contacts = data.contacts.loc[data.contacts["organization_id"] == org_id]
        tab_names = ["Coverage", "Job families", "Business contacts", "Outreach history"]
        tabs = dict(zip(tab_names, st.tabs(tab_names)))
        tabs["Coverage"].dataframe(_label_columns(coverage_detail[["county_name", "state_code", "coverage_strength", "verified_status"]]), hide_index=True, use_container_width=True)
        tabs["Job families"].dataframe(_label_columns(capabilities[["job_family", "capability_level", "evidence_source"]]), hide_index=True, use_container_width=True)
        tabs["Business contacts"].dataframe(_label_columns(contacts[["contact_name", "contact_title", "contact_email", "preferred_channel"]]), hide_index=True, use_container_width=True)
        activities = data.outreach.loc[data.outreach["organization_id"] == org_id].sort_values("activity_date", ascending=False)
        tabs["Outreach history"].dataframe(_label_columns(activities[["activity_date", "outreach_type", "outcome_code", "next_follow_up_date"]].head(20)), hide_index=True, use_container_width=True)


def render_outreach(data: DemoData, target: float, scenario: str) -> None:
    _page_header(
        "Outreach Command Center",
        "Who should we contact next, why should we contact them, and what should we say?",
        "Recruiting / Action Queue",
    )
    st.markdown(f'<div class="draft-banner">{DRAFT_BANNER} · ROCC has no email sending capability.</div>', unsafe_allow_html=True)
    forecasts = _cached_forecast_sites(data, DEFAULT_SEED, target, scenario, 90)
    scores = _cached_source_performance(data, DEFAULT_SEED)
    queue = build_outreach_queue(data, scores, forecasts)

    cols = st.columns(4)
    cols[0].metric("Open queue", len(queue))
    cols[1].metric("Due / overdue", int((pd.to_datetime(queue["next_follow_up_date"]) <= pd.Timestamp(DATA_AS_OF_DATE)).sum()))
    cols[2].metric("At-risk site actions", int(queue["risk_status"].isin(["At Risk", "Critical"]).sum()))
    cols[3].metric("Warm or stronger", int(queue["relationship_status"].isin(["Warm", "Active Partner", "Strategic Partner"]).sum()))

    st.markdown("### Prioritized outreach queue")
    queue_view = queue[
        [
            "organization_name",
            "organization_type",
            "relationship_status",
            "site_name",
            "risk_status",
            "days_overdue",
            "partner_priority_score",
            "suggested_next_action",
        ]
    ].head(100).copy()
    queue_view["partner_priority_score"] = queue_view["partner_priority_score"].round(1)
    st.dataframe(queue_view, hide_index=True, use_container_width=True, height=360)

    st.markdown("### Draft generator")
    draft_cols = st.columns(2)
    selected_org_name = draft_cols[0].selectbox("Organization", queue["organization_name"].head(100).tolist())
    selected_queue = queue.loc[queue["organization_name"] == selected_org_name].iloc[0]
    org_id = selected_queue["organization_id"]
    contacts = data.contacts.loc[data.contacts["organization_id"] == org_id]
    selected_contact_name = draft_cols[1].selectbox("Synthetic business contact", contacts["contact_name"].tolist())
    site_options = data.sites["site_name"].tolist()
    default_site = selected_queue["site_name"] if pd.notna(selected_queue["site_name"]) else site_options[0]
    draft_cols2 = st.columns(2)
    selected_site_name = draft_cols2[0].selectbox("Site supported", site_options, index=site_options.index(default_site))
    selected_site = data.sites.loc[data.sites["site_name"] == selected_site_name].iloc[0]
    job_family_name = JOB_FAMILIES[selected_site["job_family_code"]][0]
    draft_cols2[1].text_input("Job family", value=job_family_name, disabled=True)

    subject, body = outreach_email_draft(
        selected_org_name,
        selected_contact_name,
        selected_site_name,
        job_family_name,
        selected_queue["relationship_status"],
    )
    st.text_input("Draft subject", value=subject, disabled=True)
    st.text_area("Draft message", value=body, height=300, disabled=True)
    st.caption("Review through approved organizational channels. The demo intentionally provides no Send button and stores no real contact data.")

    with st.expander("Call and voicemail scripts"):
        st.markdown(
            f"**Call script**\n\nHello, this is the ROCC demo user with {selected_site_name}. "
            f"I’m calling to learn how {selected_org_name} works with local employers and whether our {job_family_name.lower()} role family may fit your referral process. "
            "I’m not requesting medical or disability information. May we schedule a 20-minute conversation?"
        )
        st.markdown(
            "**Voicemail**\n\nHello, this is the ROCC demo user. I’m reaching out to learn about your employment referral process and explore a possible community partnership for upcoming openings. "
            "No sensitive applicant information is needed. This is a synthetic demonstration message and has not been sent."
        )


def render_applicant_pipeline(data: DemoData, target: float, scenario: str) -> None:
    """Render applicant-side pipeline health as aggregate outputs only."""

    del target, scenario
    _page_header(
        "Pipeline Health",
        "Portfolio-level movement, stage timing, and referral-source mix from synthetic aggregation inputs.",
        "Recruiting / Aggregate View",
    )
    st.caption(
        "applicants are never listed or scored here — aggregate pipeline health only; "
        "synthetic partner-org contacts appear only in the outreach workflow and are never scored."
    )

    funnel, stage_age, source_mix = pipeline_health(data)
    funnel_counts = funnel.set_index("Stage")["Reached stage"]
    cols = st.columns(4)
    cols[0].metric("Synthetic referrals", int(funnel_counts.get("Referred", 0)))
    cols[1].metric("Reached application", int(funnel_counts.get("Applied", 0)))
    cols[2].metric("Reached hire", int(funnel_counts.get("Hired", 0)))
    cols[3].metric("Referral sources", len(source_mix))

    st.markdown("### Stage funnel and conversion")
    fig = px.bar(
        funnel,
        x="Reached stage",
        y="Stage",
        orientation="h",
        text="Reached stage",
        hover_data={"Conversion from prior stage": ":.1%"},
        title="Synthetic stage funnel",
    )
    fig.update_traces(marker_color="#167D7F")
    fig.update_yaxes(
        categoryorder="array",
        categoryarray=list(reversed(funnel["Stage"].tolist())),
    )
    st.plotly_chart(_plot_layout(fig, 420), use_container_width=True)
    funnel_display = funnel.copy()
    funnel_display["Conversion from prior stage"] = funnel_display[
        "Conversion from prior stage"
    ].map(lambda value: "Entry" if pd.isna(value) else f"{value:.1%}")
    st.dataframe(funnel_display, hide_index=True, use_container_width=True)

    stage_col, source_col = st.columns(2)
    with stage_col:
        st.markdown("### Median time in current stage")
        st.dataframe(
            stage_age,
            hide_index=True,
            use_container_width=True,
            height=430,
        )
    with source_col:
        st.markdown("### Referral-source mix")
        source_display = _format_percent_frame(source_mix, ["Portfolio share"])
        st.dataframe(
            source_display,
            hide_index=True,
            use_container_width=True,
            height=430,
        )
    st.caption(
        "All values are synthetic portfolio aggregates. Stage and source measures describe process performance, never a person."
    )


def render_source_performance(data: DemoData, target: float, scenario: str) -> None:
    del target, scenario
    _page_header(
        "Source Performance",
        "Which organizations create the most workforce-readiness value—not merely the most referrals?",
        "Intelligence / Attribution",
    )
    scores = _cached_source_performance(data, DEFAULT_SEED)
    cols = st.columns(4)
    cols[0].metric("Scored sources", len(scores))
    cols[1].metric("High-confidence sources", int(scores["confidence_level"].eq("High").sum()))
    cols[2].metric("Mature referrals", int(scores["referral_volume"].sum()))
    cols[3].metric("Expected QDL hours attributed", f"{scores['expected_qdl_hours_produced'].sum():,.0f}")

    fig = px.scatter(
        scores,
        x="referral_volume",
        y="reliability_score",
        size="expected_qdl_hours_produced",
        color="confidence_level",
        hover_name="organization_name",
        hover_data=["organization_type", "hire_yield", "retention_90", "partner_priority_score"],
        title="Referral volume vs. adjusted source reliability",
        color_discrete_map={"High": "#167D7F", "Medium": "#B7791F", "Low": "#8AA4B8"},
        log_x=True,
    )
    fig.update_yaxes(range=[0, 100])
    st.plotly_chart(_plot_layout(fig, 500), use_container_width=True)

    display = scores[
        [
            "organization_name",
            "organization_type",
            "relationship_status",
            "referral_volume",
            "hire_yield",
            "eligibility_clearance_yield",
            "documentation_completion",
            "retention_90",
            "reliability_score",
            "partner_priority_score",
            "confidence_level",
        ]
    ].copy()
    display = display.round(1)
    st.dataframe(_label_columns(display), hide_index=True, use_container_width=True, height=350)

    selected = st.selectbox("Open source detail", scores["organization_name"].tolist())
    row = scores.loc[scores["organization_name"] == selected].iloc[0]
    st.markdown(f"### {selected}")
    detail_cols = st.columns(5)
    detail_cols[0].metric("Referrals", int(row["referral_volume"]))
    detail_cols[1].metric("Hire yield", f"{row['hire_yield']:.1f}%")
    detail_cols[2].metric("90-day retention", "—" if pd.isna(row["retention_90"]) else f"{row['retention_90']:.1f}%")
    detail_cols[3].metric("Reliability", f"{row['reliability_score']:.1f}")
    detail_cols[4].metric("Confidence", row["confidence_level"])
    st.markdown(
        f'<div class="insight-box"><strong>Interpretation:</strong> {html.escape(selected)} has an adjusted reliability score of '
        f'{row["reliability_score"]:.1f} based on {int(row["referral_volume"])} mature referrals. '
        f'The partner priority is {row["partner_priority_score"]:.1f} after current site need, job-family fit, and relationship readiness are included.</div>',
        unsafe_allow_html=True,
    )
    with st.expander("Formula and small-sample protection"):
        st.code(
            "Reliability = 35% adjusted clearance + 20% adjusted hire yield\n"
            "            + 20% adjusted 90-day retention + 15% adjusted documentation completion\n"
            "            + 10% volume score - days-to-clear penalty\n\n"
            "Adjusted rate = n/(n+20) × observed + 20/(n+20) × peer prior",
            language="text",
        )
        st.caption(f"Formula version: {row['formula_version']}. Scores apply to sources and operations, never to individuals.")


def render_ratio_forecast(data: DemoData, target: float, scenario: str) -> None:
    _page_header(
        "Ratio Forecast",
        "Explore organization and site planning scenarios with transparent numerator, denominator, pipeline, and attrition assumptions.",
        "Compliance-Aware Operations / Scenario",
    )
    _planning_banner()
    controls = st.columns(3)
    horizon = controls[0].selectbox("Forecast horizon", [90, 180], format_func=lambda value: f"{value} days")
    controls[1].text_input("Selected scenario", value=scenario, disabled=True)
    controls[2].text_input("Planning target", value=f"{target:.1%}", disabled=True)

    forecasts = _cached_forecast_sites(data, DEFAULT_SEED, target, scenario, horizon)
    summary = portfolio_summary(forecasts)
    cols = st.columns(4)
    cols[0].metric("Portfolio scenario", f"{summary['projected_ratio']:.1%}")
    cols[1].metric(
        "Planning floor (internal)",
        f"{POLICY_FLOOR:.1%}",
        help="Synthetic internal early-warning floor for this demo - NOT a statutory figure. The AbilityOne requirement is the 75% direct-labor-hours ratio.",
    )
    cols[2].metric("At Risk / Critical", summary["at_risk_sites"])
    cols[3].metric("Ready hires still needed", summary["qualified_hires_needed"])
    st.caption(f"Formula version: {forecasts['formula_version'].iloc[0]} - synthetic planning model")

    comparison = forecasts[["site_name", "current_ratio", "projected_ratio", "risk_status"]].melt(
        id_vars=["site_name", "risk_status"],
        value_vars=["current_ratio", "projected_ratio"],
        var_name="series",
        value_name="ratio",
    )
    comparison["series"] = comparison["series"].map({"current_ratio": "Current", "projected_ratio": f"Projected {horizon}-day"})
    fig = px.bar(
        comparison,
        x="site_name",
        y="ratio",
        color="series",
        barmode="group",
        title="Site planning indicators",
        color_discrete_map={"Current": "#8AA4B8", f"Projected {horizon}-day": "#167D7F"},
    )
    fig.add_hline(y=target, line_dash="dash", line_color="#9B2C2C", annotation_text=f"Target {target:.0%}")
    fig.update_yaxes(tickformat=".0%", range=[0.60, 0.86])
    st.plotly_chart(_plot_layout(fig, 500), use_container_width=True)

    table = forecasts[
        [
            "site_name",
            "current_ratio",
            "projected_ratio",
            "direction",
            "expected_attrition_fte",
            "pipeline_candidates",
            "expected_ready_hires",
            "qualified_hiring_need",
            "pipeline_coverage",
            "risk_status",
        ]
    ].copy()
    table = _format_percent_frame(table, ["current_ratio", "projected_ratio", "direction"])
    table["expected_ready_hires"] = table["expected_ready_hires"].round(1)
    table["pipeline_coverage"] = table["pipeline_coverage"].map(lambda value: "N/A" if pd.isna(value) else f"{value:.2f}")
    st.dataframe(_label_columns(table), hide_index=True, use_container_width=True)
    st.caption(
        "'Projected pipeline arrivals' are already included in the projected indicator; "
        "'Ready hires still needed' is the residual gap after them, so a site can show "
        "more arrivals than needed and still be At Risk. Coverage = arrivals / need."
    )

    st.markdown("### Scenario sensitivity")
    scenario_frames = []
    for scenario_name in ["Conservative", "Base", "Optimistic"]:
        frame = _cached_forecast_sites(data, DEFAULT_SEED, target, scenario_name, horizon)
        rollup = portfolio_summary(frame)
        scenario_frames.append(
            {
                "scenario": scenario_name,
                "portfolio_ratio": rollup["projected_ratio"],
                "at_risk_sites": rollup["at_risk_sites"],
                "qualified_hires_needed": rollup["qualified_hires_needed"],
            }
        )
    sensitivity = pd.DataFrame(scenario_frames)
    fig = px.bar(
        sensitivity,
        x="scenario",
        y="portfolio_ratio",
        color="scenario",
        text=sensitivity["portfolio_ratio"].map(lambda value: f"{value:.1%}"),
        color_discrete_map={"Conservative": "#C05640", "Base": "#167D7F", "Optimistic": "#8AA4B8"},
        title="Portfolio scenario range",
    )
    fig.add_hline(y=target, line_dash="dash", line_color="#9B2C2C")
    fig.update_yaxes(tickformat=".0%", range=[0.60, 0.86])
    st.plotly_chart(_plot_layout(fig, 360), use_container_width=True)

    with st.expander("Forecast formulas and important edge cases"):
        st.code(
            "Projected QDLH = baseline QDLH + expected pipeline QDLH - expected attrition QDLH\n"
            "Projected DLH  = baseline DLH  + expected pipeline DLH  - expected attrition DLH\n"
            "Projected ratio = Projected QDLH / Projected DLH\n\n"
            "Additional ready hires = ceil(max(0, target × D - Q) / (Hq - target × Hd))",
            language="text",
        )
        st.markdown(
            "- Started people are excluded from expected pipeline hours to prevent actual/expected double counting.\n"
            "- Site percentages are never averaged; the portfolio rolls up summed numerator and denominator.\n"
            "- A zero denominator displays Not Applicable.\n"
            "- If a hire assumption cannot mathematically reach the target, the app returns an assumption error instead of a number."
        )


def render_reports(data: DemoData, target: float, scenario: str) -> None:
    _page_header(
        "Reports",
        "Generate readable, versioned management outputs from the same synthetic metric contract as the dashboards.",
        "Management / Outputs",
    )
    st.markdown(f'<div class="draft-banner">{DRAFT_BANNER}</div>', unsafe_allow_html=True)
    forecasts = _cached_forecast_sites(data, DEFAULT_SEED, target, scenario, 90)
    scores = _cached_source_performance(data, DEFAULT_SEED)
    queue = build_outreach_queue(data, scores, forecasts)
    report_type = st.selectbox(
        "Report type",
        ["Monthly leadership summary", "Site readiness report", "Partner priority list", "Privacy-by-design statement"],
    )
    if report_type == "Monthly leadership summary":
        report = leadership_summary_markdown(forecasts, queue)
        filename = "ROCC_Synthetic_Leadership_Summary.md"
    elif report_type == "Site readiness report":
        selected_site = st.selectbox("Site", forecasts["site_name"].tolist())
        report = site_report_markdown(forecasts.loc[forecasts["site_name"] == selected_site].iloc[0])
        filename = f"ROCC_{selected_site.replace(' ', '_')}_Readiness.md"
    elif report_type == "Partner priority list":
        top = scores.nlargest(15, "partner_priority_score")
        lines = [
            f"{index}. {row.organization_name} — priority {row.partner_priority_score:.1f}, reliability {row.reliability_score:.1f}, confidence {row.confidence_level}"
            for index, row in enumerate(top.itertuples(index=False), start=1)
        ]
        report = (
            "# ROCC Synthetic Partner Priority List\n\n"
            "**SYNTHETIC DEMO — HUMAN REVIEW REQUIRED**\n\n"
            + "\n".join(lines)
            + "\n\nScores apply to partner-source operations, not to individuals. Do Not Contact overrides all priorities."
        )
        filename = "ROCC_Synthetic_Partner_Priorities.md"
    else:
        report = """# ROCC Privacy-by-Design Statement

ROCC uses synthetic inputs only and excludes diagnoses, disability narratives, medical records, accommodation information, eligibility-document images, and real applicant or employee information.

Applicant-side outputs are aggregate by design: people are never listed or scored. Synthetic partner-organization contacts may appear by name only in the outreach workflow and are never scored. The platform evaluates source effectiveness, outreach activity, site readiness, and labor-hour scenarios—not the value or disability status of individuals. Any future use of real data requires employer sponsorship plus formal HR, compliance, privacy, security, and accessibility approval.
"""
        filename = "ROCC_Privacy_by_Design.md"
    st.markdown(report)
    st.download_button("Download Markdown report", data=report, file_name=filename, mime="text/markdown")


def render_governance(data: DemoData, target: float, scenario: str) -> None:
    del target, scenario
    _page_header(
        "Privacy & Governance",
        "The boundaries that keep ROCC synthetic, aggregate by design, explainable, and decision-support only.",
        "Governance / Trust",
    )
    validation = validate_demo_data(data)
    if validation.ok:
        st.success("Synthetic-data validation passed: row counts, ID prefixes, stage gate, domains, references, flags, and labor-hour math are consistent.")
    else:
        st.error("Validation failed. Dashboard outputs should not be used until corrected.")
        for error in validation.errors:
            st.markdown(f"- {error}")

    counts = pd.DataFrame(
        [{"dataset": name, "rows": len(frame), "synthetic_flag_complete": bool(frame["synthetic_flag"].all())} for name, frame in data.frames().items()]
    )
    left, right = st.columns([1, 1.1])
    with left:
        st.markdown("### Data inventory")
        st.dataframe(_label_columns(counts), hide_index=True, use_container_width=True)
        st.caption("The applicants and stage-history rows exist only as in-memory aggregation inputs; they are never rendered, listed, or scored per person (ADR-024).")
        st.markdown("### Non-negotiable commitments")
        st.markdown(
            "- **SYNTHETIC ONLY UNTIL EMPLOYER SPONSORSHIP.** No real-data pathway ships in this demo.\n"
            "- **AGGREGATES BY DESIGN.** Referral sources, sites, and contracts may be measured; applicants never are.\n"
            "- Applicant-side outputs contain no person rows, identifiers, names, statuses, or scores.\n"
            "- Synthetic partner-organization contacts may appear by name only in the outreach workflow. They are never applicants and are never scored."
        )
    with right:
        st.markdown("### Deliberately excluded")
        st.markdown(
            "- Medical diagnoses or disability narratives\n"
            "- Doctor notes or psychological evaluations\n"
            "- IEP/504 or accommodation details\n"
            "- Scanned eligibility documents\n"
            "- Real applicant, employee, or partner data\n"
            "- Automated email sending\n"
            "- Any applicant-level rendering or scoring\n"
            "- Official ODLH compliance certification\n"
            "- Final bid/no-bid automation"
        )
        st.markdown("### Decision boundaries")
        st.markdown(
            "- Site views are internal planning indicators.\n"
            "- Organization scenarios use summed hours, but remain synthetic.\n"
            "- Source scores use mature cohorts and small-sample shrinkage.\n"
            "- All generated communications and reports require human review.\n"
            "- Any future real-data work requires employer sponsorship and formal HR, compliance, privacy, security, and accessibility approval."
        )

    st.markdown("### Manager-facing value statement")
    st.markdown(
        '<div class="insight-box">ROCC connects aggregate recruiting activity to operational readiness. It helps a manager see which sites may need attention, why a forecast changed, which partner organizations are relevant, and who owns the next outreach step. It does not replace HR, compliance, timekeeping, or management judgment.</div>',
        unsafe_allow_html=True,
    )

    with st.expander("Current primary-source framing used by this concept"):
        st.markdown(
            "- [41 U.S.C. § 8501](https://uscode.house.gov/view.xhtml?edition=prelim&num=0&req=granuleid%3AUSC-prelim-title41-section8501)\n"
            "- [AbilityOne Commission Policy 51.404 — Direct Labor Hour Ratio Requirements](https://www.abilityone.gov/laws%2C_regulations_and_policy/documents/U.S.%20AbilityOne%20Commission%20Policy%2051.404%20Direct%20Labor%20Hour%20Ratio%20Requirements%2020250902-a%20signed.pdf)\n"
            "- [AbilityOne Commission Policy 51.403 — QDL Employee Determination](https://www.abilityone.gov/laws%2C_regulations_and_policy/documents/U.S.%20AbilityOne%20Commission%20Policy%2051.403%20Qualifying%20Direct%20Labor%20Employee%20Determination%2020250902-a%20signed.pdf)\n"
            "- [EEOC — Pre-Employment Inquiries and Medical Questions](https://www.eeoc.gov/pre-employment-inquiries-and-medical-questions-examinations)"
        )
        st.caption("Policies can change. A future real-data implementation requires current legal, HR, compliance, CNA, privacy, and security review.")


PAGE_RENDERERS = {
    "Home / Executive Overview": render_home,
    "Site Readiness": render_site_readiness,
    "Resource Network": render_resource_network,
    "Outreach Command Center": render_outreach,
    "Pipeline Health": render_applicant_pipeline,
    "Source Performance": render_source_performance,
    "Ratio Forecast": render_ratio_forecast,
    "Reports": render_reports,
    "Privacy & Governance": render_governance,
}
