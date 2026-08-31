"""Deterministic and statistical reports for the locked Combined Leg audit."""

import math
from collections.abc import Callable, Mapping, Sequence
from itertools import combinations

from research.combined_audit_contract import (
    DETERMINISTIC_FLOAT_ABS_TOL,
    DETERMINISTIC_FLOAT_REL_TOL,
    DETERMINISTIC_REGISTRY,
    DETERMINISTIC_RELATIONS,
    MAIN_FEATURES,
    RAW_DIRECTION_SENSITIVE,
    TIMEFRAMES,
)
from research.combined_audit_stats import partial_spearman_duration, spearman_pairwise


FLOAT_TOLERANCE_POLICY = (
    f"float: rel_tol={DETERMINISTIC_FLOAT_REL_TOL:g}, "
    f"abs_tol={DETERMINISTIC_FLOAT_ABS_TOL:g}; counts=exact; None=exact"
)


def _float_equal(expected: object, observed: object) -> bool:
    """Compare defined numeric identity values with the locked tolerance."""

    return math.isclose(
        float(expected),
        float(observed),
        rel_tol=DETERMINISTIC_FLOAT_REL_TOL,
        abs_tol=DETERMINISTIC_FLOAT_ABS_TOL,
    )


def _optional_float_equal(expected: object, observed: object) -> bool:
    """Compare optional identity values without treating ``None`` as zero."""

    if expected is None or observed is None:
        return expected is None and observed is None
    return _float_equal(expected, observed)


def _close_displacement_abs(row: Mapping[str, object]) -> bool:
    if row["direction"] not in {"BULLISH", "BEARISH"}:
        return False
    return _float_equal(abs(row["signed_close_displacement"]), row["net_close_displacement"])


def _continuity_count_sum(row: Mapping[str, object]) -> bool:
    expected = (
        row["aligned_close_steps"]
        + row["opposing_close_steps"]
        + row["flat_close_steps"]
    )
    return expected == row["active_bar_count"]


def _continuity_ratio(row: Mapping[str, object]) -> bool:
    active_bar_count = row["active_bar_count"]
    expected = (
        row["aligned_close_steps"] / active_bar_count
        if active_bar_count > 0
        else None
    )
    return _optional_float_equal(expected, row["directional_continuity_ratio"])


def _body_strength_ratio(row: Mapping[str, object]) -> bool:
    gross_candle_range = row["gross_candle_range"]
    expected = (
        row["gross_body_magnitude"] / gross_candle_range
        if gross_candle_range > 0
        else None
    )
    return _optional_float_equal(expected, row["body_strength_ratio"])


def _gap_path_share(row: Mapping[str, object]) -> bool:
    gross_close_path = row["gross_close_path"]
    expected = (
        row["gap_path_contribution"] / gross_close_path
        if gross_close_path > 0
        else None
    )
    return _optional_float_equal(expected, row["gap_path_share"])


def _shadow_magnitude_sum(row: Mapping[str, object]) -> bool:
    expected = row["gross_forward_shadow"] + row["gross_backward_shadow"]
    return _float_equal(expected, row["gross_shadow_magnitude"])


def _shadow_position_imbalance(row: Mapping[str, object]) -> bool:
    gross_shadow_magnitude = row["gross_shadow_magnitude"]
    expected = (
        (row["gross_backward_shadow"] - row["gross_forward_shadow"])
        / gross_shadow_magnitude
        if gross_shadow_magnitude > 0
        else None
    )
    return _optional_float_equal(expected, row["shadow_position_imbalance"])


def _overlap_ratio(row: Mapping[str, object]) -> bool:
    gross_overlap_capacity = row["gross_overlap_capacity"]
    expected = (
        row["gross_overlap_magnitude"] / gross_overlap_capacity
        if gross_overlap_capacity > 0
        else None
    )
    return _optional_float_equal(expected, row["overlap_ratio"])


