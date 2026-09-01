import csv
import hashlib
import inspect
import io
import json
import warnings
import zipfile
from collections.abc import Callable
from pathlib import Path

import pytest

from research.task11_hypothesis_contract import (
    CONTROL_FEATURE,
    CONTROL_NOT_APPLICABLE,
    DETERMINISTIC_RELATION_IDS_BY_PAIR_KEY,
    ELIGIBLE,
    LOCKED_STATISTICAL_STATUSES,
    TASK10_CANONICAL_PAIR_KEYS,
    TASK10_CONTROL_PARTIAL_TF_FIELDS,
    TASK10_CROSS_TF_FIELDS,
    TASK10_DETERMINISTIC_CONTEXT_FIELDS,
    TASK10_ELIGIBLE_PARTIAL_TF_FIELDS,
    TASK10_MAIN_DOSSIER_FIELDS,
    TASK10_MANIFEST_EXPECTED_VALUES,
    TASK10_MANIFEST_FIELDS,
    TASK10_RAW_TF_FIELDS,
    TIMEFRAMES,
)
from research.task11_hypothesis_io import (
    Task10ProductionBundle,
    _load_task10_production_bytes,
    load_task10_production_package,
)


MAIN = "TASK10_MAIN_RELATIONSHIP_DOSSIERS.json"
SUPPLEMENTARY = "TASK10_SUPPLEMENTARY_EVIDENCE.csv"
FEATURES = "TASK10_FEATURE_DOSSIERS.json"
HYPOTHESES = "TASK10_FUTURE_ABLATION_HYPOTHESES.json"
MANIFEST = "TASK10_MANIFEST.json"


def _json_bytes(value: object) -> bytes:
    return json.dumps(value, allow_nan=False, separators=(",", ":")).encode("utf-8")


def _read_json(members: dict[str, bytes], name: str) -> object:
    return json.loads(members[name].decode("utf-8"))


def _write_json(members: dict[str, bytes], name: str, value: object) -> None:
    members[name] = _json_bytes(value)


def _raw(feature_x: str, feature_y: str, index: int) -> dict[str, object]:
    return {
        "feature_x": feature_x,
        "feature_y": feature_y,
        "n_missing_x": index,
        "n_missing_y": index + 1,
        "n_total": 1000 + index,
        "n_valid_pairwise": 900 + index,
        "rho_raw": 0.01 * (index + 1),
        "status": "DEFINED",
    }


def _eligible_partial(feature_x: str, feature_y: str, index: int) -> dict[str, object]:
    return {
        "feature_x": feature_x,
        "feature_y": feature_y,
        "rho_raw_for_delta": 0.01 * (index + 1),
        "rho_duration_controlled": 0.02 * (index + 1),
        "delta_rho": 0.01,
        "n_valid_triple": 800 + index,
        "status": "DEFINED",
    }


def _control_partial() -> dict[str, object]:
    return {
        "rho_raw_for_delta": None,
        "rho_duration_controlled": None,
        "delta_rho": None,
        "n_valid_triple": None,
        "status": CONTROL_NOT_APPLICABLE,
    }


def _cross(feature_x: str, feature_y: str, eligible: bool, index: int) -> dict[str, object]:
    return {
        "controlled_eligible": eligible,
        "controlled_rho_H1": 0.1 if eligible else None,
        "controlled_rho_M15": 0.2 if eligible else None,
        "controlled_rho_M30": 0.3 if eligible else None,
        "controlled_rho_M5": 0.4 if eligible else None,
        "feature_x": feature_x,
        "feature_y": feature_y,
        "n_defined_tf": 4,
        "n_negative_tf": 0,
        "n_positive_tf": 4,
        "n_undefined_tf": 0,
        "n_valid_H1": 900 + index,
        "n_valid_M15": 900 + index,
        "n_valid_M30": 900 + index,
        "n_valid_M5": 900 + index,
        "n_zero_tf": 0,
        "rho_H1": 0.11,
        "rho_M15": 0.12,
        "rho_M30": 0.13,
        "rho_M5": 0.14,
        "rho_max": 0.14,
        "rho_min": 0.11,
        "rho_range": 0.03,
        "sign_agreement_count": 4,
        "sign_agreement_modal_signs": ["POSITIVE"],
        "sign_agreement_tie": False,
    }


