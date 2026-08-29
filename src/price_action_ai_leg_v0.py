from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence

UPSTREAM_SWING_INVARIANT_ERROR = "UPSTREAM_SWING_INVARIANT_ERROR"


@dataclass(frozen=True)
class ConfirmedLeg:
    start: dict[str, Any]
    end: dict[str, Any]
    direction: str
    active_bar_count: int
    net_thrust: float
    gross_close_path: float | None = None
    net_close_displacement: float | None = None
    signed_close_displacement: float | None = None
    direction_agreement: bool | None = None
    directional_efficiency: float | None = None
    aligned_close_steps: int | None = None
    opposing_close_steps: int | None = None
    flat_close_steps: int | None = None
    directional_continuity_ratio: float | None = None
    close_confirmation_ratio: float | None = None
    temporal_profile_tag: str | None = None
    gap_path_contribution: float | None = None
    gap_path_share: float | None = None
    gross_body_magnitude: float | None = None
    gross_candle_range: float | None = None
    body_strength_ratio: float | None = None
    gross_upper_shadow: float | None = None
    gross_lower_shadow: float | None = None
    gross_forward_shadow: float | None = None
    gross_backward_shadow: float | None = None
    gross_shadow_magnitude: float | None = None
    shadow_position_imbalance: float | None = None


@dataclass(frozen=True)
class LegBuildError:
    code: str
    pair_index: int
    left: dict[str, Any]
    right: dict[str, Any]


@dataclass(frozen=True)
class LegBuildResult:
    legs: list[ConfirmedLeg]
    errors: list[LegBuildError]


def _direction_for_pair(left_kind: str, right_kind: str) -> str:
    if left_kind == "SL" and right_kind == "SH":
        return "BULLISH"
    if left_kind == "SH" and right_kind == "SL":
        return "BEARISH"
    raise ValueError(f"Unsupported Major Swing pair: {left_kind}->{right_kind}")


def _temporal_profile(active_bar_count: int) -> str:
    if active_bar_count <= 3:
        return "UNDER_SAMPLED"
    if active_bar_count <= 15:
        return "NORMAL_TEMPORAL_PROFILE"
    return "HIGHER_TF_CANDIDATE"


def _close_path_metrics(
    closes: Sequence[float] | None,
    start_index: int,
    end_index: int,
    direction: str,
    scheduled_gap_after_indices: set[int],
):
    if closes is None:
        return (None,) * 11
    if start_index < 0 or end_index < start_index or end_index >= len(closes):
        raise IndexError(
            f"Close series does not cover Leg indexes {start_index}->{end_index}; len(closes)={len(closes)}"
        )

    segment = [float(closes[i]) for i in range(start_index, end_index + 1)]
    close_steps = [segment[i] - segment[i - 1] for i in range(1, len(segment))]
    steps = [abs(step) for step in close_steps]
    gross_close_path = sum(steps)
    raw_close_change = segment[-1] - segment[0]
    net_close_displacement = abs(raw_close_change)
    direction_sign = 1.0 if direction == "BULLISH" else -1.0
    signed_close_displacement = direction_sign * raw_close_change
    direction_agreement = signed_close_displacement > 0.0
    directional_efficiency = (
        min(1.0, max(0.0, signed_close_displacement) / gross_close_path)
        if gross_close_path > 0
        else None
    )

    directional_steps = [direction_sign * step for step in close_steps]
    aligned_close_steps = sum(1 for step in directional_steps if step > 0.0)
    opposing_close_steps = sum(1 for step in directional_steps if step < 0.0)
    flat_close_steps = sum(1 for step in directional_steps if step == 0.0)
    total_close_steps = aligned_close_steps + opposing_close_steps + flat_close_steps
    expected_close_steps = end_index - start_index
    if total_close_steps != expected_close_steps:
        raise AssertionError(
            "Directional Continuity invariant failed: "
            f"{total_close_steps} classified close steps != {expected_close_steps} active bars"
        )
    directional_continuity_ratio = (
        aligned_close_steps / total_close_steps if total_close_steps > 0 else None
    )

    gap_path_contribution = 0.0
    for current_index in range(start_index + 1, end_index + 1):
        if current_index in scheduled_gap_after_indices:
            gap_path_contribution += abs(
                float(closes[current_index]) - float(closes[current_index - 1])
            )
    gap_path_share = (
        gap_path_contribution / gross_close_path if gross_close_path > 0 else None
    )

    return (
        gross_close_path,
        net_close_displacement,
        signed_close_displacement,
        direction_agreement,
        directional_efficiency,
        gap_path_contribution,
        gap_path_share,
        aligned_close_steps,
        opposing_close_steps,
        flat_close_steps,
        directional_continuity_ratio,
    )


def _body_strength_metrics(
    opens: Sequence[float] | None,
    highs: Sequence[float] | None,
    lows: Sequence[float] | None,
    closes: Sequence[float] | None,
    start_index: int,
    end_index: int,
):
    if opens is None or highs is None or lows is None or closes is None:
        return None, None, None
    if not (len(opens) == len(highs) == len(lows) == len(closes)):
        raise ValueError("OHLC series lengths must match")
    if start_index < 0 or end_index < start_index or end_index >= len(closes):
        raise IndexError(
            f"OHLC series does not cover Leg indexes {start_index}->{end_index}; len={len(closes)}"
        )

    owned_indices = range(start_index + 1, end_index + 1)
    gross_body_magnitude = sum(
        abs(float(closes[i]) - float(opens[i])) for i in owned_indices
    )
    gross_candle_range = sum(
        float(highs[i]) - float(lows[i])
        for i in range(start_index + 1, end_index + 1)
    )
    body_strength_ratio = (
        gross_body_magnitude / gross_candle_range
        if gross_candle_range > 0.0
        else None
    )
    return gross_body_magnitude, gross_candle_range, body_strength_ratio


