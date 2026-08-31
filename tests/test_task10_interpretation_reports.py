from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

import pytest

from research.combined_audit_contract import FEATURE_SPECS, MAIN_FEATURES, TIMEFRAMES
from research.task10_interpretation_contract import (
    CONTROL_FEATURE,
    CONTROL_NOT_APPLICABLE,
    MAIN_PAIR_KEYS,
    PARTIAL_PAIR_KEYS,
    pair_key,
    validate_observation_text,
)
from research.task10_interpretation_io import Task9EvidenceBundle
from research.task10_interpretation_reports import (
    build_main_relationship_dossiers,
    build_neutral_observations,
)


REQUIRED_MAIN_DOSSIER_FIELDS = {
    "pair_key",
    "source_pair_key",
    "feature_x",
    "feature_y",
    "feature_x_analysis_role",
    "feature_y_analysis_role",
    "feature_x_formula",
    "feature_y_formula",
    "feature_x_direction_semantics",
    "feature_y_direction_semantics",
    "direct_deterministic_dependency",
    "direct_deterministic_relation_ids",
    "raw_source_artifact_by_tf",
    "raw_source_row_locator_by_tf",
    "partial_source_artifact_by_tf",
    "partial_source_row_locator_by_tf",
    "cross_tf_source_artifact",
    "cross_tf_source_row_locator",
    "partial_applicability",
    "raw_by_tf",
    "partial_by_tf",
    "cross_tf",
    "deterministic_context",
    "observations",
}


def _bundle() -> Task9EvidenceBundle:
    roles = tuple(asdict(FEATURE_SPECS[feature]) for feature in FEATURE_SPECS)
    raw_by_tf = {}
    partial_by_tf = {}
    cross_tf = []
    for pair in MAIN_PAIR_KEYS:
        values = []
        for index, timeframe in enumerate(TIMEFRAMES):
            rho = (index - 1) / 10
            values.append(rho)
            raw_by_tf.setdefault(timeframe, []).append(
                {
                    "feature_x": pair[0], "feature_y": pair[1], "n_total": 15,
                    "n_valid_pairwise": 10 + index, "n_missing_x": 2,
                    "n_missing_y": 3, "rho_raw": rho, "status": "DEFINED",
                }
            )
            if pair in PARTIAL_PAIR_KEYS:
                partial_by_tf.setdefault(timeframe, []).append(
                    {
                        "feature_x": pair[0], "feature_y": pair[1],
                        "rho_raw_for_delta": rho,
                        "rho_duration_controlled": rho / 2,
                        "delta_rho": rho / 2,
                        "n_valid_triple": 9 + index, "status": "DEFINED",
                    }
                )
            else:
                partial_by_tf.setdefault(timeframe, [])
        cross_tf.append(
            {
                "feature_x": pair[0], "feature_y": pair[1],
                "controlled_eligible": "True" if pair in PARTIAL_PAIR_KEYS else "False",
                **{f"rho_{timeframe}": values[index] for index, timeframe in enumerate(TIMEFRAMES)},
                **{f"controlled_rho_{timeframe}": values[index] / 2 if pair in PARTIAL_PAIR_KEYS else None for index, timeframe in enumerate(TIMEFRAMES)},
                **{f"n_valid_{timeframe}": 10 + index for index, timeframe in enumerate(TIMEFRAMES)},
                "n_positive_tf": 2, "n_negative_tf": 1, "n_zero_tf": 1,
                "n_undefined_tf": 0, "sign_agreement_count": 2,
                "sign_agreement_tie": "False", "sign_agreement_modal_signs": '["POSITIVE"]',
                "rho_min": -0.1, "rho_max": 0.2, "rho_range": 0.30000000000000004,
            }
        )
    deterministic_rows = tuple(
        {
            "timeframe": timeframe, "relation_id": "SLOPE_NORMALIZATION",
            "participating_features": json.dumps([
                "active_bar_count", "gross_candle_range",
                "directional_close_ols_slope", "normalized_directional_close_ols_slope",
            ]),
        }
        for timeframe in TIMEFRAMES
    )
    return Task9EvidenceBundle(
        feature_roles=roles,
        deterministic_rows=deterministic_rows,
        main_raw_by_tf=raw_by_tf,
        partial_by_tf=partial_by_tf,
        supplementary_by_tf_direction={},
        cross_tf=tuple(cross_tf),
        manifest={},
        evidence_zip_sha256="synthetic",
    )


def test_build_main_dossiers_have_required_fields_and_locked_applicability_counts():
    dossiers = build_main_relationship_dossiers(_bundle())

    assert len(dossiers) == 78
    assert all(REQUIRED_MAIN_DOSSIER_FIELDS <= dossier.keys() for dossier in dossiers)
    assert sum(dossier["partial_applicability"] == "ELIGIBLE" for dossier in dossiers) == 66
    assert sum(dossier["partial_applicability"] == CONTROL_NOT_APPLICABLE for dossier in dossiers) == 12


