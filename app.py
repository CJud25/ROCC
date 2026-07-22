"""ROCC Streamlit entry point."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

import streamlit as st

from tens_hq.constants import APP_VERSION, DEFAULT_SEED, DEFAULT_TARGET, SYNTHETIC_BANNER
from tens_hq.pages import PAGE_RENDERERS, apply_theme
from tens_hq.roles import allowed_pages
from tens_hq.synthetic import generate_demo_data
from tens_hq.validation import validate_demo_data

st.set_page_config(
    page_title="ROCC",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(show_spinner="Generating deterministic synthetic operations data...")
def load_demo_data(seed: int):
    return generate_demo_data(seed)


def _query_value(name: str) -> str | None:
    value = st.query_params.get(name)
    if isinstance(value, list):
        return value[-1] if value else None
    return value


def _restore_and_clamp_navigation(visible_pages: list[str]) -> None:
    """Restore URL state before widgets exist, then clamp it to visible choices."""

    query_nav = _query_value("nav")
    if "nav" not in st.session_state and query_nav in visible_pages:
        st.session_state["nav"] = query_nav
    if st.session_state.get("nav") not in visible_pages:
        st.session_state["nav"] = visible_pages[0]


def main() -> None:
    apply_theme()
    data = load_demo_data(DEFAULT_SEED)
    validation = validate_demo_data(data)
    if not validation.ok:
        st.error("Synthetic-data validation failed. Management outputs are unavailable until corrected.")
        for error in validation.errors:
            st.markdown(f"- {error}")
        st.stop()

    with st.sidebar:
        st.markdown("# ROCC — Recruiting & Outreach Control Center")
        st.caption("part of TENS HQ")
        visible_pages = [page for page in PAGE_RENDERERS if page in allowed_pages()]
        _restore_and_clamp_navigation(visible_pages)
        page = st.radio(
            "Navigate",
            visible_pages,
            key="nav",
            label_visibility="collapsed",
        )
        st.markdown(
            f'<div class="sidebar-banner">{SYNTHETIC_BANNER}</div>',
            unsafe_allow_html=True,
        )
        st.markdown("---")
        st.markdown("**Planning controls**")
        scenario = st.selectbox("Scenario", ["Base", "Conservative", "Optimistic"])
        target_pct = st.slider("Planning target", 70.0, 82.0, DEFAULT_TARGET * 100.0, 0.5)
        st.caption("Site indicators are planning proxies. They are not official ODLH determinations.")
        st.markdown("---")
        st.caption(f"Demo v{APP_VERSION} · Seed {DEFAULT_SEED}")

    st.query_params["nav"] = page
    PAGE_RENDERERS[page](data, target_pct / 100.0, scenario)


if __name__ == "__main__":
    main()
