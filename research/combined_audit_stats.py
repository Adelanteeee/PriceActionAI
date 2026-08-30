"""Deterministic statistical primitives for the combined audit."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence


DEFINED = "DEFINED"
UNDEFINED_INSUFFICIENT_OBSERVATIONS = "UNDEFINED_INSUFFICIENT_OBSERVATIONS"
UNDEFINED_CONSTANT_INPUT = "UNDEFINED_CONSTANT_INPUT"


@dataclass(frozen=True)
class RawSpearmanResult:
    n_total: int
    n_valid_pairwise: int
    n_missing_x: int
    n_missing_y: int
    rho_raw: float | None
    status: str


@dataclass(frozen=True)
class PartialSpearmanResult:
    n_valid_triple: int
    rho_raw_for_delta: float | None
    rho_duration_controlled: float | None
    delta_rho: float | None
    status: str


def average_ranks(values: Sequence[float]) -> list[float]:
    order = sorted(range(len(values)), key=values.__getitem__)
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i + 1
        while j < len(order) and values[order[j]] == values[order[i]]:
            j += 1
        average_rank = ((i + 1) + j) / 2.0
        for k in range(i, j):
            ranks[order[k]] = average_rank
        i = j
    return ranks


def pearson(values_x: Sequence[float], values_y: Sequence[float]) -> float:
    mean_x = sum(values_x) / len(values_x)
    mean_y = sum(values_y) / len(values_y)
    deltas_x = [value - mean_x for value in values_x]
    deltas_y = [value - mean_y for value in values_y]
    numerator = sum(a * b for a, b in zip(deltas_x, deltas_y))
    denominator = math.sqrt(
        sum(value * value for value in deltas_x)
        * sum(value * value for value in deltas_y)
    )
    return numerator / denominator


def spearman_pairwise(
    values_x: Sequence[float | int | None],
    values_y: Sequence[float | int | None],
) -> RawSpearmanResult:
    pairs = [
        (value_x, value_y)
        for value_x, value_y in zip(values_x, values_y)
        if value_x is not None and value_y is not None
    ]
    n_valid_pairwise = len(pairs)
    n_missing_x = sum(value is None for value in values_x)
    n_missing_y = sum(value is None for value in values_y)
    if n_valid_pairwise < 2:
        return RawSpearmanResult(
            n_total=len(values_x),
            n_valid_pairwise=n_valid_pairwise,
            n_missing_x=n_missing_x,
            n_missing_y=n_missing_y,
            rho_raw=None,
            status=UNDEFINED_INSUFFICIENT_OBSERVATIONS,
        )

    ranked_x = average_ranks([float(value_x) for value_x, _ in pairs])
    ranked_y = average_ranks([float(value_y) for _, value_y in pairs])
    if len(set(ranked_x)) == 1 or len(set(ranked_y)) == 1:
        return RawSpearmanResult(
            n_total=len(values_x),
            n_valid_pairwise=n_valid_pairwise,
            n_missing_x=n_missing_x,
            n_missing_y=n_missing_y,
            rho_raw=None,
            status=UNDEFINED_CONSTANT_INPUT,
        )

    return RawSpearmanResult(
        n_total=len(values_x),
        n_valid_pairwise=n_valid_pairwise,
        n_missing_x=n_missing_x,
        n_missing_y=n_missing_y,
        rho_raw=pearson(ranked_x, ranked_y),
        status=DEFINED,
    )


def residuals_on_control(
    values: Sequence[float], control: Sequence[float]
) -> list[float]:
    mean_values = sum(values) / len(values)
    mean_control = sum(control) / len(control)
    centered_control = [value - mean_control for value in control]
    denominator = sum(value * value for value in centered_control)
    slope = sum(
        (value - mean_values) * centered
        for value, centered in zip(values, centered_control)
    ) / denominator
    intercept = mean_values - slope * mean_control
    return [
        value - (intercept + slope * control_value)
        for value, control_value in zip(values, control)
    ]


def partial_spearman_duration(
    values_x: Sequence[float | int | None],
    values_y: Sequence[float | int | None],
    active_bar_count: Sequence[float | int | None],
) -> PartialSpearmanResult:
    triples = [
        (value_x, value_y, duration)
        for value_x, value_y, duration in zip(values_x, values_y, active_bar_count)
        if value_x is not None and value_y is not None and duration is not None
    ]
    n_valid_triple = len(triples)
    if n_valid_triple < 3:
        return PartialSpearmanResult(
            n_valid_triple=n_valid_triple,
            rho_raw_for_delta=None,
            rho_duration_controlled=None,
            delta_rho=None,
            status=UNDEFINED_INSUFFICIENT_OBSERVATIONS,
        )

    triple_x = [float(value_x) for value_x, _, _ in triples]
    triple_y = [float(value_y) for _, value_y, _ in triples]
    triple_duration = [float(duration) for _, _, duration in triples]
    ranked_x = average_ranks(triple_x)
    ranked_y = average_ranks(triple_y)
    ranked_duration = average_ranks(triple_duration)
    if (
        len(set(ranked_x)) == 1
        or len(set(ranked_y)) == 1
        or len(set(ranked_duration)) == 1
    ):
        return PartialSpearmanResult(
            n_valid_triple=n_valid_triple,
            rho_raw_for_delta=None,
            rho_duration_controlled=None,
            delta_rho=None,
            status=UNDEFINED_CONSTANT_INPUT,
        )

    residual_x = residuals_on_control(ranked_x, ranked_duration)
    residual_y = residuals_on_control(ranked_y, ranked_duration)
    if len(set(residual_x)) == 1 or len(set(residual_y)) == 1:
        return PartialSpearmanResult(
            n_valid_triple=n_valid_triple,
            rho_raw_for_delta=None,
            rho_duration_controlled=None,
            delta_rho=None,
            status=UNDEFINED_CONSTANT_INPUT,
        )

    rho_raw_for_delta = spearman_pairwise(triple_x, triple_y).rho_raw
    rho_duration_controlled = pearson(residual_x, residual_y)
    return PartialSpearmanResult(
        n_valid_triple=n_valid_triple,
        rho_raw_for_delta=rho_raw_for_delta,
        rho_duration_controlled=rho_duration_controlled,
        delta_rho=rho_duration_controlled - rho_raw_for_delta,
        status=DEFINED,
    )
