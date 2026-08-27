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
    directional_efficiency: float | None = None


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


def _close_path_metrics(
    closes: Sequence[float] | None,
    start_index: int,
    end_index: int,
) -> tuple[float | None, float | None, float | None]:
    if closes is None:
        return None, None, None

    if start_index < 0 or end_index < start_index or end_index >= len(closes):
        raise IndexError(
            f"Close series does not cover Leg indexes {start_index}->{end_index}; "
            f"len(closes)={len(closes)}"
        )

    segment = [float(closes[i]) for i in range(start_index, end_index + 1)]
    gross_close_path = sum(abs(segment[i] - segment[i - 1]) for i in range(1, len(segment)))
    net_close_displacement = abs(segment[-1] - segment[0])
    directional_efficiency = (
        net_close_displacement / gross_close_path if gross_close_path > 0 else None
    )
    return gross_close_path, net_close_displacement, directional_efficiency


def build_confirmed_legs(
    major_swings: Iterable[dict[str, Any]],
    *,
    closes: Sequence[float] | None = None,
) -> LegBuildResult:
    swings = list(major_swings)
    legs: list[ConfirmedLeg] = []
    errors: list[LegBuildError] = []

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
        gross_close_path, net_close_displacement, directional_efficiency = _close_path_metrics(
            closes,
            start_index,
            end_index,
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
                directional_efficiency=directional_efficiency,
            )
        )

    return LegBuildResult(legs=legs, errors=errors)