def _dossier(pair_key: str, index: int) -> dict[str, object]:
    feature_x, feature_y = pair_key.split("__")
    eligible = CONTROL_FEATURE not in (feature_x, feature_y)
    relation_ids = list(DETERMINISTIC_RELATION_IDS_BY_PAIR_KEY.get(pair_key, ()))
    return {
        "cross_tf": _cross(feature_x, feature_y, eligible, index),
        "cross_tf_source_artifact": "CROSS_TF_RELATIONSHIP_REPORT.csv",
        "cross_tf_source_row_locator": f"CROSS_TF_RELATIONSHIP_REPORT.csv#{pair_key}",
        "deterministic_context": {
            "co_participating_relation_ids": relation_ids,
            "co_participation_semantics": "Both features appear in one locked Task 9 deterministic identity row.",
        },
        "direct_deterministic_dependency": bool(relation_ids),
        "direct_deterministic_relation_ids": relation_ids,
        "feature_x": feature_x,
        "feature_x_analysis_role": f"role:{feature_x}",
        "feature_x_direction_semantics": f"direction:{feature_x}",
        "feature_x_formula": f"formula:{feature_x}",
        "feature_y": feature_y,
        "feature_y_analysis_role": f"role:{feature_y}",
        "feature_y_direction_semantics": f"direction:{feature_y}",
        "feature_y_formula": f"formula:{feature_y}",
        "observations": [f"record-{index}", f"pair-{pair_key}"],
        "pair_key": pair_key,
        "partial_applicability": ELIGIBLE if eligible else CONTROL_NOT_APPLICABLE,
        "partial_by_tf": {
            tf: _eligible_partial(feature_x, feature_y, index + position)
            if eligible else _control_partial()
            for position, tf in enumerate(TIMEFRAMES)
        },
        "partial_source_artifact_by_tf": {
            tf: f"PARTIAL_SPEARMAN_{tf}.csv" if eligible else None for tf in TIMEFRAMES
        },
        "partial_source_row_locator_by_tf": {
            tf: f"PARTIAL_SPEARMAN_{tf}.csv#{pair_key}" if eligible else CONTROL_NOT_APPLICABLE
            for tf in TIMEFRAMES
        },
        "raw_by_tf": {
            tf: _raw(feature_x, feature_y, index + position) for position, tf in enumerate(TIMEFRAMES)
        },
        "raw_source_artifact_by_tf": {tf: f"MAIN_SPEARMAN_{tf}.csv" for tf in TIMEFRAMES},
        "raw_source_row_locator_by_tf": {
            tf: f"MAIN_SPEARMAN_{tf}.csv#{pair_key}" for tf in TIMEFRAMES
        },
        "source_pair_key": pair_key,
    }


def make_synthetic_task10_production_zip(
    *,
    mutate: Callable[[dict[str, bytes]], None] | None = None,
    duplicate_member: str | None = None,
    extra_member: str | None = None,
) -> bytes:
    """Build a complete test-only copy-shaped Task 10 package."""
    dossiers = [_dossier(pair_key, index) for index, pair_key in enumerate(TASK10_CANONICAL_PAIR_KEYS)]
    output = io.StringIO(newline="")
    csv.writer(output).writerows((("source", "value"), ("synthetic", "1")))
    members = {
        MAIN: _json_bytes(dossiers),
        SUPPLEMENTARY: output.getvalue().encode("utf-8"),
        FEATURES: _json_bytes([{"feature": "active_bar_count"}]),
        HYPOTHESES: _json_bytes([]),
        MANIFEST: _json_bytes(dict(TASK10_MANIFEST_EXPECTED_VALUES)),
    }
    if mutate is not None:
        mutate(members)
    package = io.BytesIO()
    with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in members.items():
            archive.writestr(name, data)
        if duplicate_member is not None:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                archive.writestr(duplicate_member, members[duplicate_member])
        if extra_member is not None:
            archive.writestr(extra_member, b"{}")
    return package.getvalue()


def member_sha256_by_filename(package_bytes: bytes) -> dict[str, str]:
    with zipfile.ZipFile(io.BytesIO(package_bytes)) as archive:
        return {info.filename: hashlib.sha256(archive.read(info)).hexdigest() for info in archive.infolist()}


def load_synthetic_task10(package_bytes: bytes) -> Task10ProductionBundle:
    return _load_task10_production_bytes(
        package_bytes,
        expected_package_sha256=hashlib.sha256(package_bytes).hexdigest(),
        expected_member_sha256_by_filename=member_sha256_by_filename(package_bytes),
    )


