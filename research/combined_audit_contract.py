"""Frozen machine-readable contract for the Combined Leg Feature Audit.

This module contains metadata only.  It deliberately has no dependency on
the production Engine or on any input snapshots.
"""

from dataclasses import asdict, dataclass


DETERMINISTIC_FLOAT_REL_TOL = 1e-12
DETERMINISTIC_FLOAT_ABS_TOL = 1e-12

TIMEFRAMES = ("M5", "M15", "M30", "H1")
DIRECTIONS = ("BULLISH", "BEARISH")

MAIN_FEATURES = (
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

RAW_DIRECTION_SENSITIVE = (
    "close_ols_slope",
    "gross_upper_shadow",
    "gross_lower_shadow",
)


@dataclass(frozen=True)
class FeatureSpec:
    feature: str
    formula: str
    sign_semantics: str
    direction_semantics: str
    analysis_role: str
    pairwise_eligible: bool
    controlled_eligible: bool
    stratified_audit_eligible: bool


def _main(
    feature: str,
    formula: str,
    sign_semantics: str,
    direction_semantics: str,
    *,
    controlled_eligible: bool = True,
) -> FeatureSpec:
    return FeatureSpec(
        feature=feature,
        formula=formula,
        sign_semantics=sign_semantics,
        direction_semantics=direction_semantics,
        analysis_role="ANALYSIS_FEATURE",
        pairwise_eligible=True,
        controlled_eligible=controlled_eligible,
        stratified_audit_eligible=True,
    )


def _component(
    feature: str,
    formula: str,
    sign_semantics: str,
    direction_semantics: str = "DIRECTION_NEUTRAL",
    *,
    identity: bool = False,
) -> FeatureSpec:
    return FeatureSpec(
        feature=feature,
        formula=formula,
        sign_semantics=sign_semantics,
        direction_semantics=direction_semantics,
        analysis_role="IDENTITY_COMPONENT" if identity else "SUPPORTING_COMPONENT",
        pairwise_eligible=False,
        controlled_eligible=False,
        stratified_audit_eligible=False,
    )


def _raw(feature: str, formula: str, sign_semantics: str) -> FeatureSpec:
    return FeatureSpec(
        feature=feature,
        formula=formula,
        sign_semantics=sign_semantics,
        direction_semantics="DIRECTION_SENSITIVE",
        analysis_role="RAW_DIRECTION_SENSITIVE",
        pairwise_eligible=False,
        controlled_eligible=False,
        stratified_audit_eligible=True,
    )


def _metadata(
    feature: str,
    formula: str,
    sign_semantics: str = "not applicable",
    direction_semantics: str = "NOT_APPLICABLE",
    *,
    role: str = "METADATA",
) -> FeatureSpec:
    return FeatureSpec(
        feature=feature,
        formula=formula,
        sign_semantics=sign_semantics,
        direction_semantics=direction_semantics,
        analysis_role=role,
        pairwise_eligible=False,
        controlled_eligible=False,
        stratified_audit_eligible=False,
    )


# Insertion order is part of the output contract: main features are first and
# remain in the locked order, followed by supporting/identity, raw, and
# traceability fields.
FEATURE_SPECS: dict[str, FeatureSpec] = {
    "active_bar_count": _main(
        "active_bar_count",
        "count of active bars",
        "nonnegative integer count",
        "DIRECTION_NEUTRAL",
        controlled_eligible=False,
    ),
    "net_thrust": _main(
        "net_thrust",
        "abs(end_price - start_price)",
        "nonnegative magnitude",
        "DIRECTION_NEUTRAL",
    ),
    "gross_close_path": _main(
        "gross_close_path",
        "sum(abs(close_i - close_{i-1})) over active close steps",
        "nonnegative magnitude",
        "DIRECTION_NEUTRAL",
    ),
    "net_close_displacement": _main(
        "net_close_displacement",
        "abs(close_end - close_start)",
        "nonnegative magnitude",
        "DIRECTION_NEUTRAL",
    ),
    "directional_efficiency": _main(
        "directional_efficiency",
        "min(1.0, max(0.0, signed_close_displacement) / gross_close_path) "
        "when gross_close_path > 0, else None",
        "nonnegative ratio; undefined when gross_close_path == 0",
        "DIRECTION_RELATIVE",
    ),
    "directional_continuity_ratio": _main(
        "directional_continuity_ratio",
        "aligned_close_steps / active_bar_count",
        "ratio in [0, 1]; undefined when active_bar_count == 0",
        "DIRECTION_RELATIVE",
    ),
    "close_confirmation_ratio": _main(
        "close_confirmation_ratio",
        "max(0.0, signed_close_displacement) / net_thrust "
        "when signed_close_displacement is defined and net_thrust > 0, else None",
        "nonnegative ratio; undefined when net_thrust == 0",
        "DIRECTION_RELATIVE",
    ),
    "gap_path_share": _main(
        "gap_path_share",
        "gap_path_contribution / gross_close_path",
        "ratio in [0, 1]; undefined when gross_close_path == 0",
        "DIRECTION_NEUTRAL",
    ),
    "body_strength_ratio": _main(
        "body_strength_ratio",
        "gross_body_magnitude / gross_candle_range",
        "ratio in [0, 1]; undefined when gross_candle_range == 0",
        "DIRECTION_NEUTRAL",
    ),
    "shadow_position_imbalance": _main(
        "shadow_position_imbalance",
        "(gross_backward_shadow - gross_forward_shadow) / gross_shadow_magnitude",
        "positive = Backward-shadow dominance; zero = equal; negative = Forward-shadow dominance",
        "DIRECTION_RELATIVE",
    ),
    "overlap_ratio": _main(
        "overlap_ratio",
        "gross_overlap_magnitude / gross_overlap_capacity",
        "ratio in [0, 1]; undefined when gross_overlap_capacity == 0",
        "DIRECTION_NEUTRAL",
    ),
    "normalized_directional_close_ols_slope": _main(
        "normalized_directional_close_ols_slope",
        "directional_close_ols_slope / mean_candle_range",
        "positive = direction-aligned slope; negative = opposing slope; zero = flat",
        "DIRECTION_RELATIVE",
    ),
    "mean_tick_activity": _main(
        "mean_tick_activity",
        "gross_tick_activity / active_bar_count",
        "nonnegative activity rate; undefined when active_bar_count == 0",
        "DIRECTION_NEUTRAL",
    ),
    "signed_close_displacement": _component(
        "signed_close_displacement",
        "direction_sign * (close_end - close_start)",
        "signed close displacement",
    ),
    "aligned_close_steps": _component(
        "aligned_close_steps",
        "count of close steps aligned with direction_sign",
        "nonnegative integer count",
        "DIRECTION_RELATIVE",
        identity=True,
    ),
    "opposing_close_steps": _component(
        "opposing_close_steps",
        "count of close steps opposing direction_sign",
        "nonnegative integer count",
        "DIRECTION_RELATIVE",
        identity=True,
    ),
    "flat_close_steps": _component(
        "flat_close_steps",
        "count of flat close steps",
        "nonnegative integer count",
        "DIRECTION_NEUTRAL",
        identity=True,
    ),
    "gap_path_contribution": _component(
        "gap_path_contribution",
        "sum(abs(close_i - close_{i-1})) only for active close steps "
        "whose current index is in scheduled_gap_after_indices",
        "nonnegative magnitude",
        "DIRECTION_RELATIVE",
        identity=True,
    ),
    "gross_body_magnitude": _component(
        "gross_body_magnitude",
        "sum(abs(close_i - open_i)) over active candles",
        "nonnegative magnitude",
        identity=True,
    ),
    "gross_candle_range": _component(
        "gross_candle_range",
        "sum(high_i - low_i) over active candles",
        "nonnegative magnitude",
        identity=True,
    ),
    "gross_forward_shadow": _component(
        "gross_forward_shadow",
        "sum of direction-forward candle shadows",
        "nonnegative magnitude",
        "DIRECTION_RELATIVE",
        identity=True,
    ),
    "gross_backward_shadow": _component(
        "gross_backward_shadow",
        "sum of direction-backward candle shadows",
        "nonnegative magnitude",
        "DIRECTION_RELATIVE",
        identity=True,
    ),
    "gross_shadow_magnitude": _component(
        "gross_shadow_magnitude",
        "gross_forward_shadow + gross_backward_shadow",
        "nonnegative magnitude",
        "DIRECTION_RELATIVE",
        identity=True,
    ),
    "gross_overlap_magnitude": _component(
        "gross_overlap_magnitude",
        "sum of overlap magnitudes across active candles",
        "nonnegative magnitude",
        "DIRECTION_NEUTRAL",
        identity=True,
    ),
    "gross_overlap_capacity": _component(
        "gross_overlap_capacity",
        "sum of overlap capacities across active candles",
        "nonnegative magnitude",
        "DIRECTION_NEUTRAL",
        identity=True,
    ),
    "directional_close_ols_slope": _component(
        "directional_close_ols_slope",
        "direction_sign * close_ols_slope",
        "signed direction-normalized slope",
        "DIRECTION_RELATIVE",
        identity=True,
    ),
    "gross_tick_activity": _component(
        "gross_tick_activity",
        "mean_tick_activity * active_bar_count",
        "nonnegative activity total",
        "DIRECTION_NEUTRAL",
        identity=True,
    ),
    "mean_candle_range": _component(
        "mean_candle_range",
        "gross_candle_range / active_bar_count",
        "nonnegative average range; undefined when active_bar_count == 0",
        "DIRECTION_NEUTRAL",
    ),
    "close_ols_slope": _raw(
        "close_ols_slope",
        "OLS slope of close prices over active bar positions",
        "signed raw slope",
    ),
    "gross_upper_shadow": _raw(
        "gross_upper_shadow",
        "sum of upper candle shadows over active candles",
        "nonnegative magnitude",
    ),
    "gross_lower_shadow": _raw(
        "gross_lower_shadow",
        "sum of lower candle shadows over active candles",
        "nonnegative magnitude",
    ),
    "direction": _metadata(
        "direction",
        "structural leg direction label",
        "categorical label",
        "STRATIFICATION_ONLY",
        role="CATEGORICAL",
    ),
    "direction_agreement": _metadata(
        "direction_agreement",
        "direction agreement diagnostic flag",
        "boolean diagnostic",
        role="DIAGNOSTIC",
    ),
    "temporal_profile_tag": _metadata(
        "temporal_profile_tag",
        "temporal profile diagnostic label",
        "categorical label",
        role="DIAGNOSTIC",
    ),
    "timeframe": _metadata(
        "timeframe",
        "source timeframe identifier",
        "categorical label",
        role="METADATA",
    ),
    "symbol": _metadata(
        "symbol",
        "source instrument identifier",
        "categorical label",
        role="METADATA",
    ),
    "leg_id": _metadata(
        "leg_id",
        "stable leg identifier",
        "identifier metadata",
        role="METADATA",
    ),
    "leg_no": _metadata(
        "leg_no",
        "one-based leg sequence number",
        "nonnegative integer identifier",
        role="METADATA",
    ),
    "start_index": _metadata(
        "start_index",
        "source active-bar start index",
        "nonnegative integer index",
        role="METADATA",
    ),
    "end_index": _metadata(
        "end_index",
        "source active-bar end index",
        "nonnegative integer index",
        role="METADATA",
    ),
    "start_time": _metadata(
        "start_time",
        "timestamp at the leg start",
        "timestamp metadata",
        role="METADATA",
    ),
    "end_time": _metadata(
        "end_time",
        "timestamp at the leg end",
        "timestamp metadata",
        role="METADATA",
    ),
    "start_kind": _metadata(
        "start_kind",
        "start pivot kind",
        "categorical label",
        role="CATEGORICAL",
    ),
    "end_kind": _metadata(
        "end_kind",
        "end pivot kind",
        "categorical label",
        role="CATEGORICAL",
    ),
    "start_price": _metadata(
        "start_price",
        "pivot price at the leg start",
        "numeric traceability value",
        role="METADATA",
    ),
    "end_price": _metadata(
        "end_price",
        "pivot price at the leg end",
        "numeric traceability value",
        role="METADATA",
    ),
    "owned_candle_count": _metadata(
        "owned_candle_count",
        "number of candles owned by the leg",
        "nonnegative integer count",
        role="METADATA",
    ),
}


DETERMINISTIC_RELATIONS = (
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

# Stable relation metadata is kept separate from feature metadata so identity
# checks cannot be mistaken for statistical feature evidence.
DETERMINISTIC_RELATION_FORMULAS: dict[str, str] = {
    "CLOSE_DISPLACEMENT_ABS": "net_close_displacement = abs(signed_close_displacement)",
    "CONTINUITY_COUNT_SUM": "aligned_close_steps + opposing_close_steps + flat_close_steps = active_bar_count",
    "CONTINUITY_RATIO": "directional_continuity_ratio = aligned_close_steps / active_bar_count",
    "BODY_STRENGTH_RATIO": "body_strength_ratio = gross_body_magnitude / gross_candle_range",
    "GAP_PATH_SHARE": "gap_path_share = gap_path_contribution / gross_close_path",
    "SHADOW_MAGNITUDE_SUM": "gross_shadow_magnitude = gross_forward_shadow + gross_backward_shadow",
    "SHADOW_POSITION_IMBALANCE": "shadow_position_imbalance = (gross_backward_shadow - gross_forward_shadow) / gross_shadow_magnitude",
    "OVERLAP_RATIO": "overlap_ratio = gross_overlap_magnitude / gross_overlap_capacity",
    "SLOPE_DIRECTION": "directional_close_ols_slope = direction_sign * close_ols_slope",
    "SLOPE_NORMALIZATION": "normalized_directional_close_ols_slope = directional_close_ols_slope / mean_candle_range",
    "TICK_ACTIVITY_IDENTITY": "gross_tick_activity = mean_tick_activity * active_bar_count",
}

DETERMINISTIC_RELATION_PARTICIPATING_FEATURES: dict[str, str] = {
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

DETERMINISTIC_RELATION_CONDITIONS: dict[str, str] = {
    "CLOSE_DISPLACEMENT_ABS": "direction_sign in {-1, +1}",
    "CONTINUITY_COUNT_SUM": "always",
    "CONTINUITY_RATIO": "active_bar_count > 0",
    "BODY_STRENGTH_RATIO": "gross_candle_range > 0",
    "GAP_PATH_SHARE": "gross_close_path > 0",
    "SHADOW_MAGNITUDE_SUM": "always",
    "SHADOW_POSITION_IMBALANCE": "gross_shadow_magnitude > 0",
    "OVERLAP_RATIO": "gross_overlap_capacity > 0",
    "SLOPE_DIRECTION": "direction_sign in {-1, +1}",
    "SLOPE_NORMALIZATION": "active_bar_count > 0 and mean_candle_range > 0",
    "TICK_ACTIVITY_IDENTITY": "always",
}

DETERMINISTIC_RELATION_UNDEFINED_WHEN: dict[str, str] = {
    "CLOSE_DISPLACEMENT_ABS": "never (invalid direction_sign is an input error)",
    "CONTINUITY_COUNT_SUM": "never",
    "CONTINUITY_RATIO": "active_bar_count == 0",
    "BODY_STRENGTH_RATIO": "gross_candle_range == 0",
    "GAP_PATH_SHARE": "gross_close_path == 0",
    "SHADOW_MAGNITUDE_SUM": "never",
    "SHADOW_POSITION_IMBALANCE": "gross_shadow_magnitude == 0",
    "OVERLAP_RATIO": "gross_overlap_capacity == 0",
    "SLOPE_DIRECTION": "never (invalid direction_sign is an input error)",
    "SLOPE_NORMALIZATION": "mean_candle_range is None or mean_candle_range <= 0",
    "TICK_ACTIVITY_IDENTITY": "never",
}

# A single named registry is convenient for report builders and keeps the
# relation IDs, formulas, and conditions synchronized in one place.
DETERMINISTIC_REGISTRY: dict[str, dict[str, str]] = {
    relation: {
        "relation": relation,
        "relation_type": "DETERMINISTIC",
        "formula": DETERMINISTIC_RELATION_FORMULAS[relation],
        "participating_features": DETERMINISTIC_RELATION_PARTICIPATING_FEATURES[relation],
        "condition": DETERMINISTIC_RELATION_CONDITIONS[relation],
        "undefined_when": DETERMINISTIC_RELATION_UNDEFINED_WHEN[relation],
        "undefined_result": (
            "None (valid undefined value)"
            if DETERMINISTIC_RELATION_UNDEFINED_WHEN[relation] != "never"
            and not DETERMINISTIC_RELATION_UNDEFINED_WHEN[relation].startswith("never ")
            else "not applicable"
        ),
    }
    for relation in DETERMINISTIC_RELATIONS
}

FEATURE_ROLE_COLUMNS = tuple(FeatureSpec.__dataclass_fields__)


def feature_role_rows() -> list[dict[str, object]]:
    """Return deterministic, CSV-ready copies of every feature role row."""

    return [asdict(spec) for spec in FEATURE_SPECS.values()]


__all__ = [
    "DETERMINISTIC_FLOAT_ABS_TOL",
    "DETERMINISTIC_FLOAT_REL_TOL",
    "DETERMINISTIC_RELATIONS",
    "DETERMINISTIC_RELATION_CONDITIONS",
    "DETERMINISTIC_RELATION_FORMULAS",
    "DETERMINISTIC_RELATION_PARTICIPATING_FEATURES",
    "DETERMINISTIC_RELATION_UNDEFINED_WHEN",
    "DETERMINISTIC_REGISTRY",
    "DIRECTIONS",
    "FEATURE_ROLE_COLUMNS",
    "FEATURE_SPECS",
    "FeatureSpec",
    "MAIN_FEATURES",
    "RAW_DIRECTION_SENSITIVE",
    "TIMEFRAMES",
    "feature_role_rows",
]
