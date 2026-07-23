from __future__ import annotations

from tens_hq.constants import COUNTY_NAMES, SITE_PROFILES
from tens_hq.validation import expected_row_counts, validate_demo_data


def test_derivable_counts_track_generator_constants():
    counts = expected_row_counts()
    assert counts["sites"] == len(SITE_PROFILES) == 12
    assert counts["counties"] == sum(len(v) for v in COUNTY_NAMES.values()) == 48
    assert counts["labor_hours"] == len(SITE_PROFILES) * 24 == 288


def test_expected_counts_reproduce_actual_generation(demo_data):
    counts = expected_row_counts()
    for name, expected in counts.items():
        assert len(getattr(demo_data, name)) == expected, name
    assert validate_demo_data(demo_data).ok
