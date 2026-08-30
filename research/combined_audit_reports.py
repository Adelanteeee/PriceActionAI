"""Deterministic, non-statistical audit reports for locked Leg identities."""

import math
from collections.abc import Callable, Mapping, Sequence

from research.combined_audit_contract import (
    DETERMINISTIC_FLOAT_ABS_TOL,
    DETERMINISTIC_FLOAT_REL_TOL,
    DETERMINISTIC_REGISTRY,
    DETERMINISTIC_RELATIONS,
)


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
    expected = direction_sign * row["close_ols_slope"]
    return _float_equal(expected, row["directional_close_ols_slope"])


def _slope_normalization(row: Mapping[str, object]) -> bool:
    active_bar_count = row["active_bar_count"]
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
                "formula": metadata["formula"],
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


__all__ = [
    "FLOAT_TOLERANCE_POLICY",
    "build_deterministic_identity_report",
]
