from itertools import combinations

import pytest

from research.combined_audit_contract import MAIN_FEATURES
from research.combined_audit_reports import (
    build_main_spearman_report,
    build_partial_spearman_report,
)


@pytest.fixture
def sample_leg_rows():
    return [
        {
            "active_bar_count": index + 2,
            "net_thrust": float(index * 3 + 1),
            "gross_close_path": float(index * 5 + 2),
            "net_close_displacement": float(index * 2 + 1),
            "directional_efficiency": 0.1 * (index + 1),
            "directional_continuity_ratio": 0.2 * (index + 1),
            "close_confirmation_ratio": 0.15 * (index + 1),
            "gap_path_share": 0.05 * (index + 1),
            "body_strength_ratio": 0.08 * (index + 1),
            "shadow_position_imbalance": -0.4 + 0.1 * index,
            "overlap_ratio": 0.12 * (index + 1),
            "normalized_directional_close_ols_slope": 0.25 * (index + 1),
            "mean_tick_activity": (100.0, 130.0, 110.0, 150.0, 120.0, 140.0)[index],
        }
        for index in range(6)
    ]


def test_main_report_uses_every_frozen_feature_pair_in_frozen_order(sample_leg_rows):
    report = build_main_spearman_report(sample_leg_rows)

    assert len(report) == 78
    assert [(row["feature_x"], row["feature_y"]) for row in report] == list(
        combinations(MAIN_FEATURES, 2)
    )
    seen = {(row["feature_x"], row["feature_y"]) for row in report}
    assert ("active_bar_count", "net_thrust") in seen
    assert all("gross_tick_activity" not in pair for pair in seen)
    assert all("close_ols_slope" not in pair for pair in seen)


def test_main_report_preserves_pairwise_missing_counts(sample_leg_rows):
    rows = [dict(row) for row in sample_leg_rows]
    rows[0]["overlap_ratio"] = None

    result = next(
        row
        for row in build_main_spearman_report(rows)
        if row["feature_x"] == "body_strength_ratio"
        and row["feature_y"] == "overlap_ratio"
    )

    assert result["n_total"] == len(rows)
    assert result["n_missing_x"] == 0
    assert result["n_missing_y"] == 1
    assert result["n_valid_pairwise"] == len(rows) - 1


def test_partial_report_excludes_control_and_uses_frozen_pair_order(sample_leg_rows):
    report = build_partial_spearman_report(sample_leg_rows)

    assert len(report) == 66
    assert [(row["feature_x"], row["feature_y"]) for row in report] == list(
        combinations(MAIN_FEATURES[1:], 2)
    )
    assert all(row["feature_x"] != "active_bar_count" for row in report)
    assert all(row["feature_y"] != "active_bar_count" for row in report)


def test_partial_report_uses_triple_complete_sample_for_delta(sample_leg_rows):
    rows = [dict(row) for row in sample_leg_rows]
    rows[0]["active_bar_count"] = None

    main = next(
        row
        for row in build_main_spearman_report(rows)
        if row["feature_x"] == "net_thrust"
        and row["feature_y"] == "mean_tick_activity"
    )
    partial = next(
        row
        for row in build_partial_spearman_report(rows)
        if row["feature_x"] == "net_thrust"
        and row["feature_y"] == "mean_tick_activity"
    )

    assert partial["n_valid_triple"] == main["n_valid_pairwise"] - 1
    assert "rho_raw_for_delta" in partial
    assert partial["rho_raw_for_delta"] != main["rho_raw"]


def test_partial_report_preserves_undefined_status_from_stats(sample_leg_rows):
    rows = [dict(row) for row in sample_leg_rows]
    for row in rows[2:]:
        row["active_bar_count"] = None

    partial = next(
        row
        for row in build_partial_spearman_report(rows)
        if row["feature_x"] == "net_thrust"
        and row["feature_y"] == "mean_tick_activity"
    )

    assert partial == {
        "feature_x": "net_thrust",
        "feature_y": "mean_tick_activity",
        "rho_raw_for_delta": None,
        "rho_duration_controlled": None,
        "delta_rho": None,
        "n_valid_triple": 2,
        "status": "UNDEFINED_INSUFFICIENT_OBSERVATIONS",
    }