def _shadow_position_metrics(
    opens: Sequence[float] | None,
    highs: Sequence[float] | None,
    lows: Sequence[float] | None,
    closes: Sequence[float] | None,
    start_index: int,
    end_index: int,
    direction: str,
):
    if opens is None or highs is None or lows is None or closes is None:
        return (None,) * 6
    if not (len(opens) == len(highs) == len(lows) == len(closes)):
        raise ValueError("OHLC series lengths must match")
    if start_index < 0 or end_index < start_index or end_index >= len(closes):
        raise IndexError(
            f"OHLC series does not cover Leg indexes {start_index}->{end_index}; len={len(closes)}"
        )

    gross_upper_shadow = 0.0
    gross_lower_shadow = 0.0
    for i in range(start_index + 1, end_index + 1):
        open_i = float(opens[i])
        high_i = float(highs[i])
        low_i = float(lows[i])
        close_i = float(closes[i])
        gross_upper_shadow += high_i - max(open_i, close_i)
        gross_lower_shadow += min(open_i, close_i) - low_i

    if direction == "BULLISH":
        gross_forward_shadow = gross_upper_shadow
        gross_backward_shadow = gross_lower_shadow
    else:
        gross_forward_shadow = gross_lower_shadow
        gross_backward_shadow = gross_upper_shadow

    gross_shadow_magnitude = gross_forward_shadow + gross_backward_shadow
    shadow_position_imbalance = (
        (gross_backward_shadow - gross_forward_shadow) / gross_shadow_magnitude
        if gross_shadow_magnitude > 0.0
        else None
    )
    return (
        gross_upper_shadow,
        gross_lower_shadow,
        gross_forward_shadow,
        gross_backward_shadow,
        gross_shadow_magnitude,
        shadow_position_imbalance,
    )


def build_confirmed_legs(
    major_swings: Iterable[dict[str, Any]],
    *,
    opens: Sequence[float] | None = None,
    highs: Sequence[float] | None = None,
    lows: Sequence[float] | None = None,
    closes: Sequence[float] | None = None,
    scheduled_gap_after_indices: Iterable[int] | None = None,
) -> LegBuildResult:
    swings = list(major_swings)
    legs: list[ConfirmedLeg] = []
    errors: list[LegBuildError] = []
    gap_indices = {int(i) for i in (scheduled_gap_after_indices or [])}

    for pair_index, (left, right) in enumerate(zip(swings[:-1], swings[1:])):
        left_kind = str(left["kind"]).upper()
        right_kind = str(right["kind"]).upper()

        if left_kind == right_kind:
            errors.append(
                LegBuildError(
                    code=UPSTREAM_SWING_INVARIANT_ERROR,
                    pair_index=pair_index,
                    left=left,
                    right=right,
                )
            )
            continue

        direction = _direction_for_pair(left_kind, right_kind)
        start_index = int(left["index"])
        end_index = int(right["index"])
        active_bar_count = end_index - start_index
        net_thrust = abs(float(right["price"]) - float(left["price"]))

        (
            gross_close_path,
            net_close_displacement,
            signed_close_displacement,
            direction_agreement,
            directional_efficiency,
            gap_path_contribution,
            gap_path_share,
            aligned_close_steps,
            opposing_close_steps,
            flat_close_steps,
            directional_continuity_ratio,
        ) = _close_path_metrics(
            closes,
            start_index,
            end_index,
            direction,
            gap_indices,
        )

        close_confirmation_ratio = (
            max(0.0, signed_close_displacement) / net_thrust
            if signed_close_displacement is not None and net_thrust > 0
            else None
        )

        (
            gross_body_magnitude,
            gross_candle_range,
            body_strength_ratio,
        ) = _body_strength_metrics(
            opens,
            highs,
            lows,
            closes,
            start_index,
            end_index,
        )

        (
            gross_upper_shadow,
            gross_lower_shadow,
            gross_forward_shadow,
            gross_backward_shadow,
            gross_shadow_magnitude,
            shadow_position_imbalance,
        ) = _shadow_position_metrics(
            opens,
            highs,
            lows,
            closes,
            start_index,
            end_index,
            direction,
        )

        legs.append(
            ConfirmedLeg(
                start=left,
                end=right,
                direction=direction,
                active_bar_count=active_bar_count,
                net_thrust=net_thrust,
                gross_close_path=gross_close_path,
                net_close_displacement=net_close_displacement,
                signed_close_displacement=signed_close_displacement,
                direction_agreement=direction_agreement,
                directional_efficiency=directional_efficiency,
                aligned_close_steps=aligned_close_steps,
                opposing_close_steps=opposing_close_steps,
                flat_close_steps=flat_close_steps,
                directional_continuity_ratio=directional_continuity_ratio,
                close_confirmation_ratio=close_confirmation_ratio,
                temporal_profile_tag=_temporal_profile(active_bar_count),
                gap_path_contribution=gap_path_contribution,
                gap_path_share=gap_path_share,
                gross_body_magnitude=gross_body_magnitude,
                gross_candle_range=gross_candle_range,
                body_strength_ratio=body_strength_ratio,
                gross_upper_shadow=gross_upper_shadow,
                gross_lower_shadow=gross_lower_shadow,
                gross_forward_shadow=gross_forward_shadow,
                gross_backward_shadow=gross_backward_shadow,
                gross_shadow_magnitude=gross_shadow_magnitude,
                shadow_position_imbalance=shadow_position_imbalance,
            )
        )

    return LegBuildResult(legs=legs, errors=errors)
