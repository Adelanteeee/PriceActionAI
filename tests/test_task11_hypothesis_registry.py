from collections.abc import Mapping

import pytest

from research.task11_hypothesis_contract import (
    CONTROL_NOT_APPLICABLE,
    DETERMINISTIC_RELATION_IDS_BY_PAIR_KEY,
    ELIGIBLE,
    TASK10_CANONICAL_PAIR_KEYS,
    TASK11_HYPOTHESIS_RECORD_FIELDS,
    TASK11_SOURCE_LOCATOR_FIELDS,
    TIMEFRAMES,
)
from research.task11_hypothesis_registry import (
    build_hypothesis_registry,
    validate_hypothesis_registry,
)
from test_task11_hypothesis_io import (
    load_synthetic_task10,
    make_synthetic_task10_production_zip,
)


PROHIBITED_FIELDS = {
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
}
OMITTED_OR_ALIAS_FIELDS = {
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
}


def json_native(value: object) -> object:
    """Convert the immutable loader boundary to the fixture's JSON types."""
    if isinstance(value, Mapping):
        return {key: json_native(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_native(item) for item in value]
    return value


def assert_json_exact(actual: object, expected: object) -> None:
    assert type(actual) is type(expected)
    if isinstance(expected, dict):
        assert set(actual) == set(expected)  # type: ignore[arg-type]
        for key in expected:
            assert_json_exact(actual[key], expected[key])  # type: ignore[index]
    elif isinstance(expected, list):
        assert len(actual) == len(expected)  # type: ignore[arg-type]
        for left, right in zip(actual, expected, strict=True):  # type: ignore[arg-type]
            assert_json_exact(left, right)
    else:
        assert actual == expected


def test_registry_is_exactly_one_record_per_source_pair_in_source_order():
    bundle = load_synthetic_task10(make_synthetic_task10_production_zip())
    registry = build_hypothesis_registry(bundle.main_dossiers)

    assert len(registry) == 78
    assert [record["pair_key"] for record in registry] == [
        dossier["pair_key"] for dossier in bundle.main_dossiers
    ]
    assert len({record["hypothesis_id"] for record in registry}) == 78
    for source, record in zip(bundle.main_dossiers, registry, strict=True):
        assert record["feature_x"] == source["feature_x"]
        assert record["feature_y"] == source["feature_y"]
        assert record["hypothesis_id"] == "TASK11_HYPOTHESIS__" + source["pair_key"]


def test_every_question_is_the_single_locked_literal_template():
    bundle = load_synthetic_task10(make_synthetic_task10_production_zip())
    registry = build_hypothesis_registry(bundle.main_dossiers)

    for source, record in zip(bundle.main_dossiers, registry, strict=True):
        expected = (
            "Under a future separately locked controlled ablation protocol, "
            f"does the information relationship between {source['feature_x']} "
            f"and {source['feature_y']} remain measurable when their incremental "
            "information contributions are evaluated separately?"
        )
        assert record["test_question_template_id"] == "TASK11_PAIRWISE_NEUTRAL_V1"
        assert record["test_question"] == expected


def test_builder_rejects_reversed_source_instead_of_sorting_or_normalizing_it():
    bundle = load_synthetic_task10(make_synthetic_task10_production_zip())

    with pytest.raises(ValueError, match="canonical pair order"):
        build_hypothesis_registry(tuple(reversed(bundle.main_dossiers)))


def test_builder_rejects_missing_locator_source_field_with_context():
    bundle = load_synthetic_task10(make_synthetic_task10_production_zip())
    sources = json_native(bundle.main_dossiers)
    assert isinstance(sources, list)
    del sources[0]["raw_source_artifact_by_tf"]

    with pytest.raises(
        ValueError,
        match=r"index 0.*active_bar_count__net_thrust.*raw_source_artifact_by_tf",
    ):
        build_hypothesis_registry(sources)


def test_builder_rejects_unsupported_nested_json_value_with_context():
    bundle = load_synthetic_task10(make_synthetic_task10_production_zip())
    sources = json_native(bundle.main_dossiers)
    assert isinstance(sources, list)
    sources[0]["raw_by_tf"]["M5"]["rho_raw"] = object()

    with pytest.raises(
        ValueError,
        match=r"index 0.*active_bar_count__net_thrust.*raw_by_tf\.M5\.rho_raw",
    ):
        build_hypothesis_registry(sources)


def test_registry_copies_every_mapped_value_with_exact_json_types_and_closed_schemas():
    bundle = load_synthetic_task10(make_synthetic_task10_production_zip())
    registry = build_hypothesis_registry(bundle.main_dossiers)

    for source, record in zip(bundle.main_dossiers, registry, strict=True):
        source_json = json_native(source)
        assert isinstance(source_json, dict)
        assert_json_exact(record["raw_evidence_by_tf"], source_json["raw_by_tf"])
        assert record["duration_control_applicability"] == source_json["partial_applicability"]
        assert_json_exact(record["controlled_evidence_by_tf"], source_json["partial_by_tf"])
        assert_json_exact(record["cross_tf_evidence"], source_json["cross_tf"])
        assert record["direct_deterministic_dependency"] is source_json["direct_deterministic_dependency"]
        assert_json_exact(record["deterministic_relation_ids"], source_json["direct_deterministic_relation_ids"])
        assert_json_exact(record["deterministic_context"], source_json["deterministic_context"])
        assert_json_exact(record["evidence_summary"], source_json["observations"])
        assert set(record) == set(TASK11_HYPOTHESIS_RECORD_FIELDS)
        assert set(record["source_locators"]) == set(TASK11_SOURCE_LOCATOR_FIELDS)
        assert_json_exact(
            record["source_locators"],
            {
                "task10_main_dossier": "TASK10_MAIN_RELATIONSHIP_DOSSIERS.json#" + source_json["pair_key"],
                "upstream_raw_source_artifact_by_tf": source_json["raw_source_artifact_by_tf"],
                "upstream_raw_source_row_locator_by_tf": source_json["raw_source_row_locator_by_tf"],
                "upstream_partial_source_artifact_by_tf": source_json["partial_source_artifact_by_tf"],
                "upstream_partial_source_row_locator_by_tf": source_json["partial_source_row_locator_by_tf"],
                "upstream_cross_tf_source_artifact": source_json["cross_tf_source_artifact"],
                "upstream_cross_tf_source_row_locator": source_json["cross_tf_source_row_locator"],
            },
        )


def test_registry_preserves_control_applicability_and_delta_rho_location():
    bundle = load_synthetic_task10(make_synthetic_task10_production_zip())
    registry = build_hypothesis_registry(bundle.main_dossiers)
    eligible = [record for record in registry if record["duration_control_applicability"] == ELIGIBLE]
    control = [record for record in registry if record["duration_control_applicability"] == CONTROL_NOT_APPLICABLE]

    assert len(eligible) == 66
    assert len(control) == 12
    for record in eligible:
        for timeframe in TIMEFRAMES:
            assert set(record["controlled_evidence_by_tf"][timeframe]) == {
                "feature_x", "feature_y", "rho_raw_for_delta", "rho_duration_controlled",
                "delta_rho", "n_valid_triple", "status",
            }
            assert "delta_rho" in record["controlled_evidence_by_tf"][timeframe]
    for record in control:
        for timeframe in TIMEFRAMES:
            partial = record["controlled_evidence_by_tf"][timeframe]
            assert partial["rho_raw_for_delta"] is None
            assert partial["rho_duration_controlled"] is None
            assert partial["delta_rho"] is None
            assert partial["n_valid_triple"] is None
            assert partial["status"] == CONTROL_NOT_APPLICABLE
            assert record["source_locators"]["upstream_partial_source_artifact_by_tf"][timeframe] is None
            assert record["source_locators"]["upstream_partial_source_row_locator_by_tf"][timeframe] == CONTROL_NOT_APPLICABLE
    for record in registry:
        assert "delta_rho_by_tf" not in record
        assert "delta_rho_by_tf" not in record["source_locators"]


def test_registry_preserves_exact_deterministic_context_without_extra_records():
    bundle = load_synthetic_task10(make_synthetic_task10_production_zip())
    registry = build_hypothesis_registry(bundle.main_dossiers)

    deterministic = {
        record["pair_key"]: tuple(record["deterministic_relation_ids"])
        for record in registry
        if record["direct_deterministic_dependency"] is True
    }
    assert len(registry) == len(TASK10_CANONICAL_PAIR_KEYS) == 78
    assert deterministic == dict(DETERMINISTIC_RELATION_IDS_BY_PAIR_KEY)
    for record in registry:
        if record["pair_key"] not in DETERMINISTIC_RELATION_IDS_BY_PAIR_KEY:
            assert record["direct_deterministic_dependency"] is False
            assert record["deterministic_relation_ids"] == []
            assert record["deterministic_context"]["co_participating_relation_ids"] == []


def test_validator_rejects_evidence_summary_content_or_order_drift_with_location():
    bundle = load_synthetic_task10(make_synthetic_task10_production_zip())
    registry = build_hypothesis_registry(bundle.main_dossiers)
    altered = json_native(registry)
    assert isinstance(altered, list)
    altered[0]["evidence_summary"][0] = "changed"

    with pytest.raises(ValueError, match=r"index 0.*active_bar_count__net_thrust.*evidence_summary\[0\]"):
        validate_hypothesis_registry(altered, bundle.main_dossiers)

    swapped = json_native(registry)
    assert isinstance(swapped, list)
    swapped[0]["evidence_summary"].reverse()
    with pytest.raises(ValueError, match=r"index 0.*active_bar_count__net_thrust.*evidence_summary\[0\]"):
        validate_hypothesis_registry(swapped, bundle.main_dossiers)


def test_validator_rejects_schema_prohibitions_and_unmapped_aliases_with_location():
    bundle = load_synthetic_task10(make_synthetic_task10_production_zip())
    registry = build_hypothesis_registry(bundle.main_dossiers)
    assert not (set(registry[0]) & (PROHIBITED_FIELDS | OMITTED_OR_ALIAS_FIELDS))

    invalid = json_native(registry)
    assert isinstance(invalid, list)
    invalid[0]["rank"] = 1
    with pytest.raises(ValueError, match=r"index 0.*active_bar_count__net_thrust.*record"):
        validate_hypothesis_registry(invalid, bundle.main_dossiers)


def test_nested_registry_values_are_mutable_copies_not_loader_references():
    bundle = load_synthetic_task10(make_synthetic_task10_production_zip())
    registry = build_hypothesis_registry(bundle.main_dossiers)

    registry[0]["raw_evidence_by_tf"]["M5"]["n_total"] = -1
    registry[0]["controlled_evidence_by_tf"]["M5"]["status"] = "CHANGED"
    registry[0]["deterministic_context"]["co_participating_relation_ids"].append("CHANGED")
    registry[0]["evidence_summary"].append("CHANGED")
    registry[0]["source_locators"]["upstream_raw_source_artifact_by_tf"]["M5"] = "CHANGED"

    assert bundle.main_dossiers[0]["raw_by_tf"]["M5"]["n_total"] == 1000
    assert bundle.main_dossiers[0]["partial_by_tf"]["M5"]["status"] == CONTROL_NOT_APPLICABLE
    assert bundle.main_dossiers[0]["deterministic_context"]["co_participating_relation_ids"] == ()
    assert bundle.main_dossiers[0]["observations"] == ("record-0", "pair-active_bar_count__net_thrust")
    assert bundle.main_dossiers[0]["raw_source_artifact_by_tf"]["M5"] == "MAIN_SPEARMAN_M5.csv"
