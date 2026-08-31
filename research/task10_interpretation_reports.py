"""Traceable Task 10 relationship dossiers built only from locked Task 9 rows."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence

from research.combined_audit_contract import (
    DIRECTIONS,
    MAIN_FEATURES,
    RAW_DIRECTION_SENSITIVE,
    TIMEFRAMES,
)
from research.task10_interpretation_contract import (
    CONTROL_FEATURE,
    CONTROL_NOT_APPLICABLE,
    MAIN_PAIR_KEYS,
    PARTIAL_PAIR_KEYS,
    SUPPLEMENTARY_OUTPUT_FIELDS,
    SUPPLEMENTARY_PAIR_KEYS,
    pair_key,
    validate_observation_text,
)
from research.task10_interpretation_io import Task9EvidenceBundle


_ELIGIBLE = "ELIGIBLE"
_LOCKED_STATISTICAL_STATUSES = frozenset(
    {
        "DEFINED",
        "UNDEFINED_INSUFFICIENT_OBSERVATIONS",
        "UNDEFINED_CONSTANT_INPUT",
    }
)
_CONTROL_PARTIAL = {
    "rho_raw_for_delta": None,
    "rho_duration_controlled": None,
    "delta_rho": None,
    "n_valid_triple": None,
    "status": CONTROL_NOT_APPLICABLE,
}


def _pair_index(
    rows: Sequence[Mapping[str, object]], *, source: str
) -> dict[str, Mapping[str, object]]:
    indexed: dict[str, Mapping[str, object]] = {}
    for row in rows:
        try:
            key = pair_key(str(row["feature_x"]), str(row["feature_y"]))
        except KeyError as exc:
            raise ValueError(f"{source} row is missing a feature key") from exc
        if key in indexed:
            raise ValueError(f"{source} contains duplicate pair {key}")
        indexed[key] = row
    return indexed


def _feature_roles(bundle: Task9EvidenceBundle) -> dict[str, Mapping[str, object]]:
    roles: dict[str, Mapping[str, object]] = {}
    for row in bundle.feature_roles:
        try:
            feature = row["feature"]
        except KeyError as exc:
            raise ValueError("Task 9 feature role row is missing feature") from exc
        if not isinstance(feature, str) or feature in roles:
            raise ValueError("Task 9 feature role rows must have unique feature names")
        required = ("analysis_role", "formula", "direction_semantics")
        if any(field not in row for field in required):
            raise ValueError(f"Task 9 feature role row for {feature} is incomplete")
        roles[feature] = row
    for feature in {item for pair in MAIN_PAIR_KEYS for item in pair}:
        if feature not in roles or roles[feature]["analysis_role"] != "ANALYSIS_FEATURE":
            raise ValueError(f"main feature {feature} must be an ANALYSIS_FEATURE")
    return roles


def _relation_participants(bundle: Task9EvidenceBundle) -> dict[str, frozenset[str]]:
    participants_by_relation: dict[str, frozenset[str]] = {}
    for row in bundle.deterministic_rows:
        try:
            relation_id = row["relation_id"]
            encoded = row["participating_features"]
        except KeyError as exc:
            raise ValueError("Task 9 deterministic row is incomplete") from exc
        if not isinstance(relation_id, str) or not isinstance(encoded, str):
            raise ValueError("Task 9 deterministic relation metadata is malformed")
        try:
            parsed = json.loads(encoded)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Task 9 deterministic relation {relation_id} has invalid participants") from exc
        if not isinstance(parsed, list) or any(not isinstance(item, str) for item in parsed):
            raise ValueError(f"Task 9 deterministic relation {relation_id} has invalid participants")
        participants = frozenset(parsed)
        previous = participants_by_relation.setdefault(relation_id, participants)
        if previous != participants:
            raise ValueError(f"Task 9 deterministic relation {relation_id} participants drift by timeframe")
    return participants_by_relation


def _audit_cross_tf(cross: Mapping[str, object]) -> None:
    raw_values = [cross[f"rho_{timeframe}"] for timeframe in TIMEFRAMES]
    defined = [value for value in raw_values if value is not None]
    n_defined_tf = len(defined)
    if n_defined_tf + cross["n_undefined_tf"] != len(TIMEFRAMES):
        raise ValueError("Task 9 cross-timeframe defined count is inconsistent")
    if not defined:
        expected = (None, None, None)
    else:
        expected = (min(defined), max(defined), max(defined) - min(defined))
    if (cross["rho_min"], cross["rho_max"], cross["rho_range"]) != expected:
        raise ValueError("Task 9 cross-timeframe range is inconsistent")


def _validate_source_statuses(
    indexes: Mapping[str, Mapping[str, Mapping[str, object]]], *, kind: str
) -> None:
    for timeframe, rows in indexes.items():
        for source_pair_key, row in rows.items():
            if row.get("status") not in _LOCKED_STATISTICAL_STATUSES:
                raise ValueError(
                    f"Task 9 {kind} status is not locked for "
                    f"{timeframe}#{source_pair_key}"
                )


def build_neutral_observations(dossier: Mapping[str, object]) -> list[str]:
    """Return frozen-order, exact-value descriptions for one main dossier."""

    cross = dossier["cross_tf"]
    raw_by_tf = dossier["raw_by_tf"]
    partial_by_tf = dossier["partial_by_tf"]
    if not isinstance(cross, Mapping) or not isinstance(raw_by_tf, Mapping) or not isinstance(partial_by_tf, Mapping):
        raise ValueError("dossier is missing source-value mappings")
    observations = [
        (
            "RAW_SIGN_COUNTS "
            f"positive={cross['n_positive_tf']} "
            f"negative={cross['n_negative_tf']} "
            f"zero={cross['n_zero_tf']} "
            f"undefined={cross['n_undefined_tf']}"
        ),
        (
            "RAW_DEFINED_TF "
            f"n_defined_tf={cross['n_defined_tf']} "
            f"rho_min={cross['rho_min']} "
            f"rho_max={cross['rho_max']} "
            f"rho_range={cross['rho_range']}"
        ),
    ]
    for timeframe in TIMEFRAMES:
        raw = raw_by_tf[timeframe]
        if not isinstance(raw, Mapping):
            raise ValueError(f"dossier raw values for {timeframe} are malformed")
        observations.append(
            f"{timeframe} RAW rho={raw['rho_raw']} status={raw['status']} "
            f"n_valid_pairwise={raw['n_valid_pairwise']}"
        )
    if dossier["partial_applicability"] == _ELIGIBLE:
        for timeframe in TIMEFRAMES:
            partial = partial_by_tf[timeframe]
            if not isinstance(partial, Mapping):
                raise ValueError(f"dossier partial values for {timeframe} are malformed")
            observations.append(
                f"{timeframe} CONTROLLED "
                f"rho_raw_for_delta={partial['rho_raw_for_delta']} "
                f"rho_duration_controlled={partial['rho_duration_controlled']} "
                f"delta_rho={partial['delta_rho']} status={partial['status']} "
                f"n_valid_triple={partial['n_valid_triple']}"
            )
    elif dossier["partial_applicability"] == CONTROL_NOT_APPLICABLE:
        observations.extend(
            f"{timeframe} CONTROLLED {CONTROL_NOT_APPLICABLE}" for timeframe in TIMEFRAMES
        )
    else:
        raise ValueError("dossier has invalid partial applicability")
    for observation in observations:
        validate_observation_text(observation)
    return observations


def build_main_relationship_dossiers(bundle: Task9EvidenceBundle) -> list[dict[str, object]]:
    """Build all 78 main dossiers by copying locked Task 9 evidence values."""

    roles = _feature_roles(bundle)
    relations = _relation_participants(bundle)
    raw_indexes = {
        timeframe: _pair_index(bundle.main_raw_by_tf[timeframe], source=f"MAIN_SPEARMAN_{timeframe}.csv")
        for timeframe in TIMEFRAMES
    }
    partial_indexes = {
        timeframe: _pair_index(bundle.partial_by_tf[timeframe], source=f"PARTIAL_SPEARMAN_{timeframe}.csv")
        for timeframe in TIMEFRAMES
    }
    cross_index = _pair_index(bundle.cross_tf, source="CROSS_TF_RELATIONSHIP_REPORT.csv")
    expected_main = {pair_key(*pair) for pair in MAIN_PAIR_KEYS}
    if set(cross_index) != expected_main or any(set(index) != expected_main for index in raw_indexes.values()):
        raise ValueError("Task 9 main source pair set is incomplete")
    expected_partial = {pair_key(*pair) for pair in PARTIAL_PAIR_KEYS}
    if any(set(index) != expected_partial for index in partial_indexes.values()):
        raise ValueError("Task 9 partial source pair set is inconsistent")
    _validate_source_statuses(raw_indexes, kind="raw")
    _validate_source_statuses(partial_indexes, kind="controlled")

    dossiers: list[dict[str, object]] = []
    for feature_x, feature_y in MAIN_PAIR_KEYS:
        source_pair_key = pair_key(feature_x, feature_y)
        cross_source = cross_index[source_pair_key]
        _audit_cross_tf(cross_source)
        cross_tf = dict(cross_source)
        cross_tf["n_defined_tf"] = len(
            [cross_tf[f"rho_{timeframe}"] for timeframe in TIMEFRAMES if cross_tf[f"rho_{timeframe}"] is not None]
        )
        raw_by_tf = {timeframe: dict(raw_indexes[timeframe][source_pair_key]) for timeframe in TIMEFRAMES}
        eligible = CONTROL_FEATURE not in (feature_x, feature_y)
        if eligible:
            partial_by_tf = {timeframe: dict(partial_indexes[timeframe][source_pair_key]) for timeframe in TIMEFRAMES}
            partial_artifacts = {timeframe: f"PARTIAL_SPEARMAN_{timeframe}.csv" for timeframe in TIMEFRAMES}
            partial_locators = {timeframe: f"PARTIAL_SPEARMAN_{timeframe}.csv#{source_pair_key}" for timeframe in TIMEFRAMES}
            applicability = _ELIGIBLE
        else:
            if any(source_pair_key in index for index in partial_indexes.values()):
                raise ValueError(f"Task 9 partial source contains control pair {source_pair_key}")
            partial_by_tf = {timeframe: dict(_CONTROL_PARTIAL) for timeframe in TIMEFRAMES}
            partial_artifacts = {timeframe: None for timeframe in TIMEFRAMES}
            partial_locators = {timeframe: CONTROL_NOT_APPLICABLE for timeframe in TIMEFRAMES}
            applicability = CONTROL_NOT_APPLICABLE
        relation_ids = sorted(
            relation_id for relation_id, participants in relations.items()
            if {feature_x, feature_y} <= participants
        )
        dossier: dict[str, object] = {
            "pair_key": source_pair_key,
            "source_pair_key": source_pair_key,
            "feature_x": feature_x,
            "feature_y": feature_y,
            "feature_x_analysis_role": roles[feature_x]["analysis_role"],
            "feature_y_analysis_role": roles[feature_y]["analysis_role"],
            "feature_x_formula": roles[feature_x]["formula"],
            "feature_y_formula": roles[feature_y]["formula"],
            "feature_x_direction_semantics": roles[feature_x]["direction_semantics"],
            "feature_y_direction_semantics": roles[feature_y]["direction_semantics"],
            "direct_deterministic_dependency": bool(relation_ids),
            "direct_deterministic_relation_ids": relation_ids,
            "raw_source_artifact_by_tf": {timeframe: f"MAIN_SPEARMAN_{timeframe}.csv" for timeframe in TIMEFRAMES},
            "raw_source_row_locator_by_tf": {timeframe: f"MAIN_SPEARMAN_{timeframe}.csv#{source_pair_key}" for timeframe in TIMEFRAMES},
            "partial_source_artifact_by_tf": partial_artifacts,
            "partial_source_row_locator_by_tf": partial_locators,
            "cross_tf_source_artifact": "CROSS_TF_RELATIONSHIP_REPORT.csv",
            "cross_tf_source_row_locator": f"CROSS_TF_RELATIONSHIP_REPORT.csv#{source_pair_key}",
            "partial_applicability": applicability,
            "raw_by_tf": raw_by_tf,
            "partial_by_tf": partial_by_tf,
            "cross_tf": cross_tf,
            "deterministic_context": {
                "co_participating_relation_ids": relation_ids,
                "co_participation_semantics": "Both features appear in one locked Task 9 deterministic identity row.",
            },
        }
        dossier["observations"] = build_neutral_observations(dossier)
        dossiers.append(dossier)
    return dossiers


def build_supplementary_evidence(
    bundle: Task9EvidenceBundle,
) -> list[dict[str, object]]:
    """Copy the 960 locked direction-stratified Task 9 rows with provenance."""

    expected_pairs = {pair_key(*pair) for pair in SUPPLEMENTARY_PAIR_KEYS}
    main_pairs = {pair_key(*pair) for pair in MAIN_PAIR_KEYS}
    sensitive_features = set(RAW_DIRECTION_SENSITIVE)
    output: list[dict[str, object]] = []
    source_fields = SUPPLEMENTARY_OUTPUT_FIELDS[8:]
    for timeframe in TIMEFRAMES:
        for direction in DIRECTIONS:
            source_artifact = f"SUPPLEMENTARY_{timeframe}_{direction}.csv"
            try:
                source_rows = bundle.supplementary_by_tf_direction[
                    (timeframe, direction)
                ]
            except KeyError as exc:
                raise ValueError(
                    f"Task 9 supplementary source is missing {source_artifact}"
                ) from exc
            indexed = _pair_index(source_rows, source=source_artifact)
            if set(indexed) != expected_pairs:
                raise ValueError(
                    f"Task 9 supplementary pair set is inconsistent for {source_artifact}"
                )
            for feature_x, feature_y in SUPPLEMENTARY_PAIR_KEYS:
                source_pair_key = pair_key(feature_x, feature_y)
                source = indexed[source_pair_key]
                if any(field not in source for field in source_fields):
                    raise ValueError(
                        f"Task 9 supplementary row is incomplete for "
                        f"{source_artifact}#{source_pair_key}"
                    )
                contains_sensitive = bool(
                    {feature_x, feature_y} & sensitive_features
                )
                is_main_pair = source_pair_key in main_pairs
                if contains_sensitive and is_main_pair:
                    raise ValueError("raw-direction-sensitive pair entered main scope")
                output.append(
                    {
                        "timeframe": timeframe,
                        "direction": direction,
                        "source_artifact": source_artifact,
                        "pair_key": source_pair_key,
                        "feature_x": feature_x,
                        "feature_y": feature_y,
                        "contains_raw_direction_sensitive": contains_sensitive,
                        "is_main_pair": is_main_pair,
                        **{field: source[field] for field in source_fields},
                    }
                )
    return output


def build_feature_dossiers(
    bundle: Task9EvidenceBundle,
    main_dossiers: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    """Build one metadata-only dossier for each locked main feature."""

    roles = _feature_roles(bundle)
    pair_keys_by_feature = {feature: [] for feature in MAIN_FEATURES}
    seen_pairs: set[str] = set()
    for dossier in main_dossiers:
        try:
            feature_x = str(dossier["feature_x"])
            feature_y = str(dossier["feature_y"])
            source_pair_key = str(dossier["pair_key"])
        except KeyError as exc:
            raise ValueError("main dossier is missing pair metadata") from exc
        if source_pair_key != pair_key(feature_x, feature_y):
            raise ValueError("main dossier pair key is inconsistent")
        if source_pair_key in seen_pairs:
            raise ValueError(f"duplicate main dossier pair {source_pair_key}")
        seen_pairs.add(source_pair_key)
        pair_keys_by_feature[feature_x].append(source_pair_key)
        pair_keys_by_feature[feature_y].append(source_pair_key)
    expected_pairs = {pair_key(*pair) for pair in MAIN_PAIR_KEYS}
    if seen_pairs != expected_pairs:
        raise ValueError("main dossiers do not contain the locked 78-pair set")

    return [
        {
            "feature": feature,
            "formula": roles[feature]["formula"],
            "analysis_role": roles[feature]["analysis_role"],
            "direction_semantics": roles[feature]["direction_semantics"],
            "main_relationship_pair_keys": pair_keys_by_feature[feature],
            "future_ablation_hypothesis_ids": [],
        }
        for feature in MAIN_FEATURES
    ]


def build_future_ablation_hypotheses() -> list[dict[str, object]]:
    """Return the locked empty artifact; Task 10 invents no hypotheses."""

    return []


__all__ = [
    "build_feature_dossiers",
    "build_future_ablation_hypotheses",
    "build_main_relationship_dossiers",
    "build_neutral_observations",
    "build_supplementary_evidence",
]