def _mutate_main(members: dict[str, bytes], change: Callable[[list[dict[str, object]]], None]) -> None:
    dossiers = _read_json(members, MAIN)
    assert isinstance(dossiers, list)
    change(dossiers)
    _write_json(members, MAIN, dossiers)


def test_public_loader_rejects_noncanonical_sha_before_zip_parse(tmp_path: Path):
    path = tmp_path / "not-a-zip.bin"
    path.write_bytes(b"not a zip")
    with pytest.raises(ValueError, match="Task 10 Production SHA-256 mismatch"):
        load_task10_production_package(path)


def test_public_loader_has_no_hash_or_bundle_override():
    parameters = inspect.signature(load_task10_production_package).parameters
    assert tuple(parameters) == ("path",)


def test_private_loader_loads_complete_frozen_bundle_and_immutable_boundary():
    bundle = load_synthetic_task10(make_synthetic_task10_production_zip())
    assert len(bundle.main_dossiers) == 78
    assert tuple(item["pair_key"] for item in bundle.main_dossiers) == TASK10_CANONICAL_PAIR_KEYS
    assert bundle.main_dossiers[0]["raw_by_tf"]["M5"]["n_total"] == 1000
    assert bundle.manifest["task10_implementation_commit"] == TASK10_MANIFEST_EXPECTED_VALUES["task10_implementation_commit"]
    with pytest.raises(TypeError):
        bundle.manifest["task"] = "changed"  # type: ignore[index]
    with pytest.raises(TypeError):
        bundle.main_dossiers[0]["raw_by_tf"]["M5"]["n_total"] = 0  # type: ignore[index]


def test_private_loader_rejects_duplicate_and_unsafe_members():
    duplicate = make_synthetic_task10_production_zip(duplicate_member=MANIFEST)
    with pytest.raises(ValueError, match="duplicate ZIP members"):
        load_synthetic_task10(duplicate)
    unsafe = make_synthetic_task10_production_zip(extra_member="../escape.json")
    with pytest.raises(ValueError, match="unsafe ZIP member"):
        load_synthetic_task10(unsafe)


@pytest.mark.parametrize("name", ("/absolute.json", "directory/", r"back\\slash.json", "empty//part.json", "./dot.json", "dot/../parent.json"))
def test_private_loader_rejects_every_unsafe_zip_member_name(name: str):
    package = make_synthetic_task10_production_zip(extra_member=name)
    with pytest.raises(ValueError, match="unsafe ZIP member"):
        load_synthetic_task10(package)


def test_private_loader_rejects_missing_and_unexpected_safe_zip_members():
    def missing(members: dict[str, bytes]) -> None:
        del members[FEATURES]
    with pytest.raises(ValueError, match="ZIP members.*missing"):
        load_synthetic_task10(make_synthetic_task10_production_zip(mutate=missing))
    with pytest.raises(ValueError, match="ZIP members.*unexpected"):
        load_synthetic_task10(make_synthetic_task10_production_zip(extra_member="extra.json"))


@pytest.mark.parametrize(
    "extra_member,expected_error",
    (("../escape.json", "unsafe ZIP member"), ("extra.json", "ZIP members.*unexpected")),
)
def test_zip_safety_and_exact_set_win_before_member_hash_comparison(
    extra_member: str, expected_error: str
):
    package = make_synthetic_task10_production_zip(extra_member=extra_member)
    with pytest.raises(ValueError, match=expected_error):
        _load_task10_production_bytes(
            package,
            expected_package_sha256=hashlib.sha256(package).hexdigest(),
            expected_member_sha256_by_filename={},
        )


def test_member_sha_mismatch_stops_before_json_decode(monkeypatch):
    package = make_synthetic_task10_production_zip()
    expected_members = member_sha256_by_filename(package)
    expected_members[MANIFEST] = "0" * 64
    import research.task11_hypothesis_io as module
    monkeypatch.setattr(module, "_decode_json", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("JSON decode ran before member SHA validation")))
    with pytest.raises(ValueError, match="member SHA-256 mismatch"):
        _load_task10_production_bytes(package, expected_package_sha256=hashlib.sha256(package).hexdigest(), expected_member_sha256_by_filename=expected_members)


