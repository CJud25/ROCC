from __future__ import annotations

from dataclasses import replace

import pytest

from tens_hq.constants import COUNTY_NAMES, SITE_PROFILES
from tens_hq.validation import expected_row_counts, validate_demo_data


def _with_frame(data, name, mutate):
    frame = getattr(data, name).copy()
    mutate(frame)
    return replace(data, **{name: frame})


def _wrong_row_count(data):
    return replace(data, counties=data.counties.iloc[:-1].copy())


def _prohibited_column(data):
    return _with_frame(data, "sites", lambda frame: frame.__setitem__("medical_record", "none"))


def _missing_synthetic_flag(data):
    return replace(data, sites=data.sites.drop(columns="synthetic_flag").copy())


def _unmarked_synthetic_row(data):
    return _with_frame(data, "sites", lambda frame: frame.__setitem__("synthetic_flag", False))


def _invalid_id_prefix(data):
    return _with_frame(data, "sites", lambda frame: frame.__setitem__("site_id", "INVALID"))


def _duplicate_id(data):
    def mutate(frame):
        frame.loc[frame.index[1], "site_id"] = frame.loc[frame.index[0], "site_id"]

    return _with_frame(data, "sites", mutate)


def _non_reserved_email(data):
    return _with_frame(
        data,
        "contacts",
        lambda frame: frame.__setitem__("contact_email", "person@example.com"),
    )


def _non_reserved_website(data):
    return _with_frame(
        data,
        "organizations",
        lambda frame: frame.__setitem__("website_url", "https://example.com"),
    )


def _qdl_exceeds_total(data):
    def mutate(frame):
        frame.loc[frame.index[0], "mock_qdl_hours"] = frame.loc[frame.index[0], "total_direct_labor_hours"] + 1

    return _with_frame(data, "labor_hours", mutate)


def _negative_hours(data):
    def mutate(frame):
        frame.loc[frame.index[0], "mock_qdl_hours"] = -1

    return _with_frame(data, "labor_hours", mutate)


def _ratio_does_not_reproduce(data):
    def mutate(frame):
        frame.loc[frame.index[0], "current_ratio_pct"] += 1

    return _with_frame(data, "labor_hours", mutate)


def _missing_synthetic_display_label(data):
    return _with_frame(
        data,
        "applicants",
        lambda frame: frame.__setitem__("display_label", "Applicant"),
    )


def _eligibility_before_start(data):
    def mutate(frame):
        index = frame.index[frame["start_date"].isna()][0]
        frame.loc[index, "eligibility_review_status"] = "Cleared"

    return _with_frame(data, "applicants", mutate)


def _documentation_before_start(data):
    def mutate(frame):
        index = frame.index[frame["start_date"].isna()][0]
        frame.loc[index, "documentation_status"] = "Complete"

    return _with_frame(data, "applicants", mutate)


def _unknown_source_organization(data):
    return _with_frame(
        data,
        "applicants",
        lambda frame: frame.__setitem__("source_organization_id", "SYN-ORG-UNKNOWN"),
    )


def _unknown_target_site(data):
    return _with_frame(
        data,
        "applicants",
        lambda frame: frame.__setitem__("target_site_id", "SYN-SITE-UNKNOWN"),
    )


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


@pytest.mark.parametrize(
    ("mutator", "error"),
    [
        (_wrong_row_count, "counties: expected 48 rows, found 47"),
        (_prohibited_column, "prohibited columns present"),
        (_missing_synthetic_flag, "synthetic_flag is missing"),
        (_unmarked_synthetic_row, "one or more rows are not marked synthetic"),
        (_invalid_id_prefix, "ID prefix contract failed"),
        (_duplicate_id, "duplicate IDs detected"),
        (_non_reserved_email, "non-reserved email domain detected"),
        (_non_reserved_website, "non-reserved website domain detected"),
        (_qdl_exceeds_total, "QDL hours exceed total direct labor hours"),
        (_negative_hours, "negative hours detected"),
        (_ratio_does_not_reproduce, "stored ratios do not reproduce"),
        (_missing_synthetic_display_label, "synthetic display label missing"),
        (_eligibility_before_start, "eligibility status used before the synthetic start-stage gate"),
        (_documentation_before_start, "documentation status used before the synthetic start-stage gate"),
        (_unknown_source_organization, "unknown source organization reference"),
        (_unknown_target_site, "unknown target site reference"),
    ],
    ids=lambda value: value.__name__ if callable(value) else None,
)
def test_validation_flags_each_corrupted_contract(demo_data, mutator, error):
    result = validate_demo_data(mutator(demo_data))
    assert result.ok is False
    assert any(error in message for message in result.errors)


def test_thin_stage_history_is_a_warning_not_an_error(demo_data):
    corrupted = replace(demo_data, stage_history=demo_data.stage_history.iloc[:3999].copy())
    result = validate_demo_data(corrupted)
    assert result.ok is True
    assert "stage_history: fewer than 4,000 events; dashboard story may be thin" in result.warnings
