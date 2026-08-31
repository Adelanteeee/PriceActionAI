from dataclasses import asdict

from research.combined_audit_contract import (
    DETERMINISTIC_FLOAT_ABS_TOL,
    DETERMINISTIC_FLOAT_REL_TOL,
    DETERMINISTIC_RELATIONS,
    DETERMINISTIC_REGISTRY,
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
    assert all(FEATURE_SPECS[name].stratified_audit_eligible for name in MAIN_FEATURES)
    assert all(FEATURE_SPECS[name].stratified_audit_eligible for name in RAW_DIRECTION_SENSITIVE)
    assert all(not FEATURE_SPECS[name].pairwise_eligible for name in RAW_DIRECTION_SENSITIVE)
    supplementary = set(MAIN_FEATURES) | set(RAW_DIRECTION_SENSITIVE)
    assert all(
        not spec.stratified_audit_eligible
        for name, spec in FEATURE_SPECS.items()
        if name not in supplementary
    )


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


def test_directional_formulas_preserve_locked_signed_clamping():
    assert FEATURE_SPECS["directional_efficiency"].formula == (
        "min(1.0, max(0.0, signed_close_displacement) / gross_close_path) "
        "when gross_close_path > 0, else None"
    )
    assert FEATURE_SPECS["close_confirmation_ratio"].formula == (
        "max(0.0, signed_close_displacement) / net_thrust "
        "when signed_close_displacement is defined and net_thrust > 0, else None"
    )
    assert "abs(signed_close_displacement)" not in FEATURE_SPECS["directional_efficiency"].formula
    assert "abs(signed_close_displacement)" not in FEATURE_SPECS["close_confirmation_ratio"].formula


def test_gap_path_contribution_uses_scheduled_close_step_path():
    assert FEATURE_SPECS["gap_path_contribution"].formula == (
        "sum(abs(close_i - close_{i-1})) only for active close steps "
        "whose current index is in scheduled_gap_after_indices"
    )


def test_none_branches_are_explicit_in_deterministic_registry():
    expected = {
        "CONTINUITY_RATIO": "active_bar_count == 0",
        "BODY_STRENGTH_RATIO": "gross_candle_range == 0",
        "GAP_PATH_SHARE": "gross_close_path == 0",
        "SHADOW_POSITION_IMBALANCE": "gross_shadow_magnitude == 0",
        "OVERLAP_RATIO": "gross_overlap_capacity == 0",
        "SLOPE_NORMALIZATION": "active_bar_count < 2 (Source-defined directional_close_ols_slope and normalized_directional_close_ols_slope are None), or mean_candle_range is None or mean_candle_range <= 0",
    }
    for relation_id, undefined_when in expected.items():
        metadata = DETERMINISTIC_REGISTRY[relation_id]
        assert metadata["undefined_when"] == undefined_when
        assert metadata["undefined_result"] == "None (valid undefined value)"


def test_deterministic_registry_has_locked_machine_readable_metadata():
    expected_participants = {
        "CLOSE_DISPLACEMENT_ABS": '["direction","signed_close_displacement","net_close_displacement"]',
        "CONTINUITY_COUNT_SUM": '["aligned_close_steps","opposing_close_steps","flat_close_steps","active_bar_count"]',
        "CONTINUITY_RATIO": '["aligned_close_steps","active_bar_count","directional_continuity_ratio"]',
        "BODY_STRENGTH_RATIO": '["gross_body_magnitude","gross_candle_range","body_strength_ratio"]',
        "GAP_PATH_SHARE": '["gap_path_contribution","gross_close_path","gap_path_share"]',
        "SHADOW_MAGNITUDE_SUM": '["gross_forward_shadow","gross_backward_shadow","gross_shadow_magnitude"]',
        "SHADOW_POSITION_IMBALANCE": '["gross_forward_shadow","gross_backward_shadow","gross_shadow_magnitude","shadow_position_imbalance"]',
        "OVERLAP_RATIO": '["gross_overlap_magnitude","gross_overlap_capacity","overlap_ratio"]',
        "SLOPE_DIRECTION": '["direction","close_ols_slope","directional_close_ols_slope"]',
        "SLOPE_NORMALIZATION": '["active_bar_count","gross_candle_range","directional_close_ols_slope","normalized_directional_close_ols_slope"]',
        "TICK_ACTIVITY_IDENTITY": '["mean_tick_activity","active_bar_count","gross_tick_activity"]',
    }
    assert {
        relation_id: metadata["participating_features"]
        for relation_id, metadata in DETERMINISTIC_REGISTRY.items()
    } == expected_participants
    assert all(
        metadata["relation_type"] == "DETERMINISTIC"
        for metadata in DETERMINISTIC_REGISTRY.values()
    )
    assert DETERMINISTIC_REGISTRY["TICK_ACTIVITY_IDENTITY"]["condition"] == "always"


def test_feature_role_rows_are_csv_ready_and_do_not_alias_registry():
    rows = feature_role_rows()
    assert len(rows) == len(FEATURE_SPECS)
    assert tuple(rows[0]) == FEATURE_ROLE_COLUMNS
    assert all(tuple(row) == FEATURE_ROLE_COLUMNS for row in rows)
    assert [row["feature"] for row in rows[: len(MAIN_FEATURES)]] == list(MAIN_FEATURES)
    assert rows[0] == asdict(FEATURE_SPECS[rows[0]["feature"]])
    rows[0]["feature"] = "mutated-copy"
    assert rows[0]["feature"] != next(iter(FEATURE_SPECS))