def test_dossiers_copy_source_values_traceability_and_frozen_observations():
    dossiers = build_main_relationship_dossiers(_bundle())
    pair = pair_key("active_bar_count", "normalized_directional_close_ols_slope")
    dossier = next(item for item in dossiers if item["pair_key"] == pair)

    assert dossier["source_pair_key"] == pair
    assert dossier["feature_x_analysis_role"] == "ANALYSIS_FEATURE"
    assert dossier["feature_x_formula"] == FEATURE_SPECS["active_bar_count"].formula
    assert dossier["raw_source_artifact_by_tf"] == {
        tf: f"MAIN_SPEARMAN_{tf}.csv" for tf in TIMEFRAMES
    }
    assert dossier["raw_source_row_locator_by_tf"] == {
        tf: f"MAIN_SPEARMAN_{tf}.csv#{pair}" for tf in TIMEFRAMES
    }
    assert dossier["partial_source_artifact_by_tf"] == {tf: None for tf in TIMEFRAMES}
    assert dossier["partial_source_row_locator_by_tf"] == {
        tf: CONTROL_NOT_APPLICABLE for tf in TIMEFRAMES
    }
    assert dossier["cross_tf_source_artifact"] == "CROSS_TF_RELATIONSHIP_REPORT.csv"
    assert dossier["cross_tf_source_row_locator"] == (
        f"CROSS_TF_RELATIONSHIP_REPORT.csv#{pair}"
    )
    assert dossier["raw_by_tf"]["M15"]["rho_raw"] == 0.0
    assert dossier["partial_by_tf"]["M5"] == {
        "rho_raw_for_delta": None, "rho_duration_controlled": None,
        "delta_rho": None, "n_valid_triple": None,
        "status": CONTROL_NOT_APPLICABLE,
    }
    assert dossier["direct_deterministic_dependency"] is True
    assert dossier["direct_deterministic_relation_ids"] == ["SLOPE_NORMALIZATION"]
    assert dossier["observations"] == build_neutral_observations(dossier)
    assert dossier["observations"][2:6] == [
        "M5 RAW rho=-0.1 status=DEFINED n_valid_pairwise=10",
        "M15 RAW rho=0.0 status=DEFINED n_valid_pairwise=11",
        "M30 RAW rho=0.1 status=DEFINED n_valid_pairwise=12",
        "H1 RAW rho=0.2 status=DEFINED n_valid_pairwise=13",
    ]
    assert dossier["observations"][6:] == [
        f"{tf} CONTROLLED NOT_APPLICABLE_CONTROL_FEATURE" for tf in TIMEFRAMES
    ]
    for observation in dossier["observations"]:
        validate_observation_text(observation)

    eligible = next(item for item in dossiers if item["pair_key"] == pair_key("net_thrust", "gross_close_path"))
    assert eligible["partial_source_row_locator_by_tf"]["M5"] == (
        f"PARTIAL_SPEARMAN_M5.csv#{eligible['source_pair_key']}"
    )
    assert eligible["partial_by_tf"]["H1"] == {
        "feature_x": "net_thrust", "feature_y": "gross_close_path",
        "rho_raw_for_delta": 0.2, "rho_duration_controlled": 0.1,
        "delta_rho": 0.1, "n_valid_triple": 12, "status": "DEFINED",
    }
    assert eligible["observations"][6:] == [
        "M5 CONTROLLED rho_raw_for_delta=-0.1 rho_duration_controlled=-0.05 delta_rho=-0.05 status=DEFINED n_valid_triple=9",
        "M15 CONTROLLED rho_raw_for_delta=0.0 rho_duration_controlled=0.0 delta_rho=0.0 status=DEFINED n_valid_triple=10",
        "M30 CONTROLLED rho_raw_for_delta=0.1 rho_duration_controlled=0.05 delta_rho=0.05 status=DEFINED n_valid_triple=11",
        "H1 CONTROLLED rho_raw_for_delta=0.2 rho_duration_controlled=0.1 delta_rho=0.1 status=DEFINED n_valid_triple=12",
    ]


def test_raw_status_injection_is_rejected_before_observation_interpolation():
    bundle = _bundle()
    bundle.main_raw_by_tf["M5"][0]["status"] = "REDUNDANT"

    with pytest.raises(ValueError, match="raw status"):
        build_main_relationship_dossiers(bundle)


def test_eligible_controlled_status_injection_is_rejected_before_observation_interpolation():
    bundle = _bundle()
    bundle.partial_by_tf["M5"][0]["status"] = "arbitrary injected status"

    with pytest.raises(ValueError, match="controlled status"):
        build_main_relationship_dossiers(bundle)


def test_task10_reports_do_not_recompute_task9_statistics():
    text = Path("research/task10_interpretation_reports.py").read_text("utf-8")
    assert "spearman_pairwise(" not in text
    assert "partial_spearman_duration(" not in text