def _slope_direction(row: Mapping[str, object]) -> bool:
    direction_sign = {"BULLISH": 1, "BEARISH": -1}[row["direction"]]
    if row["active_bar_count"] < 2:
        return (
            row["close_ols_slope"] is None
            and row["directional_close_ols_slope"] is None
        )
    if (
        row["close_ols_slope"] is None
        or row["directional_close_ols_slope"] is None
    ):
        return False
    expected = direction_sign * row["close_ols_slope"]
    return _float_equal(expected, row["directional_close_ols_slope"])


def _slope_normalization(row: Mapping[str, object]) -> bool:
    active_bar_count = row["active_bar_count"]
    if active_bar_count < 2:
        return (
            row["directional_close_ols_slope"] is None
            and row["normalized_directional_close_ols_slope"] is None
        )
    if row["directional_close_ols_slope"] is None:
        return False
    mean_candle_range = (
        row["gross_candle_range"] / active_bar_count
        if active_bar_count > 0
        else None
    )
    expected = (
        row["directional_close_ols_slope"] / mean_candle_range
        if mean_candle_range is not None and mean_candle_range > 0
        else None
    )
    if row["normalized_directional_close_ols_slope"] is None:
        return expected is None
    return _optional_float_equal(expected, row["normalized_directional_close_ols_slope"])


def _tick_activity_identity(row: Mapping[str, object]) -> bool:
    expected = row["mean_tick_activity"] * row["active_bar_count"]
    return _float_equal(expected, row["gross_tick_activity"])


_IDENTITY_HOLDERS: dict[str, Callable[[Mapping[str, object]], bool]] = {
    "CLOSE_DISPLACEMENT_ABS": _close_displacement_abs,
    "CONTINUITY_COUNT_SUM": _continuity_count_sum,
    "CONTINUITY_RATIO": _continuity_ratio,
    "BODY_STRENGTH_RATIO": _body_strength_ratio,
    "GAP_PATH_SHARE": _gap_path_share,
    "SHADOW_MAGNITUDE_SUM": _shadow_magnitude_sum,
    "SHADOW_POSITION_IMBALANCE": _shadow_position_imbalance,
    "OVERLAP_RATIO": _overlap_ratio,
    "SLOPE_DIRECTION": _slope_direction,
    "SLOPE_NORMALIZATION": _slope_normalization,
    "TICK_ACTIVITY_IDENTITY": _tick_activity_identity,
}


def _identity_holds(
    identity_holds: Callable[[Mapping[str, object]], bool], row: Mapping[str, object]
) -> bool:
    """Return a classification for every row, including malformed direct inputs."""

    try:
        return identity_holds(row)
    except (KeyError, TypeError, ValueError, OverflowError, ZeroDivisionError):
        return False


