"""Fail-closed reader for the canonical Task 10 Production package."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import zipfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from research.task11_hypothesis_contract import (
    CONTROL_FEATURE,
    CONTROL_FEATURE_NON_APPLICABLE_COUNT,
    CONTROL_NOT_APPLICABLE,
    DETERMINISTIC_RELATION_IDS_BY_PAIR_KEY,
    DURATION_CONTROL_ELIGIBLE_COUNT,
    ELIGIBLE,
    LOCKED_STATISTICAL_STATUSES,
    MAIN_PAIR_COUNT,
    TASK10_CANONICAL_PAIR_KEYS,
    TASK10_CONTROL_PARTIAL_TF_FIELDS,
    TASK10_CROSS_TF_FIELDS,
    TASK10_DETERMINISTIC_CONTEXT_FIELDS,
    TASK10_ELIGIBLE_PARTIAL_TF_FIELDS,
    TASK10_MAIN_DOSSIER_FIELDS,
    TASK10_MANIFEST_EXPECTED_VALUES,
    TASK10_MANIFEST_FIELDS,
    TASK10_MEMBER_SHA256_BY_FILENAME,
    TASK10_PRODUCTION_PACKAGE_SHA256,
    TASK10_RAW_TF_FIELDS,
    DETERMINISTIC_CONTEXT_PAIR_COUNT,
    HYPOTHESIS_COUNT,
    HYPOTHESIS_ID_PREFIX,
    LOGICAL_FILE_COUNT,
    OUTPUT_ZIP_FILENAME,
    TASK10_IMPLEMENTATION_COMMIT,
    TASK10_MAIN_DOSSIERS_MEMBER_SHA256,
    TASK10_MANIFEST_MEMBER_SHA256,
    TASK10_PRODUCTION_PACKAGE_FILENAME,
    TASK11_FALSE_SCOPE_FIELDS,
    TASK11_LOGICAL_FILENAMES,
    TASK11_MANIFEST_FIELDS,
    TASK11_SPEC_COMMIT,
    TEST_QUESTION_TEMPLATE_ID,
    TIMEFRAMES,
)


_MAIN = "TASK10_MAIN_RELATIONSHIP_DOSSIERS.json"
_SUPPLEMENTARY = "TASK10_SUPPLEMENTARY_EVIDENCE.csv"
_FEATURES = "TASK10_FEATURE_DOSSIERS.json"
_HYPOTHESES = "TASK10_FUTURE_ABLATION_HYPOTHESES.json"
_MANIFEST = "TASK10_MANIFEST.json"
_EXPECTED_MEMBERS = frozenset(TASK10_MEMBER_SHA256_BY_FILENAME)
_DETERMINISTIC_SEMANTICS = (
    "Both features appear in one locked Task 9 deterministic identity row."
)


@dataclass(frozen=True, slots=True)
class Task10ProductionBundle:
    main_dossiers: Sequence[Mapping[str, object]]
    manifest: Mapping[str, object]
    production_zip_sha256: str
    member_sha256_by_filename: Mapping[str, str]


class _DuplicateJSONKey(ValueError):
    pass


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJSONKey(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_nonfinite_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant {value!r}")


def _validate_json_finite(value: object) -> None:
    if type(value) is float and not math.isfinite(value):
        raise ValueError("non-finite JSON float")
    if type(value) is list:
        for item in value:
            _validate_json_finite(item)
    elif type(value) is dict:
        for item in value.values():
            _validate_json_finite(item)


def _decode_json(name: str, data: bytes) -> object:
    try:
        decoded = json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_json_keys,
            parse_constant=_reject_nonfinite_constant,
        )
        _validate_json_finite(decoded)
        return decoded
    except _DuplicateJSONKey as exc:
        raise ValueError(f"{name} contains {exc}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{name} must contain valid UTF-8 JSON: {exc}") from exc
    except ValueError as exc:
        raise ValueError(f"{name} contains non-finite JSON: {exc}") from exc


def _validate_csv(name: str, data: bytes) -> None:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{name} must be UTF-8: {exc}") from exc
    try:
        list(csv.reader(io.StringIO(text, newline=""), strict=True))
    except csv.Error as exc:
        raise ValueError(f"{name} contains malformed CSV: {exc}") from exc


def _member_counts(archive: zipfile.ZipFile) -> dict[str, int]:
    counts: dict[str, int] = {}
    for info in archive.infolist():
        name = info.filename
        if (
            not name
            or "\\" in name
            or name.startswith("/")
            or name.endswith("/")
            or any(component in {"", ".", ".."} for component in name.split("/"))
        ):
            raise ValueError(f"Task 10 Production contains unsafe ZIP member name {name!r}")
        counts[name] = counts.get(name, 0) + 1
    duplicates = sorted(name for name, count in counts.items() if count > 1)
    if duplicates:
        raise ValueError(f"Task 10 Production contains duplicate ZIP members: {duplicates}")
    return counts


def _read_exact_members(package_bytes: bytes) -> dict[str, bytes]:
    try:
        archive_context = zipfile.ZipFile(io.BytesIO(package_bytes))
    except zipfile.BadZipFile as exc:
        raise ValueError(f"Task 10 Production is not a valid ZIP: {exc}") from exc
    with archive_context as archive:
        counts = _member_counts(archive)
        names = set(counts)
        if names != _EXPECTED_MEMBERS:
            raise ValueError(
                "Task 10 Production ZIP members do not match the locked set: "
                f"missing={sorted(_EXPECTED_MEMBERS - names)}, "
                f"unexpected={sorted(names - _EXPECTED_MEMBERS)}"
            )
        return {name: archive.read(name) for name in _EXPECTED_MEMBERS}


def _freeze(value: object) -> object:
    if type(value) is dict:
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if type(value) is list:
        return tuple(_freeze(item) for item in value)
    return value


def _exact_keys(name: str, location: str, value: object, expected: Sequence[str]) -> dict[str, object]:
    if type(value) is not dict:
        raise ValueError(f"{name}: {location} must be a JSON object")
    if set(value) != set(expected):
        raise ValueError(
            f"{name}: {location} fields do not match locked schema: "
            f"missing={sorted(set(expected) - set(value))}, unexpected={sorted(set(value) - set(expected))}"
        )
    return value


def _timeframe_mapping(name: str, pair_key: str, field: str, value: object) -> dict[str, object]:
    return _exact_keys(name, f"pair_key {pair_key} {field}", value, TIMEFRAMES)


def _nonblank_text(name: str, location: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{name}: {location} must be nonblank text")
    return value


def _integer(name: str, location: str, value: object, *, nullable: bool = False) -> int | None:
    if nullable and value is None:
        return None
    if type(value) is not int:
        raise ValueError(f"{name}: {location} must be an integer")
    return value


def _number(name: str, location: str, value: object, *, nullable: bool = False) -> float | int | None:
    if nullable and value is None:
        return None
    if type(value) is int:
        return value
    if type(value) is not float or not math.isfinite(value):
        raise ValueError(f"{name}: {location} must be a finite number")
    return value


def _validate_raw(name: str, pair_key: str, timeframe: str, value: object, feature_x: str, feature_y: str) -> None:
    raw = _exact_keys(name, f"pair_key {pair_key} timeframe {timeframe} raw", value, TASK10_RAW_TF_FIELDS)
    if raw["feature_x"] != feature_x or raw["feature_y"] != feature_y:
        raise ValueError(f"{name}: pair_key {pair_key} timeframe {timeframe} raw feature identity conflicts")
    for field in ("n_missing_x", "n_missing_y", "n_total", "n_valid_pairwise"):
        _integer(name, f"pair_key {pair_key} timeframe {timeframe} raw {field}", raw[field])
    _number(name, f"pair_key {pair_key} timeframe {timeframe} raw rho_raw", raw["rho_raw"], nullable=True)
    if type(raw["status"]) is not str:
        raise ValueError(f"{name}: pair_key {pair_key} timeframe {timeframe} raw status must be text")
    if raw["status"] not in LOCKED_STATISTICAL_STATUSES:
        raise ValueError(f"{name}: pair_key {pair_key} timeframe {timeframe} raw status is not locked")


def _validate_partial(name: str, pair_key: str, timeframe: str, value: object, feature_x: str, feature_y: str, eligible: bool) -> None:
    fields = TASK10_ELIGIBLE_PARTIAL_TF_FIELDS if eligible else TASK10_CONTROL_PARTIAL_TF_FIELDS
    partial = _exact_keys(name, f"pair_key {pair_key} timeframe {timeframe} partial", value, fields)
    if eligible:
        if partial["feature_x"] != feature_x or partial["feature_y"] != feature_y:
            raise ValueError(f"{name}: pair_key {pair_key} timeframe {timeframe} partial feature identity conflicts")
        for field in ("rho_raw_for_delta", "rho_duration_controlled", "delta_rho"):
            _number(name, f"pair_key {pair_key} timeframe {timeframe} partial {field}", partial[field], nullable=True)
        _integer(name, f"pair_key {pair_key} timeframe {timeframe} partial n_valid_triple", partial["n_valid_triple"], nullable=True)
        if type(partial["status"]) is not str:
            raise ValueError(f"{name}: pair_key {pair_key} timeframe {timeframe} partial status must be text")
        if partial["status"] not in LOCKED_STATISTICAL_STATUSES:
            raise ValueError(f"{name}: pair_key {pair_key} timeframe {timeframe} partial status is not locked")
    else:
        for field in ("rho_raw_for_delta", "rho_duration_controlled", "delta_rho", "n_valid_triple"):
            if partial[field] is not None:
                raise ValueError(f"{name}: pair_key {pair_key} timeframe {timeframe} partial {field} must be JSON null")
        if partial["status"] != CONTROL_NOT_APPLICABLE:
            raise ValueError(f"{name}: pair_key {pair_key} timeframe {timeframe} partial status must be {CONTROL_NOT_APPLICABLE}")


def _validate_cross(name: str, pair_key: str, value: object, feature_x: str, feature_y: str, eligible: bool) -> None:
    cross = _exact_keys(name, f"pair_key {pair_key} cross_tf", value, TASK10_CROSS_TF_FIELDS)
    if cross["feature_x"] != feature_x or cross["feature_y"] != feature_y:
        raise ValueError(f"{name}: pair_key {pair_key} cross_tf feature identity conflicts")
    if type(cross["controlled_eligible"]) is not bool or cross["controlled_eligible"] is not eligible:
        raise ValueError(f"{name}: pair_key {pair_key} cross_tf controlled eligibility conflicts")
    for field in ("n_defined_tf", "n_negative_tf", "n_positive_tf", "n_undefined_tf", "n_valid_H1", "n_valid_M15", "n_valid_M30", "n_valid_M5", "n_zero_tf", "sign_agreement_count"):
        _integer(name, f"pair_key {pair_key} cross_tf {field}", cross[field], nullable=field.startswith("n_valid_"))
    if cross["n_defined_tf"] + cross["n_undefined_tf"] != len(TIMEFRAMES):
        raise ValueError(f"{name}: pair_key {pair_key} cross_tf n_defined_tf + n_undefined_tf must equal 4")
    for field in ("controlled_rho_H1", "controlled_rho_M15", "controlled_rho_M30", "controlled_rho_M5", "rho_H1", "rho_M15", "rho_M30", "rho_M5", "rho_max", "rho_min", "rho_range"):
        _number(name, f"pair_key {pair_key} cross_tf {field}", cross[field], nullable=True)
    if type(cross["sign_agreement_modal_signs"]) is not list or any(type(item) is not str for item in cross["sign_agreement_modal_signs"]):
        raise ValueError(f"{name}: pair_key {pair_key} cross_tf sign_agreement_modal_signs must be string array")
    if type(cross["sign_agreement_tie"]) is not bool:
        raise ValueError(f"{name}: pair_key {pair_key} cross_tf sign_agreement_tie must be boolean")
    for field in ("controlled_rho_H1", "controlled_rho_M15", "controlled_rho_M30", "controlled_rho_M5"):
        if not eligible and cross[field] is not None:
            raise ValueError(f"{name}: pair_key {pair_key} cross_tf {field} must be JSON null for control pair")


def _validate_locators(name: str, pair_key: str, dossier: dict[str, object], eligible: bool) -> None:
    raw_artifacts = _timeframe_mapping(name, pair_key, "raw_source_artifact_by_tf", dossier["raw_source_artifact_by_tf"])
    raw_locators = _timeframe_mapping(name, pair_key, "raw_source_row_locator_by_tf", dossier["raw_source_row_locator_by_tf"])
    partial_artifacts = _timeframe_mapping(name, pair_key, "partial_source_artifact_by_tf", dossier["partial_source_artifact_by_tf"])
    partial_locators = _timeframe_mapping(name, pair_key, "partial_source_row_locator_by_tf", dossier["partial_source_row_locator_by_tf"])
    for timeframe in TIMEFRAMES:
        if raw_artifacts[timeframe] != f"MAIN_SPEARMAN_{timeframe}.csv" or raw_locators[timeframe] != f"MAIN_SPEARMAN_{timeframe}.csv#{pair_key}":
            raise ValueError(f"{name}: pair_key {pair_key} timeframe {timeframe} raw source locator conflicts")
        if eligible:
            if partial_artifacts[timeframe] != f"PARTIAL_SPEARMAN_{timeframe}.csv" or partial_locators[timeframe] != f"PARTIAL_SPEARMAN_{timeframe}.csv#{pair_key}":
                raise ValueError(f"{name}: pair_key {pair_key} timeframe {timeframe} partial source locator conflicts")
        elif partial_artifacts[timeframe] is not None or partial_locators[timeframe] != CONTROL_NOT_APPLICABLE:
            raise ValueError(f"{name}: pair_key {pair_key} timeframe {timeframe} partial_source_artifact conflicts with control structure")
    if dossier["cross_tf_source_artifact"] != "CROSS_TF_RELATIONSHIP_REPORT.csv" or dossier["cross_tf_source_row_locator"] != f"CROSS_TF_RELATIONSHIP_REPORT.csv#{pair_key}":
        raise ValueError(f"{name}: pair_key {pair_key} cross_tf source locator conflicts")


def _validate_main_dossiers(value: object) -> Sequence[Mapping[str, object]]:
    if type(value) is not list:
        raise ValueError(f"{_MAIN} must be a JSON array")
    if len(value) != MAIN_PAIR_COUNT:
        raise ValueError(f"{_MAIN} must contain exactly {MAIN_PAIR_COUNT} dossiers")
    declared_eligible_count = sum(
        type(dossier) is dict and dossier.get("partial_applicability") == ELIGIBLE
        for dossier in value
    )
    declared_control_count = sum(
        type(dossier) is dict and dossier.get("partial_applicability") == CONTROL_NOT_APPLICABLE
        for dossier in value
    )
    if (declared_eligible_count, declared_control_count) != (
        DURATION_CONTROL_ELIGIBLE_COUNT,
        CONTROL_FEATURE_NON_APPLICABLE_COUNT,
    ):
        raise ValueError(f"{_MAIN} applicability counts must remain 66/12")
    observed: list[str] = []
    eligible_count = 0
    control_count = 0
    for index, raw_dossier in enumerate(value):
        fallback_pair = f"index {index}"
        if type(raw_dossier) is not dict:
            raise ValueError(f"{_MAIN}: {fallback_pair} must be a JSON object")
        pair_key = raw_dossier.get("pair_key")
        if type(pair_key) is not str:
            raise ValueError(f"{_MAIN}: {fallback_pair} pair_key must be text")
        dossier = _exact_keys(_MAIN, f"pair_key {pair_key}", raw_dossier, TASK10_MAIN_DOSSIER_FIELDS)
        feature_x = _nonblank_text(_MAIN, f"pair_key {pair_key} feature_x", dossier["feature_x"])
        feature_y = _nonblank_text(_MAIN, f"pair_key {pair_key} feature_y", dossier["feature_y"])
        if feature_x == feature_y or pair_key != f"{feature_x}__{feature_y}" or dossier["source_pair_key"] != pair_key:
            raise ValueError(f"{_MAIN}: pair_key {pair_key} feature identity conflicts")
        if pair_key in observed:
            raise ValueError(f"{_MAIN}: duplicate pair_key {pair_key}")
        observed.append(pair_key)
        for field in ("feature_x_analysis_role", "feature_x_direction_semantics", "feature_x_formula", "feature_y_analysis_role", "feature_y_direction_semantics", "feature_y_formula"):
            _nonblank_text(_MAIN, f"pair_key {pair_key} {field}", dossier[field])
        if type(dossier["observations"]) is not list or any(type(item) is not str for item in dossier["observations"]):
            raise ValueError(f"{_MAIN}: pair_key {pair_key} observations must be a string array")
        eligible = CONTROL_FEATURE not in (feature_x, feature_y)
        expected_applicability = ELIGIBLE if eligible else CONTROL_NOT_APPLICABLE
        if dossier["partial_applicability"] != expected_applicability:
            raise ValueError(f"{_MAIN}: pair_key {pair_key} partial_applicability conflicts with locked control structure")
        eligible_count += eligible
        control_count += not eligible
        raw_by_tf = _timeframe_mapping(_MAIN, pair_key, "raw_by_tf", dossier["raw_by_tf"])
        partial_by_tf = _timeframe_mapping(_MAIN, pair_key, "partial_by_tf", dossier["partial_by_tf"])
        for timeframe in TIMEFRAMES:
            _validate_raw(_MAIN, pair_key, timeframe, raw_by_tf[timeframe], feature_x, feature_y)
            _validate_partial(_MAIN, pair_key, timeframe, partial_by_tf[timeframe], feature_x, feature_y, eligible)
        _validate_cross(_MAIN, pair_key, dossier["cross_tf"], feature_x, feature_y, eligible)
        relation_ids = DETERMINISTIC_RELATION_IDS_BY_PAIR_KEY.get(pair_key, ())
        context = _exact_keys(_MAIN, f"pair_key {pair_key} deterministic_context", dossier["deterministic_context"], TASK10_DETERMINISTIC_CONTEXT_FIELDS)
        if (type(dossier["direct_deterministic_dependency"]) is not bool or dossier["direct_deterministic_dependency"] is not bool(relation_ids) or type(dossier["direct_deterministic_relation_ids"]) is not list or tuple(dossier["direct_deterministic_relation_ids"]) != relation_ids or type(context["co_participating_relation_ids"]) is not list or tuple(context["co_participating_relation_ids"]) != relation_ids or context["co_participation_semantics"] != _DETERMINISTIC_SEMANTICS):
            raise ValueError(f"{_MAIN}: pair_key {pair_key} deterministic context conflicts with locked Task 10 contract")
        _validate_locators(_MAIN, pair_key, dossier, eligible)
    if tuple(observed) != TASK10_CANONICAL_PAIR_KEYS:
        raise ValueError(f"{_MAIN} canonical pair order does not match locked Task 10 source order")
    if (eligible_count, control_count) != (DURATION_CONTROL_ELIGIBLE_COUNT, CONTROL_FEATURE_NON_APPLICABLE_COUNT):
        raise ValueError(f"{_MAIN} applicability counts must remain 66/12")
    return tuple(_freeze(dossier) for dossier in value)


def _validate_task10_manifest(value: object) -> Mapping[str, object]:
    manifest = _exact_keys(_MANIFEST, "manifest", value, TASK10_MANIFEST_FIELDS)
    for field, expected in TASK10_MANIFEST_EXPECTED_VALUES.items():
        actual = manifest[field]
        if type(actual) is not type(expected) or actual != expected:
            raise ValueError(f"{_MANIFEST} {field} does not match locked Task 10 provenance")
    return _freeze(manifest)  # type: ignore[return-value]


def _decode_and_validate_task10_members(members: Mapping[str, bytes], *, production_zip_sha256: str, member_sha256_by_filename: Mapping[str, str]) -> Task10ProductionBundle:
    main_json = _decode_json(_MAIN, members[_MAIN])
    _validate_csv(_SUPPLEMENTARY, members[_SUPPLEMENTARY])
    _feature_dossiers_json = _decode_json(_FEATURES, members[_FEATURES])
    hypotheses_json = _decode_json(_HYPOTHESES, members[_HYPOTHESES])
    manifest_json = _decode_json(_MANIFEST, members[_MANIFEST])
    # Every member has now crossed its syntax/encoding boundary.  Structural
    # validation begins only after no malformed member remains undiscovered.
    hypotheses = hypotheses_json
    if type(hypotheses) is not list or hypotheses != []:
        raise ValueError(f"{_HYPOTHESES} must be the exact empty array")
    manifest = _validate_task10_manifest(manifest_json)
    main = _validate_main_dossiers(main_json)
    return Task10ProductionBundle(
        main_dossiers=main,
        manifest=manifest,
        production_zip_sha256=production_zip_sha256,
        member_sha256_by_filename=MappingProxyType(dict(member_sha256_by_filename)),
    )


def _load_task10_production_bytes(package_bytes: bytes, *, expected_package_sha256: str, expected_member_sha256_by_filename: Mapping[str, str]) -> Task10ProductionBundle:
    actual_package_sha256 = hashlib.sha256(package_bytes).hexdigest()
    if actual_package_sha256 != expected_package_sha256:
        raise ValueError(
            "Task 10 Production SHA-256 mismatch: "
            f"expected {expected_package_sha256}, got {actual_package_sha256}"
        )
    members = _read_exact_members(package_bytes)
    actual_member_hashes = {name: hashlib.sha256(data).hexdigest() for name, data in members.items()}
    if actual_member_hashes != dict(expected_member_sha256_by_filename):
        raise ValueError("Task 10 Production member SHA-256 mismatch")
    return _decode_and_validate_task10_members(members, production_zip_sha256=actual_package_sha256, member_sha256_by_filename=actual_member_hashes)


def load_task10_production_package(path: Path) -> Task10ProductionBundle:
    return _load_task10_production_bytes(
        Path(path).read_bytes(),
        expected_package_sha256=TASK10_PRODUCTION_PACKAGE_SHA256,
        expected_member_sha256_by_filename=TASK10_MEMBER_SHA256_BY_FILENAME,
    )


_LOWER_SHA1 = re.compile(r"[0-9a-f]{40}\Z")


def _validate_output_zip_path(output_zip: Path) -> Path:
    destination = Path(output_zip)
    if destination.name != OUTPUT_ZIP_FILENAME:
        raise ValueError(
            "Task 11 production ZIP basename must equal "
            f"{OUTPUT_ZIP_FILENAME!r}"
        )
    return destination


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            allow_nan=False,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _write_deterministic_zip(path: Path, members: Mapping[str, bytes]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        destination,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for name in sorted(members):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(
                info,
                members[name],
                compress_type=zipfile.ZIP_DEFLATED,
                compresslevel=9,
            )


def _exact_manifest_value(
    manifest: Mapping[str, object], field: str, expected: object
) -> None:
    actual = manifest[field]
    if type(actual) is not type(expected) or actual != expected:
        raise ValueError(f"Task 11 manifest {field} does not match locked value")


def _validate_task11_manifest(
    manifest: Mapping[str, object], *, implementation_commit: str, registry: object
) -> bytes:
    if set(manifest) != set(TASK11_MANIFEST_FIELDS):
        raise ValueError("Task 11 manifest fields do not match the closed schema")
    _exact_manifest_value(
        manifest, "task", "Task 11 — Evidence Review & Hypothesis Registration"
    )
    _exact_manifest_value(manifest, "task11_spec_commit", TASK11_SPEC_COMMIT)
    _exact_manifest_value(
        manifest, "task11_implementation_commit", implementation_commit
    )
    _exact_manifest_value(
        manifest, "hypothesis_registry_filename", TASK11_LOGICAL_FILENAMES[0]
    )
    _exact_manifest_value(
        manifest, "production_archive_filename", OUTPUT_ZIP_FILENAME
    )
    _exact_manifest_value(
        manifest, "logical_output_filenames", list(TASK11_LOGICAL_FILENAMES)
    )
    for field, expected in (
        ("task10_implementation_commit", TASK10_IMPLEMENTATION_COMMIT),
        ("task10_production_package_filename", TASK10_PRODUCTION_PACKAGE_FILENAME),
        ("task10_production_package_sha256", TASK10_PRODUCTION_PACKAGE_SHA256),
        ("task10_main_dossiers_member_sha256", TASK10_MAIN_DOSSIERS_MEMBER_SHA256),
        ("task10_manifest_member_sha256", TASK10_MANIFEST_MEMBER_SHA256),
        ("hypothesis_unit", "PAIRWISE_ONLY"),
        ("hypothesis_cardinality", "EXACTLY_ONE_PER_CANONICAL_PAIR"),
        ("hypothesis_id_policy", "DETERMINISTIC_FROM_PAIR_KEY"),
        ("hypothesis_id_prefix", HYPOTHESIS_ID_PREFIX),
        ("test_question_policy", "SINGLE_FIXED_TEMPLATE"),
        ("test_question_template_id", TEST_QUESTION_TEMPLATE_ID),
        ("evidence_summary_policy", "COPY_LOCKED_TASK10_OBSERVATIONS"),
        ("cross_tf_evidence_policy", "COPY_LOCKED_TASK10_CROSS_TF"),
        ("main_pair_count", MAIN_PAIR_COUNT),
        ("hypothesis_count", HYPOTHESIS_COUNT),
        ("duration_control_eligible_count", DURATION_CONTROL_ELIGIBLE_COUNT),
        (
            "control_feature_non_applicable_count",
            CONTROL_FEATURE_NON_APPLICABLE_COUNT,
        ),
        ("deterministic_context_pair_count", DETERMINISTIC_CONTEXT_PAIR_COUNT),
        ("logical_file_count", LOGICAL_FILE_COUNT),
    ):
        _exact_manifest_value(manifest, field, expected)
    for field in TASK11_FALSE_SCOPE_FIELDS:
        _exact_manifest_value(manifest, field, False)
    registry_bytes = _json_bytes(registry)
    _exact_manifest_value(
        manifest,
        "hypothesis_registry_sha256",
        hashlib.sha256(registry_bytes).hexdigest(),
    )
    return registry_bytes


def write_task11_outputs(
    output_dir: Path,
    *,
    implementation_commit: str,
    registry: Sequence[Mapping[str, object]],
    manifest: Mapping[str, object],
    output_zip: Path,
) -> None:
    """Write the exact Task 11 logical files and their reproducible archive."""
    destination_zip = _validate_output_zip_path(output_zip)
    if type(implementation_commit) is not str or not _LOWER_SHA1.fullmatch(
        implementation_commit
    ):
        raise ValueError("Task 11 implementation commit must be lowercase SHA-1")
    registry_bytes = _validate_task11_manifest(
        manifest, implementation_commit=implementation_commit, registry=registry
    )
    manifest_bytes = _json_bytes(manifest)
    members = {
        TASK11_LOGICAL_FILENAMES[0]: registry_bytes,
        TASK11_LOGICAL_FILENAMES[1]: manifest_bytes,
    }
    if set(members) != set(TASK11_LOGICAL_FILENAMES):
        raise RuntimeError("Task 11 logical output member schema drifted")

    destination_dir = Path(output_dir)
    destination_dir.mkdir(parents=True, exist_ok=True)
    for name in TASK11_LOGICAL_FILENAMES:
        (destination_dir / name).write_bytes(members[name])
    _write_deterministic_zip(destination_zip, members)


__all__ = ["Task10ProductionBundle", "load_task10_production_package"]
