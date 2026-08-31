import pytest

from research.task10_interpretation_contract import (
    CONTROL_PAIR_KEYS,
    CONTROL_NOT_APPLICABLE,
    MAIN_PAIR_KEYS,
    PARTIAL_PAIR_KEYS,
    SUPPLEMENTARY_PAIR_KEYS,
    SUPPLEMENTARY_OUTPUT_FIELDS,
    TASK10_LOGICAL_FILENAMES,
    TASK10_SPEC_COMMIT,
    TASK9_ACTIVITY_INPUT_SHA256,
    TASK9_AUDIT_CODE_COMMIT,
    TASK9_EVIDENCE_PACKAGE_FILENAME,
    TASK9_EVIDENCE_SHA256,
    TASK9_REGISTRATION_COMMIT,
    canonical_pair,
    pair_key,
    validate_observation_text,
)


def test_pair_counts_are_locked():
    assert len(MAIN_PAIR_KEYS) == 78
    assert len(PARTIAL_PAIR_KEYS) == 66
    assert len(CONTROL_PAIR_KEYS) == 12
    assert len(SUPPLEMENTARY_PAIR_KEYS) == 120
    assert set(PARTIAL_PAIR_KEYS).isdisjoint(CONTROL_PAIR_KEYS)
    assert set(PARTIAL_PAIR_KEYS) | set(CONTROL_PAIR_KEYS) == set(MAIN_PAIR_KEYS)


def test_task9_and_task10_provenance_constants_are_exact():
    assert TASK9_EVIDENCE_PACKAGE_FILENAME == "GOLD_COMBINED_LEG_FEATURE_AUDIT_PACKAGE.zip"
    assert TASK9_EVIDENCE_SHA256 == "968f4826858a0bbb8254218711f4ad3e3487370ca8d0f288133ee36f7a4fa40d"
    assert TASK9_ACTIVITY_INPUT_SHA256 == "1e9f13fd88fc1e8e0e66d801be8c15d726639eaea25e53fef7c3bb88bfd05192"
    assert TASK9_AUDIT_CODE_COMMIT == "1c40cd3d3507c473fd07ea25c010d386be8a0043"
    assert TASK9_REGISTRATION_COMMIT == "78e54fb50ce82a0cba7f91f40a6451e82996008d"
    assert TASK10_SPEC_COMMIT == "dfc91e3c75a12a3dfa008c17453b622f03ed41ad"


def test_pair_key_is_canonical_in_frozen_feature_order():
    assert canonical_pair("net_thrust", "active_bar_count") == (
        "active_bar_count",
        "net_thrust",
    )
    assert pair_key("net_thrust", "active_bar_count") == (
        "active_bar_count__net_thrust"
    )


def test_pair_helpers_reject_invalid_pairs():
    with pytest.raises(ValueError, match="distinct"):
        canonical_pair("net_thrust", "net_thrust")
    with pytest.raises(ValueError, match="unknown Task 10 feature"):
        canonical_pair("unknown", "net_thrust")


def test_task10_output_names_and_supplementary_csv_schema_are_exact():
    assert TASK10_LOGICAL_FILENAMES == (
        "TASK10_MAIN_RELATIONSHIP_DOSSIERS.json",
        "TASK10_SUPPLEMENTARY_EVIDENCE.csv",
        "TASK10_FEATURE_DOSSIERS.json",
        "TASK10_FUTURE_ABLATION_HYPOTHESES.json",
        "TASK10_MANIFEST.json",
    )
    assert SUPPLEMENTARY_OUTPUT_FIELDS == (
        "timeframe",
        "direction",
        "source_artifact",
        "pair_key",
        "feature_x",
        "feature_y",
        "contains_raw_direction_sensitive",
        "is_main_pair",
        "n_total",
        "n_valid_pairwise",
        "n_missing_x",
        "n_missing_y",
        "rho_raw",
        "raw_status",
        "rho_raw_for_delta",
        "rho_duration_controlled",
        "delta_rho",
        "n_valid_triple",
        "controlled_status",
        "evidence_scope",
    )
    assert CONTROL_NOT_APPLICABLE == "NOT_APPLICABLE_CONTROL_FEATURE"


@pytest.mark.parametrize(
    "text",
    [
        "Feature X is STRONG",
        "feature x is weak",
        "this is redundant",
        "KEEP feature x",
        "drop feature y",
        "near_duplicate candidate",
    ],
)
def test_observation_text_rejects_decision_language(text):
    with pytest.raises(ValueError):
        validate_observation_text(text)


def test_observation_text_allows_exact_numeric_description():
    validate_observation_text(
        "M15 raw rho=-0.21; controlled rho=-0.08; delta_rho=0.13"
    )