def build_deterministic_identity_report(
    rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    """Audit every input row against every locked deterministic identity.

    This consumer intentionally has no skipped-row state.  Package execution
    supplies complete schema, while direct callers with missing components get
    a counted failure for each affected identity.
    """

    total_rows = len(rows)
    report: list[dict[str, object]] = []
    for relation_id in DETERMINISTIC_RELATIONS:
        identity_holds = _IDENTITY_HOLDERS[relation_id]
        verified_rows = sum(_identity_holds(identity_holds, row) for row in rows)
        failed_rows = total_rows - verified_rows
        assert verified_rows + failed_rows == total_rows

        metadata = DETERMINISTIC_REGISTRY[relation_id]
        report.append(
            {
                "relation_id": relation_id,
                "relation_type": metadata["relation_type"],
                "formula": metadata["formula"],
                "participating_features": metadata["participating_features"],
                "condition": metadata["condition"],
                "undefined_when": metadata["undefined_when"],
                "undefined_result": metadata["undefined_result"],
                "tolerance_policy": FLOAT_TOLERANCE_POLICY,
                "total_rows": total_rows,
                "verified_rows": verified_rows,
                "failed_rows": failed_rows,
            }
        )
    return report


def _column(rows: Sequence[Mapping[str, object]], name: str) -> list[object]:
    """Return a report feature column while retaining missing values."""

    return [row.get(name) for row in rows]


def build_main_spearman_report(
    rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    """Build the frozen pairwise-complete Main Spearman report for one TF."""

    report: list[dict[str, object]] = []
    for feature_x, feature_y in combinations(MAIN_FEATURES, 2):
        result = spearman_pairwise(
            _column(rows, feature_x),
            _column(rows, feature_y),
        )
        report.append(
            {
                "feature_x": feature_x,
                "feature_y": feature_y,
                "n_total": result.n_total,
                "n_valid_pairwise": result.n_valid_pairwise,
                "n_missing_x": result.n_missing_x,
                "n_missing_y": result.n_missing_y,
                "rho_raw": result.rho_raw,
                "status": result.status,
            }
        )
    return report


def build_partial_spearman_report(
    rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    """Build duration-controlled, triple-complete Spearman results for one TF."""

    active_bar_count = _column(rows, "active_bar_count")
    report: list[dict[str, object]] = []
    for feature_x, feature_y in combinations(MAIN_FEATURES[1:], 2):
        result = partial_spearman_duration(
            _column(rows, feature_x),
            _column(rows, feature_y),
            active_bar_count,
        )
        report.append(
            {
                "feature_x": feature_x,
                "feature_y": feature_y,
                "rho_raw_for_delta": result.rho_raw_for_delta,
                "rho_duration_controlled": result.rho_duration_controlled,
                "delta_rho": result.delta_rho,
                "n_valid_triple": result.n_valid_triple,
                "status": result.status,
            }
        )
    return report


def build_direction_stratified_report(
    rows: Sequence[Mapping[str, object]], direction: str
) -> dict[str, object]:
    """Build same-direction supplementary raw and duration-controlled tables.

    The supplementary universe is deliberately broader than the main matrix,
    but remains limited to analysis features and frozen raw direction-sensitive
    fields.  Filtering happens before column extraction so no Bull/Bear values
    can participate in the same statistic.
    """

    eligible = MAIN_FEATURES + RAW_DIRECTION_SENSITIVE
    subset = [row for row in rows if row.get("direction") == direction]

    raw: list[dict[str, object]] = []
    for feature_x, feature_y in combinations(eligible, 2):
        result = spearman_pairwise(
            _column(subset, feature_x),
            _column(subset, feature_y),
        )
        raw.append(
            {
                "feature_x": feature_x,
                "feature_y": feature_y,
                "n_total": result.n_total,
                "n_valid_pairwise": result.n_valid_pairwise,
                "n_missing_x": result.n_missing_x,
                "n_missing_y": result.n_missing_y,
                "rho_raw": result.rho_raw,
                "status": result.status,
                "evidence_scope": "SUPPLEMENTARY_ONLY",
            }
        )

    control = _column(subset, "active_bar_count")
    partial: list[dict[str, object]] = []
    for feature_x, feature_y in combinations(eligible[1:], 2):
        result = partial_spearman_duration(
            _column(subset, feature_x),
            _column(subset, feature_y),
            control,
        )
        partial.append(
            {
                "feature_x": feature_x,
                "feature_y": feature_y,
                "rho_raw_for_delta": result.rho_raw_for_delta,
                "rho_duration_controlled": result.rho_duration_controlled,
                "delta_rho": result.delta_rho,
                "n_valid_triple": result.n_valid_triple,
                "status": result.status,
                "evidence_scope": "SUPPLEMENTARY_ONLY",
            }
        )

    return {
        "source_row_count": len(subset),
        "raw": raw,
        "partial": partial,
    }


def _pair_index(
    reports_by_tf: Mapping[str, Sequence[Mapping[str, object]]],
) -> dict[str, dict[tuple[object, object], Mapping[str, object]]]:
    """Index independently computed report rows by pair, never row position."""

    return {
        timeframe: {
            (row["feature_x"], row["feature_y"]): row
            for row in reports_by_tf.get(timeframe, ())
        }
        for timeframe in TIMEFRAMES
    }


def _cross_tf_pair_order(
    main_index: Mapping[str, Mapping[tuple[object, object], Mapping[str, object]]]
) -> list[tuple[object, object]]:
    """Use frozen main-pair order, with deterministic support for direct inputs."""

    observed_pairs = set().union(*(index.keys() for index in main_index.values()))
    frozen_pairs = list(combinations(MAIN_FEATURES, 2))
    ordered = [pair for pair in frozen_pairs if pair in observed_pairs]
    extra_pairs = sorted(
        observed_pairs - set(frozen_pairs),
        key=lambda pair: (str(pair[0]), str(pair[1])),
    )
    return ordered + extra_pairs


def build_cross_tf_relationship_report(
    main_by_tf: Mapping[str, Sequence[Mapping[str, object]]],
    partial_by_tf: Mapping[str, Sequence[Mapping[str, object]]],
) -> list[dict[str, object]]:
    """Compare independently calculated per-TF pair rows without pooling data."""

    main_index = _pair_index(main_by_tf)
    partial_index = _pair_index(partial_by_tf)
    report: list[dict[str, object]] = []
    for pair_key in _cross_tf_pair_order(main_index):
        feature_x, feature_y = pair_key
        controlled_eligible = "active_bar_count" not in pair_key
        raw_values = [
            main_index[timeframe].get(pair_key, {}).get("rho_raw")
            for timeframe in TIMEFRAMES
        ]
        positive = sum(value is not None and value > 0 for value in raw_values)
        negative = sum(value is not None and value < 0 for value in raw_values)
        zero = sum(value is not None and value == 0 for value in raw_values)
        undefined = sum(value is None for value in raw_values)
        defined_values = [value for value in raw_values if value is not None]

        if defined_values:
            sign_counts = {
                "NEGATIVE": negative,
                "POSITIVE": positive,
                "ZERO": zero,
            }
            agreement_count = max(sign_counts.values())
            modal_signs = [
                sign for sign, count in sign_counts.items() if count == agreement_count
            ]
            sign_agreement_tie: bool | None = len(modal_signs) > 1
            rho_min: object = min(defined_values)
            rho_max: object = max(defined_values)
            rho_range: object = rho_max - rho_min
        else:
            agreement_count = None
            sign_agreement_tie = None
            modal_signs = None
            rho_min = None
            rho_max = None
            rho_range = None

        row: dict[str, object] = {
            "feature_x": feature_x,
            "feature_y": feature_y,
            "controlled_eligible": controlled_eligible,
            "n_positive_tf": positive,
            "n_negative_tf": negative,
            "n_zero_tf": zero,
            "n_undefined_tf": undefined,
            "sign_agreement_count": agreement_count,
            "sign_agreement_tie": sign_agreement_tie,
            "sign_agreement_modal_signs": modal_signs,
            "rho_min": rho_min,
            "rho_max": rho_max,
            "rho_range": rho_range,
        }
        for timeframe in TIMEFRAMES:
            main_row = main_index[timeframe].get(pair_key)
            partial_row = partial_index[timeframe].get(pair_key)
            row[f"rho_{timeframe}"] = (
                main_row.get("rho_raw") if main_row is not None else None
            )
            row[f"n_valid_{timeframe}"] = (
                main_row.get("n_valid_pairwise") if main_row is not None else None
            )
            row[f"controlled_rho_{timeframe}"] = (
                partial_row.get("rho_duration_controlled")
                if controlled_eligible and partial_row is not None
                else None
            )
        report.append(row)
    return report


__all__ = [
    "FLOAT_TOLERANCE_POLICY",
    "build_deterministic_identity_report",
    "build_direction_stratified_report",
    "build_cross_tf_relationship_report",
    "build_main_spearman_report",
    "build_partial_spearman_report",
]
