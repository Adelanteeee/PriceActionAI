from dataclasses import asdict

from research.combined_audit_contract import (
    DETERMINISTIC_FLOAT_ABS_TOL,
    DETERMINISTIC_FLOAT_REL_TOL,
    DETERMINISTIC_RELATIONS,
    FEATURE_ROLE_COLUMNS,
    FEATURE_SPECS,
    MAIN_FEATURES,
    RAW_DIRECTION_SENSITIVE,
    feature_role_rows,
)


def test_main_feature_set_is_exactly_locked_13():
    assert MAIN_FEATURES == (
        "active_bar_count",
        "net_thrust",
        "gross_close_path",
        "net_close_displacement",
        "directional_efficiency",
        "directional_continuity_ratio",
        "close_confirmation_ratio",
        "gap_path_share",
        "body_strength_ratio",
        "shadow_position_imbalance",
        "overlap_ratio",
        "normalized_directional_close_ols_slope",
        "mean_tick_activity",
    )
    assert len(MAIN_FEATURES) == 13


def test_raw_direction_sensitive_fields_are_not_main_features():
    assert RAW_DIRECTION_SENSITIVE == (
        "close_ols_slope",
        "gross_upper_shadow",
        "gross_lower_shadow",
    )
    assert set(RAW_DIRECTION_SENSITIVE).isdisjoint(MAIN_FEATURES)


def test_direction_and_roles_match_locked_contract():
    assert FEATURE_SPECS["net_thrust"].direction_semantics == "DIRECTION_NEUTRAL"
    assert FEATURE_SPECS["net_close_displacement"].direction_semantics == "DIRECTION_NEUTRAL"
    assert FEATURE_SPECS["shadow_position_imbalance"].direction_semantics == "DIRECTION_RELATIVE"
    assert FEATURE_SPECS["close_ols_slope"].analysis_role == "RAW_DIRECTION_SENSITIVE"
    assert FEATURE_SPECS["gross_tick_activity"].analysis_role == "IDENTITY_COMPONENT"
    assert FEATURE_SPECS["mean_candle_range"].analysis_role == "SUPPORTING_COMPONENT"


def test_locked_float_tolerance_is_exact():
    assert DETERMINISTIC_FLOAT_REL_TOL == 1e-12
    assert DETERMINISTIC_FLOAT_ABS_TOL == 1e-12


def test_registry_covers_main_raw_and_traceability_fields():
    expected = set(MAIN_FEATURES) | set(RAW_DIRECTION_SENSITIVE) | {
        "signed_close_displacement",
        "aligned_close_steps",
        "opposing_close_steps",
        "flat_close_steps",
        "gap_path_contribution",
        "gross_body_magnitude",
        "gross_candle_range",
        "gross_forward_shadow",
        "gross_backward_shadow",
        "gross_shadow_magnitude",
        "gross_overlap_magnitude",
        "gross_overlap_capacity",
        "directional_close_ols_slope",
        "gross_tick_activity",
        "mean_candle_range",
        "direction",
        "direction_agreement",
        "temporal_profile_tag",
        "timeframe",
        "symbol",
        "leg_id",
        "leg_no",
        "start_index",
        "end_index",
        "start_time",
        "end_time",
        "start_kind",
        "end_kind",
        "start_price",
        "end_price",
        "owned_candle_count",
    }
    assert expected <= FEATURE_SPECS.keys()
    assert FEATURE_SPECS["active_bar_count"].controlled_eligible is False
    assert "mean_candle_range" not in MAIN_FEATURES


def test_main_and_raw_eligibility_are_explicit():
    assert all(FEATURE_SPECS[name].pairwise_eligible for name in MAIN_FEATURES)
    assert all(FEATURE_SPECS[name].controlled_eligible for name in MAIN_FEATURES if name != "active_bar_count")
    assert all(FEATURE_SPECS[name].stratified_audit_eligible for name in RAW_DIRECTION_SENSITIVE)
    assert all(not FEATURE_SPECS[name].pairwise_eligible for name in RAW_DIRECTION_SENSITIVE)


def test_shadow_formula_and_deterministic_relation_ids_are_locked():
    assert FEATURE_SPECS["shadow_position_imbalance"].formula == (
        "(gross_backward_shadow - gross_forward_shadow) / gross_shadow_magnitude"
    )
    assert DETERMINISTIC_RELATIONS == (
        "CLOSE_DISPLACEMENT_ABS",
        "CONTINUITY_COUNT_SUM",
        "CONTINUITY_RATIO",
        "BODY_STRENGTH_RATIO",
        "GAP_PATH_SHARE",
        "SHADOW_MAGNITUDE_SUM",
        "SHADOW_POSITION_IMBALANCE",
        "OVERLAP_RATIO",
        "SLOPE_DIRECTION",
        "SLOPE_NORMALIZATION",
        "TICK_ACTIVITY_IDENTITY",
    )


def test_feature_role_rows_are_csv_ready_and_do_not_alias_registry():
    rows = feature_role_rows()
    assert len(rows) == len(FEATURE_SPECS)
    assert tuple(rows[0]) == FEATURE_ROLE_COLUMNS
    assert all(tuple(row) == FEATURE_ROLE_COLUMNS for row in rows)
    assert [row["feature"] for row in rows[: len(MAIN_FEATURES)]] == list(MAIN_FEATURES)
    assert rows[0] == asdict(FEATURE_SPECS[rows[0]["feature"]])
    rows[0]["feature"] = "mutated-copy"
    assert rows[0]["feature"] != next(iter(FEATURE_SPECS))
