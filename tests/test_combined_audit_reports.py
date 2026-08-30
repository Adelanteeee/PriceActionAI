from itertools import combinations
import math

import pytest

from research.combined_audit_contract import MAIN_FEATURES, RAW_DIRECTION_SENSITIVE
from research.combined_audit_reports import (
    build_cross_tf_relationship_report,
    build_direction_stratified_report,
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
            "direction": "BULLISH" if index % 2 == 0 else "BEARISH",
            "close_ols_slope": -0.3 + 0.1 * index,
            "gross_upper_shadow": float(index + 3),
            "gross_lower_shadow": float(10 - index),
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


def test_direction_stratified_report_never_mixes_bull_and_bear(sample_leg_rows):
    bullish = build_direction_stratified_report(sample_leg_rows, "BULLISH")
    bearish = build_direction_stratified_report(sample_leg_rows, "BEARISH")

    assert bullish["source_row_count"] == sum(
        row["direction"] == "BULLISH" for row in sample_leg_rows
    )
    assert bearish["source_row_count"] == sum(
        row["direction"] == "BEARISH" for row in sample_leg_rows
    )
    assert len(bullish["raw"]) == 120
    assert len(bullish["partial"]) == 105
    assert all(row["evidence_scope"] == "SUPPLEMENTARY_ONLY" for row in bullish["raw"])
    assert all(
        row["evidence_scope"] == "SUPPLEMENTARY_ONLY" for row in bullish["partial"]
    )


def test_raw_direction_fields_exist_only_in_supplementary_pairs(sample_leg_rows):
    supplementary = build_direction_stratified_report(sample_leg_rows, "BULLISH")
    pairs = {(row["feature_x"], row["feature_y"]) for row in supplementary["raw"]}

    assert all(
        any(field in pair for pair in pairs) for field in RAW_DIRECTION_SENSITIVE
    )
    assert all(
        all(field != feature for feature in main_pair)
        for field in RAW_DIRECTION_SENSITIVE
        for main_pair in (
            (row["feature_x"], row["feature_y"])
            for row in build_main_spearman_report(sample_leg_rows)
        )
    )


@pytest.fixture
def cross_tf_tie_inputs():
    main_by_tf = {
        "M5": [
            {
                "feature_x": "a",
                "feature_y": "b",
                "rho_raw": 0.2,
                "status": "DEFINED",
                "n_valid_pairwise": 10,
            }
        ],
        "M15": [
            {
                "feature_x": "a",
                "feature_y": "b",
                "rho_raw": -0.3,
                "status": "DEFINED",
                "n_valid_pairwise": 11,
            }
        ],
        "M30": [
            {
                "feature_x": "a",
                "feature_y": "b",
                "rho_raw": 0.0,
                "status": "DEFINED",
                "n_valid_pairwise": 12,
            }
        ],
        "H1": [
            {
                "feature_x": "a",
                "feature_y": "b",
                "rho_raw": None,
                "status": "UNDEFINED_CONSTANT_INPUT",
                "n_valid_pairwise": 13,
            }
        ],
    }
    return main_by_tf, {timeframe: [] for timeframe in main_by_tf}


def test_cross_tf_sign_accounting_reports_tie_without_picking_sign(cross_tf_tie_inputs):
    main_by_tf, partial_by_tf = cross_tf_tie_inputs
    row = build_cross_tf_relationship_report(main_by_tf, partial_by_tf)[0]

    assert row["n_positive_tf"] == 1
    assert row["n_negative_tf"] == 1
    assert row["n_zero_tf"] == 1
    assert row["n_undefined_tf"] == 1
    assert row["sign_agreement_count"] == 1
    assert row["sign_agreement_tie"] is True
    assert row["sign_agreement_modal_signs"] == ["NEGATIVE", "POSITIVE", "ZERO"]


def test_cross_tf_range_ignores_undefined_not_zero(cross_tf_tie_inputs):
    main_by_tf, partial_by_tf = cross_tf_tie_inputs
    row = build_cross_tf_relationship_report(main_by_tf, partial_by_tf)[0]

    assert row["rho_min"] == -0.3
    assert row["rho_max"] == 0.2
    assert math.isclose(row["rho_range"], 0.5)


def test_cross_tf_merges_each_timeframe_by_pair_key_not_row_position():
    pairs_m5 = [
        {"feature_x": "a", "feature_y": "b", "rho_raw": 0.1, "n_valid_pairwise": 5},
        {"feature_x": "c", "feature_y": "d", "rho_raw": -0.1, "n_valid_pairwise": 6},
    ]
    pairs_m15 = list(
        reversed(
            [
                {
                    "feature_x": "a",
                    "feature_y": "b",
                    "rho_raw": 0.2,
                    "n_valid_pairwise": 7,
                },
                {
                    "feature_x": "c",
                    "feature_y": "d",
                    "rho_raw": -0.2,
                    "n_valid_pairwise": 8,
                },
            ]
        )
    )
    main_by_tf = {"M5": pairs_m5, "M15": pairs_m15, "M30": [], "H1": []}

    rows = build_cross_tf_relationship_report(
        main_by_tf, {timeframe: [] for timeframe in main_by_tf}
    )
    by_pair = {(row["feature_x"], row["feature_y"]): row for row in rows}

    assert by_pair[("a", "b")]["rho_M5"] == 0.1
    assert by_pair[("a", "b")]["rho_M15"] == 0.2
    assert by_pair[("c", "d")]["rho_M5"] == -0.1
    assert by_pair[("c", "d")]["rho_M15"] == -0.2


def test_cross_tf_all_undefined_sign_fields_remain_undefined():
    main_by_tf = {
        timeframe: [
            {"feature_x": "a", "feature_y": "b", "rho_raw": None, "n_valid_pairwise": 2}
        ]
        for timeframe in ("M5", "M15", "M30", "H1")
    }

    row = build_cross_tf_relationship_report(
        main_by_tf, {timeframe: [] for timeframe in main_by_tf}
    )[0]

    assert row["n_undefined_tf"] == 4
    assert row["sign_agreement_count"] is None
    assert row["sign_agreement_tie"] is None
    assert row["sign_agreement_modal_signs"] is None
    assert row["rho_min"] is None
    assert row["rho_max"] is None
    assert row["rho_range"] is None


def test_cross_tf_main_pairs_include_controlled_eligibility(sample_leg_rows):
    main_by_tf = {
        timeframe: build_main_spearman_report(sample_leg_rows)
        for timeframe in ("M5", "M15", "M30", "H1")
    }
    partial_by_tf = {
        timeframe: build_partial_spearman_report(sample_leg_rows)
        for timeframe in main_by_tf
    }

    report = build_cross_tf_relationship_report(main_by_tf, partial_by_tf)

    assert len(report) == 78
    assert sum(not row["controlled_eligible"] for row in report) == 12
    assert all(
        row["controlled_rho_M5"] is None
        for row in report
        if not row["controlled_eligible"]
    )
