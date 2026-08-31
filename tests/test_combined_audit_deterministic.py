import pytest

from research.combined_audit_contract import DETERMINISTIC_RELATIONS
from research.combined_audit_reports import build_deterministic_identity_report


def _by_id(report):
    return {row["relation_id"]: row for row in report}


@pytest.fixture
def full_identity_rows():
    return [
        {
            "signed_close_displacement": -4.0,
            "net_close_displacement": 4.0,
            "aligned_close_steps": 3,
            "opposing_close_steps": 1,
            "flat_close_steps": 1,
            "active_bar_count": 5,
            "directional_continuity_ratio": 0.6,
            "gross_body_magnitude": 12.0,
            "gross_candle_range": 20.0,
            "body_strength_ratio": 0.6,
            "gap_path_contribution": 3.0,
            "gross_close_path": 12.0,
            "gap_path_share": 0.25,
            "gross_forward_shadow": 2.0,
            "gross_backward_shadow": 6.0,
            "gross_shadow_magnitude": 8.0,
            "shadow_position_imbalance": 0.5,
            "gross_overlap_magnitude": 3.0,
            "gross_overlap_capacity": 12.0,
            "overlap_ratio": 0.25,
            "close_ols_slope": -2.0,
            "direction": "BEARISH",
            "directional_close_ols_slope": 2.0,
            "normalized_directional_close_ols_slope": 0.5,
            "gross_tick_activity": 3001,
            "mean_tick_activity": 600.2,
        },
        {
            "signed_close_displacement": 0.0,
            "net_close_displacement": 0.0,
            "aligned_close_steps": 0,
            "opposing_close_steps": 0,
            "flat_close_steps": 0,
            "active_bar_count": 0,
            "directional_continuity_ratio": None,
            "gross_body_magnitude": 0.0,
            "gross_candle_range": 0.0,
            "body_strength_ratio": None,
            "gap_path_contribution": 0.0,
            "gross_close_path": 0.0,
            "gap_path_share": None,
            "gross_forward_shadow": 0.0,
            "gross_backward_shadow": 0.0,
            "gross_shadow_magnitude": 0.0,
            "shadow_position_imbalance": None,
            "gross_overlap_magnitude": 0.0,
            "gross_overlap_capacity": 0.0,
            "overlap_ratio": None,
            "close_ols_slope": 0.0,
            "direction": "BULLISH",
            "directional_close_ols_slope": 0.0,
            "normalized_directional_close_ols_slope": None,
            "gross_tick_activity": 0,
            "mean_tick_activity": 0.0,
        },
    ]


def test_shadow_identity_uses_backward_minus_forward():
    rows = [{
        "gross_forward_shadow": 2.0,
        "gross_backward_shadow": 6.0,
        "gross_shadow_magnitude": 8.0,
        "shadow_position_imbalance": 0.5,
    }]
    result = _by_id(build_deterministic_identity_report(rows))
    row = result["SHADOW_POSITION_IMBALANCE"]
    assert row["total_rows"] == 1
    assert row["verified_rows"] == 1
    assert row["failed_rows"] == 0


def test_zero_shadow_denominator_requires_none_and_is_verified():
    rows = [{
        "gross_forward_shadow": 0.0,
        "gross_backward_shadow": 0.0,
        "gross_shadow_magnitude": 0.0,
        "shadow_position_imbalance": None,
    }]
    result = _by_id(build_deterministic_identity_report(rows))
    row = result["SHADOW_POSITION_IMBALANCE"]
    assert row["total_rows"] == 1
    assert row["verified_rows"] == 1
    assert row["failed_rows"] == 0


def test_every_identity_accounts_for_every_input_row(full_identity_rows):
    report = build_deterministic_identity_report(full_identity_rows)
    assert tuple(row["relation_id"] for row in report) == DETERMINISTIC_RELATIONS
    for row in report:
        assert row["total_rows"] == len(full_identity_rows)
        assert row["verified_rows"] + row["failed_rows"] == row["total_rows"]


def test_full_fixture_verifies_all_locked_identities(full_identity_rows):
    report = build_deterministic_identity_report(full_identity_rows)
    assert all(row["verified_rows"] == len(full_identity_rows) for row in report)
    assert all(row["failed_rows"] == 0 for row in report)


def test_a_failed_row_is_counted_not_silently_skipped(full_identity_rows):
    rows = [dict(r) for r in full_identity_rows]
    rows[0]["shadow_position_imbalance"] = -rows[0]["shadow_position_imbalance"]
    row = _by_id(build_deterministic_identity_report(rows))["SHADOW_POSITION_IMBALANCE"]
    assert row["total_rows"] == len(rows)
    assert row["verified_rows"] + row["failed_rows"] == len(rows)
    assert row["failed_rows"] == 1


def test_count_identity_uses_exact_equality():
    rows = [{
        "aligned_close_steps": 3,
        "opposing_close_steps": 1,
        "flat_close_steps": 1,
        "active_bar_count": 5,
    }]
    result = _by_id(build_deterministic_identity_report(rows))
    assert result["CONTINUITY_COUNT_SUM"]["failed_rows"] == 0