@pytest.mark.parametrize(
    "member,replacement,error",
    [
        (MAIN, b"{bad json", "valid UTF-8 JSON"),
        (FEATURES, b'[{"x":NaN}]', "non-finite JSON"),
        (MANIFEST, b'{"task":1,"task":2}', "duplicate JSON key"),
        (SUPPLEMENTARY, b"\xff", "must be UTF-8"),
    ],
)
def test_private_loader_rejects_malformed_member_content(member: str, replacement: bytes, error: str):
    package = make_synthetic_task10_production_zip(mutate=lambda members: members.__setitem__(member, replacement))
    with pytest.raises(ValueError, match=error):
        load_synthetic_task10(package)


def test_all_member_parsing_wins_over_main_dossier_structural_validation():
    def mutate(members: dict[str, bytes]) -> None:
        _mutate_main(members, lambda dossiers: dossiers[0].pop("observations"))
        members[FEATURES] = b"{bad json"

    with pytest.raises(ValueError, match=f"{FEATURES}.*valid UTF-8 JSON"):
        load_synthetic_task10(make_synthetic_task10_production_zip(mutate=mutate))


@pytest.mark.parametrize("count", (77, 79))
def test_main_dossier_array_requires_exact_count(count: int):
    def change(dossiers: list[dict[str, object]]) -> None:
        if count == 77:
            dossiers.pop()
        else:
            dossiers.append(dict(dossiers[-1]))
    with pytest.raises(ValueError, match=f"{MAIN}.*78"):
        load_synthetic_task10(make_synthetic_task10_production_zip(mutate=lambda members: _mutate_main(members, change)))


def test_main_dossier_root_must_be_array():
    package = make_synthetic_task10_production_zip(mutate=lambda members: _write_json(members, MAIN, {}))
    with pytest.raises(ValueError, match=f"{MAIN}.*array"):
        load_synthetic_task10(package)


@pytest.mark.parametrize("change", (lambda dossiers: dossiers.reverse(), lambda dossiers: dossiers.__setitem__(slice(0, 2), [dossiers[1], dossiers[0]])))
def test_main_dossier_order_is_exact_canonical_source_order(change):
    with pytest.raises(ValueError, match="canonical pair order"):
        load_synthetic_task10(make_synthetic_task10_production_zip(mutate=lambda members: _mutate_main(members, change)))


def test_main_dossier_rejects_duplicate_pair_key():
    def change(dossiers: list[dict[str, object]]) -> None:
        dossiers[1] = dict(dossiers[0])
    with pytest.raises(ValueError, match=f"{MAIN}.*duplicate pair_key"):
        load_synthetic_task10(make_synthetic_task10_production_zip(mutate=lambda members: _mutate_main(members, change)))


@pytest.mark.parametrize("mode", ("missing", "extra"))
def test_main_dossier_top_level_schema_is_closed(mode: str):
    def change(dossiers: list[dict[str, object]]) -> None:
        if mode == "missing":
            del dossiers[0]["observations"]
        else:
            dossiers[0]["surprise"] = True
    with pytest.raises(ValueError, match=f"{MAIN}.*{TASK10_CANONICAL_PAIR_KEYS[0]}.*fields"):
        load_synthetic_task10(make_synthetic_task10_production_zip(mutate=lambda members: _mutate_main(members, change)))


@pytest.mark.parametrize(
    "field,value,pair_fragment",
    (("pair_key", "wrong", "wrong"), ("feature_y", "active_bar_count", TASK10_CANONICAL_PAIR_KEYS[0]), ("feature_x", 1, TASK10_CANONICAL_PAIR_KEYS[0])),
)
def test_main_dossier_pair_identity_is_strict(field: str, value: object, pair_fragment: str):
    def change(dossiers: list[dict[str, object]]) -> None:
        dossiers[0][field] = value
    with pytest.raises(ValueError, match=f"{MAIN}.*{pair_fragment}"):
        load_synthetic_task10(make_synthetic_task10_production_zip(mutate=lambda members: _mutate_main(members, change)))


