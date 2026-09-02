from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from prototype import visual_leg_inspector as inspector


EXPECTED_FEATURE_FIELDS = (
    "active_bar_count",
    "net_thrust",
    "gross_close_path",
    "net_close_displacement",
    "signed_close_displacement",
    "direction_agreement",
    "directional_efficiency",
    "aligned_close_steps",
    "opposing_close_steps",
    "flat_close_steps",
    "directional_continuity_ratio",
    "close_confirmation_ratio",
    "temporal_profile_tag",
    "gap_path_contribution",
    "gap_path_share",
    "gross_body_magnitude",
    "gross_candle_range",
    "body_strength_ratio",
    "gross_upper_shadow",
    "gross_lower_shadow",
    "gross_forward_shadow",
    "gross_backward_shadow",
    "gross_shadow_magnitude",
    "shadow_position_imbalance",
    "gross_overlap_magnitude",
    "gross_overlap_capacity",
    "overlap_ratio",
    "close_ols_slope",
    "directional_close_ols_slope",
    "normalized_directional_close_ols_slope",
    "gross_tick_activity",
    "mean_tick_activity",
)


@dataclass
class DummyLeg:
    start: dict
    end: dict
    direction: str = "BULLISH"
    active_bar_count: int = 2
    net_thrust: float = 20.0
    gross_close_path: float = 18.0
    net_close_displacement: float = 17.0
    signed_close_displacement: float = 17.0
    direction_agreement: bool = True
    directional_efficiency: float = 17.0 / 18.0
    aligned_close_steps: int = 2
    opposing_close_steps: int = 0
    flat_close_steps: int = 0
    directional_continuity_ratio: float = 1.0
    close_confirmation_ratio: float = 0.85
    temporal_profile_tag: str = "UNDER_SAMPLED"
    gap_path_contribution: float = 0.0
    gap_path_share: float = 0.0
    gross_body_magnitude: float = 12.0
    gross_candle_range: float = 24.0
    body_strength_ratio: float = 0.5
    gross_upper_shadow: float = 4.0
    gross_lower_shadow: float = 8.0
    gross_forward_shadow: float = 4.0
    gross_backward_shadow: float = 8.0
    gross_shadow_magnitude: float = 12.0
    shadow_position_imbalance: float = 1.0 / 3.0
    gross_overlap_magnitude: float = 6.0
    gross_overlap_capacity: float = 10.0
    overlap_ratio: float = 0.6
    close_ols_slope: float = 8.5
    directional_close_ols_slope: float = 8.5
    normalized_directional_close_ols_slope: float = 0.7
    gross_tick_activity: int = 2100
    mean_tick_activity: float = 1050.0


def sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "time": pd.to_datetime([
                "2026-09-01 10:00:00",
                "2026-09-01 10:15:00",
                "2026-09-01 10:30:00",
            ]),
            "open": [3400.0, 3405.0, 3412.0],
            "high": [3408.0, 3415.0, 3422.0],
            "low": [3398.0, 3402.0, 3410.0],
            "close": [3405.0, 3412.0, 3420.0],
            "tick_volume": [900, 1000, 1100],
        }
    )


def test_feature_contract_is_existing_measurements_only():
    assert inspector.LEG_FEATURE_FIELDS == EXPECTED_FEATURE_FIELDS
    forbidden = {"trend", "range", "choppy", "correction", "setup", "entry", "score", "threshold", "weight"}
    assert forbidden.isdisjoint({field.lower() for field in inspector.LEG_FEATURE_FIELDS})


def test_leg_engine_kwargs_forwards_existing_raw_inputs():
    df = sample_df()
    kwargs = inspector.leg_engine_kwargs(df, {2})
    assert kwargs["opens"] == [3400.0, 3405.0, 3412.0]
    assert kwargs["highs"] == [3408.0, 3415.0, 3422.0]
    assert kwargs["lows"] == [3398.0, 3402.0, 3410.0]
    assert kwargs["closes"] == [3405.0, 3412.0, 3420.0]
    assert kwargs["tick_volume"] == [900, 1000, 1100]
    assert kwargs["scheduled_gap_after_indices"] == {2}
    assert "real_volume" not in kwargs


def test_leg_feature_record_contains_identity_times_and_all_existing_metrics():
    df = sample_df()
    leg = DummyLeg(
        start={"index": 0, "kind": "SL", "price": 3400.0},
        end={"index": 2, "kind": "SH", "price": 3420.0},
    )
    record = inspector.leg_feature_record(7, leg, df)
    assert record["leg_no"] == 7
    assert record["direction"] == "BULLISH"
    assert record["start_kind"] == "SL"
    assert record["end_kind"] == "SH"
    assert record["start_time"] == "2026-09-01 10:00:00"
    assert record["end_time"] == "2026-09-01 10:30:00"
    for field in EXPECTED_FEATURE_FIELDS:
        assert field in record
        assert record[field] == getattr(leg, field)


def test_output_paths_are_deterministic_and_auditable(tmp_path: Path):
    html_path, csv_path = inspector.output_paths(tmp_path, "XAUUSD_o", "M15")
    assert html_path.name == "PriceActionAI_Parallel_Leg_Inspector_XAUUSD_o_M15.html"
    assert csv_path.name == "PriceActionAI_Parallel_Leg_Inspector_XAUUSD_o_M15.csv"


def test_inspector_html_contains_manual_click_panel(tmp_path: Path):
    records = [{"leg_no": 1, "direction": "BULLISH", "net_thrust": 10.0}]
    figure = inspector.empty_test_figure_with_leg_trace(records[0])
    out = tmp_path / "inspector.html"
    inspector.write_inspector_html(figure, records, out)
    text = out.read_text(encoding="utf-8")
    assert "Leg Inspector" in text
    assert "plotly_click" in text
    assert "leg-inspector-panel" in text
