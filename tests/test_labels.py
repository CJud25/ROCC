from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).resolve().parents[1] / "app.py")
SNAKE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)+$")


def _columns_on_page(page_key: str) -> set[str]:
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.session_state["nav"] = page_key
    at.run()
    assert not at.exception, f"{page_key} raised: {at.exception}"
    cols: set[str] = set()
    for df in at.dataframe:
        value = df.value
        # AppTest returns the underlying DataFrame even for a Styler-backed
        # st.dataframe (verified empirically on streamlit 1.46.1: the Outreach
        # queue's Styler surfaces as a plain DataFrame with friendly columns).
        # The .data guard is defensive only and is a no-op on 1.46.1.
        frame = value.data if hasattr(value, "data") else value
        if isinstance(frame, pd.DataFrame):
            cols.update(str(c) for c in frame.columns)
    return cols


def test_leadership_tables_have_no_snake_case_headers():
    for page in [
        "Site Readiness",
        "Resource Network",
        "Source Performance",
        "Ratio Forecast",
        "Privacy & Governance",
        "Outreach Command Center",
    ]:
        offenders = {c for c in _columns_on_page(page) if SNAKE.match(c)}
        assert not offenders, f"{page} still shows raw headers: {sorted(offenders)}"