@pytest.mark.parametrize(
    "map_name",
    (
        "raw_by_tf",
        "partial_by_tf",
        "raw_source_artifact_by_tf",
        "raw_source_row_locator_by_tf",
        "partial_source_artifact_by_tf",
        "partial_source_row_locator_by_tf",
    ),
)
@pytest.mark.parametrize("operation", ("missing", "extra"))
def test_timeframe_maps_have_exact_locked_keys(map_name: str, operation: str):
    def change(dossiers: list[dict[str, object]]) -> None:
        mapping = dossiers[0][map_name]
        assert isinstance(mapping, dict)
        if operation == "missing":
            del mapping["M5"]
        else:
            mapping["D1"] = mapping["M5"]
    with pytest.raises(ValueError, match=f"{MAIN}.*{TASK10_CANONICAL_PAIR_KEYS[0]}.*{map_name}"):
        load_synthetic_task10(make_synthetic_task10_production_zip(mutate=lambda members: _mutate_main(members, change)))


@pytest.mark.parametrize("field", ("raw_by_tf", "cross_tf", "deterministic_context"))
def test_nested_source_schema_is_closed(field: str):
    def change(dossiers: list[dict[str, object]]) -> None:
        container = dossiers[0][field]
        if field in {"raw_by_tf", "partial_by_tf"}:
            assert isinstance(container, dict)
            container["M5"].pop(next(iter(container["M5"])))
        else:
            assert isinstance(container, dict)
            container["unexpected"] = True
    with pytest.raises(ValueError, match=f"{MAIN}.*{TASK10_CANONICAL_PAIR_KEYS[0]}"):
        load_synthetic_task10(make_synthetic_task10_production_zip(mutate=lambda members: _mutate_main(members, change)))


def test_eligible_partial_schema_is_closed_for_an_eligible_pair():
    pair_key = TASK10_CANONICAL_PAIR_KEYS[12]

    def change(dossiers: list[dict[str, object]]) -> None:
        dossiers[12]["partial_by_tf"]["M5"].pop("feature_x")

    with pytest.raises(ValueError, match=f"{MAIN}.*{pair_key}.*M5.*partial.*fields"):
        load_synthetic_task10(make_synthetic_task10_production_zip(mutate=lambda members: _mutate_main(members, change)))


def test_cross_tf_defined_and_undefined_counts_sum_to_four():
    def change(dossiers: list[dict[str, object]]) -> None:
        dossiers[0]["cross_tf"]["n_defined_tf"] = 3
    with pytest.raises(ValueError, match=f"{MAIN}.*{TASK10_CANONICAL_PAIR_KEYS[0]}.*n_defined_tf"):
        load_synthetic_task10(make_synthetic_task10_production_zip(mutate=lambda members: _mutate_main(members, change)))


@pytest.mark.parametrize("change", (
    lambda dossiers: dossiers[12].__setitem__("partial_applicability", CONTROL_NOT_APPLICABLE),
    lambda dossiers: dossiers[0].__setitem__("partial_applicability", ELIGIBLE),
))
def test_control_pair_applicability_is_locked(change):
    with pytest.raises(ValueError, match=f"{MAIN}.*(partial_applicability|66/12)"):
        load_synthetic_task10(make_synthetic_task10_production_zip(mutate=lambda members: _mutate_main(members, change)))


def test_applicability_counts_must_remain_66_eligible_and_12_control():
    def change(dossiers: list[dict[str, object]]) -> None:
        dossiers[12]["partial_applicability"] = CONTROL_NOT_APPLICABLE
    with pytest.raises(ValueError, match=f"{MAIN}.*66/12"):
        load_synthetic_task10(make_synthetic_task10_production_zip(mutate=lambda members: _mutate_main(members, change)))


@pytest.mark.parametrize("field,value", (("rho_raw_for_delta", 0.2), ("status", "DEFINED")))
def test_control_partial_rows_are_exact_non_applicable_nulls(field: str, value: object):
    def change(dossiers: list[dict[str, object]]) -> None:
        dossiers[0]["partial_by_tf"]["M5"][field] = value
    with pytest.raises(ValueError, match=f"{MAIN}.*{TASK10_CANONICAL_PAIR_KEYS[0]}.*M5.*partial"):
        load_synthetic_task10(make_synthetic_task10_production_zip(mutate=lambda members: _mutate_main(members, change)))


@pytest.mark.parametrize("where", ("raw", "eligible"))
def test_statistical_statuses_are_locked(where: str):
    def change(dossiers: list[dict[str, object]]) -> None:
        record = dossiers[12] if where == "eligible" else dossiers[0]
        map_name = "partial_by_tf" if where == "eligible" else "raw_by_tf"
        record[map_name]["M5"]["status"] = "OTHER"
    with pytest.raises(ValueError, match=f"{MAIN}.*status"):
        load_synthetic_task10(make_synthetic_task10_production_zip(mutate=lambda members: _mutate_main(members, change)))