def test_count_identity_rejects_nearby_non_integer_total():
    rows = [{
        "aligned_close_steps": 3,
        "opposing_close_steps": 1,
        "flat_close_steps": 1,
        "active_bar_count": 5.0000000000001,
    }]
    result = _by_id(build_deterministic_identity_report(rows))
    assert result["CONTINUITY_COUNT_SUM"]["verified_rows"] == 0
    assert result["CONTINUITY_COUNT_SUM"]["failed_rows"] == 1


def test_slope_normalization_matches_source_defined_chain():
    rows = [{
        "active_bar_count": 4,
        "gross_candle_range": 20.0,
        "close_ols_slope": -2.0,
        "direction": "BEARISH",
        "directional_close_ols_slope": 2.0,
        "normalized_directional_close_ols_slope": 0.4,
    }]
    result = _by_id(build_deterministic_identity_report(rows))
    assert result["SLOPE_DIRECTION"]["failed_rows"] == 0
    assert result["SLOPE_NORMALIZATION"]["failed_rows"] == 0


def test_tick_activity_identity_uses_locked_float_tolerance():
    rows = [{
        "gross_tick_activity": 3001,
        "mean_tick_activity": 1000.3333333333334,
        "active_bar_count": 3,
    }]
    result = _by_id(build_deterministic_identity_report(rows))
    assert result["TICK_ACTIVITY_IDENTITY"]["failed_rows"] == 0


@pytest.mark.parametrize(
    ("relation_id", "row"),
    [
        ("CONTINUITY_RATIO", {"active_bar_count": 0, "aligned_close_steps": 0, "directional_continuity_ratio": None}),
        ("BODY_STRENGTH_RATIO", {"gross_candle_range": 0.0, "gross_body_magnitude": 0.0, "body_strength_ratio": None}),
        ("GAP_PATH_SHARE", {"gross_close_path": 0.0, "gap_path_contribution": 0.0, "gap_path_share": None}),
        ("OVERLAP_RATIO", {"gross_overlap_capacity": 0.0, "gross_overlap_magnitude": 0.0, "overlap_ratio": None}),
        ("SLOPE_NORMALIZATION", {"active_bar_count": 0, "gross_candle_range": 0.0, "directional_close_ols_slope": 0.0, "normalized_directional_close_ols_slope": None}),
    ],
)
def test_zero_denominator_ratio_identities_require_none(relation_id, row):
    result = _by_id(build_deterministic_identity_report([row]))
    assert result[relation_id]["verified_rows"] == 1
    assert result[relation_id]["failed_rows"] == 0


def test_zero_shadow_denominator_rejects_numeric_replacement_for_none():
    rows = [{
        "gross_forward_shadow": 0.0,
        "gross_backward_shadow": 0.0,
        "gross_shadow_magnitude": 0.0,
        "shadow_position_imbalance": 0.0,
    }]
    result = _by_id(build_deterministic_identity_report(rows))
    assert result["SHADOW_POSITION_IMBALANCE"]["verified_rows"] == 0
    assert result["SHADOW_POSITION_IMBALANCE"]["failed_rows"] == 1


def test_missing_columns_fail_the_unrelated_identity_instead_of_skipping():
    rows = [{"gross_forward_shadow": 2.0, "gross_backward_shadow": 6.0, "gross_shadow_magnitude": 8.0, "shadow_position_imbalance": 0.5}]
    result = _by_id(build_deterministic_identity_report(rows))
    assert result["SHADOW_POSITION_IMBALANCE"]["verified_rows"] == 1
    assert result["CLOSE_DISPLACEMENT_ABS"]["failed_rows"] == 1
    assert result["CLOSE_DISPLACEMENT_ABS"]["verified_rows"] == 0


def test_report_reuses_locked_registry_metadata(full_identity_rows):
    row = build_deterministic_identity_report(full_identity_rows)[0]
    assert row["relation_id"] == "CLOSE_DISPLACEMENT_ABS"
    assert row["relation_type"] == "DETERMINISTIC"
    assert row["participating_features"] == (
        '["direction","signed_close_displacement","net_close_displacement"]'
    )
    assert row["formula"] == "net_close_displacement = abs(signed_close_displacement)"
    assert row["condition"] == "direction_sign in {-1, +1}"
    assert "rel_tol=1e-12" in row["tolerance_policy"]
    assert "None=exact" in row["tolerance_policy"]


def test_invalid_direction_fails_both_direction_conditioned_identities():
    row = {
        "direction": "SIDEWAYS",
        "signed_close_displacement": -4.0,
        "net_close_displacement": 4.0,
        "close_ols_slope": -2.0,
        "directional_close_ols_slope": 2.0,
    }

    result = _by_id(build_deterministic_identity_report([row]))

    for relation_id in ("CLOSE_DISPLACEMENT_ABS", "SLOPE_DIRECTION"):
        assert result[relation_id]["total_rows"] == 1
        assert result[relation_id]["verified_rows"] == 0
        assert result[relation_id]["failed_rows"] == 1
