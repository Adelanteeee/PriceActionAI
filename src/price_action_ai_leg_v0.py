from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


UPSTREAM_SWING_INVARIANT_ERROR = "UPSTREAM_SWING_INVARIANT_ERROR"


@dataclass(frozen=True)
class ConfirmedLeg:
    start: dict[str, Any]
    end: dict[str, Any]
    direction: str
    active_bar_count: int
    net_thrust: float


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


def build_confirmed_legs(major_swings: Iterable[dict[str, Any]]) -> LegBuildResult:
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
        active_bar_count = int(right["index"]) - int(left["index"])
        net_thrust = abs(float(right["price"]) - float(left["price"]))

        legs.append(
            ConfirmedLeg(
                start=left,
                end=right,
                direction=direction,
                active_bar_count=active_bar_count,
                net_thrust=net_thrust,
            )
        )

    return LegBuildResult(legs=legs, errors=errors)
