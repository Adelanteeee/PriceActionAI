"""Exact Task 10-to-Task 11 Hypothesis registry transformation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from research.task11_hypothesis_contract import (
    CONTROL_FEATURE_NON_APPLICABLE_COUNT,
    CONTROL_NOT_APPLICABLE,
    DETERMINISTIC_CONTEXT_PAIR_COUNT,
    DETERMINISTIC_RELATION_IDS_BY_PAIR_KEY,
    DURATION_CONTROL_ELIGIBLE_COUNT,
    ELIGIBLE,
    HYPOTHESIS_COUNT,
    HYPOTHESIS_ID_PREFIX,
    TASK10_CANONICAL_PAIR_KEYS,
    TASK11_HYPOTHESIS_RECORD_FIELDS,
    TASK11_SOURCE_LOCATOR_FIELDS,
    TEST_QUESTION_TEMPLATE,
    TEST_QUESTION_TEMPLATE_ID,
)


_OMITTED_OR_ALIAS_FIELDS = frozenset({
    "source_pair_key",
    "feature_x_analysis_role",
    "feature_y_analysis_role",
    "feature_x_formula",
    "feature_y_formula",
    "feature_x_direction_semantics",
    "feature_y_direction_semantics",
    "raw_by_tf",
    "partial_by_tf",
    "cross_tf",
    "observations",
    "raw_source_artifact_by_tf",
    "raw_source_row_locator_by_tf",
    "partial_source_artifact_by_tf",
    "partial_source_row_locator_by_tf",
    "cross_tf_source_artifact",
    "cross_tf_source_row_locator",
})
_PROHIBITED_FIELDS = frozenset({
    "rank",
    "score",
    "weight",
    "priority",
    "strength_label",
    "stability_label",
    "redundancy_label",
    "keep_recommendation",
    "drop_recommendation",
    "outcome",
    "prediction",
    "threshold",
    "ablation_result",
    "causal_interpretation",
    "delta_rho_by_tf",
})


def _failure(index: int, pair_key: object, path: str, detail: str) -> ValueError:
    return ValueError(
        "Task 11 hypothesis registry validation failed "
        f"at index {index} pair_key {pair_key!r} {path}: {detail}"
    )


def _copy_source_json(
    source: Mapping[str, object], field: str, *, index: int, pair_key: str
) -> object:
    """Copy one required source field, making all boundary failures contextual."""
    try:
        source_value = source[field]
    except KeyError as exc:
        raise _failure(index, pair_key, field, "source field is missing") from exc

    def copy_value(value: object, path: str) -> object:
        if isinstance(value, Mapping):
            copied: dict[str, object] = {}
            for key, item in value.items():
                if type(key) is not str:
                    raise _failure(
                        index,
                        pair_key,
                        path,
                        f"unsupported JSON object key type: {type(key).__name__}",
                    )
                copied[key] = copy_value(item, f"{path}.{key}")
            return copied
        if isinstance(value, (list, tuple)):
            return [
                copy_value(item, f"{path}[{item_index}]")
                for item_index, item in enumerate(value)
            ]
        if value is None or type(value) in {str, bool, int, float}:
            return value
        raise _failure(
            index,
            pair_key,
            path,
            f"unsupported JSON value type: {type(value).__name__}",
        )

    return copy_value(source_value, field)


def render_test_question(feature_x: str, feature_y: str) -> str:
    return TEST_QUESTION_TEMPLATE.replace("{feature_x}", feature_x).replace(
        "{feature_y}", feature_y
    )


def _source_pairs(main_dossiers: Sequence[Mapping[str, object]]) -> tuple[str, ...]:
    if len(main_dossiers) != HYPOTHESIS_COUNT:
        raise _failure(-1, "<source>", "main_dossiers", "must contain exactly 78 records")
    observed: list[str] = []
    for index, source in enumerate(main_dossiers):
        if not isinstance(source, Mapping):
            raise _failure(index, "<unknown>", "main_dossiers", "must contain mappings")
        pair_key = source.get("pair_key")
        if type(pair_key) is not str:
            raise _failure(index, pair_key, "pair_key", "must be text")
        observed.append(pair_key)
    if tuple(observed) != TASK10_CANONICAL_PAIR_KEYS:
        differing_index = next(
            index
            for index, (actual, expected) in enumerate(
                zip(observed, TASK10_CANONICAL_PAIR_KEYS, strict=True)
            )
            if actual != expected
        )
        raise _failure(
            differing_index,
            observed[differing_index],
            "pair_key",
            "canonical pair order does not match the locked Task 10 source order",
        )
    return tuple(observed)


def _source_text(source: Mapping[str, object], index: int, pair_key: str, field: str) -> str:
    value = source.get(field)
    if type(value) is not str:
        raise _failure(index, pair_key, field, "source value must be text")
    return value


def _assert_json_exact(
    actual: object, expected: object, *, index: int, pair_key: str, path: str
) -> None:
    if type(actual) is not type(expected):
        raise _failure(
            index,
            pair_key,
            path,
            f"JSON type mismatch: expected {type(expected).__name__}, got {type(actual).__name__}",
        )
    if type(expected) is dict:
        actual_dict = actual
        expected_dict = expected
        if set(actual_dict) != set(expected_dict):  # type: ignore[arg-type]
            raise _failure(index, pair_key, path, "JSON object keys differ")
        for key in expected_dict:  # type: ignore[union-attr]
            _assert_json_exact(
                actual_dict[key],  # type: ignore[index]
                expected_dict[key],  # type: ignore[index]
                index=index,
                pair_key=pair_key,
                path=f"{path}.{key}",
            )
    elif type(expected) is list:
        actual_list = actual
        expected_list = expected
        if len(actual_list) != len(expected_list):  # type: ignore[arg-type]
            raise _failure(index, pair_key, path, "JSON array lengths differ")
        for item_index, (actual_item, expected_item) in enumerate(
            zip(actual_list, expected_list, strict=True)  # type: ignore[arg-type]
        ):
            _assert_json_exact(
                actual_item,
                expected_item,
                index=index,
                pair_key=pair_key,
                path=f"{path}[{item_index}]",
            )
    elif actual != expected:
        raise _failure(index, pair_key, path, "JSON values differ")


def _assert_no_prohibited_keys(value: object, *, index: int, pair_key: str, path: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in _PROHIBITED_FIELDS:
                raise _failure(index, pair_key, f"{path}.{key}", "prohibited field")
            _assert_no_prohibited_keys(item, index=index, pair_key=pair_key, path=f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for item_index, item in enumerate(value):
            _assert_no_prohibited_keys(item, index=index, pair_key=pair_key, path=f"{path}[{item_index}]")


def _assert_exact_keys(
    value: object,
    expected: Sequence[str],
    *,
    index: int,
    pair_key: str,
    path: str,
) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise _failure(index, pair_key, path, "must be a JSON object")
    if set(value) != set(expected):
        raise _failure(index, pair_key, path, "keys do not match the closed schema")
    return value


def _assert_equal_copy(
    record: Mapping[str, object],
    source: Mapping[str, object],
    record_field: str,
    source_field: str,
    *,
    index: int,
    pair_key: str,
) -> None:
    expected = _copy_source_json(
        source, source_field, index=index, pair_key=pair_key
    )
    _assert_json_exact(
        record[record_field],
        expected,
        index=index,
        pair_key=pair_key,
        path=record_field,
    )


def _assert_locator_mapping(
    record: Mapping[str, object], source: Mapping[str, object], *, index: int, pair_key: str
) -> None:
    locators = _assert_exact_keys(
        record["source_locators"],
        TASK11_SOURCE_LOCATOR_FIELDS,
        index=index,
        pair_key=pair_key,
        path="source_locators",
    )
    expected: dict[str, object] = {
        "task10_main_dossier": "TASK10_MAIN_RELATIONSHIP_DOSSIERS.json#" + pair_key,
        "upstream_raw_source_artifact_by_tf": _copy_source_json(source, "raw_source_artifact_by_tf", index=index, pair_key=pair_key),
        "upstream_raw_source_row_locator_by_tf": _copy_source_json(source, "raw_source_row_locator_by_tf", index=index, pair_key=pair_key),
        "upstream_partial_source_artifact_by_tf": _copy_source_json(source, "partial_source_artifact_by_tf", index=index, pair_key=pair_key),
        "upstream_partial_source_row_locator_by_tf": _copy_source_json(source, "partial_source_row_locator_by_tf", index=index, pair_key=pair_key),
        "upstream_cross_tf_source_artifact": _copy_source_json(source, "cross_tf_source_artifact", index=index, pair_key=pair_key),
        "upstream_cross_tf_source_row_locator": _copy_source_json(source, "cross_tf_source_row_locator", index=index, pair_key=pair_key),
    }
    _assert_json_exact(
        dict(locators), expected, index=index, pair_key=pair_key, path="source_locators"
    )


def build_hypothesis_registry(
    main_dossiers: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    """Build one closed-schema neutral Hypothesis record per canonical source pair."""
    _source_pairs(main_dossiers)
    registry: list[dict[str, object]] = []
    for index, source in enumerate(main_dossiers):
        pair_key = _source_text(source, index, "<unknown>", "pair_key")
        feature_x = _source_text(source, index, pair_key, "feature_x")
        feature_y = _source_text(source, index, pair_key, "feature_y")
        registry.append({
            "hypothesis_id": HYPOTHESIS_ID_PREFIX + pair_key,
            "pair_key": pair_key,
            "feature_x": feature_x,
            "feature_y": feature_y,
            "raw_evidence_by_tf": _copy_source_json(source, "raw_by_tf", index=index, pair_key=pair_key),
            "duration_control_applicability": _copy_source_json(source, "partial_applicability", index=index, pair_key=pair_key),
            "controlled_evidence_by_tf": _copy_source_json(source, "partial_by_tf", index=index, pair_key=pair_key),
            "cross_tf_evidence": _copy_source_json(source, "cross_tf", index=index, pair_key=pair_key),
            "direct_deterministic_dependency": _copy_source_json(source, "direct_deterministic_dependency", index=index, pair_key=pair_key),
            "deterministic_relation_ids": _copy_source_json(source, "direct_deterministic_relation_ids", index=index, pair_key=pair_key),
            "deterministic_context": _copy_source_json(source, "deterministic_context", index=index, pair_key=pair_key),
            "evidence_summary": _copy_source_json(source, "observations", index=index, pair_key=pair_key),
            "test_question_template_id": TEST_QUESTION_TEMPLATE_ID,
            "test_question": render_test_question(feature_x, feature_y),
            "source_locators": {
                "task10_main_dossier": "TASK10_MAIN_RELATIONSHIP_DOSSIERS.json#" + pair_key,
                "upstream_raw_source_artifact_by_tf": _copy_source_json(source, "raw_source_artifact_by_tf", index=index, pair_key=pair_key),
                "upstream_raw_source_row_locator_by_tf": _copy_source_json(source, "raw_source_row_locator_by_tf", index=index, pair_key=pair_key),
                "upstream_partial_source_artifact_by_tf": _copy_source_json(source, "partial_source_artifact_by_tf", index=index, pair_key=pair_key),
                "upstream_partial_source_row_locator_by_tf": _copy_source_json(source, "partial_source_row_locator_by_tf", index=index, pair_key=pair_key),
                "upstream_cross_tf_source_artifact": _copy_source_json(source, "cross_tf_source_artifact", index=index, pair_key=pair_key),
                "upstream_cross_tf_source_row_locator": _copy_source_json(source, "cross_tf_source_row_locator", index=index, pair_key=pair_key),
            },
        })
    validate_hypothesis_registry(registry, main_dossiers)
    return registry


def validate_hypothesis_registry(
    registry: Sequence[Mapping[str, object]], main_dossiers: Sequence[Mapping[str, object]]
) -> None:
    """Fail closed unless the registry is the exact canonical source projection."""
    _source_pairs(main_dossiers)
    if len(registry) != HYPOTHESIS_COUNT:
        raise _failure(-1, "<registry>", "registry", "must contain exactly 78 records")

    eligible_count = 0
    control_count = 0
    deterministic_count = 0
    for index, (record, source, expected_pair_key) in enumerate(
        zip(registry, main_dossiers, TASK10_CANONICAL_PAIR_KEYS, strict=True)
    ):
        if not isinstance(record, Mapping):
            raise _failure(index, "<unknown>", "record", "must be a JSON object")
        pair_key = record.get("pair_key")
        if type(pair_key) is not str:
            raise _failure(index, pair_key, "pair_key", "must be text")
        if pair_key != expected_pair_key:
            raise _failure(index, pair_key, "pair_key", "canonical pair order does not match locked order")
        _assert_exact_keys(
            record,
            TASK11_HYPOTHESIS_RECORD_FIELDS,
            index=index,
            pair_key=pair_key,
            path="record",
        )
        if set(record) & (_OMITTED_OR_ALIAS_FIELDS | _PROHIBITED_FIELDS):
            raise _failure(index, pair_key, "record", "contains an excluded or prohibited field")
        _assert_no_prohibited_keys(record, index=index, pair_key=pair_key, path="record")

        feature_x = _source_text(source, index, pair_key, "feature_x")
        feature_y = _source_text(source, index, pair_key, "feature_y")
        for field, expected in (
            ("pair_key", expected_pair_key),
            ("feature_x", feature_x),
            ("feature_y", feature_y),
            ("hypothesis_id", HYPOTHESIS_ID_PREFIX + expected_pair_key),
            ("test_question_template_id", TEST_QUESTION_TEMPLATE_ID),
            ("test_question", render_test_question(feature_x, feature_y)),
        ):
            _assert_json_exact(record[field], expected, index=index, pair_key=pair_key, path=field)

        for record_field, source_field in (
            ("raw_evidence_by_tf", "raw_by_tf"),
            ("duration_control_applicability", "partial_applicability"),
            ("controlled_evidence_by_tf", "partial_by_tf"),
            ("cross_tf_evidence", "cross_tf"),
            ("direct_deterministic_dependency", "direct_deterministic_dependency"),
            ("deterministic_relation_ids", "direct_deterministic_relation_ids"),
            ("deterministic_context", "deterministic_context"),
            ("evidence_summary", "observations"),
        ):
            _assert_equal_copy(
                record,
                source,
                record_field,
                source_field,
                index=index,
                pair_key=pair_key,
            )
        _assert_locator_mapping(record, source, index=index, pair_key=pair_key)

        applicability = record["duration_control_applicability"]
        if applicability == ELIGIBLE:
            eligible_count += 1
        elif applicability == CONTROL_NOT_APPLICABLE:
            control_count += 1
        else:
            raise _failure(index, pair_key, "duration_control_applicability", "is not locked")

        expected_relation_ids = list(DETERMINISTIC_RELATION_IDS_BY_PAIR_KEY.get(pair_key, ()))
        expected_dependency = bool(expected_relation_ids)
        _assert_json_exact(
            record["direct_deterministic_dependency"],
            expected_dependency,
            index=index,
            pair_key=pair_key,
            path="direct_deterministic_dependency",
        )
        _assert_json_exact(
            record["deterministic_relation_ids"],
            expected_relation_ids,
            index=index,
            pair_key=pair_key,
            path="deterministic_relation_ids",
        )
        deterministic_count += expected_dependency

    if (eligible_count, control_count, deterministic_count) != (
        DURATION_CONTROL_ELIGIBLE_COUNT,
        CONTROL_FEATURE_NON_APPLICABLE_COUNT,
        DETERMINISTIC_CONTEXT_PAIR_COUNT,
    ):
        raise _failure(
            -1,
            "<registry>",
            "counts",
            "applicability/deterministic counts must remain exactly 66/12/4",
        )


__all__ = ["build_hypothesis_registry", "render_test_question", "validate_hypothesis_registry"]