@pytest.mark.parametrize("where", ("raw", "eligible"))
def test_statistical_statuses_must_be_json_strings(where: str):
    pair_index = 12 if where == "eligible" else 0
    pair_key = TASK10_CANONICAL_PAIR_KEYS[pair_index]

    def change(dossiers: list[dict[str, object]]) -> None:
        record = dossiers[pair_index]
        map_name = "partial_by_tf" if where == "eligible" else "raw_by_tf"
        record[map_name]["M5"]["status"] = True

    with pytest.raises(ValueError, match=f"{MAIN}.*{pair_key}.*M5.*status.*text"):
        load_synthetic_task10(make_synthetic_task10_production_zip(mutate=lambda members: _mutate_main(members, change)))


def test_deterministic_context_must_match_exact_locked_four_pairs():
    target = next(iter(DETERMINISTIC_RELATION_IDS_BY_PAIR_KEY))
    target_index = TASK10_CANONICAL_PAIR_KEYS.index(target)
    def change(dossiers: list[dict[str, object]]) -> None:
        dossiers[target_index]["direct_deterministic_relation_ids"] = []
    with pytest.raises(ValueError, match=f"{MAIN}.*{target}.*deterministic"):
        load_synthetic_task10(make_synthetic_task10_production_zip(mutate=lambda members: _mutate_main(members, change)))


def test_fifth_pair_cannot_be_marked_direct_deterministic():
    pair_key = TASK10_CANONICAL_PAIR_KEYS[0]

    def change(dossiers: list[dict[str, object]]) -> None:
        dossier = dossiers[0]
        dossier["direct_deterministic_dependency"] = True
        dossier["direct_deterministic_relation_ids"] = ["FORGED_FIFTH_RELATION"]
        dossier["deterministic_context"]["co_participating_relation_ids"] = ["FORGED_FIFTH_RELATION"]

    with pytest.raises(ValueError, match=f"{MAIN}.*{pair_key}.*deterministic"):
        load_synthetic_task10(make_synthetic_task10_production_zip(mutate=lambda members: _mutate_main(members, change)))


def test_artifact_and_locator_maps_must_agree_with_control_structure():
    def change(dossiers: list[dict[str, object]]) -> None:
        dossiers[0]["partial_source_artifact_by_tf"]["M5"] = "PARTIAL_SPEARMAN_M5.csv"
    with pytest.raises(ValueError, match=f"{MAIN}.*{TASK10_CANONICAL_PAIR_KEYS[0]}.*partial_source_artifact"):
        load_synthetic_task10(make_synthetic_task10_production_zip(mutate=lambda members: _mutate_main(members, change)))


@pytest.mark.parametrize("change", (
    lambda manifest: manifest.pop("task"),
    lambda manifest: manifest.__setitem__("extra", False),
    lambda manifest: manifest.__setitem__("task10_implementation_commit", "0" * 40),
    lambda manifest: manifest.__setitem__("task9_audit_code_commit", "0" * 40),
    lambda manifest: manifest.__setitem__("main_relationship_dossier_count", 77),
    lambda manifest: manifest.__setitem__("ranking_performed", True),
))
def test_manifest_is_exact_locked_task10_provenance(change):
    def mutate(members: dict[str, bytes]) -> None:
        manifest = _read_json(members, MANIFEST)
        assert isinstance(manifest, dict)
        change(manifest)
        _write_json(members, MANIFEST, manifest)
    with pytest.raises(ValueError, match=MANIFEST):
        load_synthetic_task10(make_synthetic_task10_production_zip(mutate=mutate))


def test_future_hypotheses_must_be_exact_empty_array():
    package = make_synthetic_task10_production_zip(mutate=lambda members: _write_json(members, HYPOTHESES, [{}]))
    with pytest.raises(ValueError, match=f"{HYPOTHESES}.*empty"):
        load_synthetic_task10(package)


def test_supplementary_csv_must_be_strictly_parseable():
    package = make_synthetic_task10_production_zip(mutate=lambda members: members.__setitem__(SUPPLEMENTARY, b'one,"unterminated'))
    with pytest.raises(ValueError, match=f"{SUPPLEMENTARY}.*malformed"):
        load_synthetic_task10(package)
